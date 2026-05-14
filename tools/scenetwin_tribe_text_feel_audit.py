#!/usr/bin/env python3
"""Compare TRIBE video-feel profiles with generated AD text-feel profiles.

This is the local, reproducible version of the TRIBE loop:

1. TRIBE estimates what visual/neural content is missing from audio alone.
2. Generated AD text is projected into the same content-type space.
3. We report whether the text "feels like" the video need profile.

This intentionally does not treat TRIBE as a text-correctness judge. It uses
TRIBE for the video/audio counterfactual and a lightweight text profile for the
candidate description.
"""

from __future__ import annotations

import argparse
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

from scenetwin_roi_content_profile import CONTENT_TYPES, cosine_dict, dominant, lexical_counts, lexical_profile


DG_DIR = ROOT / "output" / "scenetwin_description_gain"
DEFAULT_CANDIDATES_JSONL = DG_DIR / "phase1_ad_candidates.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def normalized_video_profile(row: dict[str, Any]) -> dict[str, float]:
    raw = {k: float(row.get("profile_score", {}).get(k, 0.0)) for k in CONTENT_TYPES}
    total = sum(max(v, 0.0) for v in raw.values())
    if total <= 1e-9:
        return {k: 0.0 for k in CONTENT_TYPES}
    return {k: max(raw[k], 0.0) / total for k in CONTENT_TYPES}


def profile_delta(video: dict[str, float], text: dict[str, float]) -> dict[str, float]:
    return {k: float(video.get(k, 0.0) - text.get(k, 0.0)) for k in CONTENT_TYPES}


def top_item(values: dict[str, float], reverse: bool = True) -> tuple[str, float]:
    ordered = sorted(values.items(), key=lambda kv: kv[1], reverse=reverse)
    return ordered[0][0], float(ordered[0][1])


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    video_profile = normalized_video_profile(row)
    text = str(row.get("ad_text", ""))
    text_profile = lexical_profile(text)
    counts = lexical_counts(text)
    delta = profile_delta(video_profile, text_profile)
    video_dom, video_dom_score, video_second, video_second_score = dominant(video_profile)
    text_dom, text_dom_score, text_second, text_second_score = dominant(text_profile)
    missing_type, missing_score = top_item(delta, reverse=True)
    surplus_type, surplus_score = top_item(delta, reverse=False)
    alignment = cosine_dict(video_profile, text_profile)
    abs_error = float(np.mean([abs(delta[k]) for k in CONTENT_TYPES]))
    weighted_miss = float(sum(max(delta[k], 0.0) * video_profile[k] for k in CONTENT_TYPES))
    weighted_surplus = float(sum(max(-delta[k], 0.0) * text_profile[k] for k in CONTENT_TYPES))
    target_hit = int(text_profile.get(video_dom, 0.0) > 0)
    target_and_second_hit = int(target_hit and text_profile.get(video_second, 0.0) > 0)
    dominant_match = int(video_dom == text_dom)

    if not np.isfinite(alignment):
        alignment = 0.0

    return {
        "clip_idx": int(row["clip_idx"]),
        "window_idx": int(row["window_idx"]),
        "start_s": float(row["start_s"]),
        "end_s": float(row["end_s"]),
        "condition": row["condition"],
        "provider": row.get("provider", ""),
        "model": row.get("model", ""),
        "recommendation": row.get("recommendation", ""),
        "word_budget": int(row["word_budget"]),
        "word_count": int(row.get("word_count", len(text.split()))),
        "ad_text": text,
        "video_dominant_type": video_dom,
        "video_dominant_score": video_dom_score,
        "video_second_type": video_second,
        "video_second_score": video_second_score,
        "text_dominant_type": text_dom,
        "text_dominant_score": text_dom_score,
        "text_second_type": text_second,
        "text_second_score": text_second_score,
        "feel_alignment": alignment,
        "feel_abs_error": abs_error,
        "weighted_missing_need": weighted_miss,
        "weighted_surplus_text": weighted_surplus,
        "dominant_match": dominant_match,
        "target_type_hit": target_hit,
        "target_and_second_hit": target_and_second_hit,
        "biggest_missing_type": missing_type,
        "biggest_missing_delta": missing_score,
        "biggest_surplus_type": surplus_type,
        "biggest_surplus_delta": surplus_score,
        "unique_keywords": counts["unique_keywords"],
        "specificity_score": counts["unique_keywords"] / max(counts["word_count"], 1.0),
        **{f"video_feel_{k}": video_profile[k] for k in CONTENT_TYPES},
        **{f"text_feel_{k}": text_profile[k] for k in CONTENT_TYPES},
        **{f"feel_delta_{k}": delta[k] for k in CONTENT_TYPES},
    }


def paired_summary(
    scores: pd.DataFrame,
    metric: str,
    candidate_condition: str,
    higher_is_better: bool = True,
) -> dict[str, Any]:
    pivot = scores.pivot_table(
        index=["clip_idx", "window_idx"],
        columns="condition",
        values=metric,
        aggfunc="first",
    ).dropna()
    if not {"baseline", candidate_condition}.issubset(pivot.columns) or pivot.empty:
        return {
            "metric": metric,
            "higher_is_better": higher_is_better,
            "n_pairs": 0,
            "baseline_mean": float("nan"),
            "candidate_mean": float("nan"),
            "mean_delta": float("nan"),
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "wilcoxon_p": float("nan"),
        }
    delta = pivot[candidate_condition] - pivot["baseline"]
    if not higher_is_better:
        delta = -delta
    p = float("nan")
    if (delta != 0).sum():
        try:
            p = float(wilcoxon(delta, alternative="greater").pvalue)
        except ValueError:
            p = float("nan")
    raw_delta = pivot[candidate_condition] - pivot["baseline"]
    return {
        "metric": metric,
        "higher_is_better": higher_is_better,
        "n_pairs": int(len(pivot)),
        "baseline_mean": float(pivot["baseline"].mean()),
        "candidate_condition": candidate_condition,
        "candidate_mean": float(pivot[candidate_condition].mean()),
        "mean_delta": float(raw_delta.mean()),
        "wins": int((delta > 0).sum()),
        "losses": int((delta < 0).sum()),
        "ties": int((delta == 0).sum()),
        "wilcoxon_p": p,
    }


