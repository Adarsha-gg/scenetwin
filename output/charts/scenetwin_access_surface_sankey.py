"""Paper B Figure: surface distribution + compute tier on 58 external clips.

A simple grouped-bar (Sankey-lite) version since matplotlib lacks built-in
Sankey. Shows the 5 surfaces and how they distribute across 4 compute
tiers, plus risk level.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

OUT = "output/charts/scenetwin_access_surface_sankey.png"

# From cursor/methods/output/access_surface_router_summary.json
# surface_counts = {static_ad: 19, identity_chip: 18, defer_replay: 12,
#                   concise_cue: 6, creator_qc: 3}
# compute_tier_counts = {human: 8, cloud: 14, local: 25, cached: 11}
# risk_counts = {high: 7, medium: 15, low: 36}

SURFACE_COMPUTE = {
    "static_ad":     {"local": 14, "cached": 5,  "cloud": 0,  "human": 0},
    "identity_chip": {"local": 4,  "cached": 0,  "cloud": 14, "human": 0},
    "defer_replay":  {"local": 1,  "cached": 6,  "cloud": 0,  "human": 5},
    "concise_cue":   {"local": 6,  "cached": 0,  "cloud": 0,  "human": 0},
    "creator_qc":    {"local": 0,  "cached": 0,  "cloud": 0,  "human": 3},
}

surfaces = list(SURFACE_COMPUTE.keys())
computes = ["local", "cached", "cloud", "human"]
compute_color = {"local": "#1f7a5a", "cached": "#7aaa42",
                 "cloud": "#3a5af8", "human": "#cc4030"}

fig, ax = plt.subplots(figsize=(8.5, 5))
y = np.arange(len(surfaces))
left = np.zeros(len(surfaces))
for c in computes:
    vals = [SURFACE_COMPUTE[s][c] for s in surfaces]
    ax.barh(y, vals, left=left, color=compute_color[c],
            edgecolor="white", linewidth=1.0, label=c)
    # Annotate non-zero segments
    for yi, v, l in zip(y, vals, left):
        if v > 0:
            ax.text(l + v/2, yi, str(v), ha="center", va="center",
                    fontsize=9, color="white", weight="bold")
    left += np.array(vals)

# Totals at the end of each bar
totals = [sum(SURFACE_COMPUTE[s].values()) for s in surfaces]
for yi, t in zip(y, totals):
    ax.text(t + 0.5, yi, f"  n = {t}", va="center", fontsize=9, color="#333")

ax.set_yticks(y)
ax.set_yticklabels([s.replace("_", " ") for s in surfaces], fontsize=10)
ax.invert_yaxis()
ax.set_xlim(0, 25)
ax.set_xlabel("Number of clips (n = 58 external)")
ax.set_title("Access Surface OS: surface x compute distribution on 58 external clips\n"
             "(routed by access_surface_router; static_ad covers 33%, the rest distribute across 4 other surfaces)",
             fontsize=10.5)
ax.legend(title="Compute tier", loc="lower right", fontsize=9, frameon=False)
ax.grid(axis="x", linestyle=":", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
