"""Load and analyze the TRIBE tensor bundle from Colab.

After unzipping tribe_tensors_all78.zip into cursor/research/output/tribe_tensors/,
this provides:

  - load_clip(clip_key) -> (tensors_dict, meta_dict)
  - load_manifest() -> DataFrame of all 78 clips with meta
  - per_region_accessibility_gap(P_AV, P_A, atlas) -> {region: gap}
  - per_timestep_gap(P_AV, P_A) -> (T,) array
  - summary_table() -> DataFrame of derived features

Cortical mesh: fsaverage5, 20484 vertices total
  (10242 left hemisphere + 10242 right hemisphere).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TENSOR_DIR = ROOT / "cursor" / "research" / "output" / "tribe_tensors"


# ============================================================
# Loaders
# ============================================================

def load_manifest() -> pd.DataFrame:
    """Master per-clip metadata (corpus, category, scalar gaps, video_id, ...)."""
    p = TENSOR_DIR / "manifest.csv"
    if not p.exists():
        raise FileNotFoundError(f"manifest.csv not found at {p}. "
                                f"Did you unzip tribe_tensors_all78.zip into {TENSOR_DIR}?")
    return pd.read_csv(p)


def load_clip(clip_key: str) -> tuple[dict, dict]:
    """Return ({P_AV, P_A, P_AD, P_AV_AD: np.ndarray}, meta_dict).

    Shapes: each P_* is (T, 20484) float32 where T depends on clip duration
    and TRIBE's TR (~1.5 s). For a 10s clip T~7; for a 30s clip T~20.
    """
    corpus = "inbench" if clip_key.startswith("inbench_") else "external"
    npz_path = TENSOR_DIR / corpus / f"{clip_key}.npz"
    meta_path = TENSOR_DIR / corpus / f"{clip_key}.json"
    if not npz_path.exists():
        raise FileNotFoundError(npz_path)
    z = np.load(npz_path)
    tensors = {k: z[k] for k in z.files}
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    return tensors, meta


# ============================================================
# Derived analyses
# ============================================================

def per_timestep_gap(p_av: np.ndarray, p_a: np.ndarray) -> np.ndarray:
    """Return accessibility_gap per timestep (T,).

    gap_t = 1 - cos(P_AV[t], P_A[t]) where the cosine is per-timestep
    over all 20484 vertices. High = visual information missing from audio
    at that moment.
    """
    assert p_av.shape == p_a.shape, f"shape mismatch: {p_av.shape} vs {p_a.shape}"
    T = p_av.shape[0]
    out = np.zeros(T, dtype=float)
    for t in range(T):
        a = p_av[t].astype(float)
        b = p_a[t].astype(float)
        denom = np.linalg.norm(a) * np.linalg.norm(b) + 1e-9
        out[t] = 1.0 - float(np.dot(a, b) / denom)
    return out


def hemisphere_split(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split a (T, 20484) prediction into (T, 10242) left + (T, 10242) right."""
    assert p.shape[-1] == 20484, f"expected 20484 vertices, got {p.shape[-1]}"
    return p[..., :10242], p[..., 10242:]


def per_hemisphere_gap(p_av: np.ndarray, p_a: np.ndarray) -> dict[str, float]:
    """Return clip-level accessibility_gap split by hemisphere."""
    lh_av, rh_av = hemisphere_split(p_av)
    lh_a, rh_a = hemisphere_split(p_a)

    def _cos(a, b):
        a = a.mean(axis=0).flatten().astype(float)
        b = b.mean(axis=0).flatten().astype(float)
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))

    return {
        "gap_lh": 1.0 - _cos(lh_av, lh_a),
        "gap_rh": 1.0 - _cos(rh_av, rh_a),
        "gap_full": 1.0 - _cos(p_av, p_a),
    }


