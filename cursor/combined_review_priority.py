#!/usr/bin/env python3
"""Composite human-review priority: TRIBE risk × ADQA judge fragility."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_CSV = OUT_DIR / "combined_review_priority.csv"


def normalize(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")

    df["judge_fragility"] = 1.0 - df["all4_mean_full_order"].fillna(0)
    df["margin_fragility"] = 1.0 - df["all4_mean_tier3_margin"].clip(0, 1)
    df["tribe_norm"] = normalize(df["risk_score"])
    df["fragility_norm"] = normalize(df["judge_fragility"] + 0.5 * df["margin_fragility"])

    # Weighted composite — TRIBE leads because it is pre-AD
    df["review_priority"] = 0.6 * df["tribe_norm"] + 0.4 * df["fragility_norm"]
    df["review_rank"] = df["review_priority"].rank(ascending=False, method="min").astype(int)

    known_fail = df[df["target"] == 1][["clip_idx", "category", "risk_rank", "review_rank", "review_priority"]]
    top3 = df.nsmallest(3, "review_rank")[
        ["clip_idx", "category", "risk_rank", "review_rank", "review_priority", "quality_risk"]
    ]

    out = df[[
        "clip_idx", "category", "risk_score", "risk_rank",
        "all4_mean_full_order", "all4_mean_tier3_margin",
        "review_priority", "review_rank", "target", "quality_risk", "tribe_route",
    ]].sort_values("review_rank")
    out.to_csv(OUT_CSV, index=False)

    print("Known failure clips (target=1):")
    print(known_fail.to_string(index=False))
    print("\nTop 3 composite review priority:")
    print(top3.to_string(index=False))
    print(f"\nWrote {OUT_CSV}")

    # Check if composite catches both failures in top-3
    if len(known_fail) >= 2:
        ranks = set(known_fail["review_rank"])
        caught = sum(1 for r in known_fail["review_rank"] if r <= 3)
        print(f"\nRecall@3 on known failures: {caught}/{len(known_fail)}")


if __name__ == "__main__":
    main()
