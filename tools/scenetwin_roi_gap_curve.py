#!/usr/bin/env python3
"""ROI-restricted SceneTwin gap curves.

This is deliberately mask-driven. We do not fake anatomical ROIs from arbitrary
vertex ranges; pass a CSV/NPY mask that maps fsaverage5 vertices to ROI names.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
PRED_DIR = DG_DIR / "preds"
OUT_CSV = DG_DIR / "roi_gap_curve.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-roi-gap-curve.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-roi-gap-curve.md"


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom <= 1e-9:
        return float("nan")
    return float(np.dot(a, b) / denom)


def minmax(values: np.ndarray) -> np.ndarray:
    lo = np.nanmin(values)
    hi = np.nanmax(values)
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return np.zeros_like(values, dtype=float)
    return (values - lo) / (hi - lo)


def load_mask(path: Path) -> dict[str, np.ndarray]:
    if path.suffix == ".npy":
        data = np.load(path, allow_pickle=True)
        if isinstance(data.item() if data.shape == () else None, dict):
            raw = data.item()
            return {str(k): np.asarray(v, dtype=bool) for k, v in raw.items()}
        raise ValueError("NPY mask must be a dict: {roi_name: bool mask or index array}")

    df = pd.read_csv(path)
    if {"roi", "vertex"}.issubset(df.columns):
        n_vertices = int(df["vertex"].max()) + 1
        out = {}
        for roi, group in df.groupby("roi"):
            mask = np.zeros(n_vertices, dtype=bool)
            mask[group["vertex"].to_numpy(dtype=int)] = True
            out[str(roi)] = mask
        return out
    if {"vertex", "roi_name"}.issubset(df.columns):
        renamed = df.rename(columns={"roi_name": "roi"})
        n_vertices = int(renamed["vertex"].max()) + 1
        out = {}
        for roi, group in renamed.groupby("roi"):
            mask = np.zeros(n_vertices, dtype=bool)
            mask[group["vertex"].to_numpy(dtype=int)] = True
            out[str(roi)] = mask
        return out
    raise ValueError("CSV mask must have columns roi,vertex")


def available_clip_indices() -> list[int]:
    clips = []
    for p_av in sorted(PRED_DIR.glob("clip_*_P_AV.npy")):
        clip_idx = int(p_av.name.split("_")[1])
        if (PRED_DIR / f"clip_{clip_idx:02d}_P_A.npy").exists():
            clips.append(clip_idx)
    return clips


def compute(mask_path: Path) -> pd.DataFrame:
    masks = load_mask(mask_path)
    rows = []
    for clip_idx in available_clip_indices():
        av = np.load(PRED_DIR / f"clip_{clip_idx:02d}_P_AV.npy")
        audio = np.load(PRED_DIR / f"clip_{clip_idx:02d}_P_A.npy")
        if av.shape != audio.shape:
            raise ValueError(f"shape mismatch for clip_{clip_idx:02d}")
        n_vertices = av.shape[1]
        for roi, mask in masks.items():
            if mask.dtype != bool:
                bool_mask = np.zeros(n_vertices, dtype=bool)
                bool_mask[np.asarray(mask, dtype=int)] = True
                mask = bool_mask
            if len(mask) != n_vertices:
                raise ValueError(f"ROI {roi} mask length {len(mask)} != tensor vertices {n_vertices}")
            if mask.sum() == 0:
                continue
            residual = np.linalg.norm(av[:, mask] - audio[:, mask], axis=1) / np.sqrt(mask.sum())
            cosine_gap = np.array([1.0 - cosine(av[t, mask], audio[t, mask]) for t in range(len(av))])
            score = 0.5 * minmax(residual) + 0.5 * minmax(cosine_gap)
            for t in range(len(av)):
                rows.append(
                    {
                        "clip_idx": clip_idx,
                        "roi": roi,
                        "t": t,
                        "n_vertices": int(mask.sum()),
                        "residual_norm": float(residual[t]),
                        "cosine_gap": float(cosine_gap[t]),
                        "roi_need_score": float(score[t]),
                    }
                )
    return pd.DataFrame(rows)


def write_blocked_report(mask_path: Path | None) -> None:
    msg = "No ROI mask was provided." if mask_path is None else f"ROI mask not found: `{mask_path}`."
    report = f"""---
title: "SceneTwin ROI Gap Curve"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5]
created: 2026-05-03
updated: 2026-05-03
---

# SceneTwin ROI Gap Curve

## Status

Blocked: {msg}

This script is implemented, but it intentionally requires a real fsaverage5 ROI mask. We should not use fake vertex slices as FFA/PPA/MT+.

## Accepted Mask Formats

- CSV with columns `roi,vertex`
- NPY containing a Python dict `{{roi_name: mask_or_indices}}`

Run:

```bash
python tools/scenetwin_roi_gap_curve.py --mask path/to/fsaverage5_roi_mask.csv
```
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mask", type=Path, help="CSV/NPY fsaverage5 ROI mask")
    args = parser.parse_args()
    if args.mask is None or not args.mask.exists():
        write_blocked_report(args.mask)
        return

    out = compute(args.mask)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    summary = (
        out.groupby(["clip_idx", "roi"])
        .agg(mean_need=("roi_need_score", "mean"), max_need=("roi_need_score", "max"), n_vertices=("n_vertices", "first"))
        .reset_index()
    )
    report = f"""---
title: "SceneTwin ROI Gap Curve"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_gap_curve.csv
---

# SceneTwin ROI Gap Curve

## Summary

{summary.to_markdown(index=False)}

## Verdict

ROI-restricted gap curves are now available from the provided mask. Compare these against whole-cortex need curves before using them as the headline signal.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(summary)
    print(f"Wrote {OUT_CSV}")


if __name__ == "__main__":
    main()
