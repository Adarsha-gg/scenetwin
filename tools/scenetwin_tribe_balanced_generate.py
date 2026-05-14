#!/usr/bin/env python3
"""Generate TRIBE-balanced AD candidates.

This is prompt v2 for making TRIBE native to generation. The old gap-targeted
prompt matched the dominant TRIBE content type but often became generic. This
version keeps TRIBE's dominant/second type guidance and forces concrete visual
tokens from the provided context.
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
BASELINE_JSONL = DG_DIR / "phase1_ad_candidates.jsonl"
OUT_JSONL = DG_DIR / "phase1_ad_candidates_tribe_balanced.jsonl"
OUT_PREVIEW = DG_DIR / "phase1_ad_candidates_tribe_balanced_preview.md"
ENV_PATH = ROOT / ".env"

CONTENT_TYPES = [
    "motion_action",
    "scene_spatial",
    "face_character",
    "object_body",
    "visual_form",
    "language_auditory",
]


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", str(text or ""))


def trim_words(text: str, budget: int) -> str:
    words = tokenize(text)
    return " ".join(words[:budget])


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}", text, flags=re.S)
    obj = json.loads(match.group(0) if match else text)
    ad_text = str(obj.get("ad_text", "")).strip()
    return {
        "ad_text": ad_text,
        "targeted_types": list(obj.get("targeted_types", [])),
        "word_count": int(obj.get("word_count", len(tokenize(ad_text)))),
    }


def call_anthropic(prompt: str, model: str) -> dict[str, Any]:
    from anthropic import Anthropic

    client = Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=220,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", "") == "text")
    return parse_json_response(text)


def balanced_prompt(row: dict[str, Any]) -> str:
    profile = row["profile_share"]
    second = row["second_type"]
    second_instruction = (
        f"If possible, include one word for the second gap `{second}` too."
        if second in CONTENT_TYPES and profile.get(second, 0.0) >= 0.15
        else "Do not force the second gap if the word budget is too tight."
    )
    return f"""You are writing a very short audio-description insert.

Window: {row['start_s']:.2f}-{row['end_s']:.2f}s
Recommendation: {row['recommendation']}
Word budget: {row['word_budget']}
Audio already heard: {row['audio_transcript'] or '[silent]'}
Visual context: {row.get('visual_context') or '[none]'}

TRIBE brain-model gap profile says the missing visual content is:
- dominant: {row['dominant_type']} ({profile.get(row['dominant_type'], 0.0):.0%} share)
- second: {row['second_type']} ({profile.get(row['second_type'], 0.0):.0%} share)

Write an AD insert that:
1. Hits the dominant TRIBE type: `{row['dominant_type']}`.
2. Uses at least one concrete noun or action from the visual context.
3. {second_instruction}
4. Avoids generic adjectives like important, visible, emotional, beautiful.
5. Does not repeat audio-only information unless it is visible text.
6. Stays within the word budget exactly or under.

Return JSON only:
{{
  "ad_text": "short insert",
  "targeted_types": ["{row['dominant_type']}"],
  "word_count": 0
}}
"""


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["anthropic", "local"], default="anthropic")
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    prompts = read_jsonl(PROMPTS_JSONL)
    if args.limit:
        prompts = prompts[: args.limit]

    baseline_rows = [
        r for r in read_jsonl(BASELINE_JSONL)
        if r.get("condition") == "baseline"
    ]
    baseline_key = {(r["clip_idx"], r["window_idx"]): r for r in baseline_rows}

    rows = []
    for prompt_row in prompts:
        key = (prompt_row["clip_idx"], prompt_row["window_idx"])
        if key in baseline_key:
            rows.append(baseline_key[key])

        prompt_text = balanced_prompt(prompt_row)
        if args.provider == "anthropic":
            parsed = call_anthropic(prompt_text, args.model)
            provider = "anthropic"
            model = args.model
        else:
            parsed = {
                "ad_text": trim_words(prompt_row.get("visual_context", ""), int(prompt_row["word_budget"])),
                "targeted_types": [prompt_row["dominant_type"]],
                "word_count": int(prompt_row["word_budget"]),
            }
            provider = "local"
            model = "local-context-trim"

        ad_text = trim_words(parsed.get("ad_text", ""), int(prompt_row["word_budget"]))
        out = {
            **{k: prompt_row[k] for k in [
                "clip_idx",
                "window_idx",
                "start_s",
                "end_s",
                "duration_s",
                "word_budget",
                "recommendation",
                "dominant_type",
                "second_type",
                "profile_score",
                "profile_share",
                "audio_transcript",
                "visual_context",
            ]},
            "condition": "tribe_balanced",
            "provider": provider,
            "model": model,
            "prompt": prompt_text,
            "ad_text": ad_text,
            "targeted_types": parsed.get("targeted_types", [prompt_row["dominant_type"]]),
            "word_count": len(tokenize(ad_text)),
        }
        rows.append(out)
        print(f"clip_{prompt_row['clip_idx']:02d} t{prompt_row['window_idx']:02d}: {ad_text!r}", flush=True)

    write_jsonl(OUT_JSONL, rows)
    preview = ["# TRIBE Balanced Candidate Preview", "", f"Rows: {len(rows)}", ""]
    for row in rows[:30]:
        preview.append(
            f"- clip {row['clip_idx']} t{row['window_idx']} `{row['condition']}`: {row['ad_text']}"
        )
    OUT_PREVIEW.write_text("\n".join(preview) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSONL}")
    print(f"Wrote {OUT_PREVIEW}")


if __name__ == "__main__":
    main()
