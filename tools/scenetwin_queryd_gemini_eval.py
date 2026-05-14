"""Evaluate SceneTwin scoring on real human AD transcript windows from QuerYD.

This uses QuerYD v2 captions/timestamps downloaded into data/queryd:
  raw_captions_combined_filtered-v2.pkl
  times_captions_combined_filtered-v2.pkl
  relevant-video-links-v2.txt

The candidate tiers are deliberately transcript-derived:
  tier0_cross: full human AD from a different clip
  tier1_min: first AD utterance only
  tier2_partial: first half of the AD utterances
  tier3_full: full human AD window
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, "demo")
import live_pipeline as lp  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "queryd"
OUT = ROOT / "output"
CACHE = ROOT / "demo" / "live_cache" / "queryd_segments"
TIER_ORDER = ["tier0_cross", "tier1_min", "tier2_partial", "tier3_full"]
GT = {"tier0_cross": 0, "tier1_min": 1, "tier2_partial": 2, "tier3_full": 3}


def read_queryd() -> tuple[dict[str, list[list[str]]], dict[str, list[list[float]]], dict[str, str]]:
    caps = pickle.load(open(DATA / "raw_captions_combined_filtered-v2.pkl", "rb"))
    times = pickle.load(open(DATA / "times_captions_combined_filtered-v2.pkl", "rb"))
    links: dict[str, str] = {}
    for line in (DATA / "relevant-video-links-v2.txt").read_text().splitlines():
        m = re.search(r"v=([^&]+)", line)
        if m:
            links[f"video-{m.group(1)}"] = line.strip()
    return caps, times, links


def words(parts: list[str]) -> str:
    text = " ".join(parts)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def pick_windows(
    caps: dict[str, list[list[str]]],
    times: dict[str, list[list[float]]],
    links: dict[str, str],
    limit: int,
) -> list[dict[str, Any]]:
    """Pick compact windows with several human AD utterances."""
    candidates: list[dict[str, Any]] = []
    for vid, utts in caps.items():
        if vid not in times or vid not in links or len(utts) < 3:
            continue
        rows = []
        for utt, tm in zip(utts, times[vid]):
            if not tm or len(tm) < 2:
                continue
            start, end = float(tm[0]), float(tm[1])
            if start < 0:
                continue
            if end < start:
                end = start
            text = words(utt)
            if len(text.split()) >= 4:
                rows.append((start, end, text))
        rows.sort()
        if len(rows) < 3:
            continue

        best = None
        for i in range(len(rows)):
            group = []
            start = rows[i][0]
            for row in rows[i:]:
                if row[0] - start > 12.0:
                    break
                group.append(row)
            if len(group) < 3:
                continue
            full = " ".join(r[2] for r in group)
            wc = len(full.split())
            if wc < 22:
                continue
            span = max(r[1] for r in group) - start
            score = (len(group), min(wc, 90), -span)
            if best is None or score > best[0]:
                best = (score, group)
        if not best:
            continue
        group = best[1]
        full = " ".join(r[2] for r in group)
        candidates.append({
            "video_key": vid,
            "yt_id": vid.replace("video-", ""),
            "url": links[vid],
            "start": max(0.0, min(r[0] for r in group) - 1.0),
            "duration": min(16.0, max(8.0, max(r[1] for r in group) - min(r[0] for r in group) + 2.0)),
            "utterances": [r[2] for r in group],
            "full_ad": full,
            "word_count": len(full.split()),
        })

    # Prefer dense, not enormous windows; spread across source videos by natural order.
    candidates.sort(key=lambda x: (-len(x["utterances"]), -min(x["word_count"], 100)))
    return candidates[:limit]


def download_segment(url: str, start: float, duration: float, key: str) -> str | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    slug = hashlib.sha1(f"{url}:{start}:{duration}".encode()).hexdigest()[:12]
    work = CACHE / slug
    work.mkdir(parents=True, exist_ok=True)
    out = work / "clip.mp4"
    if out.exists() and out.stat().st_size > 1024:
        return str(out)
    try:
        import yt_dlp
    except Exception as exc:
        print(f"yt_dlp missing: {exc}", flush=True)
        return None
    raw_tmpl = work / "raw.%(ext)s"
    home = Path.home()
    browser_choices: list[tuple[str, ...]] = []
    if (home / "Library/Application Support/BraveSoftware/Brave-Browser").exists():
        browser_choices.append(("brave",))
    if (home / "Library/Application Support/Google/Chrome").exists():
        browser_choices.append(("chrome",))
    if (home / "Library/Application Support/Firefox/Profiles").exists():
        browser_choices.append(("firefox",))
    base_opts = {
        "format": "mp4[height<=480]/best[height<=480]/best",
        "outtmpl": str(raw_tmpl),
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
        "retries": 2,
        "fragment_retries": 2,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    }
    attempts = [
        {**base_opts, "extractor_args": {"youtube": {"player_client": ["tv_embedded", "ios", "mweb"]}}},
        {**base_opts, "extractor_args": {"youtube": {"player_client": ["android", "web_embedded"]}}},
    ]
    for bc in browser_choices:
        attempts.append({
            **base_opts,
            "cookiesfrombrowser": bc,
            "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
        })
    last_err = ""
    for opts in attempts:
        for stale in work.glob("raw.*"):
            try:
                stale.unlink()
            except Exception:
                pass
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.extract_info(url, download=True)
            break
        except Exception as exc:
            last_err = str(exc).splitlines()[-1][:120]
    else:
        print(f"download failed {key}: {last_err}", flush=True)
        return None
    raws = list(work.glob("raw.*"))
    if not raws:
        return None
    if not shutil.which("ffmpeg"):
        shutil.copy(raws[0], out)
        return str(out)
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", f"{start:.3f}",
            "-i", str(raws[0]),
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            "-loglevel", "error",
            str(out),
        ], check=True, timeout=120)
    except Exception as exc:
        print(f"ffmpeg trim failed {key}: {exc}", flush=True)
        return None
    return str(out) if out.exists() and out.stat().st_size > 1024 else None


def parse_json(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if not m:
            raise
        return json.loads(m.group(1))


def gemini_grader():
    import google.generativeai as genai

    env = lp._read_env_file()
    key = env.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY missing")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        "gemini-flash-latest",
        generation_config={"temperature": 0.0, "response_mime_type": "application/json"},
    )

    def call(parts: list[Any], retries: int = 4):
        for i in range(retries):
            try:
                return model.generate_content(parts)
            except Exception as exc:
                if "429" in str(exc) and i < retries - 1:
                    wait = 20 * (i + 1)
                    print(f"Gemini 429, waiting {wait}s", flush=True)
                    time.sleep(wait)
                    continue
                raise

    return genai, call


VIDEO_Q = (
    "You are evaluating audio descriptions for blind and low vision viewers. "
    "Watch the video clip and write exactly 3 yes/no questions that a complete "
    "audio description should answer. Focus on visible actions, scene changes, "
    "spatial details, and temporal events. Return JSON only as "
    '{"questions":[{"q":"...","evidence":"..."}]}.'
)
VIDEO_G = (
    "Watch the video clip. Grade whether the AD text answers the question with "
    "the required visual evidence. Score 1 if adequately covered, else 0. "
    "Return JSON only as {\"score\":0,\"rationale\":\"...\"}."
)


def minmax(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if hi == lo:
        return pd.Series([0.5] * len(s), index=s.index)
    return (s - lo) / (hi - lo)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--out", default=str(OUT / "live_held_out_queryd_gemini.csv"))
    args = ap.parse_args()

    caps, times, links = read_queryd()
    picked = pick_windows(caps, times, links, limit=max(args.n * 20, 50))
    print(f"QuerYD videos={len(caps)} links={len(links)} picked_candidates={len(picked)}", flush=True)

    clip_data = []
    for cand in picked:
        if len(clip_data) >= args.n:
            break
        print(f"[{len(clip_data)+1}/{args.n}] {cand['yt_id']} t={cand['start']:.1f} words={cand['word_count']}", flush=True)
        video = download_segment(cand["url"], cand["start"], cand["duration"], cand["video_key"])
        if not video:
            continue
        slug = "queryd_" + hashlib.sha1(video.encode()).hexdigest()[:12]
        ok, msg, fr = lp.stage_frames(video, slug, n=8)
        if not ok:
            print(f"  frames failed: {msg}", flush=True)
            continue
        utts = cand["utterances"]
        half = max(1, len(utts) // 2)
        clip_data.append({
            **cand,
            "video_path": video,
            "frames": fr["frames"],
            "tier1_min": utts[0],
            "tier2_partial": " ".join(utts[:half]),
            "tier3_full": cand["full_ad"],
        })

    if len(clip_data) < 2:
        raise RuntimeError("Not enough downloadable QuerYD clips")

    for i, cd in enumerate(clip_data):
        cd["tier0_cross"] = clip_data[(i + 1) % len(clip_data)]["tier3_full"]

    print(f"\nScoring {len(clip_data)} QuerYD real-human-AD clips", flush=True)
    lp._load_clip()
    genai, call = gemini_grader()
    rows = []
    for cd in clip_data:
        print(f"\n=== {cd['yt_id']} @ {cd['start']:.1f}s ===", flush=True)
        vf = genai.upload_file(cd["video_path"])
        while vf.state.name == "PROCESSING":
            time.sleep(1)
            vf = genai.get_file(vf.name)
        qr = call([vf, VIDEO_Q + "\nJSON only."])
        parsed = parse_json(qr.text)
        questions = parsed.get("questions", []) if isinstance(parsed, dict) else parsed
        questions = [q for q in questions if isinstance(q, dict) and q.get("q")][:3]
        for q in questions:
            print(f"  Q: {q['q'][:100]}", flush=True)

        for tier in TIER_ORDER:
            ad = cd[tier]
            _, _, cl = lp.stage_clip_grounding(cd["frames"], ad)
            graded = []
            for q in questions:
                try:
                    gr = call([
                        vf,
                        VIDEO_G
                        + f"\nAD: {ad}\nQuestion: {q.get('q','')}\nNeeded: {q.get('evidence','')}\nJSON only.",
                    ])
                    gj = parse_json(gr.text)
                    if isinstance(gj, list) and gj:
                        gj = gj[0]
                    graded.append(int(gj.get("score", 0)) if isinstance(gj, dict) else 0)
                except Exception:
                    graded.append(0)
            adqa = float(np.mean(graded)) if graded else 0.0
            clip_score = float(cl.get("top3", 0.0))
            print(f"  {tier:13} gt={GT[tier]} clip={clip_score:.3f} adqa={adqa:.2f}", flush=True)
            rows.append({
                "clip": cd["video_key"],
                "yt_id": cd["yt_id"],
                "start": cd["start"],
                "tier": tier,
                "gt": GT[tier],
                "clip_score": clip_score,
                "adqa_score": adqa,
                "ad": ad,
            })

    df = pd.DataFrame(rows)
    df["clip_norm"] = df.groupby("clip")["clip_score"].transform(minmax)
    df["adqa_norm"] = df.groupby("clip")["adqa_score"].transform(minmax)
    df["ensemble"] = (df["clip_norm"] + df["adqa_norm"]) / 2
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)

    print("\n========================================", flush=True)
    print(f"GEMINI VIDEO NATIVE on QUERYD HUMAN AD, n={df['clip'].nunique()} clips, {len(df)} obs", flush=True)
    print("========================================", flush=True)
    for col in ["clip_score", "adqa_score", "ensemble"]:
        rho, p = spearmanr(df["gt"], df[col])
        print(f"rho ({col:>10}): {rho:.3f}  p={p:.4f}", flush=True)
    wins = total = ordered = 0
    for _, g in df.groupby("clip"):
        vals = {r.tier: r.ensemble for r in g.itertuples()}
        for a, b in [("tier3_full", "tier2_partial"), ("tier2_partial", "tier1_min"), ("tier1_min", "tier0_cross")]:
            total += 1
            wins += int(vals[a] > vals[b])
        ordered += int(vals["tier3_full"] > vals["tier2_partial"] > vals["tier1_min"] > vals["tier0_cross"])
    print(f"Pairwise ordered wins: {wins}/{total}", flush=True)
    print(f"Fully ordered: {ordered}/{df['clip'].nunique()}", flush=True)
    print(f"Saved to {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
