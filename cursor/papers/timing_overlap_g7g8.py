#!/usr/bin/env python3
"""VideoA11y guideline G7/G8 proxy — AD overlap with speech (openreview timeliness paper).

G7: count overlapping seconds if AD read at 200 wpm during speech.
G8: words of AD per silent second.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
NEED_CSV = ROOT / "output" / "scenetwin_timing_20clip" / "need" / "coarse_need_windows.csv"
FRAMES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames"
OUT = Path(__file__).resolve().parent / "output" / "timing_overlap_g7g8.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-timing-g7g8.md"

WPM = 200
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COL = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
       "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}


def ad_duration_seconds(text: str) -> float:
    words = len(text.split())
    return words / (WPM / 60.0)


def speech_seconds_in_clip(clip_idx: int) -> float:
    sub = pd.read_csv(NEED_CSV)
    sub = sub[sub["clip_idx"] == clip_idx]
    return float((sub["speech_density"] * (sub["end_s"] - sub["start_s"])).sum())


def clip_duration(clip_idx: int) -> float:
    sub = pd.read_csv(NEED_CSV)
    sub = sub[sub["clip_idx"] == clip_idx]
    if sub.empty:
        return 10.0
    return float(sub["end_s"].max())


def main() -> None:
    fc = pd.read_csv(FORECAST)
    rows = []
    for _, clip in fc.iterrows():
        cidx = int(clip["clip_idx"])
        dur = clip_duration(cidx)
        speech_s = speech_seconds_in_clip(cidx)
        silent_s = max(0.01, dur - speech_s)
        for tier in TIERS:
            text = str(clip[COL[tier]])
            ad_s = ad_duration_seconds(text)
            overlap = min(ad_s, speech_s)  # naive: AD starts at t=0
            g7 = overlap
            g8 = len(text.split()) / silent_s
            # Higher g8 (fill silent gaps) good; lower g7 (speech collision) good
            g7g8_score = g8 - 0.35 * g7
            rows.append({"clip_idx": cidx, "tier": tier, "gt": TIERS.index(tier),
                         "g7_overlap_seconds": g7, "g8_words_per_silent_sec": g8,
                         "g7g8_score": g7g8_score,
                         "ad_read_seconds": ad_s, "speech_seconds": speech_s})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    # Lower G7 is better for tier3 (less speech collision)
    t3 = df[df["tier"] == "tier3_va11y"]["g7_overlap_seconds"].mean()
    t1 = df[df["tier"] == "tier1_vatex_short"]["g7_overlap_seconds"].mean()
    FINDINGS.write_text(
        f"# Timing G7/G8 proxy\n\n"
        f"Mean G7 overlap (lower=better): pro **{t3:.2f}s** vs short **{t1:.2f}s**\n\n"
        f"Pro AD is longer → more speech collision risk on speech-heavy clips.\n",
        encoding="utf-8",
    )
    print(f"G7 pro={t3:.2f}s short={t1:.2f}s → {OUT}")


if __name__ == "__main__":
    main()
