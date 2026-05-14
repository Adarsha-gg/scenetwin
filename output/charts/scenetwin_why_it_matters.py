#!/usr/bin/env python3
"""Build the SceneTwin "why it matters" poster panel.

Output: output/charts/scenetwin_why_it_matters.png
"""
from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

CHARTS = Path("/Users/adarsha/Knowledge/output/charts")

INK = "#161a1d"
MUTED = "#56636d"
LINE = "#cfd8de"
PAPER = "#fbfaf6"
WHITE = "#ffffff"
ORANGE = "#ca8a1c"
TEAL = "#0d7f83"
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


def rounded(ax, x, y, w, h, *, face=WHITE, edge=LINE, lw=1.1, radius=0.08):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.015,rounding_size={radius}",
        linewidth=lw, edgecolor=edge, facecolor=face))


def text_block(ax, x, y, heading, body, *, heading_color=INK, body_width=42):
    ax.text(x, y, heading, ha="left", va="top", fontsize=11.5,
            color=heading_color, fontweight="bold")
    yy = y - 0.38
    for line in wrap(body, body_width):
        ax.text(x, yy, line, ha="left", va="top", fontsize=9.1,
                color=MUTED)
        yy -= 0.27


def stat(ax, x, y, w, h, value, label, *, color=TEAL, fs=18):
    rounded(ax, x, y, w, h, face=WHITE, edge=color, lw=1.2, radius=0.06)
    ax.text(x + w / 2, y + h * 0.62, value, ha="center", va="center",
            fontsize=fs, color=color, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.25, label, ha="center", va="center",
            fontsize=8.8, color=INK, fontweight="bold")


def main():
    fig, ax = plt.subplots(figsize=(18.0, 6.35))
    fig.patch.set_facecolor(PAPER)
    ax.set_facecolor(PAPER)
    ax.set_xlim(0, 18.0)
    ax.set_ylim(0, 6.35)
    ax.axis("off")

    ax.text(0.45, 5.92, "Why this matters",
            fontsize=24, fontweight="bold", color=ORANGE,
            ha="left", va="top")
    ax.text(0.45, 5.42,
            "Audio description quality is becoming a scale problem, not just a captioning problem.",
            fontsize=12.5, color=INK, fontweight="bold",
            ha="left", va="top")
    ax.text(0.45, 5.05,
            "AI can generate descriptions quickly. The missing piece is an audit that checks whether those descriptions actually match the visual scene.",
            fontsize=9.8, color=MUTED, style="italic",
            ha="left", va="top")

    # Left: concise problem statement.
    rounded(ax, 0.45, 0.55, 5.25, 4.20, face=WHITE, edge=SLATE, lw=1.5)
    ax.add_patch(Rectangle((0.45, 4.24), 5.25, 0.51,
                           facecolor=SLATE, edgecolor="none"))
    ax.text(0.72, 4.495, "The problem", fontsize=12.2,
            color=WHITE, fontweight="bold", ha="left", va="center")
    ax.text(0.82, 3.76,
            "Bad AD can be present\nbut still fail.",
            fontsize=14.8, color=INK, fontweight="bold",
            ha="left", va="top", linespacing=1.08)
    for i, line in enumerate(wrap(
            "A description can exist, sound fluent, and still miss the action, identify the wrong scene, or omit the visual fact a blind viewer needs.",
            42)):
        ax.text(0.82, 2.90 - i * 0.30, line, fontsize=10.7,
                color=MUTED, ha="left", va="top")
    ax.plot([0.82, 5.32], [1.55, 1.55], color=LINE, linewidth=1.0)
    ax.text(0.82, 1.20,
            "Availability is not quality.",
            fontsize=15.5, color=ORANGE, fontweight="bold",
            ha="left", va="top")

    # Middle: current bottlenecks.
    rounded(ax, 6.05, 0.55, 5.25, 4.20, face=WHITE, edge=LINE, lw=1.0)
    ax.add_patch(Rectangle((6.05, 4.24), 5.25, 0.51,
                           facecolor="#eeeeee", edgecolor="none"))
    ax.text(6.32, 4.495, "Current QA options", fontsize=12.2,
            color=INK, fontweight="bold", ha="left", va="center")
    rows = [
        ("Manual review", "Human judgment is strongest, but does not scale to every generated clip."),
        ("BLEU / ROUGE", "Reference text metrics need a gold script and miss visual grounding."),
        ("Visual-only proxies", "They catch wrong scenes, but not vague or unhelpful descriptions."),
    ]
    y = 3.76
    for title, body in rows:
        ax.text(6.35, y, title, fontsize=12.3, color=INK,
                fontweight="bold", ha="left", va="top")
        for i, line in enumerate(wrap(body, 47)):
            ax.text(6.35, y - 0.32 - i * 0.25, line, fontsize=9.0,
                    color=MUTED, ha="left", va="top")
        y -= 1.05

    # Right: SceneTwin contribution.
    rounded(ax, 11.70, 0.55, 5.80, 4.20, face="#fffaf0",
            edge=ORANGE, lw=1.4)
    ax.add_patch(Rectangle((11.70, 4.24), 5.80, 0.51,
                           facecolor=ORANGE, edgecolor="none"))
    ax.text(11.98, 4.495, "What SceneTwin adds", fontsize=12.2,
            color=WHITE, fontweight="bold", ha="left", va="center")
    text_block(
        ax, 11.98, 3.76,
        "Reference-free audit",
        "Scores one candidate AD against the video itself, not against a single human script.",
        heading_color=INK,
        body_width=43,
    )
    sx, sy = 12.00, 0.88
    sw, sh = 2.42, 0.86
    stat(ax, sx, sy + 0.96, sw, sh, "0", "reference scripts", color=ORANGE, fs=20)
    stat(ax, sx + 2.72, sy + 0.96, sw, sh, "0.929", "rho vs tier", color=TEAL, fs=18)
    stat(ax, sx, sy, sw, sh, "54/54", "pairwise wins", color=TEAL, fs=18)
    stat(ax, sx + 2.72, sy, sw, sh, "AUC 1.00", "risk forecast", color=TEAL, fs=16)

    # Small flow cue.
    ax.text(5.86, 2.65, "→", fontsize=26, color=ORANGE,
            fontweight="bold", ha="center", va="center")
    ax.text(11.52, 2.65, "→", fontsize=26, color=ORANGE,
            fontweight="bold", ha="center", va="center")

    out = CHARTS / "scenetwin_why_it_matters.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)
    print(f"  wrote {out}")


if __name__ == "__main__":
    main()
