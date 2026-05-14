#!/usr/bin/env python3
"""Validate TRIBE as a policy router for SceneTwin scorers.

TRIBE should not be treated as a generic text scorer. Its native strength is
multimodal brain-state prediction: it can characterize the clip, then route the
evaluation stack toward the scorer that works best for that kind of clip.

This script tests that claim without API calls:

1. Build candidate policies from TRIBE clip features.
2. Choose each policy using only training clips.
3. Apply the chosen policy to the held-out clip.
4. Compare against non-TRIBE single scorers and same-set upper bounds.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
SCORES_CSV = TIMING_DIR / "ensemble" / "vlm_rater_merged_scores.csv"
TRIBE_CSV = TIMING_DIR / "tribe_native" / "tribe_clip_features.csv"
OUT_DIR = TIMING_DIR / "tribe_native"
OUT_PRED = OUT_DIR / "tribe_policy_loocv_scores.csv"
OUT_SUMMARY = OUT_DIR / "tribe_policy_validation_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-policy-validation.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-policy-validation.md"

TRIBE_FEATURES = [
    "mean_need",
    "max_need",
    "need_entropy",
    "high_need_frac",
    "high_need_seconds_frac",
    "extended_seconds_frac",
    "mean_speech_density",
    "mean_standard_slot_score",
    "mean_extended_need_score",
    "tribe_pressure",
]

BASE_METRICS = [
    "all4_mean",
    "selected3_mean",
    "strict_all4_80adqa_20clip",
    "clip_mean_norm",
    "claude_vlm_completeness_norm",
    "claude_vlm_specificity_norm",
    "vlm_best_dims_mean",
]


def evaluate(df: pd.DataFrame, col: str) -> dict[str, object]:
    rho = spearmanr(df["gt"], df[col]).statistic
    tau = kendalltau(df["gt"], df[col]).statistic
    wins = total = full = 0
    for _, group in df.groupby("clip_idx"):
        by = dict(zip(group["tier"], group[col]))
        if not {"tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"}.issubset(by):
            continue
        for tier in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
            total += 1
            wins += int(by["tier3_va11y"] > by[tier])
        full += int(by["tier3_va11y"] > by["tier2_vatex_long"] > by["tier1_vatex_short"] > by["tier0_cross"])
    return {
        "rho": float(rho),
        "tau": float(tau),
        "wins": f"{wins}/{total}",
        "full": f"{full}/{df['clip_idx'].nunique()}",
    }


def load_data() -> pd.DataFrame:
    scores = pd.read_csv(SCORES_CSV)
    features = pd.read_csv(TRIBE_CSV)
    metrics = [m for m in BASE_METRICS if m in scores.columns]
    missing = sorted(set(BASE_METRICS) - set(metrics))
    if missing:
        print(f"Skipping missing metrics: {missing}")
    keep = ["clip_idx", "tier", "gt", *metrics]
    df = scores[keep].merge(features[["clip_idx", *[f for f in TRIBE_FEATURES if f in features.columns]]], on="clip_idx")
    return df


def policy_score(df: pd.DataFrame, policy: dict[str, object]) -> pd.Series:
    kind = str(policy["kind"])
    if kind == "single":
        return df[str(policy["metric"])]
    if kind == "blend":
        w = float(policy["w"])
        return w * df[str(policy["a"])] + (1.0 - w) * df[str(policy["b"])]
    if kind == "hard_gate":
        feature = str(policy["feature"])
        high = str(policy["high"])
        low = str(policy["low"])
        threshold = float(policy["threshold"])
        return np.where(df[feature] >= threshold, df[high], df[low])
    if kind == "soft_gate":
        feature = str(policy["feature"])
        high = str(policy["high"])
        low = str(policy["low"])
        values = df[feature].astype(float)
        lo = float(policy["lo"])
        hi = float(policy["hi"])
        if hi <= lo:
            weight = pd.Series(np.zeros(len(df)), index=df.index)
        else:
            weight = ((values - lo) / (hi - lo)).clip(0.0, 1.0)
        return weight * df[high] + (1.0 - weight) * df[low]
    raise ValueError(f"unknown policy kind: {kind}")


def candidate_policies(train: pd.DataFrame) -> list[dict[str, object]]:
    metrics = [m for m in BASE_METRICS if m in train.columns]
    features = [f for f in TRIBE_FEATURES if f in train.columns and train[f].nunique() > 1]
    policies: list[dict[str, object]] = [{"kind": "single", "metric": m, "name": m} for m in metrics]

    for a in metrics:
        for b in metrics:
            if a == b:
                continue
            for w_i in range(0, 101, 5):
                w = w_i / 100
                policies.append({"kind": "blend", "a": a, "b": b, "w": w, "name": f"blend:{a}:{b}:{w:.2f}"})

    for feature in features:
        thresholds = sorted(set(float(x) for x in train.groupby("clip_idx")[feature].first().quantile([0.25, 0.33, 0.5, 0.67, 0.75]).to_numpy()))
        lo = float(train[feature].min())
        hi = float(train[feature].max())
        for high in metrics:
            for low in metrics:
                if high == low:
                    continue
                for threshold in thresholds:
                    policies.append(
                        {
                            "kind": "hard_gate",
                            "feature": feature,
                            "threshold": threshold,
                            "high": high,
                            "low": low,
                            "name": f"gate:{feature}>={threshold:.3f}:{high}:{low}",
                        }
                    )
                policies.append(
                    {
                        "kind": "soft_gate",
                        "feature": feature,
                        "lo": lo,
                        "hi": hi,
                        "high": high,
                        "low": low,
                        "name": f"soft:{feature}:{high}:{low}",
                    }
                )
    return policies


def select_policy(train: pd.DataFrame) -> tuple[dict[str, object], dict[str, object]]:
    best_policy: dict[str, object] | None = None
    best_metrics: dict[str, object] | None = None
    best_key = (-np.inf, -np.inf, -np.inf)
    for policy in candidate_policies(train):
        col = "_candidate_score"
        tmp = train.copy()
        tmp[col] = policy_score(tmp, policy)
        metrics = evaluate(tmp, col)
        wins_num = int(str(metrics["wins"]).split("/")[0])
        full_num = int(str(metrics["full"]).split("/")[0])
        key = (float(metrics["rho"]), float(metrics["tau"]), wins_num + full_num / 100)
        if key > best_key:
            best_key = key
            best_policy = policy
            best_metrics = metrics
    if best_policy is None or best_metrics is None:
        raise RuntimeError("no policy selected")
    return best_policy, best_metrics


def loocv(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pred_rows = []
    choices = []
    for holdout in sorted(df["clip_idx"].unique()):
        train = df[df["clip_idx"] != holdout].copy()
        test = df[df["clip_idx"] == holdout].copy()
        policy, train_metrics = select_policy(train)
        test["tribe_policy_loocv"] = policy_score(test, policy)
        test["selected_policy"] = str(policy["name"])
        pred_rows.append(test[["clip_idx", "tier", "gt", "tribe_policy_loocv", "selected_policy"]])
        choices.append(
            {
                "holdout_clip": int(holdout),
                "selected_policy": str(policy["name"]),
                "train_rho": train_metrics["rho"],
                "train_tau": train_metrics["tau"],
                "train_wins": train_metrics["wins"],
                "train_full": train_metrics["full"],
            }
        )
    return pd.concat(pred_rows, ignore_index=True), pd.DataFrame(choices)


def same_set_best(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for policy in candidate_policies(df):
        tmp = df.copy()
        tmp["_score"] = policy_score(tmp, policy)
        rows.append({"metric": str(policy["name"]), **evaluate(tmp, "_score")})
    return pd.DataFrame(rows).sort_values(["rho", "tau"], ascending=False)


def write_report(summary: pd.DataFrame, choices: pd.DataFrame) -> None:
    top_same_set = summary[summary["kind"] == "same_set_upper_bound"].head(8)
    loocv_rows = summary[summary["kind"].isin(["loocv", "baseline"])].copy()
    common = choices["selected_policy"].value_counts().rename_axis("selected_policy").reset_index(name="folds")
    report = f"""---
