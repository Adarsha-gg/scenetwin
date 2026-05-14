#!/usr/bin/env python3
"""Try multiple closure metrics on the visual-closure pilot tensors.

Question: the default L2 closure is verbosity-confounded — longer AD perturbs
TRIBE more regardless of content quality, so tier1 (13 words) beats tier3
(62 words). Try magnitude-invariant alternatives and see which (if any) gives
monotonic tier3 > tier2 > tier1 > tier0 ranking on the 2 clips we have.

Inputs: /Users/adarsha/Knowledge/output/visual_closure_preds/clip_{01,03}_*.npy
        /Users/adarsha/Knowledge/output/colab_upload_closure/glasser_roi_mask.csv

Output: /Users/adarsha/Knowledge/output/reports/scenetwin-closure-metric-sweep.md
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path("/Users/adarsha/Knowledge")
PREDS = ROOT / "output" / "visual_closure_preds"
MASK_CSV = ROOT / "output" / "colab_upload_closure" / "glasser_roi_mask.csv"
OUT_MD = ROOT / "output" / "reports" / "scenetwin-closure-metric-sweep.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
CLIPS = ["clip_01", "clip_03"]

# Visual ROIs in Glasser mask
VIS_ROIS = {"object_motion", "scene_spatial", "early_visual",
            "lateral_object_loc", "scene_ppa", "motion_mt"}


def load_mask() -> np.ndarray:
    df = pd.read_csv(MASK_CSV)
    vis = df[df["roi"].isin(VIS_ROIS)]["vertex"].astype(int).values
    print(f"Visual ROI vertices: {len(vis)} / 20484")
    return vis


def load_tensor(name: str) -> np.ndarray:
    return np.load(PREDS / f"{name}.npy")


def align_tr(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Crop both arrays to the shorter TR length."""
    n = min(a.shape[0], b.shape[0])
    return a[:n], b[:n]


# ── Metric definitions ────────────────────────────────────────────────────
def m_l2(p_a_ad, p_av, p_a):
    """Original closure: dist(P_A, P_AV) - dist(P_A+AD, P_AV). Positive = AD helped."""
    p_a_ad, p_av_crop = align_tr(p_a_ad, p_av)
    _, p_a_crop = align_tr(p_a, p_av_crop)
    d_base = np.linalg.norm(p_a_crop - p_av_crop)
    d_ad = np.linalg.norm(p_a_ad - p_av_crop)
    return d_base - d_ad


def m_cosine(p_a_ad, p_av, p_a):
    """Cosine sim of flattened patterns. Scale-invariant."""
    p_a_ad, p_av_crop = align_tr(p_a_ad, p_av)
    _, p_a_crop = align_tr(p_a, p_av_crop)

    def cos(x, y):
        x, y = x.ravel(), y.ravel()
        return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))

    return cos(p_a_ad, p_av_crop) - cos(p_a_crop, p_av_crop)


def m_per_voxel_corr(p_a_ad, p_av, p_a):
    """Per-voxel Pearson across TRs, then average. Temporal pattern, not magnitude."""
    p_a_ad, p_av_crop = align_tr(p_a_ad, p_av)
    _, p_a_crop = align_tr(p_a, p_av_crop)
    if p_av_crop.shape[0] < 3:
        return np.nan

    def avg_corr(x, y):
        # corr per voxel across TR axis
        x = x - x.mean(0, keepdims=True)
        y = y - y.mean(0, keepdims=True)
        num = (x * y).sum(0)
        den = np.sqrt((x**2).sum(0) * (y**2).sum(0)) + 1e-9
        return float(np.nanmean(num / den))

    return avg_corr(p_a_ad, p_av_crop) - avg_corr(p_a_crop, p_av_crop)


def m_voxel_direction(p_a_ad, p_av, p_a):
    """Fraction of voxels moving FROM p_a TOWARD p_av when AD is added."""
    p_a_ad, p_av_crop = align_tr(p_a_ad, p_av)
    _, p_a_crop = align_tr(p_a, p_av_crop)
    gap_before = p_av_crop - p_a_crop          # what AD needs to fill
    move = p_a_ad - p_a_crop                   # what AD added
    # Voxels where move and gap point same direction = good
    aligned = (np.sign(move) == np.sign(gap_before)).mean()
    return float(aligned) - 0.5  # baseline 0.5 = random


