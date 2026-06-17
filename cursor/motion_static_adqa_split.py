#!/usr/bin/env python3
"""SemVideo-inspired split: static vs motion ADQA questions → separate tier rankings."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
Q_PATH = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
G_PATH = TIMING / "adqa_v4" / "adqa_v4_grades.csv"
OUT = Path(__file__).resolve().parent / "output" / "motion_static_adqa.csv"

MOTION_KW = re.compile(
    r"\b(run|running|jump|ski|skii|move|moving|throw|fall|slide|spike|serve|"
    r"weav|alternat|motion|action|perform)\b",
    re.I,
)
STATIC_KW = re.compile(
    r"\b(wear|setting|location|text|logo|sign|background|object|holding|"
    r"kitchen|coat|shirt|color|visible on)\b",
    re.I,
)


def classify_question(q: str, evidence: str) -> str:
    text = f"{q} {evidence}"
    m = bool(MOTION_KW.search(text))
    s = bool(STATIC_KW.search(text))
    if m and not s:
        return "motion"
    if s and not m:
        return "static"
    if m and s:
        return "mixed"
    return "other"


def tier_scores(grades: pd.DataFrame, questions: pd.DataFrame, bucket: str) -> pd.DataFrame:
    qmap = {}
    for _, row in questions.iterrows():
        key = (row["clip_idx"], row["q_idx"])
        qmap[key] = classify_question(str(row["question"]), str(row.get("required_visual_evidence", "")))

    rows = []
    for (cidx, tier), grp in grades.groupby(["clip_idx", "tier"]):
        scores = []
        for _, r in grp.iterrows():
            b = qmap.get((cidx, r["q_idx"]), "other")
            if bucket == "all" or b == bucket:
                scores.append(float(r["score"]))
        if scores:
            rows.append({"clip_idx": cidx, "tier": tier, f"adqa_{bucket}": sum(scores) / len(scores)})
    return pd.DataFrame(rows)


def inversion_count(df: pd.DataFrame, col: str) -> int:
    n = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        if by.get("tier2_vatex_long", 0) > by.get("tier3_va11y", 0):
            n += 1
        if by.get("tier1_vatex_short", 0) > by.get("tier3_va11y", 0):
            n += 1
    return n


def main() -> None:
    q = pd.read_csv(Q_PATH)
    g = pd.read_csv(G_PATH)

    counts = {"motion": 0, "static": 0, "mixed": 0, "other": 0}
    for _, row in q.iterrows():
        counts[classify_question(str(row["question"]), str(row.get("required_visual_evidence", "")))] += 1

    all_s = tier_scores(g, q, "all")
    mot_s = tier_scores(g, q, "motion")
    sta_s = tier_scores(g, q, "static")
    df = all_s.merge(mot_s, on=["clip_idx", "tier"], how="outer")
    df = df.merge(sta_s, on=["clip_idx", "tier"], how="outer")

    gt = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}
    df["gt"] = df["tier"].map(gt)

    rows = []
    for col in ["adqa_all", "adqa_motion", "adqa_static"]:
        if col not in df.columns:
            continue
        sub = df.dropna(subset=[col])
        rho, p = spearmanr(sub["gt"], sub[col])
        rows.append({
            "bucket": col.replace("adqa_", ""),
            "spearman_rho": rho,
            "p": p,
            "tier2_over_tier3_clips": inversion_count(sub, col) // 2,
            "question_count": counts.get(col.replace("adqa_", ""), len(q)),
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT, index=False)
    df.to_csv(OUT.with_name("motion_static_adqa_scores.csv"), index=False)
    print("Question bucket counts:", counts)
    print(out.to_string(index=False))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
