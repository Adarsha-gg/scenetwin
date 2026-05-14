#!/usr/bin/env python3
"""Trajectory metrics for saved TRIBE description tensors.

Whole-cortex time-averaged cosine throws away temporal order. This script tests
whether a description's predicted cortical trajectory follows the original AV
trajectory after resampling/DTW alignment.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
PRED_DIR = DG_DIR / "preds"
OUT_CSV = DG_DIR / "trajectory_metrics_results.csv"
OUT_SUMMARY = DG_DIR / "trajectory_metrics_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-trajectory-metrics.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-trajectory-metrics.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
GT = {"tier3_va11y": 3, "tier2_vatex_long": 2, "tier1_vatex_short": 1, "tier0_cross": 0}
COMPS = ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
N_PROJ_DIMS = 256
RNG_SEED = 11


def load_pred(name: str) -> np.ndarray:
    x = np.load(PRED_DIR / f"{name}.npy").astype(np.float32)
    return np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a / np.maximum(np.linalg.norm(a, axis=1, keepdims=True), 1e-9)
    b = b / np.maximum(np.linalg.norm(b, axis=1, keepdims=True), 1e-9)
    return a @ b.T


def resample_sequence(x: np.ndarray, n: int) -> np.ndarray:
    if len(x) == n:
        return x
    if len(x) == 1:
        return np.repeat(x, n, axis=0)
    src = np.linspace(0.0, 1.0, len(x))
    dst = np.linspace(0.0, 1.0, n)
    out = np.empty((n, x.shape[1]), dtype=np.float32)
    for j in range(x.shape[1]):
        out[:, j] = np.interp(dst, src, x[:, j])
    return out


def random_projection(*arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    n_vertices = arrays[0].shape[1]
    rng = np.random.default_rng(RNG_SEED)
    proj = rng.normal(size=(n_vertices, N_PROJ_DIMS)).astype(np.float32)
    proj /= np.sqrt(N_PROJ_DIMS)
    return tuple(a @ proj for a in arrays)


def dtw_similarity(a: np.ndarray, b: np.ndarray) -> float:
    sims = cosine_matrix(a, b)
    costs = 1.0 - sims
    n, m = costs.shape
    dp = np.full((n + 1, m + 1), np.inf, dtype=np.float32)
    dp[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i, j] = costs[i - 1, j - 1] + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])
    avg_cost = float(dp[n, m] / (n + m))
    return 1.0 - avg_cost


def trajectory_shift(x: np.ndarray) -> np.ndarray:
    if len(x) < 2:
        return np.zeros(1, dtype=np.float32)
    sims = np.diag(cosine_matrix(x[:-1], x[1:]))
    return (1.0 - sims).astype(np.float32)


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    rho, p_rho = spearmanr(df["gt"], df[metric], nan_policy="omit")
    tau, p_tau = kendalltau(df["gt"], df[metric], nan_policy="omit")
    out: dict[str, object] = {
        "metric": metric,
        "spearman_rho": float(rho),
        "spearman_p": float(p_rho),
        "kendall_tau": float(tau),
        "kendall_p": float(p_tau),
    }
    wins_total = 0
    pair_total = 0
    for comp in COMPS:
        wins = 0
        total = 0
        for _, group in df.groupby("clip_idx"):
            t3 = group[group["tier"] == "tier3_va11y"][metric]
            tx = group[group["tier"] == comp][metric]
            if len(t3) and len(tx):
                total += 1
                wins += int(float(t3.iloc[0]) > float(tx.iloc[0]))
        out[f"tier3_gt_{comp}_wins"] = wins
        out[f"tier3_gt_{comp}_total"] = total
        wins_total += wins
        pair_total += total
    out["pairwise_wins"] = wins_total
    out["pairwise_total"] = pair_total
    full = 0
    for _, group in df.groupby("clip_idx"):
        vals = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        full += int(vals["tier3_va11y"] > vals["tier2_vatex_long"] > vals["tier1_vatex_short"] > vals["tier0_cross"])
    out["full_order_clips"] = full
    out["full_order_total"] = int(df["clip_idx"].nunique())
    return out


def available_clip_indices() -> list[int]:
    clips = []
    for p_av in sorted(PRED_DIR.glob("clip_*_P_AV.npy")):
        clip_idx = int(p_av.name.split("_")[1])
        clips.append(clip_idx)
    return clips


def main() -> None:
    rows = []
    for clip_idx in available_clip_indices():
        av = load_pred(f"clip_{clip_idx:02d}_P_AV")
        audio = load_pred(f"clip_{clip_idx:02d}_P_A")
        av_p, audio_p = random_projection(av, audio)
        av_shift = trajectory_shift(av_p)

        for tier in TIER_KEYS:
            desc = load_pred(f"clip_{clip_idx:02d}_{tier}_P_D")
            desc_p = random_projection(desc)[0]
            desc_resampled = resample_sequence(desc_p, len(av_p))
            desc_shift = trajectory_shift(desc_resampled)
            sims = np.diag(cosine_matrix(av_p, desc_resampled))
            audio_sims = np.diag(cosine_matrix(audio_p, desc_resampled))
            shift_corr = float(np.corrcoef(av_shift, desc_shift)[0, 1]) if len(av_shift) > 1 else float("nan")
            rows.append(
                {
                    "clip_idx": clip_idx,
                    "tier": tier,
                    "gt": GT[tier],
                    "resampled_traj_cos": float(np.nanmean(sims)),
                    "resampled_traj_gain_vs_audio": float(np.nanmean(sims - audio_sims)),
                    "dtw_traj_similarity": dtw_similarity(av_p, desc_p),
                    "shift_curve_corr": shift_corr,
                    "desc_steps": int(len(desc)),
                    "av_steps": int(len(av)),
                }
            )

    out = pd.DataFrame(rows)
    metrics = [
        "resampled_traj_cos",
        "resampled_traj_gain_vs_audio",
        "dtw_traj_similarity",
        "shift_curve_corr",
    ]
    summary = pd.DataFrame([evaluate(out, metric) for metric in metrics]).sort_values(
        ["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False
    )
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    means = out.groupby("tier")[metrics].mean().loc[TIER_KEYS]
    report = f"""---
title: "SceneTwin TRIBE Trajectory Metrics"
category: research
tags: [SceneTwin, TRIBE, trajectories, DTW, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/trajectory_metrics_results.csv
  - output/scenetwin_description_gain/trajectory_metrics_summary.csv
  - output/scenetwin_description_gain/preds/
---

# SceneTwin TRIBE Trajectory Metrics

## Question

Do temporal TRIBE trajectory metrics recover AD quality better than whole-cortex average cosine?

## Metrics

- `resampled_traj_cos`: resample description trajectory to AV length, then average per-step cosine.
- `resampled_traj_gain_vs_audio`: same, but subtract audio-only similarity.
- `dtw_traj_similarity`: dynamic time warping similarity between AV and description trajectories.
- `shift_curve_corr`: correlation between AV state-change curve and description state-change curve.

All metrics use a fixed random projection to 256 dimensions for speed.

## Summary

{summary.to_markdown(index=False)}

## Mean Scores By Tier

{means.to_markdown()}

## Verdict

This is useful as a diagnostic, but it is not yet the headline metric. On two clips, trajectory metrics do not clearly beat need-weighted visual grounding. The main value is catching descriptions that are semantically right but temporally out of order, which needs a larger test set.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(out)
    print()
    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
