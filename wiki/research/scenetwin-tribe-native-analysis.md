---
title: "SceneTwin TRIBE Native Analysis"
category: research
tags: [SceneTwin, TRIBE, brain-model, routing, accessibility]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/need/coarse_need_windows.csv
  - output/scenetwin_timing_20clip/need/neural_description_need_curve.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_clip_features.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_native_correlations.csv
---

# SceneTwin TRIBE Native Analysis

## Role

TRIBE is the brain-model layer for **accessibility pressure and routing**.
It says where the soundtrack fails to carry the audiovisual scene and whether
the clip likely needs standard AD, extended/integrated AD, or only spot checks.

This makes TRIBE native without forcing it to be the final text scorer:

```text
TRIBE: how much / when / what kind of AD is needed
CLIP/VLM: whether text is visually grounded
ADQA: whether text supports comprehension
```

## Route Counts

| route                                |   clips |
|:-------------------------------------|--------:|
| extended/integrated AD likely needed |      10 |
| low/normal AD pressure               |       9 |
| standard AD priority                 |       1 |

## Highest TRIBE-Pressure Clips

|   clip_idx | category       |   duration_s |   mean_need |   max_need |   high_need_seconds_frac |   extended_seconds_frac |   tribe_pressure |   tier3_va11y_words |   all4_mean_full_order |   all4_mean_tier3_margin |   all4_mean_tier2_vs_tier1 |   claude_vlm_specificity_norm_tier3_margin | tribe_route                          | quality_risk                 |
|-----------:|:---------------|-------------:|------------:|-----------:|-------------------------:|------------------------:|-----------------:|--------------------:|-----------------------:|-------------------------:|---------------------------:|-------------------------------------------:|:-------------------------------------|:-----------------------------|
|          5 | Food & Cooking |        16.39 |    0.659645 |   0.855974 |                 0.909091 |                0.909091 |         1.25932  |                  60 |                      1 |                 0.133929 |                  0.531746  |                                  0.0555556 | extended/integrated AD likely needed | clean                        |
|          9 | Sports         |        16.39 |    0.583079 |   0.765009 |                 0.909091 |                0.909091 |         1.11315  |                  35 |                      1 |                 0.1      |                  0.242857  |                                  0.411765  | extended/integrated AD likely needed | clean                        |
|         18 | Pets & Animals |        16.39 |    0.567958 |   0.794159 |                 0.818182 |                0.818182 |         1.03265  |                  55 |                      1 |                 0.4125   |                  0.3375    |                                  0.277778  | extended/integrated AD likely needed | clean                        |
|         17 | Pets & Animals |        19.37 |    0.571962 |   0.989736 |                 0.769231 |                0.769231 |         1.01193  |                  60 |                      1 |                 0.736607 |                  0.0669643 |                                 -0.0588235 | extended/integrated AD likely needed | clean                        |
|         15 | Pets & Animals |        16.39 |    0.559624 |   0.749315 |                 0.909091 |                0.727273 |         0.966624 |                  53 |                      0 |                -0.025    |                  0.45      |                                  0.411765  | extended/integrated AD likely needed | professional AD barely leads |
|         12 | Sports         |        23.84 |    0.51826  |   0.875534 |                 0.625    |                0.5      |         0.77739  |                  64 |                      0 |                 0.510417 |                 -0.0208333 |                                  0.571429  | extended/integrated AD likely needed | tier2/tier1 inversion risk   |
|         14 | Sports         |        16.39 |    0.400373 |   0.537624 |                 0.727273 |                0.727273 |         0.691553 |                  46 |                      1 |                 0.3      |                  0.15      |                                  0.235294  | extended/integrated AD likely needed | clean                        |
|         11 | Sports         |        16.39 |    0.478241 |   0.620496 |                 0.727273 |                0.363636 |         0.652147 |                  69 |                      1 |                 0.283333 |                  0.383333  |                                  0.294118  | standard AD priority                 | clean                        |
|          0 | Food & Cooking |        14.9  |    0.388396 |   0.584181 |                 0.6      |                0.6      |         0.621434 |                  40 |                      1 |                 0.184524 |                  0.077381  |                                  0.2       | extended/integrated AD likely needed | clean                        |
|          6 | Travel         |        17.88 |    0.397606 |   0.764626 |                 0.5      |                0.5      |         0.596409 |                  40 |                      1 |                 0.432143 |                  0.157143  |                                  0.333333  | extended/integrated AD likely needed | clean                        |
|          7 | Travel         |        16.39 |    0.387123 |   0.939135 |                 0.454545 |                0.454545 |         0.563088 |                  41 |                      1 |                 0.354167 |                  0.0416667 |                                  0.176471  | extended/integrated AD likely needed | clean                        |
|         13 | Sports         |        14.9  |    0.375766 |   0.634439 |                 0.4      |                0.4      |         0.526072 |                  67 |                      1 |                 0.221825 |                  0.260317  |                                  0.230769  | low/normal AD pressure               | clean                        |
|          8 | Travel         |        16.39 |    0.378995 |   0.701496 |                 0.363636 |                0.363636 |         0.516811 |                  56 |                      1 |                 0.28125  |                  0.364583  |                                  0.357143  | low/normal AD pressure               | clean                        |
|          2 | Food & Cooking |        26.82 |    0.435571 |   0.800366 |                 0.444444 |                0.111111 |         0.483967 |                  27 |                    nan |               nan        |                nan         |                                nan         | low/normal AD pressure               | clean                        |

