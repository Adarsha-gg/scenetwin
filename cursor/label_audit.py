#!/usr/bin/env python3
"""Audit tier ground-truth labels — are we ranking the wrong AD as 'best'?"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
SCORES = TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv"
QUESTIONS = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
GRADES = TIMING / "adqa_v4" / "adqa_v4_grades.csv"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_CSV = OUT_DIR / "label_audit.csv"
OUT_MD = Path(__file__).resolve().parent / "findings" / "label-audit.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}


def pairwise_wins(df: pd.DataFrame, col: str) -> tuple[int, int]:
    wins = total = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        for lo in ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]:
            total += 1
            wins += int(by["tier3_va11y"] > by[lo])
    return wins, total


def full_order_clips(df: pd.DataFrame, col: str) -> int:
    n = 0
    for _, g in df.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        if all(by[t] >= by[t2] for t, t2 in zip(TIERS, TIERS[1:])):
            n += 1
    return n


def build_critical_adqa() -> pd.DataFrame:
    q = pd.read_csv(QUESTIONS)
    g = pd.read_csv(GRADES)
    crit_q = {
        (int(row["clip_idx"]), int(row["q_idx"]))
        for _, row in q.iterrows()
        if str(row.get("importance", "")).lower() == "critical"
    }
    rows = []
    for (cidx, tier), grp in g.groupby(["clip_idx", "tier"]):
        scores = [
            float(r["score"]) for _, r in grp.iterrows()
            if (int(cidx), int(r["q_idx"])) in crit_q
        ]
        if not scores:
            continue
        rows.append({
            "clip_idx": int(cidx),
            "tier": tier,
            "gt": TIER_GT[tier],
            "adqa_critical_mean": float(np.mean(scores)),
            "adqa_critical_yes_rate": float(np.mean(scores)),
        })
    return pd.DataFrame(rows)


def build_adqa_rank_gt(scores: pd.DataFrame, col: str) -> pd.DataFrame:
    """Alternative GT: rank tiers by observed ADQA score within each clip."""
    rows = []
    for cidx, g in scores.groupby("clip_idx"):
        g = g.sort_values(col, ascending=True).reset_index(drop=True)
        rank_map = {row["tier"]: i for i, row in g.iterrows()}
        for _, row in g.iterrows():
            rows.append({
                "clip_idx": cidx,
                "tier": row["tier"],
                "gt": rank_map[row["tier"]],
                "gt_original": row["gt"],
            })
    return pd.DataFrame(rows)


def eval_metric(df: pd.DataFrame, col: str, gt_col: str = "gt") -> dict:
    rho, rp = spearmanr(df[gt_col], df[col])
    tau, tp = kendalltau(df[gt_col], df[col])
    w, t = pairwise_wins(df, col)
    return {
        "metric": col,
        "spearman_rho": float(rho),
        "spearman_p": float(rp),
        "pairwise_wins": w,
        "pairwise_total": t,
        "full_order": full_order_clips(df, col),
        "n_clips": df["clip_idx"].nunique(),
    }


def inversion_report(scores: pd.DataFrame, col: str) -> pd.DataFrame:
    """Flag only GT violations: lower tier scoring above higher tier."""
    order = TIERS  # tier0 < tier1 < tier2 < tier3
    rows = []
    for cidx, g in scores.groupby("clip_idx"):
        by = dict(zip(g["tier"], g[col]))
        issues = []
        for i in range(len(order)):
            for j in range(i + 1, len(order)):
                lo, hi = order[i], order[j]
                if by.get(hi, -1) < by.get(lo, -1):
                    issues.append(f"{lo}>{hi}")
        rows.append({
            "clip_idx": cidx,
            "pro_score": by.get("tier3_va11y"),
            "tier2_score": by.get("tier2_vatex_long"),
            "tier1_score": by.get("tier1_vatex_short"),
            "tier0_score": by.get("tier0_cross"),
            "inversions": ";".join(issues) if issues else "clean",
            "n_inversions": len(issues),
        })
    return pd.DataFrame(rows).sort_values("n_inversions", ascending=False)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    scores = pd.read_csv(SCORES)
    crit = build_critical_adqa()
    crit = crit.merge(scores[["clip_idx", "tier", "clip_top3", "ensemble_mean_clip_top3"]], on=["clip_idx", "tier"], how="left")

    inv = inversion_report(scores, "adqa_v2_score")
    inv_clip = inversion_report(scores, "clip_top3")
    inv_ens = inversion_report(scores, "ensemble_mean_clip_top3")

    results = []
    for col in ["adqa_v2_score", "clip_top3", "clip_mean", "ensemble_mean_clip_top3", "adqa_critical_mean"]:
        sub = crit if col == "adqa_critical_mean" else scores
        if col not in sub.columns:
            continue
        results.append(eval_metric(sub, col))

    # Alternative GT: ADQA-derived ranking within each clip
    alt_rows = []
    for cidx, g in scores.groupby("clip_idx"):
        g = g.sort_values("adqa_v2_score")
        for rank, (_, row) in enumerate(g.iterrows()):
            alt_rows.append({"clip_idx": cidx, "tier": row["tier"], "gt_adqa_rank": rank})
    alt = pd.DataFrame(alt_rows)
    merged = scores.merge(alt, on=["clip_idx", "tier"])
    sub = merged[["clip_idx", "tier", "clip_top3", "gt_adqa_rank"]].dropna()
    r = eval_metric(sub.rename(columns={"gt_adqa_rank": "gt"}), "clip_top3")
    r["metric"] = "clip_top3_vs_adqa_rank_gt"
    results.append(r)

    res_df = pd.DataFrame(results)
    res_df.to_csv(OUT_CSV, index=False)

    inv.to_csv(OUT_DIR / "label_inversions_adqa.csv", index=False)
    inv_ens.to_csv(OUT_DIR / "label_inversions_ensemble.csv", index=False)

    bad = inv[inv["n_inversions"] > 0]
    lines = [
        "# Label audit — is tier3 always the best AD?",
        "",
        f"Clips with **any ADQA inversion** vs pro AD: **{len(bad)}/18**",
        "",
        "## Inversions by metric (pro AD not top)",
        "",
        inv.to_markdown(index=False),
        "",
        "## Metric correlation with original tier GT (0=cross … 3=pro)",
        "",
        res_df.to_markdown(index=False),
        "",
        "## Findings",
        "",
    ]
    if len(bad):
        for _, row in bad.head(5).iterrows():
            lines.append(
                f"- clip_{int(row['clip_idx']):02d}: {row['inversions']} "
                f"(pro={row['pro_score']:.2f}, tier2={row['tier2_score']:.2f})"
            )
    else:
        lines.append("- No ADQA inversions vs pro AD on any clip.")

    crit_inv = inversion_report(crit, "adqa_critical_mean")
    crit_bad = crit_inv[crit_inv["n_inversions"] > 0]
    lines.extend([
        "",
        f"## Critical-only ADQA inversions: {len(crit_bad)}/18",
        "",
        "If this count exceeds full ADQA inversions, **importance weighting** may fix label noise.",
    ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(res_df.to_string(index=False))
    print(f"\nADQA inversions: {len(bad)}/18")
    print(f"Critical-only inversions: {len(crit_bad)}/18")
    print(f"Wrote {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
