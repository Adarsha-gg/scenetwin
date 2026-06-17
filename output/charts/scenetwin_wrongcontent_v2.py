"""Fig 6 - wrong-content gate, restyled as a 1-D separation (reads wrong_content_global_gate.json)."""
from __future__ import annotations

import json
import os

import matplotlib.pyplot as plt
import scenetwin_style as st

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "..", "..", "cursor", "output", "wrong_content_global_gate.json")))
sep = d["raw_separation"]
loco = d["leave_one_clip_out"]

fig, ax = st.figure(w=8.6, h=4.2)
ax.grid(axis="x"); ax.grid(axis="y", visible=False)
st.style_axes(ax)

# threshold band (LOCO range), amber
ax.axvspan(loco["T_min"], loco["T_max"], color=st.AMBER_SOFT if hasattr(st, "AMBER_SOFT") else "#FBF1DC", zorder=1)
ax.axvline(loco["T_median"], color=st.HIGHLIGHT, lw=2.0, zorder=4)

# two group ranges with mean markers
def band(y, lo, hi, mean, color, edge, label):
    ax.plot([lo, hi], [y, y], color=color, lw=10, solid_capstyle="round", alpha=0.5, zorder=3)
    ax.scatter([mean], [y], s=160, color=color, edgecolor=edge, lw=1.4, zorder=5)
    ax.text(mean, y + 0.22, f"mean {mean:.2f}", ha="center", va="bottom", fontsize=10.5,
            fontweight="bold", color=edge)
    ax.text(0.015, y, label, ha="left", va="center", fontsize=12, fontweight="bold", color=edge)

band(1.0, sep["legit_min"], 0.40, sep["legit_mean"], st.OURS, st.OURS_HI, "")
band(0.0, 0.0, sep["cross_max"], sep["cross_mean"], st.DANGER, "#8E2E36", "")

ax.text(0.015, 1.0, "Legitimate AD", ha="left", va="center", fontsize=12.5, fontweight="bold",
        color=st.OURS_HI, transform=ax.get_yaxis_transform())
ax.text(0.015, 0.0, "Wrong-clip AD", ha="left", va="center", fontsize=12.5, fontweight="bold",
        color="#8E2E36", transform=ax.get_yaxis_transform())

# threshold annotation
ax.annotate(f"single threshold\ncatches {loco['catch_rate']*100:.0f}%  ·  {loco['false_alarm_rate']*100:.0f}% false alarm",
            xy=(loco["T_median"], 0.5), xytext=(loco["T_median"] + 0.055, 0.62),
            fontsize=10.5, color="#B5791F", fontweight="bold",
            arrowprops=dict(arrowstyle="-|>", color=st.HIGHLIGHT, lw=1.8))

ax.set_yticks([])
ax.set_ylim(-0.5, 1.5)
ax.set_xlim(0, 0.42)
ax.set_xlabel("raw CLIP visual grounding  (unnormalized, no reference)")

st.titles(ax,
          "One threshold separates 'describes the wrong clip' from real AD",
          "Raw CLIP grounding on a single description. No candidate pool, no normalization, "
          "no human reference. 60 wrong-clip vs 180 legitimate ADs.")
st.save(fig, "scenetwin_wrongcontent_v2")
