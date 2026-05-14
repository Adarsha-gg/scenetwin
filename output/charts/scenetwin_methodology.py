#!/usr/bin/env python3
"""Visual methodology diagram for the SceneTwin poster.

Six-step pipeline drawn left to right with small icons inside each step,
plus a side-car TRIBE risk forecast lane below. Replaces a long methods
paragraph with a glanceable visual.

Output: output/charts/scenetwin_methodology.png
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle

CHARTS = Path("/Users/adarsha/Knowledge/output/charts")

INK    = "#161a1d"
MUTED  = "#56636d"
LINE   = "#cdd6dc"
WHITE  = "#ffffff"
PAPER  = "#fbfaf6"
TEAL   = "#0d7f83"
BLUE   = "#285a8f"
ROSE   = "#9c2a47"
GOLD   = "#c88a20"
SLATE  = "#26313a"


# ─────────────────────────────────────────────────────────────────────────
# Mini-icons drawn inside each step box
# ─────────────────────────────────────────────────────────────────────────
def icon_input(ax, cx, cy, scale=1.0):
    s = scale
    # Video frame rectangle with play triangle
    ax.add_patch(Rectangle((cx - 0.55 * s, cy - 0.05 * s),
                           1.10 * s, 0.55 * s,
                           facecolor=SLATE, edgecolor=INK, linewidth=1.0))
    tri = np.array([[cx - 0.10 * s, cy + 0.07 * s],
                    [cx - 0.10 * s, cy + 0.43 * s],
                    [cx + 0.18 * s, cy + 0.25 * s]])
    ax.fill(tri[:, 0], tri[:, 1], color=GOLD)
    # AD text line
    ax.add_patch(Rectangle((cx - 0.55 * s, cy - 0.35 * s),
                           1.10 * s, 0.20 * s,
                           facecolor=WHITE, edgecolor=INK, linewidth=1.0))
    for i, dx in enumerate([-0.42, -0.20, 0.02, 0.22, 0.40]):
        ax.plot([cx + dx * s, cx + (dx + 0.13) * s],
                [cy - 0.25 * s, cy - 0.25 * s],
                color=INK, linewidth=1.4)


def icon_frames(ax, cx, cy, scale=1.0):
    s = scale
    # 8 small frame rects
    for i, x in enumerate(np.linspace(-0.55, 0.55, 8)):
        ax.add_patch(Rectangle((cx + x * s - 0.06 * s, cy - 0.25 * s),
                               0.12 * s, 0.50 * s,
                               facecolor=SLATE, edgecolor=INK, linewidth=0.6))


def icon_clip(ax, cx, cy, scale=1.0):
    s = scale
    # Two circles + similarity arrow
    ax.add_patch(Circle((cx - 0.35 * s, cy), 0.18 * s,
                        facecolor=SLATE, edgecolor=INK, linewidth=1.0))
    ax.text(cx - 0.35 * s, cy, "F",
            fontsize=10 * s, color="white", fontweight="bold",
            ha="center", va="center")
    ax.add_patch(Circle((cx + 0.35 * s, cy), 0.18 * s,
                        facecolor=BLUE, edgecolor=INK, linewidth=1.0))
    ax.text(cx + 0.35 * s, cy, "T",
            fontsize=10 * s, color="white", fontweight="bold",
            ha="center", va="center")
    # Sim arrow
    ax.add_patch(FancyArrowPatch((cx - 0.17 * s, cy), (cx + 0.17 * s, cy),
                                 arrowstyle="<->", mutation_scale=10,
                                 color=INK, linewidth=1.2))
    ax.text(cx, cy + 0.32 * s, "cos sim",
            fontsize=8 * s, color=INK, ha="center", va="bottom")


def icon_adqa(ax, cx, cy, scale=1.0):
    s = scale
    # Question bubble + grader bubble
    ax.add_patch(FancyBboxPatch(
        (cx - 0.62 * s, cy - 0.05 * s), 0.55 * s, 0.45 * s,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor=TEAL, edgecolor=INK, linewidth=1.0))
    ax.text(cx - 0.34 * s, cy + 0.18 * s, "Q?",
            fontsize=11 * s, color="white", fontweight="bold",
            ha="center", va="center")
    # Arrow
    ax.add_patch(FancyArrowPatch((cx - 0.04 * s, cy + 0.18 * s),
                                 (cx + 0.10 * s, cy + 0.18 * s),
                                 arrowstyle="-|>", mutation_scale=10,
                                 color=INK, linewidth=1.2))
    # Grade bubble
    ax.add_patch(FancyBboxPatch(
        (cx + 0.12 * s, cy - 0.05 * s), 0.55 * s, 0.45 * s,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        facecolor=WHITE, edgecolor=INK, linewidth=1.0))
    ax.text(cx + 0.40 * s, cy + 0.18 * s, "Y / N",
            fontsize=10 * s, color=INK, fontweight="bold",
            ha="center", va="center")
    # Blind label
    ax.text(cx, cy - 0.22 * s, "blind",
            fontsize=7.5 * s, color=MUTED, style="italic",
            ha="center", va="top")


def icon_ensemble(ax, cx, cy, scale=1.0):
    s = scale
    # Two inputs merging into one
    ax.add_patch(Circle((cx - 0.40 * s, cy + 0.20 * s), 0.14 * s,
                        facecolor=BLUE, edgecolor=INK, linewidth=1.0))
    ax.add_patch(Circle((cx - 0.40 * s, cy - 0.20 * s), 0.14 * s,
                        facecolor=TEAL, edgecolor=INK, linewidth=1.0))
    ax.add_patch(Circle((cx + 0.35 * s, cy), 0.20 * s,
                        facecolor=GOLD, edgecolor=INK, linewidth=1.0))
    ax.add_patch(FancyArrowPatch((cx - 0.26 * s, cy + 0.20 * s),
                                 (cx + 0.15 * s, cy + 0.05 * s),
                                 arrowstyle="-|>", mutation_scale=10,
                                 color=INK, linewidth=1.0))
    ax.add_patch(FancyArrowPatch((cx - 0.26 * s, cy - 0.20 * s),
                                 (cx + 0.15 * s, cy - 0.05 * s),
                                 arrowstyle="-|>", mutation_scale=10,
                                 color=INK, linewidth=1.0))
    ax.text(cx + 0.35 * s, cy, "50/50",
            fontsize=7.5 * s, color="white", fontweight="bold",
            ha="center", va="center")


def icon_score(ax, cx, cy, scale=1.0):
    s = scale
    ax.add_patch(Rectangle((cx - 0.60 * s, cy - 0.30 * s),
                           1.20 * s, 0.65 * s,
                           facecolor=INK, edgecolor=INK, linewidth=1.0))
    ax.text(cx, cy + 0.05 * s, "ρ = 0.929",
            fontsize=12 * s, color="#fdd96b", fontweight="bold",
            ha="center", va="center")
    ax.text(cx, cy - 0.20 * s, "audit score",
            fontsize=7.5 * s, color="white", ha="center", va="center")


def icon_brain(ax, cx, cy, scale=1.0):
    """Small stylised cortex with a heat patch."""
    s = scale
    # Bilateral brain shape: two overlapping ellipses
    from matplotlib.patches import Ellipse
    ax.add_patch(Ellipse((cx - 0.18 * s, cy), 0.55 * s, 0.42 * s,
                         facecolor="#e8e1d4", edgecolor=INK, linewidth=1.0))
    ax.add_patch(Ellipse((cx + 0.18 * s, cy), 0.55 * s, 0.42 * s,
                         facecolor="#e8e1d4", edgecolor=INK, linewidth=1.0))
    # Heat patch (occipital region)
    ax.add_patch(Ellipse((cx - 0.20 * s, cy - 0.08 * s), 0.22 * s, 0.16 * s,
                         facecolor="#ffcd45", edgecolor="none", alpha=0.95))
    ax.add_patch(Ellipse((cx + 0.20 * s, cy - 0.08 * s), 0.22 * s, 0.16 * s,
                         facecolor="#ffcd45", edgecolor="none", alpha=0.95))
    ax.add_patch(Ellipse((cx, cy - 0.10 * s), 0.18 * s, 0.10 * s,
                         facecolor="#f25c4a", edgecolor="none", alpha=0.85))


# ─────────────────────────────────────────────────────────────────────────
def step(ax, x, y, w, h, *, n, title, body, icon_fn, color, label_pos="top"):
    """Render one labelled step box with an icon area."""
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.01,rounding_size=0.10",
        linewidth=1.4, edgecolor=color, facecolor=WHITE))
    # Step number badge
    ax.add_patch(Circle((x + 0.25, y + h - 0.30), 0.20,
                        facecolor=color, edgecolor=color))
    ax.text(x + 0.25, y + h - 0.30, n, fontsize=10,
            color="white", fontweight="bold", ha="center", va="center")
    # Title
    ax.text(x + 0.55, y + h - 0.30, title, fontsize=11.5,
            color=INK, fontweight="bold", ha="left", va="center")
    # Icon area (centered horizontally)
    cx, cy = x + w / 2, y + h * 0.55
    icon_fn(ax, cx, cy, scale=1.0)
    # Body text
    for i, line in enumerate(_wrap(body, 26)):
        ax.text(x + w / 2, y + 0.25 - i * 0.21, line, fontsize=9,
                color=INK, ha="center", va="bottom")


def arrow_between(ax, x1, y, x2, color=INK):
    ax.add_patch(FancyArrowPatch((x1, y), (x2, y),
                                 arrowstyle="-|>", mutation_scale=18,
                                 color=color, linewidth=1.8))


def _wrap(text, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines


def main():
    fig, ax = plt.subplots(figsize=(20.5, 7.6))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(0, 17.3)
    ax.set_ylim(0, 8.4)
    ax.axis("off")

    # Title
    ax.text(0.25, 7.95, "Methodology",
            fontsize=20, fontweight="bold", color=INK,
            ha="left", va="top")
    ax.text(0.25, 7.55,
            "Two reference-free signals run in parallel on each clip and "
            "candidate description. A separate fMRI encoder forecasts "
            "fragile evaluations from video and audio alone.",
            fontsize=10.5, color=MUTED, style="italic",
            ha="left", va="top")

    # ── Main pipeline (top row) ───────────────────────────────────────────
    box_w, box_h = 2.55, 3.10
    y_main = 3.20
    xs = [0.25, 3.10, 5.95, 8.80, 11.65, 14.50]

    step(ax, xs[0], y_main, box_w, box_h, n="1", title="Input",
         body="one clip plus one candidate AD",
         icon_fn=icon_input, color=SLATE)
    step(ax, xs[1], y_main, box_w, box_h, n="2", title="Sample frames",
         body="8 evenly spaced frames",
         icon_fn=icon_frames, color=SLATE)
    step(ax, xs[2], y_main, box_w, box_h, n="3a", title="CLIP grounding",
         body="cosine sim between frames and AD text",
         icon_fn=icon_clip, color=BLUE)
    step(ax, xs[3], y_main, box_w, box_h, n="3b", title="ADQA",
         body="VLM writes Qs, LLM grades blind",
         icon_fn=icon_adqa, color=TEAL)
    step(ax, xs[4], y_main, box_w, box_h, n="4", title="Ensemble",
         body="clip-wise normalize, 50/50 mean",
         icon_fn=icon_ensemble, color=GOLD)
    step(ax, xs[5], y_main, box_w, box_h, n="5", title="Audit score",
         body="returned per (clip, AD) pair",
         icon_fn=icon_score, color=INK)

    # Arrows
    arrow_y = y_main + box_h / 2
    for i in range(5):
        x_start = xs[i] + box_w + 0.03
        x_end = xs[i + 1] - 0.03
        # Branch arrows at step 2 → 3a + 3b
        if i == 1:
            ax.add_patch(FancyArrowPatch(
                (x_start, arrow_y), (x_end, arrow_y + 0.06),
                arrowstyle="-|>", mutation_scale=15, color=BLUE, linewidth=1.6,
                connectionstyle="arc3,rad=0.10"))
            ax.add_patch(FancyArrowPatch(
                (x_start, arrow_y), (x_end, arrow_y - 0.06),
                arrowstyle="-|>", mutation_scale=15, color=TEAL, linewidth=1.6,
                connectionstyle="arc3,rad=-0.10"))
        elif i == 2:
            # 3a → 4 (curve up)
            ax.add_patch(FancyArrowPatch(
                (x_start, arrow_y), (x_end, arrow_y),
                arrowstyle="-|>", mutation_scale=15, color=BLUE, linewidth=1.6))
        elif i == 3:
            ax.add_patch(FancyArrowPatch(
                (x_start, arrow_y), (x_end, arrow_y),
                arrowstyle="-|>", mutation_scale=15, color=TEAL, linewidth=1.6))
        else:
            arrow_between(ax, x_start, arrow_y, x_end, color=INK)

    # ── Side-car: TRIBE risk forecast (bottom row) ────────────────────────
    sc_w, sc_h = 2.55, 2.05
    y_sc = 0.55
    ax.add_patch(FancyBboxPatch(
        (xs[2], y_sc), sc_w, sc_h,
        boxstyle="round,pad=0.01,rounding_size=0.10",
        linewidth=1.4, edgecolor=ROSE, facecolor=WHITE))
    ax.add_patch(Circle((xs[2] + 0.25, y_sc + sc_h - 0.30), 0.20,
                        facecolor=ROSE, edgecolor=ROSE))
    ax.text(xs[2] + 0.25, y_sc + sc_h - 0.30, "6",
            fontsize=10, color="white", fontweight="bold",
            ha="center", va="center")
    ax.text(xs[2] + 0.55, y_sc + sc_h - 0.30,
            "TRIBE encoder", fontsize=11.5, color=INK,
            fontweight="bold", ha="left", va="center")
    icon_brain(ax, xs[2] + sc_w / 2, y_sc + sc_h * 0.55, scale=1.4)
    ax.text(xs[2] + sc_w / 2, y_sc + 0.25,
            "predicts |P_AV − P_A|", fontsize=9,
            color=INK, ha="center", va="bottom")

    # Risk-forecast card
    ax.add_patch(FancyBboxPatch(
        (xs[3] + 0.30, y_sc + 0.15), sc_w, sc_h - 0.30,
        boxstyle="round,pad=0.01,rounding_size=0.10",
        linewidth=1.4, edgecolor=ROSE, facecolor=WHITE))
    ax.text(xs[3] + 0.30 + sc_w / 2, y_sc + sc_h - 0.40,
            "Risk forecast", fontsize=12, fontweight="bold",
            color=ROSE, ha="center")
    ax.text(xs[3] + 0.30 + sc_w / 2, y_sc + sc_h - 0.80,
            "AUC = 1.00", fontsize=18, fontweight="bold",
            color=ROSE, ha="center")
    ax.text(xs[3] + 0.30 + sc_w / 2, y_sc + 0.32,
            "11.1% review budget,\n100% recall on known\nADQA failures",
            fontsize=8.5, color=INK, ha="center")

    # Arrow from TRIBE to Risk-forecast
    arrow_between(ax, xs[2] + sc_w + 0.03, y_sc + sc_h / 2,
                  xs[3] + 0.30 - 0.03, color=ROSE)

    # Light divider between main pipeline and risk-forecast row
    ax.plot([0.25, 16.75], [3.05, 3.05], color=LINE, linewidth=0.8,
            linestyle=":")

    out = CHARTS / "scenetwin_methodology.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
