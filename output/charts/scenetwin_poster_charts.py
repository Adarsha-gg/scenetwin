#!/usr/bin/env python3
"""Statistical charts for the SceneTwin NJBDA poster.

Each chart is independently sized and styled to drop into the 36×48 poster.

Outputs:
  scenetwin_per_tier_heatmap.png
  scenetwin_bootstrap_ci.png
  scenetwin_length_bias.png
  scenetwin_failure_forecast.png
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.stats import rankdata

ROOT = Path("/Users/adarsha/Knowledge")
CHARTS = ROOT / "output" / "charts"
ENSEMBLE_DIR = ROOT / "output" / "scenetwin_timing_20clip" / "ensemble"
TRIBE_DIR = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native"

INK   = "#161a1d"
MUTED = "#56636d"
LINE  = "#cdd6dc"
TEAL  = "#0d7f83"
BLUE  = "#285a8f"
ROSE  = "#b73558"
GOLD  = "#c88a20"
GREEN = "#4d7f3a"

TIER_ORDER  = ["tier3_va11y", "tier2_vatex_long",
               "tier1_vatex_short", "tier0_cross"]
TIER_LABEL  = {
    "tier3_va11y":       "tier 3 · professional AD",
    "tier2_vatex_long":  "tier 2 · VATEX long",
    "tier1_vatex_short": "tier 1 · VATEX short",
    "tier0_cross":       "tier 0 · cross-category (wrong scene)",
}

PLT_RC = {
    "font.family": "DejaVu Sans",
    "axes.titlesize": 12, "axes.labelsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white",
}


def load_ensemble() -> pd.DataFrame:
    df = pd.read_csv(ENSEMBLE_DIR / "adqa_clip_ensemble_scores.csv")
    return df[["clip_idx", "tier", "gt", "ensemble_mean_clip_mean"]].rename(
        columns={"ensemble_mean_clip_mean": "ensemble"})


def spearman(x, y):
    return float(np.corrcoef(rankdata(x), rankdata(y))[0, 1])


# ─────────────────────────────────────────────────────────────────────────
# Per-tier heatmap
# ─────────────────────────────────────────────────────────────────────────
def chart_heatmap(df: pd.DataFrame, outpath: Path):
    rho = spearman(df["gt"], df["ensemble"])
    clips = sorted(df["clip_idx"].unique())
    pivot = df.pivot(index="tier", columns="clip_idx", values="ensemble")
    pivot = pivot.reindex(TIER_ORDER)
    mat = pivot.values

    fig = plt.figure(figsize=(13, 6.2))
    fig.patch.set_facecolor("white")

    gs = fig.add_gridspec(1, 2, width_ratios=[5, 1], wspace=0.06,
                          left=0.08, right=0.97, top=0.82, bottom=0.18)
    ax = fig.add_subplot(gs[0, 0])
    ax_marg = fig.add_subplot(gs[0, 1], sharey=ax)

    im = ax.imshow(mat, cmap="YlOrRd", aspect="auto",
                   vmin=0, vmax=1, interpolation="nearest")
    # annotate each cell
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat[i, j]
            txt = "—" if np.isnan(v) else f"{v:.2f}"
            color = "white" if (not np.isnan(v) and v > 0.55) else INK
            ax.text(j, i, txt, ha="center", va="center",
                    fontsize=8.0, color=color)

    ax.set_xticks(range(len(clips)))
    ax.set_xticklabels([f"{c:02d}" for c in clips], fontsize=8.5)
    ax.set_yticks(range(len(TIER_ORDER)))
    ax.set_yticklabels([TIER_LABEL[t] for t in TIER_ORDER], fontsize=9.5)
    ax.set_xlabel("Clip index", fontsize=10)
    ax.tick_params(axis="x", which="both", length=0)
    ax.tick_params(axis="y", which="both", length=0)
    ax.set_title("Ensemble audit score per (clip × tier) — darker = higher quality",
                 fontsize=11.5, fontweight="bold", loc="left", pad=8)

    # ── Marginal: tier mean bars ──────────────────────────────────────────
    tier_means = pivot.mean(axis=1).values
    colors = ["#0d7f83", "#285a8f", "#c88a20", "#b73558"]
    ax_marg.barh(range(len(TIER_ORDER)), tier_means, color=colors,
                 edgecolor="black", linewidth=0.6, height=0.78)
    for i, v in enumerate(tier_means):
        ax_marg.text(v + 0.02, i, f"{v:.2f}", va="center",
                     fontsize=9.5, fontweight="bold", color=INK)
    ax_marg.set_xlim(0, 1.15)
    ax_marg.set_xticks([0, 0.5, 1.0])
    ax_marg.set_xticklabels(["0", "0.5", "1.0"], fontsize=8)
    ax_marg.set_xlabel("mean score", fontsize=9.5)
    ax_marg.tick_params(axis="y", which="both", length=0,
                        labelleft=False)
    ax_marg.spines["left"].set_visible(False)
    ax_marg.set_title("Tier mean", fontsize=10.5,
                      fontweight="bold", loc="left", pad=8)

    # Big-headline strip
    fig.text(0.50, 0.93,
             f"ρ = {rho:.3f}   [CI 0.90, 0.96]   "
             "54 / 54 pairwise wins   ·   15 / 18 fully ordered",
             ha="center", fontsize=14, fontweight="bold", color=INK)
    fig.text(0.50, 0.895,
             "n = 18 clips × 4 quality tiers · permutation p < 0.0005",
             ha="center", fontsize=10, color=MUTED, style="italic")

    # Colorbar bottom
    cax = fig.add_axes([0.10, 0.07, 0.55, 0.018])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal")
    cb.set_label("audit score  (0 = worst tier of clip, 1 = best tier of clip)",
                 fontsize=9, color=INK)
    cb.ax.tick_params(labelsize=8)

    fig.savefig(outpath, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {outpath}  (ρ={rho:.4f})")


# ─────────────────────────────────────────────────────────────────────────
# Bootstrap CI bars
# ─────────────────────────────────────────────────────────────────────────
def chart_bootstrap_ci(outpath: Path):
    bars = [
        ("CLIP-only",         0.801, 0.728, 0.873, "#56636d"),
        ("ADQA-only",         0.789, 0.700, 0.880, "#56636d"),
        ("CLIP + ADQA\nensemble", 0.929, 0.904, 0.957, TEAL),
    ]
    labels = [b[0] for b in bars]
    means  = np.array([b[1] for b in bars])
    los    = np.array([b[2] for b in bars])
    his    = np.array([b[3] for b in bars])
    colors = [b[4] for b in bars]

    fig, ax = plt.subplots(figsize=(7.8, 5.75))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(top=0.70, bottom=0.16, left=0.13, right=0.97)
    fig.text(0.13, 0.95,
             "Bootstrap 95 % CI: ensemble beats either signal alone",
             fontsize=12.5, fontweight="bold", color=INK, ha="left", va="top")
    fig.text(0.13, 0.905,
             "n = 18 clips · 2000 resamples. Non-overlapping CIs indicate the\n"
             "ensemble lift is not a small-sample artifact.",
             fontsize=8.9, color=MUTED, style="italic", ha="left", va="top")
    xs = np.arange(len(bars))
    err = np.vstack([means - los, his - means])
    ax.bar(xs, means, yerr=err, color=colors, capsize=10,
           edgecolor="black", linewidth=0.8, width=0.55,
           error_kw={"elinewidth": 1.5, "capthick": 1.5})
    for x, m, lo, hi in zip(xs, means, los, his):
        ax.text(x, hi + 0.02, f"{m:.3f}\n[{lo:.2f}, {hi:.2f}]",
                ha="center", va="bottom", fontsize=9.5, fontweight="bold")

    ax.axhline(0.873, linestyle=":", color=ROSE, linewidth=1.3)
    ax.text(0.015, 0.879, "CLIP-only 95 % upper bound", color=ROSE,
            fontsize=8.5, transform=ax.get_yaxis_transform())

    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=9.8)
    ax.set_ylabel("Spearman ρ vs ground-truth tier", fontsize=10)
    ax.set_ylim(0.5, 1.06)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.savefig(outpath, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {outpath}")


# ─────────────────────────────────────────────────────────────────────────
# Length bias check
# ─────────────────────────────────────────────────────────────────────────
def chart_length_bias(outpath: Path):
    bars = [
        ("Length only\n(word count)",           0.318, ROSE,  "0 / 18\nfully ordered",
         "If verbosity alone explained the result,\nthis bar would match the ensemble."),
        ("Length-residualized\nensemble",        0.874, GOLD,  "perm  p ≈ 0",
         "After removing the effect of word count\nfrom every score, the signal survives."),
        ("Full ensemble\n(headline)",            0.929, TEAL,  "15 / 18\nfully ordered",
         "Final pipeline. Verbosity is a partial\ncorrelate, not the underlying signal."),
    ]
    fig, ax = plt.subplots(figsize=(10.5, 7.0))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(top=0.74, bottom=0.20, left=0.10, right=0.97)
    fig.text(0.10, 0.90,
             "Is the result just word count?  No.",
             fontsize=15, fontweight="bold", color=INK, ha="left")
    fig.text(0.10, 0.85,
             "Three rankings of the same 18 clips × 4 tiers. Length-only is "
             "the most a pipeline could achieve\nif it secretly used word count "
             "as a proxy for quality.",
             fontsize=10, color=MUTED, style="italic", ha="left", va="top")
    xs = np.arange(len(bars))
    rhos = [b[1] for b in bars]
    colors = [b[2] for b in bars]
    foot = [b[3] for b in bars]
    notes = [b[4] for b in bars]

    ax.bar(xs, rhos, color=colors, edgecolor="black", linewidth=0.8, width=0.60)
    for x, r, n in zip(xs, rhos, foot):
        ax.text(x, r + 0.02, f"ρ = {r:.3f}", ha="center", va="bottom",
                fontsize=12, fontweight="bold")
        ax.text(x, -0.04, n, ha="center", va="top",
                fontsize=9, color=MUTED, style="italic")
    # Per-bar caption box
    for x, note, color in zip(xs, notes, colors):
        ax.text(x, -0.20, note, ha="center", va="top",
                fontsize=8.7, color=INK,
                bbox=dict(boxstyle="round,pad=0.35", fc="white",
                          ec=color, lw=1.0))

    ax.set_xticks(xs)
    ax.set_xticklabels([b[0] for b in bars], fontsize=10)
    ax.set_ylabel("Spearman ρ vs ground-truth tier", fontsize=10)
    ax.set_ylim(-0.45, 1.10)
    ax.axhline(0, color="black", linewidth=0.5)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.savefig(outpath, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {outpath}")


# ─────────────────────────────────────────────────────────────────────────
# Failure forecast
# ─────────────────────────────────────────────────────────────────────────
def chart_failure_forecast(outpath: Path):
    df = pd.read_csv(TRIBE_DIR / "tribe_failure_forecast.csv")
    df = df.sort_values("risk_rank").head(10).copy()

    fig, ax = plt.subplots(figsize=(11.5, 7.4))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(top=0.74, bottom=0.10, left=0.20, right=0.98)
    fig.text(0.20, 0.90,
             "TRIBE flags fragile evaluations before any AD is scored",
             fontsize=14, fontweight="bold", color=INK, ha="left")
    fig.text(0.20, 0.85,
             "Top-10 clips by TRIBE risk forecast — red = clip the ADQA "
             "ensemble failed to fully order.\n"
             "Computed from video + audio alone. "
             "Recall @ 11.1 % review budget = 100 %  ·  ROC-AUC = 1.00  ·  "
             "uncorrected p = 0.0065  (Bonferroni p = 0.065). Pilot evidence.",
             fontsize=9.5, color=MUTED, style="italic", ha="left", va="top")

    colors = [ROSE if f else "#cdd6dc" for f in df["all4_fail"]]
    ax.barh(range(len(df)), df["risk_score"],
            color=colors, edgecolor="black", linewidth=0.6)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(
        [f"#{r:>2}    clip {c:02d}    {cat}"
         for r, c, cat in zip(df["risk_rank"], df["clip_idx"], df["category"])],
        fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("TRIBE risk score   (mean_standard_slot_score)", fontsize=10)

    # review budget line — drawn between bar #2 and #3
    ax.axhline(1.5, color=ROSE, linewidth=1.4, linestyle=":")
    ax.annotate("review budget  =  2 / 18  =  11.1 %",
                xy=(0.30, 1.5), xycoords=("axes fraction", "data"),
                xytext=(0.32, 2.4), textcoords=("axes fraction", "data"),
                color=ROSE, fontsize=9.5, fontweight="bold", va="center",
                arrowprops=dict(arrowstyle="-", color=ROSE, lw=1))

    ax.grid(axis="x", linestyle="--", alpha=0.4)
    # No fig.tight_layout — we set subplots_adjust manually.


    # Right-side text block: what the risk score is and how to read this
    inset = ax.inset_axes([0.55, 0.18, 0.42, 0.36], transform=ax.transAxes,
                          zorder=10)
    inset.set_xticks([]); inset.set_yticks([])
    for s in inset.spines.values():
        s.set_color(ROSE); s.set_linewidth(1.4)
    inset.set_facecolor("#fff5f7")
    inset.text(0.04, 0.92, "How to read this", fontsize=10,
               fontweight="bold", color=ROSE, transform=inset.transAxes,
               va="top")
    inset.text(0.04, 0.74,
               "TRIBE flags clips whose audio-vs-AV neural gap is high\n"
               "and broadly distributed.  Those clips are also the ones\n"
               "where automatic comprehension scoring is fragile —\n"
               "either tier ordering inverts or the margin collapses.\n\n"
               "Inspecting the top 2 of 18 ranked clips catches both\n"
               "ADQA full-order failures on this set.",
               fontsize=9, color=INK, transform=inset.transAxes,
               va="top")

    fig.savefig(outpath, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote {outpath}")


def main():
    plt.rcParams.update(PLT_RC)
    df = load_ensemble()
    print(f"Loaded ensemble: {len(df)} rows, {df['clip_idx'].nunique()} clips\n")

    print("[1/4] per-tier heatmap")
    chart_heatmap(df, CHARTS / "scenetwin_per_tier_heatmap.png")

    print("[2/4] bootstrap CI bars")
    chart_bootstrap_ci(CHARTS / "scenetwin_bootstrap_ci.png")

    print("[3/4] length-bias bars")
    chart_length_bias(CHARTS / "scenetwin_length_bias.png")

    print("[4/4] failure forecast risk bars")
    chart_failure_forecast(CHARTS / "scenetwin_failure_forecast.png")

    print("\nDone.")


if __name__ == "__main__":
    main()
