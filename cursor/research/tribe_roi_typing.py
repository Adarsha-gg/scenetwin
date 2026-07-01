"""Decisive test for the TRIBE use-case: is the per-ROI accessibility-gap
profile clip-specific (a *typing* signal) or just the scalar accessibility_gap
rescaled across regions?

Reads cursor/research/output/tribe_roi_gap_per_clip.csv (from
tribe_roi_gap_usecase.py). Verdict lives in the variance decomposition:
if the clip x ROI interaction term dominates, different clips lose visual
information in different regions and a single scalar cannot represent it.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "cursor" / "research" / "output" / "tribe_roi_gap_per_clip.csv"

VIS_SCENE = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa", "retrosplenial_pos"]
VIS_AGENT = ["face_ffc", "body_eba_region", "motion_mt_complex", "lateral_object_loc"]
VIS = VIS_SCENE + VIS_AGENT


def main() -> None:
    df = pd.read_csv(CSV)

    print("=== (1) redundancy with scalar accessibility_gap (Pearson r) ===")
    for r in VIS + ["auditory_control", "language_control"]:
        print(f"  {r:24s} {np.corrcoef(df[r], df.accessibility_gap)[0, 1]:+.3f}")

    M = df[VIS].to_numpy()
    nC, nR = M.shape

    print("\n=== (2) dominant lost visual ROI per clip ===")
    dom = pd.Series([VIS[i] for i in M.argmax(1)])
    print("  " + str(dom.value_counts().to_dict()))

    df["scene_block"] = df[VIS_SCENE].mean(axis=1)
    df["agent_block"] = df[VIS_AGENT].mean(axis=1)
    df["scene_minus_agent"] = df.scene_block - df.agent_block
    print("\n=== (3) scene-minus-agent gap by category (n>=4) ===")
    g = (df.groupby("category")["scene_minus_agent"].agg(["mean", "count"])
         .query("count>=4").sort_values("mean", ascending=False))
    print(g.to_string())

    # two-way (clip, ROI) variance decomposition
    grand = M.mean()
    clip_eff = M.mean(axis=1, keepdims=True) - grand
    roi_eff = M.mean(axis=0, keepdims=True) - grand
    resid = M - grand - clip_eff - roi_eff
    tot = ((M - grand) ** 2).sum()
    ss_clip = (clip_eff[:, 0] ** 2).sum() * nR
    ss_roi = (roi_eff[0] ** 2).sum() * nC
    ss_res = (resid ** 2).sum()
    print("\n=== (4) variance decomposition of per-(clip,ROI) gap ===")
    print(f"  clip   (global magnitude / the scalar):  {ss_clip/tot*100:5.1f}%")
    print(f"  ROI    (fixed anatomy):                  {ss_roi/tot*100:5.1f}%")
    print(f"  clipxROI (clip-specific typing):         {ss_res/tot*100:5.1f}%")


if __name__ == "__main__":
    main()