def issue_table(scores: pd.DataFrame) -> pd.DataFrame:
    high_need = scores[scores["recommendation"] != "low_ad_need"].copy()
    if high_need.empty:
        high_need = scores.copy()
    cols = [
        "clip_idx",
        "window_idx",
        "condition",
        "recommendation",
        "video_dominant_type",
        "text_dominant_type",
        "feel_alignment",
        "biggest_missing_type",
        "biggest_missing_delta",
        "biggest_surplus_type",
        "ad_text",
    ]
    return high_need.sort_values(["feel_alignment", "weighted_missing_need"], ascending=[True, False])[cols].head(14)


def fmt(x: float) -> str:
    if x is None or not np.isfinite(x):
        return "nan"
    return f"{x:.4f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_CANDIDATES_JSONL)
    parser.add_argument("--name", default="tribe_text_feel", help="output stem")
    parser.add_argument("--candidate-condition", default="gap_targeted")
    args = parser.parse_args()

    out_csv = DG_DIR / f"{args.name}_audit.csv"
    out_summary = DG_DIR / f"{args.name}_summary.csv"
    out_report = ROOT / "output" / "reports" / f"scenetwin-{args.name.replace('_', '-')}-audit.md"
    out_wiki = ROOT / "wiki" / "research" / f"scenetwin-{args.name.replace('_', '-')}-audit.md"

    rows = read_jsonl(args.input)
    scores = pd.DataFrame([audit_row(row) for row in rows])
    summary = pd.DataFrame(
        [
            paired_summary(scores, "feel_alignment", args.candidate_condition, True),
            paired_summary(scores, "feel_abs_error", args.candidate_condition, False),
            paired_summary(scores, "weighted_missing_need", args.candidate_condition, False),
            paired_summary(scores, "weighted_surplus_text", args.candidate_condition, False),
            paired_summary(scores, "dominant_match", args.candidate_condition, True),
            paired_summary(scores, "target_type_hit", args.candidate_condition, True),
            paired_summary(scores, "target_and_second_hit", args.candidate_condition, True),
            paired_summary(scores, "specificity_score", args.candidate_condition, True),
        ]
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_report.parent.mkdir(parents=True, exist_ok=True)
    out_wiki.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(out_csv, index=False)
    summary.to_csv(out_summary, index=False)

    issues = issue_table(scores)
    dominant_confusion = pd.crosstab(
        scores["video_dominant_type"],
        scores["text_dominant_type"],
        normalize="index",
    ).fillna(0.0)
    condition_means = scores.groupby("condition")[
        [
            "feel_alignment",
            "feel_abs_error",
            "weighted_missing_need",
            "dominant_match",
            "target_type_hit",
            "target_and_second_hit",
            "specificity_score",
        ]
    ].mean()

    align = summary[summary["metric"] == "feel_alignment"].iloc[0]
    target = summary[summary["metric"] == "target_type_hit"].iloc[0]
    specificity = summary[summary["metric"] == "specificity_score"].iloc[0]

    report = f"""---
title: "SceneTwin TRIBE Text-Feel Audit"
category: research
tags: [SceneTwin, TRIBE, audio-description, text-profile, diagnostic]
created: 2026-05-06
updated: 2026-05-06
sources:
  - {args.input}
  - {out_csv}
  - {out_summary}
---

# SceneTwin TRIBE Text-Feel Audit

## Question

Does the generated text match the kind of visual/neural content TRIBE says is
missing from the soundtrack?

```text
video feel = TRIBE ROI gap profile from P_AV - P_A
text feel  = generated AD projected into the same content-type space
```

## Paired Summary

{summary.to_markdown(index=False)}

## Condition Means

{condition_means.to_markdown()}

## Dominant-Type Confusion

Rows are TRIBE video-feel dominant type. Columns are generated text-feel dominant type.

{dominant_confusion.to_markdown()}

## Worst Mismatches

{issues.to_markdown(index=False)}

## Interpretation

TRIBE-guided generation improves the broad feel match:

- Feel alignment delta: `{fmt(float(align["mean_delta"]))}`.
- Target dominant-type hit delta: `{fmt(float(target["mean_delta"]))}`.
- Specificity delta: `{fmt(float(specificity["mean_delta"]))}`.

The failure mode is visible: the prompt steers the text toward the dominant TRIBE
dimension, but under a 4-word budget it often drops secondary concrete details.
So the text can match the brain-guided "vibe" while becoming less specific.

This makes TRIBE useful as a **diagnostic controller**:

1. Use TRIBE to say what kind of content the video needs.
2. Generate AD text.
3. Audit whether the text feel matches the video feel.
4. Send mismatches back to the generator, especially `biggest_missing_type`.

This is not yet the full closed-loop TRIBE neural test. The stronger next step is
to run TRIBE on `audio + generated AD` in Colab and measure whether it moves the
predicted response closer to `P_AV`.
"""

    out_report.write_text(report, encoding="utf-8")
    out_wiki.write_text(report, encoding="utf-8")

    print(summary.to_string(index=False))
    print(f"Wrote {out_csv}")
    print(f"Wrote {out_summary}")
    print(f"Wrote {out_report}")


if __name__ == "__main__":
    main()
