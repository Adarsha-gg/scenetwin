---
title: "SceneTwin TRIBE Text-Feel Audit"
category: research
tags: [SceneTwin, TRIBE, audio-description, text-profile, diagnostic]
created: 2026-05-06
updated: 2026-05-06
sources:
  - /Users/adarsha/Knowledge/output/scenetwin_description_gain/phase1_ad_candidates.jsonl
  - /Users/adarsha/Knowledge/output/scenetwin_description_gain/tribe_text_feel_audit.csv
  - /Users/adarsha/Knowledge/output/scenetwin_description_gain/tribe_text_feel_summary.csv
---

# SceneTwin TRIBE Text-Feel Audit

## Question

Does the generated text match the kind of visual/neural content TRIBE says is
missing from the soundtrack?

```text
video feel = TRIBE ROI gap profile from P_AV - P_A
text feel  = generated AD projected into the same content-type space
```

## Paired Summary

| metric                | higher_is_better   |   n_pairs |   baseline_mean | candidate_condition   |   candidate_mean |   mean_delta |   wins |   losses |   ties |   wilcoxon_p |
|:----------------------|:-------------------|----------:|----------------:|:----------------------|-----------------:|-------------:|-------:|---------:|-------:|-------------:|
| feel_alignment        | True               |        21 |        0.505181 | gap_targeted          |         0.563694 |  0.0585133   |     13 |        8 |      0 |  0.292701    |
| feel_abs_error        | False              |        21 |        0.19174  | gap_targeted          |         0.192121 |  0.000380373 |     12 |        9 |      0 |  0.445866    |
| weighted_missing_need | False              |        21 |        0.198234 | gap_targeted          |         0.193871 | -0.00436269  |     12 |        9 |      0 |  0.419097    |
| weighted_surplus_text | False              |        21 |        0.239931 | gap_targeted          |         0.367001 |  0.12707     |      8 |       13 |      0 |  0.958902    |
| dominant_match        | True               |        21 |        0        | gap_targeted          |         0.619048 |  0.619048    |     13 |        0 |      8 |  0.000155745 |
| target_type_hit       | True               |        21 |        0.380952 | gap_targeted          |         0.714286 |  0.333333    |     12 |        5 |      4 |  0.0447775   |
| target_and_second_hit | True               |        21 |        0.142857 | gap_targeted          |         0.142857 |  0           |      2 |        2 |     17 |  0.5         |
| specificity_score     | True               |        21 |        0.892857 | gap_targeted          |         0.5      | -0.392857    |      1 |       20 |      0 |  0.999995    |

## Condition Means

| condition    |   feel_alignment |   feel_abs_error |   weighted_missing_need |   dominant_match |   target_type_hit |   target_and_second_hit |   specificity_score |
|:-------------|-----------------:|-----------------:|------------------------:|-----------------:|------------------:|------------------------:|--------------------:|
| baseline     |         0.505181 |         0.19174  |                0.198234 |         0        |          0.380952 |                0.142857 |            0.892857 |
| gap_targeted |         0.563694 |         0.192121 |                0.193871 |         0.619048 |          0.714286 |                0.142857 |            0.5      |

## Dominant-Type Confusion

Rows are TRIBE video-feel dominant type. Columns are generated text-feel dominant type.

| video_dominant_type   |   face_character |   motion_action |   object_body |   scene_spatial |
|:----------------------|-----------------:|----------------:|--------------:|----------------:|
| face_character        |            0.375 |        0.375    |      0.25     |             0   |
| language_auditory     |            0     |        1        |      0        |             0   |
| motion_action         |            0     |        0        |      1        |             0   |
| object_body           |            0.5   |        0.25     |      0.25     |             0   |
| scene_spatial         |            0     |        0.333333 |      0.166667 |             0.5 |
| visual_form           |            0     |        0        |      1        |             0   |

## Worst Mismatches

|   clip_idx |   window_idx | condition    | recommendation            | video_dominant_type   | text_dominant_type   |   feel_alignment | biggest_missing_type   |   biggest_missing_delta | biggest_surplus_type   | ad_text                      |
|-----------:|-------------:|:-------------|:--------------------------|:----------------------|:---------------------|-----------------:|:-----------------------|------------------------:|:-----------------------|:-----------------------------|
|          0 |            7 | baseline     | standard_ad_slot          | scene_spatial         | object_body          |         0.510283 | scene_spatial          |                0.24771  | object_body            | Chef throws tomato knife     |
|          1 |            0 | gap_targeted | extended_or_integrated_ad | object_body           | object_body          |         0.531067 | face_character         |                0.217209 | object_body            | A hamburger disappears in    |
|          0 |            8 | baseline     | standard_ad_slot          | visual_form           | object_body          |         0.53954  | visual_form            |                0.222868 | object_body            | Chef throws tomato knife     |
|          0 |            6 | baseline     | standard_ad_slot          | visual_form           | object_body          |         0.564977 | visual_form            |                0.228322 | object_body            | Chef throws tomato knife     |
|          1 |            2 | baseline     | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.566449 | scene_spatial          |                0.358778 | motion_action          | Man rapidly eating hamburger |
|          0 |            8 | gap_targeted | standard_ad_slot          | visual_form           | object_body          |         0.616459 | scene_spatial          |                0.217079 | object_body            | A small red tomato           |
|          1 |            1 | baseline     | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.627324 | scene_spatial          |                0.331434 | motion_action          | Man rapidly eating hamburger |
|          0 |            6 | gap_targeted | standard_ad_slot          | visual_form           | object_body          |         0.634174 | scene_spatial          |                0.223912 | object_body            | A small red tomato           |
|          0 |            7 | gap_targeted | standard_ad_slot          | scene_spatial         | scene_spatial        |         0.666908 | visual_form            |                0.24304  | scene_spatial          | Kitchen wall behind him      |
|          0 |            0 | gap_targeted | standard_ad_slot          | face_character        | face_character       |         0.74675  | object_body            |                0.198551 | face_character         | A chef smiles throwing       |
|          1 |            0 | baseline     | extended_or_integrated_ad | object_body           | face_character       |         0.793906 | object_body            |                0.227414 | face_character         | Bald man eating rapidly      |
|          0 |            0 | baseline     | standard_ad_slot          | face_character        | object_body          |         0.811942 | language_auditory      |                0.156429 | object_body            | Chef throws tomato knife     |
|          1 |            1 | gap_targeted | extended_or_integrated_ad | scene_spatial         | scene_spatial        |         0.816227 | visual_form            |                0.252689 | scene_spatial          | Inside a Burger King         |
|          1 |            2 | gap_targeted | extended_or_integrated_ad | scene_spatial         | scene_spatial        |         0.818476 | visual_form            |                0.262508 | face_character         | Inside Burger King people    |

## Interpretation

TRIBE-guided generation improves the broad feel match:

- Feel alignment delta: `0.0585`.
- Target dominant-type hit delta: `0.3333`.
- Specificity delta: `-0.3929`.

The failure mode is visible: the prompt steers the text toward the dominant TRIBE
dimension, but under a 4-word budget it often drops secondary concrete details.
So the text can match the brain-guided "vibe" while becoming less specific.

This makes TRIBE useful as a **diagnostic controller**:

1. Use TRIBE to say what kind of content the video needs.
2. Generate AD text.
3. Audit whether the text feel matches the video feel.
4. Send mismatches back to the generator, especially `biggest_missing_type`.

This is not yet the full closed-loop TRIBE neural test. The stronger next step is
to run TRIBE on `audio + generated AD` in Colab and measure whether it moves the
predicted response closer to `P_AV`.
