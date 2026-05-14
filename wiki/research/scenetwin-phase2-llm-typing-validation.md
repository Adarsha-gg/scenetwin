---
title: "SceneTwin Phase 2 LLM Typing Validation"
category: research
tags: [SceneTwin, TRIBE, validation, phase2, audio-description, Claude]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase2_llm_typing_validation.csv
  - output/scenetwin_description_gain/phase2_llm_typing_confusion.csv
  - output/scenetwin_description_gain/phase2_typing_validation.csv
---

# SceneTwin Phase 2 LLM Typing Validation

## Question

Was the failed TRIBE/pro-AD typing validation caused by the hand-written lexicon,
or does Glasser ROI typing still fail when a stronger classifier reads the
professional AD text?

## Method

Same windows, same proportional alignment, same Glasser TRIBE dominant labels as
`phase2_typing_validation.csv`. The only changed component is the pro-AD content
classifier: `anthropic` with model `claude-haiku-4-5-20251001`.

Claude saw the AD snippet, timing, and type definitions. It did not see TRIBE's
dominant type, ROI scores, agreement labels, or any metric target.

## Headline

| Metric | Value |
|---|---:|
| Windows scored | 21 |
| Chance agreement | 16.7% |
| Lexicon pro-AD vs TRIBE agreement | 4/21 (19.0%) |
| LLM pro-AD vs TRIBE agreement | 1/21 (4.8%) |
| LLM vs lexicon pro-AD agreement | 9/21 (42.9%) |
| High-need lexicon agreement | 14.3% |
| High-need LLM agreement | 0.0% |

## Confusion Matrix

Rows: LLM-classified professional AD dominant type. Columns: TRIBE dominant type.

| llm_primary_pro_ad   |   face_character |   motion_action |   object_body |   scene_spatial |   visual_form |
|:---------------------|-----------------:|----------------:|--------------:|----------------:|--------------:|
| face_character       |                0 |               0 |             1 |               1 |             1 |
| motion_action        |                9 |               1 |             1 |               7 |             0 |

## Per-Window Detail

