"""Fig 7 (hero) - brain-grounded steering: matched vs unmatched, restyled.

Recomputes deltas from the cross-judge per-question CSVs so the figure stays tied to disk.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import scenetwin_style as st

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "..", "cursor", "research", "output")

RUNS = [
    ("GPT-5 judge  ·  60 clips", "tribe_crossjudge_gpt5_perq.csv"),
    ("GPT-5 judge  ·  17 clips (non-headroom)", "tribe_crossjudge_opus_17_perq.csv"),
]


def load_pairs(path):
    by_key, matched_of = defaultdict(dict), {}
    with open(path) as fh:
        for r in csv.DictReader(fh):
            k = (r["video_id"], r["q_idx"])
            by_key[k][r["condition"]] = float(r["score"])
            matched_of[k] = int(r["matched"])
    diffs = {0: [], 1: []}
    for k, c in by_key.items():
        if "baseline" in c and "gap_targeted" in c:
            diffs[matched_of[k]].append(c["gap_targeted"] - c["baseline"])
    return diffs


def stat(d):
    a = np.asarray(d, float)
    mean, sd = a.mean(), a.std(ddof=0)
    rng = np.random.default_rng(0)
    boot = np.array([rng.choice(a, a.size, replace=True).mean() for _ in range(5000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return dict(mean=mean, d=(mean / sd if sd else 0), lo=lo, hi=hi,
                w=int((a > 0).sum()), l=int((a < 0).sum()), t=int((a == 0).sum()))


fig, ax = st.figure(w=8.6, h=5.4)
st.style_axes(ax)
width = 0.34
centers = [0, 1.2]
bbox = dict(boxstyle="round,pad=0.12", fc="white", ec="none")

for i, (label, fname) in enumerate(RUNS):
    diffs = load_pairs(os.path.join(DATA, fname))
    sm, su = stat(diffs[1]), stat(diffs[0])
    xm, xu = centers[i] - width / 2 - 0.03, centers[i] + width / 2 + 0.03
    for x, s, color, edge in [(xm, sm, st.OURS, st.OURS_HI), (xu, su, st.NEUTRAL, st.NEUTRAL_D)]:
        ax.bar(x, s["mean"], width, color=color, edgecolor=edge, linewidth=1.0, zorder=3)
        ax.errorbar(x, s["mean"], yerr=[[max(s["mean"] - s["lo"], 0)], [max(s["hi"] - s["mean"], 0)]],
                    fmt="none", ecolor=st.NEUTRAL_D, elinewidth=1.2, capsize=4,
                    capthick=1.2, zorder=4)
    # value label pinned just above each bar top (not the whisker), white bbox so it
    # stays readable where the CI line passes through
    ax.text(xm, sm["mean"] + 0.006, f"+{sm['mean']:.3f}", ha="center", va="bottom",
            fontsize=13, fontweight="bold", color=st.OURS_HI, zorder=6, bbox=bbox)
    ax.text(xu, max(su["mean"], 0.0) + 0.006, f"+{su['mean']:.3f}", ha="center", va="bottom",
            fontsize=13, fontweight="bold", color=st.NEUTRAL_D, zorder=6, bbox=bbox)
    # per-group stat lines in the bottom margin (one centered line each, no overlap)
    ax.text(centers[i], -0.030, f"matched   d = {sm['d']:.2f}   wins/losses/ties {sm['w']}/{sm['l']}/{sm['t']}",
            ha="center", va="top", fontsize=9, color=st.OURS_HI)
    ax.text(centers[i], -0.050, f"unmatched   d = {su['d']:.2f}   {su['w']}/{su['l']}/{su['t']}",
            ha="center", va="top", fontsize=9, color=st.NEUTRAL_D)
    ax.text(centers[i], -0.078, label, ha="center", va="top", fontsize=10.5,
            color=st.INK, fontweight="bold")

ax.axhline(0, color="#B7BCC2", linewidth=1.0, zorder=2)
ax.set_xlim(-0.55, 1.75)
ax.set_ylim(-0.095, 0.30)
ax.set_xticks([])
ax.set_ylabel("ADQA gain  (gap-targeted minus baseline)")
ax.set_yticks([0, 0.05, 0.10, 0.15, 0.20, 0.25])

# legend swatches, top-right, outside the bars
ax.add_patch(plt.Rectangle((0.78, 0.91), 0.03, 0.045, transform=ax.transAxes,
             facecolor=st.OURS, edgecolor=st.OURS_HI, clip_on=False))
ax.text(0.825, 0.93, "matched  (questions TRIBE flagged)", transform=ax.transAxes,
        va="center", fontsize=9.5, color=st.INK)
ax.add_patch(plt.Rectangle((0.78, 0.83), 0.03, 0.045, transform=ax.transAxes,
             facecolor=st.NEUTRAL, edgecolor=st.NEUTRAL_D, clip_on=False))
ax.text(0.825, 0.85, "unmatched  (control)", transform=ax.transAxes,
        va="center", fontsize=9.5, color=st.MUTE)

st.titles(ax,
          "Steering lands on the visual facts the brain flagged, and nowhere else",
          "Conditioning AD generation on TRIBE's blind-spot type. Cross-family judge "
          "(GPT-5 grades a different model). Whiskers show the 95% bootstrap CI.")
st.save(fig, "scenetwin_steering_v2")
