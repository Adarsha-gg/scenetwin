"""VLM-as-judge baseline runner for SceneTwin.

For each (clip, tier) pair:
  - Sample N frames from the clip video
  - Send frames + AD text to a frontier VLM with a structured rating prompt
  - Parse the VLM's score into a per-tier quality rating

Then compute Spearman rho vs tier GT and compare to our ensemble.

Supports Anthropic, OpenAI, and Google Gemini via a unified interface.
Set the provider's API key as an env var before running.

Usage:
    # Cost estimate dry run (no API calls):
    python3 cursor/research/vlm_as_judge_runner.py --dry-run

    # Smoke test on 2 clips (in-bench):
    python3 cursor/research/vlm_as_judge_runner.py \\
        --provider anthropic \\
        --model claude-sonnet-4-6 \\
        --corpus inbench \\
        --limit 2

    # Full run on combined 78-clip corpus:
    python3 cursor/research/vlm_as_judge_runner.py \\
        --provider anthropic \\
        --model claude-sonnet-4-6 \\
        --corpus combined

Env vars expected:
    ANTHROPIC_API_KEY               (for provider=anthropic)
    OPENAI_API_KEY                  (for provider=openai)
    GEMINI_API_KEY or GOOGLE_API_KEY (for provider=gemini)

A .env at repo root is auto-loaded if python-dotenv is available.
"""
from __future__ import annotations
from __future__ import annotations

import argparse
import base64
import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Auto-load .env at repo root
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "cursor" / "research" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Per-call token estimates (input)
EST_TOKENS_PER_IMAGE = 1600  # ~1024x576 JPEG-encoded
EST_TOKENS_PROMPT    = 500
EST_TOKENS_OUTPUT    = 100

# 2026 pricing (USD per million tokens). Approximate; update before final run.
PRICING = {
    "claude-opus-4-7":     {"in":  15.00, "out":  75.00},
    "claude-sonnet-4-6":   {"in":   3.00, "out":  15.00},
    "claude-haiku-4-5":    {"in":   0.80, "out":   4.00},
    "gpt-5":               {"in":   2.50, "out":  10.00},
    "gpt-4o":              {"in":   2.50, "out":  10.00},
    "gemini-2.5-pro":      {"in":   1.25, "out":   5.00},
    "gemini-2.5-flash":    {"in":   0.30, "out":   2.50},
}

FRAMES_PER_CLIP = 6
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}

SYSTEM = (
    "You are a careful evaluator of audio descriptions (AD) for blind and "
    "low-vision viewers. Given a short video clip (shown as sampled frames) "
    "and a candidate AD text, rate the AD's quality from 0 to 100. The score "
    "should reflect whether the AD accurately and completely describes the "
    "visual content a sighted viewer would understand. Do NOT reward fluency "
    "or length on their own. Reward visual fidelity, factual correctness, "
    "and informativeness about the visual content of these specific frames."
)

USER_PROMPT_TEMPLATE = (
    "Below are {n_frames} frames sampled across a short video clip.\n\n"
    "Candidate audio description (AD):\n"
    "<<AD_START>>\n{ad_text}\n<<AD_END>>\n\n"
    "Rate this AD from 0 to 100 based ONLY on how well it matches what a "
    "sighted viewer would see in these frames. Output strictly in JSON with "
    "no prose before or after:\n\n"
    '{{"visual_fidelity": <0-100>, "completeness": <0-100>, '
    '"informativeness": <0-100>, "overall": <0-100>}}'
)