|   clip_idx |   window_idx |   start_s |   end_s | recommendation            | tribe_dominant   | pro_ad_dominant   | llm_primary    | llm_agree   | llm_rationale                                                                 | pro_ad_text                                                                                                                                                                          |
|-----------:|-------------:|----------:|--------:|:--------------------------|:-----------------|:------------------|:---------------|:------------|:------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|          0 |            0 |     0     |   0.902 | standard_ad_slot          | face_character   | object_body       | motion_action  | False       | Chef's countdown action is primary; Spanish speech is secondary.              | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            1 |     0.902 |   1.804 | low_ad_need               | face_character   | object_body       | motion_action  | False       | Chef's countdown action is primary; Spanish speech is secondary.              | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            2 |     1.804 |   2.706 | low_ad_need               | object_body      | object_body       | motion_action  | False       | Chef's countdown action is primary; Spanish speech is secondary.              | In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish.                                                                                                      |
|          0 |            3 |     2.706 |   3.608 | low_ad_need               | face_character   | object_body       | motion_action  | False       | Throwing tomato and knife actions dominate; objects secondary.                | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place. In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish. |
|          0 |            4 |     3.608 |   4.51  | low_ad_need               | face_character   | object_body       | motion_action  | False       | Throwing and pinning actions are the primary visual events.                   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place.                                                                                 |
|          0 |            5 |     4.51  |   5.412 | low_ad_need               | scene_spatial    | object_body       | motion_action  | False       | Throwing and pinning actions are the primary visual events.                   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place.                                                                                 |
|          0 |            6 |     5.412 |   6.314 | standard_ad_slot          | scene_spatial    | face_character    | motion_action  | False       | Throwing action primary; chef's smile/expression secondary.                   | With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place. The chef smiles, showcasing his skill.                                          |
|          0 |            7 |     6.314 |   7.216 | standard_ad_slot          | scene_spatial    | face_character    | face_character | False       | Chef's smile and expression are the sole focus here.                          | The chef smiles, showcasing his skill.                                                                                                                                               |
|          0 |            8 |     7.216 |   8.118 | standard_ad_slot          | visual_form      | face_character    | face_character | False       | Chef's smile and expression are the sole focus here.                          | The chef smiles, showcasing his skill.                                                                                                                                               |
|          0 |            9 |     8.118 |   9.02  | low_ad_need               | object_body      | face_character    | face_character | False       | Chef's smile and expression are the sole focus here.                          | The chef smiles, showcasing his skill.                                                                                                                                               |
|          1 |            0 |     0     |   0.92  | extended_or_integrated_ad | face_character   | face_character    | motion_action  | False       | Rapid eating action is primary; hamburger object secondary.                   | In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                                                                              |
|          1 |            1 |     0.92  |   1.84  | extended_or_integrated_ad | scene_spatial    | face_character    | motion_action  | False       | Rapid eating action is primary; hamburger object secondary.                   | In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                                                                              |
|          1 |            2 |     1.84  |   2.76  | extended_or_integrated_ad | scene_spatial    | motion_action     | motion_action  | False       | Describes eating actions and drinking movements as primary visual content.    | He takes quick bites and washes them down with a drink. In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger.                                      |
|          1 |            3 |     2.76  |   3.68  | low_ad_need               | scene_spatial    | motion_action     | motion_action  | False       | Focuses on eating and drinking actions performed by the character.            | He takes quick bites and washes them down with a drink.                                                                                                                              |
|          1 |            4 |     3.68  |   4.6   | low_ad_need               | scene_spatial    | motion_action     | motion_action  | False       | Emphasizes struggling and coughing actions alongside eating movements.        | As he continues, he appears to struggle slightly, coughing at times. He takes quick bites and washes them down with a drink.                                                         |
|          1 |            5 |     4.6   |   5.52  | low_ad_need               | scene_spatial    | face_character    | motion_action  | False       | Describes visible struggle and coughing as primary observable actions.        | As he continues, he appears to struggle slightly, coughing at times.                                                                                                                 |
|          1 |            6 |     5.52  |   6.44  | low_ad_need               | face_character   | face_character    | motion_action  | False       | Combines character struggle with surrounding people's actions and reactions.  | As he continues, he appears to struggle slightly, coughing at times. Around him, people are laughing and clapping, encouraging him to finish.                                        |
|          1 |            7 |     6.44  |   7.36  | low_ad_need               | face_character   | language_auditory | motion_action  | False       | Describes laughing and clapping actions of surrounding people.                | Around him, people are laughing and clapping, encouraging him to finish.                                                                                                             |
|          1 |            8 |     7.36  |   8.28  | low_ad_need               | face_character   | motion_action     | motion_action  | False       | Emphasizes writing action with ketchup on tray liner as primary visual event. | Around him, people are laughing and clapping, encouraging him to finish. Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                   |
|          1 |            9 |     8.28  |   9.2   | low_ad_need               | face_character   | motion_action     | motion_action  | False       | Focuses on the action of writing with ketchup on a surface.                   | Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                                                                                            |
|          1 |           10 |     9.2   |  10.12  | low_ad_need               | motion_action    | motion_action     | motion_action  | True        | Describes writing action with ketchup as the primary visual content.          | Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.                                                                                                            |

## Verdict

LLM-classified pro AD remains near chance against TRIBE. The failure is not just the small lexicon.

Decision: Drop ROI typing from the headline and keep TRIBE for AD-need timing.

## Caveat

This still inherits the weakest part of the validation: VideoA11y text does not
come with per-sentence timestamps, so snippets are proportionally aligned to
TRIBE windows. A scale-up should either use timestamped AD, human window labels,
or ask the LLM to label clip-level AD priorities separately from per-window timing.
