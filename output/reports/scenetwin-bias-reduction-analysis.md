---
title: "SceneTwin Bias Reduction Analysis"
category: research
tags: [SceneTwin, ADQA, bias, confounds, validation]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/ensemble/bias_reduction_analysis.csv
  - output/scenetwin_timing_20clip/ensemble/bias_reduction_summary.csv
---

# SceneTwin Bias Reduction Analysis

This analysis checks whether the multi-judge lift is driven by cherry-picking,
same-set weight tuning, or description length.

## Main Results

| metric                             |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |   perm_p_ge_observed |
|:-----------------------------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|---------------------:|
| word_len_norm                      |       0.317909 |  0.00650209  |      0.271109 | 0.00374963  |              51 |               54 |                  0 |                 18 |                  nan |
| clip_mean_norm                     |       0.798568 |  4.35584e-17 |      0.689487 | 1.68756e-13 |              48 |               54 |                 11 |                 18 |                  nan |
| all4_mean                          |       0.932661 |  1.02815e-32 |      0.849919 | 5.70956e-20 |              53 |               54 |                 16 |                 18 |                    0 |
| all4_median                        |       0.923152 |  8.89488e-31 |      0.840642 | 2.89786e-19 |              53 |               54 |                 16 |                 18 |                  nan |
| all4_trimmed_mean                  |       0.922506 |  1.17896e-30 |      0.839789 | 3.04657e-19 |              53 |               54 |                 16 |                 18 |                  nan |
| strict_all4_80adqa_20clip          |       0.926012 |  2.47707e-31 |      0.834183 | 1.20672e-19 |              54 |               54 |                 16 |                 18 |                    0 |
| strict_all4_50adqa_50clip          |       0.917566 |  9.41916e-30 |      0.822039 | 4.01767e-19 |              54 |               54 |                 15 |                 18 |                  nan |
| selected3_mean                     |       0.944489 |  1.45628e-35 |      0.865052 | 1.52117e-20 |              53 |               54 |                 16 |                 18 |                  nan |
| clip_mean_norm_lenresid            |       0.875693 |  7.97504e-24 |      0.761209 | 4.00977e-16 |              50 |               54 |                  9 |                 18 |                  nan |
| all4_mean_lenresid                 |       0.873567 |  1.39066e-23 |      0.768381 | 2.12259e-16 |              49 |               54 |                 10 |                 18 |                    0 |
| all4_median_lenresid               |       0.867798 |  5.98892e-23 |      0.757383 | 5.61596e-16 |              48 |               54 |                  9 |                 18 |                  nan |
| strict_all4_50adqa_50clip_lenresid |       0.88632  |  4.20837e-25 |      0.776987 | 9.81834e-17 |              49 |               54 |                 11 |                 18 |                  nan |
| selected3_mean_lenresid            |       0.874782 |  1.01336e-23 |      0.769337 | 1.94914e-16 |              49 |               54 |                 11 |                 18 |                  nan |
| loocv_all4_clip                    |       0.932661 |  1.02815e-32 |      0.849919 | 5.70956e-20 |              53 |               54 |                 16 |                 18 |                    0 |

## Word-Length Association

| metric                    |   spearman_with_word_length |
|:--------------------------|----------------------------:|
| clip_mean_norm            |                   0.0600169 |
| cc                        |                   0.238968  |
| cg                        |                   0.218324  |
| gc                        |                   0.250875  |
| gg                        |                   0.228744  |
| all4_mean                 |                   0.248811  |
| selected3_mean            |                   0.268253  |
| strict_all4_80adqa_20clip |                   0.244755  |

## Interpretation

The least cherry-picked primary score is `all4_mean`: the equal average of all
four non-Gemini ADQA model pairs. It reaches rho=0.933, 53/54 pairwise wins,
and 16/18 fully ordered clips. This is lower than the selected 3-judge headline
rho=0.944, but it avoids choosing judges after seeing results.

Description length is a real confound for ADQA: all-judge ADQA has a
word-length Spearman association of about 0.25. Length alone is weak, however
(rho=0.318 and 0/18 fully ordered clips), so verbosity is not sufficient to
explain the result.

After removing within-clip word-length effects, the all-judge score remains
well above chance at rho=0.874 with permutation p=0.0000. This is a stricter
diagnostic, not the preferred production metric, because good ADs are often
longer for legitimate reasons.

Leave-one-clip-out weight selection picks ADQA-only for every fold, so the
strict no-heldout-tuning result is still the all-four-judge ADQA mean.
