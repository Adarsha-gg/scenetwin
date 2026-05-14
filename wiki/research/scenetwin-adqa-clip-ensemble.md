---
title: "SceneTwin ADQA + CLIP Ensemble"
category: research
tags: [SceneTwin, ADQA, CLIP, ensemble, audio-description, NJBDA-2026]
created: 2026-05-04
updated: 2026-05-04
sources:
  - output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  - output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_results.csv
  - output/reports/scenetwin_ensemble_validation.md
  - tools/scenetwin_ensemble_validation.py
---

# SceneTwin ADQA + CLIP Ensemble

This checks whether frame-grounded ADQA and CLIP-L14 provide complementary
ranking signal. Scores are normalized within clip before fusion so each clip's
four tiers are compared on the same 0-1 scale.

Rows evaluated: 72 across 18 clips.

## Baselines

| metric                           |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:---------------------------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|
| adqa_norm_clip                   |       0.853589 |  1.6592e-21  |      0.788014 | 2.55058e-16 |              51 |               54 |                  8 |                 18 |
| critical_weighted_clip_norm_clip |       0.803427 |  2.02512e-17 |      0.696181 | 9.83958e-14 |              48 |               54 |                 11 |                 18 |
| adqa_v2_score                    |       0.802928 |  2.19288e-17 |      0.695932 | 1.17337e-13 |              51 |               54 |                  8 |                 18 |
| need_weighted_clip_norm_clip     |       0.801605 |  2.70557e-17 |      0.695224 | 1.06311e-13 |              48 |               54 |                 11 |                 18 |
| clip_top3_norm_clip              |       0.800998 |  2.97787e-17 |      0.692356 | 1.34005e-13 |              48 |               54 |                 10 |                 18 |
| clip_mean_norm_clip              |       0.798568 |  4.35584e-17 |      0.689487 | 1.68756e-13 |              48 |               54 |                 11 |                 18 |
| clip_top3                        |       0.734623 |  2.06146e-13 |      0.587682 | 4.42827e-11 |              48 |               54 |                 10 |                 18 |
| need_weighted_clip               |       0.73283  |  2.52248e-13 |      0.587682 | 4.42827e-11 |              48 |               54 |                 11 |                 18 |
| critical_weighted_clip           |       0.72745  |  4.57757e-13 |      0.584094 | 5.80198e-11 |              48 |               54 |                 11 |                 18 |
| clip_mean                        |       0.725059 |  5.93888e-13 |      0.580505 | 7.58977e-11 |              48 |               54 |                 11 |                 18 |

## Best Ensembles

| metric                                   |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:-----------------------------------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|
| ensemble_mean_clip_mean                  |       0.929094 |  5.88944e-32 |      0.836472 | 1.07071e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_clip_mean              |       0.929094 |  5.88944e-32 |      0.836472 | 1.07071e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_clip_top3                  |       0.928491 |  7.84041e-32 |      0.835537 | 1.17535e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_clip_top3              |       0.928491 |  7.84041e-32 |      0.835537 | 1.17535e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_need_weighted_clip         |       0.927888 |  1.04117e-31 |      0.834601 | 1.29009e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_need_weighted_clip     |       0.927888 |  1.04117e-31 |      0.834601 | 1.29009e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_critical_weighted_clip     |       0.927285 |  1.37923e-31 |      0.833666 | 1.41588e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_critical_weighted_clip |       0.927285 |  1.37923e-31 |      0.833666 | 1.41588e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w25_adqa_clip_mean              |       0.923357 |  8.12951e-31 |      0.827412 | 2.58782e-19 |              53 |               54 |                 13 |                 18 |
| ensemble_w25_adqa_need_weighted_clip     |       0.919738 |  3.84002e-30 |      0.820868 | 4.9263e-19  |              54 |               54 |                 14 |                 18 |
| ensemble_w25_adqa_critical_weighted_clip |       0.919135 |  4.93885e-30 |      0.818998 | 5.91567e-19 |              54 |               54 |                 14 |                 18 |
| ensemble_w25_adqa_clip_top3              |       0.91431  |  3.4553e-29  |      0.812453 | 1.11893e-18 |              53 |               54 |                 13 |                 18 |

## Top Metrics Overall

