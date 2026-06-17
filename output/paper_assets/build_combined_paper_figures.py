#!/usr/bin/env python3
"""Build deterministic graph figures for the combined SceneTwin paper."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "output" / "paper_assets"
VAL_JSON = ROOT / "cursor" / "research" / "output" / "tribe_router_validation_summary.json"

BG = "#0f1418"
PANEL = "#151c22"
FG = "#edf2f4"
MUTED = "#a8b3bc"
GRID = "#33414a"
TEAL = "#2cc6bd"
AMBER = "#f2b84b"
RED = "#e95f5c"
GRAY = "#8d99a6"
BLUE = "#6aa8ff"


def save(fig, name: str) -> None:
    path = OUT / name
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print(f"wrote {path}")


def style_ax(ax, title: str, subtitle: str | None = None) -> None:
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10)
    ax.grid(axis="y", color=GRID, alpha=0.45, linewidth=0.8)
    ax.set_title(title, color=FG, fontsize=16, fontweight="bold", loc="left", pad=14)
    if subtitle:
        ax.text(0, 1.02, subtitle, transform=ax.transAxes, color=MUTED,
                fontsize=10, va="bottom")


def scoring_leaderboard() -> None:
    labels = ["SceneTwin\nCLIP+ADQA", "LLM-AD-Eval", "Best frontier\nVLM judge", "ADQA alone", "CLIP alone"]
    inbench = [0.929, 0.899, 0.756, 0.789, 0.801]
    external = [0.873, 0.857, 0.739, 0.867, 0.691]
    combined = [0.886, np.nan, 0.736, np.nan, np.nan]
    x = np.arange(len(labels))
    w = 0.24

    fig, ax = plt.subplots(figsize=(11, 5.8))
    style_ax(
        ax,
        "Reference-Free AD Scoring: SceneTwin Beats Metric and VLM Baselines",
        "Spearman rho on controlled in-benchmark clips and 60 external clips",
    )
    b1 = ax.bar(x - w, inbench, width=w, color=TEAL, label="18-clip benchmark")
    b2 = ax.bar(x, external, width=w, color=AMBER, label="60-clip external")
    b3 = ax.bar(x + w, combined, width=w, color=BLUE, label="78-clip combined")
    ax.set_ylim(0, 1.03)
    ax.set_ylabel("Spearman rho", color=FG, fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, color=FG, fontsize=10)
    ax.legend(frameon=False, labelcolor=FG, loc="upper right")

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            if np.isfinite(h):
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.018,
                        f"{h:.3f}", ha="center", va="bottom",
                        color=FG, fontsize=9, fontweight="bold")

    ax.annotate(
        "+0.134 over best external VLM",
        xy=(0, external[0]), xytext=(1.45, 0.98),
        color=FG, fontsize=11,
        arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.6),
    )
    save(fig, "fig_scoring_leaderboard.png")


def matched_target_validation(payload: dict) -> None:
    rows = [r for r in payload["evidence"] if r["subset"] == "matched"]
    keep = [
        "TRIBE target vs VLM target (VLM gets transcript)",
        "Gap-targeted AD vs generic AD (GPT-5 judge, 60 clips)",
        "Gap-targeted AD vs generic AD (Opus judge, 17 clips)",
        "Gap-targeted AD vs generic AD (Opus judge, 15-clip subset)",
        "Surgical TRIBE ADQA target vs generic AD",
    ]
    rows = [next(r for r in rows if r["experiment"] == k) for k in keep]
    labels = [
        "TRIBE vs VLM\n(transcript-fair)",
        "Gap-targeted AD\nGPT-5 judge",
        "Gap-targeted AD\nOpus 17 clips",
        "Gap-targeted AD\nOpus subset",
        "Surgical TRIBE\nADQA target",
    ]
    vals = [r["delta"] for r in rows]
    y = np.arange(len(vals))

    fig, ax = plt.subplots(figsize=(11, 6.5))
    style_ax(
        ax,
        "TRIBE Helps Where It Claims To Help",
        "Matched-target ADQA lift; ties excluded from sign-test p-values",
    )
    colors = [TEAL, TEAL, AMBER, AMBER, TEAL]
    bars = ax.barh(y, vals, color=colors, height=0.62)
    ax.axvline(0, color=FG, lw=1.0, alpha=0.7)
    ax.set_xlim(0, 0.34)
    ax.set_xlabel("ADQA score lift on matched questions/windows", color=FG, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=FG, fontsize=10)
    ax.invert_yaxis()
    ax.grid(axis="x", color=GRID, alpha=0.45)
    ax.grid(axis="y", visible=False)

    for bar, row in zip(bars, rows):
        w = bar.get_width()
        text = f"+{w:.3f}   {row['wins']}W/{row['losses']}L   p={row['sign_p_one_sided']:.2g}"
        ax.text(w + 0.008, bar.get_y() + bar.get_height() / 2, text,
                va="center", color=FG, fontsize=10, fontweight="bold")

    fig.text(
        0.12, 0.02,
        "Boundary condition: this is not a global-rho claim; it is a targeted accessibility-routing claim.",
        color=MUTED, fontsize=10,
    )
    save(fig, "fig_matched_target_validation.png")


def router_inventory(payload: dict) -> None:
    inv = payload["router_inventory"]
    cases = inv["case_counts"]
    routes = inv["route_counts"]
    case_order = [
        "scene_layout_replay",
        "low_gap_skip",
        "dynamic_type_shift",
        "moment_level_authoring",
        "agent_action_cue",
        "audio_language_confound_check",
    ]
    route_order = [
        "static_ad_ok_low_gap",
        "layout_replay_or_scene_cue",
        "action_state_or_agent_cue",
    ]

    fig = plt.figure(figsize=(13, 7.6))
    fig.patch.set_facecolor(BG)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 0.8], width_ratios=[1.25, 1])
    ax1 = fig.add_subplot(gs[:, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 1])

    style_ax(ax1, "Case Inventory", "133 route cases across 78 clips")
    vals = [cases[k] for k in case_order]
    labels = [k.replace("_", "\n") for k in case_order]
    x = np.arange(len(vals))
    colors = [TEAL, GRAY, AMBER, AMBER, BLUE, RED]
    bars = ax1.bar(x, vals, color=colors)
    ax1.set_ylabel("clips / cases", color=FG)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, color=FG, fontsize=9)
    ax1.set_ylim(0, max(vals) + 9)
    for b, v in zip(bars, vals):
        ax1.text(b.get_x() + b.get_width() / 2, v + 1, str(v),
                 ha="center", color=FG, fontsize=10, fontweight="bold")

    style_ax(ax2, "Window Routes", "334 coarse 3s windows")
    rvals = [routes[k] for k in route_order]
    rlabels = ["low-gap\nskip", "layout /\nscene cue", "action /\nagent cue"]
    rx = np.arange(len(rvals))
    rbars = ax2.bar(rx, rvals, color=[GRAY, TEAL, AMBER])
    ax2.set_xticks(rx)
    ax2.set_xticklabels(rlabels, color=FG, fontsize=9)
    ax2.set_ylim(0, max(rvals) + 35)
    for b, v in zip(rbars, rvals):
        ax2.text(b.get_x() + b.get_width() / 2, v + 5, str(v),
                 ha="center", color=FG, fontsize=10, fontweight="bold")

    ax3.set_facecolor(PANEL)
    for spine in ax3.spines.values():
        spine.set_color(GRID)
    ax3.set_xticks([])
    ax3.set_yticks([])
    ax3.set_title("Temporal Structure", color=FG, fontsize=16, fontweight="bold", loc="left", pad=10)
    stats = [
        ("external clips: scene/action rho < 0.5", f"{inv['external_type_shift_lt_0_5']}/60"),
        ("external clips: peaks at different timesteps", f"{inv['external_peak_apart']}/60"),
        ("top-1 concentration vs uniform timing", f"{inv['external_top1_vs_uniform_mean']:.2f}x"),
    ]
    y0 = 0.76
    for i, (label, value) in enumerate(stats):
        y = y0 - i * 0.28
        ax3.text(0.05, y, value, transform=ax3.transAxes, color=TEAL,
                 fontsize=22, fontweight="bold", va="center")
        ax3.text(0.38, y, label, transform=ax3.transAxes, color=FG,
                 fontsize=10.5, va="center")

    fig.suptitle("TRIBE Produces Actionable Routing State, Not A Single Score",
                 color=FG, fontsize=17, fontweight="bold", x=0.055, y=0.99, ha="left")
    fig.subplots_adjust(top=0.86, wspace=0.2, hspace=0.32)
    save(fig, "fig_blind_spot_router_inventory.png")


def negative_control(payload: dict) -> None:
    pro = payload["pro_priority_negative_result"]
    labels = ["TRIBE vs\npro AD", "VLM vs\npro AD", "Uniform vs\npro AD"]
    vals = [
        pro["tribe_vs_pro_mean"],
        pro["vlm_vs_pro_mean"],
        pro["uniform_vs_pro_mean"],
    ]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    style_ax(
        ax,
        "Negative Control: TRIBE Is Not A General Pro-AD Topic Model",
        "Cosine similarity to professional AD content-type profile, n=55",
    )
    bars = ax.bar(np.arange(3), vals, color=[TEAL, AMBER, GRAY])
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("cosine similarity", color=FG)
    ax.set_xticks(np.arange(3))
    ax.set_xticklabels(labels, color=FG)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", color=FG, fontsize=11, fontweight="bold")
    ax.text(
        0.02, 0.92,
        f"TRIBE - VLM = {pro['tribe_minus_vlm']:+.3f}; wins/losses = {pro['wins']}/{pro['losses']}",
        transform=ax.transAxes, color=RED, fontsize=11, fontweight="bold",
    )
    ax.text(
        0.02, 0.84,
        "Interpretation: keep TRIBE as localized routing, not holistic AD authorship.",
        transform=ax.transAxes, color=MUTED, fontsize=10,
    )
    save(fig, "fig_negative_control_pro_ad_priority.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.loads(VAL_JSON.read_text())
    scoring_leaderboard()
    matched_target_validation(payload)
    router_inventory(payload)
    negative_control(payload)


if __name__ == "__main__":
    main()
