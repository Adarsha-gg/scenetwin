---
title: "SceneTwin ROI Content Typing"
category: research
tags: [SceneTwin, TRIBE, ROI, content-typing, audio-description]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/roi_content_typing_windows.csv
  - output/scenetwin_description_gain/roi_content_typing_descriptions.csv
  - output/scenetwin_description_gain/roi_gap_curve.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
---

# SceneTwin ROI Content Typing

## Claim

This is the TRIBE-specific layer: convert audio-vs-audiovisual cortical gaps into an AD content-type profile. CLIP/OCR can check whether text matches frames; TRIBE can suggest what kind of information is missing.

## Content Types

```text
motion_action
scene_spatial
face_character
object_body
visual_form
language_auditory
```

These are currently based on Destrieux anatomical proxy ROIs, not functional localizer ROIs.

## Top Typed Windows

|   clip_idx |   t |   start_s |   end_s |   critical_weight |   need_score |   speech_density | dominant_type   |   dominant_score | second_type       |   second_score |   type_margin | recommendation            | ad_template                                                                                     |
|-----------:|----:|----------:|--------:|------------------:|-------------:|-----------------:|:----------------|-----------------:|:------------------|---------------:|--------------:|:--------------------------|:------------------------------------------------------------------------------------------------|
|          0 |   9 |     8.118 |   9.02  |          1        |     0.117137 |         0        | object_body     |         0.416301 | motion_action     |       0.394092 |     0.0222088 | low_ad_need               | Describe the important object/body details first: what object matters and how it is being used. |
|          0 |   8 |     7.216 |   8.118 |          0.780558 |     0.780558 |         0        | visual_form     |         0.312044 | scene_spatial     |       0.264155 |     0.0478892 | standard_ad_slot          | Describe salient visual form first: shape, color, framing, or visual state.                     |
|          0 |   0 |     0     |   0.902 |          0.649763 |     0.649763 |         0        | face_character  |         0.445953 | motion_action     |       0.234411 |     0.211542  | standard_ad_slot          | Describe visible people/characters first: identity cues, expression, attention, interaction.    |
|          0 |   6 |     5.412 |   6.314 |          0.606842 |     0.606842 |         0        | scene_spatial   |         0.275024 | visual_form       |       0.227493 |     0.0475317 | standard_ad_slot          | Describe the place/layout first: where this is and how objects/people are arranged.             |
|          0 |   7 |     6.314 |   7.216 |          0.561327 |     0.561327 |         0        | scene_spatial   |         0.309358 | visual_form       |       0.26647  |     0.0428876 | standard_ad_slot          | Describe the place/layout first: where this is and how objects/people are arranged.             |
|          1 |   1 |     0.92  |   1.84  |          1        |     1        |         0.625    | scene_spatial   |         0.374613 | visual_form       |       0.268425 |     0.106188  | extended_or_integrated_ad | Describe the place/layout first: where this is and how objects/people are arranged.             |
|          1 |  10 |     9.2   |  10.12  |          1        |     0.140605 |         0.781522 | motion_action   |         1        | language_auditory |       0.480222 |     0.519778  | low_ad_need               | Describe the action first: who moves, what changes, and the result.                             |
|          1 |   0 |     0     |   0.92  |          0.705327 |     0.705327 |         0.595652 | face_character  |         0.28418  | object_body       |       0.258345 |     0.0258345 | extended_or_integrated_ad | Describe visible people/characters first: identity cues, expression, attention, interaction.    |
|          1 |   2 |     1.84  |   2.76  |          0.643048 |     0.643048 |         0.873913 | scene_spatial   |         0.390407 | visual_form       |       0.25802  |     0.132387  | extended_or_integrated_ad | Describe the place/layout first: where this is and how objects/people are arranged.             |
|          1 |   3 |     2.76  |   3.68  |          0.403887 |     0.403887 |         0.826087 | scene_spatial   |         0.427976 | visual_form       |       0.24754  |     0.180436  | low_ad_need               | Describe the place/layout first: where this is and how objects/people are arranged.             |

## Description Alignment

|   clip_idx | tier              |   gt | target_dominant_type   | text_dominant_type   |   profile_alignment |   weighted_keyword_coverage |   specificity_score |   text_motion_action |   text_scene_spatial |   text_face_character |   text_object_body |   text_language_auditory |
|-----------:|:------------------|-----:|:-----------------------|:---------------------|--------------------:|----------------------------:|--------------------:|---------------------:|---------------------:|----------------------:|-------------------:|-------------------------:|
|          0 | tier3_va11y       |    3 | object_body            | object_body          |            0.983101 |                    6.84     |            0.425    |             0.181818 |            0.136364  |             0.212121  |          0.242424  |                0.0909091 |
|          0 | tier2_vatex_long  |    2 | object_body            | object_body          |            0.872195 |                    4.51226  |            0.44     |             0.292683 |            0.0731707 |             0.121951  |          0.365854  |                0.146341  |
|          0 | tier1_vatex_short |    1 | object_body            | motion_action        |            0.840886 |                    1.96973  |            0.545455 |             0.333333 |            0.166667  |             0.333333  |          0.166667  |                0         |
|          0 | tier0_cross       |    0 | object_body            | motion_action        |            0.660359 |                    3.72888  |            0.314286 |             0.414634 |            0.292683  |             0         |          0.0731707 |                0         |
|          1 | tier3_va11y       |    3 | motion_action          | face_character       |            0.943725 |                   11.5395   |            0.451613 |             0.214286 |            0.160714  |             0.25      |          0.160714  |                0.133929  |
|          1 | tier2_vatex_long  |    2 | motion_action          | object_body          |            0.836507 |                    3.71954  |            0.421053 |             0.25     |            0.166667  |             0.0833333 |          0.333333  |                0.166667  |
|          1 | tier1_vatex_short |    1 | motion_action          | motion_action        |            0.687676 |                    0.741617 |            0.153846 |             0.5      |            0         |             0.5       |          0         |                0         |
|          1 | tier0_cross       |    0 | motion_action          | motion_action        |            0.855655 |                    4.97404  |            0.314286 |             0.414634 |            0.292683  |             0         |          0.0731707 |                0         |

## Mean Alignment By Tier

| tier              |   profile_alignment |   weighted_keyword_coverage |   specificity_score |
|:------------------|--------------------:|----------------------------:|--------------------:|
| tier3_va11y       |            0.963413 |                     9.18975 |            0.438306 |
| tier2_vatex_long  |            0.854351 |                     4.1159  |            0.430526 |
| tier1_vatex_short |            0.764281 |                     1.35567 |            0.34965  |
| tier0_cross       |            0.758007 |                     4.35146 |            0.314286 |

## Verdict

This is the right framing for TRIBE, but the current proxy ROI/lexicon version is a prototype.

What works:

- Produces typed AD windows from TRIBE ROI gaps.
- Gives a prescriptive output: action AD vs scene/layout AD vs character/object AD.
- Keeps TRIBE out of direct text correctness scoring.

What is still weak:

- Destrieux ROIs are coarse anatomical proxies.
- The text-side validation is a lightweight lexicon check, not a real semantic parser.
- On 2 clips, content typing is plausible but not yet enough for a statistical claim.

Next version should replace Destrieux proxies with functional ROI masks and replace the lexicon with a VLM/LLM content classifier over AD text.
