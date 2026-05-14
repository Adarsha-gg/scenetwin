#!/usr/bin/env python3
"""LLM validation of TRIBE per-window content typing against professional AD.

This tests whether the failed Phase 2 typing validation was caused by the
hand-written pro-AD lexicon or by TRIBE's ROI typing itself. It keeps the same
window alignment and TRIBE dominant labels from `phase2_typing_validation.csv`,
then asks an LLM to classify each aligned pro-AD snippet into the six SceneTwin
content types without seeing the TRIBE answer.

Outputs:
  output/scenetwin_description_gain/phase2_llm_typing_validation.csv
  output/scenetwin_description_gain/phase2_llm_typing_confusion.csv
  output/reports/scenetwin-phase2-llm-typing-validation.md
  wiki/research/scenetwin-phase2-llm-typing-validation.md
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
INPUT_CSV = DG_DIR / "phase2_typing_validation.csv"
OUT_PER_WINDOW = DG_DIR / "phase2_llm_typing_validation.csv"
OUT_CONFUSION = DG_DIR / "phase2_llm_typing_confusion.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-phase2-llm-typing-validation.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-phase2-llm-typing-validation.md"
ENV_PATH = ROOT / ".env"

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]

TYPE_DEFINITIONS = {
    "motion_action": "visible actions, movements, causal events, gestures, body/object motion",
    "scene_spatial": "place, setting, background, layout, spatial relation, where things are",
    "face_character": "people/characters, identity, face, expression, attention, social presence",
    "object_body": "important objects, props, food/items, body parts when they are the described visual focus",
    "visual_form": "color, shape, size, texture, lighting, visual appearance/framing",
    "language_auditory": "spoken/written language or sound cues emphasized by the AD text",
}


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def parse_json_object(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def validate_label(label: str) -> str:
    if label not in CONTENT_TYPES:
        return "unscored"
    return label


def build_prompt(items: list[dict[str, Any]]) -> str:
    type_block = "\n".join(f"- {k}: {v}" for k, v in TYPE_DEFINITIONS.items())
    item_block = json.dumps(items, indent=2)
    return f"""Classify professional audio-description snippets by their primary visual content type.

Use exactly one primary_type from this list:
{type_block}

Rules:
- Judge what the AD snippet itself is mainly trying to convey to a blind/low-vision viewer.
- Do not infer the answer from TRIBE, brain ROIs, or metric scores. You are not given those.
- If the snippet mentions multiple things, choose the type that carries the most AD utility.
- Prefer motion_action for visible actions/events over scene_spatial when both are present.
- Prefer object_body when a named object/prop/body part is the described focus.
- Use visual_form only when appearance/color/shape/texture/framing is the main point.
- Return JSON only.

Input items:
{item_block}

Output schema:
{{
  "classifications": [
    {{
      "id": 0,
      "primary_type": "motion_action",
      "secondary_type": "object_body",
      "confidence": 0.0,
      "rationale": "short reason under 12 words"
    }}
  ]
}}
"""


def call_anthropic(items: list[dict[str, Any]], model: str) -> list[dict[str, Any]]:
    from anthropic import Anthropic

    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=3000,
        temperature=0,
        messages=[{"role": "user", "content": build_prompt(items)}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    parsed = parse_json_object(text)
    return list(parsed.get("classifications", []))


def local_fallback(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Small deterministic fallback for offline smoke tests.

    This is not evidence for the experiment; it only keeps the file runnable.
    """
    patterns = {
        "motion_action": r"\b(throw|throws|throwing|pins?|holds?|counts?|eats?|eating|drinks?|writes?|cough|takes?|moves?)\b",
        "scene_spatial": r"\b(kitchen|restaurant|wall|behind|inside|place|setting|tray|table|counter)\b",
        "face_character": r"\b(man|chef|person|people|he|his|face|eyes|smile|hoodie|bald)\b",
        "object_body": r"\b(tomato|knife|hamburger|burger|soda|ketchup|hand|mouth|body|camera)\b",
        "visual_form": r"\b(red|gray|small|large|bright|dark|shape|color|round)\b",
        "language_auditory": r"\b(spanish|countdown|says|speaking|words|text|audio|sound)\b",
    }
    out = []
    for item in items:
        text = item["pro_ad_text"].lower()
        scores = {
            label: len(re.findall(pattern, text, flags=re.IGNORECASE))
            for label, pattern in patterns.items()
        }
        label, score = max(scores.items(), key=lambda kv: (kv[1], -CONTENT_TYPES.index(kv[0])))
        if score == 0:
            label = "unscored"
        out.append({
            "id": item["id"],
            "primary_type": label,
            "secondary_type": "unscored",
            "confidence": 0.0,
            "rationale": "offline fallback",
        })
    return out


