---
title: "SceneTwin ROI Gap Curve"
category: research
tags: [SceneTwin, TRIBE, ROI, fsaverage5]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_gap_curve.csv
---

# SceneTwin ROI Gap Curve

## Summary

|   clip_idx | roi                  |   mean_need |   max_need |   n_vertices |
|-----------:|:---------------------|------------:|-----------:|-------------:|
|          0 | _unassigned_padding  |    0.165798 |   0.5      |            1 |
|          0 | auditory_control     |    0.404126 |   0.81752  |          590 |
|          0 | body_eba_region      |    0.388802 |   0.726368 |          242 |
|          0 | early_visual_v1      |    0.377428 |   1        |          523 |
|          0 | face_ffc             |    0.409965 |   0.820948 |          264 |
|          0 | higher_visual_v2v3v4 |    0.34825  |   1        |          805 |
|          0 | language_control     |    0.441924 |   0.875846 |          785 |
|          0 | lateral_object_loc   |    0.341472 |   0.647691 |          111 |
|          0 | motion_mt_complex    |    0.348914 |   0.622473 |          212 |
|          0 | retrosplenial_pos    |    0.400095 |   0.967328 |          594 |
|          0 | scene_ppa            |    0.383686 |   1        |          194 |
|          1 | _unassigned_padding  |    0.191249 |   0.5      |            1 |
|          1 | auditory_control     |    0.243655 |   1        |          590 |
|          1 | body_eba_region      |    0.256387 |   1        |          242 |
|          1 | early_visual_v1      |    0.303577 |   0.899608 |          523 |
|          1 | face_ffc             |    0.348079 |   1        |          264 |
|          1 | higher_visual_v2v3v4 |    0.323882 |   0.847831 |          805 |
|          1 | language_control     |    0.33416  |   0.928119 |          785 |
|          1 | lateral_object_loc   |    0.365335 |   1        |          111 |
|          1 | motion_mt_complex    |    0.297442 |   0.812451 |          212 |
|          1 | retrosplenial_pos    |    0.371665 |   1        |          594 |
|          1 | scene_ppa            |    0.359631 |   1        |          194 |

## Verdict

ROI-restricted gap curves are now available from the provided mask. Compare these against whole-cortex need curves before using them as the headline signal.
