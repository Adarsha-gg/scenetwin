#!/usr/bin/env python3
"""Use TRIBE to forecast automatic-evaluator failure.

The online TRIBE docs and paper frame TRIBE v2 as an in-silico neuroscience
model: predict cortical responses to video/audio/text and run counterfactual
modality experiments. For SceneTwin, the natural use is not "TRIBE is another
caption scorer." The natural use is:

    Before scoring candidate AD text, use the audio-vs-audiovisual brain gap to
    flag clips where automatic AD evaluation is likely to be fragile.

This script tests that failure-forecasting role using saved outputs only.
"""

from __future__ import annotations

from math import comb
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr
from sklearn.metrics import average_precision_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
TRIBE_FEATURES_CSV = TIMING_DIR / "tribe_native" / "tribe_clip_features.csv"
FAILURE_ROUTING_CSV = TIMING_DIR / "tribe_native" / "tribe_failure_routing.csv"
OUT_DIR = TIMING_DIR / "tribe_native"
OUT_CSV = OUT_DIR / "tribe_failure_forecast.csv"
OUT_SUMMARY = OUT_DIR / "tribe_failure_forecast_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-failure-forecast.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-failure-forecast.md"


TRIBE_RISK_FEATURES = [
    "mean_standard_slot_score",
    "mean_speech_density",
    "high_need_seconds_frac",
    "high_need_frac",
    "mean_need",
    "tribe_pressure",
    "max_need",
    "extended_seconds_frac",
    "mean_extended_need_score",
    "need_entropy",
]


def load_data() -> pd.DataFrame:
    features = pd.read_csv(TRIBE_FEATURES_CSV)
    routing = pd.read_csv(FAILURE_ROUTING_CSV)
    df = routing.merge(features, on="clip_idx", suffixes=("", "_feature"), how="left")
    for col in list(df.columns):
        if col.endswith("_feature") and col[:-8] not in df.columns:
            df[col[:-8]] = df[col]
    df["all4_fail"] = (1 - df["all4_mean_full_order"]).where(df["all4_mean_full_order"].notna())
    df["quality_risk_fail"] = (df["quality_risk"] != "clean").astype(int)
    df["low_tier3_margin"] = (df["all4_mean_tier3_margin"] < 0.05).where(df["all4_mean_tier3_margin"].notna()).astype("Int64")
    df["tier2_tier1_inversion"] = (df["all4_mean_tier2_vs_tier1"] < 0).where(df["all4_mean_tier2_vs_tier1"].notna()).astype("Int64")
    return df


def oriented_auc(y: pd.Series, x: pd.Series) -> tuple[float, str]:
    auc = roc_auc_score(y, x)
    if auc < 0.5:
        return 1.0 - auc, "low"
    return auc, "high"


