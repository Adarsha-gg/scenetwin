#!/usr/bin/env python3
"""Permutation null baselines for SceneTwin metric files."""

from __future__ import annotations

from pathlib import Path
from itertools import product, permutations

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
OUT_CSV = DG_DIR / "metric_null_baselines.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-metric-null-baselines.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-metric-null-baselines.md"

MAX_EXACT_PERMUTATIONS = 100000
N_SAMPLED_PERMUTATIONS = 2000
SEED = 17
METRIC_FILES = {
    "need_weighted_grounding": DG_DIR / "need_weighted_grounding_results.csv",
    "trajectory_metrics": DG_DIR / "trajectory_metrics_results.csv",
    "ocr_coverage": DG_DIR / "ocr_coverage_test_results.csv",
}
IGNORE_COLS = {"clip_idx", "tier", "gt", "ocr_windows", "desc_steps", "av_steps"}
TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]


def full_order_count(df: pd.DataFrame, metric: str) -> int:
    full = 0
    for _, group in df.groupby("clip_idx"):
        vals = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        if all(k in vals for k in TIER_KEYS):
            full += int(vals["tier3_va11y"] > vals["tier2_vatex_long"] > vals["tier1_vatex_short"] > vals["tier0_cross"])
    return full


def pairwise_wins(df: pd.DataFrame, metric: str) -> int:
    wins = 0
    for _, group in df.groupby("clip_idx"):
        vals = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        if "tier3_va11y" not in vals:
            continue
        for comp in ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]:
            if comp in vals:
                wins += int(vals["tier3_va11y"] > vals[comp])
    return wins


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, float]:
    valid = df[np.isfinite(df[metric])]
    if valid.empty or valid[metric].nunique() <= 1:
        return {
            "spearman_rho": float("nan"),
            "kendall_tau": float("nan"),
            "pairwise_wins": float("nan"),
            "full_order_clips": float("nan"),
        }
    rho, _ = spearmanr(valid["gt"], valid[metric], nan_policy="omit")
    tau, _ = kendalltau(valid["gt"], valid[metric], nan_policy="omit")
    return {
        "spearman_rho": float(rho),
        "kendall_tau": float(tau),
        "pairwise_wins": float(pairwise_wins(valid, metric)),
        "full_order_clips": float(full_order_count(valid, metric)),
    }


def metric_columns(df: pd.DataFrame) -> list[str]:
    out = []
    for col in df.columns:
        if col in IGNORE_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[col]) and np.isfinite(df[col]).sum() >= 4:
            out.append(col)
    return out


def null_dfs(df: pd.DataFrame, metric: str, rng: np.random.Generator):
    groups = [(clip_idx, list(idx)) for clip_idx, idx in df.groupby("clip_idx").groups.items()]
    choices = []
    total = 1
    for _, idx in groups:
        vals = tuple(df.loc[idx, metric].to_numpy())
        perms = list(permutations(vals))
        choices.append(perms)
        total *= len(perms)

    if total <= MAX_EXACT_PERMUTATIONS:
        for combo in product(*choices):
            shuffled = df.copy()
            for (_, idx), vals in zip(groups, combo):
                shuffled.loc[idx, metric] = vals
            yield shuffled
        return

    for _ in range(N_SAMPLED_PERMUTATIONS):
        shuffled = df.copy()
        for _, idx in groups:
            shuffled.loc[idx, metric] = rng.permutation(shuffled.loc[idx, metric].to_numpy())
        yield shuffled


def main() -> None:
    rng = np.random.default_rng(SEED)
    rows = []
    for source, path in METRIC_FILES.items():
        if not path.exists():
            continue
        df = pd.read_csv(path)
        for metric in metric_columns(df):
            observed = evaluate(df, metric)
            null_rho = []
            null_pairwise = []
            null_full = []
            n_permutations = 0
            for perm in null_dfs(df, metric, rng):
                n_permutations += 1
                stats = evaluate(perm, metric)
                if np.isfinite(stats["spearman_rho"]):
                    null_rho.append(stats["spearman_rho"])
                    null_pairwise.append(stats["pairwise_wins"])
                    null_full.append(stats["full_order_clips"])

            null_rho_np = np.asarray(null_rho, dtype=float)
            null_pairwise_np = np.asarray(null_pairwise, dtype=float)
            null_full_np = np.asarray(null_full, dtype=float)
            rows.append(
                {
                    "source": source,
                    "metric": metric,
                    **observed,
                    "null_spearman_mean": float(np.nanmean(null_rho_np)),
                    "null_spearman_p_ge_observed": float(np.mean(null_rho_np >= observed["spearman_rho"])),
                    "null_pairwise_mean": float(np.nanmean(null_pairwise_np)),
                    "null_pairwise_p_ge_observed": float(np.mean(null_pairwise_np >= observed["pairwise_wins"])),
                    "null_full_order_mean": float(np.nanmean(null_full_np)),
                    "null_full_order_p_ge_observed": float(np.mean(null_full_np >= observed["full_order_clips"])),
                    "n_permutations": n_permutations,
                }
            )

    out = pd.DataFrame(rows).sort_values(
        ["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False
    )
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    top = out.head(20)
    report = f"""---
title: "SceneTwin Metric Null Baselines"
category: research
tags: [SceneTwin, statistics, permutation-test, metrics]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/metric_null_baselines.csv
---

# SceneTwin Metric Null Baselines

## Method

For each metric file, keep quality labels fixed and shuffle each metric's values within each clip. For the current two-clip dataset this enumerates the exact `4! x 4! = 576` within-clip metric permutations. This gives a small-sample null for Spearman, tier3 pairwise wins, and full-order clips.

## Top Results

{top.to_markdown(index=False)}

## Caveat

This is still an `n=2` smoke test. The null prevents pure hand-waving, but it does not replace the 20-clip run.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(top)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