title: "SceneTwin TRIBE Policy Validation"
category: research
tags: [SceneTwin, TRIBE, routing, validation, VLM, ADQA]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_policy_loocv_scores.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_policy_validation_summary.csv
---

# SceneTwin TRIBE Policy Validation

## Why This Test Exists

TRIBE is strongest as a multimodal brain encoder, not a standalone text-quality
metric. This test uses TRIBE clip features as a policy router: choose which
SceneTwin scorer to trust for each clip type, then evaluate the held-out clip.

## Held-Out Results

{loocv_rows.to_markdown(index=False)}

## Same-Set Upper Bound

These are useful for exploration only; they are tuned on the same 18 clips.

{top_same_set.to_markdown(index=False)}

## LOOCV Selected Policies

{common.to_markdown(index=False)}

## Fold Choices

{choices.to_markdown(index=False)}

## Verdict

TRIBE helps most as a router when the policy is allowed to be tuned on the same
set. The stricter leave-one-clip-out test is the number to trust, and here it
does **not** beat the best non-TRIBE single scorer.

The honest conclusion is therefore:

- Keep TRIBE native to SceneTwin as an accessibility-pressure, timing, and
  scorer-routing analysis layer.
- Do not claim TRIBE as the main score booster yet.
- Treat the same-set `rho=0.968` policy result as an exploration target that
  needs more clips or an external validation split before it becomes a headline.
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = load_data()
    preds, choices = loocv(df)
    scored = df.merge(preds, on=["clip_idx", "tier", "gt"])
    scored.to_csv(OUT_PRED, index=False)

    rows = []
    for metric in [m for m in BASE_METRICS if m in df.columns]:
        rows.append({"kind": "baseline", "metric": metric, **evaluate(df, metric)})
    rows.append({"kind": "loocv", "metric": "tribe_policy_loocv", **evaluate(scored, "tribe_policy_loocv")})
    upper = same_set_best(df).head(20)
    for row in upper.to_dict("records"):
        rows.append({"kind": "same_set_upper_bound", **row})
    summary = pd.DataFrame(rows).sort_values(["kind", "rho"], ascending=[True, False])
    summary.to_csv(OUT_SUMMARY, index=False)
    write_report(summary, choices)

    print("=== Summary ===")
    print(summary.to_string(index=False))
    print("\n=== LOOCV choices ===")
    print(choices.to_string(index=False))
    print(f"\nWrote {OUT_PRED}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
