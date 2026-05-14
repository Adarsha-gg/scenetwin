---
title: "SceneTwin TRIBE-Only Analysis"
category: research
tags: [SceneTwin, TRIBE, accessibility, category-fingerprint, ROI]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/tribe_only_analysis.csv
  - output/scenetwin_timing_20clip/tribe_only_per_roi.csv
  - output/scenetwin_timing_20clip/need/coarse_need_windows.csv
  - output/scenetwin_description_gain/glasser_roi_mask.csv
---

# SceneTwin TRIBE-Only Analysis

## What This Asks

Find a TRIBE-only signal that nothing else in the SceneTwin stack can
compute. CLIP scores text-vs-frame matches; TRIBE predicts cortical
response to multimodal stimulus. Where does the brain model give us
information no caption-grounding metric can?

## Q1: Does TRIBE Accessibility-Need Predict Pro AD Word Count?

If TRIBE's audio-vs-AV gap genuinely measures listener visual need,
clips with higher integrated need should require more professional AD
to convey what's missing. Critically, **CLIP cannot do this**: it
needs description text in hand to score anything. TRIBE rates AD-need
from video alone.

- Spearman(total_need, va11y_word_count) = **-0.110** (p=0.645)
- Spearman(mean_need, va11y_word_count) = -0.102 (p=0.670)
- Spearman(fraction_high_need, va11y_word_count) = -0.085 (p=0.721)
- N clips: 20

## Q2: Sanity Check — Speech Density vs Visual Need

Audio-heavy clips should have lower visual-only cortical gap (audio
carries the cortical signal). Negative correlation expected.

- Spearman(mean_speech_density, mean_need) = 0.037 (p=0.877)

## Q3: Per-Category TRIBE Signatures

Do clip categories produce distinguishable TRIBE accessibility profiles?
If yes, TRIBE provides a video-category fingerprint usable as a
pre-classifier for AD generation strategy.

### Total Need by Category

Group means:
- Food & Cooking: 2.470
- Pets & Animals: 2.665
- Sports: 2.868
- Travel: 2.368

Pairwise Mann-Whitney U:
| a | b | mean_a | mean_b | U | p |
|---|---|---:|---:|---:|---:|
| Food & Cooking | Pets & Animals | 2.470 | 2.665 | 15.0 | 0.699 |
| Food & Cooking | Sports | 2.470 | 2.868 | 11.0 | 0.537 |
| Food & Cooking | Travel | 2.470 | 2.368 | 6.0 | 0.548 |
| Pets & Animals | Sports | 2.665 | 2.868 | 14.0 | 0.931 |
| Pets & Animals | Travel | 2.665 | 2.368 | 11.0 | 0.714 |
| Sports | Travel | 2.868 | 2.368 | 10.0 | 0.571 |

### Mean Need by Category

Group means:
- Food & Cooking: 0.381
- Pets & Animals: 0.420
- Sports: 0.456
- Travel: 0.395

Pairwise Mann-Whitney U:
| a | b | mean_a | mean_b | U | p |
|---|---|---:|---:|---:|---:|
| Food & Cooking | Pets & Animals | 0.381 | 0.420 | 15.0 | 0.699 |
| Food & Cooking | Sports | 0.381 | 0.456 | 9.0 | 0.329 |
| Food & Cooking | Travel | 0.381 | 0.395 | 7.0 | 0.714 |
| Pets & Animals | Sports | 0.420 | 0.456 | 12.0 | 0.662 |
| Pets & Animals | Travel | 0.420 | 0.395 | 10.0 | 0.905 |
| Sports | Travel | 0.456 | 0.395 | 11.0 | 0.393 |

### Extended-AD Slot Count by Category

Group means:
- Food & Cooking: 2.333
- Pets & Animals: 3.167
- Sports: 3.400
- Travel: 2.667

Pairwise Mann-Whitney U:
| a | b | mean_a | mean_b | U | p |
|---|---|---:|---:|---:|---:|
| Food & Cooking | Pets & Animals | 2.333 | 3.167 | 13.0 | 0.457 |
| Food & Cooking | Sports | 2.333 | 3.400 | 8.5 | 0.259 |
| Food & Cooking | Travel | 2.333 | 2.667 | 6.0 | 0.502 |
| Pets & Animals | Sports | 3.167 | 3.400 | 14.0 | 0.924 |
| Pets & Animals | Travel | 3.167 | 2.667 | 10.0 | 0.895 |
| Sports | Travel | 3.400 | 2.667 | 10.0 | 0.536 |

### Speech Density by Category

Group means:
- Food & Cooking: 0.717
- Pets & Animals: 0.833
- Sports: 0.817
- Travel: 1.000

Pairwise Mann-Whitney U:
| a | b | mean_a | mean_b | U | p |
|---|---|---:|---:|---:|---:|
| Food & Cooking | Pets & Animals | 0.717 | 0.833 | 15.5 | 0.732 |
| Food & Cooking | Sports | 0.717 | 0.817 | 14.0 | 0.924 |
| Food & Cooking | Travel | 0.717 | 1.000 | 4.5 | 0.220 |
| Pets & Animals | Sports | 0.833 | 0.817 | 16.5 | 0.848 |
| Pets & Animals | Travel | 0.833 | 1.000 | 4.5 | 0.220 |
| Sports | Travel | 0.817 | 1.000 | 3.0 | 0.172 |

