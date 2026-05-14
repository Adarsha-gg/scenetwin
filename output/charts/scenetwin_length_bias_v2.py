#!/usr/bin/env python3
"""Length-bias chart, v2 — replace the 3-bar comparison with a scatter
plot of word count vs audit score, coloured by tier. Reader can see
directly that tier 0 (cross-category, wrong scene) has the same word
counts as tier 1/2 but scores far lower — so the score is not just
word count.

Output: output/charts/scenetwin_length_bias.png
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import rankdata

ROOT = Path("/Users/adarsha/Knowledge")
CHARTS = ROOT / "output" / "charts"
ENSEMBLE_DIR = ROOT / "output" / "scenetwin_timing_20clip" / "ensemble"
TRIBE_DIR = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native"

INK   = "#161a1d"
MUTED = "#56636d"
TEAL  = "#0d7f83"
BLUE  = "#285a8f"
ROSE  = "#b73558"
GOLD  = "#c88a20"

TIER_COLOR = {
    "tier3_va11y":       TEAL,
    "tier2_vatex_long":  BLUE,
    "tier1_vatex_short": GOLD,
    "tier0_cross":       ROSE,
}
TIER_LABEL = {
    "tier3_va11y":       "tier 3 · professional AD",
    "tier2_vatex_long":  "tier 2 · VATEX long",
    "tier1_vatex_short": "tier 1 · VATEX short",
    "tier0_cross":       "tier 0 · cross-category   (wrong scene)",
}


def main():
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "axes.spines.top": False, "axes.spines.right": False,
    })

    ens = pd.read_csv(ENSEMBLE_DIR / "adqa_clip_ensemble_scores.csv")[
        ["clip_idx", "tier", "ensemble_mean_clip_mean"]].rename(
        columns={"ensemble_mean_clip_mean": "ensemble"})

    feats = pd.read_csv(TRIBE_DIR / "tribe_failure_forecast.csv")
    word_cols = {
        "tier0_cross":       "tier0_cross_words",
        "tier1_vatex_short": "tier1_vatex_short_words",
        "tier2_vatex_long":  "tier2_vatex_long_words",
        "tier3_va11y":       "tier3_va11y_words_feature",
    }
    rows = []
    for tier, col in word_cols.items():
        for _, r in feats.iterrows():
            rows.append({"clip_idx": int(r["clip_idx"]),
                         "tier": tier,
                         "words": int(r[col])})
    wc = pd.DataFrame(rows)
    df = ens.merge(wc, on=["clip_idx", "tier"], how="inner")

    # ── Compute the two ρ values shown as captions ───────────────────────
    rho_len = float(np.corrcoef(rankdata(df["words"]),
                                rankdata(df["ensemble"]))[0, 1])
    # Per-row ground-truth tier (encoded in tier name)
    tier_rank = {"tier0_cross": 0, "tier1_vatex_short": 1,
                 "tier2_vatex_long": 2, "tier3_va11y": 3}
    df["gt"] = df["tier"].map(tier_rank)
    rho_words_vs_gt = float(np.corrcoef(rankdata(df["words"]),
                                        rankdata(df["gt"]))[0, 1])

    # ── Plot ──────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(top=0.74, bottom=0.13, left=0.08, right=0.97)

    fig.text(0.08, 0.94, "Is the SceneTwin score just word count?  No.",
             fontsize=16, fontweight="bold", color=INK, ha="left")
    fig.text(0.08, 0.89,
             "Each dot is one (clip × tier) pair.  X = words in that "
             "description.  Y = SceneTwin audit score.",
             fontsize=10.5, color=MUTED, style="italic", ha="left")
    fig.text(0.08, 0.855,
             "If length explained quality, the dots would line up "
             "diagonally.  They don't — they stack by tier (colour), "
             "not by length.",
             fontsize=10.5, color=MUTED, style="italic", ha="left")

    # Background bands per tier mean score (subtle)
    tier_y_means = df.groupby("tier")["ensemble"].mean()
    for tier, ycol in TIER_COLOR.items():
        if tier in tier_y_means.index:
            ax.axhline(tier_y_means[tier], color=ycol, linewidth=1.0,
                       linestyle=":", alpha=0.35)

    # Scatter, ordered so pro is on top
    for tier in ["tier0_cross", "tier1_vatex_short",
                 "tier2_vatex_long", "tier3_va11y"]:
        sub = df[df["tier"] == tier]
        ax.scatter(sub["words"], sub["ensemble"],
                   color=TIER_COLOR[tier], s=95, alpha=0.85,
                   edgecolor="white", linewidth=1.2,
                   label=TIER_LABEL[tier], zorder=3)

    ax.set_xlabel("Word count of the description", fontsize=11)
    ax.set_ylabel("SceneTwin audit score   (0 = worst, 1 = best per clip)",
                  fontsize=11)
    ax.set_xlim(0, max(df["words"]) + 8)
    ax.set_ylim(-0.05, 1.10)
    ax.grid(linestyle="--", alpha=0.35)
    ax.legend(loc="lower right", fontsize=9.5, frameon=False,
              title="Tier  (colour)", title_fontsize=9.5)

    # Per-tier mean labels on the right axis
    for tier, ycol in TIER_COLOR.items():
        if tier in tier_y_means.index:
            y = tier_y_means[tier]
            ax.text(ax.get_xlim()[1] - 1, y, f"  mean = {y:.2f}",
                    fontsize=8.5, color=ycol, va="center", ha="right",
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.18", fc="white",
                              ec=ycol, lw=0.8))

    # Callout: cross-category dots
    cross = df[df["tier"] == "tier0_cross"]
    cx, cy = float(cross["words"].mean()), float(cross["ensemble"].mean())
    ax.annotate(
        "These are wrong-scene\ndescriptions — middling length,\n"
        "lowest score every time.",
        xy=(cx + 1, cy + 0.04), xytext=(cx + 10, 0.30),
        fontsize=9.5, color=ROSE, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.30", fc="white", ec=ROSE, lw=1.0),
        arrowprops=dict(arrowstyle="-|>", color=ROSE, lw=1.3,
                        connectionstyle="arc3,rad=-0.18"))

    # Bottom note: numeric summary
    ax.text(
        0.0, -0.18,
        f"Spearman of word count vs SceneTwin score = {rho_len:+.2f}    ·    "
        f"word count vs ground-truth tier = {rho_words_vs_gt:+.2f}    ·    "
        "SceneTwin score vs ground-truth tier = +0.93",
        transform=ax.transAxes, fontsize=9.5, color=INK)

    out = CHARTS / "scenetwin_length_bias.png"
    fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {out}  (rho_words_vs_score = {rho_len:.3f})")


if __name__ == "__main__":
    main()
