#!/usr/bin/env python3
"""Self-contained Colab runner for TRIBE Neural Contrastive Retrieval (NCR).

Prereq on a persistent Colab GPU session:
  1. tools/colab_tribe_setup.py
  2. colab restart-kernel
  3. tools/colab_tribe_smoke.py passes
  4. upload ncr metadata JSON to /content/ncr_external_metadata.json

Outputs under /content/tribe_ncr by default:
  - ncr_similarity.csv
  - ncr_vectors.npz
  - ncr_run_summary.json
"""
from __future__ import annotations

import csv
import base64
import contextlib
import gc
import gzip
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from gtts import gTTS
from langdetect import detect
from tribev2 import TribeModel
from tribev2.demo_utils import get_audio_and_text_events

for _logger_name in ["tribev2", "neuralset", "exca", "moviepy", "huggingface_hub"]:
    logging.getLogger(_logger_name).setLevel(logging.ERROR)
logging.disable(logging.WARNING)
warnings.filterwarnings("ignore")

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
DEFAULT_CONFIG = {
    "metadata_path": "/content/ncr_external_metadata.json",
    "out_dir": "/content/tribe_ncr",
    "model_name": "facebook/tribev2",
    "cache_folder": "/content/tribe_cache",
    "video_height": 360,
    "limit": None,
    "min_refs": 2,
}


def load_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_CONFIG)
    p = Path("/content/tribe_ncr/ncr_config.json")
    if p.exists():
        cfg.update(json.loads(p.read_text(encoding="utf-8")))
    return cfg


def run(cmd: list[str], check: bool = True, timeout: int | None = None) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd), flush=True)
    cp = subprocess.run(
        cmd,
        check=False,
        timeout=timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    if cp.returncode != 0:
        print("command failed; tail:", "\n".join(cp.stdout.splitlines()[-40:]), flush=True)
        if check:
            cp.check_returncode()
    return cp


def slug(text: str) -> str:
    keep = "".join(c if c.isalnum() else "_" for c in text.strip().lower())
    while "__" in keep:
        keep = keep.replace("__", "_")
    return keep.strip("_")[:80] or "x"


def download_clip(row: dict[str, Any], video_dir: Path, height: int) -> Path | None:
    out = video_dir / f"{row['video_id']}.mp4"
    if out.exists() and out.stat().st_size > 100_000:
        return out
    tmp = video_dir / f"{row['video_id']}.%(ext)s"
    url = f"https://www.youtube.com/watch?v={row['yt_id']}"
    section = f"*{float(row['start_s']):.3f}-{float(row['end_s']):.3f}"
    base = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--quiet",
        "--no-progress",
        "--no-warnings",
        "--force-ipv4",
        "--download-sections",
        section,
        "--force-keyframes-at-cuts",
        "--merge-output-format",
        "mp4",
        "-f",
        f"bv*[height<={height}]+ba/b[height<={height}]/best[height<={height}]/best",
        "-o",
        str(tmp),
        url,
    ]
    attempts = [base, base[:3] + ["--extractor-args", "youtube:player_client=android,web_embedded"] + base[3:]]
    for cmd in attempts:
        try:
            run(cmd, check=True, timeout=300)
            candidates = sorted(video_dir.glob(f"{row['video_id']}.*"), key=lambda p: p.stat().st_size, reverse=True)
            for c in candidates:
                if c.suffix.lower() == ".mp4" and c.stat().st_size > 100_000:
                    if c != out:
                        c.replace(out)
                    return out
        except Exception as e:
            print(f"download failed for {row['video_id']}: {e}", flush=True)
    return out if out.exists() and out.stat().st_size > 100_000 else None


def mean_unit(pred: Any) -> np.ndarray | None:
    arr = np.asarray(pred, dtype=np.float32)
    if arr.ndim == 0 or arr.size == 0:
        return None
    if arr.ndim == 2:
        arr = arr.mean(axis=0)
    arr = arr.reshape(-1)
    n = float(np.linalg.norm(arr))
    if not np.isfinite(n) or n <= 0:
        return None
    return (arr / n).astype(np.float32)


def audio_video_events(*, video_path: str | None = None, audio_path: str | None = None) -> pd.DataFrame:
    if bool(video_path) == bool(audio_path):
        raise ValueError("exactly one of video_path/audio_path is required")
    event = {
        "type": "Video" if video_path else "Audio",
        "filepath": str(video_path or audio_path),
        "start": 0,
        "timeline": "default",
        "subject": "default",
    }
    # audio_only=True means skip word transcription/text-context stages. This avoids
    # gated Llama text extractor downloads while still using video+audio for refs and
    # TTS-audio for AD queries.
    return get_audio_and_text_events(pd.DataFrame([event]), audio_only=True)


def predict_vec(model: TribeModel, cache_file: Path, **kwargs: str) -> np.ndarray | None:
    if cache_file.exists():
        return np.load(cache_file)["v"]
    # TRIBE/neuralset emits unicode tqdm/progress bars that can crash the Windows
    # Colab CLI stdout decoder. Keep remote execution quiet and print our own
    # coarse progress after each vector.
    with open(os.devnull, "w", encoding="utf-8") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            df = audio_video_events(**kwargs)
            pred, _segments = model.predict(events=df, verbose=False)
    vec = mean_unit(pred)
    if vec is not None:
        np.savez_compressed(cache_file, v=vec)
    try:
        del pred, df
        torch.cuda.empty_cache()
    except Exception:
        pass
    gc.collect()
    return vec


