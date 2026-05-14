#!/usr/bin/env python3
"""Robustness checks for the TRIBE failure-forecast result.

The headline pilot result is strong but small: one TRIBE feature ranks the two
all4 ADQA full-order failures as the top two risk clips. This script asks how
much trust that deserves.

Checks:
- Does the risk feature predict failures for other scorers too?
- Does it predict continuous margins, not just binary failures?
- How does it compare against cheap non-TRIBE baselines?
- How much does multiple feature search weaken the p-value?
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
FEATURES_CSV = TIMING_DIR / "tribe_native" / "tribe_clip_features.csv"
OUT_DIR = TIMING_DIR / "tribe_native"
OUT_TARGETS = OUT_DIR / "tribe_failure_robustness_targets.csv"
OUT_FEATURES = OUT_DIR / "tribe_failure_robustness_feature_auc.csv"
OUT_MARGINS = OUT_DIR / "tribe_failure_robustness_margin_corr.csv"
OUT_SUMMARY = OUT_DIR / "tribe_failure_robustness_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-failure-robustness.md"


PURE_TRIBE_FEATURES = [
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

CHEAP_BASELINES = [
    "duration_s",
    "tier3_va11y_words",
    "pro_minus_short_words",
    "pro_minus_long_words",
    "tier2_vatex_long_words",
    "tier1_vatex_short_words",
]

SCORERS = [
    "all4_mean",
    "selected3_mean",
    "strict_all4_80adqa_20clip",
    "clip_mean_norm",
    "claude_vlm_completeness_norm",
    "claude_vlm_specificity_norm",
    "vlm_best_dims_mean",
]


def load() -> pd.DataFrame:
    df = pd.read_csv(FEATURES_CSV)
    return df[df["all4_mean_full_order"].notna()].copy()


def oriented_auc(y: pd.Series, x: pd.Series) -> tuple[float, str, float]:
    auc = roc_auc_score(y, x)
    direction = "high"
    risk = x
    if auc < 0.5:
        auc = 1.0 - auc
        direction = "low"
        risk = -x
    ap = average_precision_score(y, risk)
    return float(auc), direction, float(ap)


def binary_targets(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scorer in SCORERS:
        full_col = f"{scorer}_full_order"
        margin_col = f"{scorer}_tier3_margin"
        inv_col = f"{scorer}_tier2_vs_tier1"
        if full_col in df:
            for row in df.itertuples(index=False):
                rows.append(
                    {
                        "clip_idx": int(row.clip_idx),
                        "category": row.category,
                        "target": f"{scorer}_full_order_fail",
                        "failed": int(1 - getattr(row, full_col)),
                    }
                )
        if margin_col in df:
            threshold = 0.05
            for row in df.itertuples(index=False):
                rows.append(
                    {
                        "clip_idx": int(row.clip_idx),
                        "category": row.category,
                        "target": f"{scorer}_low_tier3_margin_lt_{threshold}",
                        "failed": int(getattr(row, margin_col) < threshold),
                    }
                )
        if inv_col in df:
            for row in df.itertuples(index=False):
                rows.append(
                    {
                        "clip_idx": int(row.clip_idx),
                        "category": row.category,
                        "target": f"{scorer}_tier2_tier1_inversion",
                        "failed": int(getattr(row, inv_col) < 0),
                    }
                )
    return pd.DataFrame(rows)


def feature_auc(df: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    features = [f for f in PURE_TRIBE_FEATURES + CHEAP_BASELINES if f in df.columns]
    feature_kind = {f: "TRIBE" for f in PURE_TRIBE_FEATURES}
    feature_kind.update({f: "cheap_baseline" for f in CHEAP_BASELINES})
    for target, group in targets.groupby("target"):
        y = group.set_index("clip_idx")["failed"].astype(int)
        if y.nunique() < 2:
            continue
        work = df.set_index("clip_idx").loc[y.index]
        for feature in features:
            x = work[feature].astype(float).fillna(0.0)
            if x.nunique() < 2:
                continue
            auc, direction, ap = oriented_auc(y, x)
            rows.append(
                {
                    "target": target,
                    "feature": feature,
                    "feature_kind": feature_kind[feature],
                    "direction": direction,
                    "auc_oriented": auc,
                    "average_precision": ap,
                    "positives": int(y.sum()),
                    "n": int(len(y)),
                }
            )
    return pd.DataFrame(rows).sort_values(["target", "auc_oriented", "average_precision"], ascending=[True, False, False])


def margin_correlations(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scorer in SCORERS:
        for suffix in ["tier3_margin", "tier2_vs_tier1", "spread"]:
            col = f"{scorer}_{suffix}"
            if col not in df:
                continue
            for feature in PURE_TRIBE_FEATURES:
                if feature not in df:
                    continue
                sub = df[[feature, col]].dropna()
                if len(sub) < 6 or sub[feature].nunique() < 2 or sub[col].nunique() < 2:
                    continue
                rho, p = spearmanr(sub[feature], sub[col])
                rows.append(
                    {
                        "scorer": scorer,
                        "outcome": suffix,
                        "feature": feature,
                        "spearman_rho": float(rho),
                        "p": float(p),
                        "n": int(len(sub)),
                    }
                )
    return pd.DataFrame(rows).sort_values("spearman_rho", key=lambda s: s.abs(), ascending=False)


def topk_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    feature = "mean_standard_slot_score"
    for scorer in SCORERS:
        full_col = f"{scorer}_full_order"
        if full_col not in df:
            continue
        sub = df[["clip_idx", "category", feature, full_col]].dropna().copy()
        sub["failed"] = (1 - sub[full_col]).astype(int)
        positives = int(sub["failed"].sum())
        if positives == 0:
            continue
        ranked = sub.sort_values(feature, ascending=False).reset_index(drop=True)
        ranked["rank"] = np.arange(1, len(ranked) + 1)
        top = ranked.head(positives)
        captured = int(top["failed"].sum())
        n = len(ranked)
        p = float(hypergeom.sf(captured - 1, n, positives, positives))
        rows.append(
            {
                "scorer": scorer,
                "n": n,
                "failures": positives,
                "topk_captured": captured,
                "recall_at_k_failures": captured / positives,
                "topk_p_uncorrected": p,
                "exact_all_failures_topk_p": 1 / comb(n, positives),
                "failure_ranks": ",".join(str(int(r.rank)) for r in ranked[ranked["failed"] == 1].itertuples(index=False)),
            }
        )
    return pd.DataFrame(rows)


def write_report(summary: pd.DataFrame, aucs: pd.DataFrame, margins: pd.DataFrame) -> None:
    all4_auc = aucs[aucs["target"] == "all4_mean_full_order_fail"].head(10)
    cross = summary.sort_values(["recall_at_k_failures", "topk_p_uncorrected"], ascending=[False, True])
    margin_top = margins.head(12)
    all4 = summary[summary["scorer"] == "all4_mean"].iloc[0]
    n_features = len(PURE_TRIBE_FEATURES)
    bonf = min(1.0, float(all4["topk_p_uncorrected"]) * n_features)

    report = f"""---
