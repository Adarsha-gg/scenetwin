#!/usr/bin/env python3
"""Make TRIBE native to SceneTwin as a routing/difficulty layer.

This analysis does not ask TRIBE to be the final AD quality scorer. Instead it
uses TRIBE's brain-model outputs to explain:

- how much AD a clip needs,
- whether the clip needs standard vs extended/integrated AD,
- whether professional AD length tracks neural accessibility pressure,
- whether high-need clips create larger quality separation between good/bad AD,
- where the current scoring stack struggles.
"""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr, spearmanr


ROOT = Path(__file__).resolve().parents[1]
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
BUNDLE_ZIP = ROOT / "output" / "scenetwin_description_gain_bundle.zip"
NEED_WINDOWS_CSV = TIMING_DIR / "need" / "coarse_need_windows.csv"
NEED_TR_CSV = TIMING_DIR / "need" / "neural_description_need_curve.csv"
SCORES_CSV = TIMING_DIR / "ensemble" / "bias_reduction_analysis.csv"
VLM_MERGED_CSV = TIMING_DIR / "ensemble" / "vlm_rater_merged_scores.csv"
OUT_DIR = TIMING_DIR / "tribe_native"
OUT_FEATURES = OUT_DIR / "tribe_clip_features.csv"
OUT_CORR = OUT_DIR / "tribe_native_correlations.csv"
OUT_FAILURES = OUT_DIR / "tribe_failure_routing.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-native-analysis.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-native-analysis.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]


def word_count(text: str) -> int:
    return len(re.findall(r"\w+", str(text or "")))


def load_metadata() -> pd.DataFrame:
    with zipfile.ZipFile(BUNDLE_ZIP) as zf:
        data = json.loads(zf.read("vatex_eval_clips.json"))
    rows = []
    for clip_idx, meta in enumerate(data):
        row = {
            "clip_idx": clip_idx,
            "video_id": meta.get("video_id", ""),
            "category": meta.get("category", ""),
        }
        for tier in TIERS:
            row[f"{tier}_words"] = word_count(meta.get(tier, ""))
            row[f"{tier}_text"] = str(meta.get(tier, "") or "")
        rows.append(row)
    out = pd.DataFrame(rows)
    out["pro_minus_short_words"] = out["tier3_va11y_words"] - out["tier1_vatex_short_words"]
    out["pro_minus_long_words"] = out["tier3_va11y_words"] - out["tier2_vatex_long_words"]
    return out


def normalized_entropy(values: np.ndarray) -> float:
    vals = np.asarray(values, dtype=float)
    vals = np.clip(vals, 0, None)
    if vals.sum() <= 1e-12:
        return 0.0
    p = vals / vals.sum()
    p = p[p > 1e-12]
    if len(p) <= 1:
        return 0.0
    return float(-(p * np.log2(p)).sum() / np.log2(len(vals)))


def tribe_clip_features() -> pd.DataFrame:
    windows = pd.read_csv(NEED_WINDOWS_CSV)
    tr = pd.read_csv(NEED_TR_CSV)
    rows = []
    for clip_idx, group in windows.groupby("clip_idx"):
        group = group.copy()
        group["duration"] = group["end_s"] - group["start_s"]
        duration = float(group["duration"].sum())
        high = group[group["recommendation"] != "low_ad_need"]
        extended = group[group["recommendation"] == "extended_or_integrated_ad"]
        standard = group[group["recommendation"] == "standard_ad_slot"]
        weighted_need = float(np.average(group["need_score"], weights=group["duration"])) if duration else float("nan")
        tr_clip = tr[tr["clip_idx"] == clip_idx]
        rows.append(
            {
                "clip_idx": int(clip_idx),
                "duration_s": duration,
                "mean_need": weighted_need,
                "max_need": float(group["need_score"].max()),
                "need_entropy": normalized_entropy(group["need_score"].to_numpy()),
                "high_need_windows": int(len(high)),
                "high_need_frac": float(len(high) / len(group)),
                "high_need_seconds": float(high["duration"].sum()),
                "high_need_seconds_frac": float(high["duration"].sum() / duration) if duration else 0.0,
                "standard_windows": int(len(standard)),
                "standard_seconds": float(standard["duration"].sum()),
                "extended_windows": int(len(extended)),
                "extended_seconds": float(extended["duration"].sum()),
                "extended_seconds_frac": float(extended["duration"].sum() / duration) if duration else 0.0,
                "mean_speech_density": float(np.average(group["speech_density"], weights=group["duration"])) if duration else float("nan"),
                "mean_standard_slot_score": float(tr_clip["standard_slot_score"].mean()) if len(tr_clip) else float("nan"),
                "mean_extended_need_score": float(tr_clip["extended_need_score"].mean()) if len(tr_clip) else float("nan"),
                "tribe_pressure": weighted_need * (1.0 + float(extended["duration"].sum() / duration) if duration else 1.0),
            }
        )
    return pd.DataFrame(rows)


