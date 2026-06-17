"""Fig 8 - neural review triage, restyled. Two-group comparison of the per-clip brain gap."""
from __future__ import annotations

import scenetwin_style as st

# from cursor/findings/tribe-clip-level-triage.md (ADQA-only layer, 60 OOD clips)
GAP_FAIL = 0.267   # clips the metric misorders
GAP_OK   = 0.158   # clips the metric gets right
AUC = 0.79
P = 0.0018

fig, ax = st.figure(w=7.2, h=4.6)
st.style_axes(ax)

x = [0, 1]
vals = [GAP_OK, GAP_FAIL]
colors = [(st.NEUTRAL, st.NEUTRAL_D), (st.DANGER, "#8E2E36")]
labels = ["metric ordered\nthe clip correctly", "metric MISORDERED\nthe clip"]
for xi, v, (fc, ec), lab in zip(x, vals, colors, labels):
    ax.bar(xi, v, width=0.5, color=fc, edgecolor=ec, lw=1.0, zorder=3)
    ax.text(xi, v + 0.006, f"{v:.2f}", ha="center", va="bottom", fontsize=13,
            fontweight="bold", color=ec)
    ax.text(xi, -0.022, lab, ha="center", va="top", fontsize=10.5, color=st.INK)

ax.set_xticks([])
ax.set_xlim(-0.55, 1.55)
ax.set_ylim(0, 0.33)
ax.set_ylabel("brain accessibility gap  (per clip)")

# AUC callout
ax.text(0.5, 0.305, f"separates the two groups at AUC {AUC:.2f}   (p = {P})",
        ha="center", va="center", fontsize=11, fontweight="bold", color=st.OURS_HI,
        bbox=dict(boxstyle="round,pad=0.35", fc=st.OURS_SOFT if hasattr(st, "OURS_SOFT") else "#E7F2F0", ec=st.OURS, lw=1.2))

st.titles(ax,
          "The brain gap flags which clips the metric will get wrong",
          "Per-clip signal, 60 unseen clips. Route the highest-gap clips to human review: "
          "the top 20% catch 60% of all mis-orderings.")
st.save(fig, "scenetwin_triage_v2")
