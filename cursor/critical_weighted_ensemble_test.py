#!/usr/bin/env python3
"""Test critical-weighted ADQA + CLIP ensemble vs current stack."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
SCORES = TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv"
Q = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
G = TIMING / "adqa_v4" / "adqa_v4_grades.csv"
OUT = Path(__file__).resolve().parent / "output" / "critical_weighted_sweep.csv"

WEIGHTS = {"critical": 3.0, "useful": 1.0, "": 1.0}


def weighted_adqa() -> pd.DataFrame:
    q = pd.read_csv(Q)
    imp = { (int(r.clip_idx), int(r.q_idx)): WEIGHTS.get(str(r.importance).lower(), 1.0) for _, r in q.iterrows() }
    g = pd.read_csv(G)
    rows = []
    for (cidx, tier), grp in g.groupby(["clip_idx", "tier"]):
        num = den = 0.0
        for _, r in grp.iterrows():
            w = imp.get((int(cidx), int(r.q_idx)), 1.0)
            num += w * float(r["score"])
            den += w
        if den > 0:
            rows.append({"clip_idx": cidx, "tier": tier, "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier], "adqa_critical_w": num / den})
    return pd.DataFrame(rows)


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo, hi = s.min(), s.max()
        if not np.isfinite(lo) or hi == lo:
            return pd.Series(np.zeros(len(s)), index=s.index)
        return (s - lo) / (hi - lo)
    return df.groupby("clip_idx", group_keys=False)[col].apply(scale)


def eval_df(df: pd.DataFrame, col: str) -> dict:
    rho, rp = spearmanr(df["gt"], df[col])
    tau, _ = kendalltau(df["gt"], df[col])
    wins = total = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        for lo in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
            total += 1
            wins += int(by["tier3_va11y"] > by[lo])
    return {"metric": col, "rho": float(rho), "p": float(rp), "tau": float(tau), "wins": f"{wins}/{total}"}


def main() -> None:
    base = pd.read_csv(SCORES)
    crit = weighted_adqa()
    df = base.merge(crit, on=["clip_idx", "tier"], how="left", suffixes=("", "_c"))
    if "gt_c" in df.columns:
        df = df.drop(columns=["gt_c"])
    df["adqa_critical_w_norm"] = minmax_clipwise(df, "adqa_critical_w")
    df["ensemble_crit_clip"] = 0.5 * df["clip_top3_norm_clip"] + 0.5 * df["adqa_critical_w_norm"]
    df["ensemble_crit_mean"] = 0.5 * df["clip_mean_norm_clip"] + 0.5 * df["adqa_critical_w_norm"]

    rows = [eval_df(df, c) for c in ["adqa_v2_score", "adqa_critical_w", "ensemble_mean_clip_top3", "ensemble_crit_clip", "ensemble_crit_mean"]]
    out = pd.DataFrame(rows).sort_values("rho", ascending=False)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
