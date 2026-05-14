---
title: "SceneTwin TRIBE Failure Forecast"
category: research
tags: [SceneTwin, TRIBE, failure-forecast, QA, accessibility]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast_summary.csv
---

# SceneTwin TRIBE Failure Forecast

## Core Claim

TRIBE is not strongest as a direct AD text scorer. Its native SceneTwin role is
pre-scoring risk forecasting: from video/audio alone, estimate whether the
automatic evaluator is likely to be fragile.

## Breakthrough Result

Using `mean_standard_slot_score`, TRIBE ranks the two clips where the all-judge
ADQA scorer loses full tier ordering as the **top two risk clips**.

| target    | feature                  | direction   |   n |   positives |   review_budget_clips |   review_budget_frac |   captured_in_topk |   recall_at_topk |   hypergeom_p_at_least |   exact_all_positive_topk_p |
|:----------|:-------------------------|:------------|----:|------------:|----------------------:|---------------------:|-------------------:|-----------------:|-----------------------:|----------------------------:|
| all4_fail | mean_standard_slot_score | high        |  18 |           2 |                     2 |             0.111111 |                  2 |                1 |             0.00653595 |                  0.00653595 |

This means a TRIBE-based review queue could inspect 2/18 scored clips
(11.1% of the set) and catch both known
all-judge full-order failures.

## Ranked Clips

|   risk_rank |   clip_idx | category       |   mean_standard_slot_score |   all4_fail | quality_risk                 |   all4_mean_tier3_margin |   all4_mean_tier2_vs_tier1 | tribe_route                          |
|------------:|-----------:|:---------------|---------------------------:|------------:|:-----------------------------|-------------------------:|---------------------------:|:-------------------------------------|
|           1 |         12 | Sports         |                  0.280861  |           1 | tier2/tier1 inversion risk   |                0.510417  |                 -0.0208333 | extended/integrated AD likely needed |
|           2 |         15 | Pets & Animals |                  0.245035  |           1 | professional AD barely leads |               -0.025     |                  0.45      | extended/integrated AD likely needed |
|           3 |         11 | Sports         |                  0.215215  |           0 | clean                        |                0.283333  |                  0.383333  | standard AD priority                 |
|           4 |          4 | Food & Cooking |                  0.123797  |           0 | clean                        |                0.520833  |                  0.0625    | low/normal AD pressure               |
|           5 |          3 | Food & Cooking |                  0.117447  |           0 | clean                        |                0.0666667 |                  0.233333  | low/normal AD pressure               |
|           6 |         19 | Pets & Animals |                  0.117186  |           0 | clean                        |                0.392857  |                  0.345238  | low/normal AD pressure               |
|           7 |         14 | Sports         |                  0.064418  |           0 | clean                        |                0.3       |                  0.15      | extended/integrated AD likely needed |
|           8 |         17 | Pets & Animals |                  0.0459038 |           0 | clean                        |                0.736607  |                  0.0669643 | extended/integrated AD likely needed |
|           9 |          5 | Food & Cooking |                  0         |           0 | clean                        |                0.133929  |                  0.531746  | extended/integrated AD likely needed |
|          10 |          8 | Travel         |                  0         |           0 | clean                        |                0.28125   |                  0.364583  | low/normal AD pressure               |
|          11 |          1 | Food & Cooking |                  0         |           0 | clean                        |                0.436111  |                  0.461111  | low/normal AD pressure               |
|          12 |          6 | Travel         |                  0         |           0 | clean                        |                0.432143  |                  0.157143  | extended/integrated AD likely needed |
|          13 |         13 | Sports         |                  0         |           0 | clean                        |                0.221825  |                  0.260317  | low/normal AD pressure               |
|          14 |          7 | Travel         |                  0         |           0 | clean                        |                0.354167  |                  0.0416667 | extended/integrated AD likely needed |
|          15 |          9 | Sports         |                  0         |           0 | clean                        |                0.1       |                  0.242857  | extended/integrated AD likely needed |
|          16 |          0 | Food & Cooking |                  0         |           0 | clean                        |                0.184524  |                  0.077381  | extended/integrated AD likely needed |
|          17 |         18 | Pets & Animals |                  0         |           0 | clean                        |                0.4125    |                  0.3375    | extended/integrated AD likely needed |
|          18 |         16 | Pets & Animals |                  0         |           0 | clean                        |                0.546825  |                  0.294841  | low/normal AD pressure               |