def m_topk_gap(p_a_ad, p_av, p_a, k_frac=0.1):
    """Closure restricted to top-K voxels where P_A is most different from P_AV."""
    p_a_ad, p_av_crop = align_tr(p_a_ad, p_av)
    _, p_a_crop = align_tr(p_a, p_av_crop)
    gap = np.abs(p_av_crop - p_a_crop).mean(0)  # per-voxel gap, avg over TR
    k = int(len(gap) * k_frac)
    top = np.argsort(-gap)[:k]
    d_base = np.linalg.norm(p_a_crop[:, top] - p_av_crop[:, top])
    d_ad = np.linalg.norm(p_a_ad[:, top] - p_av_crop[:, top])
    return d_base - d_ad


METRICS = {
    "L2_closure (orig)": m_l2,
    "cosine_closure":    m_cosine,
    "per_voxel_corr":    m_per_voxel_corr,
    "voxel_direction":   m_voxel_direction,
    "topk10_gap_L2":     m_topk_gap,
}


def run(restrict_to: np.ndarray | None, label: str) -> pd.DataFrame:
    rows = []
    for clip in CLIPS:
        p_av = load_tensor(f"{clip}_P_AV")
        p_a = load_tensor(f"{clip}_P_A")
        if restrict_to is not None:
            p_av = p_av[:, restrict_to]
            p_a = p_a[:, restrict_to]
        for tier in TIERS:
            p_a_ad = load_tensor(f"{clip}_{tier}_P_A_ADtext")
            if restrict_to is not None:
                p_a_ad = p_a_ad[:, restrict_to]
            for mname, mfn in METRICS.items():
                rows.append({
                    "scope": label, "clip": clip, "tier": tier,
                    "metric": mname,
                    "value": mfn(p_a_ad, p_av, p_a),
                })
    return pd.DataFrame(rows)


def score_monotonicity(df: pd.DataFrame) -> pd.DataFrame:
    """For each (scope, metric), does ordering match tier3 > tier2 > tier1 > tier0?"""
    out = []
    rank_target = {"tier0_cross": 0, "tier1_vatex_short": 1,
                   "tier2_vatex_long": 2, "tier3_va11y": 3}
    for (scope, metric), g in df.groupby(["scope", "metric"]):
        per_clip_monotonic = 0
        per_clip_tier3_top = 0
        per_clip_tier3_beats_tier0 = 0
        n_clips = 0
        for clip, gg in g.groupby("clip"):
            ordered = gg.sort_values("value", ascending=False)["tier"].tolist()
            ranks_seen = [rank_target[t] for t in ordered]
            if ranks_seen == [3, 2, 1, 0]:
                per_clip_monotonic += 1
            if ranks_seen[0] == 3:
                per_clip_tier3_top += 1
            t3_val = gg[gg["tier"] == "tier3_va11y"]["value"].iloc[0]
            t0_val = gg[gg["tier"] == "tier0_cross"]["value"].iloc[0]
            if t3_val > t0_val:
                per_clip_tier3_beats_tier0 += 1
            n_clips += 1
        out.append({
            "scope": scope, "metric": metric,
            "n_clips": n_clips,
            "fully_monotonic": per_clip_monotonic,
            "tier3_ranked_top": per_clip_tier3_top,
            "tier3_beats_tier0": per_clip_tier3_beats_tier0,
        })
    return pd.DataFrame(out).sort_values(
        ["fully_monotonic", "tier3_ranked_top", "tier3_beats_tier0"],
        ascending=False)


def main():
    vis = load_mask()
    print("\nLoading tensors and computing metrics ...")
    df_full = run(None, "whole_cortex")
    df_vis = run(vis, "visual_roi")
    df = pd.concat([df_full, df_vis], ignore_index=True)

    summary = score_monotonicity(df)
    print("\n=== Per-tier values (raw) ===")
    pivot = df.pivot_table(
        index=["scope", "metric", "clip"], columns="tier", values="value")
    print(pivot.round(4).to_string())

    print("\n=== Monotonicity ranking ===")
    print(summary.to_string(index=False))

    out_csv = OUT_MD.with_suffix(".csv")
    df.to_csv(out_csv, index=False)
    summary_csv = OUT_MD.parent / "scenetwin-closure-metric-sweep-summary.csv"
    summary.to_csv(summary_csv, index=False)

    md = ["# SceneTwin closure metric sweep",
          "",
          "Comparing 5 closure metrics on the 2 clips that finished the visual-closure Colab "
          "(clip_01, clip_03). Goal: find a magnitude-invariant metric where tier3 (pro AD) "
          "ranks above tier0 (cross-category AD).",
          "",
          "## Monotonicity summary",
          "",
          summary.to_markdown(index=False),
          "",
          "## Raw per-tier values",
          "",
          pivot.round(4).to_markdown(),
          ""]
    OUT_MD.write_text("\n".join(md))
    print(f"\nWrote {OUT_MD}")


if __name__ == "__main__":
    main()
