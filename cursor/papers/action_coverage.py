#!/usr/bin/env python3
"""Shot-by-Shot Action Score proxy — ADQA critical action questions only."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
Q = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v4" / "adqa_v4_questions.csv"
G = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v4" / "adqa_v4_grades.csv"
OUT = Path(__file__).resolve().parent / "output" / "action_coverage_score.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-action-coverage.md"

ACTION_RE = re.compile(r"\b(doing|action|perform|hold|throw|eat|walk|run|jump|play|cook|pour|stir)\b", re.I)


def main() -> None:
    q = pd.read_csv(Q)
    g = pd.read_csv(G)
    q["is_action"] = q["question"].str.contains(ACTION_RE) | q["answer_key"].str.contains(ACTION_RE, na=False)
    merged = g.merge(q[["clip_idx", "q_idx", "is_action"]], on=["clip_idx", "q_idx"])
    action = merged[merged["is_action"]]
    rows = []
    for (cidx, tier), sub in action.groupby(["clip_idx", "tier"]):
        acc = float((sub["label"] == "yes").mean())
        rows.append({"clip_idx": cidx, "tier": tier, "action_coverage": acc, "n_action_q": len(sub),
                     "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier]})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["action_coverage"])
    FINDINGS.write_text(f"# Action coverage (Shot-by-Shot proxy)\n\nρ={rho:.3f} p={p:.4f} n_q={action.shape[0]}\n", encoding="utf-8")
    print(f"Action coverage ρ={rho:.3f} ({action['is_action'].sum()} action questions)")


if __name__ == "__main__":
    main()
