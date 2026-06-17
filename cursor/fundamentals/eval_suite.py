#!/usr/bin/env python3
"""Multi-metric evaluation suite — not just Spearman.

Scores any long-form CSV with clip_idx, tier, gt, and numeric score columns.
Reports: Kendall, pairwise wins, full-order rate, violation rate, tier margins,
leave-one-clip-out stability, permutation p, clip difficulty ranking.
"""
from __future__ import annotations

import argparse
from itertools import product, permutations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "eval_suite_report.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "fundamentals-eval-suite.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}
MAX_EXACT_PERM = 100_000
N_SAMPLE_PERM = 1500
SEED = 17

SCORE_SOURCES = [
    ("ensemble", TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv", "ensemble_w50_adqa_need_weighted_clip"),
    ("adqa_full", TIMING / "adqa_v4" / "adqa_v4_tier_scores.csv", "adqa_v4_score"),
    ("vt_consistency", Path(__file__).resolve().parents[1] / "methods" / "output" / "av_consistency_scores.csv", "vt_consistency"),
    ("vidscribe", Path(__file__).resolve().parents[1] / "methods" / "output" / "vidscribe_query_coverage.csv", "query_coverage"),
]


def pairwise_wins(df: pd.DataFrame, col: str) -> int:
    wins = 0
    for _, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        if "tier3_va11y" not in v:
            continue
        for lo in ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]:
            if lo in v:
                wins += int(v["tier3_va11y"] > v[lo])
    return wins


def full_order_clips(df: pd.DataFrame, col: str) -> int:
    n = 0
    for _, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        if all(k in v for k in TIER_KEYS):
            n += int(v["tier3_va11y"] > v["tier2_vatex_long"] > v["tier1_vatex_short"] > v["tier0_cross"])
    return n


def _tier_vals(g: pd.DataFrame, col: str) -> dict[str, float]:
    return dict(zip(g["tier"], g[col]))


def violation_clips(df: pd.DataFrame, col: str) -> list[int]:
    bad = []
    for clip_idx, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        for hi, lo in [("tier3_va11y", "tier2_vatex_long"), ("tier3_va11y", "tier1_vatex_short"),
                       ("tier2_vatex_long", "tier1_vatex_short"), ("tier3_va11y", "tier0_cross")]:
            if hi in v and lo in v and v[hi] < v[lo]:
                bad.append(int(clip_idx))
                break
    return sorted(set(bad))


def mean_tier3_margin(df: pd.DataFrame, col: str) -> float:
    margins = []
    for _, g in df.groupby("clip_idx"):
        v = _tier_vals(g, col)
        if "tier3_va11y" in v and "tier1_vatex_short" in v:
            margins.append(v["tier3_va11y"] - v["tier1_vatex_short"])
    return float(np.mean(margins)) if margins else float("nan")


def loo_rho(df: pd.DataFrame, col: str) -> tuple[float, float]:
    """Leave-one-clip-out mean Spearman — stability proxy."""
    clips = sorted(df["clip_idx"].unique())
    rhos = []
    for drop in clips:
        sub = df[df["clip_idx"] != drop]
        if sub[col].nunique() <= 1:
            continue
        r, _ = spearmanr(sub["gt"], sub[col], nan_policy="omit")
        if np.isfinite(r):
            rhos.append(r)
    if not rhos:
        return float("nan"), float("nan")
    return float(np.mean(rhos)), float(np.std(rhos))


def perm_p(df: pd.DataFrame, col: str, rng: np.random.Generator) -> float:
    obs, _ = spearmanr(df["gt"], df[col], nan_policy="omit")
    groups = list(df.groupby("clip_idx").groups.values())
    ge = 0
    n = 0
    total = 1
    for idx in groups:
        total *= len(list(permutations(df.loc[idx, col].to_numpy())))
    if total <= MAX_EXACT_PERM:
        for combo in product(*[list(permutations(df.loc[idx, col].to_numpy())) for idx in groups]):
            sh = df.copy()
            for idx, vals in zip(groups, combo):
                sh.loc[idx, col] = vals
            r, _ = spearmanr(sh["gt"], sh[col], nan_policy="omit")
            ge += int(r >= obs)
            n += 1
    else:
        for _ in range(N_SAMPLE_PERM):
            sh = df.copy()
            for idx in groups:
                sh.loc[idx, col] = rng.permutation(sh.loc[idx, col].to_numpy())
            r, _ = spearmanr(sh["gt"], sh[col], nan_policy="omit")
            ge += int(r >= obs)
            n += 1
    return ge / max(n, 1)


