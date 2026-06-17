#!/usr/bin/env python3
"""Sanity check: our CLIP pipeline matches benchmark clip_top3 on same 18 clips."""
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
FRAMES = ROOT / "output" / "scenetwin_timing_20clip" / "adqa_frames"
BENCH = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "clip_scores" / "need_weighted_grounding_results.csv")
FORECAST = pd.read_csv(ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv")
OUT = Path(__file__).resolve().parents[1] / "output" / "benchmark_clip_sanity.csv"


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def clip_top3(model, preprocess, tokenizer, device, frame_paths, text):
    imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in frame_paths]).to(device)
    tokens = tokenizer([text]).to(device)
    with torch.no_grad():
        img_f = model.encode_image(imgs)
        img_f = img_f / img_f.norm(dim=-1, keepdim=True)
        txt_f = model.encode_text(tokens)
        txt_f = txt_f / txt_f.norm(dim=-1, keepdim=True)
        sims = (img_f @ txt_f.T).squeeze().cpu().numpy()
    k = min(3, len(sims))
    return float(np.sort(sims)[-k:].mean())


def main() -> None:
    device = torch.device(device_name())
    model, _, preprocess = open_clip.create_model_and_transforms("ViT-L-14", pretrained="laion2b_s32b_b82k")
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    rows = []
    for cidx in sorted(BENCH["clip_idx"].unique()):
        frame_dir = FRAMES / f"clip_{int(cidx):02d}"
        paths = sorted(frame_dir.glob("frame_*.jpg"))
        if not paths:
            continue
        fc = FORECAST[FORECAST["clip_idx"] == cidx].iloc[0]
        for tier in ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]:
            col = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
                   "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}[tier]
            text = str(fc[col])
            ours = clip_top3(model, preprocess, tokenizer, device, paths, text)
            ref = float(BENCH[(BENCH["clip_idx"] == cidx) & (BENCH["tier"] == tier)]["clip_top3"].iloc[0])
            rows.append({"clip_idx": cidx, "tier": tier, "ours": ours, "benchmark": ref, "delta": ours - ref})

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    r, _ = spearmanr(df["ours"], df["benchmark"])
    mae = df["delta"].abs().mean()
    print(f"Sanity: ours vs benchmark clip_top3 Spearman={r:.3f} MAE={mae:.4f}")
    print(f"Wrote {OUT}")
    if r < 0.9:
        print("WARNING: pipeline diverges from benchmark CLIP", file=sys.stderr)


if __name__ == "__main__":
    main()
