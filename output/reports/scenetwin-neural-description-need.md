---
title: "SceneTwin Neural Description Need"
category: research
tags: [SceneTwin, TRIBE, audio-description, timing, accessibility-gap]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_description_need_summary.csv
  - output/scenetwin_description_gain/neural_description_need_curve.svg
  - https://uwm.edu/digital-accessibility/documentation-guides/video-audio/audio-descriptions/
  - https://accessibility.huit.harvard.edu/audio-description
  - https://www.washington.edu/accesstech/checklist/description/
  - https://pubmed.ncbi.nlm.nih.gov/40918301/
  - https://www.pearson.com/accessibility-guidelines/perceivable-principle/audio-description-prerecorded.html
---

# SceneTwin Neural Description Need

## Pivot

TRIBE should not be used as the primary text-correctness judge. The smoke tests show that rich wrong descriptions can still look neurally plausible.

The stronger use of TRIBE is upstream:

```text
AccessibilityGap(t) = distance(P_AV[t], P_A[t])
```

This asks where the full audiovisual scene contains predicted neural signal that the soundtrack alone does not carry. That is exactly the audio-description problem: describe important visual information not available through audio alone.

This lines up with accessibility guidance from UWM, Harvard, and the University of Washington: AD is for key visual content that is not accessible or obvious from audio alone. It also matches the "Describe Now" user-study direction: BLV users benefit from control over timing and detail, not just one fixed description track.

## Metrics

For each time window:

- `residual_norm`: normalized magnitude of `P_AV[t] - P_A[t]`
- `cosine_gap`: `1 - cos(P_AV[t], P_A[t])`
- `need_score`: combined normalized residual/cosine gap
- `speech_density`: how much original speech occupies the window
- `standard_slot_score`: high gap with low speech
- `extended_need_score`: high gap with high speech

## Clip Summary

|   clip_idx |   mean_need_score |   max_need_score |   mean_speech_density | top_need_windows                                                                                                                   | top_standard_slots                                | top_extended_needs                                |
|-----------:|------------------:|-----------------:|----------------------:|:-----------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------|:--------------------------------------------------|
|          0 |          0.388279 |         0.780558 |              0.106874 | 7.2-8.1s (0.78, standard_ad_slot); 0.0-0.9s (0.65, standard_ad_slot); 5.4-6.3s (0.61, standard_ad_slot)                            | 7.2-8.1s (0.78); 0.0-0.9s (0.65); 5.4-6.3s (0.61) | 0.9-1.8s (0.24); 1.8-2.7s (0.08); 0.0-0.9s (0.00) |
|          1 |          0.347116 |         1        |              0.63834  | 0.9-1.8s (1.00, extended_or_integrated_ad); 0.0-0.9s (0.71, extended_or_integrated_ad); 1.8-2.8s (0.64, extended_or_integrated_ad) | 0.9-1.8s (0.38); 0.0-0.9s (0.29); 8.3-9.2s (0.29) | 0.9-1.8s (0.62); 1.8-2.8s (0.56); 0.0-0.9s (0.42) |

## Highest-Need Windows

|   clip_idx |   start_s |   end_s |   need_score |   speech_density |   standard_slot_score |   extended_need_score | recommendation            |
|-----------:|----------:|--------:|-------------:|-----------------:|----------------------:|----------------------:|:--------------------------|
|          0 |     7.216 |   8.118 |     0.780558 |         0        |             0.780558  |             0         | standard_ad_slot          |
|          0 |     0     |   0.902 |     0.649763 |         0        |             0.649763  |             0         | standard_ad_slot          |
|          0 |     5.412 |   6.314 |     0.606842 |         0        |             0.606842  |             0         | standard_ad_slot          |
|          0 |     6.314 |   7.216 |     0.561327 |         0        |             0.561327  |             0         | standard_ad_slot          |
|          0 |     4.51  |   5.412 |     0.32164  |         0        |             0.32164   |             0         | low_ad_need               |
|          1 |     0.92  |   1.84  |     1        |         0.625    |             0.375     |             0.625     | extended_or_integrated_ad |
|          1 |     0     |   0.92  |     0.705327 |         0.595652 |             0.285198  |             0.42013   | extended_or_integrated_ad |
|          1 |     1.84  |   2.76  |     0.643048 |         0.873913 |             0.08108   |             0.561968  | extended_or_integrated_ad |
|          1 |     2.76  |   3.68  |     0.403887 |         0.826087 |             0.0702412 |             0.333646  | low_ad_need               |
|          1 |     8.28  |   9.2   |     0.338044 |         0.156522 |             0.285133  |             0.0529112 | low_ad_need               |

## Why This Is Better

This avoids the failure mode from raw Description Gain:

- It does not ask TRIBE to decide whether text is correct.
- It uses TRIBE only for video/audio counterfactuals from the same source clip.
- It creates an actionable product: when to describe, how urgent the need is, and whether standard or extended AD is required.

The content layer should be handled separately with CLIP/SigLIP/PAC-S and a VLM captioner.

## Product Direction

SceneTwin becomes an **AD need planner**:

1. Use TRIBE to compute the accessibility gap curve.
2. Use speech density to find available narration windows.
3. Use a VLM to propose descriptions for high-need moments.
4. Use CLIP/SigLIP/PAC-S to ground the proposed descriptions.
5. Use user profile settings to choose concise vs detailed output.

This is more defensible than raw neural text scoring and much closer to a useful accessibility tool.
