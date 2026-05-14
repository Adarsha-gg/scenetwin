#!/usr/bin/env python3
"""Phase 1 AD generation wrapper for SceneTwin.

Reads gap-targeted prompts and emits paired candidates:

- baseline: same timing/audio context, no TRIBE ROI profile
- gap_targeted: TRIBE ROI profile + dominant/second content-type instructions

If `ANTHROPIC_API_KEY` is available and `--provider anthropic`/`auto` is used,
the script calls Anthropic. Otherwise it runs a deterministic local-template
fallback so the A/B scoring pipeline can be exercised without an API key.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
PROMPTS_JSONL = DG_DIR / "gap_targeted_prompts.jsonl"
TEXT_DIR = DG_DIR / "texts"
OUT_JSONL = DG_DIR / "phase1_ad_candidates.jsonl"
OUT_PREVIEW = DG_DIR / "phase1_ad_candidates_preview.md"
ENV_PATH = ROOT / ".env"

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]

TYPE_KEYWORDS = {
    "motion_action": [
        "throws",
        "pins",
        "eats",
        "drinks",
        "coughs",
        "writes",
        "moves",
        "weaves",
        "descends",
    ],
    "scene_spatial": ["kitchen", "restaurant", "Burger King", "wall", "tray", "snowy hill", "course"],
    "face_character": ["chef", "man", "bald man", "people", "someone", "smiles", "struggles"],
    "object_body": ["tomato", "knife", "hamburger", "drink", "ketchup", "tray liner", "poles"],
    "visual_form": ["gray hoodie", "red tomato", "snowy", "night", "quick", "bustling"],
    "language_auditory": ["BURGER EATING", "countdown", "Spanish", "clapping", "laughing"],
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text)


def trim_words(text: str, budget: int) -> str:
    words = tokenize(text)
    if len(words) <= budget:
        return " ".join(words)
    return " ".join(words[:budget])


def clip_reference_text(clip_idx: int) -> str:
    path = TEXT_DIR / f"clip_{clip_idx:02d}_tier3_va11y.txt"
    return path.read_text(encoding="utf-8")


def select_targeted_words(prompt: dict[str, Any], reference: str) -> str:
    budget = int(prompt["word_budget"])
    dominant = prompt["dominant_type"]
    second = prompt["second_type"]
    if dominant == "language_auditory":
        # Keep this behavior explicit: when the neural profile says language/audio,
        # only read visible text if the reference contains it.
        if "BURGER EATING" in reference.upper():
            return trim_words("BURGER EATING appears", min(budget, 4))
        return ""

    reference_lower = reference.lower()
    selected: list[str] = []
    for content_type in [dominant, second]:
        for kw in TYPE_KEYWORDS.get(content_type, []):
            if kw.lower() in reference_lower and kw not in selected:
                selected.extend(kw.split())
            if len(selected) >= budget:
                break
        if len(selected) >= budget:
            break

    if not selected:
        selected = tokenize(reference)[:budget]
    return " ".join(selected[:budget])


def local_template_candidate(prompt: dict[str, Any], condition: str) -> dict[str, Any]:
    reference = clip_reference_text(int(prompt["clip_idx"]))
    budget = int(prompt["word_budget"])
    if condition == "baseline":
        # A generic baseline: concise AD from the same visual source, without using
        # the ROI profile to choose content dimensions.
        ad_text = trim_words(reference, budget)
        targeted_types: list[str] = []
    else:
        ad_text = select_targeted_words(prompt, reference)
        targeted_types = [prompt["dominant_type"]]
        if prompt["second_type"] in CONTENT_TYPES and prompt["second_type"] != prompt["dominant_type"]:
            targeted_types.append(prompt["second_type"])

    return {
        "ad_text": ad_text,
        "targeted_types": targeted_types,
        "word_count": len(tokenize(ad_text)),
    }


def baseline_prompt(prompt: dict[str, Any]) -> str:
    return f"""You are generating an audio description for blind/low-vision listeners.

