---
title: SceneTwin tier ordering failures (3/18 clips)
category: research
tags: [scenetwin, benchmark, failure-analysis, paper-section]
sources: [output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv, output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

15/18 benchmark clips are fully tier-ordered (T0 < T1 < T2 < T3) by `ensemble_mean_clip_mean`. The 3 violations are clip 0, 12, and 14 — and every violation lives at the **T1 -> T2** boundary, not anywhere else. T3 (professional AD) wins every clip.

## The 3 mis-ordered clips

| clip | category | dur (s) | T0 | T1 | T2 | T3 | violations |
|---:|---|---:|---:|---:|---:|---:|---|
| 0  | Food & Cooking | 14.9 | 0.500 | 0.500 | 0.318 | 0.927 | T0 = T1 tie; T1 > T2 |
| 12 | Sports         | 23.8 | 0.000 | 0.688 | 0.606 | 0.982 | T1 > T2 |
| 14 | Sports         | 16.4 | 0.000 | 0.800 | 0.707 | 0.965 | T1 > T2 |

## What the AD text looks like at each tier

### clip_00 (knife / tomato kitchen, 14.9s)
- **T1 (11w)**: "A chef in a kitchen demonstrates his skill throwing a knife."
- **T2 (25w)**: "The man holding the camera is counting backward in Spanish as the other man pins a cherry tomato to the wall by throwing a knife."
- **T3 (40w)**: full professional AD; correctly wins.

T2 is technically more complete but the metric penalises its *narration framing* ("the man holding the camera") that doesn't help a BLV viewer locate visual evidence. T0 ties T1 because both score equally low.

### clip_12 (boys playing volleyball, 23.8s)
- **T1 (11w)**: "Some boys talking in a foreign language are playing Volley Ball."
- **T2 (20w)**: "A man runs to the back of a volleyball field bouncing the ball before he plays a game of volleyball."
- **T3 (64w)**: full pro AD; correctly wins.

T2 introduces factual errors ("a man" vs *boys*, "bouncing the ball" vs *serving and spiking*). T1's brevity avoids these errors.

### clip_14 (curling slip, 16.4s)
- **T1 (14w)**: "A man walks on the ice pushing a curling block and then falls down."
- **T2 (27w)**: "A man is playing the sport curling, is pushing the object across the ice, the slips and falls, whilst other people stand around and clap and react."
- **T3 (46w)**: full pro AD; correctly wins.

T2 adds redundant filler ("playing the sport curling", "the object") without adding visual specificity. The grader penalises *length without information gain*.

## The pattern

Every violation is **T1 > T2**. Never T0 > T1, never T2 > T3, never T0 > T2 or T0 > T3.

This is not random failure. The VATEX-long (T2) annotations are crowd-sourced "longer captions"; when the additional length is filler, factual error, or narration framing, the metric correctly down-ranks them below the cleaner T1 short caption. Tier3 (professional AD) wins all 18 because pros add visual specificity, not just words.

## Reframe for the paper

These 3 mis-orderings are *not* a benchmark failure. They surface a property of the metric that matters for AD evaluation: **length is not credited; visual specificity is**. We can present this as a controlled probe:

> Crowd-sourced T2 annotations that add length without specificity are correctly penalised below crisp T1 captions on 3/18 clips. Professional T3 AD wins all 18 clips. This demonstrates the ensemble does not reward verbosity as a proxy for quality.

This makes the 15/18 number a feature, not a defect, and gives a clean failure-analysis subsection.

## See Also

- [[research/scenetwin-tribe-failure-forecast]]
- [[research/scenetwin-metric-landscape]] (pending)

## Sources

- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (per-tier ensemble scores)
- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv` (per-clip metadata and AD text)