def classify_rows(df: pd.DataFrame, provider: str, model: str, batch_size: int) -> tuple[list[dict[str, Any]], str]:
    rows = []
    actual_provider = provider
    if provider == "auto":
        actual_provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "local_fallback"

    for start in range(0, len(df), batch_size):
        batch = df.iloc[start:start + batch_size]
        items = [
            {
                "id": int(row.row_id),
                "clip_idx": int(row.clip_idx),
                "window_idx": int(row.window_idx),
                "time_window_s": [round(float(row.start_s), 3), round(float(row.end_s), 3)],
                "recommendation": row.recommendation,
                "pro_ad_text": row.pro_ad_text,
            }
            for row in batch.itertuples(index=False)
        ]
        if actual_provider == "anthropic":
            classified = call_anthropic(items, model)
        else:
            classified = local_fallback(items)
        by_id = {int(item.get("id")): item for item in classified if "id" in item}
        for item in items:
            c = by_id.get(item["id"], {})
            rows.append({
                "row_id": item["id"],
                "llm_primary": validate_label(str(c.get("primary_type", "unscored"))),
                "llm_secondary": validate_label(str(c.get("secondary_type", "unscored"))),
                "llm_confidence": float(c.get("confidence", 0.0) or 0.0),
                "llm_rationale": str(c.get("rationale", ""))[:160],
            })
    return rows, actual_provider


def agreement(df: pd.DataFrame, pred_col: str, target_col: str = "tribe_dominant") -> tuple[int, int, float]:
    scored = df[df[pred_col] != "unscored"].copy()
    n = len(scored)
    wins = int((scored[pred_col] == scored[target_col]).sum())
    rate = wins / n if n else float("nan")
    return wins, n, rate


