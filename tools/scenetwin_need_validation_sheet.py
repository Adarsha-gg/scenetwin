#!/usr/bin/env python3
"""Create visual validation sheets for SceneTwin neural need curves."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
NEED_CSV = ROOT / "output" / "scenetwin_description_gain" / "neural_description_need_curve.csv"
VIDEO_ROOT = Path("/Users/adarsha/njbda/vatex_clips")
OUT_DIR = ROOT / "output" / "scenetwin_need_validation"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-neural-need-visual-validation.md"


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


def extract_frame(video: Path, timestamp: float, out: Path) -> None:
    if out.exists():
        return
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def label_color(recommendation: str) -> tuple[int, int, int]:
    if recommendation == "standard_ad_slot":
        return (31, 97, 141)
    if recommendation == "extended_or_integrated_ad":
        return (181, 88, 38)
    if recommendation == "compressed_or_after_dialogue":
        return (142, 68, 173)
    return (90, 90, 90)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, max_width: int, fnt: ImageFont.ImageFont) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        box = draw.textbbox((0, 0), trial, font=fnt)
        if box[2] <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def make_sheet(clip_idx: int, group: pd.DataFrame) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame_dir = OUT_DIR / f"clip_{clip_idx:02d}_frames"
    frame_dir.mkdir(parents=True, exist_ok=True)
    video = VIDEO_ROOT / f"clip_{clip_idx:02d}.mp4"

    rows = []
    for row in group.itertuples(index=False):
        mid = (row.start_s + row.end_s) / 2.0
        frame_path = frame_dir / f"t{int(row.t):02d}.jpg"
        extract_frame(video, mid, frame_path)
        rows.append((row, frame_path))

    thumb_w, thumb_h = 240, 136
    label_h = 104
    cols = 3
    cell_w = thumb_w
    cell_h = thumb_h + label_h
    sheet_w = cols * cell_w
    sheet_h = ((len(rows) + cols - 1) // cols) * cell_h + 56
    sheet = Image.new("RGB", (sheet_w, sheet_h), "white")
    draw = ImageDraw.Draw(sheet)
    title_font = font(18)
    small_font = font(12)
    tiny_font = font(10)
    draw.text((10, 10), f"clip_{clip_idx:02d} neural AD need validation", fill=(20, 20, 20), font=title_font)

    for i, (row, frame_path) in enumerate(rows):
        col = i % cols
        line = i // cols
        x = col * cell_w
        y = 56 + line * cell_h
        img = Image.open(frame_path).convert("RGB")
        img.thumbnail((thumb_w, thumb_h))
        canvas = Image.new("RGB", (thumb_w, thumb_h), (235, 235, 235))
        canvas.paste(img, ((thumb_w - img.width) // 2, (thumb_h - img.height) // 2))
        sheet.paste(canvas, (x, y))

        color = label_color(row.recommendation)
        draw.rectangle((x, y + thumb_h, x + cell_w, y + cell_h), fill=(248, 248, 248))
        draw.rectangle((x, y + thumb_h, x + cell_w, y + thumb_h + 5), fill=color)
        label = (
            f"t{int(row.t):02d} {row.start_s:.1f}-{row.end_s:.1f}s | "
            f"need {row.need_score:.2f} speech {row.speech_density:.2f}"
        )
        draw.text((x + 6, y + thumb_h + 11), label, fill=(20, 20, 20), font=small_font)
        for j, line_text in enumerate(wrap_text(draw, row.recommendation, thumb_w - 12, tiny_font)[:2]):
            draw.text((x + 6, y + thumb_h + 33 + 15 * j), line_text, fill=color, font=tiny_font)
        draw.text(
            (x + 6, y + thumb_h + 68),
            f"std {row.standard_slot_score:.2f} ext {row.extended_need_score:.2f}",
            fill=(60, 60, 60),
            font=tiny_font,
        )

    out = OUT_DIR / f"clip_{clip_idx:02d}_need_validation.jpg"
    sheet.save(out, quality=92)
    return out


def write_report(df: pd.DataFrame, sheets: dict[int, Path]) -> None:
    observations = {
        0: (
            "High-need windows are mostly silent visual-action windows. This is the "
            "behavior we want for standard AD timing: the curve finds places where "
            "there is visual change but no dialogue competing for narration."
        ),
        1: (
            "Highest-need windows overlap dense speech. This is useful because the "
            "curve does not pretend a clean narration slot exists; it flags that the "
            "clip likely needs extended/integrated AD or a post-dialogue summary."
        ),
    }

    rows = []
    for clip_idx, group in df.groupby("clip_idx"):
        top = group.sort_values("need_score", ascending=False).head(3)
        rows.append(
            {
                "clip": f"clip_{clip_idx:02d}",
                "sheet": str(sheets[clip_idx].relative_to(ROOT)),
                "top_windows": "; ".join(
                    f"{r.start_s:.1f}-{r.end_s:.1f}s need={r.need_score:.2f} speech={r.speech_density:.2f}"
                    for r in top.itertuples(index=False)
                ),
                "judgment": observations.get(int(clip_idx), ""),
            }
        )

    table = pd.DataFrame(rows)
    report = f"""---
title: "SceneTwin Neural Need Visual Validation"
category: research
tags: [SceneTwin, TRIBE, validation, audio-description, timing]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_need_validation/
  - wiki/research/scenetwin-neural-description-need-pivot.md
---

# SceneTwin Neural Need Visual Validation

## Verdict

The two-clip visual check supports the pivot enough to justify a 20-clip `P_AV`/`P_A` run.

This does **not** prove the metric is validated. It shows that, on the two clips we already processed, the curve is not random:

- clip 00: high need appears in silent visual-action windows, so standard AD slots are plausible.
- clip 01: high need appears during dense speech, so the model correctly surfaces an extended/integrated AD problem instead of pretending there is room for ordinary narration.

## Evidence

{table.to_markdown(index=False)}

## Interpretation

This is a better TRIBE use case than text scoring because it only compares the same clip under two conditions:

```text
P_AV = audiovisual scene
P_A = audio-only scene
AccessibilityGap(t) = distance(P_AV[t], P_A[t])
```

The content of the description should still be generated and checked with VLM/CLIP/SigLIP/PAC-S. TRIBE's role is timing and need estimation.

## Next Test

Run all 20 clips for only:

- `P_AV`
- `P_A`
- speech transcript / density

Then create validation sheets and compare top windows against human judgment: should this moment need AD, and is it standard or extended?
"""
    OUT_REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    df = pd.read_csv(NEED_CSV)
    sheets = {int(clip_idx): make_sheet(int(clip_idx), group) for clip_idx, group in df.groupby("clip_idx")}
    write_report(df, sheets)
    for clip_idx, path in sheets.items():
        print(f"clip_{clip_idx:02d}: {path}")
    print(f"report: {OUT_REPORT}")


if __name__ == "__main__":
    main()
