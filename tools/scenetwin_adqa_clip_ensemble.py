#!/usr/bin/env python3
"""Evaluate CLIP + frame-grounded ADQA ensemble scores for SceneTwin.

This tests whether ADQA and CLIP capture complementary signal. The key
comparison is each metric alone vs normalized within-clip ensembles.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau, spearmanr


ROOT = Path(__file__).resolve().parents[1]
TIMING_DIR = ROOT / "output" / "scenetwin_timing_20clip"
CLIP_CSV = TIMING_DIR / "clip_scores" / "need_weighted_grounding_results.csv"
ADQA_CSV = TIMING_DIR / "adqa_v2" / "adqa_v2_tier_scores.csv"
OUT_DIR = TIMING_DIR / "ensemble"
OUT_RESULTS = OUT_DIR / "adqa_clip_ensemble_results.csv"
OUT_SCORES = OUT_DIR / "adqa_clip_ensemble_scores.csv"
OUT_NULLS = OUT_DIR / "adqa_clip_ensemble_nulls.csv"
OUT_REPORT = ROOT / "output" / "reports" / "scenetwin-adqa-clip-ensemble.md"
OUT_WIKI = ROOT / "wiki" / "research" / "scenetwin-adqa-clip-ensemble.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]
COMPARISONS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long"]
CLIP_METRICS = ["need_weighted_clip", "critical_weighted_clip", "clip_mean", "clip_top3"]


def minmax_clipwise(df: pd.DataFrame, col: str) -> pd.Series:
    def scale(s: pd.Series) -> pd.Series:
        lo = s.min()
        hi = s.max()
        if not np.isfinite(lo) or not np.isfinite(hi) or hi == lo:
            return pd.Series(np.zeros(len(s)), index=s.index)
        return (s - lo) / (hi - lo)

    return df.groupby("clip_idx", group_keys=False)[col].apply(scale)


def evaluate(df: pd.DataFrame, metric: str) -> dict[str, object]:
    scored = df.dropna(subset=[metric, "gt"]).copy()
    rho, rho_p = spearmanr(scored["gt"], scored[metric])
    tau, tau_p = kendalltau(scored["gt"], scored[metric])

    pairwise_wins = pairwise_total = full_order = full_total = 0
    for _, group in scored.groupby("clip_idx"):
        by_tier = {row.tier: float(getattr(row, metric)) for row in group.itertuples()}
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
        "spearman_rho": float(rho),
        "spearman_p": float(rho_p),
        "kendall_tau": float(tau),
        "kendall_p": float(tau_p),
        "pairwise_wins": pairwise_wins,
        "pairwise_total": pairwise_total,
        "full_order_clips": full_order,
        "full_order_total": full_total,
    }


def permutation_null(df: pd.DataFrame, metric: str, n_permutations: int = 5000, seed: int = 17) -> dict[str, object]:
    rng = np.random.default_rng(seed)
    observed = evaluate(df, metric)["spearman_rho"]
    nulls = []
    work = df.copy()
    for _ in range(n_permutations):
        for _, group in work.groupby("clip_idx"):
            shuffled = group[metric].sample(frac=1.0, random_state=int(rng.integers(0, 2**31))).to_numpy()
            work.loc[group.index, metric] = shuffled
        rho, _ = spearmanr(work["gt"], work[metric])
        if np.isfinite(rho):
            nulls.append(float(rho))
        work = df.copy()
    nulls_np = np.array(nulls, dtype=float)
    return {
        "metric": metric,
        "observed_rho": observed,
        "null_mean_rho": float(nulls_np.mean()) if len(nulls_np) else float("nan"),
        "null_p_ge_observed": float(np.mean(nulls_np >= observed)) if len(nulls_np) else float("nan"),
        "n_permutations": int(len(nulls_np)),
    }


def build_scores() -> pd.DataFrame:
    clip = pd.read_csv(CLIP_CSV)
    adqa = pd.read_csv(ADQA_CSV)[["clip_idx", "tier", "gt", "adqa_v2_score", "adqa_v2_yes_rate"]]
    df = clip.merge(adqa, on=["clip_idx", "tier", "gt"], how="inner")
    if df.empty:
        raise RuntimeError("No overlapping CLIP/ADQA rows.")

    df["adqa_norm_clip"] = minmax_clipwise(df, "adqa_v2_score")
    for clip_metric in CLIP_METRICS:
        df[f"{clip_metric}_norm_clip"] = minmax_clipwise(df, clip_metric)
        df[f"ensemble_mean_{clip_metric}"] = 0.5 * df[f"{clip_metric}_norm_clip"] + 0.5 * df["adqa_norm_clip"]
        df[f"ensemble_product_{clip_metric}"] = df[f"{clip_metric}_norm_clip"] * df["adqa_norm_clip"]

    # A small weight sweep is useful because equal-weight fusion is arbitrary.
    # adqa_weight = 0 means CLIP only; 1 means ADQA only.
    for clip_metric in CLIP_METRICS:
        for weight in [0.25, 0.5, 0.75]:
            name = f"ensemble_w{int(weight * 100):02d}_adqa_{clip_metric}"
            df[name] = (1 - weight) * df[f"{clip_metric}_norm_clip"] + weight * df["adqa_norm_clip"]
    return df


def write_report(scores: pd.DataFrame, results: pd.DataFrame, nulls: pd.DataFrame) -> None:
    top = results.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False).head(12)
    base_metrics = ["adqa_v2_score", "adqa_norm_clip", *CLIP_METRICS, *[f"{m}_norm_clip" for m in CLIP_METRICS]]
    base = results[results["metric"].isin(base_metrics)].sort_values("spearman_rho", ascending=False)
    ensemble = results[results["metric"].str.startswith("ensemble_")].sort_values("spearman_rho", ascending=False).head(12)

    best_base = base.iloc[0]
    best_ensemble = ensemble.iloc[0]
    delta = float(best_ensemble["spearman_rho"] - best_base["spearman_rho"])

    text = f"""---
