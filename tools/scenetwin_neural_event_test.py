#!/usr/bin/env python3
"""Test TRIBE neural event metrics on the two saved SceneTwin clips.

This evaluates a TRIBE-native use case:

    visual-only neural events = state changes in P_AV that are stronger than
    corresponding state changes in P_A.

Unlike description scoring, this does not ask TRIBE to judge text correctness.
It asks whether removing vision changes the predicted brain-state trajectory.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PRED_DIR = ROOT / "output" / "scenetwin_description_gain" / "preds"
NEED_CSV = ROOT / "output" / "scenetwin_description_gain" / "neural_description_need_curve.csv"
FRAME_ROOT = ROOT / "output" / "scenetwin_need_validation"
OUT_DIR = ROOT / "output" / "scenetwin_event_validation"
OUT_CSV = ROOT / "output" / "scenetwin_description_gain" / "neural_event_test_results.csv"
OUT_SUMMARY = ROOT / "output" / "scenetwin_description_gain" / "neural_event_test_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-neural-event-test.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-neural-event-test.md"


def load_pred(name: str) -> np.ndarray:
    return np.load(PRED_DIR / f"{name}.npy")


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return float("nan")
    return float(np.dot(a, b) / denom)


def robust_norm(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    lo = np.nanmin(values)
    hi = np.nanmax(values)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def available_clip_indices() -> list[int]:
    out = []
    for p in sorted(PRED_DIR.glob("clip_*_P_AV.npy")):
        clip_idx = int(p.name.split("_")[1])
        if (PRED_DIR / f"clip_{clip_idx:02d}_P_A.npy").exists():
            out.append(clip_idx)
    return out


def compute_events() -> pd.DataFrame:
    need = pd.read_csv(NEED_CSV)
    rows = []
    for clip_idx in available_clip_indices():
        av = load_pred(f"clip_{clip_idx:02d}_P_AV")
        a = load_pred(f"clip_{clip_idx:02d}_P_A")
        if av.shape != a.shape:
            raise ValueError(f"shape mismatch for clip_{clip_idx:02d}: {av.shape} vs {a.shape}")

        clip_need = need[need["clip_idx"] == clip_idx].set_index("t")
        av_shift = np.array([0.0] + [1.0 - cosine(av[t - 1], av[t]) for t in range(1, len(av))])
        a_shift = np.array([0.0] + [1.0 - cosine(a[t - 1], a[t]) for t in range(1, len(a))])
        visual_delta = np.maximum(av_shift - a_shift, 0.0)
        audio_delta = np.maximum(a_shift - av_shift, 0.0)
        visual_event_score = robust_norm(visual_delta)
        av_event_score = robust_norm(av_shift)

        for t in range(len(av)):
            nrow = clip_need.loc[t]
            rows.append(
                {
                    "clip_idx": clip_idx,
                    "t": t,
                    "start_s": float(nrow.start_s),
                    "end_s": float(nrow.end_s),
                    "av_shift": av_shift[t],
                    "audio_shift": a_shift[t],
                    "visual_only_delta": visual_delta[t],
                    "audio_only_delta": audio_delta[t],
                    "av_event_score": av_event_score[t],
                    "visual_event_score": visual_event_score[t],
                    "need_score": float(nrow.need_score),
                    "speech_density": float(nrow.speech_density),
                    "visual_event_need": visual_event_score[t] * float(nrow.need_score),
                    "recommendation": nrow.recommendation,
                }
            )
    return pd.DataFrame(rows)


def font(size: int) -> ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def make_transition_sheet(df: pd.DataFrame) -> dict[int, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sheets = {}
    title_font = font(18)
    small = font(12)
    tiny = font(10)

    for clip_idx, group in df.groupby("clip_idx"):
        transitions = group[group["t"] > 0].sort_values("visual_event_need", ascending=False).head(6)
        cell_w = 360
        cell_h = 250
        sheet = Image.new("RGB", (cell_w * 2, cell_h * 3 + 44), "white")
        draw = ImageDraw.Draw(sheet)
        draw.text((10, 10), f"clip_{clip_idx:02d}: top visual-only neural transitions", font=title_font, fill=(20, 20, 20))

        for i, row in enumerate(transitions.itertuples(index=False)):
            x = (i % 2) * cell_w
            y = 44 + (i // 2) * cell_h
            before = FRAME_ROOT / f"clip_{clip_idx:02d}_frames" / f"t{int(row.t) - 1:02d}.jpg"
            after = FRAME_ROOT / f"clip_{clip_idx:02d}_frames" / f"t{int(row.t):02d}.jpg"
            pair = Image.new("RGB", (cell_w, 130), (235, 235, 235))
            for j, path in enumerate([before, after]):
                img = Image.open(path).convert("RGB")
                img.thumbnail((176, 120))
                pair.paste(img, (j * 180 + (176 - img.width) // 2, 5 + (120 - img.height) // 2))
            sheet.paste(pair, (x, y))
            label = (
                f"t{int(row.t)-1:02d}->t{int(row.t):02d} {row.start_s:.1f}-{row.end_s:.1f}s\n"
                f"visual event {row.visual_event_score:.2f} | need {row.need_score:.2f}\n"
                f"AV shift {row.av_shift:.3f} vs audio {row.audio_shift:.3f}\n"
                f"speech {row.speech_density:.2f} | {row.recommendation}"
            )
            draw.multiline_text((x + 8, y + 138), label, font=small, fill=(30, 30, 30), spacing=4)
            draw.text((x + 8, y + 222), "before -> after", font=tiny, fill=(90, 90, 90))

        out = OUT_DIR / f"clip_{clip_idx:02d}_event_validation.jpg"
        sheet.save(out, quality=92)
        sheets[int(clip_idx)] = out
    return sheets


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for clip_idx, group in df.groupby("clip_idx"):
        top_visual = group[group["t"] > 0].sort_values("visual_event_need", ascending=False).head(3)
        top_av = group[group["t"] > 0].sort_values("av_event_score", ascending=False).head(3)
        rows.append(
            {
                "clip_idx": clip_idx,
                "mean_visual_only_delta": group["visual_only_delta"].mean(),
                "max_visual_event_score": group["visual_event_score"].max(),
                "top_visual_only_events": "; ".join(
                    f"t{int(r.t)-1}->t{int(r.t)} {r.start_s:.1f}-{r.end_s:.1f}s "
                    f"(event={r.visual_event_score:.2f}, need={r.need_score:.2f})"
                    for r in top_visual.itertuples(index=False)
                ),
                "top_av_events": "; ".join(
                    f"t{int(r.t)-1}->t{int(r.t)} {r.start_s:.1f}-{r.end_s:.1f}s "
                    f"(AV={r.av_event_score:.2f}, audio={r.audio_shift:.3f})"
                    for r in top_av.itertuples(index=False)
                ),
            }
        )
    return pd.DataFrame(rows)


def write_report(df: pd.DataFrame, summary: pd.DataFrame, sheets: dict[int, Path]) -> None:
    top = df[df["t"] > 0].sort_values(["clip_idx", "visual_event_need"], ascending=[True, False]).groupby("clip_idx").head(5)
    sheet_table = pd.DataFrame(
        {
            "clip_idx": list(sheets.keys()),
            "validation_sheet": [str(path.relative_to(ROOT)) for path in sheets.values()],
        }
    )
    report = f"""---
