#!/usr/bin/env python3
"""Research analysis: TRIBE-guided agency map for BLV video access.

Breakthrough framing:
- Static AD assumes the author knows what every BLV viewer needs in advance.
- Custom/VQA systems give users agency, but they do not know when agency is
  most valuable.
- TRIBE can provide that missing control signal from P_AV - P_A: where the
  original audio leaves high visual debt, especially when there is no clean
  narration slot.

This script joins TRIBE debt with ADQA question failures to rank clips/windows
that should become interactive, queryable, or human-reviewed rather than merely
passively described.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEBT_CSV = ROOT / "cursor" / "output" / "neural_accessibility_debt.csv"
QUESTIONS_CSV = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_questions.csv"
GRADES_CSV = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_v2" / "adqa_v2_grades.csv"
OUT_DIR = ROOT / "cursor" / "output"
OUT_CSV = OUT_DIR / "neural_agency_map.csv"
OUT_WINDOWS = OUT_DIR / "neural_agency_windows.csv"
OUT_REPORT = ROOT / "cursor" / "findings" / "neural-agency-map.md"
NEED_WINDOWS = ROOT / "output" / "scenetwin_timing_20clip" / "need" / "coarse_need_windows.csv"


def normalize(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    lo = s.min()
    hi = s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series([0.0] * len(s), index=s.index)
    return (s - lo) / (hi - lo)


def rank_corr(a: pd.Series, b: pd.Series) -> float:
    data = pd.DataFrame({"a": a, "b": b}).dropna()
    if len(data) < 2:
        return float("nan")
    return float(data["a"].rank().corr(data["b"].rank()))


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for record in df[columns].to_dict(orient="records"):
        values = []
        for col in columns:
            value = record[col]
            if isinstance(value, float):
                values.append("unlabeled" if pd.isna(value) else f"{value:.3f}")
            elif pd.isna(value):
                values.append("unlabeled")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def load_pro_adqa_summary() -> pd.DataFrame:
    questions = pd.read_csv(QUESTIONS_CSV)
    grades = pd.read_csv(GRADES_CSV)
    pro = grades[grades["tier"] == "tier3_va11y"].copy()
    joined = pro.merge(
        questions[["clip_idx", "q_idx", "importance", "question", "required_visual_evidence"]],
        on=["clip_idx", "q_idx"],
        how="left",
    )
    joined["critical"] = joined["importance"].astype(str).str.lower().eq("critical")
    joined["miss"] = pd.to_numeric(joined["score"], errors="coerce").fillna(0) < 0.5
    joined["critical_miss"] = joined["critical"] & joined["miss"]
    summary = joined.groupby("clip_idx").agg(
        pro_questions=("q_idx", "count"),
        pro_yes_rate=("score", "mean"),
        pro_misses=("miss", "sum"),
        pro_miss_rate=("miss", "mean"),
        critical_questions=("critical", "sum"),
        critical_misses=("critical_miss", "sum"),
    )
    summary["critical_miss_rate"] = summary["critical_misses"] / summary["critical_questions"].replace(0, pd.NA)

    missed = joined[joined["critical_miss"]].copy()
    examples = (
        missed.groupby("clip_idx")
        .head(2)
        .groupby("clip_idx")["question"]
        .apply(lambda s: " | ".join(s.astype(str)))
    )
    summary["missed_critical_examples"] = examples
    return summary.reset_index()


def intervention(row: pd.Series) -> str:
    agency = row["agency_score"]
    critical_miss = row.get("critical_miss_rate", 0.0)
    collision = row.get("collision_debt_frac", 0.0)
    slotable = row.get("slotable_debt_frac", 0.0)
    risk = row.get("risk_score", 0.0)
    if collision >= 0.65 and critical_miss >= 0.5:
        return "interactive_vqa_first"
    if agency >= 0.45 and critical_miss >= 0.4:
        return "interactive_vqa_first"
    if risk >= 0.20 or row.get("target", 0.0) == 1:
        return "human_review"
    if collision >= 0.65:
        return "extended_or_integrated_ad"
    if slotable >= 0.55:
        return "standard_inserted_ad"
    return "lightweight_or_no_ad"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)

    debt = pd.read_csv(DEBT_CSV)
    adqa = load_pro_adqa_summary()
    df = debt.merge(adqa, on="clip_idx", how="left")

    df["critical_miss_rate"] = pd.to_numeric(df["critical_miss_rate"], errors="coerce").fillna(0.0)
    df["pro_miss_rate"] = pd.to_numeric(df["pro_miss_rate"], errors="coerce").fillna(0.0)
    df["collision_norm"] = normalize(df["collision_debt"])
    df["slotable_norm"] = normalize(df["slotable_debt"])
    df["unanswered_norm"] = normalize(df["critical_miss_rate"])
    df["risk_norm"] = normalize(df["risk_score"].fillna(0.0))

    # Agency means: the video contains inaccessible visual state, passive AD
    # already misses some of it, and the audio timeline makes fixed narration
    # difficult.
    df["agency_score"] = (
        0.35 * df["collision_norm"]
        + 0.25 * df["slotable_norm"]
        + 0.25 * df["unanswered_norm"]
        + 0.15 * df["risk_norm"]
    )
    df["agency_rank"] = df["agency_score"].rank(ascending=False, method="min").astype(int)
    df["recommended_intervention"] = df.apply(intervention, axis=1)
    df = df.sort_values(["agency_rank", "clip_idx"])
    df.to_csv(OUT_CSV, index=False)

    need = pd.read_csv(NEED_WINDOWS)
    top_clips = set(df.head(6)["clip_idx"].tolist())
    windows = need[need["clip_idx"].isin(top_clips)].copy()
    windows["window_agency"] = windows["need_score"] * (
        0.6 * windows["speech_density"] + 0.4 * (1.0 - windows["speech_density"])
    )
    windows = windows.merge(
        df[["clip_idx", "agency_rank", "recommended_intervention", "category"]],
        on="clip_idx",
        how="left",
    ).sort_values(["agency_rank", "clip_idx", "window_agency"], ascending=[True, True, False])
    windows.to_csv(OUT_WINDOWS, index=False)

    labeled = df[df["all4_mean_full_order"].notna()].copy()
    correlations = {
        "agency_vs_pro_miss_rate": rank_corr(labeled["agency_score"], labeled["pro_miss_rate"]),
        "agency_vs_critical_miss_rate": rank_corr(labeled["agency_score"], labeled["critical_miss_rate"]),
        "agency_vs_full_order": rank_corr(labeled["agency_score"], labeled["all4_mean_full_order"]),
        "agency_vs_tier3_margin": rank_corr(labeled["agency_score"], labeled["all4_mean_tier3_margin"]),
    }

    intervention_counts = df["recommended_intervention"].value_counts().to_dict()
    top = df.head(8)
    top_windows = windows.groupby("clip_idx").head(2)
    cols = [
        "agency_rank",
        "clip_idx",
        "category",
        "agency_score",
        "recommended_intervention",
        "critical_miss_rate",
        "collision_debt_frac",
        "slotable_debt_frac",
        "risk_rank",
        "quality_risk",
    ]
    window_cols = [
        "clip_idx",
        "category",
        "start_s",
        "end_s",
        "need_score",
        "speech_density",
        "window_agency",
        "recommended_intervention",
    ]

    report = f"""# Neural Agency Map