## Feature Comparison

| target                | feature                  | direction   |   roc_auc_oriented |   average_precision |   spearman_rho_raw |   n |   positives |
|:----------------------|:-------------------------|:------------|-------------------:|--------------------:|-------------------:|----:|------------:|
| all4_fail             | mean_standard_slot_score | high        |           1        |            1        |           0.598506 |  18 |           2 |
| all4_fail             | mean_speech_density      | low         |           0.9375   |            0.583333 |          -0.523692 |  18 |           2 |
| all4_fail             | high_need_seconds_frac   | high        |           0.78125  |            0.291667 |           0.307774 |  18 |           2 |
| all4_fail             | high_need_frac           | high        |           0.765625 |            0.25     |           0.291738 |  18 |           2 |
| all4_fail             | mean_extended_need_score | low         |           0.75     |            0.267857 |          -0.272587 |  18 |           2 |
| quality_risk_fail     | mean_standard_slot_score | high        |           0.944444 |            0.583333 |           0.506218 |  20 |           2 |
| quality_risk_fail     | mean_speech_density      | low         |           0.888889 |            0.416667 |          -0.44294  |  20 |           2 |
| quality_risk_fail     | high_need_seconds_frac   | high        |           0.805556 |            0.291667 |           0.31878  |  20 |           2 |
| quality_risk_fail     | high_need_frac           | high        |           0.791667 |            0.25     |           0.305447 |  20 |           2 |
| quality_risk_fail     | mean_need                | high        |           0.777778 |            0.266667 |           0.289037 |  20 |           2 |
| low_tier3_margin      | mean_standard_slot_score | high        |           0.941176 |            0.5      |           0.384911 |  18 |           1 |
| low_tier3_margin      | high_need_seconds_frac   | high        |           0.941176 |            0.333333 |           0.351885 |  18 |           1 |
| low_tier3_margin      | high_need_frac           | high        |           0.911765 |            0.25     |           0.329627 |  18 |           1 |
| low_tier3_margin      | mean_speech_density      | low         |           0.882353 |            0.333333 |          -0.333589 |  18 |           1 |
| low_tier3_margin      | mean_need                | high        |           0.764706 |            0.2      |           0.210367 |  18 |           1 |
| tier2_tier1_inversion | mean_standard_slot_score | high        |           1        |            1        |           0.436232 |  18 |           1 |
| tier2_tier1_inversion | mean_speech_density      | low         |           0.941176 |            0.5      |          -0.384911 |  18 |           1 |
| tier2_tier1_inversion | max_need                 | high        |           0.882353 |            0.333333 |           0.303863 |  18 |           1 |
| tier2_tier1_inversion | mean_extended_need_score | low         |           0.823529 |            0.25     |          -0.257115 |  18 |           1 |
| tier2_tier1_inversion | mean_need                | high        |           0.705882 |            0.166667 |           0.163619 |  18 |           1 |

## Interpretation

This is the cleanest TRIBE-native result so far:

- TRIBE is computed upstream from video/audio, before candidate AD scoring.
- The risk feature comes from the audio-vs-audiovisual accessibility gap, not
  from ADQA/VLM outputs.
- The result does not claim TRIBE improves the final score. It claims TRIBE
  tells SceneTwin when automatic scoring needs stronger adjudication.

The caveat is sample size: only two full-order failures are available, so this
is a strong pilot signal, not a finished statistical proof.
