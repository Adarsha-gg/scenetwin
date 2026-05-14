---
title: "SceneTwin Need-Weighted Grounding"
category: research
tags: [SceneTwin, CLIP, TRIBE, grounding, accessibility-gap]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/need_weighted_grounding_results.csv
  - output/scenetwin_description_gain/need_weighted_grounding_summary.csv
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin Need-Weighted Grounding

## Metric

Instead of scoring descriptions against arbitrary/top video frames, this test weights frame-text grounding by TRIBE-derived AD importance:

```text
NeedWeightedGrounding(d) = sum_t CLIP(frame_t, d) * ADNeed(t)
```

Variants use standard-slot weight, extended-need weight, visual-event weight, and a critical max of need/event.

## Result

On the two saved clips, generic CLIP top-3 is already perfect. Need-weighted grounding also performs well and gives TRIBE a cleaner role: focus visual grounding on moments where AD is needed.

## Top Metrics

| metric                                |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   tier3_gt_tier2_vatex_long_wins |   tier3_gt_tier2_vatex_long_total |   tier3_gt_tier1_vatex_short_wins |   tier3_gt_tier1_vatex_short_total |   tier3_gt_tier0_cross_wins |   tier3_gt_tier0_cross_total |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:--------------------------------------|---------------:|-------------:|--------------:|------------:|---------------------------------:|----------------------------------:|----------------------------------:|-----------------------------------:|----------------------------:|-----------------------------:|----------------:|-----------------:|-------------------:|-------------------:|
| need_weighted_clip                    |       0.9759   |  3.4364e-05  |      0.92582  |  0.00218017 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  2 |                  2 |
| critical_weighted_clip                |       0.9759   |  3.4364e-05  |      0.92582  |  0.00218017 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  2 |                  2 |
| need_weighted_clip_norm_clip          |       0.938343 |  0.000559219 |      0.880705 |  0.00438228 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  2 |                  2 |
| critical_weighted_clip_norm_clip      |       0.938343 |  0.000559219 |      0.880705 |  0.00438228 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  2 |                  2 |
| clip_mean_norm_clip                   |       0.888957 |  0.00314433  |      0.800641 |  0.00959132 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| clip_top3_norm_clip                   |       0.888957 |  0.00314433  |      0.800641 |  0.00959132 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| extended_need_weighted_clip_norm_clip |       0.888957 |  0.00314433  |      0.800641 |  0.00959132 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| clip_mean                             |       0.87831  |  0.00410393  |      0.771517 |  0.0106564  |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| clip_top3                             |       0.87831  |  0.00410393  |      0.771517 |  0.0106564  |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| extended_need_weighted_clip           |       0.87831  |  0.00410393  |      0.771517 |  0.0106564  |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| opportunity_weighted_clip             |       0.927105 |  0.00091618  |      0.848668 |  0.0049673  |                                1 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               5 |                6 |                  1 |                  2 |
| standard_slot_weighted_clip           |       0.87831  |  0.00410393  |      0.771517 |  0.0106564  |                                1 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               5 |                6 |                  1 |                  2 |

## Mean Scores By Tier

| tier              |   clip_top3 |   need_weighted_clip |   event_weighted_clip |   critical_weighted_clip |   opportunity_weighted_clip |
|:------------------|------------:|---------------------:|----------------------:|-------------------------:|----------------------------:|
| tier3_va11y       |   0.343871  |            0.300996  |            0.292375   |                0.297886  |                   0.29993   |
| tier2_vatex_long  |   0.302203  |            0.26684   |            0.267077   |                0.266646  |                   0.267761  |
| tier1_vatex_short |   0.293635  |            0.255438  |            0.268133   |                0.257702  |                   0.254917  |
| tier0_cross       |   0.0787466 |            0.0359541 |            0.00889429 |                0.0300275 |                   0.0361925 |

## Interpretation

This is a better integration than `TRIBE(description_text)`:

- TRIBE never judges text correctness.
- CLIP/SigLIP/PAC-S handles visual grounding.
- TRIBE decides which frames count most for accessibility.

If this holds on 20 clips, SceneTwin becomes:

```text
ADNeed(t) from TRIBE
ContentGrounding(t, description) from CLIP/PAC-S
NeedWeightedGrounding = grounding focused on inaccessible moments
```

The next stronger version should replace CLIP with PAC-S or SigLIP and add OCR/VLM coverage for on-screen text.
