#!/usr/bin/env python3
"""Aggregate SceneTwin need curves into TRIBE-honest coarse windows.

The raw saved curves have one row per TRIBE output row. On 9-10s clips that looks
like sub-second precision, but fMRI/TRIBE timing is blurred by the hemodynamic
response. This script reports 3s windows so downstream claims do not pretend the
model can localize AD slots to the exact frame.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
NEED_CSV = DG_DIR / "neural_description_need_curve.csv"
EVENT_CSV = DG_DIR / "neural_event_test_results.csv"
OUT_CSV = DG_DIR / "coarse_need_windows.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-coarse-need-windows.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-coarse-need-windows.md"

WINDOW_SECONDS = 3.0


def classify(need: float, speech: float, visual_event: float) -> str:
    if visual_event >= 0.75 and need >= 0.20:
        return "inspect_visual_event"
    if need < 0.45:
        return "low_ad_need"
    if speech < 0.25:
        return "standard_ad_slot"
    if speech < 0.55:
        return "compressed_or_after_dialogue"
    return "extended_or_integrated_ad"


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    values_np = values.to_numpy(dtype=float)
    weights_np = weights.to_numpy(dtype=float)
    if weights_np.sum() <= 1e-9:
        return float(values_np.mean())
    return float(np.dot(values_np, weights_np) / weights_np.sum())


def main() -> None:
    need = pd.read_csv(NEED_CSV)
    events = pd.read_csv(EVENT_CSV)
    df = need.merge(
        events[["clip_idx", "t", "visual_event_score", "visual_event_need"]],
        on=["clip_idx", "t"],
        how="left",
    )
    df["visual_event_score"] = df["visual_event_score"].fillna(0.0)
    df["visual_event_need"] = df["visual_event_need"].fillna(0.0)
    df["critical_weight"] = np.maximum(df["need_score"], df["visual_event_score"])
    df["window_idx"] = np.floor(df["start_s"] / WINDOW_SECONDS).astype(int)

    rows = []
    for (clip_idx, window_idx), group in df.groupby(["clip_idx", "window_idx"]):
        start = float(group["start_s"].min())
        end = float(group["end_s"].max())
        need_score = weighted_mean(group["need_score"], group["critical_weight"])
        speech_density = weighted_mean(group["speech_density"], group["critical_weight"])
        standard_slot_score = weighted_mean(group["standard_slot_score"], group["critical_weight"])
        extended_need_score = weighted_mean(group["extended_need_score"], group["critical_weight"])
        visual_event_score = float(group["visual_event_score"].max())
        visual_event_need = float(group["visual_event_need"].max())
        rows.append(
            {
                "clip_idx": int(clip_idx),
                "window_idx": int(window_idx),
                "start_s": start,
                "end_s": end,
                "need_score": need_score,
                "speech_density": speech_density,
                "standard_slot_score": standard_slot_score,
                "extended_need_score": extended_need_score,
                "visual_event_score": visual_event_score,
                "visual_event_need": visual_event_need,
                "recommendation": classify(need_score, speech_density, visual_event_score),
                "raw_trs": int(len(group)),
            }
        )

    out = pd.DataFrame(rows).sort_values(["clip_idx", "start_s"])
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    top = out.sort_values(["clip_idx", "need_score"], ascending=[True, False]).groupby("clip_idx").head(3)
    report = f"""---
title: "SceneTwin Coarse Need Windows"
category: research
tags: [SceneTwin, TRIBE, timing, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/coarse_need_windows.csv
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin Coarse Need Windows

## Why

The raw TRIBE outputs should not be marketed as frame-exact AD timing. This file aggregates them into `{WINDOW_SECONDS:.1f}s` windows, which is closer to the model's effective temporal resolution.

## Output

{out.to_markdown(index=False)}

## Top Windows Per Clip

{top.to_markdown(index=False)}

## Interpretation

Use these windows for demos, reports, and human validation sheets. Keep raw TR rows for debugging only.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(out)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
