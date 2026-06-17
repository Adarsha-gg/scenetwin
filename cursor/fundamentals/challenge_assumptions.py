#!/usr/bin/env python3
"""Challenge SceneTwin fundamentals — assumptions that may be wrong.

Tests:
  1. Cross-video tier0 confound (wrong-category AD sometimes scores high)
  2. Metric disagreement on hard clips (clip_00, clip_12)
  3. Length confound (word count vs score)
  4. Is ensemble redundant with VT-only?
  5. GT violations are metric-specific or universal?
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "challenge_assumptions.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "fundamentals-challenges.md"

ENSEMBLE_COL = "ensemble_w50_adqa_need_weighted_clip"
ADQA_COL = "adqa_v4_score"
TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}


def _tier_vals(g: pd.DataFrame, col: str) -> dict[str, float]:
    return dict(zip(g["tier"], g[col]))


def load_merged() -> pd.DataFrame:
    ens = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")
    adqa = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv")
    vt_path = Path(__file__).resolve().parents[1] / "methods" / "output" / "av_consistency_scores.csv"
    vt = pd.read_csv(vt_path) if vt_path.exists() else pd.DataFrame()
    df = ens.merge(adqa[["clip_idx", "tier", ADQA_COL]], on=["clip_idx", "tier"], how="left")
    df = df.rename(columns={ENSEMBLE_COL: "ensemble_score", ADQA_COL: "adqa_score"})
    if not vt.empty:
        df = df.merge(vt[["clip_idx", "tier", "vt_consistency"]], on=["clip_idx", "tier"], how="left")
    forecast = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    df = df.merge(
        forecast[["clip_idx", "tribe_pressure", "risk_score", "extended_seconds_frac"]],
        on="clip_idx", how="left",
    )
    # word counts from forecast text cols
    for tier, col in [
        ("tier3_va11y", "tier3_va11y_words"),
        ("tier1_vatex_short", "tier1_vatex_short_words"),
    ]:
        if col in forecast.columns:
            w = forecast.set_index("clip_idx")[col]
            df.loc[df["tier"] == tier, "word_count"] = df.loc[df["tier"] == tier, "clip_idx"].map(w)
    return df


def tier0_beats_tier1(df: pd.DataFrame, col: str) -> list[int]:
    bad = []
    for cidx, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        if "tier0_cross" in v and "tier1_vatex_short" in v and v["tier0_cross"] > v["tier1_vatex_short"]:
            bad.append(int(cidx))
    return bad


def violations(df: pd.DataFrame, col: str) -> set[int]:
    bad = set()
    for cidx, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        for hi, lo in [("tier3_va11y", "tier2_vatex_long"), ("tier3_va11y", "tier1_vatex_short"),
                       ("tier2_vatex_long", "tier1_vatex_short")]:
            if hi in v and lo in v and v[hi] < v[lo]:
                bad.add(int(cidx))
    return bad


def main() -> None:
    df = load_merged()
    rows = []

    # 1. Cross-video confound
    for col in ["ensemble_score", "adqa_score", "vt_consistency"]:
        if col not in df.columns:
            continue
        bad = tier0_beats_tier1(df.dropna(subset=[col]), col)
        rows.append({
            "test": "tier0_beats_tier1",
            "metric": col,
            "n_clips": len(bad),
            "clip_ids": ",".join(map(str, bad)),
            "interpretation": "cross-video control outscores in-domain short caption",
        })

    # 2. Hard clips — which metrics fail?
    hard = {0, 12}
    for col in ["ensemble_score", "adqa_score", "vt_consistency"]:
        if col not in df.columns:
            continue
        viol = violations(df.dropna(subset=[col]), col)
        overlap = hard & viol
        rows.append({
            "test": "hard_clip_violations",
            "metric": col,
            "n_clips": len(overlap),
            "clip_ids": ",".join(map(str, sorted(overlap))),
            "interpretation": f"GT violations on known-hard clips; total viol={len(viol)}",
        })

    # 3. Length confound — partial: score vs word_count within tier3
    t3 = df[df["tier"] == "tier3_va11y"].dropna(subset=["ensemble_score", "word_count"])
    if len(t3) >= 5:
        r_len, p_len = pearsonr(t3["word_count"], t3["ensemble_score"])
        rows.append({
            "test": "length_confound_tier3",
            "metric": "ensemble_score",
            "n_clips": len(t3),
            "clip_ids": f"r={r_len:.3f},p={p_len:.4f}",
            "interpretation": "pro AD word count vs ensemble score (should be weak if not length-biased)",
        })

    # 4. Ensemble vs VT redundancy
    sub = df.dropna(subset=["ensemble_score", "vt_consistency"])
    if len(sub) >= 8:
        r, p = spearmanr(sub["ensemble_score"], sub["vt_consistency"])
        rows.append({
            "test": "ensemble_vt_redundancy",
            "metric": "spearman",
            "n_clips": len(sub),
            "clip_ids": f"rho={r:.3f},p={p:.4f}",
            "interpretation": "high rho → VT adds little; low rho → orthogonal signal",
        })

    # 5. TRIBE pressure vs tier3 margin
    t3m = []
    for cidx, g in df.groupby("clip_idx"):
        v = _tier_vals(g, "ensemble_score")
        if "tier3_va11y" in v and "tier1_vatex_short" in v:
            press = g["tribe_pressure"].iloc[0]
            t3m.append((press, v["tier3_va11y"] - v["tier1_vatex_short"]))
    if len(t3m) >= 5:
        press, margins = zip(*t3m)
        r, p = spearmanr(press, margins)
        rows.append({
            "test": "tribe_pressure_vs_tier3_margin",
            "metric": "ensemble",
            "n_clips": len(t3m),
            "clip_ids": f"rho={r:.3f},p={p:.4f}",
            "interpretation": "high need → harder to separate pro from short?",
        })

    rep = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUT, index=False)

    lines = ["# Fundamental assumption challenges\n\n"]
    for _, r in rep.iterrows():
        lines.append(f"## {r['test']} ({r['metric']})\n\n")
        lines.append(f"- **Result:** {r['clip_ids']}\n")
        lines.append(f"- **Read:** {r['interpretation']}\n\n")

    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(rep.to_string(index=False))
    print(f"\nWrote {OUT} and {FINDINGS}")


if __name__ == "__main__":
    main()
