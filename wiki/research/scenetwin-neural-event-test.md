---
title: "SceneTwin Neural Event Test"
category: research
tags: [SceneTwin, TRIBE, event-boundaries, accessibility-gap, validation]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_event_test_results.csv
  - output/scenetwin_description_gain/neural_event_test_summary.csv
  - output/scenetwin_event_validation/
---

# SceneTwin Neural Event Test

## Metric

TRIBE gives a time series of predicted cortical states. This test looks for visual-only neural events:

```text
AVShift(t) = 1 - cos(P_AV[t-1], P_AV[t])
AudioShift(t) = 1 - cos(P_A[t-1], P_A[t])
VisualOnlyEvent(t) = max(AVShift(t) - AudioShift(t), 0)
VisualEventNeed(t) = normalized(VisualOnlyEvent(t)) * AccessibilityGap(t)
```

This is different from frame difference or optical flow. It asks whether the predicted brain state changes more when vision is present than when only audio is present.

## Summary

|   clip_idx |   mean_visual_only_delta |   max_visual_event_score | top_visual_only_events                                                                                                      | top_av_events                                                                                                            |
|-----------:|-------------------------:|-------------------------:|:----------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------|
|          0 |                0.0248994 |                        1 | t8->t9 8.1-9.0s (event=1.00, need=0.12); t5->t6 5.4-6.3s (event=0.14, need=0.61); t4->t5 4.5-5.4s (event=0.10, need=0.32)   | t8->t9 8.1-9.0s (AV=1.00, audio=0.346); t0->t1 0.9-1.8s (AV=0.35, audio=0.188); t1->t2 1.8-2.7s (AV=0.30, audio=0.204)   |
|          1 |                0.0202418 |                        1 | t9->t10 9.2-10.1s (event=1.00, need=0.14); t2->t3 2.8-3.7s (event=0.08, need=0.40); t4->t5 4.6-5.5s (event=0.11, need=0.17) | t9->t10 9.2-10.1s (AV=1.00, audio=0.306); t0->t1 0.9-1.8s (AV=0.31, audio=0.249); t4->t5 4.6-5.5s (AV=0.11, audio=0.033) |

## Validation Sheets

|   clip_idx | validation_sheet                                               |
|-----------:|:---------------------------------------------------------------|
|          0 | output/scenetwin_event_validation/clip_00_event_validation.jpg |
|          1 | output/scenetwin_event_validation/clip_01_event_validation.jpg |

## Top Visual-Only Events

|   clip_idx |   t |   start_s |   end_s |   av_shift |   audio_shift |   visual_event_score |   need_score |   visual_event_need |   speech_density | recommendation   |
|-----------:|----:|----------:|--------:|-----------:|--------------:|---------------------:|-------------:|--------------------:|-----------------:|:-----------------|
|          0 |   9 |     8.118 |   9.02  |  0.490549  |    0.346478   |           1          |    0.117137  |          0.117137   |         0        | low_ad_need      |
|          0 |   6 |     5.412 |   6.314 |  0.0589853 |    0.0393899  |           0.136012   |    0.606842  |          0.0825378  |         0        | standard_ad_slot |
|          0 |   5 |     4.51  |   5.412 |  0.0741059 |    0.0595972  |           0.100705   |    0.32164   |          0.0323908  |         0        | low_ad_need      |
|          0 |   3 |     2.706 |   3.608 |  0.13589   |    0.0659184  |           0.485675   |    0.048162  |          0.0233911  |         0        | low_ad_need      |
|          0 |   4 |     3.608 |   4.51  |  0.0427291 |    0.0418817  |           0.00588224 |    0.196637  |          0.00115667 |         0        | low_ad_need      |
|          1 |  10 |     9.2   |  10.12  |  0.477015  |    0.305949   |           1          |    0.140605  |          0.140605   |         0.781522 | low_ad_need      |
|          1 |   3 |     2.76  |   3.68  |  0.0184167 |    0.0049116  |           0.0789468  |    0.403887  |          0.0318856  |         0.826087 | low_ad_need      |
|          1 |   5 |     4.6   |   5.52  |  0.0515746 |    0.0332857  |           0.106912   |    0.170692  |          0.0182489  |         0.672826 | low_ad_need      |
|          1 |   4 |     3.68  |   4.6   |  0.0218309 |    0.00973511 |           0.0707082  |    0.202973  |          0.0143519  |         0.847826 | low_ad_need      |
|          1 |   7 |     6.44  |   7.36  |  0.0329311 |    0.0265758  |           0.0371511  |    0.0715173 |          0.00265695 |         0.816304 | low_ad_need      |

## Verdict

This is worth keeping as a second TRIBE-native signal.

- The accessibility-gap curve answers **where visual information is missing from audio**.
- The neural-event curve answers **where the visual scene changes brain state more than the audio does**.

On these two clips, the metric is plausible but not independently validated. It should be tested on all 20 clips with visual sheets and human labels for whether each top event truly needs AD.

Known failure risk: symbolic visual content such as signs/title cards may still need OCR/VLM support.

## Manual Visual Inspection

### clip 00

The event metric is partly useful but noisier than the accessibility-gap curve.

- `t5->t6` aligns with the chef turning/preparing the key visual action. This is useful and overlaps a high need score.
- `t8->t9` is the largest visual-only transition, but it looks like the camera moving/ending after the wall-result shot. It is visually different, but not obviously the highest AD priority. This shows event score alone can over-rank abrupt camera transitions.
- The accessibility-gap curve was better for this clip because it highlighted silent windows where description can naturally fit.

### clip 01

The event metric catches something the need curve underweighted.

- `t9->t10` strongly flags the Burger King sign/title-card transition. The need curve treated this as low/moderate, but a human describer might care because on-screen text is semantically important.
- This suggests event detection is valuable as an **inspection trigger**: high event + low need may indicate cuts, title cards, signs, or visual text that the gap curve alone misses.
- The eating-action windows are still better handled by the accessibility-gap/speech-density metric because they involve ongoing visual action under dialogue.

## Tested Metric Verdict

| Metric | 2-clip result | Keep? | Role |
|---|---|---|---|
| Accessibility gap `distance(P_AV, P_A)` | Good on clip 00, useful on clip 01 | Yes | Main AD need/timing signal |
| Speech-weighted opportunity/extended need | Good distinction between silent action and action under speech | Yes | Decide standard vs extended/integrated AD |
| Visual-only neural event delta | Catches some events and title-card transition, but noisy alone | Yes | Secondary inspection trigger |
| Raw description scoring with TRIBE | Failed wrong-content controls | No | Do not use standalone |
| MVRR / UsefulScore on description tensors | Failed 2-clip smoke test | No | Do not use standalone |
| OCR / critical visual text coverage | Not run locally; no OCR installed | Needed | Add OCR/VLM layer |

Conclusion: the best two-clip metric stack is:

```text
ADNeed(t) = AccessibilityGap(t)
ADMode(t) = speech_density(t) -> standard vs extended/integrated
EventTrigger(t) = VisualOnlyEvent(t)
ContentLayer(t) = OCR/VLM/CLIP/SigLIP on flagged windows
```
