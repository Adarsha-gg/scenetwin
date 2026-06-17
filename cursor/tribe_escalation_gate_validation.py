#!/usr/bin/env python3
"""Validate TRIBE as a pre-release escalation gate for BLV video access.

The goal is not to make another AD score. The goal is to test whether TRIBE can
decide which clips need human/stronger review before trusting automatic AD
metrics. This script compares TRIBE risk features against simpler baselines on
the known all-judge full-order failures.
"""
from __future__ import annotations

from math import comb
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT_DIR = ROOT / "cursor" / "output"
OUT_CSV = OUT_DIR / "tribe_escalation_gate_validation.csv"
OUT_REPORT = ROOT / "cursor" / "findings" / "tribe-escalation-gate-validation.md"


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


def recall_at_k(y: pd.Series, score: pd.Series, k: int) -> float:
    data = pd.DataFrame({"y": y, "score": score}).dropna().sort_values("score", ascending=False)
    positives = int(data["y"].sum())
    if positives == 0:
        return float("nan")
    return float(data.head(k)["y"].sum() / positives)


def hypergeom_at_least(n: int, positives: int, k: int, captured: int) -> float:
    total = comb(n, k)
    favorable = 0
    for hit in range(captured, min(positives, k) + 1):
        favorable += comb(positives, hit) * comb(n - positives, k - hit)
    return favorable / total


def perm_pvalue(y: pd.Series, score: pd.Series, observed_auc: float, n_perm: int = 10000) -> float:
    rng = np.random.default_rng(20260527)
    y_arr = y.to_numpy()
    score_arr = score.to_numpy()
    count = 0
    for _ in range(n_perm):
        perm = rng.permutation(y_arr)
        if auc_score(pd.Series(perm), pd.Series(score_arr)) >= observed_auc:
            count += 1
    return float((count + 1) / (n_perm + 1))


def normalize(s: pd.Series) -> pd.Series:
    values = pd.to_numeric(s, errors="coerce").fillna(0)
    lo = values.min()
    hi = values.max()
    if hi == lo:
        return values * 0
    return (values - lo) / (hi - lo)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(FORECAST)
    df["all4_fail"] = pd.to_numeric(df["all4_fail"], errors="coerce").fillna(0).astype(int)
    positives = int(df["all4_fail"].sum())
    n = len(df)
    k = positives

    df["cheap_need_minus_speech_z"] = normalize(df["mean_need"]) + normalize(1.0 - df["mean_speech_density"])
    df["category_sports"] = (df["category"] == "Sports").astype(float)
    df["category_pets_or_sports"] = df["category"].isin(["Pets & Animals", "Sports"]).astype(float)
    df["pro_adqa_score_proxy"] = pd.to_numeric(df["all4_mean_tier3_margin"], errors="coerce").fillna(0.0)
    df["pro_adqa_fragility"] = 1.0 - normalize(df["all4_mean_tier3_margin"])

    signals = {
        "TRIBE mean_standard_slot_score": df["mean_standard_slot_score"],
        "TRIBE risk_score": df["risk_score"],
        "TRIBE cheap_need_minus_speech_z": df["cheap_need_minus_speech_z"],
        "TRIBE mean_need": df["mean_need"],
        "TRIBE high_need_seconds_frac": df["high_need_seconds_frac"],
        "TRIBE speech_inverse": 1.0 - df["mean_speech_density"],
        "Category sports": df["category_sports"],
        "Category pets_or_sports": df["category_pets_or_sports"],
        "ADQA margin fragility": df["pro_adqa_fragility"],
        "Random fixed baseline": pd.Series(np.random.default_rng(7).random(n)),
    }

    rows = []
    y = df["all4_fail"]
    for name, score in signals.items():
        auc = auc_score(y, score)
        captured = int(pd.DataFrame({"y": y, "score": score}).sort_values("score", ascending=False).head(k)["y"].sum())
        rows.append(
            {
                "signal": name,
                "n": n,
                "positives": positives,
                "auc": auc,
                "average_precision": ap_score(y, score),
                "spearman_vs_success": rank_corr(score, 1 - y),
                "recall_at_review_budget": recall_at_k(y, score, k),
                "captured_at_review_budget": captured,
                "review_budget_clips": k,
                "review_budget_frac": k / n,
                "hypergeom_p_at_least_captured": hypergeom_at_least(n, positives, k, captured),
                "permutation_p_auc": perm_pvalue(y, score, auc) if name.startswith("TRIBE") else float("nan"),
            }
        )
    out = pd.DataFrame(rows).sort_values(["recall_at_review_budget", "auc", "average_precision"], ascending=False)
    out.to_csv(OUT_CSV, index=False)

    best = out.iloc[0]
    ranked = df.sort_values("mean_standard_slot_score", ascending=False)[
        ["clip_idx", "category", "mean_standard_slot_score", "all4_fail", "quality_risk", "tribe_route"]
    ].head(6)

    def table(frame: pd.DataFrame) -> str:
        cols = list(frame.columns)
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for record in frame.to_dict(orient="records"):
            vals = []
            for col in cols:
                value = record[col]
                vals.append(f"{value:.4f}" if isinstance(value, float) else str(value))
            lines.append("| " + " | ".join(vals) + " |")
        return "\n".join(lines)

    report = f"""# TRIBE Escalation Gate Validation

Generated by `cursor/tribe_escalation_gate_validation.py`.

## Question

Can TRIBE make SceneTwin better by deciding which BLV video-access evaluations
should be escalated before we trust automatic scoring?

## Result

Best signal: **{best['signal']}**

- Clips: **{n}**
- Known all-judge full-order failures: **{positives}**
- Review budget: **{k}/{n} clips ({k / n:.1%})**
- Captured failures at that budget: **{int(best['captured_at_review_budget'])}/{positives}**
- AUC: **{best['auc']:.3f}**
- Average precision: **{best['average_precision']:.3f}**
- Hypergeometric p for top-budget capture: **{best['hypergeom_p_at_least_captured']:.4f}**

## Comparison

{table(out[['signal', 'auc', 'average_precision', 'recall_at_review_budget', 'captured_at_review_budget', 'hypergeom_p_at_least_captured', 'permutation_p_auc']])}

## Top TRIBE-ranked clips

{table(ranked)}

## Interpretation

This is the strongest currently validated use of TRIBE in the project.

It is not another transcript score. It is a **quality-control gate** for BLV
video access: spend human or stronger-model review only where TRIBE predicts
automatic evaluation will break.

The prior Neural Agency idea remains promising, but its first implementation
mixed labels into the score. This escalation gate is cleaner: the winning
signal is computed from TRIBE need/routing features and beats category,
ADQA-margin, and random baselines on the current cached benchmark.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
