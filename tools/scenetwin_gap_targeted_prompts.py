#!/usr/bin/env python3
"""Build gap-targeted AD generation prompts from TRIBE ROI content typing.

Reads `roi_content_typing_windows.csv` and the per-clip audio TSVs, joins them
into one structured prompt per AD-need window, and writes a JSONL ready for an
LLM pass. No LLM calls happen here — that step lives in a Colab notebook
because it is paired with a TRIBE re-run on the generated AD.

Output:
  output/scenetwin_description_gain/gap_targeted_prompts.jsonl
  output/scenetwin_description_gain/gap_targeted_prompts_preview.md
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
TYPING_CSV = DG_DIR / "roi_content_typing_windows.csv"
AUDIO_DIR = DG_DIR / "audio"
TEXT_DIR = DG_DIR / "texts"
OUT_JSONL = DG_DIR / "gap_targeted_prompts.jsonl"
OUT_PREVIEW = DG_DIR / "gap_targeted_prompts_preview.md"

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]

WORDS_PER_SEC = 2.5
MIN_WORD_BUDGET = 4

EMPHASIS_GUIDE = {
    "motion_action": "describe what moves, who acts, the trajectory and result of action",
    "scene_spatial": "describe the place, layout, and spatial arrangement of objects/people",
    "face_character": "describe visible characters, expression, gaze, attention, social cues",
    "object_body": "describe the salient object or body posture and how it is being used",
    "visual_form": "describe shape, color, framing, lighting, or visual state",
    "language_auditory": "skip standard AD; only mention visible on-screen text or sound source if ambiguous",
}


def load_audio_segments(clip_idx: int) -> pd.DataFrame:
    path = AUDIO_DIR / f"clip_{clip_idx:02d}.tsv"
    if not path.exists():
        return pd.DataFrame(columns=["start", "duration", "sentence"])
    df = pd.read_csv(path, sep="\t")
    df["end"] = df["start"] + df["duration"]
    return df


def transcript_for_window(audio: pd.DataFrame, start_s: float, end_s: float) -> str:
    if audio.empty:
        return ""
    overlap = audio[(audio["end"] > start_s) & (audio["start"] < end_s)]
    if overlap.empty:
        return ""
    sentences = overlap["sentence"].dropna().astype(str).str.strip().unique().tolist()
    return " ".join(s for s in sentences if s)


def visual_context_for_clip(clip_idx: int) -> str:
    path = TEXT_DIR / f"clip_{clip_idx:02d}_tier3_va11y.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def build_prompt(row: dict, transcript: str, visual_context: str) -> dict:
    duration = max(row["end_s"] - row["start_s"], 0.1)
    word_budget = max(MIN_WORD_BUDGET, int(round(duration * WORDS_PER_SEC)))

    profile = {ct: float(row.get(f"{ct}_need", 0.0)) for ct in CONTENT_TYPES}
    total = sum(max(v, 0.0) for v in profile.values())
    profile_pct = {
        ct: (max(v, 0.0) / total if total > 0 else 0.0)
        for ct, v in profile.items()
    }

    dominant = row["dominant_type"]
    second = row["second_type"]
    recommendation = row["recommendation"]

    profile_lines = []
    for ct in CONTENT_TYPES:
        profile_lines.append(
            f"  {ct:<20} score={profile[ct]:.2f}  share={profile_pct[ct]:.0%}"
        )
    profile_block = "\n".join(profile_lines)

    if dominant == "language_auditory":
        action = (
            "This window is audio/language dominated. Do NOT generate AD unless visible "
            "on-screen text must be conveyed. If you must describe, keep it under 5 words "
            "and only describe visible text or unambiguous sound sources."
        )
    else:
        action = (
            f"Emphasize {dominant} content first ({EMPHASIS_GUIDE[dominant]}). "
            f"If words remain, cover {second} ({EMPHASIS_GUIDE.get(second, 'secondary')}). "
            f"Skip dimensions with low share."
        )

    instruction = f"""You are generating an audio description for blind/low-vision listeners.

Window: {row['start_s']:.2f}-{row['end_s']:.2f}s (duration {duration:.2f}s)
Recommendation: {recommendation}
Speech density: {row['speech_density']:.0%}
Audio context (what listener already hears): {transcript or '[silent]'}
Visual context available to you: {visual_context or '[no visual context provided]'}

A brain-encoding model (TRIBE) predicts the listener's cortical response is missing
visual signal from the soundtrack alone. The missing signal decomposes by cortical
content type as follows:

{profile_block}

Dominant gap: {dominant} (score {row['dominant_score']:.2f}).
Second gap:   {second} (score {row['second_score']:.2f}, margin {row['type_margin']:.2f}).

Instructions:
- {action}
- Do NOT restate audible content from the soundtrack.
- Select only details supported by the visual context. Do not invent new scenes, people, objects, locations, or actions.
- Word budget: {word_budget} (~{WORDS_PER_SEC} words/sec * {duration:.2f}s).
- Use concrete sensory language for the targeted dimensions; avoid generic adjectives.
- Output JSON ONLY, with keys: ad_text (string), targeted_types (list of strings from
  {CONTENT_TYPES}), word_count (int). No prose outside JSON.
"""

    return {
        "clip_idx": int(row["clip_idx"]),
        "window_idx": int(row["t"]),
        "start_s": float(row["start_s"]),
        "end_s": float(row["end_s"]),
        "duration_s": float(duration),
        "word_budget": word_budget,
        "recommendation": recommendation,
        "dominant_type": dominant,
        "second_type": second,
        "type_margin": float(row["type_margin"]),
        "need_score": float(row["need_score"]),
        "speech_density": float(row["speech_density"]),
        "profile_score": profile,
        "profile_share": profile_pct,
        "audio_transcript": transcript,
        "visual_context": visual_context,
        "prompt": instruction,
    }


def main() -> None:
    typing = pd.read_csv(TYPING_CSV)

    rows = []
    for clip_idx, group in typing.groupby("clip_idx"):
        audio = load_audio_segments(int(clip_idx))
        visual_context = visual_context_for_clip(int(clip_idx))
        for _, row in group.iterrows():
            transcript = transcript_for_window(audio, row["start_s"], row["end_s"])
            rows.append(build_prompt(row.to_dict(), transcript, visual_context))

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    preview_lines = [
        "# Gap-Targeted AD Prompts Preview",
        "",
        f"Built from `{TYPING_CSV.relative_to(ROOT)}` and audio TSVs in "
        f"`{AUDIO_DIR.relative_to(ROOT)}`. {len(rows)} prompts emitted.",
        "",
        f"Output JSONL: `{OUT_JSONL.relative_to(ROOT)}`.",
        "",
    ]
    high_need = sorted(
        [r for r in rows if r["recommendation"] != "low_ad_need"],
        key=lambda r: -r["need_score"],
    )[:3]
    for i, r in enumerate(high_need, 1):
        preview_lines.append(
            f"## Sample {i}: clip {r['clip_idx']} window {r['window_idx']} "
            f"({r['start_s']:.1f}-{r['end_s']:.1f}s, {r['recommendation']})"
        )
        preview_lines.append("")
        preview_lines.append("```")
        preview_lines.append(r["prompt"])
        preview_lines.append("```")
        preview_lines.append("")

    OUT_PREVIEW.write_text("\n".join(preview_lines))
    print(f"Wrote {len(rows)} prompts -> {OUT_JSONL}")
    print(f"Preview -> {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
