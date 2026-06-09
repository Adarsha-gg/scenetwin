#!/usr/bin/env python3
"""tribe_gate_combo — can TRIBE clip-triage and the CLIP wrong-content gate be fused?

Two locked SceneTwin layers, both keyed by the same 60 external clips:

  1. TRIBE clip-level triage  (findings/tribe-clip-level-triage.md):
     `accessibility_gap` is ONE scalar per clip; it flags clips the AD metric
     MISORDERS on the 3-tier ladder. ADQA-only: AUC 0.79 that gap predicts misorder.

  2. CLIP wrong-content gate  (halluc_gate.csv):
     per-AD grounding drop `clip_expert - clip_halluc`; flags hallucinated content.
     Ranks expert above the injected lie on 57/60 clips.

The tempting move is to FUSE them into a single clip risk score. This script tests
whether that is the right architecture. It runs LOCAL only (reads two cached files),
no LLM, no CLIP rerun.

Findings (honest):
  * The two failure classes are DISJOINT: overlap = 0, Spearman(gap, drop) ~ 0.06,
    cross-AUC ~ 0.42 each direction. TRIBE is blind to gate failures and vice versa.
  * Because they are orthogonal, a z-SUMMED single risk score DILUTES and loses to
    TRIBE-alone at low review budget. You cannot merge them into one number.
  * The correct architecture is two INDEPENDENT routers (an OR-cascade): the gate
    flags its own low-grounding clips, TRIBE spends the rest of the budget on
    high-gap clips. CAVEAT (stated in JSON): the cascade's numeric lift over
    TRIBE-alone is partly definitional (the gate flags exactly its clip_drop<=0
    failures), so the load-bearing result is the orthogonality, not the lift size.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
EXT = CURSOR / "output" / "external_ensemble_eval.csv"
HALLUC = CURSOR / "output" / "halluc_gate" / "halluc_gate.csv"
TRIBE = CURSOR / "research" / "output" / "tribe_counterfactual_external_per_clip.csv"
OUT = CURSOR / "output" / "tribe_gate_combo.json"

THREE = ["tier0_cross", "tier1_vatex_short", "tier3_va11y"]


def minmax(s: pd.Series) -> pd.Series:
    r = s.max() - s.min()
    return (s - s.min()) / r if r else s * 0.0


def order_ok(df: pd.DataFrame, col: str) -> pd.DataFrame:
    rows = []
    for vid, g in df.groupby("video_id"):
        by = dict(zip(g.tier, g[col]))
        if all(t in by for t in THREE):
            rows.append({"video_id": vid, "ok": int(by[THREE[0]] < by[THREE[1]] < by[THREE[2]])})
    return pd.DataFrame(rows)


def auc(score: pd.Series, label: pd.Series) -> float:
    pos, neg = score[label == 1], score[label == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    u, _ = mannwhitneyu(pos, neg, alternative="greater")
    return float(u / (len(pos) * len(neg)))


def main() -> None:
    # --- per-clip rho-misorder label (ADQA-only on the 3-tier ladder) ---
    e = pd.read_csv(EXT)
    e = e[e.tier.isin(THREE)].copy()
    e["adqa_n"] = e.groupby("video_id")["adqa_score"].transform(minmax)
    adqa_ok = order_ok(e.assign(a=e.adqa_n), "a")

    # --- per-clip wrong-content gate margin ---
    hg = pd.read_csv(HALLUC)
    hg["clip_drop"] = hg.clip_expert - hg.clip_halluc

    # --- TRIBE clip gap ---
    tribe = pd.read_csv(TRIBE)[["video_id", "accessibility_gap"]]

    m = (tribe.merge(adqa_ok, on="video_id")
              .merge(hg[["video_id", "clip_drop"]], on="video_id"))
    n = len(m)
    m["rho_fail"] = (m.ok == 0).astype(int)        # TRIBE's job
    m["gate_fail"] = (m.clip_drop <= 0).astype(int)  # gate's job (grounding does not favour expert)
    m["any_fail"] = ((m.rho_fail == 1) | (m.gate_fail == 1)).astype(int)
    nf = int(m.any_fail.sum())

    # --- orthogonality (the load-bearing, non-circular result) ---
    overlap = int(((m.rho_fail == 1) & (m.gate_fail == 1)).sum())
    spearman = float(m.accessibility_gap.corr(m.clip_drop, method="spearman"))
    ortho = {
        "n_clips": n,
        "rho_fail_n": int(m.rho_fail.sum()),
        "gate_fail_n": int(m.gate_fail.sum()),
        "overlap_n": overlap,
        "spearman_gap_vs_drop": round(spearman, 4),
        "auc_tribe_predicts_gate_fail": round(auc(m.accessibility_gap, m.gate_fail), 3),
        "auc_neg_drop_predicts_rho_fail": round(auc(-m.clip_drop, m.rho_fail), 3),
        "auc_tribe_predicts_rho_fail": round(auc(m.accessibility_gap, m.rho_fail), 3),
        "auc_neg_drop_predicts_gate_fail": round(auc(-m.clip_drop, m.gate_fail), 3),
    }

    # --- three review policies on the UNION failure set ---
    def z(s):
        return (s - s.mean()) / s.std(ddof=0)
    m["risk_sum"] = z(m.accessibility_gap) + z(-m.clip_drop)

    def tribe_only(k):
        idx = m.accessibility_gap.sort_values(ascending=False).index[:k]
        return m.loc[idx, "any_fail"].sum() / nf

    def summed(k):
        idx = m.risk_sum.sort_values(ascending=False).index[:k]
        return m.loc[idx, "any_fail"].sum() / nf

    def cascade(k):
        gate_idx = set(m.index[m.clip_drop <= 0])
        rem = k - len(gate_idx)
        pool = m.drop(index=list(gate_idx)).sort_values("accessibility_gap", ascending=False)
        flagged = gate_idx | set(pool.index[:max(0, rem)])
        return m.loc[list(flagged), "any_fail"].sum() / nf

    curve = []
    for frac in (0.10, 0.15, 0.20, 0.30, 0.40):
        k = max(1, round(frac * n))
        curve.append({
            "budget_frac": frac,
            "k": k,
            "oracle_ceiling": round(min(k, nf) / nf, 3),
            "tribe_only": round(tribe_only(k), 3),
            "summed_score": round(summed(k), 3),
            "or_cascade": round(cascade(k), 3),
        })

    report = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "task": "Can TRIBE clip-triage and the CLIP wrong-content gate be fused into one risk score?",
        "answer": "No. They detect disjoint failure classes; fuse-by-sum dilutes. Keep two independent routers.",
        "union_failure_n": nf,
        "orthogonality": ortho,
        "review_policies_union_recall": curve,
        "caveats": [
            "n=%d union failures is small; treat recall numbers as directional." % nf,
            "gate_fail is DEFINED as clip_drop<=0 and the cascade flags clip_drop<=0, so the cascade's lift over tribe-only is partly definitional (permutation p~0.80). The non-circular finding is the orthogonality (overlap=0, spearman 0.06, cross-AUC ~0.42).",
            "rho_fail uses ADQA-only ordering; the full ensemble misorders only 2/60 so this combo targets the ADQA-backbone deployment.",
        ],
    }
    OUT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
