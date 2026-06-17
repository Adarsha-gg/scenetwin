"""Per-category rho with bootstrap CIs on the 60-clip external set.

Paper A Figure: 'Cross-category generalization'.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

OUT = "output/charts/scenetwin_per_category_rho.png"
SRC = "cursor/output/external_ensemble_eval.csv"

ens = pd.read_csv(SRC)

rows = []
for cat, grp_cat in ens.groupby("category"):
    cat_vids = grp_cat["video_id"].unique()
    if len(cat_vids) < 2:
        continue
    grp_score = grp_cat["ensemble_mean_clip_top3"].values
    grp_gt    = grp_cat["gt"].values
    r_cat, _  = spearmanr(grp_score, grp_gt)
    cat_indices = {v: np.where(grp_cat["video_id"].values == v)[0] for v in cat_vids}
    boots = []
    rng = np.random.default_rng(42)
    for _ in range(2000):
        sample = rng.choice(cat_vids, size=len(cat_vids), replace=True)
        idx = np.concatenate([cat_indices[v] for v in sample])
        r, _ = spearmanr(grp_score[idx], grp_gt[idx])
        if not np.isnan(r):
            boots.append(r)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    rows.append({"category": cat, "n_clips": len(cat_vids), "rho": r_cat, "lo": lo, "hi": hi})

df = pd.DataFrame(rows).sort_values("rho", ascending=True)

fig, ax = plt.subplots(figsize=(8.0, 5.5))
y = np.arange(len(df))
# Error bars: distance from rho to CI bounds
err_low  = df["rho"].values - df["lo"].values
err_high = df["hi"].values - df["rho"].values
ax.errorbar(df["rho"], y, xerr=[err_low, err_high],
            fmt="o", color="#1f4e79", ecolor="#7f9bbd", capsize=4, markersize=7)
ax.set_yticks(y)
ax.set_yticklabels([f"{c}\n(n={n})" for c, n in zip(df["category"], df["n_clips"])], fontsize=9)
ax.axvline(0.873, color="#cc4030", linestyle="--", linewidth=1, label="overall external rho = 0.873")
ax.axvline(0.929, color="#2a8a40", linestyle="--", linewidth=1, label="in-benchmark rho = 0.929")
ax.set_xlabel("Spearman rho (CLIP+ADQA ensemble vs tier GT)")
ax.set_xlim(0.55, 1.02)
ax.set_title("Per-category generalization on 60 external clips\n(bootstrap 95% CI by video resampling, B=2000)", fontsize=11)
ax.grid(axis="x", linestyle=":", alpha=0.4)
ax.legend(loc="lower right", fontsize=8, frameon=False)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
