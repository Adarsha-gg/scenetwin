#!/usr/bin/env python3
"""Test cheap proxies vs full TRIBE features for failure forecasting."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "efficiency_proxy_sweep.csv"

PROXY_FEATURES = [
    "mean_speech_density",
    "high_need_seconds_frac",
    "mean_standard_slot_score",
    "tribe_pressure",
    "mean_need",
]

CLIP_FEATURES = [
    "clip_top3",
    "clip_mean",
    "adqa_v2_score",
]

CHEAP_COMBOS = [
    ("speech_only", ["mean_speech_density"]),
    ("need_frac_only", ["high_need_seconds_frac"]),
    ("speech_x_need", ["mean_speech_density", "high_need_seconds_frac"]),
    ("slot_score_only", ["mean_standard_slot_score"]),
    ("clip_top3_clip", []),  # filled per-clip from scores
]


def clip_level_clip_features() -> pd.DataFrame:
    s = pd.read_csv(TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv")
    pro = s[s["tier"] == "tier3_va11y"][["clip_idx", "clip_top3", "clip_mean", "adqa_v2_score"]]
    return pro.rename(columns={
        "clip_top3": "pro_clip_top3",
        "clip_mean": "pro_clip_mean",
        "adqa_v2_score": "pro_adqa",
    })


def main() -> None:
    df = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    df["all4_fail"] = (1 - df["all4_mean_full_order"]).astype(int)
    clip_feats = clip_level_clip_features()
    df = df.merge(clip_feats, on="clip_idx", how="left")

    y = df["all4_fail"]
    rows = []

    for feat in PROXY_FEATURES + ["pro_clip_top3", "pro_clip_mean", "pro_adqa"]:
        if feat not in df.columns:
            continue
        x = df[feat].astype(float).fillna(0)
        auc = roc_auc_score(y, x) if y.nunique() > 1 else float("nan")
        rho, p = spearmanr(x, df["all4_mean_full_order"])
        rows.append({
            "feature": feat,
            "roc_auc_fail": auc,
            "rho_vs_judge_order": float(rho),
            "p": float(p),
            "n_params": 1,
            "needs_tribe_forward": feat in PROXY_FEATURES,
        })

    # Combined cheap proxy: z(speech)*z(need) inverted
    z_sp = (df["mean_speech_density"] - df["mean_speech_density"].mean()) / (df["mean_speech_density"].std() + 1e-9)
    z_nd = (df["high_need_seconds_frac"] - df["high_need_seconds_frac"].mean()) / (df["high_need_seconds_frac"].std() + 1e-9)
    combo = z_nd - z_sp  # high need + low speech = risky
    auc = roc_auc_score(y, combo)
    rho, p = spearmanr(combo, df["all4_mean_full_order"])
    rows.append({
        "feature": "cheap_need_minus_speech_z",
        "roc_auc_fail": auc,
        "rho_vs_judge_order": float(rho),
        "p": float(p),
        "n_params": 2,
        "needs_tribe_forward": True,
    })

    # Ultra-cheap: no TRIBE — motion proxy from category (Sports=1)
    df["is_sports"] = (df["category"] == "Sports").astype(float)
    auc = roc_auc_score(y, df["is_sports"])
    rows.append({
        "feature": "category_sports_heuristic",
        "roc_auc_fail": auc,
        "rho_vs_judge_order": float(spearmanr(df["is_sports"], df["all4_mean_full_order"])[0]),
        "p": float(spearmanr(df["is_sports"], df["all4_mean_full_order"])[1]),
        "n_params": 1,
        "needs_tribe_forward": False,
    })

    out = pd.DataFrame(rows).sort_values("roc_auc_fail", ascending=False)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"\nWrote {OUT}")

    best = out.iloc[0]
    tribe_best = out[out["needs_tribe_forward"]].iloc[0]
    print(f"\nBest overall: {best['feature']} AUC={best['roc_auc_fail']:.3f}")
    print(f"Best TRIBE feature: {tribe_best['feature']} AUC={tribe_best['roc_auc_fail']:.3f}")


if __name__ == "__main__":
    main()
