"""
SceneTwin AccessibilityGap Visualization — 2-clip poster figure.

Shows per-window need_score with speech density overlay and frame thumbnails.
Uses saved TRIBE tensors + gap curve CSV (no GPU needed).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import Normalize
from PIL import Image
import os, textwrap

# ── paths ──────────────────────────────────────────────────────────────────
DG_DIR   = "/Users/adarsha/Knowledge/output/scenetwin_description_gain"
FRAME_DIR = "/Users/adarsha/njbda/vatex_frames"
OUT_PNG  = "/Users/adarsha/Knowledge/output/reports/scenetwin_gap_viz.png"
TEXTS_DIR = os.path.join(DG_DIR, "texts")

df = pd.read_csv(os.path.join(DG_DIR, "neural_description_need_curve.csv"))

COLORS = {
    "standard_ad_slot":          "#e74c3c",
    "extended_or_integrated_ad": "#e67e22",
    "low_ad_need":               "#2ecc71",
}
LABELS = {
    "standard_ad_slot":          "Standard AD slot",
    "extended_or_integrated_ad": "Extended / integrated AD needed",
    "low_ad_need":               "Low visual-audio gap",
}

def load_frames(clip_idx, n_windows):
    """Load one frame per time window (or None if missing)."""
    folder = os.path.join(FRAME_DIR, f"clip_{clip_idx:02d}")
    frames = []
    for i in range(n_windows):
        path = os.path.join(folder, f"frame_{i+1:03d}.jpg")
        if os.path.exists(path):
            frames.append(np.array(Image.open(path)))
        else:
            frames.append(None)
    return frames

def read_desc(clip_idx, tier):
    path = os.path.join(TEXTS_DIR, f"clip_{clip_idx:02d}_{tier}.txt")
    if os.path.exists(path):
        return open(path).read().strip()
    return ""

# ── figure layout ──────────────────────────────────────────────────────────
# Two clips stacked vertically; each clip block has:
#   row 0: video frames (small thumbnails)
#   row 1: gap bar chart with speech density overlay
#   row 2: VA11y description text

fig = plt.figure(figsize=(18, 11))
fig.patch.set_facecolor("#0f1117")

outer = gridspec.GridSpec(2, 1, figure=fig, hspace=0.35)

clip_meta = {
    0: {"label": "Clip 00 — Kitchen tomato throw (Food & Cooking)", "n_frames": 9},
    1: {"label": "Clip 01 — Burger King eating challenge (Food & Cooking)", "n_frames": 10},
}

for ci, (clip_idx, meta) in enumerate(clip_meta.items()):
    sub = df[df.clip_idx == clip_idx].reset_index(drop=True)
    n = len(sub)
    frames = load_frames(clip_idx, meta["n_frames"])

    inner = gridspec.GridSpecFromSubplotSpec(
        3, n,
        subplot_spec=outer[ci],
        height_ratios=[1.8, 2.5, 0.7],
        hspace=0.05, wspace=0.04,
    )

    # ── row 0: frame thumbnails ────────────────────────────────────────────
    for t in range(n):
        ax = fig.add_subplot(inner[0, t])
        ax.set_facecolor("#0f1117")
        ax.set_xticks([]); ax.set_yticks([])

        frame = frames[t] if t < len(frames) else None
        if frame is not None:
            ax.imshow(frame, aspect="auto")
        else:
            ax.text(0.5, 0.5, "—", ha="center", va="center",
                    color="#555", fontsize=10, transform=ax.transAxes)

        # highlight high-need frames with a colored border
        rec = sub.loc[t, "recommendation"]
        color = COLORS[rec]
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(2.5 if rec != "low_ad_need" else 0.5)

        if t == 0:
            ax.set_ylabel(meta["label"], color="white", fontsize=7.5,
                          rotation=90, labelpad=4, va="center")

    # ── row 1: gap bar chart ───────────────────────────────────────────────
    ax_bar = fig.add_subplot(inner[1, :])
    ax_bar.set_facecolor("#1a1d27")

    xs = np.arange(n)
    bar_colors = [COLORS[sub.loc[t, "recommendation"]] for t in range(n)]
    bars = ax_bar.bar(xs, sub["need_score"], color=bar_colors, width=0.75,
                      zorder=3, alpha=0.9)

    # speech density as step line
    ax_sp = ax_bar.twinx()
    ax_sp.step(xs - 0.5, sub["speech_density"], where="post",
               color="#a0c4ff", linewidth=1.5, alpha=0.7, zorder=4)
    ax_sp.fill_between(xs, sub["speech_density"], step="mid",
                       color="#a0c4ff", alpha=0.12)
    ax_sp.set_ylim(0, 1.7)
    ax_sp.set_ylabel("Speech\ndensity", color="#a0c4ff", fontsize=7.5,
                     labelpad=2)
    ax_sp.tick_params(axis="y", colors="#a0c4ff", labelsize=7)
    ax_sp.spines["right"].set_color("#a0c4ff")
    ax_sp.spines["right"].set_alpha(0.4)

    ax_bar.set_ylim(0, 1.15)
    ax_bar.set_xlim(-0.5, n - 0.5)
    ax_bar.set_xticks(xs)
    labels_x = [f"{sub.loc[t,'start_s']:.1f}s" for t in range(n)]
    ax_bar.set_xticklabels(labels_x, color="white", fontsize=7.5)
    ax_bar.set_ylabel("AccessibilityGap\nneed_score", color="white", fontsize=8)
    ax_bar.tick_params(axis="y", colors="white", labelsize=7.5)
    ax_bar.spines["bottom"].set_color("#444")
    ax_bar.spines["left"].set_color("#444")
    ax_bar.spines["top"].set_visible(False)
    ax_bar.spines["right"].set_visible(False)
    ax_bar.yaxis.grid(True, color="#333", linewidth=0.5, zorder=0)
    ax_bar.set_facecolor("#1a1d27")

    # annotate high-need bars
    for t in range(n):
        rec = sub.loc[t, "recommendation"]
        if rec in ("standard_ad_slot", "extended_or_integrated_ad"):
            score = sub.loc[t, "need_score"]
            tag = "AD slot" if rec == "standard_ad_slot" else "Extended AD"
            ax_bar.text(t, score + 0.03, tag, ha="center", va="bottom",
                        color=COLORS[rec], fontsize=6.5, fontweight="bold")

    # ── row 2: description text ────────────────────────────────────────────
    ax_txt = fig.add_subplot(inner[2, :])
    ax_txt.set_facecolor("#0f1117")
    ax_txt.axis("off")
    desc = read_desc(clip_idx, "tier3_va11y")
    wrapped = textwrap.fill(f"VideoA11y AD: {desc}", width=140)
    ax_txt.text(0.01, 0.5, wrapped, transform=ax_txt.transAxes,
                color="#ccc", fontsize=7, va="center", wrap=True,
                style="italic")

# ── legend ─────────────────────────────────────────────────────────────────
legend_patches = [
    mpatches.Patch(color=COLORS[k], label=LABELS[k])
    for k in ("standard_ad_slot", "extended_or_integrated_ad", "low_ad_need")
]
legend_patches.append(
    mpatches.Patch(color="#a0c4ff", alpha=0.7, label="Speech density (0–1)")
)
fig.legend(handles=legend_patches, loc="lower center", ncol=4,
           frameon=True, facecolor="#1a1d27", edgecolor="#444",
           labelcolor="white", fontsize=8.5,
           bbox_to_anchor=(0.5, 0.01))

# ── title ──────────────────────────────────────────────────────────────────
fig.suptitle(
    "SceneTwin: Neural AccessibilityGap — When Does a BLV Viewer Need a Description?",
    color="white", fontsize=13, fontweight="bold", y=0.98,
)

fig.text(0.5, 0.95,
    "AccessibilityGap(t) = distance(P_AV[t], P_A[t])  ·  TRIBE v2 on 2 clips (L4 GPU)\n"
    "Red/orange windows = high visual–audio divergence → prime AD placement targets",
    ha="center", color="#aaa", fontsize=8)

plt.savefig(OUT_PNG, dpi=160, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"Saved → {OUT_PNG}")
plt.close()
