"""Re-run TRIBE on the 18-clip benchmark under the new counterfactual proxy.

For each clip, predict:
  P_AV  = full video (audio + visual)
  P_A   = audio-only (extracted wav)
  P_AD  = AD text-only (.txt -> TRIBE language path)

Report per-clip:
  accessibility_gap = 1 - cos(P_AV, P_A)        # what audio leaves out
  description_gain  = cos(P_AV, P_AD) - cos(P_AV, P_A)   # AD's value-add
  alignment_cosine  = cos(P_AV, P_AV+AD overlay)         # legacy proxy

Then compute AUC for each new feature against the existing failure targets
(all4_fail, low_tier3_margin) and append to the existing forecast leaderboard.

Usage:
  python3 cursor/research/tribe_counterfactual_batch.py

Outputs:
  cursor/research/output/tribe_counterfactual_per_clip.csv
  cursor/research/output/tribe_counterfactual_feature_auc.csv
  cursor/research/output/tribe_counterfactual_summary.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "demo"
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

import live_pipeline as lp  # noqa: E402

FORECAST_CSV = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
CLIPS_DIR = ROOT / "workspace" / "vatex_clips"
OUT_DIR = ROOT / "cursor" / "research" / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def find_clip_video(clip_idx: int) -> Path | None:
    for ext in (".mp4", ".mkv", ".webm"):
        p = CLIPS_DIR / f"clip_{clip_idx:02d}{ext}"
        if p.exists():
            return p
    return None


def run_one(clip_idx: int, ad_text: str) -> dict:
    video = find_clip_video(clip_idx)
    if video is None:
        return {"clip_idx": clip_idx, "error": "no video found"}
    ok, msg, payload = lp.stage_tribe_proxy(str(video), ad_text)
    out = {"clip_idx": clip_idx, "video": video.name, "ok": ok, "msg": msg}
    out.update(payload)
    return out


def auc_oriented(y: np.ndarray, x: np.ndarray) -> tuple[float, str]:
    """AUC oriented so higher x predicts y=1; flip x if AUC<0.5."""
    if np.unique(y).size < 2:
        return float("nan"), "n/a"
    try:
        a = roc_auc_score(y, x)
    except ValueError:
        return float("nan"), "n/a"
    if a < 0.5:
        return roc_auc_score(y, -x), "low_bad"
    return a, "high_bad"


def main():
    forecast = pd.read_csv(FORECAST_CSV)
    roster = forecast[["clip_idx", "video_id", "category", "tier3_va11y_text",
                       "all4_fail", "low_tier3_margin", "tier2_tier1_inversion",
                       "quality_risk_fail", "target", "risk_score"]].copy()
    print(f"Running TRIBE counterfactual on {len(roster)} clips...")

    rows = []
    for _, r in roster.iterrows():
        cidx = int(r["clip_idx"])
        print(f"  clip_{cidx:02d}  {r['video_id']:35s}  ({r['category']})")
        rows.append(run_one(cidx, str(r["tier3_va11y_text"])))

    res = pd.DataFrame(rows)
    merged = roster.merge(res, on="clip_idx", how="left")
    per_clip_path = OUT_DIR / "tribe_counterfactual_per_clip.csv"
    merged.to_csv(per_clip_path, index=False)
    print(f"\nPer-clip results -> {per_clip_path}")

    # AUC for new features against existing failure targets
    new_features = ["accessibility_gap", "description_gain", "alignment_cosine"]
    targets = ["all4_fail", "low_tier3_margin", "tier2_tier1_inversion", "quality_risk_fail"]
    auc_rows = []
    for t in targets:
        if t not in merged.columns:
            continue
        y = merged[t].astype(float).values
        if np.unique(y[~np.isnan(y)]).size < 2:
            continue
        for f in new_features:
            if f not in merged.columns:
                continue
            x = merged[f].astype(float).values
            mask = ~np.isnan(x) & ~np.isnan(y)
            if mask.sum() < 4:
                continue
            a, direction = auc_oriented(y[mask], x[mask])
            try:
                ap = average_precision_score(y[mask], x[mask] if direction == "high_bad" else -x[mask])
            except Exception:
                ap = float("nan")
            auc_rows.append({
                "target": t, "feature": f, "direction": direction,
                "auc_oriented": a, "average_precision": ap,
                "n": int(mask.sum()), "positives": int(y[mask].sum()),
            })

    auc_df = pd.DataFrame(auc_rows).sort_values(["target", "auc_oriented"], ascending=[True, False])
    auc_path = OUT_DIR / "tribe_counterfactual_feature_auc.csv"
    auc_df.to_csv(auc_path, index=False)
    print(f"Feature AUC -> {auc_path}")

    # Summary markdown
    md = ["# TRIBE counterfactual re-run — 18-clip benchmark", ""]
    md.append(f"Source: `cursor/research/tribe_counterfactual_batch.py`")
    md.append(f"Per-clip: `{per_clip_path.relative_to(ROOT)}`")
    md.append(f"Feature AUC: `{auc_path.relative_to(ROOT)}`")
    md.append("")
    md.append("## Per-feature AUC vs existing forecast targets")
    md.append("")
    for t in targets:
        sub = auc_df[auc_df["target"] == t]
        if sub.empty:
            continue
        md.append(f"### Target: `{t}`  (n={sub['n'].iloc[0]}, positives={sub['positives'].iloc[0]})")
        md.append("")
        md.append("| feature | direction | AUC | AP |")
        md.append("|---|---|---:|---:|")
        for _, row in sub.iterrows():
            md.append(f"| `{row['feature']}` | {row['direction']} | {row['auc_oriented']:.3f} | {row['average_precision']:.3f} |")
        md.append("")

    md.append("## Comparison to existing top forecast features")
    md.append("")
    md.append("Top from `tribe_failure_robustness_feature_auc.csv`:")
    md.append("- `mean_standard_slot_score` (slot heuristic): AUC 1.000, AP 1.000")
    md.append("- `mean_speech_density` (speech heuristic): AUC 0.938, AP 0.583")
    md.append("- `high_need_seconds_frac` (need-window heuristic): AUC 0.781, AP 0.292")
    md.append("")
    md.append("## Interpretation hooks (paper narrative)")
    md.append("")
    md.append("- If `accessibility_gap` AUC >= existing best -> headline: 'Directly measured neural counterfactual matches heuristic slot scoring.'")
    md.append("- If `accessibility_gap` AUC < existing but >= 0.85 -> 'Provides theoretically motivated, complementary signal.'")
    md.append("- If `description_gain` correlates with low margin -> 'AD's measurable value-add is the right calibration variable.'")
    md.append("")
    sum_path = OUT_DIR / "tribe_counterfactual_summary.md"
    sum_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Summary -> {sum_path}")


if __name__ == "__main__":
    main()
