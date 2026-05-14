---
title: "SceneTwin TRIBE Trajectory Metrics"
category: research
tags: [SceneTwin, TRIBE, trajectories, DTW, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/trajectory_metrics_results.csv
  - output/scenetwin_description_gain/trajectory_metrics_summary.csv
  - output/scenetwin_description_gain/preds/
---

# SceneTwin TRIBE Trajectory Metrics

## Question

Do temporal TRIBE trajectory metrics recover AD quality better than whole-cortex average cosine?

## Metrics

- `resampled_traj_cos`: resample description trajectory to AV length, then average per-step cosine.
- `resampled_traj_gain_vs_audio`: same, but subtract audio-only similarity.
- `dtw_traj_similarity`: dynamic time warping similarity between AV and description trajectories.
- `shift_curve_corr`: correlation between AV state-change curve and description state-change curve.

All metrics use a fixed random projection to 256 dimensions for speed.

## Summary

| metric                       |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   tier3_gt_tier2_vatex_long_wins |   tier3_gt_tier2_vatex_long_total |   tier3_gt_tier1_vatex_short_wins |   tier3_gt_tier1_vatex_short_total |   tier3_gt_tier0_cross_wins |   tier3_gt_tier0_cross_total |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:-----------------------------|---------------:|-------------:|--------------:|------------:|---------------------------------:|----------------------------------:|----------------------------------:|-----------------------------------:|----------------------------:|-----------------------------:|----------------:|-----------------:|-------------------:|-------------------:|
| resampled_traj_cos           |       0        |     1        |     0         |    1        |                                2 |                                 2 |                                 2 |                                  2 |                           1 |                            2 |               5 |                6 |                  0 |                  2 |
| resampled_traj_gain_vs_audio |       0.29277  |     0.481618 |     0.231455  |    0.443598 |                                1 |                                 2 |                                 1 |                                  2 |                           2 |                            2 |               4 |                6 |                  0 |                  2 |
| shift_curve_corr             |      -0.19518  |     0.643226 |    -0.231455  |    0.443598 |                                2 |                                 2 |                                 1 |                                  2 |                           1 |                            2 |               4 |                6 |                  0 |                  2 |
| dtw_traj_similarity          |      -0.048795 |     0.908654 |    -0.0771517 |    0.798432 |                                0 |                                 2 |                                 1 |                                  2 |                           1 |                            2 |               2 |                6 |                  0 |                  2 |

## Mean Scores By Tier

| tier              |   resampled_traj_cos |   resampled_traj_gain_vs_audio |   dtw_traj_similarity |   shift_curve_corr |
|:------------------|---------------------:|-------------------------------:|----------------------:|-------------------:|
| tier3_va11y       |             0.520703 |                     -0.101509  |              0.692183 |           0.668829 |
| tier2_vatex_long  |             0.439389 |                     -0.139526  |              0.715361 |           0.251524 |
| tier1_vatex_short |             0.496963 |                     -0.0923272 |              0.690479 |           0.429305 |
| tier0_cross       |             0.498282 |                     -0.15683   |              0.714555 |           0.886239 |

## Verdict

This is useful as a diagnostic, but it is not yet the headline metric. On two clips, trajectory metrics do not clearly beat need-weighted visual grounding. The main value is catching descriptions that are semantically right but temporally out of order, which needs a larger test set.