title: "SceneTwin Neural Event Test"
category: research
tags: [SceneTwin, TRIBE, event-boundaries, accessibility-gap, validation]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_event_test_results.csv
  - output/scenetwin_description_gain/neural_event_test_summary.csv
  - output/scenetwin_event_validation/
---

# SceneTwin Neural Event Test

## Metric

TRIBE gives a time series of predicted cortical states. This test looks for visual-only neural events:

```text
AVShift(t) = 1 - cos(P_AV[t-1], P_AV[t])
AudioShift(t) = 1 - cos(P_A[t-1], P_A[t])
VisualOnlyEvent(t) = max(AVShift(t) - AudioShift(t), 0)
VisualEventNeed(t) = normalized(VisualOnlyEvent(t)) * AccessibilityGap(t)
```

This is different from frame difference or optical flow. It asks whether the predicted brain state changes more when vision is present than when only audio is present.

## Summary

{summary.to_markdown(index=False)}

## Validation Sheets

{sheet_table.to_markdown(index=False)}

## Top Visual-Only Events

{top[["clip_idx", "t", "start_s", "end_s", "av_shift", "audio_shift", "visual_event_score", "need_score", "visual_event_need", "speech_density", "recommendation"]].to_markdown(index=False)}

## Verdict

This is worth keeping as a second TRIBE-native signal.

- The accessibility-gap curve answers **where visual information is missing from audio**.
- The neural-event curve answers **where the visual scene changes brain state more than the audio does**.

On these two clips, the metric is plausible but not independently validated. It should be tested on all 20 clips with visual sheets and human labels for whether each top event truly needs AD.

Known failure risk: symbolic visual content such as signs/title cards may still need OCR/VLM support.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")


def main() -> None:
    df = compute_events()
    summary = summarize(df)
    sheets = make_transition_sheet(df)
    df.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    write_report(df, summary, sheets)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    for path in sheets.values():
        print(f"Wrote {path}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
