#!/usr/bin/env python3
"""Render the TRIBE accessibility-gap heatmap on the fsaverage5 cortical surface.

Gap(vertex) = mean_t |P_AV[t] - P_A[t]|

Averaged across all clips that have both P_AV and P_A cached, then projected
to fsaverage5 (10242 verts/hemi). Produces 4-view (lateral/medial × L/R)
brain figure for the poster.

Inputs:  output/visual_closure_preds/clip_*_P_AV.npy, clip_*_P_A.npy
Outputs: output/charts/scenetwin_accessibility_gap_brain.png
         output/charts/scenetwin_accessibility_gap_brain_visual_roi.png
         output/charts/scenetwin_accessibility_gap_brain.csv (per-vertex gap)
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from nilearn import datasets, plotting, surface  # noqa: F401

ROOT = Path("/Users/adarsha/Knowledge")
PREDS = ROOT / "output" / "visual_closure_preds"
OUT_DIR = ROOT / "output" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)
MASK_CSV = ROOT / "output" / "colab_upload_closure" / "glasser_roi_mask.csv"

N_VERTS_HEMI = 10242  # fsaverage5

VIS_ROIS = {"object_motion", "scene_spatial", "early_visual",
            "lateral_object_loc", "scene_ppa", "motion_mt"}


def find_clip_ids() -> list[str]:
    ids = set()
    for p in PREDS.glob("clip_*_P_AV.npy"):
        m = re.match(r"clip_(\d+)_P_AV\.npy", p.name)
        if m and (PREDS / f"clip_{m.group(1)}_P_A.npy").exists():
            ids.add(m.group(1))
    return sorted(ids)


def per_vertex_gap(clip_id: str) -> np.ndarray:
    p_av = np.load(PREDS / f"clip_{clip_id}_P_AV.npy")
    p_a = np.load(PREDS / f"clip_{clip_id}_P_A.npy")
    n = min(p_av.shape[0], p_a.shape[0])
    return np.abs(p_av[:n] - p_a[:n]).mean(0)


def render_surface(gap_full: np.ndarray, title: str, outpath: Path,
                   threshold: float | None = None) -> None:
    """4-panel cortical surface plot: lateral + medial × L + R."""
    fsavg = datasets.fetch_surf_fsaverage(mesh="fsaverage5")
    gap_lh = gap_full[:N_VERTS_HEMI]
    gap_rh = gap_full[N_VERTS_HEMI:]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5),
                             subplot_kw={"projection": "3d"})
    fig.suptitle(title, fontsize=15, fontweight="bold", y=0.995)

    panels = [
        (axes[0, 0], fsavg.infl_left,  gap_lh, "lateral", "left",
         fsavg.sulc_left,  "Left hemisphere — lateral"),
        (axes[0, 1], fsavg.infl_right, gap_rh, "lateral", "right",
         fsavg.sulc_right, "Right hemisphere — lateral"),
        (axes[1, 0], fsavg.infl_left,  gap_lh, "medial", "left",
         fsavg.sulc_left,  "Left hemisphere — medial"),
        (axes[1, 1], fsavg.infl_right, gap_rh, "medial", "right",
         fsavg.sulc_right, "Right hemisphere — medial"),
    ]
    vmax = float(np.percentile(gap_full[gap_full > 0], 98)) if (gap_full > 0).any() else 1.0
    for ax, mesh, vals, view, hemi, bg, label in panels:
        plotting.plot_surf_stat_map(
            mesh, vals, hemi=hemi, view=view, bg_map=bg, bg_on_data=True,
            colorbar=False, axes=ax, figure=fig, cmap="hot",
            threshold=threshold, vmax=vmax, darkness=0.55,
        )
        ax.set_title(label, fontsize=11)

    # Shared colorbar
    cbar_ax = fig.add_axes([0.92, 0.20, 0.015, 0.60])
    norm = plt.Normalize(vmin=threshold or 0, vmax=vmax)
    sm = plt.cm.ScalarMappable(cmap="hot", norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Accessibility gap   |P_AV − P_A|", fontsize=10)

    plt.subplots_adjust(left=0.02, right=0.90, top=0.94, bottom=0.05,
                        wspace=0.02, hspace=0.0)
    fig.savefig(outpath, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {outpath}")


def main():
    clip_ids = find_clip_ids()
    print(f"Computing gap across {len(clip_ids)} clips: {clip_ids}")
    gaps = np.stack([per_vertex_gap(c) for c in clip_ids])
    print(f"  gaps shape: {gaps.shape}  (clips × verts)")
    mean_gap = gaps.mean(0)
    print(f"  mean_gap range: [{mean_gap.min():.3f}, {mean_gap.max():.3f}]")
    print(f"  mean: {mean_gap.mean():.3f}  median: {np.median(mean_gap):.3f}")

    pd.DataFrame({"vertex": np.arange(len(mean_gap)),
                  "mean_gap": mean_gap}).to_csv(
        OUT_DIR / "scenetwin_accessibility_gap_brain.csv", index=False)

    # Full-cortex render
    render_surface(
        mean_gap,
        f"TRIBE accessibility gap  |P_AV − P_A|   (mean of {len(clip_ids)} clips)",
        OUT_DIR / "scenetwin_accessibility_gap_brain.png",
        threshold=float(np.percentile(mean_gap, 60)),
    )

    # Visual-ROI-only render: zero out non-visual verts so they go to background
    df = pd.read_csv(MASK_CSV)
    vis_verts = df[df["roi"].isin(VIS_ROIS)]["vertex"].astype(int).values
    print(f"\nVisual ROI verts: {len(vis_verts)}")
    gap_vis = np.zeros_like(mean_gap)
    gap_vis[vis_verts] = mean_gap[vis_verts]
    render_surface(
        gap_vis,
        f"TRIBE accessibility gap — visual ROIs only  ({len(clip_ids)} clips)",
        OUT_DIR / "scenetwin_accessibility_gap_brain_visual_roi.png",
        threshold=float(np.percentile(mean_gap[vis_verts], 30)),
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
