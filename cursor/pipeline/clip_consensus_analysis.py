#!/usr/bin/env python3
"""Analyze a conservative two-CLIP consensus signal from cached scores."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "cursor/output/benchmark_clip_sanity.csv"
OUTPUT = ROOT / "cursor/output/clip_consensus_analysis.json"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
GT = {tier: i for i, tier in enumerate(TIERS)}


def _metric_block(df: pd.DataFrame, score_col: str) -> dict:
    rho = float(spearmanr(df["gt_num"], df[score_col], nan_policy="omit")[0])
    full_order = 0
    adjacent_wins = 0
    all_pairwise_wins = 0
    pro_beats_short = 0
    cross_lowest = 0

    for _, group in df.groupby("clip_idx"):
        scores = dict(zip(group["tier"], group[score_col]))
        full_order += int(all(scores[TIERS[i]] < scores[TIERS[i + 1]] for i in range(3)))
        pro_beats_short += int(scores["tier3_va11y"] > scores["tier1_vatex_short"])
        cross_lowest += int(scores["tier0_cross"] == min(scores.values()))
        adjacent_wins += sum(scores[TIERS[i + 1]] > scores[TIERS[i]] for i in range(3))
        all_pairwise_wins += sum(
            scores[TIERS[j]] > scores[TIERS[i]]
            for i in range(len(TIERS))
            for j in range(i + 1, len(TIERS))
        )

    n_clips = int(df["clip_idx"].nunique())
    return {
        "spearman_rho": rho,
        "full_order": int(full_order),
        "full_order_total": n_clips,
        "adjacent_wins": int(adjacent_wins),
        "adjacent_total": n_clips * 3,
        "all_pairwise_wins": int(all_pairwise_wins),
        "all_pairwise_total": n_clips * 6,
        "pro_beats_short": int(pro_beats_short),
        "pro_beats_short_total": n_clips,
        "cross_lowest": int(cross_lowest),
        "cross_lowest_total": n_clips,
    }


def _auc_bad_low(df: pd.DataFrame, score_col: str) -> float:
    bad = df.loc[df["tier"] == "tier0_cross", score_col].to_numpy()
    good = df.loc[df["tier"] != "tier0_cross", score_col].to_numpy()
    wins = 0
    ties = 0
    for score in bad:
        wins += int(np.sum(score < good))
        ties += int(np.sum(score == good))
    return float((wins + 0.5 * ties) / (len(bad) * len(good)))


def _loco_gate(df: pd.DataFrame, score_col: str, target_fpr: float = 0.10) -> dict:
    catches: list[bool] = []
    false_rejects: list[bool] = []

    for clip_idx in sorted(df["clip_idx"].unique()):
        train = df["clip_idx"] != clip_idx
        test = ~train
        train_good = df.loc[train & (df["tier"] != "tier0_cross"), score_col]
        train_bad = df.loc[train & (df["tier"] == "tier0_cross"), score_col]

        best: tuple[float, float] | None = None
        for tau in sorted(df.loc[train, score_col].unique()):
            fpr = float((train_good <= tau).mean())
            if fpr > target_fpr:
                continue
            catch = float((train_bad <= tau).mean())
            if best is None or (catch, tau) > best:
                best = (catch, float(tau))

        tau = best[1] if best else float(df.loc[train, score_col].min() - 1e-12)
        pred = df.loc[test, score_col] <= tau
        catches.extend(pred[df.loc[test, "tier"] == "tier0_cross"].tolist())
        false_rejects.extend(pred[df.loc[test, "tier"] != "tier0_cross"].tolist())

    return {
        "target_fpr": target_fpr,
        "catch": float(np.mean(catches)),
        "false_reject": float(np.mean(false_rejects)),
    }


def main() -> None:
    df = pd.read_csv(INPUT)
    df["gt_num"] = df["tier"].map(GT)
    if df["gt_num"].isna().any():
        missing = sorted(df.loc[df["gt_num"].isna(), "tier"].unique())
        raise ValueError(f"Unknown tiers in {INPUT}: {missing}")

    df["clip_consensus_min"] = np.minimum(df["ours"], df["benchmark"])

    metrics = {}
    for col in ["ours", "benchmark", "clip_consensus_min"]:
        metrics[col] = _metric_block(df, col)
        metrics[col]["wrong_content_auc_bad_low"] = _auc_bad_low(df, col)
        metrics[col]["wrong_content_loco_gate"] = _loco_gate(df, col)

    report = {
        "input": str(INPUT.relative_to(ROOT)),
        "signal": "clip_consensus_min = min(SceneTwin CLIP score, benchmark CLIP score)",
        "n_clips": int(df["clip_idx"].nunique()),
        "n_rows": int(len(df)),
        "metrics": metrics,
        "interpretation": (
            "The consensus floor is a conservative CLIP-only agreement check. "
            "It is slightly stronger than either individual scorer on rho/false-reject, "
            "but the lift is too small to call a breakthrough."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
