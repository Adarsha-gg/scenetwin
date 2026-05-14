#!/usr/bin/env python3
"""Analyze whether ROI-restricted gap curves improve SceneTwin timing."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
ROI_CSV = DG_DIR / "roi_gap_curve.csv"
NEED_CSV = DG_DIR / "neural_description_need_curve.csv"
OUT_CSV = DG_DIR / "roi_gap_analysis.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-roi-gap-analysis.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-roi-gap-analysis.md"

VISUAL_ROIS = {
    "early_visual_v1_proxy",
    "occipital_visual_proxy",
    "ventral_visual_ffa_proxy",
    "scene_context_ppa_proxy",
    "retrosplenial_precuneus_proxy",
    "lateral_object_loc_proxy",
    "motion_mt_proxy",
    "body_eba_proxy",
}
CONTROL_ROIS = {"language_control", "auditory_control"}


def top_windows(group: pd.DataFrame, score_col: str, n: int = 3) -> str:
    top = group.sort_values(score_col, ascending=False).head(n)
    return "; ".join(
        f"t{int(r.t)} {r.start_s:.1f}-{r.end_s:.1f}s {score_col}={getattr(r, score_col):.2f} whole={r.need_score:.2f}"
        for r in top.itertuples(index=False)
    )


def main() -> None:
    roi = pd.read_csv(ROI_CSV)
    need = pd.read_csv(NEED_CSV)
    df = roi.merge(
        need[["clip_idx", "t", "start_s", "end_s", "need_score", "speech_density", "recommendation"]],
        on=["clip_idx", "t"],
        how="left",
    )
    rows = []
    for (clip_idx, roi_name), group in df.groupby(["clip_idx", "roi"]):
        corr = float(np.corrcoef(group["roi_need_score"], group["need_score"])[0, 1])
        top_roi = set(group.sort_values("roi_need_score", ascending=False).head(3)["t"].astype(int))
        top_whole = set(group.sort_values("need_score", ascending=False).head(3)["t"].astype(int))
        overlap = len(top_roi & top_whole) / 3.0
        rows.append(
            {
                "clip_idx": int(clip_idx),
                "roi": roi_name,
                "roi_type": "visual_proxy" if roi_name in VISUAL_ROIS else "control",
                "mean_roi_need": float(group["roi_need_score"].mean()),
                "max_roi_need": float(group["roi_need_score"].max()),
                "corr_with_whole_need": corr,
                "top3_overlap_with_whole": overlap,
                "peak_sharpness": float(group["roi_need_score"].max() - group["roi_need_score"].median()),
                "top_roi_windows": top_windows(group, "roi_need_score"),
            }
        )

    out = pd.DataFrame(rows).sort_values(["clip_idx", "roi_type", "max_roi_need"], ascending=[True, False, False])
    summary = (
        out.groupby(["clip_idx", "roi_type"])
        .agg(
            mean_corr=("corr_with_whole_need", "mean"),
            mean_top3_overlap=("top3_overlap_with_whole", "mean"),
            mean_peak_sharpness=("peak_sharpness", "mean"),
            max_roi_need=("max_roi_need", "max"),
        )
        .reset_index()
    )
    top_by_clip = out.sort_values(["clip_idx", "max_roi_need"], ascending=[True, False]).groupby("clip_idx").head(6)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)

    report = f"""---
title: "SceneTwin ROI Gap Analysis"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5, Destrieux]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_gap_analysis.csv
  - output/scenetwin_description_gain/roi_gap_curve.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
---

# SceneTwin ROI Gap Analysis

## Question

Do anatomical proxy ROIs give a cleaner TRIBE accessibility-gap signal than the whole-cortex curve?

## Summary

{summary.to_markdown(index=False)}

## Top ROIs By Clip

{top_by_clip[["clip_idx", "roi", "roi_type", "mean_roi_need", "max_roi_need", "corr_with_whole_need", "top3_overlap_with_whole", "peak_sharpness", "top_roi_windows"]].to_markdown(index=False)}

## Verdict

The ROI experiment is unblocked, but the Destrieux proxy atlas is not clean enough to become the headline.

- Clip 00 looks promising: visual/scene proxies peak on the silent tomato/knife action windows.
- Clip 01 is mixed: title-card / speech-heavy regions also drive language and auditory controls.
- Controls can score high, so the current anatomical proxy masks do not prove a uniquely visual cortical gap.

Keep the ROI pipeline, but do not overclaim it until we replace proxy masks with a functional atlas/localizer mask.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
