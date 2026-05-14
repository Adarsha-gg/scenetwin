#!/usr/bin/env python3
"""Architecture diagram + failed-branches graphic for the SceneTwin poster.

Outputs:
  output/charts/scenetwin_architecture.png
  output/charts/scenetwin_killed_branches.png
"""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

CHARTS = Path("/Users/adarsha/Knowledge/output/charts")

INK    = "#161a1d"
MUTED  = "#56636d"
LINE   = "#cdd6dc"
WHITE  = "#ffffff"
TEAL   = "#0d7f83"
BLUE   = "#285a8f"
ROSE   = "#b73558"
GOLD   = "#c88a20"
SLATE  = "#26313a"


def block(ax, x, y, w, h, *, face, edge=INK, line_w=1.4, radius=0.10):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.005,rounding_size={radius}",
                       linewidth=line_w, edgecolor=edge, facecolor=face)
    ax.add_patch(p)


def label(ax, x, y, text, *, fc, fs=12, w=None, bold=True):
    ax.text(x, y, text, ha="center", va="center", color=fc,
            fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x1, y1, x2, y2, *, color=INK, lw=1.6, curve=0):
    a = FancyArrowPatch((x1, y1), (x2, y2),
                        arrowstyle="-|>", mutation_scale=18,
                        color=color, linewidth=lw,
                        connectionstyle=f"arc3,rad={curve}")
    ax.add_patch(a)


# ─────────────────────────────────────────────────────────────────────────
# Architecture
# ─────────────────────────────────────────────────────────────────────────
def build_architecture():
    fig, ax = plt.subplots(figsize=(15, 8.2))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 8.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)
    ax.set_facecolor(WHITE)

    # Title row
    ax.text(0.5, 7.85, "How SceneTwin scores an audio description",
            fontsize=17, fontweight="bold", color=INK)
    ax.text(0.5, 7.45,
            "A single video clip and a single candidate description go in. "
            "Three independent signals run in parallel. Two are scored and combined; "
            "the third forecasts when the score itself is fragile.",
            fontsize=10.5, color=MUTED, style="italic")

    # ── Input column ──────────────────────────────────────────────────────
    block(ax, 0.4, 3.3, 2.3, 1.55, face=SLATE)
    label(ax, 0.4 + 1.15, 3.3 + 1.05, "Video clip", fc=WHITE, fs=12.5)
    label(ax, 0.4 + 1.15, 3.3 + 0.55, "+ candidate AD text", fc=WHITE, fs=10.5, bold=False)
    ax.text(0.4 + 1.15, 3.0, "10 – 20 sec clip\n+ description in any style",
            ha="center", va="top", fontsize=9, color=MUTED, style="italic")

    # ── Three signal columns ──────────────────────────────────────────────
    col_x = 4.3
    col_w = 3.6
    rows = [
        # (y, color, title, what_it_does, catches)
        (5.7, BLUE,  "CLIP-L14  visual grounding",
         "Cosine similarity between sampled\nframes and the AD text.",
         "catches hallucinated / wrong-scene AD"),
        (3.3, TEAL,  "Frame-grounded ADQA",
         "Vision LLM writes questions from frames.\nSeparate LLM grades the AD blind,\nwithout seeing the frames.",
         "catches vague / under-specified AD"),
        (0.9, ROSE,  "TRIBE  fMRI encoder",
         "Predicts visual-cortex activation\nfor full video (P_AV) and audio-only (P_A).\nGap |P_AV − P_A| feeds risk forecast.",
         "side-car: flags fragile evaluations"),
    ]
    for y, color, title, body, catches in rows:
        block(ax, col_x, y, col_w, 1.55, face=color)
        label(ax, col_x + col_w / 2, y + 1.22, title, fc=WHITE, fs=12)
        ax.text(col_x + col_w / 2, y + 0.55, body, ha="center", va="center",
                color=WHITE, fontsize=9.2)
        ax.text(col_x + col_w / 2, y - 0.13, catches, ha="center", va="top",
                fontsize=9, color=MUTED, style="italic")

    # Input → three signals
    for y in (6.45, 4.05, 1.65):
        arrow(ax, 2.75, 4.05, 4.3, y, color=INK)

    # ── Ensemble + score (CLIP + ADQA merge) ──────────────────────────────
    ens_x = 8.85
    ens_w = 2.0
    block(ax, ens_x, 3.85, ens_w, 1.50, face=GOLD)
    label(ax, ens_x + ens_w / 2, 3.85 + 1.10, "Ensemble", fc=WHITE, fs=12.5)
    label(ax, ens_x + ens_w / 2, 3.85 + 0.65, "50 / 50  mean", fc=WHITE, fs=10.5, bold=False)
    ax.text(ens_x + ens_w / 2, 3.85 - 0.18, "weights fixed,\nno tuning required",
            ha="center", va="top", fontsize=8.5, color=MUTED, style="italic")

    arrow(ax, col_x + col_w, 6.45, ens_x, 4.85, color=BLUE, curve=-0.18)
    arrow(ax, col_x + col_w, 4.05, ens_x, 4.60, color=TEAL)

    # ── Final score ────────────────────────────────────────────────────────
    score_x = 11.7
    block(ax, score_x, 3.85, 2.95, 1.50, face=INK)
    label(ax, score_x + 1.475, 3.85 + 1.05, "Audit score", fc=WHITE, fs=12.5)
    ax.text(score_x + 1.475, 3.85 + 0.55, "ρ = 0.929", ha="center", va="center",
            color="#fdd96b", fontsize=22, fontweight="bold")
    ax.text(score_x + 1.475, 3.85 - 0.16,
            "[95% CI 0.90, 0.96]\n54/54 pairwise wins · 15/18 fully ordered",
            ha="center", va="top", fontsize=9, color=MUTED, style="italic")
    arrow(ax, ens_x + ens_w, 4.60, score_x, 4.60, color=GOLD, lw=2.0)

    # ── TRIBE side-car ────────────────────────────────────────────────────
    risk_x = 11.7
    block(ax, risk_x, 0.9, 2.95, 1.50, face=ROSE)
    label(ax, risk_x + 1.475, 0.9 + 1.05, "Risk forecast", fc=WHITE, fs=12.5)
    ax.text(risk_x + 1.475, 0.9 + 0.55, "AUC = 1.00", ha="center", va="center",
            color=WHITE, fontsize=18, fontweight="bold")
    ax.text(risk_x + 1.475, 0.9 - 0.16,
            "Catches both ADQA-failure clips\nat 11.1% review budget",
            ha="center", va="top", fontsize=9, color=MUTED, style="italic")
    arrow(ax, col_x + col_w, 1.65, risk_x, 1.65, color=ROSE, lw=1.6)

    fig.savefig(CHARTS / "scenetwin_architecture.png", dpi=220,
                bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"  wrote {CHARTS / 'scenetwin_architecture.png'}")


