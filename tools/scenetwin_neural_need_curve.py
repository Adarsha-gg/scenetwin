#!/usr/bin/env python3
"""TRIBE-based audio-description need curve.

This pivots SceneTwin away from "TRIBE judges whether text is correct" and toward
"TRIBE estimates where the original audio fails to carry the audiovisual scene."

For each clip with saved audiovisual and audio-only TRIBE predictions, compute a
time-resolved accessibility gap:

    gap(t) = difference between P_AV[t] and P_A[t]

Then combine that with speech density to separate:

    standard AD opportunities: high gap, low speech
    extended/integrated AD needs: high gap, high speech
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
PRED_DIR = DG_DIR / "preds"
AUDIO_DIR = DG_DIR / "audio"

OUT_CSV = DG_DIR / "neural_description_need_curve.csv"
OUT_SUMMARY = DG_DIR / "neural_description_need_summary.csv"
OUT_SVG = DG_DIR / "neural_description_need_curve.svg"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-neural-description-need.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-neural-description-need-pivot.md"


def load_pred(name: str) -> np.ndarray:
    return np.load(PRED_DIR / f"{name}.npy")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return float("nan")
    return float(np.dot(a, b) / denom)


def minmax(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    lo = np.nanmin(values)
    hi = np.nanmax(values)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as handle:
        return handle.getnframes() / float(handle.getframerate())


def word_intervals(path: Path) -> list[tuple[float, float]]:
    if not path.exists():
        return []
    df = pd.read_csv(path, sep="\t")
    intervals = []
    for row in df.itertuples(index=False):
        start = float(row.start)
        end = start + float(row.duration)
        intervals.append((start, end))
    return intervals


def overlap_seconds(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def speech_density(intervals: list[tuple[float, float]], start: float, end: float) -> float:
    dur = max(end - start, 1e-9)
    speech = sum(overlap_seconds(start, end, w0, w1) for w0, w1 in intervals)
    return min(1.0, speech / dur)


def recommendation(need: float, speech: float) -> str:
    if need < 0.45:
        return "low_ad_need"
    if speech < 0.25:
        return "standard_ad_slot"
    if speech < 0.55:
        return "compressed_or_after_dialogue"
    return "extended_or_integrated_ad"


def available_clip_indices() -> list[int]:
    clips = []
    for p_av in sorted(PRED_DIR.glob("clip_*_P_AV.npy")):
        clip_idx = int(p_av.name.split("_")[1])
        if (PRED_DIR / f"clip_{clip_idx:02d}_P_A.npy").exists():
            clips.append(clip_idx)
    return clips


def compute_curve() -> pd.DataFrame:
    rows = []
    for clip_idx in available_clip_indices():
        p_av = load_pred(f"clip_{clip_idx:02d}_P_AV")
        p_a = load_pred(f"clip_{clip_idx:02d}_P_A")
        if p_av.shape != p_a.shape:
            raise ValueError(f"Shape mismatch for clip_{clip_idx:02d}: {p_av.shape} vs {p_a.shape}")

        duration = wav_duration(AUDIO_DIR / f"clip_{clip_idx:02d}.wav")
        words = word_intervals(AUDIO_DIR / f"clip_{clip_idx:02d}.tsv")
        n_steps = p_av.shape[0]
        step = duration / n_steps

        residual_norm = np.linalg.norm(p_av - p_a, axis=1) / np.sqrt(p_av.shape[1])
        cosine_gap = np.array([1.0 - cosine(p_av[t], p_a[t]) for t in range(n_steps)])
        need_score = 0.5 * minmax(residual_norm) + 0.5 * minmax(cosine_gap)

        for t in range(n_steps):
            start = t * step
            end = (t + 1) * step
            speech = speech_density(words, start, end)
            rows.append(
                {
                    "clip_idx": clip_idx,
                    "t": t,
                    "start_s": start,
                    "end_s": end,
                    "residual_norm": residual_norm[t],
                    "cosine_gap": cosine_gap[t],
                    "need_score": need_score[t],
                    "speech_density": speech,
                    "standard_slot_score": need_score[t] * (1.0 - speech),
                    "extended_need_score": need_score[t] * speech,
                    "recommendation": recommendation(need_score[t], speech),
                }
            )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for clip_idx, group in df.groupby("clip_idx"):
        top_need = group.sort_values("need_score", ascending=False).head(3)
        top_standard = group.sort_values("standard_slot_score", ascending=False).head(3)
        top_extended = group.sort_values("extended_need_score", ascending=False).head(3)
        rows.append(
            {
                "clip_idx": clip_idx,
                "mean_need_score": group["need_score"].mean(),
                "max_need_score": group["need_score"].max(),
                "mean_speech_density": group["speech_density"].mean(),
                "top_need_windows": "; ".join(
                    f"{r.start_s:.1f}-{r.end_s:.1f}s ({r.need_score:.2f}, {r.recommendation})"
                    for r in top_need.itertuples(index=False)
                ),
                "top_standard_slots": "; ".join(
                    f"{r.start_s:.1f}-{r.end_s:.1f}s ({r.standard_slot_score:.2f})"
                    for r in top_standard.itertuples(index=False)
                ),
                "top_extended_needs": "; ".join(
                    f"{r.start_s:.1f}-{r.end_s:.1f}s ({r.extended_need_score:.2f})"
                    for r in top_extended.itertuples(index=False)
                ),
            }
        )
    return pd.DataFrame(rows)


def write_svg_curve(df: pd.DataFrame) -> None:
    clips = sorted(df["clip_idx"].unique())
    width = 1000
    row_height = 260
    margin_left = 60
    margin_right = 30
    margin_top = 45
    margin_bottom = 35
    height = row_height * len(clips)

    def polyline(points: list[tuple[float, float]], color: str, width_px: int = 3) -> str:
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{width_px}" />'

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white" />',
        '<style>text{font-family:Arial,sans-serif;font-size:13px;fill:#222}.title{font-size:16px;font-weight:700}.legend{font-size:12px}</style>',
    ]

    for row_idx, clip_idx in enumerate(clips):
        group = df[df["clip_idx"] == clip_idx]
        y0 = row_idx * row_height
        chart_left = margin_left
        chart_top = y0 + margin_top
        chart_width = width - margin_left - margin_right
        chart_height = row_height - margin_top - margin_bottom
        max_t = float(group["end_s"].max())

        def x_for(t: float) -> float:
            return chart_left + (t / max_t) * chart_width if max_t else chart_left

        def y_for(v: float) -> float:
            return chart_top + (1.0 - max(0.0, min(1.0, v))) * chart_height

        mid = ((group["start_s"] + group["end_s"]) / 2.0).to_numpy()
        need = group["need_score"].to_numpy()
        speech = group["speech_density"].to_numpy()
        standard = group["standard_slot_score"].to_numpy()
        extended = group["extended_need_score"].to_numpy()

        parts.append(f'<text class="title" x="{chart_left}" y="{y0 + 24}">clip_{clip_idx:02d}: neural description need</text>')
        parts.append(f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="#999" />')
        parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="#999" />')
        parts.append(f'<text x="{chart_left - 45}" y="{chart_top + 5}">1.0</text>')
        parts.append(f'<text x="{chart_left - 45}" y="{chart_top + chart_height}">0.0</text>')
        parts.append(f'<text x="{chart_left}" y="{chart_top + chart_height + 24}">0s</text>')
        parts.append(f'<text x="{chart_left + chart_width - 35}" y="{chart_top + chart_height + 24}">{max_t:.1f}s</text>')

        parts.append(polyline([(x_for(t), y_for(v)) for t, v in zip(mid, standard)], "#7fb3d5", 5))
        parts.append(polyline([(x_for(t), y_for(v)) for t, v in zip(mid, extended)], "#f5b041", 5))
        parts.append(polyline([(x_for(t), y_for(v)) for t, v in zip(mid, need)], "#1f618d", 3))
        parts.append(polyline([(x_for(t), y_for(v)) for t, v in zip(mid, speech)], "#b03a2e", 3))
        parts.append(f'<text class="legend" x="{chart_left + 520}" y="{y0 + 24}"><tspan fill="#1f618d">need</tspan> | <tspan fill="#b03a2e">speech</tspan> | <tspan fill="#7fb3d5">standard slot</tspan> | <tspan fill="#f5b041">extended need</tspan></text>')

    parts.append("</svg>")
    OUT_SVG.write_text("\n".join(parts), encoding="utf-8")


def write_report(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    top_rows = (
        df.sort_values(["clip_idx", "need_score"], ascending=[True, False])
        .groupby("clip_idx")
        .head(5)
    )

    report = f"""---
