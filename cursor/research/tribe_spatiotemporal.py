"""Spatiotemporal typing: within a clip, does the *type* of lost visual info
shift over time? Uses the per-timestep axis (the expensive part of the tensors,
untouched until now).

For each clip and each timestep t:
  scene_gap(t) = 1 - cos(P_AV[t, scene_verts], P_A[t, scene_verts])
  agent_gap(t) = 1 - cos(P_AV[t, agent_verts], P_A[t, agent_verts])

If scene_gap(t) and agent_gap(t) peak at *different* moments (low / negative
within-clip correlation), then the dominant lost content type changes through
the clip -> moment-level, typed authoring guidance is possible.

Also reports temporal concentration: is the gap peaky (localizable to a moment)
or flat? top-1 timestep share vs the uniform-null 1/T.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import tribe_tensors_load as T

ROOT = Path(__file__).resolve().parents[2]
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"
SCENE = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa", "retrosplenial_pos"]
AGENT = ["face_ffc", "body_eba_region", "motion_mt_complex", "lateral_object_loc"]


def verts_for(rois):
    m = pd.read_csv(MASK)
    return m[m.roi.isin(rois)].vertex.to_numpy()


def block_gap_traj(pav, pa, verts):
    """(T,) gap restricted to `verts`, per timestep."""
    out = np.zeros(pav.shape[0])
    for t in range(pav.shape[0]):
        a = pav[t, verts].astype(float); b = pa[t, verts].astype(float)
        out[t] = 1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
    return out


def main():
    sv, av = verts_for(SCENE), verts_for(AGENT)
    man = T.load_manifest()
    rows = []
    for _, r in man.iterrows():
        try:
            t, meta = T.load_clip(r.clip_key)
        except FileNotFoundError:
            continue
        pav, pa = t["P_AV"], t["P_A"]
        Tn = pav.shape[0]
        if Tn < 4:
            continue
        s = block_gap_traj(pav, pa, sv)
        a = block_gap_traj(pav, pa, av)
        # within-clip temporal correlation of scene-loss vs agent-loss
        rho = np.corrcoef(s, a)[0, 1] if s.std() > 0 and a.std() > 0 else np.nan
        # do they peak at different timesteps?
        peak_apart = int(s.argmax() != a.argmax())
        # temporal concentration of total (scene+agent) gap
        g = s + a
        top1 = g.max() / g.sum()
        rows.append({"clip_key": r.clip_key, "corpus": meta.get("corpus"),
                     "T": Tn, "scene_agent_time_rho": rho,
                     "peak_apart": peak_apart, "top1_share": top1,
                     "uniform_null": 1.0 / Tn})
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "cursor/research/output/tribe_spatiotemporal_per_clip.csv", index=False)

    for label, sub in [("ALL", df), ("IN-BENCH", df[df.corpus == "inbench"]),
                        ("EXTERNAL", df[df.corpus == "external"])]:
        rho = sub.scene_agent_time_rho.dropna()
        print(f"\n=== {label} (n={len(sub)}) ===")
        print(f"  scene-loss vs agent-loss within-clip time corr: "
              f"mean rho={rho.mean():+.3f}  median={rho.median():+.3f}  "
              f"frac<0.5={(rho<0.5).mean()*100:.0f}%")
        print(f"  scene & agent peak at DIFFERENT timesteps: {sub.peak_apart.mean()*100:.0f}% of clips")
        print(f"  temporal concentration: top-1 share={sub.top1_share.mean():.3f} "
              f"vs uniform null={sub.uniform_null.mean():.3f} "
              f"(ratio {(sub.top1_share/sub.uniform_null).mean():.2f}x)")


if __name__ == "__main__":
    main()
