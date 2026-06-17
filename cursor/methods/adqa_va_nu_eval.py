#!/usr/bin/env python3
"""ADQA-style Visual Appreciation vs Narrative Understanding split (EMNLP 2025).

ADQA evaluates AD on few-minute segments with VA questions (visual facts) and
NU questions (plot/story). We proxy this on our frame-grounded ADQA CSV using
question text heuristics and report separate tier correlations.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "adqa_va_nu_results.csv"
REPORT = Path(__file__).resolve().parents[1] / "findings" / "method-adqa-va-nu.md"

NU_KW = re.compile(
    r"\b(story|plot|why|because|before|after|then|next|narrative|goal|"
    r"relationship|conversation|talking about|happens next)\b",
    re.I,
)
VA_KW = re.compile(
    r"\b(wear|wearing|color|text|logo|sign|background|object|holding|"
    r"where|located|setting|visible|screen|what is|who is|how many)\b",
    re.I,
)


def bucket(q: str, evidence: str) -> str:
    t = f"{q} {evidence}"
    nu = bool(NU_KW.search(t))
    va = bool(VA_KW.search(t))
    if nu and not va:
        return "NU"
    if va and not nu:
        return "VA"
    if nu and va:
        return "mixed"
    return "other"


def tier_scores(grades: pd.DataFrame, questions: pd.DataFrame, bucket_name: str) -> pd.DataFrame:
    qmap = {}
    for _, row in questions.iterrows():
        qmap[(int(row["clip_idx"]), int(row["q_idx"]))] = bucket(
            str(row["question"]), str(row.get("required_visual_evidence", ""))
        )
    rows = []
    for (cidx, tier), grp in grades.groupby(["clip_idx", "tier"]):
        scores = [
            float(r["score"]) for _, r in grp.iterrows()
            if qmap.get((int(cidx), int(r["q_idx"])), "other") == bucket_name
        ]
        if not scores:
            continue
        gt = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier]
        rows.append({"clip_idx": cidx, "tier": tier, "gt": gt, "score": sum(scores) / len(scores)})
    return pd.DataFrame(rows)


def eval_bucket(df: pd.DataFrame, name: str) -> dict:
    if df.empty or df["gt"].nunique() < 2:
        return {"bucket": name, "rho": None, "n": 0}
    rho, p = spearmanr(df["gt"], df["score"])
    return {"bucket": name, "rho": float(rho), "p": float(p), "n": len(df), "n_questions": df.groupby("clip_idx").size().mean()}


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")

    counts = {"VA": 0, "NU": 0, "mixed": 0, "other": 0}
    for _, row in q.iterrows():
        counts[bucket(str(row["question"]), str(row.get("required_visual_evidence", "")))] += 1

    results = []
    for b in ["VA", "NU", "mixed", "all"]:
        if b == "all":
            sub = g.copy()
            sub["score"] = sub["score"].astype(float)
            sub["gt"] = sub["tier"].map({
                "tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3,
            })
            agg = sub.groupby(["clip_idx", "tier", "gt"])["score"].mean().reset_index()
            r = eval_bucket(agg, "all")
        else:
            agg = tier_scores(g, q, b)
            r = eval_bucket(agg, b)
        results.append(r)

    out = pd.DataFrame(results)
    out.to_csv(OUT, index=False)

    lines = [
        "# ADQA VA / NU split (new method)",
        "",
        f"Question counts: {counts}",
        "",
        out.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "ADQA (Kala et al. EMNLP 2025) argues AD eval must separate **visual appreciation**",
        "from **narrative understanding** on coherent multi-minute segments.",
        "If VA ρ >> NU ρ, CLIP grounding dominates; if NU lags, we need plot-level ADQA.",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(out.to_string(index=False))
    print(f"\nWrote {OUT}, {REPORT}")


if __name__ == "__main__":
    main()
