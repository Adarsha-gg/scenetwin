---
title: "SceneTwin TRIBE Text-Feel Audit"
category: research
tags: [SceneTwin, TRIBE, audio-description, text-profile, diagnostic]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_description_gain/phase1_ad_candidates_tribe_balanced.jsonl
  - /Users/adarsha/Knowledge/output/scenetwin_description_gain/tribe_balanced_text_feel_audit.csv
  - /Users/adarsha/Knowledge/output/scenetwin_description_gain/tribe_balanced_text_feel_summary.csv
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
| feel_alignment        | True               |        21 |        0.505181 | tribe_balanced        |         0.543584 |   0.0384037  |     12 |        8 |      1 |    0.287743  |
| feel_abs_error        | False              |        21 |        0.19174  | tribe_balanced        |         0.203434 |   0.0116935  |      7 |       12 |      2 |    0.832931  |
| weighted_missing_need | False              |        21 |        0.198234 | tribe_balanced        |         0.190582 |  -0.00765165 |      9 |       10 |      2 |    0.5       |
| weighted_surplus_text | False              |        21 |        0.239931 | tribe_balanced        |         0.371067 |   0.131136   |      7 |       13 |      1 |    0.966323  |
| dominant_match        | True               |        21 |        0        | tribe_balanced        |         0.238095 |   0.238095   |      5 |        0 |     16 |    0.0126737 |
| target_type_hit       | True               |        21 |        0.380952 | tribe_balanced        |         0.571429 |   0.190476   |      6 |        2 |     13 |    0.0786496 |
| target_and_second_hit | True               |        21 |        0.142857 | tribe_balanced        |         0.238095 |   0.0952381  |      3 |        1 |     17 |    0.158655  |
| specificity_score     | True               |        21 |        0.892857 | tribe_balanced        |         0.583333 |  -0.309524   |      3 |       14 |      4 |    0.999017  |

## Condition Means

| condition      |   feel_alignment |   feel_abs_error |   weighted_missing_need |   dominant_match |   target_type_hit |   target_and_second_hit |   specificity_score |
|:---------------|-----------------:|-----------------:|------------------------:|-----------------:|------------------:|------------------------:|--------------------:|
| baseline       |         0.505181 |         0.19174  |                0.198234 |         0        |          0.380952 |                0.142857 |            0.892857 |
| tribe_balanced |         0.543584 |         0.203434 |                0.190582 |         0.238095 |          0.571429 |                0.238095 |            0.583333 |

## Dominant-Type Confusion

Rows are TRIBE video-feel dominant type. Columns are generated text-feel dominant type.

| video_dominant_type   |   face_character |   motion_action |   object_body |
|:----------------------|-----------------:|----------------:|--------------:|
| face_character        |           0.3125 |          0.3125 |         0.375 |
| language_auditory     |           0      |          0.5    |         0.5   |
| motion_action         |           0      |          0      |         1     |
| object_body           |           0.75   |          0.25   |         0     |
| scene_spatial         |           0      |          0.75   |         0.25  |
| visual_form           |           0      |          0      |         1     |

## Worst Mismatches

|   clip_idx |   window_idx | condition      | recommendation            | video_dominant_type   | text_dominant_type   |   feel_alignment | biggest_missing_type   |   biggest_missing_delta | biggest_surplus_type   | ad_text                      |
|-----------:|-------------:|:---------------|:--------------------------|:----------------------|:---------------------|-----------------:|:-----------------------|------------------------:|:-----------------------|:-----------------------------|
|          1 |            2 | tribe_balanced | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.129309 | scene_spatial          |                0.358778 | motion_action          | Crowd surrounds him clapping |
|          1 |            1 | tribe_balanced | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.222086 | scene_spatial          |                0.331434 | motion_action          | Crowd surrounds him eating   |
|          0 |            6 | tribe_balanced | standard_ad_slot          | visual_form           | object_body          |         0.479416 | visual_form            |                0.228322 | object_body            | Knife pins tomato against    |
|          0 |            7 | baseline       | standard_ad_slot          | scene_spatial         | object_body          |         0.510283 | scene_spatial          |                0.24771  | object_body            | Chef throws tomato knife     |
|          0 |            7 | tribe_balanced | standard_ad_slot          | scene_spatial         | motion_action        |         0.522045 | scene_spatial          |                0.24771  | motion_action          | Chef throws tomato at        |
|          0 |            8 | baseline       | standard_ad_slot          | visual_form           | object_body          |         0.53954  | visual_form            |                0.222868 | object_body            | Chef throws tomato knife     |
|          0 |            8 | tribe_balanced | standard_ad_slot          | visual_form           | object_body          |         0.554183 | visual_form            |                0.222868 | object_body            | Knife pins tomato wall       |
|          0 |            6 | baseline       | standard_ad_slot          | visual_form           | object_body          |         0.564977 | visual_form            |                0.228322 | object_body            | Chef throws tomato knife     |
|          1 |            2 | baseline       | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.566449 | scene_spatial          |                0.358778 | motion_action          | Man rapidly eating hamburger |
|          1 |            1 | baseline       | extended_or_integrated_ad | scene_spatial         | motion_action        |         0.627324 | scene_spatial          |                0.331434 | motion_action          | Man rapidly eating hamburger |
|          1 |            0 | baseline       | extended_or_integrated_ad | object_body           | face_character       |         0.793906 | object_body            |                0.227414 | face_character         | Bald man eating rapidly      |
|          1 |            0 | tribe_balanced | extended_or_integrated_ad | object_body           | face_character       |         0.796893 | motion_action          |                0.204672 | visual_form            | Man gulps hamburger rapidly  |
|          0 |            0 | baseline       | standard_ad_slot          | face_character        | object_body          |         0.811942 | language_auditory      |                0.156429 | object_body            | Chef throws tomato knife     |
|          0 |            0 | tribe_balanced | standard_ad_slot          | face_character        | object_body          |         0.811942 | language_auditory      |                0.156429 | object_body            | Chef throws tomato knife     |

## Interpretation

TRIBE-guided generation improves the broad feel match:

- Feel alignment delta: `0.0384`.
- Target dominant-type hit delta: `0.1905`.
- Specificity delta: `-0.3095`.

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
