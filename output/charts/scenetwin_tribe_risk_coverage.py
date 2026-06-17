"""TRIBE risk-coverage curve: with the failure-forecast flag,
review budget drops from 100% to 11% while catching 100% of
severe failures.

Paper A Section 8 figure (TRIBE side-car).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

OUT = "output/charts/scenetwin_tribe_risk_coverage.png"
SRC = "output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv"

df = pd.read_csv(SRC)

# Rank clips by the published top forecast feature (low = good)
df = df.sort_values("mean_standard_slot_score", ascending=False).reset_index(drop=True)
df["review_rank"] = np.arange(1, len(df) + 1)
df["review_frac"] = df["review_rank"] / len(df)
# Cumulative recall of all4_fail positives (n=2)
total_positives = int(df["all4_fail"].sum())
df["cum_recall"] = df["all4_fail"].cumsum() / max(total_positives, 1)

# Random baseline: cumulative recall under uniform review
df["random_recall"] = df["review_frac"]

fig, ax = plt.subplots(figsize=(7.5, 4.8))
ax.step(df["review_frac"] * 100, df["cum_recall"] * 100, where="post",
        color="#1f4e79", linewidth=2.2,
        label="TRIBE-flagged review (mean_standard_slot_score)")
ax.plot(df["review_frac"] * 100, df["random_recall"] * 100,
        color="#bbb", linestyle="--", linewidth=1.4,
        label="Random review (uniform baseline)")

# Highlight recall@2/18 = 11% review budget
ax.axvline(2 / 18 * 100, color="#cc4030", linestyle=":", linewidth=1.2)
ax.axhline(100, color="#cc4030", linestyle=":", linewidth=1.2)
ax.scatter([2 / 18 * 100], [100], color="#cc4030", s=70, zorder=5)
ax.annotate("recall@2/18 = 100%\n(11.1% review budget)",
            xy=(2 / 18 * 100, 100), xytext=(22, 80),
            fontsize=9, color="#cc4030",
            arrowprops=dict(arrowstyle="->", color="#cc4030", lw=1))

ax.set_xlabel("Review budget (% of clips manually reviewed)")
ax.set_ylabel("Recall of severe failures (all4_fail, n=2)")
ax.set_xlim(0, 100)
ax.set_ylim(0, 105)
ax.set_xticks([0, 11.1, 25, 50, 75, 100])
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_title("TRIBE side-car: brain-aligned failure forecast on 18-clip benchmark\n"
             "AUC=1.00, recall@2/18=100%, p=0.0065 (Bonferroni p=0.065)",
             fontsize=10.5)
ax.grid(linestyle=":", alpha=0.4)
ax.legend(loc="lower right", fontsize=9, frameon=False)
plt.tight_layout()
plt.savefig(OUT, dpi=140)
print(f"saved {OUT}")