title: "SceneTwin Neural Description Need"
category: research
tags: [SceneTwin, TRIBE, audio-description, timing, accessibility-gap]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_description_need_summary.csv
  - output/scenetwin_description_gain/neural_description_need_curve.svg
---

# SceneTwin Neural Description Need

## Pivot

TRIBE should not be used as the primary text-correctness judge. The smoke tests show that rich wrong descriptions can still look neurally plausible.

The stronger use of TRIBE is upstream:

```text
AccessibilityGap(t) = distance(P_AV[t], P_A[t])
```

This asks where the full audiovisual scene contains predicted neural signal that the soundtrack alone does not carry. That is exactly the audio-description problem: describe important visual information not available through audio alone.

## Metrics

For each time window:

- `residual_norm`: normalized magnitude of `P_AV[t] - P_A[t]`
- `cosine_gap`: `1 - cos(P_AV[t], P_A[t])`
- `need_score`: combined normalized residual/cosine gap
- `speech_density`: how much original speech occupies the window
- `standard_slot_score`: high gap with low speech
- `extended_need_score`: high gap with high speech

## Clip Summary

{summary.to_markdown(index=False)}

## Highest-Need Windows

{top_rows[["clip_idx", "start_s", "end_s", "need_score", "speech_density", "standard_slot_score", "extended_need_score", "recommendation"]].to_markdown(index=False)}

## Why This Is Better

This avoids the failure mode from raw Description Gain:

- It does not ask TRIBE to decide whether text is correct.
- It uses TRIBE only for video/audio counterfactuals from the same source clip.
- It creates an actionable product: when to describe, how urgent the need is, and whether standard or extended AD is required.

The content layer should be handled separately with CLIP/SigLIP/PAC-S and a VLM captioner.

## Product Direction

SceneTwin becomes an **AD need planner**:

1. Use TRIBE to compute the accessibility gap curve.
2. Use speech density to find available narration windows.
3. Use a VLM to propose descriptions for high-need moments.
4. Use CLIP/SigLIP/PAC-S to ground the proposed descriptions.
5. Use user profile settings to choose concise vs detailed output.

This is more defensible than raw neural text scoring and much closer to a useful accessibility tool.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report.replace("output/scenetwin_description_gain/", "output/scenetwin_description_gain/"), encoding="utf-8")


def main() -> None:
    df = compute_curve()
    summary = summarize(df)
    df.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    write_svg_curve(df)
    write_report(df, summary)

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_SVG}")
    print(f"Wrote {OUT_REPORT}")
    print(f"Wrote {OUT_WIKI}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
