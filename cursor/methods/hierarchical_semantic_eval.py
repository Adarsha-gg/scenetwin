#!/usr/bin/env python3
"""SemVideo hierarchical semantic eval: static / motion / holistic question buckets."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT = Path(__file__).resolve().parent / "output" / "hierarchical_semantic.csv"

STATIC = re.compile(r"\b(wear|setting|background|text|logo|color|object|located|room|kitchen)\b", re.I)
MOTION = re.compile(r"\b(run|jump|throw|move|walk|ski|fall|spike|serve|pour|stir|slide)\b", re.I)
HOLISTIC = re.compile(r"\b(main|overall|scene|happening|story|about|purpose|summary)\b", re.I)


def classify(q: str) -> str:
    t = q.lower()
    m, s, h = bool(MOTION.search(t)), bool(STATIC.search(t)), bool(HOLISTIC.search(t))
    if m and not s:
        return "motion"
    if s and not m:
        return "static"
    if h:
        return "holistic"
    return "other"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    q = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_questions.csv")
    g = pd.read_csv(TIMING / "adqa_v4" / "adqa_v4_grades.csv")
    q["bucket"] = q["question"].astype(str).map(classify)
    print("Question buckets:", q["bucket"].value_counts().to_dict())

    rows = []
    for bucket in ["static", "motion", "holistic", "other"]:
        qids = set(zip(q[q["bucket"] == bucket]["clip_idx"], q[q["bucket"] == bucket]["q_idx"]))
        if not qids:
            continue
        scores = []
        for (cidx, tier), grp in g.groupby(["clip_idx", "tier"]):
            s = [float(r["score"]) for _, r in grp.iterrows() if (cidx, r["q_idx"]) in qids]
            if not s:
                continue
            gt = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier]
            scores.append({"gt": gt, "score": sum(s) / len(s)})
        if scores:
            df = pd.DataFrame(scores)
            rho, p = spearmanr(df["gt"], df["score"])
            rows.append({"bucket": bucket, "rho": float(rho), "p": float(p), "n": len(df)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    print(out.to_string(index=False))
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
