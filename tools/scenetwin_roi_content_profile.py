#!/usr/bin/env python3
"""TRIBE ROI content typing for SceneTwin AD slots.

This is the layer that makes TRIBE a differentiator instead of a text scorer.
It converts ROI-restricted accessibility gaps into content-type profiles:
scene / motion / face-character / object-body / language-auditory.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
ROI_CSV = DG_DIR / "roi_gap_curve.csv"
NEED_CSV = DG_DIR / "neural_description_need_curve.csv"
EVENT_CSV = DG_DIR / "neural_event_test_results.csv"
TEXT_DIR = DG_DIR / "texts"
OUT_WINDOW_CSV = DG_DIR / "roi_content_typing_windows.csv"
OUT_DESC_CSV = DG_DIR / "roi_content_typing_descriptions.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-roi-content-typing.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-roi-content-typing.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
GT = {"tier3_va11y": 3, "tier2_vatex_long": 2, "tier1_vatex_short": 1, "tier0_cross": 0}

ROI_TO_CONTENT = {
    # Destrieux anatomical proxies
    "scene_context_ppa_proxy": "scene_spatial",
    "retrosplenial_precuneus_proxy": "scene_spatial",
    "early_visual_v1_proxy": "visual_form",
    "occipital_visual_proxy": "visual_form",
    "lateral_object_loc_proxy": "object_body",
    "body_eba_proxy": "object_body",
    "ventral_visual_ffa_proxy": "face_character",
    "motion_mt_proxy": "motion_action",
    "language_control": "language_auditory",
    "auditory_control": "language_auditory",
    # Glasser HCP-MMP1.0 functional groups (added 2026-05-03)
    "scene_ppa": "scene_spatial",
    "retrosplenial_pos": "scene_spatial",
    "early_visual_v1": "visual_form",
    "higher_visual_v2v3v4": "visual_form",
    "lateral_object_loc": "object_body",
    "body_eba_region": "object_body",
    "face_ffc": "face_character",
    "motion_mt_complex": "motion_action",
    # `language_control` and `auditory_control` keys are shared with Destrieux above.
    "_unassigned_padding": None,
}

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]

PRESCRIPTIVE_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
]

CONTENT_LEXICON = {
    "motion_action": {
        "throw",
        "throws",
        "throwing",
        "pin",
        "pins",
        "pinned",
        "holding",
        "holds",
        "count",
        "counts",
        "counting",
        "eat",
        "eats",
        "eating",
        "drink",
        "drinks",
        "drinking",
        "take",
        "takes",
        "cough",
        "coughing",
        "clap",
        "clapping",
        "laugh",
        "laughing",
        "ski",
        "skier",
        "navigates",
        "weaving",
        "moves",
        "descend",
        "demonstrates",
        "uses",
        "write",
        "writes",
    },
    "scene_spatial": {
        "kitchen",
        "restaurant",
        "burger",
        "king",
        "wall",
        "tray",
        "liner",
        "hill",
        "snowy",
        "course",
        "night",
        "around",
        "place",
        "setting",
        "wooden",
    },
    "face_character": {
        "man",
        "chef",
        "bald",
        "hoodie",
        "people",
        "someone",
        "he",
        "she",
        "his",
        "her",
        "smiles",
        "appears",
        "struggle",
    },
    "object_body": {
        "tomato",
        "cherry",
        "knife",
        "hamburger",
        "burger",
        "soda",
        "drink",
        "ketchup",
        "tray",
        "liner",
        "poles",
        "wall",
        "camera",
    },
    "visual_form": {
        "red",
        "gray",
        "grey",
        "bustling",
        "snowy",
        "flexible",
        "precision",
        "place",
        "night",
        "rapidly",
        "quick",
    },
    "language_auditory": {
        "spanish",
        "countdown",
        "counts",
        "counting",
        "uno",
        "dos",
        "tres",
        "laughing",
        "clapping",
        "encouraging",
        "says",
        "speaking",
        "audio",
        "words",
        "burger",
        "eating",
    },
}

TYPE_TEMPLATES = {
    "motion_action": "Describe the action first: who moves, what changes, and the result.",
    "scene_spatial": "Describe the place/layout first: where this is and how objects/people are arranged.",
    "face_character": "Describe visible people/characters first: identity cues, expression, attention, interaction.",
    "object_body": "Describe the important object/body details first: what object matters and how it is being used.",
    "visual_form": "Describe salient visual form first: shape, color, framing, or visual state.",
    "language_auditory": "Check speech/on-screen text/audio context; avoid redundant AD unless visible text must be read.",
}

ADJECTIVES = {
    "bustling",
    "wooden",
    "red",
    "gray",
    "grey",
    "bald",
    "rapidly",
    "quick",
    "flexible",
    "snowy",
    "night",
}


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in re.findall(r"[A-Za-z0-9']+", text)]


def lexical_profile(text: str) -> dict[str, float]:
    tokens = tokenize(text)
    token_set = set(tokens)
    raw = {}
    for content_type, words in CONTENT_LEXICON.items():
        hits = sum(1 for token in tokens if token in words)
        unique_hits = len(token_set & words)
        raw[content_type] = hits + 0.5 * unique_hits
    total = sum(raw.values())
    if total <= 1e-9:
        return {k: 0.0 for k in CONTENT_TYPES}
    return {k: raw.get(k, 0.0) / total for k in CONTENT_TYPES}


def lexical_counts(text: str) -> dict[str, float]:
    tokens = tokenize(text)
    token_set = set(tokens)
    counts = {}
    for content_type, words in CONTENT_LEXICON.items():
        counts[content_type] = float(sum(1 for token in tokens if token in words) + 0.5 * len(token_set & words))
    counts["word_count"] = float(len(tokens))
    counts["unique_keywords"] = float(len(set().union(*CONTENT_LEXICON.values()) & token_set))
    counts["adjective_count"] = float(len(token_set & ADJECTIVES))
    return counts


def cosine_dict(a: dict[str, float], b: dict[str, float]) -> float:
    va = np.array([a.get(k, 0.0) for k in CONTENT_TYPES], dtype=float)
    vb = np.array([b.get(k, 0.0) for k in CONTENT_TYPES], dtype=float)
    denom = np.linalg.norm(va) * np.linalg.norm(vb)
    if denom <= 1e-9:
        return float("nan")
    return float(np.dot(va, vb) / denom)


def entropy(profile: dict[str, float]) -> float:
    vals = np.array([v for v in profile.values() if v > 1e-12], dtype=float)
    if len(vals) == 0:
        return 0.0
    return float(-(vals * np.log2(vals)).sum())


def dominant(profile: dict[str, float]) -> tuple[str, float, str, float]:
    ordered = sorted(profile.items(), key=lambda item: item[1], reverse=True)
    first = ordered[0]
    second = ordered[1] if len(ordered) > 1 else ("none", 0.0)
    return first[0], float(first[1]), second[0], float(second[1])


def main() -> None:
    roi = pd.read_csv(ROI_CSV)
    need = pd.read_csv(NEED_CSV)
    events = pd.read_csv(EVENT_CSV)
    roi["content_type"] = roi["roi"].map(ROI_TO_CONTENT)
    roi = roi[roi["content_type"].notna()].copy()

    profiles = []
    for (clip_idx, t), group in roi.groupby(["clip_idx", "t"]):
        type_scores = group.groupby("content_type")["roi_need_score"].mean().to_dict()
        control_score = type_scores.get("language_auditory", 0.0)
        need_row = need[(need["clip_idx"] == clip_idx) & (need["t"] == t)]
        speech_density = float(need_row["speech_density"].iloc[0]) if len(need_row) else 0.0
        visual_scores = {
            k: max(type_scores.get(k, 0.0) - 0.35 * control_score, 0.0)
            for k in PRESCRIPTIVE_TYPES
        }
        if speech_density < 0.25:
            visual_scores["motion_action"] *= 1.2
            visual_scores["object_body"] *= 1.1
            visual_scores["scene_spatial"] *= 0.9
        elif speech_density > 0.55:
            visual_scores["scene_spatial"] *= 1.2
            visual_scores["face_character"] *= 1.1
            visual_scores["motion_action"] *= 0.9
        visual_total = sum(visual_scores.values())
        profile = {
            k: (visual_scores.get(k, 0.0) / visual_total if visual_total > 1e-9 else 0.0)
            for k in PRESCRIPTIVE_TYPES
        }
        profile["language_auditory"] = control_score / max(sum(type_scores.values()), 1e-9)
        dom, dom_score, second, second_score = dominant(profile)
        profiles.append(
            {
                "clip_idx": int(clip_idx),
                "t": int(t),
                "control_need_raw": control_score,
                **{f"{k}_need": profile[k] for k in CONTENT_TYPES},
                "dominant_type": dom,
                "dominant_score": dom_score,
                "second_type": second,
                "second_score": second_score,
                "type_margin": dom_score - second_score,
                "type_entropy": entropy(profile),
                "ad_template": TYPE_TEMPLATES[dom],
            }
        )

    windows = pd.DataFrame(profiles)
    windows = windows.merge(
        need[
            [
                "clip_idx",
                "t",
                "start_s",
                "end_s",
                "need_score",
                "speech_density",
                "recommendation",
                "standard_slot_score",
                "extended_need_score",
            ]
        ],
        on=["clip_idx", "t"],
        how="left",
    )
    windows = windows.merge(
        events[["clip_idx", "t", "visual_event_score", "visual_event_need"]],
        on=["clip_idx", "t"],
        how="left",
    )
    windows["critical_weight"] = np.maximum(windows["need_score"], windows["visual_event_score"].fillna(0.0))
    windows = windows.sort_values(["clip_idx", "t"])

    desc_rows = []
    for clip_idx in sorted(windows["clip_idx"].unique()):
        clip_windows = windows[windows["clip_idx"] == clip_idx].copy()
        weight = clip_windows["critical_weight"].to_numpy(dtype=float)
        if weight.sum() <= 1e-9:
            weight = np.ones(len(clip_windows), dtype=float)
        target_profile = {
            k: float(np.dot(clip_windows[f"{k}_need"].to_numpy(dtype=float), weight) / weight.sum())
            for k in CONTENT_TYPES
        }
        dom_type, dom_score, second_type, second_score = dominant(target_profile)
        for tier in TIER_KEYS:
            text_path = TEXT_DIR / f"clip_{int(clip_idx):02d}_{tier}.txt"
            text = text_path.read_text(encoding="utf-8")
            profile = lexical_profile(text)
            counts = lexical_counts(text)
            text_dom, text_dom_score, _, _ = dominant(profile)
            desc_rows.append(
                {
                    "clip_idx": int(clip_idx),
                    "tier": tier,
                    "gt": GT[tier],
                    "target_dominant_type": dom_type,
                    "target_dominant_score": dom_score,
                    "target_second_type": second_type,
                    "target_second_score": second_score,
                    "text_dominant_type": text_dom,
                    "text_dominant_score": text_dom_score,
                    "profile_alignment": cosine_dict(target_profile, profile),
                    "weighted_keyword_coverage": sum(
                        target_profile[k] * counts.get(k, 0.0) for k in CONTENT_TYPES
                    ),
                    "unique_keywords": counts["unique_keywords"],
                    "word_count": counts["word_count"],
                    "specificity_score": counts["unique_keywords"] / max(counts["word_count"], 1.0),
                    **{f"target_{k}": target_profile[k] for k in CONTENT_TYPES},
                    **{f"text_{k}": profile[k] for k in CONTENT_TYPES},
                    **{f"text_{k}_count": counts[k] for k in CONTENT_TYPES},
                    "description": text,
                }
            )

    desc = pd.DataFrame(desc_rows)
    OUT_WINDOW_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    windows.to_csv(OUT_WINDOW_CSV, index=False)
    desc.to_csv(OUT_DESC_CSV, index=False)

    top_windows = windows.sort_values(["clip_idx", "critical_weight"], ascending=[True, False]).groupby("clip_idx").head(5)
    desc_summary = desc[
        [
            "clip_idx",
            "tier",
            "gt",
            "target_dominant_type",
            "text_dominant_type",
            "profile_alignment",
            "weighted_keyword_coverage",
            "specificity_score",
            "text_motion_action",
            "text_scene_spatial",
            "text_face_character",
            "text_object_body",
            "text_language_auditory",
        ]
    ]
    tier_means = desc.groupby("tier")[["profile_alignment", "weighted_keyword_coverage", "specificity_score"]].mean().loc[TIER_KEYS]

    report = f"""---
