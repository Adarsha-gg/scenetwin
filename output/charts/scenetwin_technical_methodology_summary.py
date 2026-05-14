#!/usr/bin/env python3
"""Poster-ready technical methodology summary.

Condenses output/reports/scenetwin-technical-methodology.md into a single
wide PNG that can replace the length-bias chart on the poster.

Output: output/charts/scenetwin_technical_methodology_summary.png
"""
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path("/Users/adarsha/Knowledge")
CHARTS = ROOT / "output" / "charts"

INK = "#161a1d"
MUTED = "#56636d"
LINE = "#cfd8de"
PAPER = "#fbfaf6"
WHITE = "#ffffff"
TEAL = "#0d7f83"
GOLD = "#ca8a1c"
BLUE = "#285a8f"
ROSE = "#9c2a47"
SLATE = "#26313a"


def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        candidate = (cur + " " + word).strip()
        if len(candidate) > width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = candidate
    if cur:
        lines.append(cur)
    return lines


def card(ax, x, y, w, h, title, color, rows):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.015,rounding_size=0.08",
        linewidth=1.0, edgecolor=LINE, facecolor=WHITE))
    ax.add_patch(Rectangle((x, y + h - 0.55), w, 0.55,
                           facecolor=color, edgecolor="none"))
    ax.text(x + 0.22, y + h - 0.28, title, fontsize=12.5,
            color=WHITE, fontweight="bold", ha="left", va="center")
    yy = y + h - 0.86
    for label, body in rows:
        ax.text(x + 0.22, yy, label, fontsize=9.4, color=INK,
                fontweight="bold", ha="left", va="top")
        yy -= 0.24
        for line in wrap(body, 45):
            ax.text(x + 0.22, yy, line, fontsize=8.3, color=MUTED,
                    ha="left", va="top")
            yy -= 0.205
        yy -= 0.12


def main():
    fig, ax = plt.subplots(figsize=(18.4, 6.25))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(0, 18.4)
    ax.set_ylim(0, 6.25)
    ax.axis("off")

    ax.text(0.35, 5.92, "Technical methodology",
            fontsize=21, fontweight="bold", color=GOLD,
            ha="left", va="top")
    ax.text(0.35, 5.50,
            "How the headline score was built: dataset, tiers, reference-free signals, validation, and TRIBE risk forecast.",
            fontsize=10.2, color=MUTED, style="italic",
            ha="left", va="top")

    cards = [
        (
            "Data and tiers",
            SLATE,
            [
                ("20 clips, 18 complete", "Short VideoA11y/VATEX clips across Food, Sports, Pets, and Travel. Primary metrics use 18 clips with complete four-tier rows."),
                ("Four candidates per clip", "Tier 3 professional AD, tier 2 VATEX long caption, tier 1 VATEX short caption, tier 0 cross-category wrong-scene AD."),
                ("Ground truth rank", "Tier 0 = 0, tier 1 = 1, tier 2 = 2, tier 3 = 3. Evaluation is within-clip tier ordering."),
            ],
        ),
        (
            "Reference-free scoring",
            TEAL,
            [
                ("Signal 1: CLIP", "Eight evenly spaced frames are embedded with CLIP ViT-L/14 and compared with the candidate AD text by cosine similarity."),
                ("Signal 2: frame-grounded ADQA", "GPT-4o writes visual comprehension questions from frames. Claude grades the candidate AD blind, seeing no frames or tier labels."),
                ("Fixed ensemble", "Both signals are min-max normalized within clip, then averaged 50/50. No learned weights or reference script are used."),
            ],
        ),
        (
            "Validation and risk",
            BLUE,
            [
                ("Primary statistics", "Spearman rho = 0.929 across 72 clip-tier pairs; bootstrap 95 percent CI [0.904, 0.957]; permutation p < 0.0005."),
                ("Ordering checks", "54/54 pairwise tier wins and 15/18 clips fully ordered. Length-only baseline reaches only rho = 0.318."),
                ("TRIBE side analysis", "TRIBE v2 predicts |P_AV - P_A| from video/audio alone. Its risk feature gives ROC-AUC = 1.00 for known ADQA full-order failures."),
            ],
        ),
    ]

    x0, gap, w, h, y = 0.35, 0.32, 5.70, 4.58, 0.66
    for i, (title, color, rows) in enumerate(cards):
        card(ax, x0 + i * (w + gap), y, w, h, title, color, rows)

    ax.text(0.35, 0.25,
            "Source: output/reports/scenetwin-technical-methodology.md",
            fontsize=8.2, color=MUTED, ha="left", va="center")
    ax.text(18.05, 0.25,
            "Limitations: n = 18 headline clips; LLM-judged ADQA; TRIBE risk is pilot evidence.",
            fontsize=8.2, color=ROSE, ha="right", va="center",
            fontweight="bold")

    out = CHARTS / "scenetwin_technical_methodology_summary.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
