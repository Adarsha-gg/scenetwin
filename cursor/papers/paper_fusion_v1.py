#!/usr/bin/env python3
"""Fuse paper metrics per cross-paper synthesis — test combinations vs tier GT."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
PAPERS_OUT = Path(__file__).resolve().parent / "output"
FINDINGS = CURSOR / "findings" / "paper-fusion-results.md"

TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

SOURCES = [
    ("llm_ad_eval", PAPERS_OUT / "llm_ad_eval_proxy.csv", "llm_ad_eval_proxy", False),
    ("adqa_v4", ROOT / "output/scenetwin_timing_20clip/adqa_v4/adqa_v4_tier_scores.csv", "adqa_v4_score", False),
    ("vt_consistency", CURSOR / "methods/output/av_consistency_scores.csv", "vt_consistency", False),
    ("story_recall", CURSOR / "discover/output/story_recall_fixed.csv", "story_recall", False),
    ("action_coverage", PAPERS_OUT / "action_coverage_score.csv", "action_coverage", False),
    ("critic_entity", PAPERS_OUT / "critic_entity_score.csv", "critic_entity", False),
    ("need_weighted_clip", ROOT / "output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv",
     "need_weighted_clip", False),
    ("coad_repetition", PAPERS_OUT / "coad_repetition.csv", "self_similarity", True),
    ("timing_g7g8", PAPERS_OUT / "timing_overlap_g7g8.csv", "g7g8_score", False),
    ("ensemble", ROOT / "output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv",
     "ensemble_w50_adqa_need_weighted_clip", False),
]

FUSIONS = {
    "semantic_core": {"llm_ad_eval": 0.34, "adqa_v4": 0.33, "vt_consistency": 0.33},
    "narrative_ground": {"adqa_v4": 0.50, "story_recall": 0.30, "action_coverage": 0.20},
    "audit_no_ref": {"adqa_v4": 0.45, "vt_consistency": 0.40, "coad_repetition": 0.15},
    "entity_action": {"adqa_v4": 0.55, "critic_entity": 0.20, "action_coverage": 0.25},
    "timing_semantic": {"adqa_v4": 0.40, "timing_g7g8": 0.35, "need_weighted_clip": 0.25},
    "paper_stack_v1": {"adqa_v4": 0.35, "story_recall": 0.20, "vt_consistency": 0.20,
                       "action_coverage": 0.10, "need_weighted_clip": 0.10, "timing_g7g8": 0.05},
}


def zscore(s: pd.Series) -> pd.Series:
    std = s.std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


def load_all() -> pd.DataFrame:
    merged: pd.DataFrame | None = None
    for name, path, col, invert in SOURCES:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if col not in df.columns:
            continue
        if "gt" not in df.columns:
            df["gt"] = df["tier"].map(TIER_GT)
        vals = -df[col] if invert else df[col]
        part = df[["clip_idx", "tier", "gt"]].copy()
        part[name] = vals
        merged = part if merged is None else merged.merge(part, on=["clip_idx", "tier", "gt"], how="outer")
    if merged is None:
        raise SystemExit("No metric sources found")
    return merged


def apply_fusion(df: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    score = pd.Series(0.0, index=df.index)
    total_w = 0.0
    for col, w in weights.items():
        if col not in df.columns:
            continue
        score = score + w * zscore(df[col])
        total_w += w
    if total_w == 0:
        return score
    return score / total_w


def grid_search(df: pd.DataFrame, cols: list[str]) -> tuple[dict[str, float], float]:
    best_rho, best_w = -2.0, {}
    # coarse grid on 3 primary cols
    primary = [c for c in ["adqa_v4", "story_recall", "vt_consistency"] if c in cols]
    if len(primary) < 2:
        return {}, -1.0
    steps = np.arange(0.0, 1.05, 0.25)
    for w0 in steps:
        for w1 in steps:
            w2 = 1.0 - w0 - w1
            if w2 < -0.01:
                continue
            weights = {primary[0]: w0, primary[1]: w1}
            if len(primary) > 2:
                weights[primary[2]] = max(0.0, w2)
            s = apply_fusion(df, weights)
            sub = df.assign(_s=s).dropna(subset=["gt", "_s"])
            if sub["_s"].nunique() <= 1:
                continue
            rho, _ = spearmanr(sub["gt"], sub["_s"])
            if rho > best_rho:
                best_rho, best_w = float(rho), weights
    return best_w, best_rho


def main() -> None:
    df = load_all()
    rows = []
    score_cols = [c for c in df.columns if c not in ("clip_idx", "tier", "gt")]

    for name, weights in FUSIONS.items():
        s = apply_fusion(df, weights)
        out_col = f"fusion_{name}"
        df[out_col] = s
        sub = df.dropna(subset=["gt", out_col])
        if len(sub) < 8 or sub[out_col].nunique() <= 1:
            continue
        rho, p = spearmanr(sub["gt"], sub[out_col])
        rows.append({"fusion": name, "rho": rho, "p": p, "weights": str(weights)})

    best_w, best_rho = grid_search(df, score_cols)
    if best_w:
        df["fusion_grid_best"] = apply_fusion(df, best_w)
        sub = df.dropna(subset=["gt", "fusion_grid_best"])
        rho, p = spearmanr(sub["gt"], sub["fusion_grid_best"])
        rows.append({"fusion": "grid_best", "rho": rho, "p": p,
                     "weights": str({k: round(float(v), 3) for k, v in best_w.items()})})

    if "ensemble" in df.columns:
        sub = df.dropna(subset=["gt", "ensemble"])
        rho, p = spearmanr(sub["gt"], sub["ensemble"])
        rows.append({"fusion": "ensemble_baseline", "rho": rho, "p": p, "weights": "existing"})

    rep = pd.DataFrame(rows).sort_values("rho", ascending=False)
    PAPERS_OUT.mkdir(parents=True, exist_ok=True)

    out_cols = ["clip_idx", "tier", "gt"] + [c for c in df.columns if c.startswith("fusion_")]
    df[out_cols].to_csv(PAPERS_OUT / "paper_fusion_scores.csv", index=False)
    rep.to_csv(PAPERS_OUT / "paper_fusion_leaderboard.csv", index=False)

    lines = ["# Paper fusion results\n\n", "| fusion | ρ | p | weights |\n|--------|---:|---:|---------|\n"]
    for _, r in rep.iterrows():
        lines.append(f"| {r['fusion']} | {r['rho']:.3f} | {r['p']:.4f} | {r['weights']} |\n")
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    main()