## Strongest Associations

| tribe_feature            | outcome                                   |   spearman_rho |           p |   n |
|:-------------------------|:------------------------------------------|---------------:|------------:|----:|
| mean_standard_slot_score | all4_mean_full_order                      |      -0.750528 | 0.000332722 |  18 |
| mean_speech_density      | all4_mean_full_order                      |       0.519282 | 0.0272124   |  18 |
| mean_extended_need_score | claude_vlm_specificity_norm_tier3_margin  |      -0.477767 | 0.0449351   |  18 |
| mean_speech_density      | claude_vlm_specificity_norm_tier3_margin  |      -0.467741 | 0.0502985   |  18 |
| mean_extended_need_score | claude_vlm_completeness_norm_tier3_margin |      -0.457882 | 0.0560311   |  18 |
| mean_standard_slot_score | claude_vlm_specificity_norm_tier3_margin  |       0.426871 | 0.0772761   |  18 |
| mean_speech_density      | claude_vlm_completeness_norm_tier3_margin |      -0.316016 | 0.201415    |  18 |
| mean_need                | all4_mean_full_order                      |      -0.314241 | 0.204096    |  18 |
| high_need_seconds_frac   | all4_mean_tier3_margin                    |      -0.306579 | 0.215942    |  18 |
| high_need_seconds_frac   | strict_all4_80adqa_20clip_tier3_margin    |      -0.302436 | 0.222529    |  18 |
| high_need_seconds_frac   | all4_mean_full_order                      |      -0.29934  | 0.227536    |  18 |
| tribe_pressure           | all4_mean_tier3_margin                    |      -0.296182 | 0.232717    |  18 |
| mean_need                | all4_mean_tier3_margin                    |      -0.28999  | 0.243092    |  18 |
| mean_standard_slot_score | strict_all4_80adqa_20clip_full_order      |      -0.280742 | 0.259126    |  18 |
| tribe_pressure           | strict_all4_80adqa_20clip_tier3_margin    |      -0.277606 | 0.26471     |  18 |
| mean_need                | strict_all4_80adqa_20clip_tier3_margin    |      -0.265222 | 0.287484    |  18 |

## Quality-Risk Clips Explained By TRIBE

|   clip_idx | category       |   duration_s |   mean_need |   max_need |   high_need_seconds_frac |   extended_seconds_frac |   tribe_pressure |   tier3_va11y_words |   all4_mean_full_order |   all4_mean_tier3_margin |   all4_mean_tier2_vs_tier1 |   claude_vlm_specificity_norm_tier3_margin | tribe_route                          | quality_risk                 |
|-----------:|:---------------|-------------:|------------:|-----------:|-------------------------:|------------------------:|-----------------:|--------------------:|-----------------------:|-------------------------:|---------------------------:|-------------------------------------------:|:-------------------------------------|:-----------------------------|
|         15 | Pets & Animals |        16.39 |    0.559624 |   0.749315 |                 0.909091 |                0.727273 |         0.966624 |                  53 |                      0 |                -0.025    |                  0.45      |                                   0.411765 | extended/integrated AD likely needed | professional AD barely leads |
|         12 | Sports         |        23.84 |    0.51826  |   0.875534 |                 0.625    |                0.5      |         0.77739  |                  64 |                      0 |                 0.510417 |                 -0.0208333 |                                   0.571429 | extended/integrated AD likely needed | tier2/tier1 inversion risk   |

## Interpretation

TRIBE gives SceneTwin a native product layer that the pure VLM/ADQA stack lacks:
it can justify **why** a clip needs more description and where the AD should be
inserted. The quality scorers say which candidate wins; TRIBE says whether the
clip needs standard AD, extended/integrated AD, or only focused high-need checks.

The next useful experiment is to feed `tribe_route`, high-need windows, and
dominant missing content type into the generator, then re-run:

1. TRIBE text-feel audit.
2. VLM direct rater.
3. ADQA.
4. Optional Colab neural closure: `P_A+AD` vs `P_AV`.