def text_vec(model: TribeModel, text: str, text_dir: Path, cache_dir: Path) -> np.ndarray | None:
    text = str(text).strip()
    if not text:
        return None
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
    txt = text_dir / f"{slug(text[:48])}_{h}.txt"
    txt.write_text(text, encoding="utf-8")
    audio = text_dir / f"{slug(text[:48])}_{h}.mp3"
    if not audio.exists() or audio.stat().st_size == 0:
        try:
            lang = detect(text)
        except Exception:
            lang = "en"
        gTTS(text, lang=lang).save(str(audio))
    return predict_vec(model, cache_dir / f"tts_audio_{h}.npz", audio_path=str(audio))


def main() -> None:
    cfg = load_config()
    out_dir = Path(cfg["out_dir"]); out_dir.mkdir(parents=True, exist_ok=True)
    video_dir = out_dir / "videos"; video_dir.mkdir(exist_ok=True)
    text_dir = out_dir / "texts"; text_dir.mkdir(exist_ok=True)
    vec_cache = out_dir / "vec_cache"; vec_cache.mkdir(exist_ok=True)

    metadata = json.loads(Path(cfg["metadata_path"]).read_text(encoding="utf-8"))
    if cfg.get("limit"):
        metadata = metadata[: int(cfg["limit"])]
    print(json.dumps({
        "n_records": len(metadata),
        "metadata_path": cfg["metadata_path"],
        "out_dir": str(out_dir),
        "cuda": torch.cuda.is_available(),
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }, indent=2), flush=True)

    t0 = time.time()
    model = TribeModel.from_pretrained(cfg["model_name"], cache_folder=cfg["cache_folder"])
    print(f"model loaded in {time.time() - t0:.1f}s", flush=True)

    vecs: dict[str, dict[str, np.ndarray]] = {}
    failures: list[dict[str, str]] = []
    for i, row in enumerate(metadata, start=1):
        vid = row["video_id"]
        print(f"\n[{i}/{len(metadata)}] {vid}", flush=True)
        out: dict[str, np.ndarray] = {}
        video_path = download_clip(row, video_dir, int(cfg["video_height"]))
        if video_path is None:
            failures.append({"video_id": vid, "stage": "download", "error": "download failed"})
            print("  video download failed; text queries still computed, ref missing", flush=True)
        else:
            try:
                ref = predict_vec(model, vec_cache / f"ref_{vid}.npz", video_path=str(video_path))
                if ref is not None:
                    out["ref"] = ref
                    print("  ref ok", flush=True)
            except Exception as e:
                failures.append({"video_id": vid, "stage": "ref", "error": repr(e)})
                print(f"  ref error: {e}", flush=True)
        for tier in TIERS:
            try:
                q = text_vec(model, row.get(tier, ""), text_dir, vec_cache)
                if q is not None:
                    out[tier] = q
                    print(f"  {tier} ok", flush=True)
            except Exception as e:
                failures.append({"video_id": vid, "stage": tier, "error": repr(e)})
                print(f"  {tier} error: {e}", flush=True)
        vecs[vid] = out
        elapsed = time.time() - t0
        print(f"  elapsed={elapsed/60:.1f}m eta={(elapsed/i*(len(metadata)-i))/60:.1f}m", flush=True)

    refs = {vid: d["ref"] for vid, d in vecs.items() if "ref" in d}
    ref_vids = sorted(refs)
    if len(ref_vids) < int(cfg["min_refs"]):
        raise RuntimeError(f"Only {len(ref_vids)} reference vectors; cannot compute NCR")
    R = np.stack([refs[v] for v in ref_vids])

    rows: list[dict[str, Any]] = []
    for row in metadata:
        qvid = row["video_id"]
        d = vecs.get(qvid, {})
        for tier in TIERS:
            if tier not in d:
                continue
            sims = R @ d[tier]
            for ref_vid, cos in zip(ref_vids, sims):
                rows.append({"query_vid": qvid, "tier": tier, "ref_vid": ref_vid, "cos": f"{float(cos):.9f}"})

    sim_path = out_dir / "ncr_similarity.csv"
    with sim_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["query_vid", "tier", "ref_vid", "cos"])
        w.writeheader(); w.writerows(rows)
    np.savez_compressed(
        out_dir / "ncr_vectors.npz",
        ref_vids=np.array(ref_vids),
        R=R,
        **{f"{tier}__{vid}": d[tier] for vid, d in vecs.items() for tier in TIERS if tier in d},
    )
    summary = {
        "n_records": len(metadata),
        "n_refs": len(ref_vids),
        "n_similarity_rows": len(rows),
        "tiers": TIERS,
        "failures": failures,
        "elapsed_seconds": round(time.time() - t0, 1),
    }
    (out_dir / "ncr_run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote {sim_path} and ncr_vectors.npz", flush=True)

    # Colab CLI sessions can disappear immediately after long jobs. Emit a compact
    # gzip+base64 copy of the critical CSV in stdout so the local saved command log
    # is enough to recover results even when `colab download` misses the session.
    sim_gz_b64 = base64.b64encode(gzip.compress(sim_path.read_bytes(), compresslevel=9)).decode("ascii")
    print("NCR_SIM_CSV_GZ_B64_BEGIN", flush=True)
    for i in range(0, len(sim_gz_b64), 120):
        print(sim_gz_b64[i:i+120], flush=True)
    print("NCR_SIM_CSV_GZ_B64_END", flush=True)


if __name__ == "__main__":
    main()
