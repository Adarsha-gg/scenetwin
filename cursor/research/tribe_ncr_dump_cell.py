"""
COLAB CELL — Neural Contrastive Retrieval (NCR) data producer.

Paste AFTER TRIBE is loaded (same prerequisites as tribe_tensor_dump_cell.py:
_TRIBE_MODEL, _tribe_from_path, _slug, CACHE_DIR all defined; repo at
/content/scenetwin; external clips at /content/scenetwin/workspace/external_clips/).

IDEA (Neural Contrastive Retrieval): feed each candidate AD's TEXT through TRIBE
(brain response to HEARING the AD), mean-pool to a vector q. For each clip's VIDEO
brain response v = mean(P_AV), ask: does q retrieve the RIGHT clip among all 60?
A good AD -> q lands near the correct v; a vague/wrong AD -> near chance. Cosine +
rank is magnitude-invariant (kills the verbosity confound that buried neural closure),
and the wrong-content control (tier0_cross) should retrieve its SOURCE clip, not this
one. This is AD-DEPENDENT, unlike the per-clip accessibility_gap.

Runs on the 60 EXTERNAL clips x 4 tiers (all tier texts are in each clip's
metadata.json). ~60 P_AV + 240 P_AD = ~300 TRIBE calls (~3-4h T4). npz-cached so
reruns are cheap. Saves a TINY long-format CSV of all query-vs-reference cosines
(~14k rows) for local analysis, plus the mean vectors for re-analysis.

OUTPUT (downloaded):
  /content/tribe_ncr/ncr_similarity.csv   query_vid, tier, ref_vid, cos
  /content/tribe_ncr/ncr_vectors.npz       refs (60,D), per-tier queries (60,D)
"""
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/content/scenetwin")
EXT_VIDEO = ROOT / "workspace" / "external_clips"
EXT_META = ROOT / "cursor" / "data" / "external_clips"
OUT = Path("/content/tribe_ncr"); OUT.mkdir(parents=True, exist_ok=True)
NPZ_CACHE = OUT / "vec_cache"; NPZ_CACHE.mkdir(exist_ok=True)
TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]

try:
    _TRIBE_MODEL
except NameError:
    ok, msg = _load_tribe(); assert ok, f"TRIBE not loaded: {msg}"


def _meanvec(pred):
    """(T, D) -> unit-norm (D,) mean-pooled vector, or None."""
    if pred is None:
        return None
    v = np.asarray(pred, dtype=np.float32)
    if v.ndim == 2:
        v = v.mean(axis=0)
    n = np.linalg.norm(v)
    return (v / n).astype(np.float32) if n > 0 else None


def _tribe_text_vec(model, text):
    if not str(text).strip():
        return None
    p = CACHE_DIR / f"ncr_{_slug(str(text)[:40])}_{abs(hash(text)) % 10**8}.txt"
    p.write_text(str(text).strip(), encoding="utf-8")
    return _meanvec(_tribe_from_path(model, text_path=str(p)))


def clip_vectors(vid):
    """Return dict with 'ref' (P_AV meanvec) and one query meanvec per tier. Cached."""
    cache = NPZ_CACHE / f"{vid}.npz"
    if cache.exists():
        d = np.load(cache)
        return {k: d[k] for k in d.files}
    meta = json.loads((EXT_META / vid / "metadata.json").read_text())
    video = EXT_VIDEO / f"{vid}.mp4"
    out = {}
    ref = _meanvec(_tribe_from_path(_TRIBE_MODEL, video_path=str(video))) if video.exists() else None
    if ref is not None:
        out["ref"] = ref
    for t in TIERS:
        q = _tribe_text_vec(_TRIBE_MODEL, meta.get(t, ""))
        if q is not None:
            out[t] = q
    if "ref" in out:
        np.savez_compressed(cache, **out)
    return out


vids = sorted(p.name for p in EXT_META.iterdir() if (p / "metadata.json").exists())
print(f"{len(vids)} external clips")
vecs = {}
t0 = time.time()
for i, vid in enumerate(vids):
    try:
        vecs[vid] = clip_vectors(vid)
    except Exception as e:
        print(f"  [{i+1}/{len(vids)}] {vid} ERR {e}"); continue
    el = time.time() - t0
    print(f"  [{i+1}/{len(vids)}] {vid}  ok  ({el:.0f}s, eta {el/(i+1)*(len(vids)-i-1):.0f}s)")

# Reference set: clips that produced a P_AV vector
refs = {v: d["ref"] for v, d in vecs.items() if "ref" in d}
ref_vids = sorted(refs)
R = np.stack([refs[v] for v in ref_vids])  # (N, D), unit-norm

rows = []
for qvid, d in vecs.items():
    for t in TIERS:
        if t not in d:
            continue
        sims = R @ d[t]  # cosine (both unit-norm)
        for rv, c in zip(ref_vids, sims):
            rows.append({"query_vid": qvid, "tier": t, "ref_vid": rv, "cos": float(c)})

sim = pd.DataFrame(rows)
sim.to_csv(OUT / "ncr_similarity.csv", index=False)
np.savez_compressed(OUT / "ncr_vectors.npz",
                    ref_vids=np.array(ref_vids),
                    R=R,
                    **{f"{t}__{v}": d[t] for v, d in vecs.items() for t in TIERS if t in d})
print(f"\nWrote {OUT/'ncr_similarity.csv'} ({len(sim)} rows), ncr_vectors.npz, N_ref={len(ref_vids)}")

try:
    from google.colab import files
    files.download(str(OUT / "ncr_similarity.csv"))
except Exception as e:
    print(f"(grab from Files pane: {OUT/'ncr_similarity.csv'})  {e}")
