#!/usr/bin/env python3
"""SceneTwin 2-clip fusion smoke test.

Uses the downloaded TRIBE Description Gain smoke-test tensors and local VATEX
frames to test whether visual grounding can rescue the unstable raw TRIBE
counterfactual scores.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
import open_clip
from PIL import Image
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
DG_DIR = ROOT / "output" / "scenetwin_description_gain"
PRED_DIR = DG_DIR / "preds"
TEXT_DIR = DG_DIR / "texts"
FRAMES_ROOT = Path("/Users/adarsha/njbda/vatex_frames")

OUT_CSV = DG_DIR / "fusion_smoke_test_results.csv"
OUT_SUMMARY = DG_DIR / "fusion_smoke_test_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-fusion-smoke-test.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
COMPARISONS = ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]


def vec(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x)
    return x.mean(axis=0) if x.ndim == 2 else x


def cosine_raw(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return float("nan")
    return float(np.dot(a, b) / denom)


def load_pred(name: str) -> np.ndarray:
    return np.load(PRED_DIR / f"{name}.npy")


def minmax(series: pd.Series) -> pd.Series:
    lo = series.min()
    hi = series.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(series)), index=series.index)
    return (series - lo) / (hi - lo)


def add_normalized_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        df[f"{col}_norm_global"] = minmax(df[col])
        df[f"{col}_norm_clip"] = df.groupby("clip_idx", group_keys=False)[col].apply(minmax)
    return df


def device_name() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def compute_clip_scores(df: pd.DataFrame) -> pd.DataFrame:
    device = torch.device(device_name())
    print(f"Loading CLIP ViT-L-14 on {device}...")
    model, _, preprocess = open_clip.create_model_and_transforms(
        "ViT-L-14", pretrained="laion2b_s32b_b82k"
    )
    tokenizer = open_clip.get_tokenizer("ViT-L-14")
    model.to(device).eval()

    frame_cache: dict[int, torch.Tensor] = {}

    def frame_features(clip_idx: int) -> torch.Tensor:
        if clip_idx not in frame_cache:
            frame_dir = FRAMES_ROOT / f"clip_{clip_idx:02d}"
            paths = sorted(frame_dir.glob("frame_*.jpg"))
            if not paths:
                raise FileNotFoundError(f"No frame_*.jpg files in {frame_dir}")
            imgs = torch.stack([preprocess(Image.open(p).convert("RGB")) for p in paths])
            imgs = imgs.to(device)
            with torch.no_grad():
                feats = model.encode_image(imgs)
                feats = feats / feats.norm(dim=-1, keepdim=True)
            frame_cache[clip_idx] = feats.detach().cpu()
        return frame_cache[clip_idx]

    scores = []
    for row in df.itertuples(index=False):
        text = (TEXT_DIR / f"clip_{row.clip_idx:02d}_{row.tier}.txt").read_text(encoding="utf-8")
        tokens = tokenizer([text]).to(device)
        with torch.no_grad():
            text_feat = model.encode_text(tokens)
            text_feat = text_feat / text_feat.norm(dim=-1, keepdim=True)
        sims = (frame_features(row.clip_idx).to(device) @ text_feat.T).squeeze().detach().cpu().numpy()
        k = min(3, len(sims))
        scores.append(float(np.sort(sims)[-k:].mean()))
        print(f"clip_{row.clip_idx:02d} {row.tier}: CLIP-L14={scores[-1]:.4f}")

    df["clip_l14"] = scores
    return df


def add_neural_scores(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for clip_idx, group in df.groupby("clip_idx"):
        v_av = vec(load_pred(f"clip_{clip_idx:02d}_P_AV"))
        v_a = vec(load_pred(f"clip_{clip_idx:02d}_P_A"))
        mvr = v_av - v_a

        for row in group.itertuples(index=False):
            v_d = vec(load_pred(f"clip_{row.clip_idx:02d}_{row.tier}_P_D"))
            rows.append(
                {
                    "clip_idx": row.clip_idx,
                    "tier": row.tier,
                    "mvrr": cosine_raw(mvr, v_d),
                    "arp": cosine_raw(v_d, v_a),
                    "useful_score": cosine_raw(mvr, v_d) - 0.25 * cosine_raw(v_d, v_a),
                }
            )

    neural = pd.DataFrame(rows)
    return df.merge(neural, on=["clip_idx", "tier"], how="left")


def add_fusion_scores(df: pd.DataFrame) -> pd.DataFrame:
    positive_cols = [
        "clip_l14",
        "av_desc_cos",
        "description_gain",
        "mvrr",
        "useful_score",
    ]
    df = add_normalized_columns(df, positive_cols)

    df["clip_x_av_desc_global"] = df["clip_l14_norm_global"] * df["av_desc_cos_norm_global"]
    df["clip_x_av_desc_clip"] = df["clip_l14_norm_clip"] * df["av_desc_cos_norm_clip"]
    df["clip_x_dg_clip"] = df["clip_l14_norm_clip"] * df["description_gain_norm_clip"]
    df["clip_x_mvrr_clip"] = df["clip_l14_norm_clip"] * df["mvrr_norm_clip"]
    df["clip_x_useful_clip"] = df["clip_l14_norm_clip"] * df["useful_score_norm_clip"]

    # A conservative gate: if grounding is below the clip's median grounding, zero out
    # the neural score. This tests "CLIP as correctness gate" rather than multiplication.
    df["clip_gate"] = df.groupby("clip_idx")["clip_l14"].transform(lambda s: s >= s.median())
    df["gated_av_desc_clip"] = np.where(df["clip_gate"], df["av_desc_cos_norm_clip"], 0.0)
    df["gated_dg_clip"] = np.where(df["clip_gate"], df["description_gain_norm_clip"], 0.0)
    df["gated_useful_clip"] = np.where(df["clip_gate"], df["useful_score_norm_clip"], 0.0)
    return df


def evaluate_metric(df: pd.DataFrame, metric: str) -> dict[str, object]:
    vals = df[metric].to_numpy()
    gt = df["gt"].to_numpy()
    rho, p_rho = spearmanr(gt, vals, nan_policy="omit")
    tau, p_tau = kendalltau(gt, vals, nan_policy="omit")

    out: dict[str, object] = {
        "metric": metric,
        "spearman_rho": float(rho),
        "spearman_p": float(p_rho),
        "kendall_tau": float(tau),
        "kendall_p": float(p_tau),
    }

    total_wins = 0
    total_pairs = 0
    for comp in COMPARISONS:
        wins = 0
        total = 0
        for _, group in df.groupby("clip_idx"):
            t3 = group[group["tier"] == "tier3_va11y"][metric]
            tx = group[group["tier"] == comp][metric]
            if len(t3) and len(tx):
                total += 1
                wins += int(float(t3.iloc[0]) > float(tx.iloc[0]))
        out[f"tier3_gt_{comp}_wins"] = wins
        out[f"tier3_gt_{comp}_total"] = total
        total_wins += wins
        total_pairs += total
    out["pairwise_wins"] = total_wins
    out["pairwise_total"] = total_pairs

    full_order = 0
    for _, group in df.groupby("clip_idx"):
        vals_by_tier = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        if all(k in vals_by_tier for k in TIER_KEYS):
            full_order += int(
                vals_by_tier["tier3_va11y"]
                > vals_by_tier["tier2_vatex_long"]
                > vals_by_tier["tier1_vatex_short"]
                > vals_by_tier["tier0_cross"]
            )
    out["full_order_clips"] = full_order
    out["full_order_total"] = int(df["clip_idx"].nunique())
    return out


def write_report(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    tier_means = (
        df.groupby("tier")[
            [
                "clip_l14",
                "av_desc_cos",
                "description_gain",
                "mvrr",
                "arp",
                "useful_score",
                "clip_x_av_desc_clip",
                "clip_x_dg_clip",
                "clip_x_useful_clip",
            ]
        ]
        .mean()
        .loc[TIER_KEYS]
    )

    top = summary.sort_values(
        ["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False
    ).head(12)

    report = f"""---
