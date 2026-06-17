"""Metric pairwise correlation heatmap — paper A 'related work' figure.

Shows 10 reference-free metrics + our ensemble, ordered by clustering.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

OUT = "output/charts/scenetwin_metric_correlation_heatmap.png"
SRC = "cursor/papers/output/metric_correlations.csv"

df = pd.read_csv(SRC)
metrics = sorted(set(df["metric_a"]) | set(df["metric_b"]))
n = len(metrics)
mat = np.eye(n)
idx = {m: i for i, m in enumerate(metrics)}
for _, r in df.iterrows():
    i, j = idx[r["metric_a"]], idx[r["metric_b"]]
    mat[i, j] = r["rho"]
    mat[j, i] = r["rho"]

# Hierarchical cluster ordering (1 - rho as distance)
dist = 1 - np.abs(mat)
np.fill_diagonal(dist, 0)
condensed = squareform(dist, checks=False)
Z = linkage(condensed, method="average")
order = leaves_list(Z)
metrics_ord = [metrics[i] for i in order]
mat_ord = mat[np.ix_(order, order)]

# Pretty labels
pretty = {
    "ensemble": "SceneTwin ensemble",
    "llm_ad_eval": "LLM-AD-Eval",
    "adqa_v4": "ADQA v4",
    "vt_consistency": "VT consistency",
    "need_weighted_clip": "Need-weighted CLIP",
    "story_recall": "Story recall",
    "critic_entity": "CRITIC entity",
    "action_coverage": "Action coverage",
    "multi_ref_r3": "Multi-ref R@3",
    "coad_repetition": "CoAD repetition",
    "coad_repetition_inv": "CoAD repetition (inv)",
    "timing_g7g8": "Timing G7/G8",
}
labels = [pretty.get(m, m) for m in metrics_ord]

fig, ax = plt.subplots(figsize=(7.5, 6.5))
im = ax.imshow(mat_ord, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")
ax.set_xticks(range(len(labels)))
ax.set_yticks(range(len(labels)))
ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8.5)
ax.set_yticklabels(labels, fontsize=8.5)

# Annotate cells with rho value
for i in range(len(labels)):
    for j in range(len(labels)):
        if i == j: continue
        val = mat_ord[i, j]
        if abs(val) > 0.05:
            color = "white" if abs(val) > 0.6 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)

ax.set_title("Pairwise Spearman rho among 11 reference-free metrics (18-clip benchmark, n=72)\n"
             "Hierarchical-clustered ordering", fontsize=10)
cbar = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.03)
cbar.set_label("Spearman rho", fontsize=9)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
