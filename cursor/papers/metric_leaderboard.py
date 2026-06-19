#!/usr/bin/env python3
"""Compare ALL paper metrics — which predicts tier GT best?"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
PAPERS_OUT = Path(__file__).resolve().parent / "output"
FINDINGS = CURSOR / "findings" / "paper-metric-leaderboard.md"

TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

METRICS = [
    ("coad_repetition_inv", PAPERS_OUT / "coad_repetition.csv", "self_similarity", True),
    ("critic_entity", PAPERS_OUT / "critic_entity_score.csv", "critic_entity", False),
    ("llm_ad_eval", PAPERS_OUT / "llm_ad_eval_proxy.csv", "llm_ad_eval_proxy", False),
    ("multi_ref_r3", PAPERS_OUT / "multi_ref_r_at_k.csv", "r_at_3", False),
    ("action_coverage", PAPERS_OUT / "action_coverage_score.csv", "action_coverage", False),
    ("story_recall", CURSOR / "discover/output/story_recall_fixed.csv", "story_recall", False),
    ("vt_consistency", CURSOR / "methods/output/av_consistency_scores.csv", "vt_consistency", False),
    ("adqa_v4", ROOT / "output/scenetwin_timing_20clip/adqa_v4/adqa_v4_tier_scores.csv", "adqa_v4_score", False),
    ("ensemble", ROOT / "output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv", "ensemble_w50_adqa_need_weighted_clip", False),
    ("need_weighted_clip", ROOT / "output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv", "need_weighted_clip", False),
]


def main() -> None:
    rows = []
    for name, path, col, invert in METRICS:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if col not in df.columns:
            continue
        if "gt" not in df.columns and "tier" in df.columns:
            df["gt"] = df["tier"].map(TIER_GT)
        sub = df.dropna(subset=["gt", col])
        if len(sub) < 8 or sub[col].nunique() <= 1:
            continue
        vals = -sub[col] if invert else sub[col]
        rho, p = spearmanr(sub["gt"], vals)
        rows.append({"metric": name, "rho": float(rho), "p": float(p), "n": len(sub)})

    rep = pd.DataFrame(rows).sort_values("rho", ascending=False)
    rep.to_csv(PAPERS_OUT / "metric_leaderboard.csv", index=False)
    lines = ["# Paper metric leaderboard\n\n| metric | ρ | p | n |\n|--------|---:|---:|---:|\n"]
    for _, r in rep.iterrows():
        lines.append(f"| {r['metric']} | {r['rho']:.3f} | {r['p']:.4f} | {int(r['n'])} |\n")
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(rep.to_string(index=False))


if __name__ == "__main__":
    main()
