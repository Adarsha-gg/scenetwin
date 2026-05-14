#!/usr/bin/env python3
"""Build a poster figure comparing baseline AD QA solutions with SceneTwin."""
from __future__ import annotations

from pathlib import Path
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

CHARTS = Path("/Users/adarsha/Knowledge/output/charts")

INK = "#161a1d"
MUTED = "#56636d"
LINE = "#cdd6dc"
WHITE = "#ffffff"
TEAL = "#0d7f83"
BLUE = "#285a8f"
ROSE = "#b73558"
GOLD = "#c88a20"
SLATE = "#26313a"


def _wrap(text, width):
    words = text.split()
    lines = []
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


def build():
    fig, ax = plt.subplots(figsize=(14.5, 7.0))
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 14.5)
    ax.set_ylim(0, 7.0)
    ax.axis("off")

    ax.text(0.55, 6.55, "Problem: current AD QA does not scale to AI-generated descriptions",
            fontsize=16, fontweight="bold", color=INK, ha="left", va="top")
    ax.text(0.55, 6.08,
            "Accessibility standards require descriptions of visual information not available from audio alone. "
            "But practical QA still leans on availability checks, manual review, or narrow automated proxies.",
            fontsize=9.8, color=MUTED, style="italic", ha="left", va="top", wrap=True)

    # Left: current/prior approaches as a vertical grayscale table.
    x0, y0 = 0.55, 1.12
    table_w, table_h = 8.72, 4.48
    ax.add_patch(FancyBboxPatch(
        (x0, y0), table_w, table_h,
        boxstyle="round,pad=0.01,rounding_size=0.06",
        linewidth=1.1, edgecolor=LINE, facecolor=WHITE))

    cols = [
        ("Current / baseline", 0.00, 2.65),
        ("rho", 2.65, 0.82),
        ("wins", 3.47, 0.98),
        ("ordered", 4.45, 1.02),
        ("limitation", 5.47, 3.25),
    ]
    header_h = 0.52
    row_h = (table_h - header_h) / 3

    # Header
    ax.add_patch(Rectangle((x0, y0 + table_h - header_h), table_w, header_h,
                           facecolor=SLATE, edgecolor="none"))
    for label, cx, cw in cols:
        ax.text(x0 + cx + 0.12, y0 + table_h - header_h / 2, label,
                color=WHITE, fontsize=8.8, fontweight="bold",
                ha="left", va="center")

    baseline_rows = [
        {
            "approach": "Manual / compliance QA",
            "rho": "N/A",
            "wins": "N/A",
            "ordered": "N/A",
            "breaks": "Accurate when expert-led, but slow; availability checks do not rank quality.",
            "color": "#f7f8f9",
        },
        {
            "approach": "CLIP-only visual grounding",
            "rho": "0.801",
            "wins": "48/54",
            "ordered": "11/18",
            "breaks": "Misses vague but visually plausible descriptions.",
            "color": "#f7f8f9",
        },
        {
            "approach": "Frame-grounded ADQA only",
            "rho": "0.803",
            "wins": "51/54",
            "ordered": "8/18",
            "breaks": "Strong comprehension proxy, but less stable than the ensemble.",
            "color": "#eef1f3",
        },
    ]

    for i, row in enumerate(baseline_rows):
        y = y0 + table_h - header_h - (i + 1) * row_h
        ax.add_patch(Rectangle((x0, y), table_w, row_h,
                               facecolor=row["color"], edgecolor=LINE,
                               linewidth=0.65))
        values = [
            row["approach"], row["rho"], row["wins"], row["ordered"],
            row["breaks"],
        ]
        for (label, cx, cw), value in zip(cols, values):
            color = "#424b52" if label in {"rho", "wins", "ordered"} else INK
            fs = 8.7 if label == "Current / baseline" else 8.0
            weight = "bold" if label == "Current / baseline" or label in {"rho", "wins", "ordered"} else "normal"
            if label in {"rho", "wins", "ordered"}:
                ax.text(x0 + cx + cw / 2, y + row_h / 2, value,
                        color=color, fontsize=11.5, fontweight="bold",
                        ha="center", va="center")
            else:
                wrap_width = 23 if label == "Current / baseline" else 36
                ax.text(x0 + cx + 0.12, y + row_h / 2,
                        "\n".join(_wrap(value, wrap_width)),
                        color=color, fontsize=fs, fontweight=weight,
                        ha="left", va="center", linespacing=1.18)

    # Right: highlighted SceneTwin panel.
    sx, sy = 9.65, 1.12
    sw, sh = 4.3, 4.48
    ax.add_patch(FancyBboxPatch(
        (sx, sy), sw, sh,
        boxstyle="round,pad=0.015,rounding_size=0.075",
        linewidth=1.4, edgecolor=TEAL, facecolor="#f3fbfb"))
    ax.add_patch(FancyBboxPatch(
        (sx, sy + sh - 0.70), sw, 0.70,
        boxstyle="round,pad=0.0,rounding_size=0.075",
        linewidth=0, facecolor=TEAL))
    ax.text(sx + 0.22, sy + sh - 0.35, "SceneTwin",
            color=WHITE, fontsize=14.2, fontweight="bold",
            ha="left", va="center")
    ax.text(sx + 0.22, sy + sh - 0.97,
            "CLIP + frame-grounded ADQA + TRIBE triage",
            color=INK, fontsize=9.2, fontweight="bold",
            ha="left", va="top")

    stat_y = sy + 2.30
    stat_w, stat_h = 1.20, 0.90
    stat_gap = 0.16
    stats = [
        ("0.929", "rho"),
        ("54/54", "pairwise wins"),
        ("15/18", "fully ordered"),
    ]
    for i, (num, lab) in enumerate(stats):
        x = sx + 0.22 + i * (stat_w + stat_gap)
        ax.add_patch(FancyBboxPatch(
            (x, stat_y), stat_w, stat_h,
            boxstyle="round,pad=0.01,rounding_size=0.05",
            linewidth=1.0, edgecolor="#98caca", facecolor=WHITE))
        ax.text(x + stat_w / 2, stat_y + 0.57, num, ha="center", va="center",
                color=TEAL, fontsize=14.5, fontweight="bold")
        ax.text(x + stat_w / 2, stat_y + 0.23, lab, ha="center", va="center",
                color=MUTED, fontsize=7.2, fontweight="bold")

    ax.text(sx + 0.22, sy + 1.78,
            "What it measures",
            color=INK, fontsize=8.8, fontweight="bold",
            ha="left", va="top")
    ax.text(sx + 0.22, sy + 1.48,
            "Grounding: does the AD match the frames?\n"
            "Answerability: can it answer visual questions?\n"
            "Risk: should this clip be sent to stronger review?",
            color=INK, fontsize=8.1, ha="left", va="top",
            linespacing=1.25)
    ax.text(sx + 0.22, sy + 0.54,
            "Pilot evaluation on 18 complete clips;\n"
            "requires BLV-user validation.",
            color=MUTED, fontsize=7.8, style="italic",
            ha="left", va="top", linespacing=1.18)

    ax.text(x0, 0.78,
            "Automatic rows use SceneTwin's 18 complete clips x 4 quality tiers. Manual/compliance QA is included as the dominant practical baseline; it does not produce rho or pairwise-win metrics.",
            fontsize=7.8, color=MUTED, style="italic", ha="left", va="top")

    # Bottom punchline
    ax.add_patch(FancyBboxPatch(
        (0.55, 0.18), 13.4, 0.43,
        boxstyle="round,pad=0.02,rounding_size=0.055",
        linewidth=1.0, edgecolor="#b8c7ce", facecolor="#f7fbfb"))
    ax.text(0.80, 0.395,
            "SceneTwin changes QA from 'does description exist?' to 'is it visually grounded, answerable, and likely reliable?'",
            fontsize=9.6, fontweight="bold", color=INK, va="center", ha="left")

    fig.savefig(CHARTS / "scenetwin_current_solution_comparison.png",
                dpi=220, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"wrote {CHARTS / 'scenetwin_current_solution_comparison.png'}")


if __name__ == "__main__":
    build()