title: "SceneTwin ROI Content Typing"
category: research
tags: [SceneTwin, TRIBE, ROI, content-typing, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_content_typing_windows.csv
  - output/scenetwin_description_gain/roi_content_typing_descriptions.csv
  - output/scenetwin_description_gain/roi_gap_curve.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
---

# SceneTwin ROI Content Typing

## Claim

This is the TRIBE-specific layer: convert audio-vs-audiovisual cortical gaps into an AD content-type profile. CLIP/OCR can check whether text matches frames; TRIBE can suggest what kind of information is missing.

## Content Types

```text
motion_action
scene_spatial
face_character
object_body
visual_form
language_auditory
```

These are currently based on Destrieux anatomical proxy ROIs, not functional localizer ROIs.

## Top Typed Windows

{top_windows[["clip_idx", "t", "start_s", "end_s", "critical_weight", "need_score", "speech_density", "dominant_type", "dominant_score", "second_type", "second_score", "type_margin", "recommendation", "ad_template"]].to_markdown(index=False)}

## Description Alignment

{desc_summary.to_markdown(index=False)}

## Mean Alignment By Tier

{tier_means.to_markdown()}

## Verdict

This is the right framing for TRIBE, but the current proxy ROI/lexicon version is a prototype.

What works:

- Produces typed AD windows from TRIBE ROI gaps.
- Gives a prescriptive output: action AD vs scene/layout AD vs character/object AD.
- Keeps TRIBE out of direct text correctness scoring.

What is still weak:

- Destrieux ROIs are coarse anatomical proxies.
- The text-side validation is a lightweight lexicon check, not a real semantic parser.
- On 2 clips, content typing is plausible but not yet enough for a statistical claim.

Next version should replace Destrieux proxies with functional ROI masks and replace the lexicon with a VLM/LLM content classifier over AD text.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(top_windows[["clip_idx", "t", "start_s", "end_s", "dominant_type", "dominant_score", "second_type", "type_margin"]])
    print()
    print(desc_summary)
    print(f"Wrote {OUT_WINDOW_CSV}")
    print(f"Wrote {OUT_DESC_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
