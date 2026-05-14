---
title: "SceneTwin Phase 2 Typing Validation"
category: research
tags: [SceneTwin, TRIBE, validation, phase2, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase2_typing_validation.csv
  - output/scenetwin_description_gain/phase2_typing_confusion.csv
  - output/scenetwin_description_gain/roi_content_typing_windows.csv
  - output/scenetwin_description_gain/texts/
---

# SceneTwin Phase 2 Typing Validation

## Question

Before running TRIBE in a closed loop with an LLM, does TRIBE's per-window
dominant content type agree with the content type a professional AD writer
chose to describe at that moment? If not, the loop optimizes a metric
decoupled from real AD usefulness.

## Method

1. Split each clip's VideoA11y professional AD into sentences.
2. Proportionally time-align sentences to windows by clip duration.
3. Classify each window's pro-AD content via the same content lexicon used
   for TRIBE typing (with shared-vocabulary words split evenly).
4. Compare per-window dominant type from pro AD against TRIBE's dominant
   type. Report agreement rate and confusion matrix.

## Headline

- Windows scored: 21 of 21
- Pro AD vs TRIBE dominant-type agreement: **19.0%**
- Chance agreement (uniform over 6 types): 16.7%
- High-need windows (standard/extended AD slots) agreement: **14.3%** on 7 windows

## Confusion Matrix

Rows: pro AD dominant content type. Columns: TRIBE dominant content type.

| pro_ad_dominant   |   face_character |   motion_action |   object_body |   scene_spatial |   visual_form |
|:------------------|-----------------:|----------------:|--------------:|----------------:|--------------:|
| face_character    |                2 |               0 |             1 |               4 |             1 |
| language_auditory |                1 |               0 |             0 |               0 |             0 |
| motion_action     |                2 |               1 |             0 |               3 |             0 |
| object_body       |                4 |               0 |             1 |               1 |             0 |

## Per-Window Detail

|   clip_idx |   window_idx |   start_s |   end_s | recommendation            | tribe_dominant   | pro_ad_dominant   | agree   | pro_ad_text                                                                                                                                                                          |
|-----------:|-------------:|----------:|--------:|:--------------------------|:-----------------|:------------------|:--------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|          0 |            0 |     0     |   0.902 | standard_ad_slot          | face_character   | object_body       | False   | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            1 |     0.902 |   1.804 | low_ad_need               | face_character   | object_body       | False   | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            2 |     1.804 |   2.706 | low_ad_need               | object_body      | object_body       | True    | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            3 |     2.706 |   3.608 | low_ad_need               | face_character   | object_body       | False   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place. In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish. |
|          0 |            4 |     3.608 |   4.51  | low_ad_need               | face_character   | object_body       | False   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place.                                                                                 |
|          0 |            5 |     4.51  |   5.412 | low_ad_need               | scene_spatial    | object_body       | False   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place.                                                                                 |
|          0 |            6 |     5.412 |   6.314 | standard_ad_slot          | scene_spatial    | face_character    | False   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place. The chef smiles, showcasing his skill.                                          |
|          0 |            7 |     6.314 |   7.216 | standard_ad_slot          | scene_spatial    | face_character    | False   | The chef smiles, showcasing his skill.                                                                                                                                               |
|          0 |            8 |     7.216 |   8.118 | standard_ad_slot          | visual_form      | face_character    | False   | The chef smiles, showcasing his skill.                                                                                                                                               |
|          0 |            9 |     8.118 |   9.02  | low_ad_need               | object_body      | face_character    | False   | The chef smiles, showcasing his skill.                                                                                                                                               |
|          1 |            0 |     0     |   0.92  | extended_or_integrated_ad | face_character   | face_character    | True    | In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                                                                              |
|          1 |            1 |     0.92  |   1.84  | extended_or_integrated_ad | scene_spatial    | face_character    | False   | In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                                                                              |
|          1 |            2 |     1.84  |   2.76  | extended_or_integrated_ad | scene_spatial    | motion_action     | False   | He takes quick bites and washes them down with a drink. In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                      |
|          1 |            3 |     2.76  |   3.68  | low_ad_need               | scene_spatial    | motion_action     | False   | He takes quick bites and washes them down with a drink.                                                                                                                              |
|          1 |            4 |     3.68  |   4.6   | low_ad_need               | scene_spatial    | motion_action     | False   | As he continues, he appears to struggle slightly, coughing at times. He takes quick bites and washes them down with a drink.                                                         |
|          1 |            5 |     4.6   |   5.52  | low_ad_need               | scene_spatial    | face_character    | False   | As he continues, he appears to struggle slightly, coughing at times.                                                                                                                 |
|          1 |            6 |     5.52  |   6.44  | low_ad_need               | face_character   | face_character    | True    | As he continues, he appears to struggle slightly, coughing at times. Around him, people are laughing and clapping, encouraging him to finish.                                        |
|          1 |            7 |     6.44  |   7.36  | low_ad_need               | face_character   | language_auditory | False   | Around him, people are laughing and clapping, encouraging him to finish.                                                                                                             |
|          1 |            8 |     7.36  |   8.28  | low_ad_need               | face_character   | motion_action     | False   | Around him, people are laughing and clapping, encouraging him to finish. Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                   |
|          1 |            9 |     8.28  |   9.2   | low_ad_need               | face_character   | motion_action     | False   | Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                                                                                            |
|          1 |           10 |     9.2   |  10.12  | low_ad_need               | motion_action    | motion_action     | True    | Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                                                                                            |

## Verdict

Agreement 19.0% is at or below chance (16.7%). The current TRIBE typing does NOT track what professional AD writers choose to describe. Phase 2 with TRIBE in the loop will amplify a circular metric. Do not run it. Either switch to a functional atlas or anchor the loop against pro AD / ADQA / human ratings instead of TRIBE residual gap.

## Caveats

- Sentence-to-window alignment is proportional, not timestamped. Pro AD
  does not come with per-sentence timing. Off-by-one window slips are
  expected; clip-level agreement is more robust than per-window.
- The lexicon is small. Words missing from it (e.g. specific food items,
  body parts) score as zero. This biases agreement downward.
- Pro AD for these clips is short (3-5 sentences) covering the whole clip.
  A real test needs longer pro AD or human per-window judgments.