def sample_frames(video_path: Path, n: int = FRAMES_PER_CLIP) -> list[bytes]:
    """Return n evenly-spaced JPEG frames as bytes."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        # Probe duration
        probe = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=nokey=1:noprint_wrappers=1", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        dur = float(probe.stdout.strip() or 10.0)
        frames = []
        for i in range(n):
            t = dur * (i + 0.5) / n
            out = tdp / f"frame_{i:02d}.jpg"
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}",
                 "-i", str(video_path), "-frames:v", "1",
                 "-vf", "scale='min(1024,iw)':-2",
                 "-q:v", "5", str(out)],
                capture_output=True, timeout=30,
            )
            if out.exists() and out.stat().st_size > 0:
                frames.append(out.read_bytes())
        return frames


def call_anthropic(model: str, frames: list[bytes], ad_text: str) -> dict:
    """Call Anthropic Messages API; return {score_dict, raw_response}."""
    import anthropic
    client = anthropic.Anthropic()
    content = []
    for f in frames:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": base64.b64encode(f).decode("ascii"),
            },
        })
    content.append({
        "type": "text",
        "text": USER_PROMPT_TEMPLATE.format(n_frames=len(frames), ad_text=ad_text),
    })
    resp = client.messages.create(
        model=model,
        system=SYSTEM,
        max_tokens=400,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    return {"text": text, "model": resp.model, "usage": dict(resp.usage) if hasattr(resp, "usage") else {}}


def call_openai(model: str, frames: list[bytes], ad_text: str) -> dict:
    import openai
    client = openai.OpenAI()
    content = []
    for f in frames:
        b64 = base64.b64encode(f).decode("ascii")
        content.append({"type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
    content.append({"type": "text",
                    "text": USER_PROMPT_TEMPLATE.format(n_frames=len(frames), ad_text=ad_text)})
    # GPT-5 / o1 series use max_completion_tokens; older 4o uses max_tokens.
    kwargs = dict(
        model=model,
        messages=[{"role": "system", "content": SYSTEM},
                  {"role": "user", "content": content}],
    )
    if model.startswith(("gpt-5", "o1", "o3")):
        # Reasoning models burn internal tokens before visible output
        kwargs["max_completion_tokens"] = 4000
    else:
        kwargs["max_tokens"] = 400
    resp = client.chat.completions.create(**kwargs)
    text = resp.choices[0].message.content or ""
    return {"text": text, "model": resp.model, "usage": dict(resp.usage)}


def call_gemini(model: str, frames: list[bytes], ad_text: str) -> dict:
    from google import genai
    from google.genai import types
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = genai.Client(api_key=key)
    parts = [types.Part.from_bytes(data=f, mime_type="image/jpeg") for f in frames]
    parts.append(types.Part.from_text(
        text=USER_PROMPT_TEMPLATE.format(n_frames=len(frames), ad_text=ad_text)))
    # Gemini 2.5 Pro is a thinking model -- burns reasoning tokens before output.
    # Allow generous budget (4000) so JSON gets emitted after thinking.
    is_thinking = "2.5" in model and "flash" not in model
    max_out = 4000 if is_thinking else 400
    resp = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM, max_output_tokens=max_out),
    )
    text = resp.text or ""
    return {"text": text, "model": model, "usage": {}}


def parse_score(text: str) -> dict | None:
    """Pull the JSON rating block out of the model's reply."""
    m = re.search(r"\{[^{}]*\}", text)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return {k: float(v) for k, v in d.items() if k in
                {"visual_fidelity", "completeness", "informativeness", "overall"}}
    except Exception:
        return None


def cost_estimate(n_calls: int, model: str) -> dict:
    if model not in PRICING:
        return {"model": model, "note": "no pricing in table"}
    p = PRICING[model]
    in_tok = EST_TOKENS_PROMPT + FRAMES_PER_CLIP * EST_TOKENS_PER_IMAGE
    out_tok = EST_TOKENS_OUTPUT
    cost = n_calls * (in_tok * p["in"] + out_tok * p["out"]) / 1_000_000
    return {
        "model": model, "n_calls": n_calls,
        "in_tokens_per_call": in_tok, "out_tokens_per_call": out_tok,
        "input_usd": round(n_calls * in_tok * p["in"] / 1_000_000, 3),
        "output_usd": round(n_calls * out_tok * p["out"] / 1_000_000, 3),
        "total_usd": round(cost, 3),
    }


def load_inbench_roster() -> list[dict]:
    fc = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv")
    rows = []
    for _, c in fc.iterrows():
        cidx = int(c["clip_idx"])
        video = None
        for ext in (".mp4", ".mkv", ".webm"):
            p = ROOT / "workspace" / "vatex_clips" / f"clip_{cidx:02d}{ext}"
            if p.exists():
                video = p; break
        if video is None: continue
        rows.append({
            "corpus": "inbench", "video_id": c["video_id"], "clip_idx": cidx,
            "category": c["category"], "video_path": str(video),
            "tier0_text": c["tier0_cross_text"], "tier1_text": c["tier1_vatex_short_text"],
            "tier2_text": c["tier2_vatex_long_text"], "tier3_text": c["tier3_va11y_text"],
        })
    return rows


