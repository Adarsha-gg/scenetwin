#!/usr/bin/env python3
"""CoAD StoryRecall — FIXED: story beats from ADQA answer keys, NOT pro AD text.

Tests whether each tier AD conveys the same visual story as critical ADQA facts.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
Q = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v4" / "adqa_v4_questions.csv"
OUT = Path(__file__).resolve().parent / "output" / "story_recall_fixed.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-story-recall.md"

TIER_COL = {
    "tier3_va11y": "tier3_va11y_text",
    "tier2_vatex_long": "tier2_vatex_long_text",
    "tier1_vatex_short": "tier1_vatex_short_text",
    "tier0_cross": "tier0_cross_text",
}


def beats_from_adqa(clip_idx: int, questions: pd.DataFrame) -> list[str]:
    sub = questions[(questions["clip_idx"] == clip_idx) & (questions["importance"] == "critical")]
    beats = []
    for _, row in sub.iterrows():
        beats.append(str(row["answer_key"]).lower())
        for part in str(row.get("required_visual_evidence", "")).split(";"):
            if part.strip():
                beats.append(part.strip().lower())
    return beats


def beat_recall(beats: list[str], hyp: str) -> float:
    if not beats:
        return float("nan")
    hyp_l = hyp.lower()
    hit = 0
    for beat in beats:
        words = [w for w in re.findall(r"[a-z]{4,}", beat)]
        if not words:
            continue
        if sum(1 for w in words if w in hyp_l) / len(words) >= 0.35:
            hit += 1
    return hit / len(beats)


def main() -> None:
    fc = pd.read_csv(FORECAST)
    questions = pd.read_csv(Q)
    rows = []
    for _, clip in fc.iterrows():
        cidx = int(clip["clip_idx"])
        beats = beats_from_adqa(cidx, questions)
        for tier, col in TIER_COL.items():
            rows.append({
                "clip_idx": cidx,
                "tier": tier,
                "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier],
                "story_recall": beat_recall(beats, str(clip[col])),
                "n_beats": len(beats),
            })
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    means = df.groupby("tier")["story_recall"].mean()
    tier_gt = df.groupby("tier")["gt"].first().sort_values()
    rho, p = spearmanr(tier_gt.values, means.reindex(tier_gt.index).values)

    wins = 0
    full = 0
    for cidx, g in df.groupby("clip_idx"):
        v = dict(zip(g["tier"], g["story_recall"]))
        if v.get("tier3_va11y", 0) >= max(v.get("tier2_vatex_long", 0), v.get("tier1_vatex_short", 0), v.get("tier0_cross", 0)):
            wins += 1
        if v.get("tier3_va11y", 0) > v.get("tier2_vatex_long", 0) > v.get("tier1_vatex_short", 0) > v.get("tier0_cross", 0):
            full += 1
    n = df["clip_idx"].nunique()

    FINDINGS.write_text(
        f"# StoryRecall (ADQA beats as reference)\n\n"
        f"- tier3 wins clip: **{wins}/{n}**\n"
        f"- full order 3>2>1>0: **{full}/{n}**\n"
        f"- tier means: {means.to_dict()}\n"
        f"- ρ(gt, tier_mean)={rho:.3f} p={p:.4f}\n\n"
        f"Compare ensemble full-order 15/18.\n",
        encoding="utf-8",
    )
    print(f"tier3 wins {wins}/{n} | full order {full}/{n}")
    print(means)
    print(f"ρ={rho:.3f} p={p:.4f}")


if __name__ == "__main__":
    main()