def metric_clip_stats(scores: pd.DataFrame, metric: str) -> pd.DataFrame:
    rows = []
    for clip_idx, group in scores.groupby("clip_idx"):
        by = dict(zip(group["tier"], group[metric]))
        if not set(TIERS).issubset(by):
            continue
        lower = [by["tier0_cross"], by["tier1_vatex_short"], by["tier2_vatex_long"]]
        ordered = by["tier3_va11y"] > by["tier2_vatex_long"] > by["tier1_vatex_short"] > by["tier0_cross"]
        rows.append(
            {
                "clip_idx": int(clip_idx),
                f"{metric}_full_order": int(ordered),
                f"{metric}_tier3_margin": float(by["tier3_va11y"] - max(lower)),
                f"{metric}_tier3_vs_tier0": float(by["tier3_va11y"] - by["tier0_cross"]),
                f"{metric}_tier2_vs_tier1": float(by["tier2_vatex_long"] - by["tier1_vatex_short"]),
                f"{metric}_spread": float(max(by.values()) - min(by.values())),
            }
        )
    return pd.DataFrame(rows)


def load_score_features() -> pd.DataFrame:
    base = pd.read_csv(SCORES_CSV)
    metrics = ["clip_mean_norm", "all4_mean", "selected3_mean", "strict_all4_80adqa_20clip"]
    if VLM_MERGED_CSV.exists():
        vlm = pd.read_csv(VLM_MERGED_CSV)
        extra = [
            "claude_vlm_completeness_norm",
            "claude_vlm_specificity_norm",
            "vlm_best_dims_mean",
        ]
        keep = ["clip_idx", "tier", "gt", *[m for m in extra if m in vlm.columns]]
        base = base.merge(vlm[keep], on=["clip_idx", "tier", "gt"], how="left")
        metrics.extend([m for m in extra if m in base.columns])

    stats = None
    for metric in metrics:
        if metric not in base.columns:
            continue
        one = metric_clip_stats(base, metric)
        stats = one if stats is None else stats.merge(one, on="clip_idx", how="outer")
    return stats if stats is not None else pd.DataFrame({"clip_idx": []})


def correlations(df: pd.DataFrame) -> pd.DataFrame:
    tribe_cols = [
        "mean_need",
        "max_need",
        "high_need_seconds_frac",
        "extended_seconds_frac",
        "mean_speech_density",
        "mean_standard_slot_score",
        "mean_extended_need_score",
        "tribe_pressure",
    ]
    outcome_cols = [
        "tier3_va11y_words",
        "pro_minus_short_words",
        "pro_minus_long_words",
        "all4_mean_tier3_margin",
        "all4_mean_tier3_vs_tier0",
        "all4_mean_tier2_vs_tier1",
        "strict_all4_80adqa_20clip_tier3_margin",
        "claude_vlm_completeness_norm_tier3_margin",
        "claude_vlm_specificity_norm_tier3_margin",
    ]
    rows = []
    for a in tribe_cols:
        if a not in df.columns:
            continue
        for b in outcome_cols:
            if b not in df.columns:
                continue
            sub = df[[a, b]].dropna()
            if len(sub) < 4 or sub[a].nunique() < 2 or sub[b].nunique() < 2:
                continue
            rho, p = spearmanr(sub[a], sub[b])
            rows.append({"tribe_feature": a, "outcome": b, "spearman_rho": float(rho), "p": float(p), "n": int(len(sub))})
    for metric in ["all4_mean_full_order", "strict_all4_80adqa_20clip_full_order"]:
        if metric not in df.columns:
            continue
        for feature in tribe_cols:
            sub = df[[feature, metric]].dropna()
            if len(sub) >= 4 and sub[metric].nunique() == 2 and sub[feature].nunique() >= 2:
                r, p = pointbiserialr(sub[metric], sub[feature])
                rows.append({"tribe_feature": feature, "outcome": metric, "spearman_rho": float(r), "p": float(p), "n": int(len(sub))})
    return pd.DataFrame(rows).sort_values("spearman_rho", key=lambda s: s.abs(), ascending=False)