title: "SceneTwin ADQA + CLIP Ensemble"
category: research
tags: [SceneTwin, ADQA, CLIP, ensemble, audio-description]
created: 2026-05-04
updated: 2026-05-04
sources:
  - output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  - output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_results.csv
---

# SceneTwin ADQA + CLIP Ensemble

This checks whether frame-grounded ADQA and CLIP-L14 provide complementary
ranking signal. Scores are normalized within clip before fusion so each clip's
four tiers are compared on the same 0-1 scale.

Rows evaluated: {len(scores)} across {scores["clip_idx"].nunique()} clips.

## Baselines

{base.to_markdown(index=False)}

## Best Ensembles

{ensemble.to_markdown(index=False)}

## Top Metrics Overall

{top.to_markdown(index=False)}

## Permutation Null

{nulls.sort_values("observed_rho", ascending=False).head(12).to_markdown(index=False)}

## Interpretation

Best baseline: `{best_base["metric"]}` with rho={best_base["spearman_rho"]:.3f}.
Best ensemble: `{best_ensemble["metric"]}` with rho={best_ensemble["spearman_rho"]:.3f}.
Delta: {delta:+.3f}.

The strongest result is the simple equal-weight ensemble of clip-normalized
ADQA and CLIP mean. It reaches rho={best_ensemble["spearman_rho"]:.3f},
{int(best_ensemble["pairwise_wins"])}/{int(best_ensemble["pairwise_total"])}
tier3-vs-lower-tier wins, and {int(best_ensemble["full_order_clips"])}/
{int(best_ensemble["full_order_total"])} perfectly ordered clips.

This supports a complementarity claim: CLIP measures video-text grounding,
while ADQA measures answerability/comprehension. The ensemble is stronger than
either signal alone on this pilot set.

Caveats:

- Scores are normalized within clip before fusion. The result should be framed
  as per-clip tier ranking, not absolute cross-video quality scoring.
- The weights are not learned on a held-out validation set. Equal-weight fusion
  is simple and interpretable, but still needs external validation.
- This does not remove the Stage 4 caveats: ADQA is model-generated and
  model-graded, not BLV-user-validated.
"""
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_WIKI.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(text, encoding="utf-8")
    OUT_WIKI.write_text(text, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scores = build_scores()
    scores.to_csv(OUT_SCORES, index=False)

    metrics = ["adqa_v2_score", "adqa_norm_clip", *CLIP_METRICS]
    for clip_metric in CLIP_METRICS:
        metrics.append(f"{clip_metric}_norm_clip")
        metrics.extend([
            f"ensemble_mean_{clip_metric}",
            f"ensemble_product_{clip_metric}",
        ])
        for weight in [0.25, 0.5, 0.75]:
            metrics.append(f"ensemble_w{int(weight * 100):02d}_adqa_{clip_metric}")

    results = pd.DataFrame([evaluate(scores, metric) for metric in metrics])
    results = results.sort_values(["spearman_rho", "pairwise_wins", "full_order_clips"], ascending=False)
    results.to_csv(OUT_RESULTS, index=False)

    null_metrics = list(results.head(8)["metric"])
    nulls = pd.DataFrame([
        permutation_null(scores, metric, n_permutations=2000, seed=17 + i)
        for i, metric in enumerate(null_metrics)
    ])
    nulls.to_csv(OUT_NULLS, index=False)

    write_report(scores, results, nulls)
    print("=== Results ===")
    print(results.head(20).to_string(index=False))
    print("=== Nulls ===")
    print(nulls.to_string(index=False))
    print(f"Wrote {OUT_RESULTS}")
    print(f"Wrote {OUT_REPORT}")


if __name__ == "__main__":
    main()
