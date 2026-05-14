---
title: "SceneTwin Phase 1 AD A/B Test"
category: research
tags: [SceneTwin, TRIBE, AD-generation, A-B-test, ROI-content-typing]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase1_ad_candidates.jsonl
  - output/scenetwin_description_gain/phase1_ad_scores.csv
  - output/scenetwin_description_gain/phase1_ad_summary.csv
  - output/scenetwin_description_gain/gap_targeted_prompts.jsonl
---

# SceneTwin Phase 1 AD A/B Test

## Setup

Condition A: baseline prompt with timing/audio context and no TRIBE ROI profile.

Condition B: gap-targeted prompt with TRIBE ROI content profile and dominant/second content-type instructions.

Provider used for this run: `anthropic`.

Model used for this run: `claude-haiku-4-5-20251001`.

All generated AD lines were hard-clamped to the per-window word budget before scoring.

## Summary

| metric                    |   n_pairs |   baseline_mean |   gap_targeted_mean |   mean_delta |   wins |   losses |   ties |   wilcoxon_p |
|:--------------------------|----------:|----------------:|--------------------:|-------------:|-------:|---------:|-------:|-------------:|
| profile_alignment         |        19 |        0.506992 |            0.62303  |     0.116038 |     13 |        6 |      0 |   0.105059   |
| weighted_keyword_coverage |        21 |        1.04837  |            0.997836 |    -0.050537 |     10 |       11 |      0 |   0.683352   |
| dominant_keyword_coverage |        21 |        0.571429 |            1.85714  |     1.28571  |     14 |        5 |      2 |   0.00256889 |
| second_keyword_coverage   |        21 |        0.857143 |            0.428571 |    -0.428571 |      1 |        5 |     15 |   0.958217   |
| specificity_score         |        21 |        0.892857 |            0.5      |    -0.392857 |      1 |       20 |      0 |   0.999949   |
| over_budget               |        21 |        0        |            0        |     0        |      0 |        0 |     21 | nan          |

## Example Outputs

|   clip_idx |   window_idx | condition    | dominant_type   |   word_budget |   word_count |   profile_alignment |   weighted_keyword_coverage | ad_text                    |
|-----------:|-------------:|:-------------|:----------------|--------------:|-------------:|--------------------:|----------------------------:|:---------------------------|
|          0 |            0 | baseline     | face_character  |             4 |            4 |            0.811942 |                    1.58582  | Chef throws tomato knife   |
|          0 |            0 | gap_targeted | face_character  |             4 |            4 |            0.74675  |                    1.33142  | A chef smiles throwing     |
|          0 |            1 | baseline     | face_character  |             4 |            4 |            0.375285 |                    0.806597 | Knife pins tomato to       |
|          0 |            1 | gap_targeted | face_character  |             4 |            4 |            0.844622 |                    1.62369  | Chef smiles eyes bright    |
|          0 |            2 | baseline     | motion_action   |             4 |            4 |            0.407388 |                    1.5      | Knife pins tomato to       |
|          0 |            2 | gap_targeted | motion_action   |             4 |            4 |            0        |                    0        | Tomato flies knife follows |
|          0 |            3 | baseline     | face_character  |             4 |            4 |            0.113412 |                    0.335413 | Knife pins tomato to       |
|          0 |            3 | gap_targeted | face_character  |             4 |            4 |            0.880515 |                    2.32917  | Chef smiles eyes bright    |
|          0 |            4 | baseline     | face_character  |             4 |            4 |            0.511998 |                    0.895572 | Knife pins tomato to       |
|          0 |            4 | gap_targeted | face_character  |             4 |            4 |            0.879351 |                    1.68494  | Chef smiles throws tomato  |
|          0 |            5 | baseline     | scene_spatial   |             4 |            4 |            0.425293 |                    0.694535 | Knife pins tomato to       |
|          0 |            5 | gap_targeted | scene_spatial   |             4 |            4 |            0.633717 |                    1.03491  | Kitchen wall behind him    |
|          0 |            6 | baseline     | visual_form     |             4 |            4 |            0.564977 |                    0.988973 | Chef throws tomato knife   |
|          0 |            6 | gap_targeted | visual_form     |             4 |            4 |            0.634174 |                    0.640917 | A small red tomato         |
|          0 |            7 | baseline     | scene_spatial   |             4 |            4 |            0.510283 |                    0.919547 | Chef throws tomato knife   |
|          0 |            7 | gap_targeted | scene_spatial   |             4 |            4 |            0.666908 |                    1.09708  | Kitchen wall behind him    |

## Verdict

This is a real LLM run. Both conditions received the same visual context; only the gap-targeted condition received the TRIBE ROI profile and type instructions.

Profile alignment delta: `0.1160`.

Weighted keyword coverage delta: `-0.0505`.

Dominant ROI keyword coverage delta: `1.2857` with Wilcoxon p=`0.0026`.

Over-budget delta: `0.0000`.

Interpretation: TRIBE guidance reliably steered the LLM toward the dominant cortical content type, but it reduced secondary-type coverage and specificity after the strict word-budget clamp. The next prompt iteration should preserve the dominant-type instruction while requiring one concrete visual noun or action verb from the shared visual context.
