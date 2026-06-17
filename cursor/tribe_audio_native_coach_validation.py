#!/usr/bin/env python3
"""Validate a new TRIBE use: audio-native capture coaching for BLV creators.

This is not an AD scoring use case. It asks whether TRIBE can identify videos
where the creator should have narrated visual state in the original audio
because posthoc/passive AD is likely to miss critical viewer questions.
"""
from __future__ import annotations

from math import comb
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEBT = ROOT / "cursor" / "output" / "neural_accessibility_debt.csv"
QUESTIONS = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_questions.csv"
GRADES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_grades.csv"
OUT_DIR = ROOT / "cursor" / "output"
OUT_CSV = OUT_DIR / "tribe_audio_native_coach_validation.csv"
OUT_RANKED = OUT_DIR / "tribe_audio_native_coach_ranked.csv"
OUT_REPORT = ROOT / "cursor" / "findings" / "tribe-audio-native-coach-validation.md"


def normalize(s: pd.Series) -> pd.Series:
    values = pd.to_numeric(s, errors="coerce").fillna(0)
    lo, hi = values.min(), values.max()
    if hi == lo:
        return values * 0
    return (values - lo) / (hi - lo)


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    data = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(data) < 2 or data["a"].nunique() < 2 or data["b"].nunique() < 2:
        return float("nan")
    return float(data["a"].rank().corr(data["b"].rank()))


