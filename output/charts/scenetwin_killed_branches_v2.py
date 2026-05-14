#!/usr/bin/env python3
"""Failed-branches graphic v2 — serif, paragraph-style, less polished UI,
more like a researcher's notes than a sales deck.

Output:
  output/charts/scenetwin_killed_branches.png
"""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

CHARTS = Path("/Users/adarsha/Knowledge/output/charts")

INK    = "#1a1a1a"
MUTED  = "#5a5a5a"
RULE   = "#9a9a9a"
LINE   = "#d4d2cb"
PAPER  = "#fbfaf6"
ROSE   = "#9c2a47"
WHITE  = "#ffffff"
GOLD   = "#ca8a1c"


def wrap(text, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    return lines


def write_section(ax, x, y, w, *, title, hypothesis, test, failure, lesson):
    """Write one failed-branch section in researcher-notes style."""
    # Title
    ax.text(x, y, title, fontsize=12.5, fontweight="bold", color=INK,
            family="serif", ha="left", va="top")
    # Status pill (small)
    ax.text(x + w - 0.15, y, "DROPPED", fontsize=8, color=ROSE,
            family="serif", fontweight="bold", ha="right", va="top",
            bbox=dict(boxstyle="round,pad=0.25", fc=WHITE, ec=ROSE, lw=0.9))
    cur_y = y - 0.34

    # Rule under title
    ax.plot([x, x + w], [cur_y, cur_y], color=RULE, linewidth=0.8)
    cur_y -= 0.22

    def block(lbl, body, color=INK, width_chars=78):
        nonlocal cur_y
        ax.text(x, cur_y, lbl, fontsize=8.5, color=MUTED,
                family="serif", style="italic", ha="left", va="top")
        cur_y -= 0.22
        for line in wrap(body, width_chars):
            ax.text(x, cur_y, line, fontsize=9.5, color=color,
                    family="serif", ha="left", va="top")
            cur_y -= 0.20
        cur_y -= 0.07

    block("Hypothesis.",  hypothesis)
    block("What we tested.", test)
    block("Why it failed.", failure, color=INK)
    block("Lesson kept.", lesson, color=INK)


# ─────────────────────────────────────────────────────────────────────────
def build():
    sections = [
        (
            "Description Gain (MVRR)",
            "Hypothesis",
            "A good AD should fill the neural gap between audio-only and audiovisual viewing.",
            "Why it failed",
            "Unstable on the two-clip TRIBE smoke test; unrelated AD sometimes beat matching AD."
        ),
        (
            "ROI content typing",
            "Hypothesis",
            "High-gap visual ROIs should reveal what type of content an AD needs to cover.",
            "Why it failed",
            "Glasser ROI typing reached 19.0% agreement versus 16.7% chance against pro AD."
        ),
        (
            "Neural closure",
            "Hypothesis",
            "Adding AD text to audio should move predicted brain response back toward full video.",
            "Why it failed",
            "Closure stayed negative; shorter captions could beat professional AD because language volume dominated."
        ),
        (
            "TRIBE-weighted ADQA",
            "Hypothesis",
            "High TRIBE-gap moments should receive more weight in frame-grounded ADQA.",
            "Why it failed",
            "Null result: Delta rho < 0.002 versus uniform ADQA weighting."
        ),
    ]

    fig = plt.figure(figsize=(17.2, 5.15))
    fig.patch.set_facecolor(PAPER)

    fig.text(0.035, 0.925,
             "What did not survive validation",
             fontsize=20, fontweight="bold", color=GOLD,
             family="serif", ha="left")
    fig.text(0.035, 0.855,
             "Each of these branches looked plausible on a whiteboard. "
             "Each was measured against ground-truth quality tiers or "
             "professional audio description.",
             fontsize=11.2, color=MUTED, family="serif",
             style="italic", ha="left")
    fig.text(0.035, 0.808,
             "Each was dropped before being claimed in the final pipeline.",
             fontsize=11.2, color=MUTED, family="serif",
             style="italic", ha="left")

    ax = fig.add_axes([0.025, 0.08, 0.95, 0.66])
    ax.set_xlim(0, 16.4)
    ax.set_ylim(0, 4.0)
    ax.axis("off")

    card_w = 3.86
    for i, (title, h1, b1, h2, b2) in enumerate(sections):
        x = 0.08 + i * 4.06
        ax.add_patch(FancyBboxPatch(
            (x, 0.05), card_w, 3.72,
            boxstyle="round,pad=0.025,rounding_size=0.06",
            linewidth=0.9, edgecolor=LINE, facecolor=WHITE))
        ax.text(x + 0.18, 3.46, f"{i + 1}.  {title}",
                fontsize=12.2, fontweight="bold", color=INK,
                family="serif", ha="left", va="top")
        ax.text(x + card_w - 0.18, 3.47, "DROPPED",
                fontsize=7.2, color=ROSE, family="serif",
                fontweight="bold", ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.22", fc=WHITE, ec=ROSE, lw=0.8))
        ax.plot([x + 0.18, x + card_w - 0.18], [3.16, 3.16],
                color=RULE, linewidth=0.7)
        y = 2.85
        for heading, body in ((h1, b1), (h2, b2)):
            ax.text(x + 0.18, y, heading + ".",
                    fontsize=8.8, color=MUTED, family="serif",
                    style="italic", ha="left", va="top")
            y -= 0.28
            for line in wrap(body, 42):
                ax.text(x + 0.18, y, line, fontsize=9.6, color=INK,
                        family="serif", ha="left", va="top")
                y -= 0.27
            y -= 0.20

    fig.text(0.035, 0.035,
             "Takeaway: reference-free visual/comprehension scoring survived; direct neural text scoring did not.",
             fontsize=12.0, color=INK, family="serif", fontweight="bold",
             ha="left")

    out = CHARTS / "scenetwin_killed_branches.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    build()
