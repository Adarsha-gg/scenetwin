---
title: "SceneTwin Description Gain — Real VideoA11y/VATEX Clips"
category: research
tags: [SceneTwin, TRIBE, Description-Gain, VideoA11y, VATEX]
created: 2026-05-02
updated: 2026-05-02
---

# SceneTwin Description Gain — Real VideoA11y/VATEX Clips

## Metric

`DescriptionGain = cos(P_AV, P_D) - cos(P_AV, P_A)`

- `P_AV`: TRIBE prediction for original audiovisual video
- `P_A`: TRIBE prediction for audio-only soundtrack
- `P_D`: TRIBE prediction for candidate text description

## Main Result

| Metric | Value |
|---|---:|
| Spearman rho | 0.0488 |
| Spearman p | 0.9087 |
| Kendall tau | 0.0772 |
| Kendall p | 0.7984 |

## Mean Scores by Tier

| tier              |   description_gain |   av_desc_cos |   av_audio_cos |   desc_words |
|:------------------|-------------------:|--------------:|---------------:|-------------:|
| tier3_va11y       |          -0.196809 |      0.685539 |       0.882348 |           51 |
| tier2_vatex_long  |          -0.33448  |      0.547869 |       0.882348 |           22 |
| tier1_vatex_short |          -0.368515 |      0.513833 |       0.882348 |           12 |
| tier0_cross       |          -0.185436 |      0.696912 |       0.882348 |           35 |

## Pairwise Accuracy

| comparison                      |   wins |   total |   accuracy |
|:--------------------------------|-------:|--------:|-----------:|
| tier3_va11y > tier2_vatex_long  |      2 |       2 |        1   |
| tier3_va11y > tier1_vatex_short |      2 |       2 |        1   |
| tier3_va11y > tier0_cross       |      1 |       2 |        0.5 |

## Files

- `description_gain_results.csv`
- `description_gain_partial.csv`
- `description_gain_tiers.png`
- `preds/*.npy`
