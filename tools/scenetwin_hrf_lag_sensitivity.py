#!/usr/bin/env python3
"""HRF/frame-alignment sensitivity test for need-weighted grounding.

This checks whether the current frame matching is silently off by the approximate
hemodynamic lag. It evaluates need-weighted CLIP grounding at several positive
frame offsets without overwriting the main metric file.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import numpy as np
import open_clip
import pandas as pd
import torch
from PIL import Image
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
NEED_CSV = DG_DIR / "neural_description_need_curve.csv"
EVENT_CSV = DG_DIR / "neural_event_test_results.csv"
TEXT_DIR = DG_DIR / "texts"
VIDEO_ROOT = Path("/Users/adarsha/njbda/vatex_clips")
FRAME_ROOT = ROOT / "output" / "scenetwin_hrf_lag_frames"
OUT_CSV = DG_DIR / "hrf_lag_sensitivity_results.csv"
OUT_SUMMARY = DG_DIR / "hrf_lag_sensitivity_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-hrf-lag-sensitivity.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-hrf-lag-sensitivity.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
GT = {"tier3_va11y": 3, "tier2_vatex_long": 2, "tier1_vatex_short": 1, "tier0_cross": 0}
LAGS_SECONDS = [0.0, 2.5, 5.0]


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    weights = np.asarray(weights, dtype=float)
    values = np.asarray(values, dtype=float)
    if weights.sum() <= 1e-9:
        return float(values.mean())
    return float(np.dot(values, weights) / weights.sum())


def extract_frame(video: Path, timestamp: float, out: Path) -> None:
    if out.exists():
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(video),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def video_duration(video: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def frame_path_for(row: object, lag_s: float, clip_duration: float) -> Path:
    center = (float(row.start_s) + float(row.end_s)) / 2.0
    timestamp = min(max(center + lag_s, 0.0), max(clip_duration - 0.35, 0.0))
    lag_name = f"lag_{lag_s:.1f}".replace(".", "p")
    return FRAME_ROOT / lag_name / f"clip_{int(row.clip_idx):02d}" / f"t{int(row.t):02d}_{timestamp:.2f}.jpg"


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    rho, p_rho = spearmanr(df["gt"], df[metric], nan_policy="omit")
    tau, p_tau = kendalltau(df["gt"], df[metric], nan_policy="omit")
    full = 0
    pairwise = 0
    for _, group in df.groupby("clip_idx"):
        vals = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        full += int(vals["tier3_va11y"] > vals["tier2_vatex_long"] > vals["tier1_vatex_short"] > vals["tier0_cross"])
        for comp in ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]:
            pairwise += int(vals["tier3_va11y"] > vals[comp])
    return {
        "metric": metric,
        "spearman_rho": float(rho),
        "spearman_p": float(p_rho),
        "kendall_tau": float(tau),
        "kendall_p": float(p_tau),
        "pairwise_wins": pairwise,
        "pairwise_total": int(df["clip_idx"].nunique() * 3),
        "full_order_clips": full,
        "full_order_total": int(df["clip_idx"].nunique()),
    }


def main() -> None:
    device = torch.device(device_name())
    print(f"Loading CLIP ViT-L-14 on {device}...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="laion2b_s32b_b82k"
    )
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    need = pd.read_csv(NEED_CSV)
    events = pd.read_csv(EVENT_CSV)
    weights = need.merge(
        events[["clip_idx", "t", "visual_event_score"]],
        on=["clip_idx", "t"],
        how="left",
    )
    weights["critical_weight"] = np.maximum(weights["need_score"], weights["visual_event_score"].fillna(0.0))

    text_cache = {}
    for clip_idx in sorted(weights["clip_idx"].unique()):
        for tier in TIER_KEYS:
            text = (TEXT_DIR / f"clip_{int(clip_idx):02d}_{tier}.txt").read_text(encoding="utf-8")
            with torch.no_grad():
                tokens = tokenizer([text]).to(device)
                feat = model.encode_text(tokens)
                feat = feat / feat.norm(dim=-1, keepdim=True)
            text_cache[(int(clip_idx), tier)] = feat

    rows = []
    for lag_s in LAGS_SECONDS:
        image_cache: dict[int, torch.Tensor] = {}

        def image_features(clip_idx: int) -> torch.Tensor:
            if clip_idx not in image_cache:
                group = weights[weights["clip_idx"] == clip_idx].sort_values("t")
                video = VIDEO_ROOT / f"clip_{int(clip_idx):02d}.mp4"
                clip_duration = min(float(group["end_s"].max()), video_duration(video))
                imgs = []
                for row in group.itertuples(index=False):
                    path = frame_path_for(row, lag_s, clip_duration)
                    timestamp = min(
                        max((float(row.start_s) + float(row.end_s)) / 2.0 + lag_s, 0.0),
                        max(clip_duration - 0.35, 0.0),
                    )
                    extract_frame(video, timestamp, path)
                    imgs.append(preprocess(Image.open(path).convert("RGB")))
                with torch.no_grad():
                    batch = torch.stack(imgs).to(device)
                    feats = model.encode_image(batch)
                    feats = feats / feats.norm(dim=-1, keepdim=True)
                image_cache[clip_idx] = feats
            return image_cache[clip_idx]

        for clip_idx in sorted(weights["clip_idx"].unique()):
            group = weights[weights["clip_idx"] == clip_idx].sort_values("t")
            feats = image_features(int(clip_idx))
            for tier in TIER_KEYS:
                sims = (feats @ text_cache[(int(clip_idx), tier)].T).squeeze().detach().cpu().numpy()
                rows.append(
                    {
                        "lag_s": lag_s,
                        "clip_idx": int(clip_idx),
                        "tier": tier,
                        "gt": GT[tier],
                        "clip_mean": float(sims.mean()),
                        "clip_top3": float(np.sort(sims)[-min(3, len(sims)):].mean()),
                        "need_weighted_clip": weighted_average(sims, group["need_score"].to_numpy()),
                        "critical_weighted_clip": weighted_average(sims, group["critical_weight"].to_numpy()),
                    }
                )
                print(
                    f"lag={lag_s:.1f}s clip_{int(clip_idx):02d} {tier}: "
                    f"need={rows[-1]['need_weighted_clip']:.4f}"
                )

    out = pd.DataFrame(rows)
    summary_rows = []
    for lag_s, group in out.groupby("lag_s"):
        for metric in ["clip_mean", "clip_top3", "need_weighted_clip", "critical_weighted_clip"]:
            stats = evaluate(group, metric)
            stats["lag_s"] = lag_s
            summary_rows.append(stats)
    summary = pd.DataFrame(summary_rows).sort_values(
        ["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False
    )

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    best = summary.head(12)
    report = f"""---
title: "SceneTwin HRF Lag Sensitivity"
category: research
tags: [SceneTwin, TRIBE, HRF, CLIP, grounding]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/hrf_lag_sensitivity_results.csv
  - output/scenetwin_description_gain/hrf_lag_sensitivity_summary.csv
---

# SceneTwin HRF Lag Sensitivity

## Question

Does need-weighted grounding change if TRIBE rows are matched to video frames with a positive frame offset for hemodynamic lag?

## Result

{best.to_markdown(index=False)}

## Interpretation

This script does not assume the right lag. It gives us a sensitivity table. If `0.0s` wins, the current extracted validation frames are likely already closer to the model's effective alignment. If `5.0s` wins, the previous frame matching was probably offset.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")
    print(summary)
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
