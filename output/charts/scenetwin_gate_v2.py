"""Fig 5 - hallucination gate, restyled as an AUC summary (reads gate_summary.json)."""
from __future__ import annotations

import json
import os

import scenetwin_style as st

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "..", "..", "cursor", "output", "gate_summary.json")))

# (label, json key, role)
ROWS = [
    ("Grader-free CLIP grounding-drop", "with_reference_clip_drop", "ours"),
    ("CLIP + ADQA fused  (uses a grader)", "with_reference_clip_plus_adqa", "vlm"),
    ("Zero-reference, single AD", "zero_reference_claim_gate", "danger"),
]
COLOR = {"ours": (st.OURS, st.OURS_HI), "vlm": (st.VLM, "#2742A8"), "danger": (st.DANGER, "#8E2E36")}

fig, ax = st.figure(w=8.6, h=4.0)
ax.grid(axis="x"); ax.grid(axis="y", visible=False)
st.style_axes(ax)

ys = list(range(len(ROWS)))[::-1]
for y, (label, key, role) in zip(ys, ROWS):
    g = d[key]
    auc = g["auc"]
    rec = g.get("recall_at_10pct_fpr")
    fc, ec = COLOR[role]
    ax.barh(y, auc, height=0.58, color=fc, edgecolor=ec, lw=1.0, zorder=3)
    note = f"AUC {auc:.2f}"
    if rec is not None:
        note += f"   ·   catches {rec*100:.0f}% at 10% false alarm"
    ax.text(auc + 0.006, y, note, va="center", ha="left", fontsize=11,
            fontweight="bold" if role == "ours" else "normal",
            color=ec if role != "vlm" else st.VLM)
    ax.text(0.012, y + 0.34, label, va="bottom", ha="left", fontsize=11.5,
            color=st.INK if role == "ours" else st.MUTE,
            fontweight="bold" if role == "ours" else "normal")

ax.axvline(0.5, color=st.NEUTRAL_D, ls=(0, (4, 3)), lw=1.3, zorder=2)
ax.text(0.5, len(ROWS) - 0.45, "chance", ha="center", va="bottom", fontsize=9.5, color=st.NEUTRAL_D)
ax.set_yticks([])
ax.set_xlim(0.4, 1.0)
ax.set_ylim(-0.6, len(ROWS) - 0.2)
ax.set_xlabel("detection AUC  (catch a hallucinated AD vs flag a truthful one)")

st.titles(ax,
          "A grader-free signal catches most hallucinations",
          "Same-length fabricated facts vs faithful paraphrase, 60 unseen clips. The "
          "deployable gate uses CLIP grounding only, no model judge.")
st.save(fig, "scenetwin_gate_v2")
