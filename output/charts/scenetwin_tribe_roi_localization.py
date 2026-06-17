"""TRIBE use-case chart: the AV-vs-A accessibility gap localizes to visual cortex.

Reads cursor/research/output/tribe_roi_gap_per_clip.csv (produced by
cursor/research/tribe_roi_gap_usecase.py) and renders per-ROI mean gap for the
in-bench and external corpora side by side, visual ROIs vs control ROIs.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "cursor" / "research" / "output" / "tribe_roi_gap_per_clip.csv"

VISUAL = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa",
          "retrosplenial_pos", "face_ffc", "body_eba_region",
          "motion_mt_complex", "lateral_object_loc"]
CONTROL = ["auditory_control", "language_control"]
PRETTY = {
    "early_visual_v1": "Early visual V1", "higher_visual_v2v3v4": "Higher visual V2-V4",
    "scene_ppa": "Scene (PPA)", "retrosplenial_pos": "Retrosplenial/spatial",
    "face_ffc": "Face (FFC)", "body_eba_region": "Body (EBA)",
    "motion_mt_complex": "Motion (MT+)", "lateral_object_loc": "Object",
    "auditory_control": "Auditory [ctrl]", "language_control": "Language [ctrl]",
}

df = pd.read_csv(CSV)
order = VISUAL + CONTROL

fig, ax = plt.subplots(figsize=(9, 5.5))
inb = df[df.corpus == "inbench"][order].mean()
ext = df[df.corpus == "external"][order].mean()

y = np.arange(len(order))[::-1]
h = 0.4
colors = ["#2b6cb0" if r in VISUAL else "#b04a2b" for r in order]
ax.barh(y + h/2, inb.values, height=h, color=colors, alpha=0.55, label="in-bench (18)")
ax.barh(y - h/2, ext.values, height=h, color=colors, alpha=1.0, label="external (60)")

ax.set_yticks(y)
ax.set_yticklabels([PRETTY[r] for r in order], fontsize=10)
ax.set_xlabel("AV-vs-A accessibility gap  (1 - cosine, time-averaged)")
ax.set_title("TRIBE: removing video diverges visual cortex, not auditory\n"
             "Gap concentrates in scene / spatial / early-visual ROIs; holds external (p=5e-5)",
             fontsize=11)
ax.axvline(df[df.corpus == "external"][CONTROL].mean().mean(), ls="--",
           color="#b04a2b", lw=1, alpha=0.7)
ax.legend(loc="lower right", frameon=False)
for spine in ("top", "right"):
    ax.spines[spine].set_visible(False)
fig.tight_layout()
out = Path(__file__).with_suffix(".png")
fig.savefig(out, dpi=150)
print(f"wrote {out}")
