#!/usr/bin/env python3
"""Counterfactual TRIBE gaps from saved P_AV / P_A tensors (Description Gain scaffold)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "output" / "scenetwin_description_gain" / "preds"
OUT = Path(__file__).resolve().parent / "output" / "tribe_counterfactual_clips.csv"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a.flatten().astype(float)
    b = b.flatten().astype(float)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def description_gain(p_av: np.ndarray, p_a: np.ndarray, p_ad: np.ndarray) -> float:
    """cos(P_AV, P_AD) - cos(P_AV, P_A) — positive = AD recovers visual signal."""
    return cosine(p_av.mean(0), p_ad.mean(0)) - cosine(p_av.mean(0), p_a.mean(0))


def main() -> None:
    if not PRED.exists():
        print(f"No preds at {PRED} — skip")
        return

    av_files = sorted(PRED.glob("*_av.npy"))
    if not av_files:
        print("No *_av.npy tensors found")
        return

    rows = []
    for av_path in av_files:
        stem = av_path.name.replace("_av.npy", "")
        a_path = PRED / f"{stem}_a.npy"
        if not a_path.exists():
            continue
        p_av = np.load(av_path)
        p_a = np.load(a_path)
        gap_mean = float(np.mean(np.linalg.norm(p_av - p_a, axis=-1)))

        for tier in TIERS:
            ad_path = PRED / f"{stem}_{tier}.npy"
            if not ad_path.exists():
                continue
            p_ad = np.load(ad_path)
            dg = description_gain(p_av, p_a, p_ad)
            rows.append({
                "clip_stem": stem,
                "tier": tier,
                "gt": TIER_GT[tier],
                "description_gain": dg,
                "av_a_gap_mean": gap_mean,
            })

    if not rows:
        print("No tier AD tensors found alongside AV/A")
        return

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    for tier in TIERS:
        sub = df[df["tier"] == tier]
        if len(sub):
            print(f"  {tier}: mean DG = {sub['description_gain'].mean():.4f} (n={len(sub)})")

    if df["gt"].nunique() > 1:
        rho, p = spearmanr(df["gt"], df["description_gain"])
        print(f"\nSpearman(gt, description_gain) = {rho:.3f}, p = {p:.4g}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
