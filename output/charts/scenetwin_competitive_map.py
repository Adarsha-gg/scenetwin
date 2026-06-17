"""Cost vs quality map: ensemble + 10 paper baselines + 3 frontier VLM judges.

Paper A figure for §6.1 headline competitive claim.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

OUT = "output/charts/scenetwin_competitive_map.png"

# Cost per (clip, tier) inference in USD (approximate; verified for VLMs,
# estimated for paper baselines as compute-fraction of CLIP/ADQA pipeline).
ENTRIES = [
    # (name, in_bench_rho, ext_rho, cost_per_call_usd, kind)
    ("SceneTwin ensemble (CLIP+ADQA)", 0.929, 0.873, 0.001, "ours"),
    ("ADQA v4 alone",                  0.789, 0.867, 0.0005, "baseline"),
    ("LLM-AD-Eval (AutoAD III)",       0.899, 0.857, 0.0001, "baseline"),
    ("CRITIC entity (AutoAD III)",     0.638, 0.613, 0.00005, "baseline"),
    ("Story recall (CoAD)",            0.703, None,  0.0001, "baseline"),
    ("Action coverage (AutoAD III)",   0.601, None,  0.0001, "baseline"),
    ("VT consistency (AVBench)",       0.768, None,  0.0001, "baseline"),
    ("Need-weighted CLIP (TRIBE)",     0.733, None,  0.0005, "baseline"),
    ("Multi-ref R@3",                  0.532, None,  0.00001, "leaky"),
    ("CoAD repetition (inv)",          -0.064, None, 0.00001, "leaky"),
    # VLM judges
    ("Claude Sonnet 4.6 VLM judge",    0.713, 0.715, 0.0318, "vlm"),
    ("GPT-5 VLM judge",                0.727, 0.739, 0.0263, "vlm"),
    ("Gemini 2.5 Pro VLM judge",       0.756, 0.734, 0.0131, "vlm"),
]

color_kind = {
    "ours":     "#2a8a40",
    "baseline": "#888a8c",
    "leaky":    "#cc8030",
    "vlm":      "#3a5af8",
}
marker_kind = {
    "ours":     "*",
    "baseline": "o",
    "leaky":    "x",
    "vlm":      "s",
}

fig, ax = plt.subplots(figsize=(9, 5.5))
for name, rho_in, rho_ext, cost, kind in ENTRIES:
    rho = rho_in  # in-bench is comparable across all entries
    ax.scatter(cost, rho, s=160 if kind == "ours" else 80,
               color=color_kind[kind], marker=marker_kind[kind],
               edgecolor="#222", linewidth=0.6, zorder=4, label=None)
    # Label placement: ours / vlm always shown; baselines suppressed if cluttered
    if kind in ("ours", "vlm") or "ADQA" in name or "LLM-AD-Eval" in name or "Multi-ref" in name:
        ax.annotate(name, (cost, rho),
                    xytext=(7, 0), textcoords="offset points",
                    fontsize=8.5, color=color_kind[kind], va="center")

ax.axhline(0.929, color="#2a8a40", linestyle="--", linewidth=1, alpha=0.5,
           label="SceneTwin ensemble rho = 0.929 (in-bench)")
ax.set_xscale("log")
ax.set_xlim(0.5e-5, 0.08)
ax.set_ylim(-0.15, 1.0)
ax.set_xlabel("Cost per (clip, tier) inference  (USD, log scale)")
ax.set_ylabel("Spearman rho vs tier GT  (in-benchmark, n=72)")
ax.set_title("Cost vs quality: SceneTwin ensemble beats 10 paper baselines and 3 frontier VLM-as-judges\n"
             "at trivial inference cost",
             fontsize=10.5)
ax.grid(linestyle=":", alpha=0.4)

from matplotlib.lines import Line2D
legend = [
    Line2D([0],[0], marker="*", color="w", markerfacecolor=color_kind["ours"],
           markeredgecolor="#222", markersize=12, label="Ours (CLIP+ADQA)"),
    Line2D([0],[0], marker="s", color="w", markerfacecolor=color_kind["vlm"],
           markeredgecolor="#222", markersize=9, label="Frontier VLM judge"),
    Line2D([0],[0], marker="o", color="w", markerfacecolor=color_kind["baseline"],
           markeredgecolor="#222", markersize=9, label="Paper baseline"),
    Line2D([0],[0], marker="x", color=color_kind["leaky"],
           markersize=9, label="Reference-leakage (not paper-usable)"),
]
ax.legend(handles=legend, loc="lower left", fontsize=9, frameon=False)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