def load_scores(name: str, path: Path, col: str) -> pd.DataFrame | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if col not in df.columns:
        # try first numeric after gt
        for c in df.columns:
            if c not in {"clip_idx", "tier", "gt"} and pd.api.types.is_numeric_dtype(df[c]):
                col = c
                break
    if "gt" not in df.columns and "tier" in df.columns:
        df["gt"] = df["tier"].map(TIER_GT)
    if col not in df.columns:
        return None
    out = df[["clip_idx", "tier", "gt", col]].dropna()
    out = out.rename(columns={col: "score"})
    out["source"] = name
    return out


def evaluate(df: pd.DataFrame) -> dict:
    col = "score"
    valid = df[np.isfinite(df[col])]
    n_clips = valid["clip_idx"].nunique()
    rho, _ = spearmanr(valid["gt"], valid[col], nan_policy="omit")
    tau, _ = kendalltau(valid["gt"], valid[col], nan_policy="omit")
    rng = np.random.default_rng(SEED)
    loo_mean, loo_std = loo_rho(valid, col)
    viol = violation_clips(valid, col)
    return {
        "n_rows": len(valid),
        "n_clips": n_clips,
        "spearman_rho": float(rho),
        "kendall_tau": float(tau),
        "pairwise_wins": pairwise_wins(valid, col),
        "pairwise_max": n_clips * 3,
        "full_order_clips": full_order_clips(valid, col),
        "full_order_rate": full_order_clips(valid, col) / max(n_clips, 1),
        "violation_clips": len(viol),
        "violation_rate": len(viol) / max(n_clips, 1),
        "violation_clip_ids": ",".join(map(str, viol)),
        "mean_tier3_margin": mean_tier3_margin(valid, col),
        "loo_rho_mean": loo_mean,
        "loo_rho_std": loo_std,
        "perm_p_rho": perm_p(valid, col, rng),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extra", action="append", default=[], help="name:path:col")
    args = parser.parse_args()

    rows = []
    for name, path, col in SCORE_SOURCES:
        df = load_scores(name, path, col)
        if df is None:
            continue
        m = evaluate(df)
        m["metric"] = name
        rows.append(m)

    for spec in args.extra:
        parts = spec.split(":")
        if len(parts) != 3:
            continue
        df = load_scores(parts[0], Path(parts[1]), parts[2])
        if df is None:
            continue
        m = evaluate(df)
        m["metric"] = parts[0]
        rows.append(m)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    rep = pd.DataFrame(rows)
    rep.to_csv(OUT, index=False)

    lines = ["# Fundamentals eval suite\n", f"Generated from {len(rows)} score sources.\n\n",
             "| metric | ρ | τ | pairwise | full-order | violations | LOO ρ±σ | perm p |\n",
             "|--------|---:|---:|---:|---:|---:|---:|---:|\n"]
    for _, r in rep.iterrows():
        pw = f"{int(r['pairwise_wins'])}/{int(r['pairwise_max'])}"
        lines.append(
            f"| {r['metric']} | {r['spearman_rho']:.3f} | {r['kendall_tau']:.3f} | {pw} | "
            f"{int(r['full_order_clips'])}/{int(r['n_clips'])} | {int(r['violation_clips'])} | "
            f"{r['loo_rho_mean']:.3f}±{r['loo_rho_std']:.3f} | {r['perm_p_rho']:.4f} |\n"
        )
    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(rep.to_string(index=False))
    print(f"\nWrote {OUT} and {FINDINGS}")


if __name__ == "__main__":
    main()