def routing_table(df: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "clip_idx",
        "category",
        "duration_s",
        "mean_need",
        "max_need",
        "high_need_seconds_frac",
        "extended_seconds_frac",
        "tribe_pressure",
        "tier3_va11y_words",
        "all4_mean_full_order",
        "all4_mean_tier3_margin",
        "all4_mean_tier2_vs_tier1",
        "claude_vlm_specificity_norm_tier3_margin",
    ]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    out["tribe_route"] = np.select(
        [
            out["extended_seconds_frac"] >= 0.45,
            out["high_need_seconds_frac"] >= 0.45,
            out["mean_need"] >= 0.45,
        ],
        [
            "extended/integrated AD likely needed",
            "standard AD priority",
            "spot-check high-need moments",
        ],
        default="low/normal AD pressure",
    )
    if "all4_mean_tier3_margin" in out.columns:
        out["quality_risk"] = np.select(
            [
                out["all4_mean_tier3_margin"] < 0.05,
                out["all4_mean_tier2_vs_tier1"] < 0,
            ],
            ["professional AD barely leads", "tier2/tier1 inversion risk"],
            default="clean",
        )
    return out.sort_values(["tribe_pressure", "high_need_seconds_frac"], ascending=False)


def write_report(features: pd.DataFrame, corr: pd.DataFrame, routing: pd.DataFrame) -> None:
    top_corr = corr.head(16) if not corr.empty else corr
    top_routes = routing.head(14)
    failure_rows = routing[routing.get("quality_risk", "") != "clean"].head(14)
    route_counts = routing["tribe_route"].value_counts().rename_axis("route").reset_index(name="clips")

    report = f"""---
title: "SceneTwin TRIBE Native Analysis"
category: research
tags: [SceneTwin, TRIBE, brain-model, routing, accessibility]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/need/coarse_need_windows.csv
  - output/scenetwin_timing_20clip/need/neural_description_need_curve.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_clip_features.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_native_correlations.csv
---

# SceneTwin TRIBE Native Analysis

## Role

TRIBE is the brain-model layer for **accessibility pressure and routing**.
It says where the soundtrack fails to carry the audiovisual scene and whether
the clip likely needs standard AD, extended/integrated AD, or only spot checks.

This makes TRIBE native without forcing it to be the final text scorer:

```text
TRIBE: how much / when / what kind of AD is needed
CLIP/VLM: whether text is visually grounded
ADQA: whether text supports comprehension
```

## Route Counts

{route_counts.to_markdown(index=False)}

## Highest TRIBE-Pressure Clips

{top_routes.to_markdown(index=False)}

## Strongest Associations

{top_corr.to_markdown(index=False)}

## Quality-Risk Clips Explained By TRIBE

{failure_rows.to_markdown(index=False)}

## Interpretation

TRIBE gives SceneTwin a native product layer that the pure VLM/ADQA stack lacks:
it can justify **why** a clip needs more description and where the AD should be
inserted. The quality scorers say which candidate wins; TRIBE says whether the
clip needs standard AD, extended/integrated AD, or only focused high-need checks.

The next useful experiment is to feed `tribe_route`, high-need windows, and
dominant missing content type into the generator, then re-run:

1. TRIBE text-feel audit.
2. VLM direct rater.
3. ADQA.
4. Optional Colab neural closure: `P_A+AD` vs `P_AV`.
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    features = tribe_clip_features()
    meta = load_metadata()
    scores = load_score_features()
    merged = features.merge(meta, on="clip_idx", how="left").merge(scores, on="clip_idx", how="left")
    corr = correlations(merged)
    routing = routing_table(merged)

    merged.to_csv(OUT_FEATURES, index=False)
    corr.to_csv(OUT_CORR, index=False)
    routing.to_csv(OUT_FAILURES, index=False)
    write_report(merged, corr, routing)

    print("Route counts:")
    print(routing["tribe_route"].value_counts().to_string())
    print("\nTop correlations:")
    print(corr.head(12).to_string(index=False))
    print(f"\nWrote {OUT_FEATURES}")
    print(f"Wrote {OUT_CORR}")
    print(f"Wrote {OUT_FAILURES}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
