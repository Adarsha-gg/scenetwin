#!/usr/bin/env python3
"""Pairwise Spearman correlations between all paper metrics on tier scores."""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
PAPERS_OUT = Path(__file__).resolve().parent / "output"
SYNTH = CURSOR / "research" / "papers" / "CROSS-PAPER-SYNTHESIS.md"

TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}

METRICS = [
    ("coad_repetition", PAPERS_OUT / "coad_repetition.csv", "self_similarity", True),
    ("critic_entity", PAPERS_OUT / "critic_entity_score.csv", "critic_entity", False),
    ("llm_ad_eval", PAPERS_OUT / "llm_ad_eval_proxy.csv", "llm_ad_eval_proxy", False),
    ("multi_ref_r3", PAPERS_OUT / "multi_ref_r_at_k.csv", "r_at_3", False),
    ("action_coverage", PAPERS_OUT / "action_coverage_score.csv", "action_coverage", False),
    ("story_recall", CURSOR / "discover/output/story_recall_fixed.csv", "story_recall", False),
    ("vt_consistency", CURSOR / "methods/output/av_consistency_scores.csv", "vt_consistency", False),
    ("adqa_v4", ROOT / "output/scenetwin_timing_20clip/adqa_v4/adqa_v4_tier_scores.csv", "adqa_v4_score", False),
    ("ensemble", ROOT / "output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv",
     "ensemble_w50_adqa_need_weighted_clip", False),
    ("need_weighted_clip", ROOT / "output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv",
     "need_weighted_clip", False),
    ("timing_g7g8", PAPERS_OUT / "timing_overlap_g7g8.csv", "g7g8_score", False),
]


def load_metric(name: str, path: Path, col: str, invert: bool) -> pd.Series | None:
    if not path.exists():
        return None
    df = pd.read_csv(path)
    if col not in df.columns:
        return None
    key_cols = ["clip_idx", "tier"] if "tier" in df.columns else ["clip_idx"]
    if "tier" not in df.columns and "gt" in df.columns:
        inv = {v: k for k, v in TIER_GT.items()}
        df["tier"] = df["gt"].map(inv)
    vals = -df[col] if invert else df[col]
    out = df[key_cols].copy()
    out[name] = vals
    return out


def zscore(s: pd.Series) -> pd.Series:
    std = s.std()
    if std == 0 or pd.isna(std):
        return s * 0.0
    return (s - s.mean()) / std


def main() -> None:
    merged: pd.DataFrame | None = None
    loaded: list[str] = []
    for name, path, col, invert in METRICS:
        part = load_metric(name, path, col, invert)
        if part is None:
            continue
        loaded.append(name)
        merged = part if merged is None else merged.merge(part, on=["clip_idx", "tier"], how="outer")

    if merged is None or len(loaded) < 2:
        print("Need at least 2 metric files")
        return

    rows = []
    for a, b in combinations(loaded, 2):
        sub = merged[[a, b]].dropna()
        if len(sub) < 8:
            continue
        r, p = spearmanr(sub[a], sub[b])
        rows.append({"metric_a": a, "metric_b": b, "rho": float(r), "p": float(p), "n": len(sub)})

    corr = pd.DataFrame(rows).sort_values("rho", ascending=False)
    PAPERS_OUT.mkdir(parents=True, exist_ok=True)
    corr.to_csv(PAPERS_OUT / "metric_correlations.csv", index=False)

    # Append high-correlation pairs to synthesis (idempotent block marker)
    high = corr[corr["rho"].abs() > 0.85]
    block = ["\n\n## Auto-generated correlation highlights\n\n"]
    block.append("| pair | ρ | n |\n|------|---:|---:|\n")
    for _, r in high.head(15).iterrows():
        block.append(f"| {r['metric_a']} × {r['metric_b']} | {r['rho']:.3f} | {int(r['n'])} |\n")

    text = SYNTH.read_text(encoding="utf-8") if SYNTH.exists() else ""
    marker = "## Auto-generated correlation highlights"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "".join(block)
    else:
        text = text.rstrip() + "".join(block)
    SYNTH.write_text(text + "\n", encoding="utf-8")
    print(corr.head(20).to_string(index=False))
    print(f"\nWrote {PAPERS_OUT / 'metric_correlations.csv'}")


if __name__ == "__main__":
    main()
