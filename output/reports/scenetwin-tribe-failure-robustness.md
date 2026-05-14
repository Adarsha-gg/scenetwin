---
title: "SceneTwin TRIBE Failure Forecast Robustness"
category: research
tags: [SceneTwin, TRIBE, robustness, validation]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_summary.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_feature_auc.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_robustness_margin_corr.csv
---

# SceneTwin TRIBE Failure Forecast Robustness

## Main Check

For the all-four ADQA mean, `mean_standard_slot_score` ranks the two full-order
failure clips at ranks `1,2`. Reviewing the top two TRIBE
risk clips catches `2/2` failures.

- Uncorrected random top-k p: `0.0065`
- Bonferroni over 10 TRIBE features: `0.0654`

The result is a strong pilot signal, but after accounting for feature search it
is not yet a finished proof. The correct claim is **promising failure forecast**,
not solved validation.

## Cross-Scorer Top-k Capture

| scorer                       |   n |   failures |   topk_captured |   recall_at_k_failures |   topk_p_uncorrected |   exact_all_failures_topk_p | failure_ranks     |
|:-----------------------------|----:|-----------:|----------------:|-----------------------:|---------------------:|----------------------------:|:------------------|
| all4_mean                    |  18 |          2 |               2 |               1        |           0.00653595 |                 0.00653595  | 1,2               |
| selected3_mean               |  18 |          2 |               2 |               1        |           0.00653595 |                 0.00653595  | 1,2               |
| strict_all4_80adqa_20clip    |  18 |          2 |               1 |               0.5      |           0.215686   |                 0.00653595  | 1,18              |
| claude_vlm_completeness_norm |  18 |          2 |               1 |               0.5      |           0.215686   |                 0.00653595  | 1,5               |
| vlm_best_dims_mean           |  18 |          2 |               1 |               0.5      |           0.215686   |                 0.00653595  | 1,5               |
| clip_mean_norm               |  18 |          7 |               3 |               0.428571 |           0.583145   |                 3.14228e-05 | 1,4,7,13,14,16,18 |
| claude_vlm_specificity_norm  |  18 |          2 |               0 |               0        |           1          |                 0.00653595  | 5,8               |

## All4 Feature Comparison

| target                    | feature                  | feature_kind   | direction   |   auc_oriented |   average_precision |   positives |   n |
|:--------------------------|:-------------------------|:---------------|:------------|---------------:|--------------------:|------------:|----:|
| all4_mean_full_order_fail | mean_standard_slot_score | TRIBE          | high        |       1        |            1        |           2 |  18 |
| all4_mean_full_order_fail | mean_speech_density      | TRIBE          | low         |       0.9375   |            0.583333 |           2 |  18 |
| all4_mean_full_order_fail | high_need_seconds_frac   | TRIBE          | high        |       0.78125  |            0.291667 |           2 |  18 |
| all4_mean_full_order_fail | high_need_frac           | TRIBE          | high        |       0.765625 |            0.25     |           2 |  18 |
| all4_mean_full_order_fail | mean_extended_need_score | TRIBE          | low         |       0.75     |            0.267857 |           2 |  18 |
| all4_mean_full_order_fail | mean_need                | TRIBE          | high        |       0.75     |            0.266667 |           2 |  18 |
| all4_mean_full_order_fail | tribe_pressure           | TRIBE          | high        |       0.75     |            0.266667 |           2 |  18 |
| all4_mean_full_order_fail | pro_minus_long_words     | cheap_baseline | high        |       0.734375 |            0.35     |           2 |  18 |
| all4_mean_full_order_fail | duration_s               | cheap_baseline | high        |       0.71875  |            0.5625   |           2 |  18 |
| all4_mean_full_order_fail | max_need                 | TRIBE          | high        |       0.71875  |            0.277778 |           2 |  18 |

## Strongest Continuous Margin Associations

| scorer                      | outcome        | feature                  |   spearman_rho |         p |   n |
|:----------------------------|:---------------|:-------------------------|---------------:|----------:|----:|
| vlm_best_dims_mean          | tier2_vs_tier1 | mean_speech_density      |       0.552879 | 0.0173256 |  18 |
| vlm_best_dims_mean          | tier2_vs_tier1 | mean_standard_slot_score |      -0.550613 | 0.0178865 |  18 |
| claude_vlm_specificity_norm | tier2_vs_tier1 | mean_standard_slot_score |      -0.542682 | 0.0199633 |  18 |
| vlm_best_dims_mean          | tier3_margin   | mean_extended_need_score |      -0.53354  | 0.022588  |  18 |
| vlm_best_dims_mean          | spread         | mean_need                |      -0.513994 | 0.0291029 |  18 |
| claude_vlm_specificity_norm | tier2_vs_tier1 | mean_speech_density      |       0.506428 | 0.0319835 |  18 |
| vlm_best_dims_mean          | spread         | mean_extended_need_score |      -0.481869 | 0.0428708 |  18 |
| vlm_best_dims_mean          | spread         | tribe_pressure           |      -0.481869 | 0.0428708 |  18 |
| claude_vlm_specificity_norm | tier3_margin   | mean_extended_need_score |      -0.477767 | 0.0449351 |  18 |
| vlm_best_dims_mean          | tier3_margin   | mean_speech_density      |      -0.476971 | 0.0453444 |  18 |
| vlm_best_dims_mean          | spread         | max_need                 |      -0.470531 | 0.0487597 |  18 |
| claude_vlm_specificity_norm | tier3_margin   | mean_speech_density      |      -0.467741 | 0.0502985 |  18 |

## Verdict

The signal is real enough to keep: the same TRIBE risk feature also predicts
`tier2/tier1` inversion risk and low tier3 margin better than cheap text-length
baselines. But it is fragile because there are only two all4 failures. The next
clean validation would be to run this on a larger clip set and freeze
`mean_standard_slot_score` as the risk feature before looking at outcomes.
