#!/usr/bin/env python3
"""SceneTwin poster brain visuals.

Pial surface, lateral view of both hemispheres, white background,
truncated-hot colormap. No anatomical labels (the user adds those by hand
on the poster).

Outputs:
  output/charts/scenetwin_accessibility_gap_brain_annotated.png
  output/charts/scenetwin_brain_three_panel.png
"""
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, ListedColormap
from nilearn import datasets, surface

ROOT = Path("/Users/adarsha/Knowledge")
PREDS = ROOT / "output" / "visual_closure_preds"
OUT_DIR = ROOT / "output" / "charts"
N_HEMI = 10242

INK   = "#161a1d"
MUTED = "#56636d"
BG    = "#ffffff"

_hot = plt.get_cmap("hot")(np.linspace(0.30, 1.0, 256))
CMAP = ListedColormap(_hot, name="hot_trunc")


def find_clip_ids() -> list[str]:
    ids = set()
    for p in PREDS.glob("clip_*_P_AV.npy"):
        m = re.match(r"clip_(\d+)_P_AV\.npy", p.name)
        if m and (PREDS / f"clip_{m.group(1)}_P_A.npy").exists():
            ids.add(m.group(1))
    return sorted(ids)


def stack(suffix: str) -> np.ndarray:
    return np.stack([np.load(PREDS / f"clip_{c}_{suffix}.npy").mean(0)
                     for c in find_clip_ids()])


def load_meshes(kind="pial"):
    fsavg = datasets.fetch_surf_fsaverage(mesh="fsaverage5")
    l = fsavg.pial_left if kind == "pial" else fsavg.infl_left
    r = fsavg.pial_right if kind == "pial" else fsavg.infl_right
    v_l, f_l = surface.load_surf_mesh(l)
    v_r, f_r = surface.load_surf_mesh(r)
    sulc_l = surface.load_surf_data(fsavg.sulc_left)
    sulc_r = surface.load_surf_data(fsavg.sulc_right)
    return v_l, f_l, v_r, f_r, sulc_l, sulc_r


def plot_one_hemi(ax, verts, faces, vals, sulc, *, cmap, vmin, vmax,
                  threshold, side):
    cm = plt.get_cmap(cmap)
    norm = Normalize(vmin=vmin, vmax=vmax)
    face_v = vals[faces].mean(1)
    face_s = sulc[faces].mean(1)
    s_norm = (face_s - face_s.min()) / (np.ptp(face_s) + 1e-9)
    light = 0.82 - 0.20 * s_norm   # 0.62 (sulci) to 0.82 (gyri)
    bg = np.zeros((len(faces), 4))
    bg[:, :3] = light[:, None]
    bg[:, 3] = 1.0
    mask = face_v >= threshold
    fg = cm(norm(face_v))
    out = bg.copy()
    out[mask] = fg[mask]
    tri = ax.plot_trisurf(verts[:, 0], verts[:, 1], verts[:, 2],
                          triangles=faces, linewidth=0, antialiased=True,
                          shade=False)
    tri.set_facecolors(out)
    ax.view_init(elev=0, azim=180 if side == "left" else 0)
    ax.set_axis_off()
    ax.set_box_aspect((1, 1, 1))
    ax.set_facecolor(BG)
    pad = 4
    ax.set_xlim(verts[:, 0].min() - pad, verts[:, 0].max() + pad)
    ax.set_ylim(verts[:, 1].min() - pad, verts[:, 1].max() + pad)
    ax.set_zlim(verts[:, 2].min() - pad, verts[:, 2].max() + pad)


