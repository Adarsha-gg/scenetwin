#!/usr/bin/env python3
"""Compute per-frame need weights for external clips (motion + speech proxy).

When TRIBE preds unavailable, mirrors neural_need_curve logic:
  need = motion salience + speech density gap
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

EXT = Path(__file__).resolve().parents[1] / "data" / "external_clips"
REGISTRY = EXT / "registry.jsonl"
NEED_DIR = EXT / "need"
FRAMES_ROOT = EXT / "frames"


def speech_intervals(mp4: Path) -> list[tuple[float, float]]:
    cmd = [
        "ffmpeg", "-i", str(mp4), "-af", "silencedetect=noise=-30dB:d=0.3",
        "-f", "null", "-",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = r.stderr
    starts = [float(x) for x in re.findall(r"silence_start: (\d+\.?\d*)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: (\d+\.?\d*)", log)]
    # invert silence → speech intervals (approx)
    cap = cv2.VideoCapture(str(mp4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / fps
    cap.release()
    if not starts:
        return [(0.0, total)] if total > 0 else []
    speech = []
    t0 = 0.0
    for s in starts:
        if s > t0:
            speech.append((t0, s))
        t0 = ends[min(len(ends) - 1, starts.index(s))] if ends else s
    if t0 < total:
        speech.append((t0, total))
    return speech


def speech_density(intervals: list[tuple[float, float]], start: float, end: float) -> float:
    dur = max(end - start, 1e-9)
    sp = sum(max(0.0, min(end, b) - max(start, a)) for a, b in intervals)
    return min(1.0, sp / dur)


def frame_motion_scores(frame_paths: list[Path]) -> np.ndarray:
    scores = []
    prev = None
    for p in frame_paths:
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is None:
            scores.append(0.0)
            continue
        if prev is None:
            scores.append(0.0)
        else:
            diff = cv2.absdiff(img, prev)
            scores.append(float(np.mean(diff)))
        prev = img
    arr = np.array(scores, dtype=float)
    lo, hi = arr.min(), arr.max()
    if hi > lo:
        arr = (arr - lo) / (hi - lo)
    return arr


def minmax(v: np.ndarray) -> np.ndarray:
    lo, hi = np.nanmin(v), np.nanmax(v)
    if not np.isfinite(lo) or hi == lo:
        return np.zeros_like(v)
    return (v - lo) / (hi - lo)


def build_need_curve(video_id: str, mp4: Path, frame_paths: list[Path]) -> pd.DataFrame:
    motion = frame_motion_scores(frame_paths)
    intervals = speech_intervals(mp4)
    n = len(frame_paths)
    cap = cv2.VideoCapture(str(mp4))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = (cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0) / fps
    cap.release()
    rows = []
    for i, p in enumerate(frame_paths):
        t_mid = (i + 0.5) * total / max(n, 1)
        t0 = i * total / max(n, 1)
        t1 = (i + 1) * total / max(n, 1)
        sp = speech_density(intervals, t0, t1)
        need = 0.6 * motion[i] + 0.4 * (1.0 - sp)  # high motion + silent gaps = need AD
        rows.append({
            "video_id": video_id,
            "frame_idx": i,
            "t_mid": t_mid,
            "motion_score": float(motion[i]),
            "speech_density": sp,
            "need_score": float(need),
            "standard_slot_score": float(need * (1.0 - sp)),
            "extended_need_score": float(need * sp),
        })
    df = pd.DataFrame(rows)
    df["need_score"] = minmax(df["need_score"].to_numpy())
    return df


def main() -> None:
    NEED_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        meta = json.loads(line)
        vid = meta["video_id"]
        mp4 = EXT / vid / "clip.mp4"
        frames = sorted((FRAMES_ROOT / vid).glob("frame_*.jpg"))
        if not mp4.exists() or not frames:
            continue
        df = build_need_curve(vid, mp4, frames)
        out = NEED_DIR / f"{vid}.csv"
        df.to_csv(out, index=False)
        n += 1
        print(f"{vid}: mean_need={df['need_score'].mean():.3f} speech={df['speech_density'].mean():.2f}")
    print(f"Wrote {n} need curves → {NEED_DIR}")


if __name__ == "__main__":
    main()