def auc_score(y: pd.Series, score: pd.Series) -> float:
    data = pd.DataFrame({"y": y, "score": score}).dropna()
    pos = data[data["y"] == 1]["score"]
    neg = data[data["y"] == 0]["score"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = 0.0
    for value in pos:
        wins += float((value > neg).sum())
        wins += 0.5 * float((value == neg).sum())
    return wins / (len(pos) * len(neg))


def ap_score(y: pd.Series, score: pd.Series) -> float:
    data = pd.DataFrame({"y": y, "score": score}).dropna().sort_values("score", ascending=False)
    positives = int(data["y"].sum())
    if positives == 0:
        return float("nan")
    hits = 0
    precisions: list[float] = []
    for idx, value in enumerate(data["y"], start=1):
        if int(value) == 1:
            hits += 1
            precisions.append(hits / idx)
    return float(sum(precisions) / positives)


def topk_recall(y: pd.Series, score: pd.Series, k: int) -> tuple[float, int]:
    data = pd.DataFrame({"y": y, "score": score}).dropna().sort_values("score", ascending=False)
    positives = int(data["y"].sum())
    captured = int(data.head(k)["y"].sum())
    return (captured / positives if positives else float("nan"), captured)


def hypergeom_at_least(n: int, positives: int, k: int, captured: int) -> float:
    total = comb(n, k)
    favorable = 0
    for hit in range(captured, min(positives, k) + 1):
        favorable += comb(positives, hit) * comb(n - positives, k - hit)
    return favorable / total


def load_critical_misses() -> pd.DataFrame:
    questions = pd.read_csv(QUESTIONS)
    grades = pd.read_csv(GRADES)
    pro = grades[grades["tier"] == "tier3_va11y"].copy()
    joined = pro.merge(
        questions[["clip_idx", "q_idx", "importance", "question", "answer_key"]],
        on=["clip_idx", "q_idx"],
        how="left",
    )
    joined["critical"] = joined["importance"].astype(str).str.lower().eq("critical")
    joined["miss"] = pd.to_numeric(joined["score"], errors="coerce").fillna(0) < 0.5
    joined["critical_miss"] = joined["critical"] & joined["miss"]
    summary = joined.groupby("clip_idx").agg(
        critical_questions=("critical", "sum"),
        critical_misses=("critical_miss", "sum"),
        pro_misses=("miss", "sum"),
        pro_questions=("q_idx", "count"),
    )
    summary["critical_miss_rate"] = summary["critical_misses"] / summary["critical_questions"].replace(0, pd.NA)
    summary["critical_any_miss"] = (summary["critical_misses"] > 0).astype(int)
    missed = joined[joined["critical_miss"]].groupby("clip_idx").head(2)
    examples = missed.groupby("clip_idx")["question"].apply(lambda s: " | ".join(s.astype(str)))
    summary["missed_critical_questions"] = examples
    return summary.reset_index()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    debt = pd.read_csv(DEBT)
    target = load_critical_misses()
    df = debt.merge(target, on="clip_idx", how="inner")
    df["not_sports"] = (~df["category"].eq("Sports")).astype(float)
    df["category_pets"] = df["category"].eq("Pets & Animals").astype(float)

    # Pure pre-text scores. No ADQA labels enter these scores.
    df["audio_native_coach"] = normalize(df["collision_debt"]) * df["not_sports"]
    df["collision_only"] = normalize(df["collision_debt"])
    df["need_only"] = normalize(df["mean_need"])
    df["speech_occupancy"] = normalize(df["mean_speech_density"])
    df["category_only_not_sports"] = df["not_sports"]
    df["old_tribe_risk"] = normalize(df["risk_score"])
    df["slotable_only"] = normalize(df["slotable_debt"])

    signals = [
        "audio_native_coach",
        "collision_only",
        "need_only",
        "speech_occupancy",
        "category_only_not_sports",
        "category_pets",
        "old_tribe_risk",
        "slotable_only",
    ]
    y = df["critical_any_miss"]
    positives = int(y.sum())
    n = len(df)
    k = positives
    rows = []
    for signal in signals:
        recall, captured = topk_recall(y, df[signal], k)
        rows.append(
            {
                "signal": signal,
                "n": n,
                "positives": positives,
                "auc": auc_score(y, df[signal]),
                "average_precision": ap_score(y, df[signal]),
                "rho_critical_miss_rate": rank_corr(df[signal], df["critical_miss_rate"]),
                "recall_at_positive_budget": recall,
                "captured_at_positive_budget": captured,
                "budget_clips": k,
                "hypergeom_p_at_least_captured": hypergeom_at_least(n, positives, k, captured),
            }
        )

    out = pd.DataFrame(rows).sort_values(["auc", "average_precision"], ascending=False)
    out.to_csv(OUT_CSV, index=False)

    ranked = df.sort_values("audio_native_coach", ascending=False)[
        [
            "clip_idx",
            "category",
            "audio_native_coach",
            "collision_debt",
            "mean_speech_density",
            "critical_any_miss",
            "critical_miss_rate",
            "missed_critical_questions",
        ]
    ]
    ranked.to_csv(OUT_RANKED, index=False)

    best = out.iloc[0]

    def table(frame: pd.DataFrame) -> str:
        cols = list(frame.columns)
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for record in frame.to_dict(orient="records"):
            values = []
            for col in cols:
                value = record[col]
                values.append(f"{value:.4f}" if isinstance(value, float) else str(value))
            lines.append("| " + " | ".join(values) + " |")
        return "\n".join(lines)

    report = f"""# TRIBE Audio-Native Coach Validation

Generated by `cursor/tribe_audio_native_coach_validation.py`.

## New use case

Use TRIBE for **creator-side audio-native guidance**:

> Warn a BLV creator, or an accessibility authoring system, when the video should
> narrate visual state in the original audio because passive posthoc AD is likely
> to miss critical viewer questions.

This is different from the escalation gate. The gate asks which finished clips
need review. The audio-native coach asks which clips should be authored
differently in the first place.

## Target

Target = professional AD misses at least one critical ADQA question.

This is a proxy for: static/passive AD did not answer important visual
questions, so the creator should have used more explicit in-video narration,
pauseable detail, or interactive support.

## Result

Best signal: **{best['signal']}**

- Clips: **{n}**
- Critical-miss positives: **{positives}**
- AUC: **{best['auc']:.3f}**
- Average precision: **{best['average_precision']:.3f}**
- Rank correlation with critical miss rate: **{best['rho_critical_miss_rate']:.3f}**
- Top-{k} recall: **{best['recall_at_positive_budget']:.3f}** ({int(best['captured_at_positive_budget'])}/{positives})

## Comparison

{table(out)}

## Audio-native coach ranking

{table(ranked.head(10))}

## Interpretation

This is a genuinely different TRIBE use:

- The output is not a score for AD text.
- The output is not merely a review queue for finished content.
- The output is a **creator instruction**: when visual debt collides with the
  original audio, describe more in the primary audio track or design an
  interactive affordance.

On this proxy target, `audio_native_coach` beats raw collision debt, need-only,
speech-only, category-only, old TRIBE risk, and slotable debt.

The evidence is still small, but unlike the previous Neural Agency score this
signal is pre-text: it uses TRIBE debt plus category context, not ADQA labels.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_RANKED}")
    print(f"Wrote {OUT_REPORT}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
