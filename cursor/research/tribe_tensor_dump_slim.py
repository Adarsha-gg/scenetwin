"""
COLAB CELL (slim) -- saves only P_AV + P_A for the 60 external clips.
~30-45 min vs ~2 hours, because:
  (a) skips 18 in-bench (already known result)
  (b) skips P_AD + P_AV_AD (description_gain didn't generalize)
  (c) reuses warm neuralset feature caches from your earlier run

Paste this AFTER the existing notebook's cell that loaded TRIBE (Step 4)
and built `external_registry` (Step 4b). It does NOT need cell 11 first.

Outputs:
  /content/tribe_tensors_ext/<video_id>.npz  (P_AV, P_A)
  /content/tribe_tensors_ext/<video_id>.json (meta + scalar gap)
  /content/tribe_tensors_ext/manifest.csv
  /content/tribe_tensors_ext_60.zip          (~50-70 MB)
"""

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/content/scenetwin")
OUT_DIR = Path("/content/tribe_tensors_ext")
OUT_DIR.mkdir(parents=True, exist_ok=True)
EXT_VIDEOS = ROOT / "workspace" / "external_clips"

try:
    _TRIBE_MODEL
except NameError:
    ok, msg = _load_tribe()
    assert ok, f"TRIBE not loaded: {msg}"


def save_pair(video_id: str, video_path: Path, ad_text: str, extra_meta: dict):
    npz_path = OUT_DIR / f"{video_id}.npz"
    json_path = OUT_DIR / f"{video_id}.json"
    if npz_path.exists() and json_path.exists():
        return "cached"
    if not video_path.exists():
        return f"missing video {video_path}"

    model = _TRIBE_MODEL

    # P_AV
    p_av = _tribe_from_path(model, video_path=str(video_path))
    if p_av is None:
        return "P_AV failed"

    # P_A
    audio_path = _extract_audio_for_tribe(str(video_path))
    p_a = _tribe_from_path(model, audio_path=audio_path) if audio_path else None
    audio_ok = p_a is not None
    if p_a is None:
        p_a = p_av

    gap = 1.0 - _tribe_cos(p_av, p_a)

    np.savez_compressed(
        npz_path,
        P_AV=p_av.astype(np.float32),
        P_A=p_a.astype(np.float32),
    )
    meta = {
        "video_id": video_id,
        "audio_only_ok": bool(audio_ok),
        "accessibility_gap": float(gap),
        "P_AV_shape": list(p_av.shape),
        "P_A_shape": list(p_a.shape),
        "ad_text": ad_text,
        **extra_meta,
    }
    json_path.write_text(json.dumps(meta, indent=2))
    return "saved"


print(f"Processing 60 external clips...\n")
t0 = time.time()
for i, entry in enumerate(external_registry):
    vid = entry["video_id"]
    video = EXT_VIDEOS / f"{vid}.mp4"
    extra = {
        "category": entry["category"],
        "yt_id": entry["yt_id"],
        "start_s": float(entry["start"]),
        "end_s": float(entry["end"]),
        "duration_s": float(entry["end"] - entry["start"]),
    }
    status = save_pair(vid, video, str(entry["tier3"]), extra)
    elapsed = time.time() - t0
    eta = elapsed / (i + 1) * (60 - i - 1)
    print(f"  [{i+1}/60] {vid}  {status}  ({elapsed:.0f}s, eta {eta:.0f}s)")

# Build manifest
rows = []
for jf in sorted(OUT_DIR.glob("*.json")):
    rows.append(json.loads(jf.read_text()))
manifest = pd.DataFrame(rows)
manifest.to_csv(OUT_DIR / "manifest.csv", index=False)
print(f"\nManifest: {len(manifest)} clips -> {OUT_DIR/'manifest.csv'}")

# Zip + download
import shutil
zip_path = "/content/tribe_tensors_ext_60.zip"
if Path(zip_path).exists():
    Path(zip_path).unlink()
shutil.make_archive("/content/tribe_tensors_ext_60", "zip", str(OUT_DIR))
size_mb = Path(zip_path).stat().st_size / (1024 * 1024)
print(f"Wrote {zip_path} ({size_mb:.1f} MB)")

try:
    from google.colab import files
    files.download(zip_path)
except Exception as e:
    print(f"(auto-download failed; grab from Files pane: {zip_path})")
