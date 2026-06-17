"""Fig 4 - fusion ablation, restyled. Horizontal bars, ours on top."""
from __future__ import annotations

import scenetwin_style as st

# (label, rho, is_ours)
ROWS = [
    ("SceneTwin  (CLIP + ADQA)", 0.928, True),
    ("semantic core  (LLM + ADQA + VT)", 0.887, False),
    ("entity + action", 0.816, False),
    ("grid-searched blend", 0.810, False),
    ("six-feature stack", 0.794, False),
    ("timing + semantic", 0.785, False),
    ("narrative + grounding", 0.781, False),
    ("reference-free audit blend", 0.776, False),
]
ROWS = ROWS[::-1]  # plot bottom-up so ours ends on top

fig, ax = st.figure(w=8.4, h=4.8)
ax.grid(axis="x"); ax.grid(axis="y", visible=False)
st.style_axes(ax)

ys = range(len(ROWS))
for y, (label, rho, ours) in zip(ys, ROWS):
    ax.barh(y, rho, height=0.62, color=st.OURS if ours else st.NEUTRAL,
            edgecolor=st.OURS_HI if ours else st.NEUTRAL_D, lw=1.0, zorder=3)
    ax.text(rho + 0.003, y, f"{rho:.3f}", va="center", ha="left",
            fontsize=10.5, fontweight="bold" if ours else "normal",
            color=st.OURS_HI if ours else st.NEUTRAL_D)

ax.axvline(0.928, color=st.OURS, ls=(0, (4, 3)), lw=1.4, zorder=2)
ax.set_yticks(list(ys))
ax.set_yticklabels([r[0] for r in ROWS], fontsize=10.5)
for tick, r in zip(ax.get_yticklabels(), ROWS):
    tick.set_color(st.INK if r[2] else st.MUTE)
    tick.set_fontweight("bold" if r[2] else "normal")
ax.set_xlim(0.75, 0.96)
ax.set_xlabel("Spearman ρ  vs quality tiers  (in-benchmark, n = 72)")

# left-align the title to the figure (this chart has long y labels, so plot-left is far in)
fig.suptitle("Stacking more metrics does not beat two signals",
             x=0.012, y=1.06, ha="left", fontsize=14, fontweight="bold", color=st.INK)
fig.text(0.012, 1.005, "Six engineered fusions of up to six published metrics. None passes "
         "the dashed SceneTwin line. Parsimony wins.", ha="left", fontsize=10, color=st.MUTE)
fig.tight_layout(rect=[0, 0, 1, 0.95])
st.save(fig, "scenetwin_fusion_v2")
