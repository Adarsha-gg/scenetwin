#!/usr/bin/env python3
"""Regime-aware SceneTwin auditor — TRIBE routes, ADQA scores.

Implements the two-stage model from GROUND-UP-THESIS.md and compares to
pooled ensemble ranking.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
GU = Path(__file__).resolve().parent / "output" / "ground_up_scores.csv"
OUT = Path(__file__).resolve().parent / "output" / "regime_aware_audit.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "regime-aware-audit.md"

TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}
KNOWN_VIOLATIONS = {0, 12, 14}  # ensemble fails strict tier order


def collision_index(fc: pd.DataFrame) -> pd.Series:
    def nz(s: pd.Series) -> pd.Series:
        x = s.astype(float)
        lo, hi = x.min(), x.max()
        return (x - lo) / (hi - lo) if hi > lo else x * 0
    return nz(fc["extended_seconds_frac"]) * nz(fc["mean_speech_density"]) + 0.35 * nz(fc["tribe_pressure"])


def word_count_penalty(df: pd.DataFrame) -> pd.Series:
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    colmap = {
        "tier3_va11y": "tier3_va11y_words",
        "tier2_vatex_long": "tier2_vatex_long_words",
        "tier1_vatex_short": "tier1_vatex_short_words",
        "tier0_cross": "tier0_cross_words",
    }
    wc_idx = fc.set_index("clip_idx")
    return df.apply(
        lambda r: float(wc_idx.loc[int(r["clip_idx"]), colmap[r["tier"]]])
        if int(r["clip_idx"]) in wc_idx.index else 20.0,
        axis=1,
    )


def build_regime_scores(df: pd.DataFrame, fc: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["collision"] = df["clip_idx"].map(collision_index(fc))
    thr = df.groupby("clip_idx")["collision"].first().median()
    df["regime"] = np.where(df["collision"] >= thr, "collision", "standard")
    df["words"] = word_count_penalty(df)

    # Standard regime: honest v4 ensemble
    df["score_standard"] = df["ensemble_v4_minmax_50"]

    # Collision regime: critical ADQA + penalty for verbosity (shortest sufficient)
    wmax = df.groupby("clip_idx")["words"].transform("max").replace(0, 1)
    df["brevity"] = 1.0 - df["words"] / wmax
    crit_norm = df.groupby("clip_idx")["adqa_critical_only"].transform(
        lambda s: (s - s.min()) / (s.max() - s.min()) if s.max() > s.min() else 0.5
    )
    df["score_collision"] = 0.65 * crit_norm + 0.35 * df["brevity"]

    df["score_regime_aware"] = np.where(
        df["regime"] == "collision", df["score_collision"], df["score_standard"],
    )
    return df, float(thr)


def auc(y: pd.Series, s: pd.Series) -> float:
    d = pd.DataFrame({"y": y, "s": s}).dropna()
    pos, neg = d[d["y"] == 1]["s"], d[d["y"] == 0]["s"]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    wins = sum((p > neg).sum() + 0.5 * (p == neg).sum() for p in pos)
    return wins / (len(pos) * len(neg))


def eval_rho(df: pd.DataFrame, col: str) -> float:
    sub = df.dropna(subset=[col, "gt"])
    if sub[col].nunique() <= 1:
        return float("nan")
    r, _ = spearmanr(sub["gt"], sub[col])
    return float(r)


def consensus_gt(df: pd.DataFrame) -> pd.Series:
    """Per-row GT: tier ordinal unless ADQA-best disagrees (clips 3,7)."""
    gt_ch = pd.read_csv(Path(__file__).resolve().parent / "output" / "ground_up_gt_challenge.csv")
    disagree = set(gt_ch.loc[~gt_ch["gt_matches_adqa"].astype(bool), "clip_idx"])
    out = df["gt"].copy()
    for cidx in disagree:
        best = gt_ch.loc[gt_ch["clip_idx"] == cidx, "adqa_best_name"].iloc[0]
        out.loc[(df["clip_idx"] == cidx) & (df["tier"] == best)] = 3
        for t, g in TIER_GT.items():
            if t != best:
                out.loc[(df["clip_idx"] == cidx) & (df["tier"] == t)] = min(g, 2)
    return out


def main() -> None:
    if not GU.exists():
        raise SystemExit(f"Run ground_up_reframe.py first — missing {GU}")
    df = pd.read_csv(GU)
    fc = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    df, thr = build_regime_scores(df, fc)

    df["gt_consensus"] = consensus_gt(df)

    clip_level = fc.copy()
    clip_level["collision"] = collision_index(clip_level)
    clip_level["ensemble_violation"] = clip_level["clip_idx"].isin(KNOWN_VIOLATIONS).astype(int)
    clip_level["high_collision"] = (clip_level["collision"] >= thr).astype(int)

    router_auc = {
        "collision_vs_violation": auc(clip_level["ensemble_violation"], clip_level["collision"]),
        "collision_vs_high_need": auc(
            (clip_level["extended_seconds_frac"] > clip_level["extended_seconds_frac"].median()).astype(int),
            clip_level["collision"],
        ),
    }

    rhos = {
        "tier_gt_stale_ensemble": eval_rho(df, "ensemble_w50_adqa_need_weighted_clip"),
        "tier_gt_v4_ensemble": eval_rho(df, "ensemble_v4_minmax_50"),
        "tier_gt_regime_aware": eval_rho(df, "score_regime_aware"),
        "consensus_gt_regime_aware": eval_rho(
            df.assign(gt=df["gt_consensus"]), "score_regime_aware",
        ),
        "consensus_gt_v4_ensemble": eval_rho(df.assign(gt=df["gt_consensus"]), "ensemble_v4_minmax_50"),
    }

    std = df[df["regime"] == "standard"]
    col = df[df["regime"] == "collision"]
    regime_rhos = {
        "standard_regime_regime_score": eval_rho(std, "score_regime_aware"),
        "collision_regime_regime_score": eval_rho(col, "score_regime_aware"),
        "standard_regime_v4_ensemble": eval_rho(std, "ensemble_v4_minmax_50"),
        "collision_regime_v4_ensemble": eval_rho(col, "ensemble_v4_minmax_50"),
    }

    rows = [{"test": k, "value": v} for k, v in {**rhos, **regime_rhos, **router_auc}.items()]
    pd.DataFrame(rows).to_csv(OUT, index=False)
    df[["clip_idx", "tier", "gt", "regime", "score_regime_aware", "ensemble_v4_minmax_50"]].to_csv(
        OUT.with_name("regime_aware_scores.csv"), index=False,
    )

    lines = [
        "# Regime-aware audit\n",
        f"Collision threshold: {thr:.3f}\n\n",
        "## Does TRIBE predict where ensemble GT breaks?\n\n",
        f"- collision → known violation clips {{0,12,14}}: AUC **{router_auc['collision_vs_violation']:.3f}**\n\n",
        "## ρ under different GT definitions\n\n",
        "| test | ρ |\n|------|--:|\n",
    ]
    for k, v in rhos.items():
        lines.append(f"| {k} | {v:.3f} |\n")

    lines += ["\n## Regime-conditional ρ\n\n| test | ρ |\n|------|--:|\n"]
    for k, v in regime_rhos.items():
        lines.append(f"| {k} | {v:.3f} |\n")

    lines.append(
        "\n## Interpretation\n\n"
        "Pooled stale ensemble ρ≈0.928 drops to **v4 ρ≈0.882** when recomputed honestly. "
        "Regime-aware scoring does not beat v4 on tier GT — TRIBE's value is **routing** "
        "(flag collision clips for integrated AD workflow), not another blend weight.\n"
    )
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(json.dumps({"rhos": rhos, "regime_rhos": regime_rhos, "router_auc": router_auc}, indent=2))
    print(f"\nWrote {OUT} and {FINDINGS}")


if __name__ == "__main__":
    main()
