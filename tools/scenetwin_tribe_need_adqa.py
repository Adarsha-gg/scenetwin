#!/usr/bin/env python3
"""TRIBE need-weighted ADQA and adaptive CLIP/ADQA ensembles.

This is a no-GPU analysis pass over existing SceneTwin CSVs.

Implemented ablations:
  A. Need-weighted question scoring for ADQA runs with question timestamps.
  B. Adaptive ensemble: mean_need * ADQA + (1 - mean_need) * CLIP.
  C. Difficulty-calibrated ADQA: ADQA / (1 - mean_need), then ensemble.
  D. High-need-window-only ADQA for runs with question timestamps.

The script supports explicit question timestamp columns. For the existing
TRIBE-weighted ADQA run, it also parses time ranges embedded in question
rationales, e.g. "high-need window (0-3s)".
"""

from __future__ import annotations

import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, pearsonr, spearmanr


ROOT = Path(__file__).resolve().parents[1]
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
OUT_DIR = TIMING_DIR / "tribe_need_adqa"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-tribe-need-adqa.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-tribe-need-adqa.md"

CLIP_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
NEED_WINDOWS_CSV = TIMING_DIR / "need" / "coarse_need_windows.csv"
TRIBE_FEATURES_CSV = TIMING_DIR / "tribe_native" / "tribe_clip_features.csv"

DEFAULT_ADQA = {
    "adqa_v4": {
        "grades": TIMING_DIR / "adqa_v4" / "adqa_v4_grades.csv",
        "questions": TIMING_DIR / "adqa_v4" / "adqa_v4_questions.csv",
        "tier_scores": TIMING_DIR / "adqa_v4" / "adqa_v4_tier_scores.csv",
    },
    "adqa_tribe_claude": {
        "grades": TIMING_DIR / "adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5" / "grades.csv",
        "questions": TIMING_DIR / "adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5" / "questions.csv",
        "tier_scores": TIMING_DIR / "adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5" / "tier_scores.csv",
    },
}

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COMPARISONS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]
CLIP_METRICS = ["need_weighted_clip", "critical_weighted_clip", "clip_mean", "clip_top3"]
HIGH_NEED_THRESHOLD = 0.4
DIFFICULTY_DENOM_FLOOR = 0.10


def finite_float(value: object, default: float = float("nan")) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def minmax(s: pd.Series) -> pd.Series:
    lo = s.min()
    hi = s.max()
    if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - lo) / (hi - lo)


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    return df.groupby("clip_idx", group_keys=False)[col].apply(minmax)


def safe_corr(fn, x: pd.Series, y: pd.Series) -> tuple[float, float]:
    mask = x.notna() & y.notna()
    if mask.sum() < 3 or x[mask].nunique() < 2 or y[mask].nunique() < 2:
        return float("nan"), float("nan")
    stat, p = fn(x[mask], y[mask])
    return finite_float(stat), finite_float(p)


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    scored = df.dropna(subset=[metric, "gt"]).copy()
    rho, rho_p = safe_corr(spearmanr, scored["gt"], scored[metric])
    pear, pear_p = safe_corr(pearsonr, scored["gt"], scored[metric])
    tau, tau_p = safe_corr(kendalltau, scored["gt"], scored[metric])

    pairwise_wins = pairwise_total = full_order = full_total = 0
    for _, group in scored.groupby("clip_idx"):
        by_tier = {row.tier: finite_float(getattr(row, metric)) for row in group.itertuples()}
        if "tier3_va11y" in by_tier:
            for comp in COMPARISONS:
                if comp in by_tier:
                    pairwise_total += 1
                    pairwise_wins += int(by_tier["tier3_va11y"] > by_tier[comp])
        if set(TIERS).issubset(by_tier):
            full_total += 1
            full_order += int(
                by_tier["tier3_va11y"]
                > by_tier["tier2_vatex_long"]
                > by_tier["tier1_vatex_short"]
                > by_tier["tier0_cross"]
            )

    return {
        "metric": metric,
        "spearman_rho": rho,
        "spearman_p": rho_p,
        "pearson_r": pear,
        "pearson_p": pear_p,
        "kendall_tau": tau,
        "kendall_p": tau_p,
        "pairwise_wins": pairwise_wins,
        "pairwise_total": pairwise_total,
        "full_order_clips": full_order,
        "full_order_total": full_total,
        "rows": len(scored),
        "clips": scored["clip_idx"].nunique(),
    }


