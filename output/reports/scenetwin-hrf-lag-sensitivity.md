---
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

| metric                 |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |   lag_s |
|:-----------------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|--------:|
| need_weighted_clip     |       0.9759   |   3.4364e-05 |      0.92582  |  0.00218017 |               6 |                6 |                  2 |                  2 |     0   |
| critical_weighted_clip |       0.9759   |   3.4364e-05 |      0.92582  |  0.00218017 |               6 |                6 |                  2 |                  2 |     0   |
| clip_mean              |       0.87831  |   0.00410393 |      0.771517 |  0.0106564  |               6 |                6 |                  1 |                  2 |     0   |
| clip_top3              |       0.87831  |   0.00410393 |      0.771517 |  0.0106564  |               6 |                6 |                  1 |                  2 |     0   |
| clip_mean              |       0.87831  |   0.00410393 |      0.771517 |  0.0106564  |               6 |                6 |                  1 |                  2 |     2.5 |
| clip_top3              |       0.87831  |   0.00410393 |      0.771517 |  0.0106564  |               6 |                6 |                  1 |                  2 |     2.5 |
| need_weighted_clip     |       0.87831  |   0.00410393 |      0.771517 |  0.0106564  |               6 |                6 |                  1 |                  2 |     2.5 |
| critical_weighted_clip |       0.78072  |   0.0222145  |      0.694365 |  0.0215395  |               5 |                6 |                  1 |                  2 |     2.5 |
| clip_top3              |       0.731925 |   0.0389983  |      0.617213 |  0.0410509  |               5 |                6 |                  1 |                  2 |     5   |
| need_weighted_clip     |       0.68313  |   0.0618347  |      0.540062 |  0.0738343  |               5 |                6 |                  1 |                  2 |     5   |
| critical_weighted_clip |       0.68313  |   0.0618347  |      0.540062 |  0.0738343  |               5 |                6 |                  1 |                  2 |     5   |
| clip_mean              |       0.731925 |   0.0389983  |      0.617213 |  0.0410509  |               4 |                6 |                  1 |                  2 |     5   |

## Interpretation

This script does not assume the right lag. It gives us a sensitivity table. If `0.0s` wins, the current extracted validation frames are likely already closer to the model's effective alignment. If `5.0s` wins, the previous frame matching was probably offset.
