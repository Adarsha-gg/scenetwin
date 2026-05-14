#!/usr/bin/env python3
"""Phase 2 prerequisite: validate TRIBE per-window content typing against pro AD.

Splits each clip's professional VideoA11y AD into sentences, aligns them
proportionally to the TRIBE windows in `roi_content_typing_windows.csv`, and
classifies each sentence by the same lexicon TRIBE typing uses. Then asks the
question that matters before any closed-loop run:

  Does TRIBE's per-window dominant content type agree with what a professional
  AD writer chose to describe at that moment?

If agreement is meaningful, the typing is sound and Phase 2 (TRIBE-in-loop)
can run on top of it. If agreement is low, the typing is the failure point
and the loop will amplify a circular metric instead of producing better AD.

Outputs:
  output/scenetwin_description_gain/phase2_typing_validation.csv
  output/scenetwin_description_gain/phase2_typing_confusion.csv
  output/reports/scenetwin-phase2-typing-validation.md
  wiki/research/scenetwin-phase2-typing-validation.md
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
TYPING_CSV = DG_DIR / "roi_content_typing_windows.csv"
TEXT_DIR = DG_DIR / "texts"
OUT_PER_WINDOW = DG_DIR / "phase2_typing_validation.csv"
OUT_CONFUSION = DG_DIR / "phase2_typing_confusion.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-phase2-typing-validation.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-phase2-typing-validation.md"

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]

CONTENT_LEXICON = {
    "motion_action": {
        "throw", "throws", "throwing", "pin", "pins", "pinned", "holding",
        "holds", "count", "counts", "counting", "eat", "eats", "eating",
        "drink", "drinks", "drinking", "take", "takes", "cough", "coughing",
        "clap", "clapping", "laugh", "laughing", "ski", "skier", "navigates",
        "weaving", "moves", "descend", "demonstrates", "uses", "write",
        "writes", "bites", "washes", "struggle", "struggling", "throws",
        "lunges", "turns",
    },
    "scene_spatial": {
        "kitchen", "restaurant", "wall", "tray", "liner", "hill", "snowy",
        "course", "around", "place", "setting", "wooden", "behind", "near",
        "above", "below", "inside", "outside", "table", "counter", "floor",
    },
    "face_character": {
        "man", "chef", "bald", "hoodie", "people", "someone", "he", "she",
        "his", "her", "smiles", "smile", "appears", "expression", "face",
        "eyes", "gaze", "character", "boy", "girl", "woman", "guy",
    },
    "object_body": {
        "tomato", "cherry", "knife", "hamburger", "burger", "soda", "ketchup",
        "tray", "liner", "poles", "camera", "object", "hand", "arm", "head",
        "body", "fingers", "mouth",
    },
    "visual_form": {
        "red", "gray", "grey", "bustling", "flexible", "precision", "rapidly",
        "quick", "small", "large", "bright", "dark", "light", "color",
        "colored", "shape", "shaped", "round", "tall", "short", "wide",
    },
    "language_auditory": {
        "spanish", "countdown", "uno", "dos", "tres", "encouraging", "says",
        "speaking", "audio", "words", "shouting", "whisper", "music",
        "sound", "speech", "voice", "talks", "talking",
    },
}

# Words that match more than one type. Split mass evenly across types so neither
# wins by accident.
SHARED = {
    "burger": {"scene_spatial", "object_body"},
    "tray": {"scene_spatial", "object_body"},
    "liner": {"scene_spatial", "object_body"},
    "wall": {"scene_spatial", "object_body"},
    "drink": {"motion_action", "object_body"},
    "drinks": {"motion_action", "object_body"},
    "eating": {"motion_action", "language_auditory"},
    "snowy": {"scene_spatial", "visual_form"},
    "night": {"scene_spatial", "visual_form"},
    "place": {"scene_spatial", "visual_form"},
    "counts": {"motion_action", "language_auditory"},
    "counting": {"motion_action", "language_auditory"},
    "laughing": {"motion_action", "language_auditory"},
    "clapping": {"motion_action", "language_auditory"},
}


def tokenize(text: str) -> list[str]:
    return [tok.lower() for tok in re.findall(r"[A-Za-z0-9']+", text)]


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def sentence_profile(text: str) -> dict[str, float]:
    tokens = tokenize(text)
    raw = {ct: 0.0 for ct in CONTENT_TYPES}
    for tok in tokens:
        if tok in SHARED:
            shared_types = SHARED[tok]
            share = 1.0 / len(shared_types)
            for ct in shared_types:
                raw[ct] += share
            continue
        for ct, words in CONTENT_LEXICON.items():
            if tok in words:
                raw[ct] += 1.0
                break
    total = sum(raw.values())
    if total <= 1e-9:
        return raw
    return {ct: raw[ct] / total for ct in CONTENT_TYPES}


def dominant_type(profile: dict[str, float]) -> tuple[str, float]:
    if all(v == 0.0 for v in profile.values()):
        return ("unscored", 0.0)
    top = max(profile.items(), key=lambda kv: kv[1])
    return top[0], top[1]


def align_sentences_to_windows(
    sentences: list[str], windows: pd.DataFrame
) -> list[tuple[str, dict[str, float]]]:
    """Proportionally map sentences to windows by clip duration.

    Pro AD has no per-window timestamps; sentences are evenly spread across the
    clip duration. Each window gets the sentence whose midpoint falls inside it.
    Multiple sentences inside one window are merged; an empty window inherits
    the nearest sentence by midpoint.
    """
    if not sentences or windows.empty:
        return [("", {ct: 0.0 for ct in CONTENT_TYPES}) for _ in range(len(windows))]
    total_duration = float(windows["end_s"].max() - windows["start_s"].min())
    n = len(sentences)
    sentence_spans = []
    for i, s in enumerate(sentences):
        sentence_spans.append((
            i / n * total_duration,
            (i + 1) / n * total_duration,
            s,
        ))

    out = []
    for _, w in windows.iterrows():
        ws, we = float(w["start_s"]), float(w["end_s"])
        overlapping = []
        for ss, se, txt in sentence_spans:
            if se > ws and ss < we:
                overlap = min(se, we) - max(ss, ws)
                overlapping.append((overlap, txt))
        if overlapping:
            overlapping.sort(reverse=True)
            text = " ".join(t for _, t in overlapping)
        else:
            mid = 0.5 * (ws + we)
            best = min(sentence_spans, key=lambda s: abs(0.5 * (s[0] + s[1]) - mid))
            text = best[2]
        out.append((text, sentence_profile(text)))
    return out


def main() -> None:
    typing = pd.read_csv(TYPING_CSV)
    rows = []

    for clip_idx, group in typing.groupby("clip_idx"):
        ad_path = TEXT_DIR / f"clip_{int(clip_idx):02d}_tier3_va11y.txt"
        if not ad_path.exists():
            continue
        ad_text = ad_path.read_text(encoding="utf-8").strip()
        sentences = split_sentences(ad_text)
        windows = group.sort_values("t").reset_index(drop=True)
        aligned = align_sentences_to_windows(sentences, windows)

        for (sentence_text, pro_profile), (_, win) in zip(aligned, windows.iterrows()):
            pro_dom, pro_score = dominant_type(pro_profile)
            tribe_dom = win["dominant_type"]
            agree = (pro_dom == tribe_dom) if pro_dom != "unscored" else None
            rows.append({
                "clip_idx": int(win["clip_idx"]),
                "window_idx": int(win["t"]),
                "start_s": float(win["start_s"]),
                "end_s": float(win["end_s"]),
                "need_score": float(win["need_score"]),
                "speech_density": float(win["speech_density"]),
                "recommendation": win["recommendation"],
                "tribe_dominant": tribe_dom,
                "tribe_dominant_score": float(win["dominant_score"]),
                "tribe_type_margin": float(win["type_margin"]),
                "pro_ad_text": sentence_text,
                "pro_ad_dominant": pro_dom,
                "pro_ad_dominant_share": float(pro_score),
                **{f"pro_ad_{ct}": float(pro_profile[ct]) for ct in CONTENT_TYPES},
                "agree": agree,
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUT_PER_WINDOW, index=False)

    scored = df[df["pro_ad_dominant"] != "unscored"].copy()
    n_scored = len(scored)
    n_agree = int(scored["agree"].sum())
    agreement_rate = n_agree / n_scored if n_scored else float("nan")

    high_need = scored[scored["recommendation"].isin([
        "standard_ad_slot", "extended_or_integrated_ad", "inspect_visual_event"
    ])]
    high_need_rate = (
        high_need["agree"].sum() / len(high_need) if len(high_need) else float("nan")
    )

    confusion = pd.crosstab(
        scored["pro_ad_dominant"],
        scored["tribe_dominant"],
        rownames=["pro_ad_dominant"],
        colnames=["tribe_dominant"],
        dropna=False,
    )
    confusion.to_csv(OUT_CONFUSION)

    chance = 1.0 / len(CONTENT_TYPES)

    report = [
        "---",
        'title: "SceneTwin Phase 2 Typing Validation"',
        "category: research",
        "tags: [SceneTwin, TRIBE, validation, phase2, audio-description]",
        "created: 2026-05-03",
        "updated: 2026-05-03",
        "sources:",
        "  - output/scenetwin_description_gain/phase2_typing_validation.csv",
        "  - output/scenetwin_description_gain/phase2_typing_confusion.csv",
        "  - output/scenetwin_description_gain/roi_content_typing_windows.csv",
        "  - output/scenetwin_description_gain/texts/",
        "---",
        "",
        "# SceneTwin Phase 2 Typing Validation",
        "",
        "## Question",
        "",
        "Before running TRIBE in a closed loop with an LLM, does TRIBE's per-window",
        "dominant content type agree with the content type a professional AD writer",
        "chose to describe at that moment? If not, the loop optimizes a metric",
        "decoupled from real AD usefulness.",
        "",
        "## Method",
        "",
        "1. Split each clip's VideoA11y professional AD into sentences.",
        "2. Proportionally time-align sentences to windows by clip duration.",
        "3. Classify each window's pro-AD content via the same content lexicon used",
        "   for TRIBE typing (with shared-vocabulary words split evenly).",
        "4. Compare per-window dominant type from pro AD against TRIBE's dominant",
        "   type. Report agreement rate and confusion matrix.",
        "",
        "## Headline",
        "",
        f"- Windows scored: {n_scored} of {len(df)}",
        f"- Pro AD vs TRIBE dominant-type agreement: **{agreement_rate:.1%}**",
        f"- Chance agreement (uniform over {len(CONTENT_TYPES)} types): {chance:.1%}",
        f"- High-need windows (standard/extended AD slots) agreement: **{high_need_rate:.1%}** on {len(high_need)} windows",
        "",
        "## Confusion Matrix",
        "",
        "Rows: pro AD dominant content type. Columns: TRIBE dominant content type.",
        "",
        confusion.to_markdown(),
        "",
        "## Per-Window Detail",
        "",
        scored[[
            "clip_idx",
            "window_idx",
            "start_s",
            "end_s",
            "recommendation",
            "tribe_dominant",
            "pro_ad_dominant",
            "agree",
            "pro_ad_text",
        ]].to_markdown(index=False),
        "",
        "## Verdict",
        "",
    ]

    if np.isnan(agreement_rate):
        report.append(
            "Insufficient pro AD signal to score. Need more windows or richer pro AD."
        )
    elif agreement_rate >= 0.5:
        report.append(
            f"Agreement {agreement_rate:.1%} clears chance ({chance:.1%}) and is high "
            "enough that TRIBE typing is roughly tracking pro-AD intent. Phase 2 "
            "(TRIBE-in-loop) is justified, but each disagreement should be inspected "
            "before scaling."
        )
    elif agreement_rate >= 1.5 * chance:
        report.append(
            f"Agreement {agreement_rate:.1%} beats chance ({chance:.1%}) but is too "
            "low to support a closed loop. The typing is partially right and partially "
            "wrong. Replace Destrieux proxies with a functional atlas (Glasser/Wang) "
            "before running Phase 2, and inspect the confusion matrix for systematic "
            "biases (e.g. visual_form winning when pros chose motion_action)."
        )
    else:
        report.append(
            f"Agreement {agreement_rate:.1%} is at or below chance ({chance:.1%}). "
            "The current TRIBE typing does NOT track what professional AD writers "
            "choose to describe. Phase 2 with TRIBE in the loop will amplify a "
            "circular metric. Do not run it. Either switch to a functional atlas "
            "or anchor the loop against pro AD / ADQA / human ratings instead of "
            "TRIBE residual gap."
        )

    report.append("")
    report.append("## Caveats")
    report.append("")
    report.append("- Sentence-to-window alignment is proportional, not timestamped. Pro AD")
    report.append("  does not come with per-sentence timing. Off-by-one window slips are")
    report.append("  expected; clip-level agreement is more robust than per-window.")
    report.append("- The lexicon is small. Words missing from it (e.g. specific food items,")
    report.append("  body parts) score as zero. This biases agreement downward.")
    report.append("- Pro AD for these clips is short (3-5 sentences) covering the whole clip.")
    report.append("  A real test needs longer pro AD or human per-window judgments.")

    report_text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(report_text)
    OUT_WIKI.write_text(report_text)

    print(f"Windows scored: {n_scored}/{len(df)}")
    print(f"Agreement: {agreement_rate:.1%}  (chance {chance:.1%})")
    print(f"High-need agreement: {high_need_rate:.1%}")
    print(f"Per-window CSV -> {OUT_PER_WINDOW}")
    print(f"Confusion CSV  -> {OUT_CONFUSION}")
    print(f"Report         -> {OUT_REPORT}")


if __name__ == "__main__":
    main()