def load_mean_need() -> pd.DataFrame:
    if TRIBE_FEATURES_CSV.exists():
        features = pd.read_csv(TRIBE_FEATURES_CSV)
        if {"clip_idx", "mean_need"}.issubset(features.columns):
            return features[["clip_idx", "mean_need"]].drop_duplicates("clip_idx")

    windows = pd.read_csv(NEED_WINDOWS_CSV)
    return windows.groupby("clip_idx", as_index=False).agg(mean_need=("need_score", "mean"))


def need_for_range(windows: pd.DataFrame, clip_idx: int, start_s: float, end_s: float) -> dict[str, object]:
    clip = windows[windows["clip_idx"] == clip_idx].copy()
    if clip.empty:
        return {"question_need": float("nan"), "question_recommendation": "", "high_need": False}
    if end_s < start_s:
        start_s, end_s = end_s, start_s
    if end_s == start_s:
        row = clip[(clip["start_s"] <= start_s) & (start_s < clip["end_s"])]
        if row.empty:
            row = clip.iloc[[(clip["start_s"] - start_s).abs().argmin()]]
        need = float(row["need_score"].iloc[0])
        rec = str(row["recommendation"].iloc[0]) if "recommendation" in row else ""
        return {"question_need": need, "question_recommendation": rec, "high_need": need >= HIGH_NEED_THRESHOLD}

    clip["overlap"] = np.maximum(0.0, np.minimum(clip["end_s"], end_s) - np.maximum(clip["start_s"], start_s))
    overlap = clip[clip["overlap"] > 0]
    if overlap.empty:
        mid = (start_s + end_s) / 2.0
        return need_for_range(windows, clip_idx, mid, mid)
    need = float(np.average(overlap["need_score"], weights=overlap["overlap"]))
    rec = "high_need" if need >= HIGH_NEED_THRESHOLD else "low_ad_need"
    return {"question_need": need, "question_recommendation": rec, "high_need": need >= HIGH_NEED_THRESHOLD}


def parse_time_range_from_text(text: str) -> tuple[float, float] | None:
    if not text:
        return None
    # Matches "(0-3s)", "t=8.9-14.9s", and the en dash variant in cached CSVs.
    pattern = re.compile(r"(?:t\s*=\s*)?(\d+(?:\.\d+)?)\s*[-\u2013]\s*(\d+(?:\.\d+)?)\s*s")
    match = pattern.search(text)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def question_need_table(source_name: str, questions_csv: Path, windows: pd.DataFrame) -> pd.DataFrame:
    questions = pd.read_csv(questions_csv)
    rows = []
    for q in questions.to_dict(orient="records"):
        clip_idx = int(q["clip_idx"])
        q_idx = int(q["q_idx"])
        start_s = end_s = float("nan")
        timestamp_source = ""

        if {"start_s", "end_s"}.issubset(questions.columns):
            start_s = finite_float(q.get("start_s"))
            end_s = finite_float(q.get("end_s"))
            timestamp_source = "columns:start_s,end_s"
        else:
            for col in ["question_time_s", "timestamp_s", "time_s", "t"]:
                if col in questions.columns:
                    t = finite_float(q.get(col))
                    if math.isfinite(t):
                        start_s = end_s = t
                        timestamp_source = f"column:{col}"
                        break

        if not math.isfinite(start_s):
            for col in ["rationale", "question_rationale"]:
                if col in questions.columns:
                    parsed = parse_time_range_from_text(str(q.get(col, "")))
                    if parsed:
                        start_s, end_s = parsed
                        timestamp_source = f"parsed:{col}"
                        break

        if math.isfinite(start_s) and math.isfinite(end_s):
            need = need_for_range(windows, clip_idx, start_s, end_s)
            rows.append(
                {
                    "source": source_name,
                    "clip_idx": clip_idx,
                    "q_idx": q_idx,
                    "question_start_s": start_s,
                    "question_end_s": end_s,
                    "timestamp_source": timestamp_source,
                    **need,
                    "question": q.get("question", ""),
                    "importance": q.get("importance", ""),
                }
            )

    return pd.DataFrame(rows)