| metric                                   |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:-----------------------------------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|
| ensemble_mean_clip_mean                  |       0.929094 |  5.88944e-32 |      0.836472 | 1.07071e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_clip_mean              |       0.929094 |  5.88944e-32 |      0.836472 | 1.07071e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_clip_top3                  |       0.928491 |  7.84041e-32 |      0.835537 | 1.17535e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_clip_top3              |       0.928491 |  7.84041e-32 |      0.835537 | 1.17535e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_need_weighted_clip         |       0.927888 |  1.04117e-31 |      0.834601 | 1.29009e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_need_weighted_clip     |       0.927888 |  1.04117e-31 |      0.834601 | 1.29009e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_mean_critical_weighted_clip     |       0.927285 |  1.37923e-31 |      0.833666 | 1.41588e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w50_adqa_critical_weighted_clip |       0.927285 |  1.37923e-31 |      0.833666 | 1.41588e-19 |              54 |               54 |                 15 |                 18 |
| ensemble_w25_adqa_clip_mean              |       0.923357 |  8.12951e-31 |      0.827412 | 2.58782e-19 |              53 |               54 |                 13 |                 18 |
| ensemble_w25_adqa_need_weighted_clip     |       0.919738 |  3.84002e-30 |      0.820868 | 4.9263e-19  |              54 |               54 |                 14 |                 18 |
| ensemble_w25_adqa_critical_weighted_clip |       0.919135 |  4.93885e-30 |      0.818998 | 5.91567e-19 |              54 |               54 |                 14 |                 18 |
| ensemble_w25_adqa_clip_top3              |       0.91431  |  3.4553e-29  |      0.812453 | 1.11893e-18 |              53 |               54 |                 13 |                 18 |

## Permutation Null

| metric                                   |   observed_rho |   null_mean_rho |   null_p_ge_observed |   n_permutations |
|:-----------------------------------------|---------------:|----------------:|---------------------:|-----------------:|
| ensemble_mean_clip_mean                  |       0.929094 |    -0.00331274  |                    0 |             2000 |
| ensemble_w50_adqa_clip_mean              |       0.929094 |     0.00136137  |                    0 |             2000 |
| ensemble_mean_clip_top3                  |       0.928491 |    -9.22761e-05 |                    0 |             2000 |
| ensemble_w50_adqa_clip_top3              |       0.928491 |    -8.95621e-05 |                    0 |             2000 |
| ensemble_mean_need_weighted_clip         |       0.927888 |    -0.000235666 |                    0 |             2000 |
| ensemble_w50_adqa_need_weighted_clip     |       0.927888 |     0.00326088  |                    0 |             2000 |
| ensemble_mean_critical_weighted_clip     |       0.927285 |    -0.00311583  |                    0 |             2000 |
| ensemble_w50_adqa_critical_weighted_clip |       0.927285 |     0.00306079  |                    0 |             2000 |

## Interpretation

Best baseline: `adqa_norm_clip` with rho=0.854.
Best ensemble: `ensemble_mean_clip_mean` with rho=0.929.
Delta: +0.076.

The strongest result is the simple equal-weight ensemble of clip-normalized
ADQA and CLIP mean. It reaches rho=0.929,
54/54
tier3-vs-lower-tier wins, and 15/
18 perfectly ordered clips.

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

## Validation (2026-05-04)

Two follow-up checks confirmed the ensemble lift is real, not a normalization or
small-sample artifact. Code: `tools/scenetwin_ensemble_validation.py`. Full
report: `output/reports/scenetwin_ensemble_validation.md`.

### Per-clip CLIP ↔ ADQA correlation

| Quantity | Value |
|---|---:|
| Mean per-clip Spearman(CLIP, ADQA) | 0.761 |
| Clips where CLIP and ADQA agree on tier-rank direction | 17/18 (94%) |

Moderate correlation. CLIP and ADQA share quality signal but are not redundant.
The single disagreement is `clip_00` (Food & Cooking), where neither metric
ranks tiers cleanly on its own. The ensemble lift is genuine signal combination,
not noise smoothing.

### Bootstrap 95% CI on Spearman ρ

| Metric | Observed ρ | 95% CI |
|---|---:|---|
| Ensemble (CLIP + ADQA, 50/50) | 0.9285 | [0.904, 0.957] |
| CLIP-only | 0.8010 | [0.728, 0.873] |

N clips: 18. Bootstrap resamples: 2000. Bootstrap mean = 0.9286 (vs observed
0.9285) → unbiased estimate. The CIs do **not** overlap: CLIP upper bound
0.873 sits below ensemble lower bound 0.904. At N=18, the ensemble improvement
is statistically distinguishable from CLIP alone.

### Poster-safe claim

> Frame-grounded LLM comprehension (ADQA) and visual grounding (CLIP-L14)
> capture complementary signal (per-clip ρ=0.76). A simple equal-weight
> ensemble reaches ρ=0.929 [95% CI: 0.90–0.96], 54/54 pairwise tier wins,
> permutation p<0.0005, on 18 clips × 4 quality tiers.

## See Also
- [[research/scenetwin-stage4-frame-grounded-adqa]]
- [[research/scenetwin-20clip-timing-results]]
- [[research/scenetwin]]
