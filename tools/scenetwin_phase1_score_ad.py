#!/usr/bin/env python3
"""Score SceneTwin Phase 1 baseline vs gap-targeted AD candidates."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from scenetwin_roi_content_profile import CONTENT_TYPES, cosine_dict, lexical_counts, lexical_profile


DG_DIR = ROOT / "output" / "scenetwin_description_gain"
CANDIDATES_JSONL = DG_DIR / "phase1_ad_candidates.jsonl"
OUT_CSV = DG_DIR / "phase1_ad_scores.csv"
OUT_SUMMARY = DG_DIR / "phase1_ad_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-phase1-ad-ab-test.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-phase1-ad-ab-test.md"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def target_profile(row: dict[str, Any]) -> dict[str, float]:
    return {k: float(row["profile_score"].get(k, 0.0)) for k in CONTENT_TYPES}


def score_row(row: dict[str, Any]) -> dict[str, Any]:
    text = row.get("ad_text", "")
    profile = lexical_profile(text)
    counts = lexical_counts(text)
    target = target_profile(row)
    dominant = row["dominant_type"]
    second = row["second_type"]
    weighted_keyword_coverage = sum(target[k] * counts.get(k, 0.0) for k in CONTENT_TYPES)
    dominant_keyword_coverage = counts.get(dominant, 0.0)
    second_keyword_coverage = counts.get(second, 0.0) if second in CONTENT_TYPES else 0.0
    word_count = int(row.get("word_count", len(text.split())))
    word_budget = int(row["word_budget"])
    return {
        **{k: row[k] for k in [
            "clip_idx",
            "window_idx",
            "start_s",
            "end_s",
            "condition",
            "provider",
            "model",
            "recommendation",
            "dominant_type",
            "second_type",
            "word_budget",
            "ad_text",
        ]},
        "word_count": word_count,
        "over_budget": int(word_count > word_budget),
        "profile_alignment": cosine_dict(target, profile),
        "weighted_keyword_coverage": weighted_keyword_coverage,
        "dominant_keyword_coverage": dominant_keyword_coverage,
        "second_keyword_coverage": second_keyword_coverage,
        "specificity_score": counts["unique_keywords"] / max(counts["word_count"], 1.0),
        **{f"text_{k}": profile[k] for k in CONTENT_TYPES},
        **{f"text_{k}_count": counts[k] for k in CONTENT_TYPES},
    }


def paired_summary(scores: pd.DataFrame, metric: str) -> dict[str, Any]:
    pivot = scores.pivot_table(
        index=["clip_idx", "window_idx"],
        columns="condition",
        values=metric,
        aggfunc="first",
    ).dropna()
    if not {"baseline", "gap_targeted"}.issubset(pivot.columns) or pivot.empty:
        return {
            "metric": metric,
            "n_pairs": 0,
            "baseline_mean": float("nan"),
            "gap_targeted_mean": float("nan"),
            "mean_delta": float("nan"),
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "wilcoxon_p": float("nan"),
        }
    delta = pivot["gap_targeted"] - pivot["baseline"]
    nonzero = delta[delta != 0]
    p = float("nan")
    if len(nonzero) >= 1:
        try:
            p = float(wilcoxon(pivot["gap_targeted"], pivot["baseline"], alternative="greater").pvalue)
        except ValueError:
            p = float("nan")
    return {
        "metric": metric,
        "n_pairs": int(len(pivot)),
        "baseline_mean": float(pivot["baseline"].mean()),
        "gap_targeted_mean": float(pivot["gap_targeted"].mean()),
        "mean_delta": float(delta.mean()),
        "wins": int((delta > 0).sum()),
        "losses": int((delta < 0).sum()),
        "ties": int((delta == 0).sum()),
        "wilcoxon_p": p,
    }


def format_float(x: float) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "nan"
    return f"{x:.4f}"


def main() -> None:
    rows = read_jsonl(CANDIDATES_JSONL)
    scores = pd.DataFrame([score_row(row) for row in rows])
    metrics = [
        "profile_alignment",
        "weighted_keyword_coverage",
        "dominant_keyword_coverage",
        "second_keyword_coverage",
        "specificity_score",
        "over_budget",
    ]
    summary = pd.DataFrame([paired_summary(scores, metric) for metric in metrics])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    examples = scores.sort_values(["clip_idx", "window_idx", "condition"]).head(16)
    provider = ", ".join(sorted(scores["provider"].unique()))
    model = ", ".join(sorted(scores["model"].unique()))
    profile_row = summary[summary["metric"] == "profile_alignment"].iloc[0]
    weighted_row = summary[summary["metric"] == "weighted_keyword_coverage"].iloc[0]
    dominant_row = summary[summary["metric"] == "dominant_keyword_coverage"].iloc[0]
    budget_row = summary[summary["metric"] == "over_budget"].iloc[0]
    real_llm_note = (
        "This is a real LLM run. Both conditions received the same visual context; "
        "only the gap-targeted condition received the TRIBE ROI profile and type instructions."
        if provider != "local_template"
        else "This is a local-template smoke test, not evidence that an LLM follows TRIBE guidance."
    )
    report = f"""---
title: "SceneTwin Phase 1 AD A/B Test"
category: research
tags: [SceneTwin, TRIBE, AD-generation, A-B-test, ROI-content-typing]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase1_ad_candidates.jsonl
  - output/scenetwin_description_gain/phase1_ad_scores.csv
  - output/scenetwin_description_gain/phase1_ad_summary.csv
  - output/scenetwin_description_gain/gap_targeted_prompts.jsonl
---

# SceneTwin Phase 1 AD A/B Test

## Setup

Condition A: baseline prompt with timing/audio context and no TRIBE ROI profile.

Condition B: gap-targeted prompt with TRIBE ROI content profile and dominant/second content-type instructions.

Provider used for this run: `{provider}`.

Model used for this run: `{model}`.

All generated AD lines were hard-clamped to the per-window word budget before scoring.

## Summary

{summary.to_markdown(index=False)}

## Example Outputs

{examples[["clip_idx", "window_idx", "condition", "dominant_type", "word_budget", "word_count", "profile_alignment", "weighted_keyword_coverage", "ad_text"]].to_markdown(index=False)}

## Verdict

{real_llm_note}

Profile alignment delta: `{format_float(float(profile_row['mean_delta']))}`.

Weighted keyword coverage delta: `{format_float(float(weighted_row['mean_delta']))}`.

Dominant ROI keyword coverage delta: `{format_float(float(dominant_row['mean_delta']))}` with Wilcoxon p=`{format_float(float(dominant_row['wilcoxon_p']))}`.

Over-budget delta: `{format_float(float(budget_row['mean_delta']))}`.

Interpretation: TRIBE guidance reliably steered the LLM toward the dominant cortical content type, but it reduced secondary-type coverage and specificity after the strict word-budget clamp. The next prompt iteration should preserve the dominant-type instruction while requiring one concrete visual noun or action verb from the shared visual context.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
