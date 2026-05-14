---
title: "SceneTwin Coarse Need Windows"
category: research
tags: [SceneTwin, TRIBE, timing, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/coarse_need_windows.csv
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin Coarse Need Windows

## Why

The raw TRIBE outputs should not be marketed as frame-exact AD timing. This file aggregates them into `3.0s` windows, which is closer to the model's effective temporal resolution.

## Output

|   clip_idx |   window_idx |   start_s |   end_s |   need_score |   speech_density |   standard_slot_score |   extended_need_score |   visual_event_score |   visual_event_need | recommendation            |   raw_trs |
|-----------:|-------------:|----------:|--------:|-------------:|-----------------:|----------------------:|----------------------:|---------------------:|--------------------:|:--------------------------|----------:|
|          0 |            0 |     0     |   3.608 |     0.360617 |         0.183011 |             0.306192  |             0.0544253 |            0.485675  |          0.0233911  | low_ad_need               |         4 |
|          0 |            1 |     3.608 |   6.314 |     0.453619 |         0        |             0.453619  |             0         |            0.136012  |          0.0825378  | standard_ad_slot          |         3 |
|          0 |            2 |     6.314 |   9.02  |     0.444726 |         0        |             0.444726  |             0         |            1         |          0.117137   | inspect_visual_event      |         3 |
|          1 |            0 |     0     |   3.68  |     0.753606 |         0.705145 |             0.238591  |             0.515015  |            0.0789468 |          0.0318856  | extended_or_integrated_ad |         4 |
|          1 |            1 |     3.68  |   6.44  |     0.186984 |         0.768275 |             0.0420085 |             0.144976  |            0.106912  |          0.0182489  | low_ad_need               |         3 |
|          1 |            2 |     6.44  |   9.2   |     0.252892 |         0.202632 |             0.212724  |             0.0401682 |            0.0371511 |          0.00265695 | low_ad_need               |         3 |
|          1 |            3 |     9.2   |  10.12  |     0.140605 |         0.781522 |             0.0307192 |             0.109886  |            1         |          0.140605   | low_ad_need               |         1 |

## Top Windows Per Clip

|   clip_idx |   window_idx |   start_s |   end_s |   need_score |   speech_density |   standard_slot_score |   extended_need_score |   visual_event_score |   visual_event_need | recommendation            |   raw_trs |
|-----------:|-------------:|----------:|--------:|-------------:|-----------------:|----------------------:|----------------------:|---------------------:|--------------------:|:--------------------------|----------:|
|          0 |            1 |     3.608 |   6.314 |     0.453619 |         0        |             0.453619  |             0         |            0.136012  |          0.0825378  | standard_ad_slot          |         3 |
|          0 |            2 |     6.314 |   9.02  |     0.444726 |         0        |             0.444726  |             0         |            1         |          0.117137   | inspect_visual_event      |         3 |
|          0 |            0 |     0     |   3.608 |     0.360617 |         0.183011 |             0.306192  |             0.0544253 |            0.485675  |          0.0233911  | low_ad_need               |         4 |
|          1 |            0 |     0     |   3.68  |     0.753606 |         0.705145 |             0.238591  |             0.515015  |            0.0789468 |          0.0318856  | extended_or_integrated_ad |         4 |
|          1 |            2 |     6.44  |   9.2   |     0.252892 |         0.202632 |             0.212724  |             0.0401682 |            0.0371511 |          0.00265695 | low_ad_need               |         3 |
|          1 |            1 |     3.68  |   6.44  |     0.186984 |         0.768275 |             0.0420085 |             0.144976  |            0.106912  |          0.0182489  | low_ad_need               |         3 |

## Interpretation

Use these windows for demos, reports, and human validation sheets. Keep raw TR rows for debugging only.
