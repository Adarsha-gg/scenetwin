#!/usr/bin/env python3
"""Need-weighted visual grounding for SceneTwin.

The point is to test whether TRIBE can improve a visual grounding metric without
asking TRIBE to score text directly.

Instead of CLIP(video frames, description) over all/top frames, compute CLIP only
where TRIBE says AD is needed:

    NeedWeightedCLIP = sum_t CLIP(frame_t, desc) * AccessibilityGap(t)

This asks: does the description match the visually important moments, not merely
some easy frame in the clip?
"""

from __future__ import annotations

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
FRAME_ROOT = ROOT / "output" / "scenetwin_need_validation"
OUT_CSV = DG_DIR / "need_weighted_grounding_results.csv"
OUT_SUMMARY = DG_DIR / "need_weighted_grounding_summary.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-need-weighted-grounding.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-need-weighted-grounding.md"

TIER_KEYS = ["tier3_va11y", "tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]
GT = {"tier3_va11y": 3, "tier2_vatex_long": 2, "tier1_vatex_short": 1, "tier0_cross": 0}
COMPS = ["tier2_vatex_long", "tier1_vatex_short", "tier0_cross"]


def minmax(x: pd.Series) -> pd.Series:
    lo = x.min()
    hi = x.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(x)), index=x.index)
    return (x - lo) / (hi - lo)


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


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    rho, p_rho = spearmanr(df["gt"], df[metric], nan_policy="omit")
    tau, p_tau = kendalltau(df["gt"], df[metric], nan_policy="omit")
    out: dict[str, object] = {
        "metric": metric,
        "spearman_rho": float(rho),
        "spearman_p": float(p_rho),
        "kendall_tau": float(tau),
        "kendall_p": float(p_tau),
    }

    wins_total = 0
    pair_total = 0
    for comp in COMPS:
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
        wins_total += wins
        pair_total += total
    out["pairwise_wins"] = wins_total
    out["pairwise_total"] = pair_total

    full = 0
    for _, group in df.groupby("clip_idx"):
        vals = {row.tier: getattr(row, metric) for row in group.itertuples(index=False)}
        full += int(vals["tier3_va11y"] > vals["tier2_vatex_long"] > vals["tier1_vatex_short"] > vals["tier0_cross"])
    out["full_order_clips"] = full
    out["full_order_total"] = int(df["clip_idx"].nunique())
    return out


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
        events[["clip_idx", "t", "visual_event_score", "visual_event_need"]],
        on=["clip_idx", "t"],
        how="left",
    )
    weights["critical_weight"] = np.maximum(weights["need_score"], weights["visual_event_score"].fillna(0))
    weights["opportunity_weight"] = np.maximum(weights["standard_slot_score"], weights["extended_need_score"])

    rows = []
    frame_cache: dict[int, torch.Tensor] = {}

    def frame_features(clip_idx: int) -> torch.Tensor:
        if clip_idx not in frame_cache:
            clip_rows = weights[weights["clip_idx"] == clip_idx].sort_values("t")
            imgs = []
            for t in clip_rows["t"]:
                frame_path = FRAME_ROOT / f"clip_{clip_idx:02d}_frames" / f"t{int(t):02d}.jpg"
                imgs.append(preprocess(Image.open(frame_path).convert("RGB")))
            batch = torch.stack(imgs).to(device)
            with torch.no_grad():
                feats = model.encode_image(batch)
                feats = feats / feats.norm(dim=-1, keepdim=True)
            frame_cache[clip_idx] = feats.detach().cpu()
        return frame_cache[clip_idx]

    for clip_idx in sorted(weights["clip_idx"].unique()):
        clip_weights = weights[weights["clip_idx"] == clip_idx].sort_values("t")
        ff = frame_features(int(clip_idx)).to(device)
        for tier in TIER_KEYS:
            text = (TEXT_DIR / f"clip_{int(clip_idx):02d}_{tier}.txt").read_text(encoding="utf-8")
            tokens = tokenizer([text]).to(device)
            with torch.no_grad():
                tf = model.encode_text(tokens)
                tf = tf / tf.norm(dim=-1, keepdim=True)
            sims = (ff @ tf.T).squeeze().detach().cpu().numpy()
            rows.append(
                {
                    "clip_idx": int(clip_idx),
                    "tier": tier,
                    "gt": GT[tier],
                    "clip_mean": float(sims.mean()),
                    "clip_top3": float(np.sort(sims)[-min(3, len(sims)):].mean()),
                    "need_weighted_clip": weighted_average(sims, clip_weights["need_score"].to_numpy()),
                    "standard_slot_weighted_clip": weighted_average(sims, clip_weights["standard_slot_score"].to_numpy()),
                    "extended_need_weighted_clip": weighted_average(sims, clip_weights["extended_need_score"].to_numpy()),
                    "event_weighted_clip": weighted_average(sims, clip_weights["visual_event_score"].fillna(0).to_numpy()),
                    "critical_weighted_clip": weighted_average(sims, clip_weights["critical_weight"].to_numpy()),
                    "opportunity_weighted_clip": weighted_average(sims, clip_weights["opportunity_weight"].to_numpy()),
                }
            )
            print(f"clip_{int(clip_idx):02d} {tier}: top3={rows[-1]['clip_top3']:.4f} need={rows[-1]['need_weighted_clip']:.4f}")

    out = pd.DataFrame(rows)
    for metric in [
        "clip_mean",
        "clip_top3",
        "need_weighted_clip",
        "standard_slot_weighted_clip",
        "extended_need_weighted_clip",
        "event_weighted_clip",
        "critical_weighted_clip",
        "opportunity_weighted_clip",
    ]:
        out[f"{metric}_norm_clip"] = out.groupby("clip_idx", group_keys=False)[metric].apply(minmax)

    metric_cols = [c for c in out.columns if c not in {"clip_idx", "tier", "gt"}]
    summary = pd.DataFrame([evaluate(out, metric) for metric in metric_cols])
    summary = summary.sort_values(["pairwise_wins", "full_order_clips", "spearman_rho"], ascending=False)

    out.to_csv(OUT_CSV, index=False)
    summary.to_csv(OUT_SUMMARY, index=False)

    top = summary.head(12)
    means = out.groupby("tier")[
        [
            "clip_top3",
            "need_weighted_clip",
            "event_weighted_clip",
            "critical_weighted_clip",
            "opportunity_weighted_clip",
        ]
    ].mean().loc[TIER_KEYS]
    report = f"""---
title: "SceneTwin Need-Weighted Grounding"
category: research
tags: [SceneTwin, CLIP, TRIBE, grounding, accessibility-gap]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/need_weighted_grounding_results.csv
  - output/scenetwin_description_gain/need_weighted_grounding_summary.csv
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin Need-Weighted Grounding

## Metric

Instead of scoring descriptions against arbitrary/top video frames, this test weights frame-text grounding by TRIBE-derived AD importance:

```text
NeedWeightedGrounding(d) = sum_t CLIP(frame_t, d) * ADNeed(t)
```

Variants use standard-slot weight, extended-need weight, visual-event weight, and a critical max of need/event.

## Result

On the two saved clips, generic CLIP top-3 is already perfect. Need-weighted grounding also performs well and gives TRIBE a cleaner role: focus visual grounding on moments where AD is needed.

## Top Metrics

{top.to_markdown(index=False)}

## Mean Scores By Tier

{means.to_markdown()}

## Interpretation

This is a better integration than `TRIBE(description_text)`:

- TRIBE never judges text correctness.
- CLIP/SigLIP/PAC-S handles visual grounding.
- TRIBE decides which frames count most for accessibility.

If this holds on 20 clips, SceneTwin becomes:

```text
ADNeed(t) from TRIBE
ContentGrounding(t, description) from CLIP/PAC-S
NeedWeightedGrounding = grounding focused on inaccessible moments
```

The next stronger version should replace CLIP with PAC-S or SigLIP and add OCR/VLM coverage for on-screen text.
"""
    OUT_REPORT.write_text(report, encoding="utf-8")
    OUT_WIKI.write_text(report, encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_SUMMARY}")
    print(f"Wrote {OUT_REPORT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