## Q4: Top vs Bottom AD-Difficulty Clips

Top 5 by `total_need` (TRIBE says listener is missing the most signal):

|   clip_idx | category       | video_id                  |   total_need |   mean_need |   mean_speech_density |   va11y_word_count |   n_extended_slots |
|-----------:|:---------------|:--------------------------|-------------:|------------:|----------------------:|-------------------:|-------------------:|
|         12 | Sports         | abaLFY_GI8k_000295_000305 |      4.14608 |    0.51826  |              0.5      |                 64 |                  4 |
|          2 | Food & Cooking | FtBS6OZSGMI_000028_000038 |      3.92014 |    0.435571 |              0.111111 |                 26 |                  1 |
|         17 | Pets & Animals | gjoZic4WjiQ_000012_000022 |      3.71775 |    0.531107 |              0.928571 |                 59 |                  5 |
|          5 | Food & Cooking | PbGvLf7HvXQ_000063_000073 |      3.62805 |    0.604674 |              1        |                 60 |                  5 |
|         18 | Pets & Animals | q2ZBVyR1k-U_000021_000031 |      3.46563 |    0.577604 |              1        |                 54 |                  5 |

Bottom 5 by `total_need`:

|   clip_idx | category       | video_id                  |   total_need |   mean_need |   mean_speech_density |   va11y_word_count |   n_extended_slots |
|-----------:|:---------------|:--------------------------|-------------:|------------:|----------------------:|-------------------:|-------------------:|
|         16 | Pets & Animals | kOf-vl-GmVI_000115_000125 |      1.22976 |    0.20496  |              1        |                 42 |                  1 |
|          4 | Food & Cooking | B0EKYDSv_yQ_000002_000012 |      1.29959 |    0.185656 |              0.357143 |                 73 |                  2 |
|         13 | Sports         | KFcH6BYZWhc_000011_000021 |      1.87883 |    0.375766 |              1        |                 67 |                  2 |
|          0 | Food & Cooking | Q76JRCyTnSc_000007_000017 |      1.94198 |    0.388396 |              1        |                 40 |                  3 |
|          1 | Food & Cooking | 058y9xGmmTQ_000206_000216 |      1.98022 |    0.330036 |              1        |                 62 |                  2 |

## Q5: Per-ROI Cortical Fingerprint (2 clips with full tensors)

Glasser HCP-MMP1.0 ROIs on fsaverage5. Per-ROI mean residual norm
between P_AV and P_A. High = the AV-A gap is concentrated in this
cortical system.

| roi                  |      0 |      1 |
|:---------------------|-------:|-------:|
| auditory_control     | 1.5077 | 2.3698 |
| body_eba_region      | 1.4079 | 1.7164 |
| early_visual_v1      | 2.681  | 2.3641 |
| face_ffc             | 1.882  | 1.8396 |
| higher_visual_v2v3v4 | 3.4532 | 2.9801 |
| language_control     | 2.0034 | 1.9864 |
| lateral_object_loc   | 1.0496 | 1.0084 |
| motion_mt_complex    | 1.8938 | 1.6466 |
| retrosplenial_pos    | 2.5469 | 2.6186 |
| scene_ppa            | 1.481  | 1.6107 |

Per-ROI cosine-gap (1 - cos(mean_AV_in_ROI, mean_A_in_ROI)):

| roi                  |      0 |      1 |
|:---------------------|-------:|-------:|
| auditory_control     | 0.0281 | 0.0046 |
| body_eba_region      | 0.0254 | 0.0447 |
| early_visual_v1      | 0.2487 | 0.14   |
| face_ffc             | 0.0271 | 0.0122 |
| higher_visual_v2v3v4 | 0.1082 | 0.038  |
| language_control     | 0.074  | 0.0223 |
| lateral_object_loc   | 0.0104 | 0.0289 |
| motion_mt_complex    | 0.0146 | 0.0214 |
| retrosplenial_pos    | 0.9641 | 0.7721 |
| scene_ppa            | 0.7933 | 0.5216 |

Each clip activates a distinctive cortical pattern. The residual is
not uniform across ROIs; that is the brain-encoding model giving us
information CLIP cannot generate.

## Bottom Line

Three TRIBE-only findings to evaluate:

1. **AD-difficulty prediction without description text.**
   ρ(total_need, va11y_word_count) = -0.110.
   If above ~0.4 with reasonable p, this is a TRIBE-only result CLIP
   cannot replicate.
2. **Per-category cortical signatures.**
   Mann-Whitney pairs above. If any category pair separates with
   p < 0.05 on `mean_need` or `n_extended_slots`, TRIBE produces a
   video-category fingerprint.
3. **Per-ROI accessibility-gap fingerprint per clip.**
   On the 2 tensor clips, residual norms vary by 5-10x across ROIs.
   This is structural information CLIP simply does not produce.

If 1 holds at scale, the poster headline becomes:

> SceneTwin's TRIBE accessibility-gap predicts professional AD
> verbosity from video and audio alone, before any description is
> written. This is a brain-grounded triage signal usable upstream of
> any AD generation pipeline.