def load_external_roster() -> list[dict]:
    reg_path = ROOT / "cursor" / "data" / "external_clips" / "registry.jsonl"
    rows = []
    for line in reg_path.open():
        d = json.loads(line)
        if not d.get("download_ok"): continue
        video = ROOT / "cursor" / "data" / "external_clips" / d["video_id"] / "clip.mp4"
        if not video.exists(): continue
        rows.append({
            "corpus": "external", "video_id": d["video_id"], "clip_idx": -1,
            "category": d["category"], "video_path": str(video),
            "tier0_text": d["tier0_cross"], "tier1_text": d["tier1_vatex_short"],
            "tier2_text": d["tier2_vatex_long"], "tier3_text": d["tier3_va11y"],
        })
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", choices=["anthropic", "openai", "gemini"], default="anthropic")
    ap.add_argument("--model", default="claude-sonnet-4-6")
    ap.add_argument("--corpus", choices=["inbench", "external", "combined"], default="inbench")
    ap.add_argument("--limit", type=int, default=None, help="cap n_clips (for smoke test)")
    ap.add_argument("--dry-run", action="store_true", help="print cost + sample prompt only")
    ap.add_argument("--out", default=None, help="output CSV path")
    args = ap.parse_args()

    roster = []
    if args.corpus in ("inbench", "combined"):
        roster.extend(load_inbench_roster())
    if args.corpus in ("external", "combined"):
        roster.extend(load_external_roster())
    if args.limit:
        roster = roster[: args.limit]
    n_calls = len(roster) * 4  # 4 tiers per clip
    print(f"Corpus: {args.corpus}    Clips: {len(roster)}    Tiers per clip: 4    "
          f"Total VLM calls: {n_calls}")

    est = cost_estimate(n_calls, args.model)
    print(f"\nCost estimate ({args.model}):")
    for k, v in est.items():
        print(f"  {k}: {v}")

    if args.dry_run:
        if roster:
            print("\nSample prompt (what would be sent for the first call):")
            print(f"  Video: {roster[0]['video_path']}")
            print(f"  AD (tier3): {roster[0]['tier3_text'][:200]}...")
            print(f"\nSystem prompt:\n{SYSTEM}")
            print(f"\nUser prompt template:\n{USER_PROMPT_TEMPLATE.format(n_frames=FRAMES_PER_CLIP, ad_text='<AD text here>')}")
        return

    # Live run
    out_path = Path(args.out) if args.out else OUT_DIR / f"vlm_as_judge_{args.provider}_{args.model.replace('-','_')}_{args.corpus}.csv"
    print(f"\nWriting -> {out_path}")

    # Resume support: skip (video_id, tier) pairs already in the output CSV
    completed = set()
    rows_out: list[dict] = []
    if out_path.exists():
        prev = pd.read_csv(out_path)
        keep = prev[prev["overall"].notna()] if "overall" in prev.columns else prev.iloc[0:0]
        for _, r in keep.iterrows():
            completed.add((r["video_id"], r["tier"]))
        rows_out = keep.to_dict("records")
        print(f"Resuming: {len(completed)} (clip, tier) pairs already scored, will skip.")

    tier_key = {"tier0_cross": "tier0_text", "tier1_vatex_short": "tier1_text",
                "tier2_vatex_long": "tier2_text", "tier3_va11y": "tier3_text"}
    caller = {"anthropic": call_anthropic, "openai": call_openai, "gemini": call_gemini}[args.provider]

    def call_with_retry(*a, max_tries=4):
        for attempt in range(max_tries):
            try:
                return caller(*a)
            except Exception as e:
                msg = str(e).lower()
                if attempt == max_tries - 1 or not any(k in msg for k in ("rate", "429", "overloaded", "timeout", "504", "503")):
                    raise
                wait = 2 ** attempt * 3
                print(f"     retry {attempt+1} after {wait}s ({type(e).__name__})")
                time.sleep(wait)

    t0 = time.time()
    for i, clip in enumerate(roster):
        # Skip clip if all 4 tiers already done
        if all((clip["video_id"], t) in completed for t in TIERS):
            print(f"  [{i+1}/{len(roster)}] {clip['video_id']}  already complete")
            continue
        try:
            frames = sample_frames(Path(clip["video_path"]))
            if not frames:
                print(f"  [{i+1}/{len(roster)}] {clip['video_id']}  ERR: no frames extracted")
                continue
        except Exception as e:
            print(f"  [{i+1}/{len(roster)}] {clip['video_id']}  ERR: frame sampling failed ({e})")
            continue
        for t in TIERS:
            if (clip["video_id"], t) in completed:
                continue
            ad = str(clip[tier_key[t]])
            try:
                resp = call_with_retry(args.model, frames, ad)
                score = parse_score(resp["text"])
            except Exception as e:
                print(f"     {t}: ERR {e}")
                resp = {"text": str(e)[:500]}
                score = None
            row = {
                "corpus": clip["corpus"], "video_id": clip["video_id"], "category": clip["category"],
                "tier": t, "gt": TIER_GT[t],
                "visual_fidelity": (score or {}).get("visual_fidelity"),
                "completeness":    (score or {}).get("completeness"),
                "informativeness": (score or {}).get("informativeness"),
                "overall":         (score or {}).get("overall"),
                "raw_text":        resp.get("text", "")[:500] if score is None else None,
            }
            rows_out.append(row)
            completed.add((clip["video_id"], t))
        # Incremental save every clip
        pd.DataFrame(rows_out).to_csv(out_path, index=False)
        elapsed = time.time() - t0
        n_done = i + 1
        eta = elapsed / n_done * (len(roster) - n_done)
        print(f"  [{n_done}/{len(roster)}] {clip['video_id']}  elapsed {elapsed:.0f}s  eta {eta:.0f}s")

    df = pd.DataFrame(rows_out)
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} rows -> {out_path}")
    if df["overall"].notna().sum() > 4:
        rho, p = spearmanr(df["overall"].dropna(), df.loc[df["overall"].notna(), "gt"])
        print(f"VLM-as-judge overall  rho vs tier GT: {rho:.4f}  p={p:.2e}")


if __name__ == "__main__":
    main()
