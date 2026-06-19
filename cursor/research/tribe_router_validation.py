"""Validate the TRIBE blind-spot/router story against existing experiments.

This deliberately does not ask whether TRIBE improves global rho. That result is
weak and already known. It asks the narrower paper question:

  Does a TRIBE-derived target improve the questions/windows it claims to target,
  compared with generic or VLM-selected targeting?

The script consolidates prior runs and writes one report with positive and
negative evidence.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cursor" / "research" / "output"
REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-router-validation.md"
WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-router-validation.md"
SUMMARY_JSON = OUT / "tribe_router_validation_summary.json"


def exact_one_sided_sign_p(wins: int, losses: int) -> float | None:
    """P(X >= wins), X~Binomial(wins+losses, 0.5). Ties excluded."""
    n = wins + losses
    if n == 0:
        return None
    num = sum(math.comb(n, k) for k in range(wins, n + 1))
    return num / (2 ** n)


def paired_condition_summary(path: Path, high: str, low: str,
                             label: str, matched_col: str = "matched") -> list[dict]:
    df = pd.read_csv(path)
    rows = []
    subsets = [("all", df.index >= 0)]
    if matched_col in df.columns:
        subsets.append(("matched", df[matched_col] == 1))
    for subset, mask in subsets:
        piv = (
            df[mask]
            .pivot_table(index=["video_id", "q_idx"], columns="condition",
                         values="score", aggfunc="mean")
            .dropna()
        )
        if not {high, low}.issubset(piv.columns):
            continue
        diff = piv[high] - piv[low]
        wins = int((diff > 0).sum())
        losses = int((diff < 0).sum())
        ties = int((diff == 0).sum())
        rows.append({
            "experiment": label,
            "source": str(path.relative_to(ROOT)),
            "subset": subset,
            "n_questions": int(len(piv)),
            "n_clips": int(piv.reset_index()["video_id"].nunique()),
            f"{low}_mean": float(piv[low].mean()),
            f"{high}_mean": float(piv[high].mean()),
            "delta": float(diff.mean()),
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "sign_p_one_sided": exact_one_sided_sign_p(wins, losses),
        })
    return rows


def pro_priority_summary(path: Path) -> dict:
    df = pd.read_csv(path)
    diff = df["tribe_vs_pro"] - df["vlm_vs_pro"]
    wins = int((diff > 0).sum())
    losses = int((diff < 0).sum())
    ties = int((diff == 0).sum())
    return {
        "source": str(path.relative_to(ROOT)),
        "n_clips": int(len(df)),
        "tribe_vs_pro_mean": float(df["tribe_vs_pro"].mean()),
        "vlm_vs_pro_mean": float(df["vlm_vs_pro"].mean()),
        "uniform_vs_pro_mean": float(df["uniform_vs_pro"].mean()),
        "tribe_minus_vlm": float(diff.mean()),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "sign_p_tribe_gt_vlm": exact_one_sided_sign_p(wins, losses),
        "tribe_top_match": float((df["tribe_top"] == df["pro_top"]).mean()),
        "vlm_top_match": float((df["vlm_top"] == df["pro_top"]).mean()),
    }


def router_inventory() -> dict:
    cases = pd.read_csv(OUT / "tribe_blind_spot_cases.csv")
    windows = pd.read_csv(OUT / "tribe_blind_spot_windows.csv")
    summary = pd.read_csv(OUT / "tribe_blind_spot_clip_summary.csv")
    ext = summary[summary["corpus"] == "external"]
    return {
        "n_clips": int(summary["clip_key"].nunique()),
        "n_external_clips": int(ext["clip_key"].nunique()),
        "n_windows": int(len(windows)),
        "n_cases": int(len(cases)),
        "case_counts": {k: int(v) for k, v in cases["case_id"].value_counts().items()},
        "route_counts": {k: int(v) for k, v in windows["route"].value_counts().items()},
        "external_type_shift_lt_0_5": int((ext["scene_agent_time_rho"] < 0.5).sum()),
        "external_peak_apart": int((ext["scene_agent_peak_apart"] == 1).sum()),
        "external_top1_vs_uniform_mean": float(ext["top1_vs_uniform"].mean()),
    }


def markdown_table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return "_No rows._"
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        vals = []
        for col in columns:
            val = row.get(col)
            if val is None:
                vals.append("")
            elif isinstance(val, float):
                vals.append(f"{val:.4g}")
            else:
                vals.append(str(val).replace("|", "/"))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    evidence = []

    evidence += paired_condition_summary(
        OUT / "tribe_necessity_perq.csv",
        high="tribe",
        low="vlm",
        label="TRIBE target vs VLM target (vision-only VLM)",
    )
    evidence += paired_condition_summary(
        OUT / "tribe_necessity_rematch_perq.csv",
        high="tribe",
        low="vlm",
        label="TRIBE target vs VLM target (VLM gets transcript)",
    )
    evidence += paired_condition_summary(
        OUT / "tribe_crossjudge_gpt5_perq.csv",
        high="gap_targeted",
        low="baseline",
        label="Gap-targeted AD vs generic AD (GPT-5 judge, 60 clips)",
    )
    evidence += paired_condition_summary(
        OUT / "tribe_crossjudge_opus_17_perq.csv",
        high="gap_targeted",
        low="baseline",
        label="Gap-targeted AD vs generic AD (Opus judge, 17 clips)",
    )
    evidence += paired_condition_summary(
        OUT / "tribe_crossjudge_opus_subset_perq.csv",
        high="gap_targeted",
        low="baseline",
        label="Gap-targeted AD vs generic AD (Opus judge, 15-clip subset)",
    )
    evidence += paired_condition_summary(
        OUT / "tribe_surgical_adqa_perq.csv",
        high="gap_targeted",
        low="baseline",
        label="Surgical TRIBE ADQA target vs generic AD",
    )

    pro = pro_priority_summary(OUT / "tribe_vs_pro_priority.csv")
    router = router_inventory()

    payload = {
        "evidence": evidence,
        "pro_priority_negative_result": pro,
        "router_inventory": router,
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    matched_rows = [r for r in evidence if r["subset"] == "matched"]
    all_rows = [r for r in evidence if r["subset"] == "all"]
    case_rows = [
        {"case_id": k, "count": v}
        for k, v in router["case_counts"].items()
    ]

    report = f"""---
