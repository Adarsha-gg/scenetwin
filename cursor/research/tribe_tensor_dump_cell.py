"""
COLAB CELL — paste this into the existing notebook AFTER the cells that
loaded TRIBE (i.e. after Step 4). Saves P_AV, P_A, P_AD tensors plus
metadata for all 78 clips (18 in-bench + 60 external), then bundles
into a single zip for download.

Assumes:
  - tribev2 + LLaMA-3.2 are loaded (Step 1, Step 1b, Step 4 already run)
  - SceneTwin repo cloned at /content/scenetwin (Step 2)
  - external registry available in scope as `external_registry` (Step 4b)
  - 18-clip vatex videos at /content/scenetwin/workspace/vatex_clips/ (Step 3)
  - 60-clip external videos at /content/scenetwin/workspace/external_clips/

What it saves per clip:
  /content/tribe_tensors/<corpus>/<clip_key>.npz
    - P_AV  : (T, 20484) float32  -- full video brain response
    - P_A   : (T, 20484) float32  -- audio-only brain response
    - P_AD  : (T, 20484) float32  -- AD text-only brain response
    - P_AV_AD : (T, 20484) float32 -- legacy overlay (if computed)
    - meta : structured JSON with video_id, category, ad_text, durations
    - accessibility_gap, description_gain, alignment_cosine scalars

Compute budget:
  ~2-3 hours on T4 for 78 clips * 3 predictions = 234 TRIBE calls.
  ~144 MB total raw, ~80-100 MB compressed.
"""

import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/content/scenetwin")
OUT_TENSOR_DIR = Path("/content/tribe_tensors")
OUT_TENSOR_DIR.mkdir(parents=True, exist_ok=True)
(OUT_TENSOR_DIR / "inbench").mkdir(exist_ok=True)
(OUT_TENSOR_DIR / "external").mkdir(exist_ok=True)

# These should already exist in your kernel from earlier cells; if not, re-import.
# `_TRIBE_MODEL`, `CACHE_DIR`, `_load_tribe`, `_extract_audio_for_tribe`,
# `_tribe_from_path`, `_tribe_predict_events`, `_slug`, `_tribe_cos` should
# all be defined.

try:
    _TRIBE_MODEL
except NameError:
    ok, msg = _load_tribe()
    assert ok, f"TRIBE not loaded: {msg}"


def predict_and_save(clip_key: str, video_path: str, ad_text: str,
                     extra_meta: dict, out_dir: Path):
    """Run the full counterfactual on one clip and save tensors + meta."""
    out_npz = out_dir / f"{clip_key}.npz"
    out_meta = out_dir / f"{clip_key}.json"
    if out_npz.exists() and out_meta.exists():
        return "cached"

    if not Path(video_path).exists():
        return f"missing video: {video_path}"

    model = _TRIBE_MODEL

    # P_AV  (full video)
    p_av = _tribe_from_path(model, video_path=video_path)
    if p_av is None:
        return "P_AV failed"

    # P_A   (audio-only)
    audio_path = _extract_audio_for_tribe(video_path)
    p_a = _tribe_from_path(model, audio_path=audio_path) if audio_path else None
    audio_ok = p_a is not None
    if p_a is None:
        p_a = p_av  # fallback — caller can see audio_ok=False

    # P_AD  (AD text only)
    p_ad = None
    if ad_text.strip():
        ad_txt_path = CACHE_DIR / f"{_slug(video_path)}_ad.txt"
        ad_txt_path.write_text(ad_text.strip(), encoding="utf-8")
        p_ad = _tribe_from_path(model, text_path=str(ad_txt_path))
    if p_ad is None:
        # If gtts/TTS isn't available or fails, dump a zero placeholder
        p_ad = np.zeros_like(p_av)

    # Legacy overlay (P_AV with text injected into events)
    p_av_ad = None
    try:
        events = model.get_events_dataframe(video_path=video_path)
        if "text" in events.columns:
            events = events.copy()
            events["text"] = ad_text.strip()
            p_av_ad = _tribe_predict_events(model, events)
    except Exception:
        pass
    if p_av_ad is None:
        p_av_ad = np.zeros_like(p_av)

    # Derive scalars
    accessibility_gap = 1.0 - _tribe_cos(p_av, p_a)
    description_gain = _tribe_cos(p_av, p_ad) - _tribe_cos(p_av, p_a) if p_ad.any() else 0.0
    alignment_cosine = _tribe_cos(p_av, p_av_ad) if p_av_ad.any() else 0.0

    # Save tensors (compressed)
    np.savez_compressed(
        out_npz,
        P_AV=p_av.astype(np.float32),
        P_A=p_a.astype(np.float32),
        P_AD=p_ad.astype(np.float32),
        P_AV_AD=p_av_ad.astype(np.float32),
    )
    meta = {
        "clip_key": clip_key,
        "video_path_local": str(video_path),
        "ad_text_used": ad_text,
        "audio_only_ok": bool(audio_ok),
        "accessibility_gap": float(accessibility_gap),
        "description_gain": float(description_gain),
        "alignment_cosine": float(alignment_cosine),
        "P_AV_shape": list(p_av.shape),
        "P_A_shape": list(p_a.shape),
        "P_AD_shape": list(p_ad.shape),
        **extra_meta,
    }
    out_meta.write_text(json.dumps(meta, indent=2))
    return "saved"