def compute_question_weighted_scores(source_name: str, paths: dict[str, Path], windows: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    q_need = question_need_table(source_name, paths["questions"], windows)
    if q_need.empty:
        return q_need, pd.DataFrame()

    grades = pd.read_csv(paths["grades"])
    merged = grades.merge(q_need, on=["clip_idx", "q_idx"], how="inner")
    if merged.empty:
        return q_need, pd.DataFrame()

    def weighted_mean(group: pd.DataFrame) -> float:
        weights = group["question_need"].to_numpy(dtype=float)
        scores = group["score"].to_numpy(dtype=float)
        if np.nansum(weights) <= 1e-12:
            return float(np.nanmean(scores))
        return float(np.nansum(scores * weights) / np.nansum(weights))

    key_cols = ["clip_idx", "video_id", "category", "tier", "gt"]
    weighted = (
        merged.groupby(key_cols, as_index=False)
        .apply(
            lambda g: pd.Series(
                {
                    f"{source_name}_need_weighted_adqa": weighted_mean(g),
                    f"{source_name}_uniform_adqa": float(g["score"].mean()),
                    "n_questions": int(g["q_idx"].nunique()),
                    "mean_question_need": float(g["question_need"].mean()),
                    "high_need_questions": int(g["high_need"].sum()),
                }
            ),
            include_groups=False,
        )
        .reset_index(drop=True)
    )

    high = merged[merged["high_need"]].copy()
    if not high.empty:
        high_scores = (
            high.groupby(key_cols, as_index=False)
            .agg(
                **{
                    f"{source_name}_high_need_adqa": ("score", "mean"),
                    "n_high_need_questions": ("q_idx", "nunique"),
                }
            )
        )
        weighted = weighted.merge(high_scores, on=key_cols, how="left")
    else:
        weighted[f"{source_name}_high_need_adqa"] = np.nan
        weighted["n_high_need_questions"] = 0

    return q_need, weighted


def score_column(tier_scores: pd.DataFrame) -> str:
    candidates = [
        c for c in tier_scores.columns
        if c.endswith("_score") and c not in {"score"} and pd.api.types.is_numeric_dtype(tier_scores[c])
    ]
    if not candidates:
        raise ValueError("No ADQA score column found in tier scores.")
    return candidates[0]


def load_base_adqa(source_name: str, paths: dict[str, Path]) -> pd.DataFrame:
    tier = pd.read_csv(paths["tier_scores"])
    col = score_column(tier)
    keep = ["clip_idx", "video_id", "category", "tier", "gt", col]
    keep = [c for c in keep if c in tier.columns]
    out = tier[keep].copy()
    out = out.rename(columns={col: f"{source_name}_adqa"})
    return out


def add_adaptive_ensembles(scores: pd.DataFrame, adqa_col: str, label: str) -> list[str]:
    scores[f"{label}_adqa_norm_clip"] = minmax_clipwise(scores, adqa_col)
    denom = np.maximum(1.0 - scores["mean_need"].to_numpy(dtype=float), DIFFICULTY_DENOM_FLOOR)
    scores[f"{label}_adqa_difficulty_raw"] = scores[adqa_col] / denom
    scores[f"{label}_adqa_difficulty_norm_global"] = minmax(scores[f"{label}_adqa_difficulty_raw"])

    metrics = [
        adqa_col,
        f"{label}_adqa_norm_clip",
        f"{label}_adqa_difficulty_raw",
        f"{label}_adqa_difficulty_norm_global",
    ]
    for clip_metric in CLIP_METRICS:
        norm_clip_col = f"{clip_metric}_norm_clip"
        scores[norm_clip_col] = minmax_clipwise(scores, clip_metric)
        fixed = f"{label}_ensemble_fixed50_{clip_metric}"
        adaptive = f"{label}_ensemble_adaptive_need_{clip_metric}"
        diff = f"{label}_ensemble_difficulty_{clip_metric}"
        scores[fixed] = 0.5 * scores[f"{label}_adqa_norm_clip"] + 0.5 * scores[norm_clip_col]
        scores[adaptive] = scores["mean_need"] * scores[f"{label}_adqa_norm_clip"] + (1.0 - scores["mean_need"]) * scores[norm_clip_col]
        scores[diff] = 0.5 * scores[f"{label}_adqa_difficulty_norm_global"] + 0.5 * scores[norm_clip_col]
        metrics.extend([norm_clip_col, fixed, adaptive, diff])
    return list(dict.fromkeys(metrics))


def build_ensemble_scores(adqa_scores: dict[str, pd.DataFrame], mean_need: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    clip = pd.read_csv(CLIP_CSV)
    frames = []
    all_results = []
    for label, adqa in adqa_scores.items():
        adqa_col = [c for c in adqa.columns if c.endswith("_adqa") or c.endswith("_need_weighted_adqa") or c.endswith("_high_need_adqa")]
        for col in adqa_col:
            suffix = col.replace(f"{label}_", "")
            run_label = f"{label}_{suffix}"
            base_cols = ["clip_idx", "video_id", "category", "tier", "gt", col]
            base_cols = [c for c in base_cols if c in adqa.columns]
            merged = (
                clip.merge(adqa[base_cols], on=["clip_idx", "tier", "gt"], how="inner")
                .merge(mean_need, on="clip_idx", how="left")
            )
            if merged.empty:
                continue
            metrics = add_adaptive_ensembles(merged, col, run_label)
            merged["adqa_source"] = label
            merged["adqa_metric"] = col
            frames.append(merged)
            for metric in metrics:
                result = evaluate(merged, metric)
                result["adqa_source"] = label
                result["adqa_metric"] = col
                all_results.append(result)

    return pd.concat(frames, ignore_index=True), pd.DataFrame(all_results)


def write_report(
    question_need: pd.DataFrame,
    weighted_scores: pd.DataFrame,
    ensemble_scores: pd.DataFrame,
    results: pd.DataFrame,
    unavailable: list[dict[str, str]],
) -> None:
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)

    top = results.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).head(16)
    raw_adqa = results[results["metric"] == results["adqa_metric"]].copy()
    adaptive = results[results["metric"].str.contains("ensemble_adaptive_need", na=False)]
    adaptive_top = adaptive.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).head(8)
    difficulty = results[results["metric"].str.contains("difficulty", na=False)]
    difficulty_top = difficulty.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).head(8)
    need_weighted = results[results["metric"].str.contains("need_weighted_adqa|high_need_adqa", na=False)]
    need_weighted_top = need_weighted.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False)

    summary_rows = []
    for adqa_metric in sorted(results["adqa_metric"].dropna().unique()):
        group = results[results["adqa_metric"] == adqa_metric]
        raw = group[group["metric"] == adqa_metric]
        fixed = group[group["metric"].str.contains("ensemble_fixed50", na=False)]
        adapt = group[group["metric"].str.contains("ensemble_adaptive_need", na=False)]
        diff = group[group["metric"].str.contains("ensemble_difficulty", na=False)]

        def best_row(frame: pd.DataFrame) -> pd.Series | None:
            if frame.empty:
                return None
            return frame.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).iloc[0]

        raw_best = best_row(raw)
        fixed_best = best_row(fixed)
        adapt_best = best_row(adapt)
        diff_best = best_row(diff)

        summary_rows.append(
            {
                "adqa_metric": adqa_metric,
                "raw_rho": raw_best["spearman_rho"] if raw_best is not None else float("nan"),
                "best_fixed50_metric": fixed_best["metric"] if fixed_best is not None else "",
                "best_fixed50_rho": fixed_best["spearman_rho"] if fixed_best is not None else float("nan"),
                "best_adaptive_metric": adapt_best["metric"] if adapt_best is not None else "",
                "best_adaptive_rho": adapt_best["spearman_rho"] if adapt_best is not None else float("nan"),
                "adaptive_minus_fixed": (
                    adapt_best["spearman_rho"] - fixed_best["spearman_rho"]
                    if adapt_best is not None and fixed_best is not None else float("nan")
                ),
                "best_difficulty_metric": diff_best["metric"] if diff_best is not None else "",
                "best_difficulty_rho": diff_best["spearman_rho"] if diff_best is not None else float("nan"),
            }
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_DIR / "tribe_need_adqa_summary.csv", index=False)

    unavailable_text = "None"
    if unavailable:
        unavailable_text = pd.DataFrame(unavailable).to_markdown(index=False)

    question_summary = "No timestamped questions found."
    if not question_need.empty:
        question_summary = (
            question_need.groupby(["source", "timestamp_source"], as_index=False)
            .agg(
                questions=("q_idx", "count"),
                clips=("clip_idx", "nunique"),
                mean_need=("question_need", "mean"),
                high_need_questions=("high_need", "sum"),
            )
            .to_markdown(index=False)
        )

    text = f"""---
title: "SceneTwin TRIBE Need-Weighted ADQA"
category: research
tags: [SceneTwin, TRIBE, ADQA, CLIP, ensemble, audio-description]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_need_adqa/need_weighted_adqa_scores.csv
  - output/scenetwin_timing_20clip/tribe_need_adqa/adaptive_ensemble_scores.csv
  - output/scenetwin_timing_20clip/tribe_need_adqa/tribe_need_adqa_results.csv
---

# SceneTwin TRIBE Need-Weighted ADQA

This no-GPU pass tests whether TRIBE need improves how existing ADQA and CLIP
scores are aggregated.

Rows evaluated: {len(ensemble_scores)} ensemble rows. Timestamped question rows:
{len(question_need)}. High-need threshold: need >= {HIGH_NEED_THRESHOLD}.

## Timestamp Coverage

{question_summary}

Unavailable A/D sources:

{unavailable_text}

## Main Findings

{summary.to_markdown(index=False)}

## Raw A/D ADQA Metrics

{raw_adqa.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).to_markdown(index=False)}

## Need-Weighted And High-Need ADQA

{need_weighted_top.to_markdown(index=False)}

## Adaptive Ensemble

Formula:

```text
adaptive = mean_need * ADQA_clip_norm + (1 - mean_need) * CLIP_clip_norm
```

{adaptive_top.to_markdown(index=False)}

## Difficulty Calibration

Formula:

```text
difficulty_raw = ADQA / max(1 - mean_need, {DIFFICULTY_DENOM_FLOOR})
```

The calibrated ADQA is globally min-max normalized before blending with
clip-normalized CLIP.

{difficulty_top.to_markdown(index=False)}

## Top Metrics Overall

{top.to_markdown(index=False)}

## Interpretation

A/D were only computed for ADQA sources where question timing could be recovered.
The standard `adqa_v4` questions do not contain timestamp columns, so they are
used for B/C but not for timestamp-specific question filtering.

Need-weighted ADQA uses a weighted mean, not an unnormalized weighted sum, so
scores remain on the 0-1 ADQA scale while high-need questions count more inside
each clip.
"""
    OUT_REPORT.write_text(text, encoding="utf-8")
    OUT_WIKI.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    windows = pd.read_csv(NEED_WINDOWS_CSV)
    mean_need = load_mean_need()

    question_need_frames = []
    weighted_frames = []
    unavailable = []
    base_adqa: dict[str, pd.DataFrame] = {}

    for name, paths in DEFAULT_ADQA.items():
        missing = [str(path) for path in paths.values() if not path.exists()]
        if missing:
            unavailable.append({"source": name, "reason": "missing files: " + ", ".join(missing)})
            continue

        base_adqa[name] = load_base_adqa(name, paths)
        q_need, weighted = compute_question_weighted_scores(name, paths, windows)
        if q_need.empty or weighted.empty:
            unavailable.append({"source": name, "reason": "no question timestamp columns or parseable time ranges"})
            continue
        question_need_frames.append(q_need)
        weighted_frames.append(weighted)
        base_adqa[f"{name}_timed"] = weighted

    question_need = pd.concat(question_need_frames, ignore_index=True) if question_need_frames else pd.DataFrame()
    weighted_scores = pd.concat(weighted_frames, ignore_index=True) if weighted_frames else pd.DataFrame()

    if not question_need.empty:
        question_need.to_csv(OUT_DIR / "question_need_scores.csv", index=False)
    if not weighted_scores.empty:
        weighted_scores.to_csv(OUT_DIR / "need_weighted_adqa_scores.csv", index=False)

    ensemble_scores, results = build_ensemble_scores(base_adqa, mean_need)
    results = results.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False)
    ensemble_scores.to_csv(OUT_DIR / "adaptive_ensemble_scores.csv", index=False)
    results.to_csv(OUT_DIR / "tribe_need_adqa_results.csv", index=False)

    write_report(question_need, weighted_scores, ensemble_scores, results, unavailable)

    print("=== Top results ===")
    print(results.head(20).to_string(index=False))
    print("\n=== Unavailable A/D sources ===")
    if unavailable:
        print(pd.DataFrame(unavailable).to_string(index=False))
    else:
        print("None")
    print(f"\nWrote {OUT_DIR / 'tribe_need_adqa_results.csv'}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
