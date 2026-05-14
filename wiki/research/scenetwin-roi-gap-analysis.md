---
title: "SceneTwin ROI Gap Analysis"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5, Destrieux]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_gap_analysis.csv
  - output/scenetwin_description_gain/roi_gap_curve.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
---

# SceneTwin ROI Gap Analysis

## Question

Do anatomical proxy ROIs give a cleaner TRIBE accessibility-gap signal than the whole-cortex curve?

## Summary

|   clip_idx | roi_type     |   mean_corr |   mean_top3_overlap |   mean_peak_sharpness |   max_roi_need |
|-----------:|:-------------|------------:|--------------------:|----------------------:|---------------:|
|          0 | control      |    0.812395 |            0.833333 |              0.378633 |       0.798283 |
|          0 | visual_proxy |    0.782758 |            0.75     |              0.465389 |       1        |
|          1 | control      |    0.279896 |            0.333333 |              0.675597 |       1        |
|          1 | visual_proxy |    0.777746 |            0.791667 |              0.718796 |       1        |

## Top ROIs By Clip

|   clip_idx | roi                           | roi_type     |   mean_roi_need |   max_roi_need |   corr_with_whole_need |   top3_overlap_with_whole |   peak_sharpness | top_roi_windows                                                                                                                    |
|-----------:|:------------------------------|:-------------|----------------:|---------------:|-----------------------:|--------------------------:|-----------------:|:-----------------------------------------------------------------------------------------------------------------------------------|
|          0 | scene_context_ppa_proxy       | visual_proxy |        0.353803 |       1        |               0.845461 |                  0.666667 |         0.745489 | t8 7.2-8.1s roi_need_score=1.00 whole=0.78; t7 6.3-7.2s roi_need_score=0.68 whole=0.56; t6 5.4-6.3s roi_need_score=0.66 whole=0.61 |
|          0 | retrosplenial_precuneus_proxy | visual_proxy |        0.393099 |       0.967583 |               0.758219 |                  0.666667 |         0.722986 | t6 5.4-6.3s roi_need_score=0.97 whole=0.61; t8 7.2-8.1s roi_need_score=0.84 whole=0.78; t7 6.3-7.2s roi_need_score=0.80 whole=0.56 |
|          0 | occipital_visual_proxy        | visual_proxy |        0.390577 |       0.876838 |               0.958125 |                  1        |         0.521308 | t8 7.2-8.1s roi_need_score=0.88 whole=0.78; t6 5.4-6.3s roi_need_score=0.66 whole=0.61; t0 0.0-0.9s roi_need_score=0.63 whole=0.65 |
|          0 | early_visual_v1_proxy         | visual_proxy |        0.3766   |       0.861355 |               0.833837 |                  0.666667 |         0.600773 | t8 7.2-8.1s roi_need_score=0.86 whole=0.78; t6 5.4-6.3s roi_need_score=0.86 whole=0.61; t7 6.3-7.2s roi_need_score=0.72 whole=0.56 |
|          0 | language_control              | control      |        0.395119 |       0.798283 |               0.79916  |                  0.666667 |         0.451049 | t8 7.2-8.1s roi_need_score=0.80 whole=0.78; t0 0.0-0.9s roi_need_score=0.65 whole=0.65; t2 1.8-2.7s roi_need_score=0.65 whole=0.31 |
|          0 | ventral_visual_ffa_proxy      | visual_proxy |        0.40966  |       0.755565 |               0.737666 |                  0.666667 |         0.358065 | t0 0.0-0.9s roi_need_score=0.76 whole=0.65; t8 7.2-8.1s roi_need_score=0.65 whole=0.78; t1 0.9-1.8s roi_need_score=0.63 whole=0.29 |
|          1 | body_eba_proxy                | visual_proxy |        0.460045 |       1        |               0.854511 |                  1        |         0.558231 | t0 0.0-0.9s roi_need_score=1.00 whole=0.71; t1 0.9-1.8s roi_need_score=0.78 whole=1.00; t2 1.8-2.8s roi_need_score=0.64 whole=0.64 |
|          1 | early_visual_v1_proxy         | visual_proxy |        0.332595 |       1        |               0.932014 |                  1        |         0.856107 | t1 0.9-1.8s roi_need_score=1.00 whole=1.00; t2 1.8-2.8s roi_need_score=0.71 whole=0.64; t0 0.0-0.9s roi_need_score=0.62 whole=0.71 |
|          1 | lateral_object_loc_proxy      | visual_proxy |        0.399069 |       1        |               0.772646 |                  1        |         0.640556 | t0 0.0-0.9s roi_need_score=1.00 whole=0.71; t1 0.9-1.8s roi_need_score=0.63 whole=1.00; t2 1.8-2.8s roi_need_score=0.50 whole=0.64 |
|          1 | motion_mt_proxy               | visual_proxy |        0.209708 |       1        |               0.485222 |                  0.666667 |         0.867861 | t0 0.0-0.9s roi_need_score=1.00 whole=0.71; t1 0.9-1.8s roi_need_score=0.30 whole=1.00; t9 8.3-9.2s roi_need_score=0.24 whole=0.34 |
|          1 | retrosplenial_precuneus_proxy | visual_proxy |        0.397463 |       1        |               0.841621 |                  0.666667 |         0.720597 | t1 0.9-1.8s roi_need_score=1.00 whole=1.00; t2 1.8-2.8s roi_need_score=0.85 whole=0.64; t3 2.8-3.7s roi_need_score=0.69 whole=0.40 |
|          1 | scene_context_ppa_proxy       | visual_proxy |        0.308792 |       1        |               0.938636 |                  0.666667 |         0.810275 | t1 0.9-1.8s roi_need_score=1.00 whole=1.00; t2 1.8-2.8s roi_need_score=0.70 whole=0.64; t3 2.8-3.7s roi_need_score=0.52 whole=0.40 |

## Verdict

The ROI experiment is unblocked, but the Destrieux proxy atlas is not clean enough to become the headline.

- Clip 00 looks promising: visual/scene proxies peak on the silent tomato/knife action windows.
- Clip 01 is mixed: title-card / speech-heavy regions also drive language and auditory controls.
- Controls can score high, so the current anatomical proxy masks do not prove a uniquely visual cortical gap.

Keep the ROI pipeline, but do not overclaim it until we replace proxy masks with a functional atlas/localizer mask.