# ============================================================
# 1. Process 18 in-bench clips
# ============================================================
forecast = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native"
                       / "tribe_failure_forecast.csv")
print(f"\n=== 18 in-bench clips ===\n")
t0 = time.time()
for i, r in forecast.iterrows():
    cidx = int(r["clip_idx"])
    clip_key = f"inbench_clip_{cidx:02d}_{r['video_id']}"
    # Find video file
    video = None
    for ext in (".mp4", ".mkv", ".webm"):
        p = ROOT / "workspace" / "vatex_clips" / f"clip_{cidx:02d}{ext}"
        if p.exists():
            video = str(p); break
    if video is None:
        print(f"  [{i+1}/18] {clip_key}  ERR: no video file")
        continue
    extra_meta = {
        "corpus": "inbench",
        "clip_idx": cidx,
        "video_id": r["video_id"],
        "category": r["category"],
        "duration_s": float(r["duration_s"]),
        "all4_fail": int(r["all4_fail"]),
        "low_tier3_margin": int(r["low_tier3_margin"]),
        "tier2_tier1_inversion": int(r["tier2_tier1_inversion"]),
    }
    msg = predict_and_save(clip_key, video, str(r["tier3_va11y_text"]),
                           extra_meta, OUT_TENSOR_DIR / "inbench")
    elapsed = time.time() - t0
    eta = elapsed / (i + 1) * (len(forecast) - i - 1)
    print(f"  [{i+1}/18] {clip_key}  {msg}  ({elapsed:.0f}s, eta {eta:.0f}s)")

# ============================================================
# 2. Process 60 external clips
# ============================================================
print(f"\n=== 60 external clips ===\n")
EXT_DIR = ROOT / "workspace" / "external_clips"
t0 = time.time()
for i, entry in enumerate(external_registry):
    vid = entry["video_id"]
    clip_key = f"external_{vid}"
    video = EXT_DIR / f"{vid}.mp4"
    if not video.exists():
        print(f"  [{i+1}/60] {clip_key}  ERR: video missing")
        continue
    extra_meta = {
        "corpus": "external",
        "video_id": vid,
        "category": entry["category"],
        "yt_id": entry["yt_id"],
        "start_s": float(entry["start"]),
        "end_s": float(entry["end"]),
    }
    msg = predict_and_save(clip_key, str(video), str(entry["tier3"]),
                           extra_meta, OUT_TENSOR_DIR / "external")
    elapsed = time.time() - t0
    eta = elapsed / (i + 1) * (len(external_registry) - i - 1)
    print(f"  [{i+1}/60] {clip_key}  {msg}  ({elapsed:.0f}s, eta {eta:.0f}s)")

# ============================================================
# 3. Build master manifest CSV
# ============================================================
print("\n=== Building master manifest ===")
rows = []
for sub in ("inbench", "external"):
    for jf in sorted((OUT_TENSOR_DIR / sub).glob("*.json")):
        rows.append(json.loads(jf.read_text()))
manifest = pd.DataFrame(rows)
manifest_path = OUT_TENSOR_DIR / "manifest.csv"
manifest.to_csv(manifest_path, index=False)
print(f"Manifest -> {manifest_path}  ({len(manifest)} clips total)")
manifest.head(3)

# ============================================================
# 4. Zip everything for download
# ============================================================
print("\n=== Bundling for download ===")
import shutil
archive_base = "/content/tribe_tensors_all78"
zip_path = f"{archive_base}.zip"
if Path(zip_path).exists():
    Path(zip_path).unlink()
# make_archive returns the actual zip path on success -- trust it over name guessing
zip_path = shutil.make_archive(archive_base, "zip", str(OUT_TENSOR_DIR))
size_mb = Path(zip_path).stat().st_size / (1024 * 1024)
print(f"Wrote {zip_path}  ({size_mb:.1f} MB)")

try:
    from google.colab import files
    files.download(zip_path)
except Exception as e:
    print(f"(auto-download failed; grab from Colab Files pane: {zip_path})")
    print(f"  {e}")
