"""Use-case probe: does the TRIBE AV-vs-A accessibility gap concentrate in
VISUAL cortex?

If audio description's job is to restore *visual* information that audio alone
misses, then the brain-response divergence between the audiovisual encoder
(P_AV) and audio-only encoder (P_A) should be largest in visual ROIs (V1,
V2-V4, MT motion, FFC face, PPA scene, EBA body, object) and smallest in
auditory / language control ROIs.

This is an ANATOMICAL claim, not a per-clip calibration claim, so it has a
shot at holding on the external corpus where the scalar calibration signal
died (r=+0.025, p=0.85).

Run after unzipping tribe_tensors_all78.zip into
cursor/research/output/tribe_tensors/.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import tribe_tensors_load as T

ROOT = Path(__file__).resolve().parents[2]
MASK = ROOT / "output" / "scenetwin_description_gain" / "glasser_roi_mask.csv"

VISUAL_ROIS = {
    "early_visual_v1", "higher_visual_v2v3v4", "motion_mt_complex",
    "face_ffc", "scene_ppa", "body_eba_region", "lateral_object_loc",
    "retrosplenial_pos",
}
CONTROL_ROIS = {"auditory_control", "language_control"}


def build_roi_index() -> dict[str, np.ndarray]:
    """roi_name -> int array of vertex indices (0..20483)."""
    m = pd.read_csv(MASK)
    m = m[m["roi"] != "_unassigned_padding"]
    return {roi: g["vertex"].to_numpy() for roi, g in m.groupby("roi")}


def roi_gap(p_av: np.ndarray, p_a: np.ndarray, verts: np.ndarray) -> float:
    """1 - cos over the time-averaged response restricted to `verts`."""
    a = p_av.mean(axis=0)[verts].astype(float)
    b = p_a.mean(axis=0)[verts].astype(float)
    denom = np.linalg.norm(a) * np.linalg.norm(b) + 1e-9
    return 1.0 - float(np.dot(a, b) / denom)


def main() -> None:
    roi_idx = build_roi_index()
    manifest = T.load_manifest()

    rows = []
    for _, r in manifest.iterrows():
        key = r["clip_key"]
        try:
            tensors, meta = T.load_clip(key)
        except FileNotFoundError:
            continue
        p_av, p_a = tensors["P_AV"], tensors["P_A"]
        rec = {"clip_key": key, "corpus": meta.get("corpus"),
               "category": meta.get("category"),
               "accessibility_gap": float(meta.get("accessibility_gap", 0))}
        for roi, verts in roi_idx.items():
            rec[roi] = roi_gap(p_av, p_a, verts)
        rows.append(rec)

    df = pd.DataFrame(rows)
    out = ROOT / "cursor" / "research" / "output" / "tribe_roi_gap_per_clip.csv"
    df.to_csv(out, index=False)

    roi_cols = [c for c in df.columns if c in roi_idx]

    def report(sub: pd.DataFrame, label: str) -> None:
        means = sub[roi_cols].mean().sort_values(ascending=False)
        vis = sub[[c for c in roi_cols if c in VISUAL_ROIS]].mean(axis=1)
        ctl = sub[[c for c in roi_cols if c in CONTROL_ROIS]].mean(axis=1)
        # paired permutation test on the per-clip difference (sign-flip null)
        d = (vis - ctl).to_numpy()
        obs = d.mean()
        rng = np.random.default_rng(0)
        n_perm = 20000
        flips = rng.integers(0, 2, size=(n_perm, len(d))) * 2 - 1
        null = (flips * np.abs(d)).mean(axis=1)
        p = float((np.abs(null) >= abs(obs)).mean())
        d = vis - ctl  # keep as Series for the prints below
        print(f"\n=== {label}  (n={len(sub)}) ===")
        print(f"  per-ROI mean gap (high = more AV/A divergence):")
        for roi, v in means.items():
            tag = "VIS" if roi in VISUAL_ROIS else ("CTL" if roi in CONTROL_ROIS else "   ")
            print(f"    {tag} {roi:24s} {v:.4f}")
        print(f"  visual-block mean  = {vis.mean():.4f}")
        print(f"  control-block mean = {ctl.mean():.4f}")
        print(f"  per-clip (visual - control): mean={d.mean():+.4f}  "
              f"share visual>control = {(d>0).mean()*100:.0f}%")
        print(f"  paired sign-flip permutation (visual>control): p={p:.2e}")

    report(df, "ALL 78 CLIPS")
    report(df[df["corpus"] == "inbench"], "IN-BENCH (18)")
    report(df[df["corpus"] == "external"], "EXTERNAL (60)")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