Window: {prompt['start_s']:.2f}-{prompt['end_s']:.2f}s (duration {prompt['duration_s']:.2f}s)
Recommendation: {prompt['recommendation']}
Speech density: {prompt['speech_density']:.0%}
Audio context (what listener already hears): {prompt['audio_transcript'] or '[silent]'}
Visual context available to you: {prompt.get('visual_context') or '[no visual context provided]'}

Instructions:
- Describe the important visual information in this window for a blind/low-vision listener.
- Do NOT restate audible content from the soundtrack.
- Select only details supported by the visual context. Do not invent new scenes, people, objects, locations, or actions.
- Word budget: {prompt['word_budget']}.
- Use concrete, concise language.
- Output JSON ONLY, with keys: ad_text (string), targeted_types (list of strings), word_count (int).
"""


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise
        obj = json.loads(match.group(0))
    return {
        "ad_text": str(obj.get("ad_text", "")).strip(),
        "targeted_types": list(obj.get("targeted_types", [])),
        "word_count": int(obj.get("word_count", len(tokenize(str(obj.get("ad_text", "")))))),
    }


def call_anthropic(prompt_text: str, model: str) -> dict[str, Any]:
    from anthropic import Anthropic

    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=180,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt_text}],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return parse_json_response(text)


def generate(provider: str, model: str, limit: int | None) -> list[dict[str, Any]]:
    prompts = read_jsonl(PROMPTS_JSONL)
    if limit is not None:
        prompts = prompts[:limit]

    use_anthropic = provider == "anthropic" or (
        provider == "auto" and bool(os.environ.get("ANTHROPIC_API_KEY"))
    )
    actual_provider = "anthropic" if use_anthropic else "local_template"

    rows = []
    for prompt in prompts:
        for condition in ["baseline", "gap_targeted"]:
            prompt_text = baseline_prompt(prompt) if condition == "baseline" else prompt["prompt"]
            if actual_provider == "anthropic":
                candidate = call_anthropic(prompt_text, model)
            else:
                candidate = local_template_candidate(prompt, condition)
            candidate["ad_text"] = trim_words(candidate.get("ad_text", ""), int(prompt["word_budget"]))
            candidate["word_count"] = len(tokenize(candidate["ad_text"]))
            rows.append(
                {
                    "clip_idx": prompt["clip_idx"],
                    "window_idx": prompt["window_idx"],
                    "start_s": prompt["start_s"],
                    "end_s": prompt["end_s"],
                    "duration_s": prompt["duration_s"],
                    "word_budget": prompt["word_budget"],
                    "recommendation": prompt["recommendation"],
                    "dominant_type": prompt["dominant_type"],
                    "second_type": prompt["second_type"],
                    "condition": condition,
                    "provider": actual_provider,
                    "model": model if actual_provider == "anthropic" else "local-template-v0",
                    "prompt": prompt_text,
                    "ad_text": candidate["ad_text"],
                    "targeted_types": candidate["targeted_types"],
                    "word_count": candidate["word_count"],
                    "profile_score": prompt["profile_score"],
                    "profile_share": prompt["profile_share"],
                    "audio_transcript": prompt["audio_transcript"],
                    "visual_context": prompt.get("visual_context", ""),
                }
            )
            print(
                f"clip_{prompt['clip_idx']:02d} t{prompt['window_idx']:02d} "
                f"{condition}: {candidate['ad_text']!r}"
            )
    return rows


def write_preview(rows: list[dict[str, Any]]) -> None:
    lines = [
        "# SceneTwin Phase 1 AD Candidate Preview",
        "",
        f"Rows: {len(rows)}",
        "",
    ]
    for row in rows[:12]:
        lines.append(
            f"- clip {row['clip_idx']} t{row['window_idx']} `{row['condition']}` "
            f"({row['provider']}): {row['ad_text']}"
        )
    OUT_PREVIEW.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["auto", "anthropic", "local-template"], default="auto")
    parser.add_argument("--model", default="claude-3-5-haiku-latest")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", type=Path, default=OUT_JSONL)
    args = parser.parse_args()

    provider = "local-template" if args.provider == "local-template" else args.provider
    rows = generate(provider, args.model, args.limit)
    write_jsonl(args.out, rows)
    write_preview(rows)
    print(f"Wrote {len(rows)} candidates -> {args.out}")
    print(f"Preview -> {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