def rate_fmt(rate: float) -> str:
    if math.isnan(rate):
        return "nan"
    return f"{rate:.1%}"


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["auto", "anthropic", "local-fallback"], default="auto")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--batch-size", type=int, default=12)
    args = parser.parse_args()

    base = pd.read_csv(INPUT_CSV)
    base = base[base["pro_ad_dominant"] != "unscored"].copy().reset_index(drop=True)
    base.insert(0, "row_id", range(len(base)))

    llm_rows, actual_provider = classify_rows(base, args.provider.replace("-", "_"), args.model, args.batch_size)
    llm = pd.DataFrame(llm_rows)
    merged = base.merge(llm, on="row_id", how="left")
    merged["llm_agree"] = merged["llm_primary"] == merged["tribe_dominant"]
    merged["lexicon_agree"] = merged["pro_ad_dominant"] == merged["tribe_dominant"]
    merged["llm_matches_lexicon"] = merged["llm_primary"] == merged["pro_ad_dominant"]
    merged["provider"] = actual_provider
    merged["model"] = args.model if actual_provider == "anthropic" else "local-fallback"

    OUT_PER_WINDOW.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(OUT_PER_WINDOW, index=False)

    confusion = pd.crosstab(
        merged["llm_primary"],
        merged["tribe_dominant"],
        rownames=["llm_primary_pro_ad"],
        colnames=["tribe_dominant"],
        dropna=False,
    )
    confusion.to_csv(OUT_CONFUSION)

    lex_wins, lex_n, lex_rate = agreement(merged, "pro_ad_dominant")
    llm_wins, llm_n, llm_rate = agreement(merged, "llm_primary")
    llm_lex_wins = int((merged["llm_primary"] == merged["pro_ad_dominant"]).sum())
    llm_lex_rate = llm_lex_wins / len(merged) if len(merged) else float("nan")
    high = merged[merged["recommendation"].isin([
        "standard_ad_slot",
        "extended_or_integrated_ad",
        "inspect_visual_event",
    ])]
    high_lex = float(high["lexicon_agree"].mean()) if len(high) else float("nan")
    high_llm = float(high["llm_agree"].mean()) if len(high) else float("nan")
    chance = 1.0 / len(CONTENT_TYPES)

    detail_cols = [
        "clip_idx",
        "window_idx",
        "start_s",
        "end_s",
        "recommendation",
        "tribe_dominant",
        "pro_ad_dominant",
        "llm_primary",
        "llm_agree",
        "llm_rationale",
        "pro_ad_text",
    ]

    if llm_rate >= 0.5:
        verdict = (
            "LLM-classified pro AD agrees with TRIBE often enough to justify scaling "
            "the Glasser typing experiment beyond two clips. The old lexicon was the bottleneck."
        )
        decision = "Scale Glasser typing to the 20-clip set before killing the ROI-typing pitch."
    elif llm_rate >= 1.5 * chance:
        verdict = (
            "LLM classification improves the validation but still does not clear a closed-loop bar. "
            "The typing signal may be weak, or the proportional window alignment is still too noisy."
        )
        decision = "Do not run Phase 2 closed loop yet; either scale validation or pivot to timing-only."
    else:
        verdict = (
            "LLM-classified pro AD remains near chance against TRIBE. The failure is not just the small lexicon."
        )
        decision = "Drop ROI typing from the headline and keep TRIBE for AD-need timing."

    report = f"""---
title: "SceneTwin Phase 2 LLM Typing Validation"
category: research
tags: [SceneTwin, TRIBE, validation, phase2, audio-description, Claude]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase2_llm_typing_validation.csv
  - output/scenetwin_description_gain/phase2_llm_typing_confusion.csv
  - output/scenetwin_description_gain/phase2_typing_validation.csv
---

# SceneTwin Phase 2 LLM Typing Validation

## Question

Was the failed TRIBE/pro-AD typing validation caused by the hand-written lexicon,
or does Glasser ROI typing still fail when a stronger classifier reads the
professional AD text?

## Method

Same windows, same proportional alignment, same Glasser TRIBE dominant labels as
`phase2_typing_validation.csv`. The only changed component is the pro-AD content
classifier: `{actual_provider}` with model `{args.model if actual_provider == "anthropic" else "local-fallback"}`.

Claude saw the AD snippet, timing, and type definitions. It did not see TRIBE's
dominant type, ROI scores, agreement labels, or any metric target.

## Headline

| Metric | Value |
|---|---:|
| Windows scored | {llm_n} |
| Chance agreement | {chance:.1%} |
| Lexicon pro-AD vs TRIBE agreement | {lex_wins}/{lex_n} ({rate_fmt(lex_rate)}) |
| LLM pro-AD vs TRIBE agreement | {llm_wins}/{llm_n} ({rate_fmt(llm_rate)}) |
| LLM vs lexicon pro-AD agreement | {llm_lex_wins}/{len(merged)} ({rate_fmt(llm_lex_rate)}) |
| High-need lexicon agreement | {rate_fmt(high_lex)} |
| High-need LLM agreement | {rate_fmt(high_llm)} |

## Confusion Matrix

Rows: LLM-classified professional AD dominant type. Columns: TRIBE dominant type.

{confusion.to_markdown()}

## Per-Window Detail

{merged[detail_cols].to_markdown(index=False)}

## Verdict

{verdict}

Decision: {decision}

## Caveat

This still inherits the weakest part of the validation: VideoA11y text does not
come with per-sentence timestamps, so snippets are proportionally aligned to
TRIBE windows. A scale-up should either use timestamped AD, human window labels,
or ask the LLM to label clip-level AD priorities separately from per-window timing.
"""

    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(f"Provider: {actual_provider}")
    print(f"Lexicon agreement: {lex_wins}/{lex_n} ({rate_fmt(lex_rate)})")
    print(f"LLM agreement: {llm_wins}/{llm_n} ({rate_fmt(llm_rate)})")
    print(f"LLM vs lexicon: {llm_lex_wins}/{len(merged)} ({rate_fmt(llm_lex_rate)})")
    print(f"High-need LLM agreement: {rate_fmt(high_llm)}")
    print(f"Per-window CSV -> {OUT_PER_WINDOW}")
    print(f"Confusion CSV  -> {OUT_CONFUSION}")
    print(f"Report         -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
