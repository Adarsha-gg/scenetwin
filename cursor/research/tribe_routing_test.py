"""Can TRIBE's typed visual DEMAND route between CLIP and ADQA per clip?

Premise: CLIP measures visual-spatial grounding; ADQA measures factual QA.
If TRIBE says a clip's missing visual info is scene/spatial vs agent/action,
that *type* might predict which signal ranks the clip's tiers better.

Targets (per external clip, from per_clip_clip_vs_adqa_decomposition.csv):
  r_ensemble  within-clip Spearman of the ensemble vs gt  (per-clip quality)
  clip_lift   r_clip - r_adqa  (>0 => CLIP beats ADQA on this clip)

TRIBE demand features (P_AV vs P_A; a property of the CLIP, not the AD):
  scene_block, agent_block, scene_minus_agent, total_demand
  + temporal concentration (top1_share) from the spatiotemporal run.

Honest bar: a feature must (a) correlate at p<0.05 AFTER Bonferroni over the
features tested, and (b) actually improve routed rho over the fixed ensemble.
This same calibration question died for 12 *scalar* features (all p>0.16,
role-analysis); we are retesting with the new typed/temporal features.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "cursor/research/output"
SCENE = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa", "retrosplenial_pos"]
AGENT = ["face_ffc", "body_eba_region", "motion_mt_complex", "lateral_object_loc"]


def build():
    roi = pd.read_csv(R / "tribe_roi_gap_per_clip.csv")
    man = pd.read_csv(ROOT / "cursor/research/output/tribe_tensors/manifest.csv")[["clip_key", "video_id"]]
    dec = pd.read_csv(R / "per_clip_clip_vs_adqa_decomposition.csv")
    st = pd.read_csv(R / "tribe_spatiotemporal_per_clip.csv")[["clip_key", "top1_share", "T"]]
    roi = roi.merge(man, on="clip_key", how="left").merge(st, on="clip_key", how="left")
    roi["scene_block"] = roi[SCENE].mean(axis=1)
    roi["agent_block"] = roi[AGENT].mean(axis=1)
    roi["scene_minus_agent"] = roi.scene_block - roi.agent_block
    roi["total_demand"] = roi[SCENE + AGENT].mean(axis=1)
    ext = roi[roi.corpus == "external"]
    return ext.merge(dec, on="video_id", how="inner")


def main():
    j = build()
    feats = ["scene_block", "agent_block", "scene_minus_agent",
             "total_demand", "top1_share", "accessibility_gap"]
    n_feat = len(feats)
    for target in ["clip_lift", "r_ensemble"]:
        print(f"\n=== TRIBE demand vs {target}  (n={len(j)}, Bonferroni x{n_feat}) ===")
        for f in feats:
            r, p = stats.spearmanr(j[f], j[target])
            flag = "  <-- survives" if p * n_feat < 0.05 else ""
            print(f"  {f:20s} rho={r:+.3f}  p={p:.3f}  p_bonf={min(p*n_feat,1):.3f}{flag}")

    # routing simulation: on clips where scene_minus_agent is high, trust CLIP;
    # else trust ADQA. Does that beat using the ensemble everywhere?
    print("\n=== routing simulation on clip_lift ===")
    print("  baseline mean r_ensemble :", f"{j.r_ensemble.mean():.4f}")
    print("  baseline mean r_clip     :", f"{j.r_clip.mean():.4f}")
    print("  baseline mean r_adqa     :", f"{j.r_adqa.mean():.4f}")
    best = None
    for q in [0.33, 0.5, 0.67]:
        thr = j.scene_minus_agent.quantile(q)
        route_clip = j.scene_minus_agent >= thr           # high scene demand -> CLIP
        routed = np.where(route_clip, j.r_clip, j.r_adqa)
        m = routed.mean()
        print(f"  route@q{int(q*100)}: scene>=thr->CLIP else ADQA  mean r={m:.4f}  "
              f"(CLIP on {route_clip.sum()}/{len(j)})")
        best = max(best or 0, m)
    # oracle ceiling: per clip pick the better of clip/adqa
    oracle = np.maximum(j.r_clip, j.r_adqa).mean()
    print(f"  ORACLE (pick better per clip): {oracle:.4f}")
    print(f"  best TRIBE-routed: {best:.4f}   ensemble: {j.r_ensemble.mean():.4f}")


if __name__ == "__main__":
    main()
