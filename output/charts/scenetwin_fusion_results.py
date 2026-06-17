"""Negative-results fusion bar chart: every paper-baseline blend tested
fails to beat the 2-signal CLIP+ADQA ensemble.
"""
from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

OUT = "output/charts/scenetwin_fusion_results.png"
SRC = "cursor/papers/output/paper_fusion_leaderboard.csv"

df = pd.read_csv(SRC).sort_values("rho", ascending=True)

pretty = {
    "ensemble_baseline": "SceneTwin ensemble (CLIP+ADQA)",
    "semantic_core": "semantic_core (LLM+ADQA+VT)",
    "entity_action": "entity_action (ADQA+CRITIC+action)",
    "grid_best": "grid_best (5d weight search)",
    "paper_stack_v1": "paper_stack_v1 (6-feature blend)",
    "timing_semantic": "timing_semantic",
    "narrative_ground": "narrative_ground",
    "audit_no_ref": "audit_no_ref",
}
df["label"] = df["fusion"].map(pretty).fillna(df["fusion"])

# Color: ensemble = highlight, others = neutral
colors = ["#2a8a40" if f == "ensemble_baseline" else "#888a8c" for f in df["fusion"]]

fig, ax = plt.subplots(figsize=(8, 4.5))
bars = ax.barh(df["label"], df["rho"], color=colors, edgecolor="#444", linewidth=0.5)
for b, v in zip(bars, df["rho"]):
    ax.text(v + 0.005, b.get_y() + b.get_height()/2,
            f"{v:.3f}", va="center", fontsize=9)
ax.axvline(0.929, color="#2a8a40", linestyle="--", linewidth=1, alpha=0.7)
ax.set_xlabel("Spearman rho vs tier GT (n=72)")
ax.set_xlim(0.75, 0.96)
ax.set_title("Fusion ablation: paper-baseline blends do NOT beat the 2-signal ensemble\n"
             "(6 hand-engineered + grid-searched blends; in-benchmark 18 clips)",
             fontsize=10)
ax.grid(axis="x", linestyle=":", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
