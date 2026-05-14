---
title: "SceneTwin Metric Null Baselines"
category: research
tags: [SceneTwin, statistics, permutation-test, metrics]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/metric_null_baselines.csv
---

# SceneTwin Metric Null Baselines

## Method

For each metric file, keep quality labels fixed and shuffle each metric's values within each clip. For the current two-clip dataset this enumerates the exact `4! x 4! = 576` within-clip metric permutations. This gives a small-sample null for Spearman, tier3 pairwise wins, and full-order clips.

## Top Results

| source                  | metric                                |   spearman_rho |   kendall_tau |   pairwise_wins |   full_order_clips |   null_spearman_mean |   null_spearman_p_ge_observed |   null_pairwise_mean |   null_pairwise_p_ge_observed |   null_full_order_mean |   null_full_order_p_ge_observed |   n_permutations |
|:------------------------|:--------------------------------------|---------------:|--------------:|----------------:|-------------------:|---------------------:|------------------------------:|---------------------:|------------------------------:|-----------------------:|--------------------------------:|-----------------:|
| need_weighted_grounding | need_weighted_clip                    |       0.9759   |      0.92582  |               6 |                  2 |          0           |                    0.00173611 |                 3    |                        0.0625 |              0.0833333 |                      0.00173611 |              576 |
| need_weighted_grounding | critical_weighted_clip                |       0.9759   |      0.92582  |               6 |                  2 |          0           |                    0.00173611 |                 3    |                        0.0625 |              0.0833333 |                      0.00173611 |              576 |
| need_weighted_grounding | need_weighted_clip_norm_clip          |       0.938343 |      0.880705 |               6 |                  2 |          0           |                    0.00173611 |                 3    |                        0.0625 |              0.0833333 |                      0.00173611 |              576 |
| need_weighted_grounding | critical_weighted_clip_norm_clip      |       0.938343 |      0.880705 |               6 |                  2 |          0           |                    0.00173611 |                 3    |                        0.0625 |              0.0833333 |                      0.00173611 |              576 |
| need_weighted_grounding | clip_mean_norm_clip                   |       0.888957 |      0.800641 |               6 |                  1 |          0           |                    0.00520833 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | clip_top3_norm_clip                   |       0.888957 |      0.800641 |               6 |                  1 |          0           |                    0.00520833 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | extended_need_weighted_clip_norm_clip |       0.888957 |      0.800641 |               6 |                  1 |          0           |                    0.00520833 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | clip_mean                             |       0.87831  |      0.771517 |               6 |                  1 |         -1.23358e-17 |                    0.00868056 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | clip_top3                             |       0.87831  |      0.771517 |               6 |                  1 |         -6.16791e-18 |                    0.00694444 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | extended_need_weighted_clip           |       0.87831  |      0.771517 |               6 |                  1 |          0           |                    0.00694444 |                 3    |                        0.0625 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | opportunity_weighted_clip             |       0.927105 |      0.848668 |               5 |                  1 |          0           |                    0.00694444 |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | standard_slot_weighted_clip           |       0.87831  |      0.771517 |               5 |                  1 |          0           |                    0.0104167  |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | standard_slot_weighted_clip_norm_clip |       0.864263 |      0.760609 |               5 |                  1 |          0           |                    0.00868056 |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | opportunity_weighted_clip_norm_clip   |       0.864263 |      0.760609 |               5 |                  1 |          0           |                    0.00868056 |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | event_weighted_clip_norm_clip         |       0.740797 |      0.680545 |               5 |                  1 |          3.08395e-18 |                    0.0260417  |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| need_weighted_grounding | event_weighted_clip                   |       0.731925 |      0.617213 |               5 |                  1 |          0           |                    0.0329861  |                 3    |                        0.1875 |              0.0833333 |                      0.0815972  |              576 |
| trajectory_metrics      | resampled_traj_cos                    |       0        |      0        |               5 |                  0 |          6.16791e-18 |                    0.557292   |                 3    |                        0.1875 |              0.0833333 |                      1          |              576 |
| trajectory_metrics      | resampled_traj_gain_vs_audio          |       0.29277  |      0.231455 |               4 |                  0 |          3.08395e-18 |                    0.175347   |                 3    |                        0.375  |              0.0833333 |                      1          |              576 |
| trajectory_metrics      | shift_curve_corr                      |      -0.19518  |     -0.231455 |               4 |                  0 |          0           |                    0.699653   |                 3    |                        0.375  |              0.0833333 |                      1          |              576 |
| ocr_coverage            | weighted_ocr_score                    |       0.948683 |      0.912871 |               3 |                  0 |          6.16791e-18 |                    0.0833333  |                 1.25 |                        0.25   |              0         |                      1          |              576 |

## Caveat

This is still an `n=2` smoke test. The null prevents pure hand-waving, but it does not replace the 20-clip run.