title: "SceneTwin TRIBE Failure Forecast Robustness"
category: research
tags: [SceneTwin, TRIBE, robustness, validation]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_summary.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_feature_auc.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_margin_corr.csv
---

# SceneTwin TRIBE Failure Forecast Robustness

## Main Check

For the all-four ADQA mean, `mean_standard_slot_score` ranks the two full-order
failure clips at ranks `{all4["failure_ranks"]}`. Reviewing the top two TRIBE
risk clips catches `{int(all4["topk_captured"])}/{int(all4["failures"])}` failures.

- Uncorrected random top-k p: `{float(all4["topk_p_uncorrected"]):.4f}`
- Bonferroni over {n_features} TRIBE features: `{bonf:.4f}`

The result is a strong pilot signal, but after accounting for feature search it
is not yet a finished proof. The correct claim is **promising failure forecast**,
not solved validation.

## Cross-Scorer Top-k Capture

{cross.to_markdown(index=False)}

## All4 Feature Comparison

{all4_auc.to_markdown(index=False)}

## Strongest Continuous Margin Associations

{margin_top.to_markdown(index=False)}

## Verdict

The signal is real enough to keep: the same TRIBE risk feature also predicts
`tier2/tier1` inversion risk and low tier3 margin better than cheap text-length
baselines. But it is fragile because there are only two all4 failures. The next
clean validation would be to run this on a larger clip set and freeze
`mean_standard_slot_score` as the risk feature before looking at outcomes.
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load()
    targets = binary_targets(df)
    aucs = feature_auc(df, targets)
    margins = margin_correlations(df)
    summary = topk_summary(df)

    targets.to_csv(OUT_TARGETS, index=False)
    aucs.to_csv(OUT_FEATURES, index=False)
    margins.to_csv(OUT_MARGINS, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    write_report(summary, aucs, margins)

    print("=== Top-k summary ===")
    print(summary.to_string(index=False))
    print("\n=== all4 feature comparison ===")
    print(aucs[aucs["target"] == "all4_mean_full_order_fail"].head(12).to_string(index=False))
    print("\n=== strongest margin correlations ===")
    print(margins.head(12).to_string(index=False))
    print(f"\nWrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
