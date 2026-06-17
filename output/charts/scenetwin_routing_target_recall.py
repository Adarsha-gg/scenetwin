"""Paper B Figure: per-dimension target-recall vs static-AD-only baseline.

Shows the 5 routing dimensions, each with target-recall measured on 58
external clips, contrasted with a static-AD-only baseline at 0%.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

OUT = "output/charts/scenetwin_routing_target_recall.png"

DIMS = [
    ("Evidence sidecar\n(any sidecar emitted)",       1.000, "Cluster I (UniTime / T*)"),
    ("Assistant mode\n(non-plain assist routed)",     0.963, "Cluster G (Proactive Q)"),
    ("Surface\n(high-collision -> not static)",       0.917, "Cluster E (CustomAD)"),
    ("Task loop\n(needs task affordance)",            0.889, "Cluster H (Vid2Coach)"),
]

names    = [d[0] for d in DIMS]
recalls  = [d[1] for d in DIMS]
clusters = [d[2] for d in DIMS]

fig, ax = plt.subplots(figsize=(8.5, 5))
y = np.arange(len(DIMS))
bars = ax.barh(y, [r*100 for r in recalls], color="#1f4e79", edgecolor="#222", linewidth=0.6)
for b, r, c in zip(bars, recalls, clusters):
    ax.text(r*100 + 1, b.get_y() + b.get_height()/2,
            f" {r*100:.1f}%   ({c})", va="center", fontsize=9)

# Static-AD-only baseline line (always 0% recall on these targets)
ax.axvline(0, color="#cc4030", linestyle="--", linewidth=1.5, label="static-AD-only baseline (0%)")

ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=9.5)
ax.invert_yaxis()
ax.set_xlim(-3, 120)
ax.set_xlabel("Target recall on 58 external clips (%)")
ax.set_title("Access Surface OS: routing target recall per dimension\n"
             "(each dimension grounded in a distinct prior-art cluster)",
             fontsize=11)
ax.grid(axis="x", linestyle=":", alpha=0.4)
ax.legend(loc="lower right", fontsize=9, frameon=False)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
