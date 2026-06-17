"""Fig 2 - corrected ladder, restyled. Two panels: rho and % correctly ordered."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import scenetwin_style as st

GROUPS = ["Benchmark\n(in-domain)", "VATEX-60\n(out-of-distribution)"]
RHO = {"4tier": [0.93, 0.87], "3tier": [0.95, 0.95]}
ORD = {"4tier": [83, 50], "3tier": [94, 97]}

st.use()
fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.8))
x = np.arange(2)
w = 0.34


def panel(ax, before, after, ymax, fmt, ylabel):
    st.style_axes(ax)
    ax.bar(x - w / 2, before, w, color=st.NEUTRAL, edgecolor=st.NEUTRAL_D, lw=1.0, zorder=3)
    ax.bar(x + w / 2, after, w, color=st.OURS, edgecolor=st.OURS_HI, lw=1.0, zorder=3)
    for xi, b, a in zip(x, before, after):
        ax.text(xi - w / 2, b + ymax * 0.012, fmt(b), ha="center", va="bottom",
                fontsize=10.5, color=st.NEUTRAL_D, fontweight="bold")
        ax.text(xi + w / 2, a + ymax * 0.012, fmt(a), ha="center", va="bottom",
                fontsize=10.5, color=st.OURS_HI, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(GROUPS, fontsize=10, color=st.INK)
    ax.set_ylim(0, ymax)
    ax.set_ylabel(ylabel)
    return ax


a0 = panel(axes[0], RHO["4tier"], RHO["3tier"], 1.12, lambda v: f"{v:.2f}", "Spearman ρ")
a0.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
a1 = panel(axes[1], ORD["4tier"], ORD["3tier"], 118, lambda v: f"{v:.0f}%", "clips correctly ordered")
a1.set_yticks([0, 25, 50, 75, 100])

# hero callout: the OOD ordering jump 50 -> 97
xj = 1
a1.annotate("", xy=(xj + w / 2, 97), xytext=(xj - w / 2, 50),
            arrowprops=dict(arrowstyle="-|>", color=st.HIGHLIGHT, lw=2.2,
                            connectionstyle="arc3,rad=-0.25"), zorder=6)
a1.text(xj, 74, "+47 pts", ha="center", va="center", fontsize=11, fontweight="bold",
        color="#B5791F", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=st.HIGHLIGHT, lw=1.2))

# shared legend, top, outside both panels
import matplotlib.patches as mp
fig.legend(handles=[
    mp.Patch(fc=st.NEUTRAL, ec=st.NEUTRAL_D, label="4-tier ladder (with the broken rung)"),
    mp.Patch(fc=st.OURS, ec=st.OURS_HI, label="3-tier ladder (corrected)"),
], loc="upper center", ncol=2, fontsize=10, frameon=False, bbox_to_anchor=(0.5, 1.005))

fig.suptitle("Fixing a broken benchmark rung closes the generalization gap",
             x=0.012, y=1.12, ha="left", fontsize=14, fontweight="bold", color=st.INK)
fig.text(0.012, 1.05, "The 'longest crowd caption' tier graded word count, not quality. "
         "Removing it, out-of-distribution matches in-domain.",
         ha="left", fontsize=10, color=st.MUTE)
fig.tight_layout(rect=[0, 0, 1, 0.92])
st.save(fig, "scenetwin_corrected_ladder_v2")
