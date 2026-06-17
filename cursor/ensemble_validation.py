#!/usr/bin/env python3
"""Bootstrap CI on ensemble rho — repo-local paths (fixes stale ~/Knowledge paths)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
SCORES = ROOT / "output" / "scenetwin_timing_20clip" / "ensemble" / "adqa_clip_ensemble_scores.csv"
OUT = Path(__file__).resolve().parent / "findings" / "ensemble-validation.md"

CLIP_COL = "clip_top3_norm_clip"
ADQA_COL = "adqa_norm_clip"
ENS_COL = "ensemble_mean_clip_top3"
N_BOOT = 2000
RNG = np.random.default_rng(42)


def per_clip_rho(df: pd.DataFrame, col: str) -> float:
    rhos = []
    for _, grp in df.groupby("clip_idx"):
        if grp[col].notna().sum() < 3:
            continue
        r, _ = stats.spearmanr(grp["gt"], grp[col])
        if np.isfinite(r):
            rhos.append(r)
    return float(np.mean(rhos)) if rhos else float("nan")


def bootstrap_rho(df: pd.DataFrame, col: str, n: int = N_BOOT) -> tuple[float, float, float]:
    clips = df["clip_idx"].unique()
    rhos = []
    for _ in range(n):
        sample = RNG.choice(clips, size=len(clips), replace=True)
        parts = [df[df["clip_idx"] == c] for c in sample]
        boot = pd.concat(parts, ignore_index=True)
        r, _ = stats.spearmanr(boot["gt"], boot[col])
        if np.isfinite(r):
            rhos.append(r)
    arr = np.array(rhos)
    return float(np.mean(arr)), float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SCORES)
    clips_ok = (
        df.groupby("clip_idx")
        .filter(lambda g: g[CLIP_COL].notna().all() and g[ADQA_COL].notna().all())
        ["clip_idx"].unique()
    )
    df = df[df["clip_idx"].isin(clips_ok)].copy()

    r_clip, _ = stats.spearmanr(df["gt"], df[CLIP_COL])
    r_adqa, _ = stats.spearmanr(df["gt"], df[ADQA_COL])
    r_ens, _ = stats.spearmanr(df["gt"], df[ENS_COL])
    mean_clip_adqa = per_clip_rho(df, CLIP_COL)

    ens_mean, ens_lo, ens_hi = bootstrap_rho(df, ENS_COL)

    lines = [
        "# Ensemble validation (cursor rerun)",
        "",
        f"Clips with complete data: **{len(clips_ok)}**",
        "",
        "## Global Spearman vs tier ground truth",
        "",
        f"| Metric | ρ |",
        f"|--------|---|",
        f"| CLIP top3 norm | {r_clip:.4f} |",
        f"| ADQA norm | {r_adqa:.4f} |",
        f"| Ensemble 50/50 | {r_ens:.4f} |",
        "",
        f"Mean per-clip CLIP↔ADQA ρ: **{mean_clip_adqa:.3f}** (complementarity diagnostic)",
        "",
        f"Bootstrap 95% CI on ensemble ρ ({N_BOOT} resamples): **[{ens_lo:.3f}, {ens_hi:.3f}]** (point {ens_mean:.3f})",
    ]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
