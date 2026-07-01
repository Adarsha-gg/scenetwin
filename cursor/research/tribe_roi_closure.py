"""Does the audio DESCRIPTION restore the visual brain response, per region?

Three counterfactual predictions per clip:
  P_AV  audio + video        (target: full scene)
  P_A   audio only           (visual info missing)
  P_AD  audio + description   (does the AD substitute for the video?)

For each ROI:
  gap_A  = 1 - cos(mean_t P_AV[roi], mean_t P_A[roi])    # gap left by audio only
  gap_AD = 1 - cos(mean_t P_AV[roi], mean_t P_AD[roi])   # gap left after the AD
  closure = (gap_A - gap_AD) / gap_A                      # frac of visual gap the AD restores

closure > 0  -> AD moves the response toward audiovisual (good)
closure < 0  -> AD moves it away

Closure at the scalar/global level is a KILLED branch (it ranked shorter AD
above pro AD). This asks the per-region version, which was never tested:
does the AD at least close the gap in the scene/spatial ROIs that carry it?
"""
from pathlib import Path

import numpy as np
import pandas as pd

import tribe_tensors_load as T

ROOT = Path(__file__).resolve().parents[2]
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"
VIS_SCENE = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa", "retrosplenial_pos"]
VIS_AGENT = ["face_ffc", "body_eba_region", "motion_mt_complex", "lateral_object_loc"]
CONTROL = ["auditory_control", "language_control"]
ALL = VIS_SCENE + VIS_AGENT + CONTROL


def roi_index():
    m = pd.read_csv(MASK)
    m = m[m.roi != "_unassigned_padding"]
    return {roi: g.vertex.to_numpy() for roi, g in m.groupby("roi")}


def gap(p_av, p_x, verts):
    a = p_av.mean(axis=0)[verts].astype(float)
    b = p_x.mean(axis=0)[verts].astype(float)
    return 1.0 - float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def main():
    idx = roi_index()
    man = T.load_manifest()
    rows = []
    for _, r in man.iterrows():
        try:
            t, meta = T.load_clip(r.clip_key)
        except FileNotFoundError:
            continue
        if "P_AD" not in t:
            continue
        pav, pa, pad = t["P_AV"], t["P_A"], t["P_AD"]
        rec = {"clip_key": r.clip_key, "corpus": meta.get("corpus"),
               "category": meta.get("category")}
        for roi, v in idx.items():
            gA = gap(pav, pa, v)
            gAD = gap(pav, pad, v)
            rec[f"clos_{roi}"] = (gA - gAD) / (gA + 1e-9)
        rows.append(rec)
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "cursor/research/output/tribe_roi_closure_per_clip.csv", index=False)

    def block(cols):
        return df[[f"clos_{c}" for c in cols]].mean(axis=1)

    def report(sub, label):
        print(f"\n=== {label} (n={len(sub)}) ===")
        for roi in ALL:
            c = sub[f"clos_{roi}"]
            tag = "SCN" if roi in VIS_SCENE else ("AGT" if roi in VIS_AGENT else "CTL")
            print(f"  {tag} {roi:24s} mean closure {c.mean():+.3f}  "
                  f"frac>0 {(c>0).mean()*100:3.0f}%")
        for name, cols in [("scene", VIS_SCENE), ("agent", VIS_AGENT), ("control", CONTROL)]:
            b = df.loc[sub.index] if False else sub
            blk = b[[f"clos_{c}" for c in cols]].mean(axis=1)
            # sign-flip permutation that block closure > 0
            d = blk.to_numpy(); obs = d.mean()
            rng = np.random.default_rng(0)
            null = ((rng.integers(0, 2, (20000, len(d))) * 2 - 1) * np.abs(d)).mean(1)
            p = float((np.abs(null) >= abs(obs)).mean())
            print(f"  [{name:7s} block] mean closure {obs:+.3f}  perm p={p:.2e}")

    report(df, "ALL 78")
    report(df[df.corpus == "inbench"], "IN-BENCH 18")
    report(df[df.corpus == "external"], "EXTERNAL 60")


if __name__ == "__main__":
    main()