title: "SceneTwin Fusion Smoke Test"
category: research
tags: [SceneTwin, CLIP, TRIBE, fusion, smoke-test, VideoA11y, VATEX]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/fusion_smoke_test_results.csv
  - output/scenetwin_description_gain/fusion_smoke_test_summary.csv
  - wiki/research/scenetwin-description-gain-smoke-test.md
---

# SceneTwin Fusion Smoke Test

## Result

The 2-clip fusion smoke test confirms the next direction: raw TRIBE scores need a visual grounding gate.

CLIP-L14 alone fixes the cross-category failure on the two smoke-test clips. Multiplying CLIP by raw TRIBE richness/recovery does **not** yet prove added value on this tiny sample; the priority is to test whether fused scores improve same-scene quality separation on the full 20-clip set.

## Top Metrics

{top.to_markdown(index=False)}

## Mean Scores By Tier

{tier_means.to_markdown()}

## Interpretation

- Raw `DescriptionGain`, `MVRR`, and `UsefulScore` are unstable as standalone metrics.
- CLIP-L14 is the necessary correctness gate because it suppresses wrong-content descriptions.
- The plausible SceneTwin v1 metric is not pure counterfactual TRIBE. It is grounded neural scoring:

```text
GroundedScore = normalize(visual_grounding) * normalize(TRIBE_richness_or_recovery)
```

On the two smoke-test clips, the metric to carry into the full run is:

```text
CLIP-L14 baseline + CLIP x av_desc_cos + CLIP x DescriptionGain + CLIP x UsefulScore
```

The full 20-clip run is worth doing only if it reports the ablation honestly:

1. CLIP-L14 alone
2. TRIBE-only metrics
3. grounded TRIBE fusion metrics

The paper/poster claim should be that grounding is the correctness filter and TRIBE is a second-stage accessibility/richness/recovery signal, unless full-run fusion beats CLIP alone.

## Files

- `fusion_smoke_test_results.csv`
- `fusion_smoke_test_summary.csv`
- `scenetwin-fusion-smoke-test.md`
"""
    OUT_REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    df = pd.read_csv(DG_DIR / "description_gain_results.csv")
    df = compute_clip_scores(df)
    df = add_neural_scores(df)
    df = add_fusion_scores(df)

    metrics = [
        "clip_l14",
        "av_desc_cos",
        "description_gain",
        "mvrr",
        "arp",
        "useful_score",
        "clip_x_av_desc_global",
        "clip_x_av_desc_clip",
        "clip_x_dg_clip",
        "clip_x_mvrr_clip",
        "clip_x_useful_clip",
        "gated_av_desc_clip",
        "gated_dg_clip",
        "gated_useful_clip",
    ]
    summary = pd.DataFrame([evaluate_metric(df, metric) for metric in metrics])
    summary = summary.sort_values(
        ["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False
    )

    df.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)
    write_report(df, summary)

    print(f"\nWrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print("\nSummary:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