title: "TRIBE Router Validation"
category: research
tags: [SceneTwin, TRIBE, routing, validation, negative-results]
created: 2026-05-31
updated: 2026-05-31
sources:
  - cursor/research/output/tribe_router_validation_summary.json
  - cursor/research/output/tribe_necessity_perq.csv
  - cursor/research/output/tribe_necessity_rematch_perq.csv
  - cursor/research/output/tribe_crossjudge_gpt5_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_17_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_subset_perq.csv
  - cursor/research/output/tribe_surgical_adqa_perq.csv
  - cursor/research/output/tribe_vs_pro_priority.csv
---

# TRIBE Router Validation

## Bottom Line

The paper-worthy TRIBE claim is **not** global score improvement. The tiny rho
lift is the wrong story.

The defensible claim is narrower: TRIBE-derived blind-spot targets improve the
questions/windows they explicitly target. This survives several judging runs,
especially on matched questions. The claim does **not** extend to predicting the
overall content distribution of professional AD; that test is negative.

## Router Inventory

- Clips: {router["n_clips"]} total, {router["n_external_clips"]} external.
- Windows: {router["n_windows"]}.
- Cases: {router["n_cases"]}.
- External clips with scene/action time correlation < 0.5: {router["external_type_shift_lt_0_5"]}/{router["n_external_clips"]}.
- External clips with scene/action peaks at different timesteps: {router["external_peak_apart"]}/{router["n_external_clips"]}.
- Mean external top-1 concentration: {router["external_top1_vs_uniform_mean"]:.2f}x uniform timing.

{markdown_table(case_rows, ["case_id", "count"])}

## Matched-Target Evidence

These are the strongest rows: only questions/windows whose required evidence
matches the TRIBE-selected target type.

{markdown_table(matched_rows, ["experiment", "n_clips", "n_questions", "delta", "wins", "losses", "ties", "sign_p_one_sided"])}

## Whole-Question Evidence

Whole-question averages are weaker, which is expected. The router is surgical:
it should move targeted questions more than unrelated questions.

{markdown_table(all_rows, ["experiment", "n_clips", "n_questions", "delta", "wins", "losses", "ties", "sign_p_one_sided"])}

## Negative Result: Professional AD Priority

TRIBE does **not** beat the VLM at matching the overall content-type profile of
professional AD.

| comparison | value |
| --- | ---: |
| n clips | {pro["n_clips"]} |
| mean cosine(TRIBE, pro AD) | {pro["tribe_vs_pro_mean"]:.3f} |
| mean cosine(VLM, pro AD) | {pro["vlm_vs_pro_mean"]:.3f} |
| mean cosine(uniform, pro AD) | {pro["uniform_vs_pro_mean"]:.3f} |
| TRIBE - VLM | {pro["tribe_minus_vlm"]:+.3f} |
| TRIBE wins/losses/ties | {pro["wins"]}/{pro["losses"]}/{pro["ties"]} |
| top-type exact match: TRIBE | {pro["tribe_top_match"]:.0%} |
| top-type exact match: VLM | {pro["vlm_top_match"]:.0%} |

Interpretation: TRIBE is not a general replacement for a VLM or human describer.
Its useful role is localized blind-spot targeting, not global AD topic modeling.

## Paper Framing

Use this as a Paper B / systems-routing result:

> A brain-predictive audiovisual encoder can expose typed, time-localized
> accessibility blind spots that are invisible to global score metrics. When AD
> generation or ADQA is conditioned on those blind spots, matched visual-evidence
> questions improve consistently across judges. The effect is surgical, not a
> global metric lift.

Do not claim:

- TRIBE improves global rho.
- TRIBE predicts the full professional AD content distribution.
- TRIBE replaces VLM scoring.

Do claim:

- TRIBE identifies when and what kind of visual access intervention is needed.
- Matched-question gains replicate across independent judge runs.
- The router can decide where to spend expensive human/VLM review budget.
"""

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    WIKI.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    WIKI.write_text(report, encoding="utf-8")

    print("TRIBE router validation")
    print(f"  wrote {SUMMARY_JSON}")
    print(f"  wrote {REPORT}")
    print("\nMatched evidence:")
    for row in matched_rows:
        print(
            f"  {row['experiment']}: delta={row['delta']:+.3f}, "
            f"{row['wins']}W/{row['losses']}L/{row['ties']}T, "
            f"p={row['sign_p_one_sided']}"
        )
    print(
        "\nPro-priority negative: "
        f"TRIBE={pro['tribe_vs_pro_mean']:.3f}, "
        f"VLM={pro['vlm_vs_pro_mean']:.3f}, "
        f"uniform={pro['uniform_vs_pro_mean']:.3f}"
    )


if __name__ == "__main__":
    main()
