#!/usr/bin/env python3
"""Same motion+speech need proxy on benchmark clips — compare to TRIBE need-weighted CLIP."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "cursor" / "pipeline"))
from external_need_proxy import build_need_curve, speech_intervals  # noqa: E402

FRAMES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames"
FORECAST = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv")
BENCH_NW = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "clip_scores" / "need_weighted_grounding_results.csv")
OUT = Path(__file__).resolve().parents[1] / "output" / "benchmark_need_proxy_compare.csv"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
TIER_GT = {t: i for i, t in enumerate(TIERS)}
TIER_COL = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
            "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}


def weighted_avg(vals, w):
    w = np.asarray(w, dtype=float)
    return float(np.dot(vals, w) / w.sum()) if w.sum() > 1e-9 else float(np.mean(vals))


def main() -> None:
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    rows = []
    for cidx in sorted(FORECAST["clip_idx"].unique()):
        frame_paths = sorted((FRAMES / f"clip_{int(cidx):02d}").glob("frame_*.jpg"))
        videos = list((FRAMES / f"clip_{int(cidx):02d}").glob("*.mp4"))
        if not frame_paths:
            continue
        mp4 = videos[0] if videos else None
        if mp4 and mp4.exists():
            need_df = build_need_curve(f"clip_{cidx:02d}", mp4, frame_paths)
        else:
            need_df = pd.DataFrame({"need_score": np.ones(len(frame_paths)) / len(frame_paths)})
        w = need_df["need_score"].to_numpy()
        fc = FORECAST[FORECAST["clip_idx"] == cidx].iloc[0]
        imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in frame_paths]).to(device)
        with torch.no_grad():
            img_f = model.encode_image(imgs)
            img_f = img_f / img_f.norm(dim=-1, keepdim=True)
        for tier in TIERS:
            text = str(fc[TIER_COL[tier]])
            tokens = tokenizer([text]).to(device)
            with torch.no_grad():
                tf = model.encode_text(tokens)
                tf = tf / tf.norm(dim=-1, keepdim=True)
            sims = (img_f @ tf.T).squeeze().cpu().numpy()
            k = min(3, len(sims))
            proxy_nw = weighted_avg(sims, w)
            ref = float(BENCH_NW[(BENCH_NW["clip_idx"] == cidx) & (BENCH_NW["tier"] == tier)]["need_weighted_clip"].iloc[0])
            rows.append({"clip_idx": cidx, "tier": tier, "gt": TIER_GT[tier], "proxy_need_weighted": proxy_nw,
                         "tribe_need_weighted": ref, "delta": proxy_nw - ref})

    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    r_proxy, _ = spearmanr(df["gt"], df["proxy_need_weighted"])
    r_tribe, _ = spearmanr(df["gt"], df["tribe_need_weighted"])
    r_ref, _ = spearmanr(df["proxy_need_weighted"], df["tribe_need_weighted"])
    print(f"Benchmark proxy need-weighted ρ={r_proxy:.3f}")
    print(f"Benchmark TRIBE need-weighted ρ={r_tribe:.3f}")
    print(f"Proxy vs TRIBE column ρ={r_ref:.3f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