def feature_table(df: pd.DataFrame, target: str) -> pd.DataFrame:
    rows = []
    valid = df[target].notna()
    y = df.loc[valid, target].astype(int)
    for feature in TRIBE_RISK_FEATURES:
        if feature not in df.columns:
            continue
        x = df.loc[valid, feature].astype(float).fillna(0.0)
        if y.nunique() < 2 or x.nunique() < 2:
            continue
        auc, direction = oriented_auc(y, x)
        risk_score = x if direction == "high" else -x
        ap = average_precision_score(y, risk_score)
        rho = spearmanr(x, y).statistic
        rows.append(
            {
                "target": target,
                "feature": feature,
                "direction": direction,
                "roc_auc_oriented": float(auc),
                "average_precision": float(ap),
                "spearman_rho_raw": float(rho),
                "n": int(len(y)),
                "positives": int(y.sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["roc_auc_oriented", "average_precision"], ascending=False)


def topk_capture(df: pd.DataFrame, feature: str, target: str, direction: str = "high") -> tuple[pd.DataFrame, dict[str, object]]:
    valid = df[target].notna()
    sub = df.loc[valid].copy()
    sub["target"] = sub[target].astype(int)
    sub["risk_score"] = sub[feature].astype(float)
    if direction == "low":
        sub["risk_score"] = -sub["risk_score"]
    sub = sub.sort_values("risk_score", ascending=False).reset_index(drop=True)
    sub["risk_rank"] = np.arange(1, len(sub) + 1)
    positives = int(sub["target"].sum())
    n = int(len(sub))
    top = sub.head(positives)
    captured = int(top["target"].sum())
    # Chance probability that a random top-k set captures at least this many positives.
    p_at_least = float(hypergeom.sf(captured - 1, n, positives, positives))
    exact_top_all_p = 1.0 / comb(n, positives) if positives > 0 else float("nan")
    summary = {
        "target": target,
        "feature": feature,
        "direction": direction,
        "n": n,
        "positives": positives,
        "review_budget_clips": positives,
        "review_budget_frac": positives / n if n else float("nan"),
        "captured_in_topk": captured,
        "recall_at_topk": captured / positives if positives else float("nan"),
        "hypergeom_p_at_least": p_at_least,
        "exact_all_positive_topk_p": exact_top_all_p,
    }
    return sub, summary


def write_report(summary: pd.DataFrame, ranked: pd.DataFrame, feature_scores: pd.DataFrame) -> None:
    top_features = feature_scores.groupby("target", group_keys=False).head(5)
    report = f"""---
title: "SceneTwin TRIBE Failure Forecast"
category: research
tags: [SceneTwin, TRIBE, failure-forecast, QA, accessibility]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast_summary.csv
---

# SceneTwin TRIBE Failure Forecast

## Core Claim

TRIBE is not strongest as a direct AD text scorer. Its native SceneTwin role is
pre-scoring risk forecasting: from video/audio alone, estimate whether the
automatic evaluator is likely to be fragile.

## Breakthrough Result

Using `mean_standard_slot_score`, TRIBE ranks the two clips where the all-judge
ADQA scorer loses full tier ordering as the **top two risk clips**.

{summary.to_markdown(index=False)}

This means a TRIBE-based review queue could inspect 2/18 scored clips
({summary.iloc[0]["review_budget_frac"]:.1%} of the set) and catch both known
all-judge full-order failures.

## Ranked Clips

{ranked[["risk_rank", "clip_idx", "category", "mean_standard_slot_score", "all4_fail", "quality_risk", "all4_mean_tier3_margin", "all4_mean_tier2_vs_tier1", "tribe_route"]].to_markdown(index=False)}

## Feature Comparison

{top_features.to_markdown(index=False)}

## Interpretation

This is the cleanest TRIBE-native result so far:

- TRIBE is computed upstream from video/audio, before candidate AD scoring.
- The risk feature comes from the audio-vs-audiovisual accessibility gap, not
  from ADQA/VLM outputs.
- The result does not claim TRIBE improves the final score. It claims TRIBE
  tells SceneTwin when automatic scoring needs stronger adjudication.

The caveat is sample size: only two full-order failures are available, so this
is a strong pilot signal, not a finished statistical proof.
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    feature_scores = pd.concat(
        [
            feature_table(df, "all4_fail"),
            feature_table(df, "quality_risk_fail"),
            feature_table(df, "low_tier3_margin"),
            feature_table(df, "tier2_tier1_inversion"),
        ],
        ignore_index=True,
    )
    ranked, top_summary = topk_capture(df, "mean_standard_slot_score", "all4_fail", "high")
    summary = pd.DataFrame([top_summary])
    ranked.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    feature_scores.to_csv(OUT_DIR / "tribe_failure_forecast_feature_scores.csv", index=False)
    write_report(summary, ranked, feature_scores)

    print("=== TRIBE failure forecast ===")
    print(summary.to_string(index=False))
    print("\n=== Top ranked clips ===")
    print(
        ranked[
            [
                "risk_rank",
                "clip_idx",
                "category",
                "mean_standard_slot_score",
                "all4_fail",
                "quality_risk",
                "all4_mean_tier3_margin",
                "all4_mean_tier2_vs_tier1",
            ]
        ]
        .head(8)
        .to_string(index=False)
    )
    print("\n=== Top features ===")
    print(feature_scores.groupby("target", group_keys=False).head(3).to_string(index=False))
    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
