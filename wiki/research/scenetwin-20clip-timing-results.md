---
title: "SceneTwin 20-Clip Timing Stack Results"
category: research
tags: [SceneTwin, TRIBE, CLIP, OCR, VideoA11y, VATEX, timing]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/aggregate_results.csv
  - output/scenetwin_timing_20clip/aggregate_nulls.csv
  - output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv
  - output/scenetwin_timing_20clip/clip_scores/window_clip_scores.csv
  - output/scenetwin_timing_20clip/need/coarse_need_windows.csv
  - output/scenetwin_timing_20clip/need/neural_description_need_curve.csv
  - output/scenetwin_timing_20clip/ocr/ocr_coverage_results.csv
---

# SceneTwin 20-Clip Timing Stack Results

## What Ran

The 20-clip Colab ran the surviving SceneTwin stack only:

1. TRIBE `P_AV` for audiovisual video.
2. TRIBE `P_A` for audio-only soundtrack.
3. `AccessibilityGap(t) = distance(P_AV[t], P_A[t])`.
4. Coarse 3s windows.
5. CLIP-L14 grounding over sampled validation frames.
6. OCR coverage over validation frames.
7. Aggregate rank metrics and within-clip permutation nulls.

Dead branches were intentionally not rerun: Description Gain, MVRR/UsefulScore,
ROI content typing, trajectory metrics, and closed-loop TRIBE-in-loop AD.

## Coverage

- TRIBE need curves: 20 clips, 239 TR rows, 126 coarse windows.
- Frame validation: 189 sampled validation frames.
- CLIP tier-ranking analysis: 18 clips with all four description tiers, 72 clip-tier rows.
- OCR-positive analysis: 2 clips, 8 OCR rows.

The CLIP aggregate uses 18 clips because two clip rows did not produce complete
four-tier grounding rows in the Colab output. The TRIBE need-curve stage did run
across 20 clips.

## Main Result

| metric | Spearman rho | Kendall tau | pairwise tier3 wins | full-order clips | null p |
|---|---:|---:|---:|---:|---:|
| need_weighted_clip | 0.7328 | 0.5877 | 48/54 | 11/18 | <0.0005 |
| critical_weighted_clip | 0.7274 | 0.5841 | 48/54 | 11/18 | <0.0005 |
| clip_mean | 0.7251 | 0.5805 | 48/54 | 11/18 | <0.0005 |
| clip_top3 | 0.7346 | 0.5877 | 48/54 | 10/18 | <0.0005 |

Mean CLIP score by tier:

| tier | need_weighted_clip | critical_weighted_clip | clip_mean | clip_top3 |
|---|---:|---:|---:|---:|
| tier3_va11y | 0.2664 | 0.2672 | 0.2655 | 0.2723 |
| tier2_vatex_long | 0.2476 | 0.2477 | 0.2479 | 0.2523 |
| tier1_vatex_short | 0.2411 | 0.2406 | 0.2414 | 0.2460 |
| tier0_cross | 0.1022 | 0.1016 | 0.1015 | 0.1062 |

## Interpretation

The scale-up validates the grounding story: CLIP-L14 over sampled video windows
robustly ranks professional VideoA11y descriptions above shorter VATEX captions
and cross-category controls. The rank signal is strong and survives a within-clip
permutation null.

The scale-up does **not** validate a strong claim that TRIBE need-weighting
substantially improves aggregate CLIP ranking. Need-weighted CLIP, critical-window
CLIP, plain window-mean CLIP, and top-3-window CLIP all land around `rho=0.73`.
Need weighting is still useful as an accessibility-motivated windowing and
prioritization layer, but it should not be sold as a large aggregate lift over
plain CLIP on this dataset.

OCR is inconclusive at this scale. Only two clips produced OCR-positive windows,
and OCR metrics did not beat the permutation null (`p=0.357`).

## Updated Claim

Old claim after the 2-clip smoke test:

> TRIBE need-weighting improves description ranking.

Updated claim after the 20-clip scale-up:

> SceneTwin scales as a practical AD audit stack: TRIBE computes an
> audio-vs-audiovisual accessibility-gap curve for timing and window
> prioritization, while CLIP grounding robustly scores content quality inside
> sampled video windows. On 18 complete clips, CLIP-based metrics reach
> Spearman `rho≈0.73` with permutation-null `p<0.0005`; TRIBE weighting provides
> the accessibility framing but not a large aggregate ranking advantage over
> plain CLIP.

## What Changed

- The project is still shippable, but the headline is less aggressive.
- TRIBE remains the differentiator for **when to inspect/describe**, not for
  **what content is correct** and not for proving a big CLIP-score boost.
- The 20-clip result replaces the earlier n=2 claim in abstracts/reports.
- The strongest poster number is now the 18-clip CLIP ranking result, not the
  earlier n=2 need-weighted result.

## Next Step

Ask an independent reviewer to evaluate the conclusion:

1. Does the 20-clip result justify "brain-model-guided timing" as a contribution?
2. Is TRIBE's role still meaningful if plain CLIP ranking is almost as strong?
3. Should the poster headline say "TRIBE-guided timing + CLIP grounding" or
   simply "video-window grounding for AD evaluation with neural prioritization"?
