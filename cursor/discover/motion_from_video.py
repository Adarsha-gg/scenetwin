#!/usr/bin/env python3
"""FluNet/VFA-inspired: motion fluency from pixels on external + benchmark clips.

Uses ffmpeg scene detection — no CLIP, no Spearman on benchmark.
Correlates motion score with TRIBE need / ADQA on same clip.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EXT = Path(__file__).resolve().parents[1] / "data" / "external_clips"
BENCH_FRAMES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames"
NEED = ROOT / "output" / "scenetwin_timing_20clip" / "need" / "neural_description_need_curve.csv"
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "motion_scores.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-motion.md"


def motion_score_ffmpeg(video: Path) -> float:
    if not video.exists():
        return float("nan")
    cmd = [
        "ffmpeg", "-i", str(video), "-vf", "select='gt(scene,0.25)',showinfo", "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    scenes = len(re.findall(r"pts_time:", r.stderr))
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "default=noprint_wrappers=1:nokey=1", str(video)]
    dur_r = subprocess.run(dur_cmd, capture_output=True, text=True)
    try:
        dur = float(dur_r.stdout.strip())
    except Exception:
        dur = 10.0
    return scenes / max(dur, 1.0)  # scene changes per second


def main() -> None:
    rows = []
    # External clips
    reg = EXT / "registry.jsonl"
    if reg.exists():
        for line in reg.read_text().splitlines():
            if not line.strip():
                continue
            meta = json.loads(line)
            vid = meta["video_id"]
            mp4 = EXT / vid / "clip.mp4"
            rows.append({
                "source": "external",
                "clip_id": vid,
                "motion_scenes_per_s": motion_score_ffmpeg(mp4),
                "category": meta.get("category"),
            })

    # Benchmark: use adqa_frames videos if present
    fc = pd.read_csv(FORECAST)
    for cidx in fc["clip_idx"].unique()[:8]:  # sample 8 per run for speed
        for p in (BENCH_FRAMES / f"clip_{int(cidx):02d}").glob("*.mp4"):
            rows.append({
                "source": "benchmark",
                "clip_id": f"clip_{int(cidx):02d}",
                "clip_idx": int(cidx),
                "motion_scenes_per_s": motion_score_ffmpeg(p),
                "category": fc[fc["clip_idx"] == cidx]["category"].iloc[0],
                "tribe_pressure": float(fc[fc["clip_idx"] == cidx]["tribe_pressure"].iloc[0]),
            })
            break

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    bench = df[(df["source"] == "benchmark") & df["tribe_pressure"].notna()] if "tribe_pressure" in df.columns else pd.DataFrame()
    r_txt = "n/a"
    if len(bench) >= 4:
        from scipy.stats import spearmanr
        r, p = spearmanr(bench["motion_scenes_per_s"], bench["tribe_pressure"])
        r_txt = f"ρ(motion, tribe_pressure)={r:.3f} p={p:.4f}"

    FINDINGS.write_text(
        f"# Motion fluency from pixels (VFA/FluNet inspired)\n\n"
        f"{r_txt}\n\n"
        f"**NEW axis:** high motion → more need for extended AD?\n\n"
        f"{df.to_string(index=False)}\n",
        encoding="utf-8",
    )
    print(df.to_string(index=False))
    print(r_txt)


if __name__ == "__main__":
    main()
