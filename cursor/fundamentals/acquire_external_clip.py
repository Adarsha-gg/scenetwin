#!/usr/bin/env python3
"""Download NEW clips from vatex_overlap.json — expand beyond the 18-clip benchmark.

Picks overlap candidates not in vatex_eval_clips.json, downloads YouTube segment,
writes tier scaffold (va11y + vatex short/long + cross control).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERLAP = ROOT / "workspace" / "vatex_overlap.json"
EVAL = ROOT / "workspace" / "vatex_eval_clips.json"
EXT_DIR = Path(__file__).resolve().parent.parent / "data" / "external_clips"
REGISTRY = EXT_DIR / "registry.jsonl"
CROSS_CONTROL = (
    "At night, a skier navigates a snowy hill, weaving between flexible poles in a "
    "slalom course. The skier moves swiftly, alternating left and right, purposefully "
    "making contact with each pole as they descend the slope."
)


def parse_video_id(vid: str) -> tuple[str, float, float]:
    m = re.match(r"^(.+?)_(\d+(?:\.\d+)?)_(\d+(?:\.\d+)?)$", vid)
    if not m:
        raise ValueError(f"bad video_id: {vid}")
    return m.group(1), float(m.group(2)), float(m.group(3))


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def existing_ids() -> set[str]:
    ids = {r["video_id"] for r in load_json(EVAL)}
    if REGISTRY.exists():
        for line in REGISTRY.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ids.add(json.loads(line)["video_id"])
    return ids


def pick_candidate(index: int) -> dict:
    have = existing_ids()
    pool = [r for r in load_json(OVERLAP) if r["video_id"] not in have]
    if not pool:
        raise SystemExit("No new overlap candidates — expand vatex_overlap.json")
    return pool[index % len(pool)]


def build_tiers(row: dict) -> dict:
    caps = row.get("vatex_caps") or []
    short = caps[0] if caps else ""
    long_cap = max(caps, key=len) if caps else short
    return {
        "video_id": row["video_id"],
        "category": row.get("category", "Unknown"),
        "tier3_va11y": row.get("va11y_desc", ""),
        "tier1_vatex_short": short,
        "tier2_vatex_long": long_cap,
        "tier0_cross": CROSS_CONTROL,
    }


def download_segment(yt_id: str, start: float, end: float, out_mp4: Path) -> tuple[bool, str]:
    if out_mp4.exists() and out_mp4.stat().st_size > 4096:
        return True, "cached"
    try:
        import yt_dlp
    except ImportError:
        return False, "yt-dlp not installed"

    work = out_mp4.parent
    work.mkdir(parents=True, exist_ok=True)
    raw = work / "raw.%(ext)s"
    url = f"https://www.youtube.com/watch?v={yt_id}"
    if start > 0:
        url += f"&t={int(start)}"

    opts = {
        "format": "mp4[height<=480]/best[height<=480]/best",
        "outtmpl": str(raw),
        "quiet": True,
        "noplaylist": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception as e:
        return False, str(e).splitlines()[-1][:200]

    candidates = list(work.glob("raw.*"))
    if not candidates:
        return False, "no download file"
    src = candidates[0]
    dur = max(1.0, end - start)
    if not shutil.which("ffmpeg"):
        shutil.copy(src, out_mp4)
        return True, "no ffmpeg — full file kept"

    cmd = [
        "ffmpeg", "-y", "-ss", str(start), "-i", str(src),
        "-t", str(dur), "-c:v", "libx264", "-c:a", "aac",
        "-movflags", "+faststart", str(out_mp4),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stderr[-200:]
    return True, f"trimmed {dur:.1f}s"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", type=int, default=0, help="rotation index into candidate pool")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cand = pick_candidate(args.index)
    yt_id, start, end = parse_video_id(cand["video_id"])
    meta = build_tiers(cand)
    meta["yt_id"] = yt_id
    meta["start"] = start
    meta["end"] = end
    meta["acquired_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    clip_dir = EXT_DIR / cand["video_id"]
    meta_path = clip_dir / "metadata.json"
    video_path = clip_dir / "clip.mp4"

    print(f"Candidate: {cand['video_id']} ({meta['category']})")
    print(f"  tier3 words: {len(meta['tier3_va11y'].split())}")
    print(f"  vatex caps: {len(cand.get('vatex_caps', []))}")

    if args.dry_run:
        print("dry-run — skip download")
        return

    ok, msg = download_segment(yt_id, start, end, video_path)
    meta["download_ok"] = ok
    meta["download_msg"] = msg
    if not ok:
        print(f"DOWNLOAD FAILED: {msg}", file=sys.stderr)
        sys.exit(1)

    clip_dir.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    with REGISTRY.open("a", encoding="utf-8") as f:
        f.write(json.dumps(meta) + "\n")
    print(f"OK → {video_path} ({msg})")
    print(f"Registry: {REGISTRY}")


if __name__ == "__main__":
    main()