Generated by `cursor/neural_agency_map.py`.

## Validation note

This is a retrospective map because `agency_score` includes ADQA miss evidence.
Use it for hypothesis generation and protocol design, not as proof of an
upstream predictor. The validated upstream TRIBE result is the escalation gate
in `cursor/findings/tribe-escalation-gate-validation.md`.

## Breakthrough claim

The next use of TRIBE for BLV access should be **agency allocation**, not just
audio-description scoring or routing.

Current BLV systems are splitting into two families:

- high-quality generated/static AD,
- customizable AD plus video question answering.

TRIBE can connect them. `P_AV - P_A` tells us where the original audio leaves
visual information inaccessible. Speech density tells us whether standard AD
can fit. ADQA misses tell us whether even professional/passive AD fails to
answer likely viewer questions.

The research object becomes:

> Where should a BLV viewer be given control, query access, pauseable detail, or
> human-reviewed description?

## Current evidence

- Clips with TRIBE debt: **{len(df)}**
- Clips with evaluator labels: **{len(labeled)}**
- Recommended intervention counts: `{intervention_counts}`

Rank correlations on labeled clips:

| Signal | Spearman rho |
|---|---:|
| agency_score vs pro AD miss rate | {correlations['agency_vs_pro_miss_rate']:.3f} |
| agency_score vs critical miss rate | {correlations['agency_vs_critical_miss_rate']:.3f} |
| agency_score vs full tier order | {correlations['agency_vs_full_order']:.3f} |
| agency_score vs tier3 margin | {correlations['agency_vs_tier3_margin']:.3f} |

## Top agency clips

{markdown_table(top, cols)}

## Highest-agency windows in top clips

{markdown_table(top_windows, window_cols)}

## Interpretation

This is different from the previous Neural Accessibility Debt artifact:

- Debt says what kind of accessibility intervention is technically required.
- Agency says where a BLV viewer should be given control because passive AD is
  likely underspecified or temporally constrained.

The breakthrough domain is **interactive accessible video**, not better caption
scoring. TRIBE becomes the scheduler for when a system should stop pretending a
single static narration is enough.

## Research hypothesis

For high-agency clips, user-driven VQA or pauseable integrated AD should beat
standard AD on:

1. BLV question-answer accuracy,
2. perceived control,
3. listener burden,
4. story/task comprehension,
5. trust in the accessibility layer.

The falsifiable claim is not that TRIBE writes better words. It is that TRIBE
can predict when a viewer needs **agency**.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_WINDOWS}")
    print(f"Wrote {OUT_REPORT}")
    print("\nIntervention counts:")
    print(df["recommended_intervention"].value_counts().to_string())
    print("\nCorrelations:")
    for key, value in correlations.items():
        print(f"{key}: {value:.3f}")


if __name__ == "__main__":
    main()