# ─────────────────────────────────────────────────────────────────────────
# Killed branches
# ─────────────────────────────────────────────────────────────────────────
def build_killed():
    fig, ax = plt.subplots(figsize=(15, 5.6))
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 5.6)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(WHITE)

    ax.text(0.4, 5.20, "What did not survive validation",
            fontsize=16, fontweight="bold", color=INK)
    ax.text(0.4, 4.78,
            "Each branch below looked plausible. Each was measured against ground-truth tiers "
            "or professional AD, and dropped before being claimed in the final pipeline.",
            fontsize=10, color=MUTED, style="italic")

    cards = [
        ("Description Gain",
         "Counterfactual neural metric (MVRR).",
         "Unstable on 2-clip smoke test, no visual grounding."),
        ("ROI content typing",
         "Match TRIBE per-ROI gap to AD content type.",
         "Glasser atlas: 19.0 % vs 16.7 % chance. Killed by LLM pro-AD check."),
        ("Neural closure",
         "Show AD text moves TRIBE prediction toward AV viewing.",
         "All values negative on 2 clips. Shorter AD wins; verbosity inflates language ROIs."),
        ("TRIBE-weighted ADQA",
         "Up-weight ADQA questions on high-gap windows.",
         "Null result. Δρ < 0.002 vs uniform weighting."),
    ]
    card_w, card_h = 3.40, 3.55
    x0, y0 = 0.4, 0.55
    gap = 0.20
    for i, (title, what, why) in enumerate(cards):
        x = x0 + i * (card_w + gap)
        ax.add_patch(FancyBboxPatch(
            (x, y0), card_w, card_h,
            boxstyle="round,pad=0.01,rounding_size=0.07",
            linewidth=1.2, edgecolor=MUTED, facecolor=WHITE))
        ax.add_patch(FancyBboxPatch(
            (x, y0 + card_h - 0.62), card_w, 0.62,
            boxstyle="round,pad=0.0,rounding_size=0.07",
            linewidth=0, facecolor=ROSE))
        ax.text(x + 0.22, y0 + card_h - 0.31, title,
                fontsize=11.5, fontweight="bold", color=WHITE, va="center")
        ax.text(x + card_w - 0.22, y0 + card_h - 0.31, "✗",
                fontsize=17, fontweight="bold", color=WHITE,
                va="center", ha="right")

        ax.text(x + 0.22, y0 + card_h - 1.05, "What it was",
                fontsize=9, fontweight="bold", color=MUTED)
        for j, line in enumerate(_wrap(what, 32)):
            ax.text(x + 0.22, y0 + card_h - 1.28 - 0.24 * j, line,
                    fontsize=9.5, color=INK)

        ax.plot([x + 0.22, x + card_w - 0.22],
                [y0 + card_h - 2.20, y0 + card_h - 2.20],
                color=LINE, linewidth=1)

        ax.text(x + 0.22, y0 + card_h - 2.48, "Why it failed",
                fontsize=9, fontweight="bold", color=ROSE)
        for j, line in enumerate(_wrap(why, 32)):
            ax.text(x + 0.22, y0 + card_h - 2.72 - 0.24 * j, line,
                    fontsize=9.5, color=INK)

    fig.savefig(CHARTS / "scenetwin_killed_branches.png", dpi=220,
                bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"  wrote {CHARTS / 'scenetwin_killed_branches.png'}")


def _wrap(text, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    return lines


def main():
    print("[1/2] architecture")
    build_architecture()
    print("[2/2] killed branches")
    build_killed()


if __name__ == "__main__":
    main()