# ─────────────────────────────────────────────────────────────────────────
# Accessibility gap brain, lateral L + R, no labels
# ─────────────────────────────────────────────────────────────────────────
def render_main_brain():
    p_av = stack("P_AV")
    p_a = stack("P_A")
    gap = np.abs(p_av - p_a).mean(0)
    v_l, f_l, v_r, f_r, sulc_l, sulc_r = load_meshes("pial")

    vmax = float(np.percentile(gap[gap > 0], 98))
    thresh = float(np.percentile(gap, 60))

    fig = plt.figure(figsize=(13, 7))
    fig.patch.set_facecolor(BG)

    ax_l = fig.add_axes([0.02, 0.04, 0.43, 0.82], projection="3d")
    ax_r = fig.add_axes([0.46, 0.04, 0.43, 0.82], projection="3d")
    plot_one_hemi(ax_l, v_l, f_l, gap[:N_HEMI], sulc_l,
                  cmap=CMAP, vmin=thresh, vmax=vmax, threshold=thresh,
                  side="left")
    plot_one_hemi(ax_r, v_r, f_r, gap[N_HEMI:], sulc_r,
                  cmap=CMAP, vmin=thresh, vmax=vmax, threshold=thresh,
                  side="right")

    fig.text(0.45, 0.95,
             "Average accessibility gap across 20 clips",
             ha="center", fontsize=16, fontweight="bold", color=INK)
    fig.text(0.45, 0.915,
             "TRIBE average gap   |P_AV − P_A|   across audiovisual vs audio-only viewing",
             ha="center", fontsize=10.5, color=MUTED, style="italic")

    fig.text(0.235, 0.045, "Left hemisphere — lateral",
             ha="center", fontsize=10, color=MUTED)
    fig.text(0.675, 0.045, "Right hemisphere — lateral",
             ha="center", fontsize=10, color=MUTED)

    cbar_ax = fig.add_axes([0.92, 0.20, 0.018, 0.55])
    sm = plt.cm.ScalarMappable(cmap=CMAP, norm=Normalize(thresh, vmax))
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Accessibility gap |P_AV − P_A|", fontsize=10, color=INK)

    out = OUT_DIR / "scenetwin_accessibility_gap_brain_annotated.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  wrote {out}")


# ─────────────────────────────────────────────────────────────────────────
# Three-panel pedagogy strip (P_AV / P_A / gap)
# ─────────────────────────────────────────────────────────────────────────
def render_three_panel():
    p_av = stack("P_AV")
    p_a = stack("P_A")
    av_strength = np.abs(p_av).mean(0)
    a_strength = np.abs(p_a).mean(0)
    gap = np.abs(p_av - p_a).mean(0)
    v_l, f_l, v_r, f_r, sulc_l, sulc_r = load_meshes("pial")

    v_av_a = float(np.percentile(np.concatenate([av_strength, a_strength]), 98))
    v_gap = float(np.percentile(gap[gap > 0], 98))
    th_av_a = float(np.percentile(np.concatenate([av_strength, a_strength]), 55))
    th_gap = float(np.percentile(gap, 60))

    fig = plt.figure(figsize=(16, 6.5))
    fig.patch.set_facecolor(BG)

    panels = [
        (av_strength, "Audiovisual viewing  (P_AV)",
         "Predicted brain activation when full video + audio are present.",
         th_av_a, v_av_a),
        (a_strength, "Audio only  (P_A)",
         "Predicted activation when only audio is heard.",
         th_av_a, v_av_a),
        (gap, "Gap  |P_AV − P_A|",
         "Where audiovisual viewing activates the brain more than audio alone.",
         th_gap, v_gap),
    ]
    for i, (vals, title, sub, th, vmx) in enumerate(panels):
        x0 = 0.02 + i * 0.327
        rect = [x0, 0.18, 0.31, 0.62]
        ax = fig.add_axes(rect, projection="3d")
        plot_one_hemi(ax, v_l, f_l, vals[:N_HEMI], sulc_l,
                      cmap=CMAP, vmin=th, vmax=vmx, threshold=th,
                      side="left")
        fig.text(x0 + 0.155, 0.85, title, ha="center", fontsize=13,
                 fontweight="bold", color=INK)
        fig.text(x0 + 0.155, 0.13, sub, ha="center", va="top",
                 fontsize=9.5, color=MUTED, style="italic", wrap=True)

    fig.text(0.347, 0.50, "−", fontsize=48, ha="center", va="center",
             color=INK, fontweight="bold")
    fig.text(0.673, 0.50, "=", fontsize=48, ha="center", va="center",
             color=INK, fontweight="bold")

    fig.text(0.5, 0.95, "How the TRIBE accessibility gap is built",
             ha="center", fontsize=15, fontweight="bold", color=INK)

    out = OUT_DIR / "scenetwin_brain_three_panel.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"  wrote {out}")


def main():
    print("[1/2] brain — lateral L + R, white bg, no labels")
    render_main_brain()
    print("[2/2] 3-panel pedagogy strip")
    render_three_panel()
    print("Done.")


if __name__ == "__main__":
    main()