def per_region_accessibility_gap(p_av: np.ndarray, p_a: np.ndarray,
                                 atlas: np.ndarray | None = None) -> dict[int, float]:
    """Per-ROI accessibility_gap.

    atlas: optional (20484,) integer label vector. If None, returns just
    {0: full_gap, 1: lh_gap, 2: rh_gap} as a hemisphere-only fallback.

    To use a real cortical atlas (e.g. Glasser-360 or Schaefer-400 projected
    onto fsaverage5), pass a vertex-to-region assignment array. TRIBE's repo
    includes some atlases under tribev2/plotting/ if you want full anatomy.
    """
    if atlas is None:
        h = per_hemisphere_gap(p_av, p_a)
        return {0: h["gap_full"], 1: h["gap_lh"], 2: h["gap_rh"]}

    assert atlas.shape == (20484,), f"atlas must be (20484,), got {atlas.shape}"
    av_mean = p_av.mean(axis=0)
    a_mean = p_a.mean(axis=0)
    out = {}
    for region in np.unique(atlas):
        mask = (atlas == region)
        if mask.sum() == 0:
            continue
        a = av_mean[mask].astype(float)
        b = a_mean[mask].astype(float)
        denom = np.linalg.norm(a) * np.linalg.norm(b) + 1e-9
        out[int(region)] = 1.0 - float(np.dot(a, b) / denom)
    return out


def summary_table(manifest: pd.DataFrame | None = None) -> pd.DataFrame:
    """Build per-clip table with extra derived features.

    Loads each tensor file once, computes hemisphere-split gap and
    per-timestep gap stats (max, median, std).
    """
    if manifest is None:
        manifest = load_manifest()
    rows = []
    for _, row in manifest.iterrows():
        key = row["clip_key"]
        try:
            tensors, meta = load_clip(key)
        except FileNotFoundError:
            continue
        p_av = tensors["P_AV"]; p_a = tensors["P_A"]
        hsplit = per_hemisphere_gap(p_av, p_a)
        ts_gap = per_timestep_gap(p_av, p_a)
        rows.append({
            "clip_key": key,
            "corpus": meta.get("corpus"),
            "video_id": meta.get("video_id"),
            "category": meta.get("category"),
            "T_timesteps": int(p_av.shape[0]),
            "gap_full": hsplit["gap_full"],
            "gap_lh": hsplit["gap_lh"],
            "gap_rh": hsplit["gap_rh"],
            "gap_lh_minus_rh": hsplit["gap_lh"] - hsplit["gap_rh"],
            "gap_t_max": float(ts_gap.max()),
            "gap_t_median": float(np.median(ts_gap)),
            "gap_t_std": float(ts_gap.std()),
            "accessibility_gap_scalar": float(meta.get("accessibility_gap", 0)),
            "description_gain_scalar": float(meta.get("description_gain", 0)),
            "alignment_cosine_scalar": float(meta.get("alignment_cosine", 0)),
            "duration_s": float(meta.get("duration_s") or (meta.get("end_s", 0) - meta.get("start_s", 0))),
        })
    return pd.DataFrame(rows)


# ============================================================
# CLI: quick sanity check
# ============================================================
if __name__ == "__main__":
    m = load_manifest()
    print(f"Manifest: {len(m)} clips ({(m['corpus']=='inbench').sum()} inbench, "
          f"{(m['corpus']=='external').sum()} external)")
    print(m.head(3).to_string(index=False))

    # Load first inbench clip as a smoke test
    first_key = m[m["corpus"] == "inbench"].iloc[0]["clip_key"]
    print(f"\nLoading {first_key}...")
    tensors, meta = load_clip(first_key)
    for k, v in tensors.items():
        print(f"  {k}: shape={v.shape}, dtype={v.dtype}, "
              f"mean={float(v.mean()):.4f}, std={float(v.std()):.4f}")
    print(f"  meta accessibility_gap = {meta.get('accessibility_gap'):.4f}")

    # Hemisphere split
    hsplit = per_hemisphere_gap(tensors["P_AV"], tensors["P_A"])
    print(f"\nPer-hemisphere gap:")
    for k, v in hsplit.items():
        print(f"  {k}: {v:.4f}")

    # Per-timestep
    ts = per_timestep_gap(tensors["P_AV"], tensors["P_A"])
    print(f"\nPer-timestep gap (T={len(ts)}):")
    print(f"  min={ts.min():.4f}  median={np.median(ts):.4f}  max={ts.max():.4f}")
