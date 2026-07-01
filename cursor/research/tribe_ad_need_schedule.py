"""Corpus-wide TRIBE audio-description NEED schedule (the actual TRIBE use-case).

TRIBE's intended role (see wiki/research/scenetwin-neural-description-need-pivot,
-coarse-need-windows, -gap-targeted-ad-loop): NOT a text-correctness scorer, but
an upstream estimator of WHERE/WHEN/WHAT-KIND of audio description is needed:

    AccessibilityGap(t) = distance(P_AV[t], P_A[t])   # video signal audio misses
    need_score(t)       = 0.5*minmax(residual_norm) + 0.5*minmax(cosine_gap)
    content type        = scene/spatial vs agent/action, from per-ROI gap

Until now this existed only for 2-18 in-bench clips (per-timestep P_AV/P_A were
never saved at scale). The tribe_tensors_all78 dump makes it computable for all
78 clips, including 60 EXTERNAL -- a ~4x scale-up and the first external
generalization of TRIBE's real deliverable.

Methodology matches tools/scenetwin_neural_need_curve.py +
scenetwin_coarse_need_windows.py (3s windows, same need_score formula). Speech
density / standard-vs-extended slot typing needs transcripts (in-bench only) and
is intentionally omitted here; the need level + content type degrade gracefully
to the external corpus.
"""
from pathlib import Path

import numpy as np
import pandas as pd

import tribe_tensors_load as T

ROOT = Path(__file__).resolve().parents[2]
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"
SCENE = ["early_visual_v1", "higher_visual_v2v3v4", "scene_ppa", "retrosplenial_pos"]
AGENT = ["face_ffc", "body_eba_region", "motion_mt_complex", "lateral_object_loc"]
WINDOW_S = 3.0


def minmax(v):
    v = np.asarray(v, float)
    lo, hi = np.nanmin(v), np.nanmax(v)
    return np.zeros_like(v) if hi == lo else (v - lo) / (hi - lo)


def verts(rois):
    m = pd.read_csv(MASK)
    return m[m.roi.isin(rois)].vertex.to_numpy()


def block_gap_t(pav, pa, vv):
    out = np.zeros(pav.shape[0])
    for t in range(pav.shape[0]):
        a, b = pav[t, vv].astype(float), pa[t, vv].astype(float)
        out[t] = 1.0 - np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)
    return out


def recommend(need_q, scene_gap, agent_gap):
    if need_q < 0.34:
        return "low_ad_need"
    kind = "spatial/scene" if scene_gap >= agent_gap else "agent/action"
    level = "high" if need_q >= 0.67 else "moderate"
    return f"{level}_ad_need:{kind}"


def main():
    sv, av = verts(SCENE), verts(AGENT)
    man = T.load_manifest()
    rows = []
    for _, r in man.iterrows():
        try:
            t, meta = T.load_clip(r.clip_key)
        except FileNotFoundError:
            continue
        pav, pa = t["P_AV"], t["P_A"]
        n = min(pav.shape[0], pa.shape[0])   # P_AV/P_A can differ by one TR
        pav, pa = pav[:n], pa[:n]
        dur = float(meta.get("duration_s") or (meta.get("end_s", 0) - meta.get("start_s", 0)) or n * 1.5)
        step = dur / n
        resid = np.linalg.norm(pav - pa, axis=1) / np.sqrt(pav.shape[1])
        cos_gap = np.array([1.0 - np.dot(pav[i], pa[i]) /
                            (np.linalg.norm(pav[i]) * np.linalg.norm(pa[i]) + 1e-9) for i in range(n)])
        need = 0.5 * minmax(resid) + 0.5 * minmax(cos_gap)
        sgap, agap = block_gap_t(pav, pa, sv), block_gap_t(pav, pa, av)
        win = (np.arange(n) * step // WINDOW_S).astype(int)
        for w in np.unique(win):
            m = win == w
            nq = need[m].mean()
            rows.append({
                "clip_key": r.clip_key, "corpus": meta.get("corpus"),
                "category": meta.get("category"),
                "window": int(w), "start_s": round(float(np.where(m)[0][0] * step), 1),
                "end_s": round(float((np.where(m)[0][-1] + 1) * step), 1),
                "need_score": round(float(nq), 3),
                "scene_gap": round(float(sgap[m].mean()), 3),
                "agent_gap": round(float(agap[m].mean()), 3),
            })
    sch = pd.DataFrame(rows)
    # within-clip need quantile -> recommendation
    sch["need_q"] = sch.groupby("clip_key").need_score.rank(pct=True)
    sch["recommendation"] = [recommend(q, s, a) for q, s, a in
                             zip(sch.need_q, sch.scene_gap, sch.agent_gap)]
    out = ROOT / "cursor/research/output/tribe_ad_need_schedule.csv"
    sch.to_csv(out, index=False)

    print(f"AD-need schedule: {len(sch)} windows across {sch.clip_key.nunique()} clips "
          f"({(sch.groupby('clip_key').corpus.first()=='external').sum()} external, "
          f"{(sch.groupby('clip_key').corpus.first()=='inbench').sum()} in-bench)")
    for corp in ["inbench", "external"]:
        s = sch[sch.corpus == corp]
        hi = s[s.recommendation.str.startswith(("high", "moderate"))]
        print(f"\n--- {corp} ---")
        print(f"  windows flagged needing AD: {len(hi)}/{len(s)} ({len(hi)/len(s)*100:.0f}%)")
        kinds = hi.recommendation.str.split(":").str[1].value_counts()
        print(f"  content-type split of flagged windows: {kinds.to_dict()}")
        print(f"  mean AD-need windows per clip: {len(hi)/s.clip_key.nunique():.1f}")

    # show a sample schedule for one external clip
    ex = sch[sch.corpus == "external"].clip_key.iloc[0]
    print(f"\n=== sample schedule: {ex} ===")
    print(sch[sch.clip_key == ex][["start_s", "end_s", "need_score",
          "scene_gap", "agent_gap", "recommendation"]].to_string(index=False))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
