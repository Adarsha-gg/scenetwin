---
title: "SceneTwin OCR Coverage Test"
category: research
tags: [SceneTwin, OCR, TRIBE, audio-description, text-on-screen]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/ocr_coverage_test_results.csv
  - output/scenetwin_description_gain/ocr_coverage_test_summary.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
---

# SceneTwin OCR Coverage Test

## Question

Can SceneTwin catch a failure mode that CLIP/TRIBE alone can miss: readable text appearing on screen?

## Method

1. Use TRIBE `critical_weight = max(AccessibilityGap, VisualOnlyEvent)` to identify important windows.
2. Run Tesseract OCR on the validation frame for each window.
3. Score each description by coverage of OCR tokens and whether the visible phrase appears in-order.

```text
OCRScore = 0.4 * token coverage + 0.6 * ordered phrase coverage
Need/EventWeightedOCR = weighted average over OCR-positive windows
```

## OCR-Positive Windows

|   clip_idx |   t |   start_s |   end_s |   critical_weight | ocr_tokens   | ocr_raw_text   |
|-----------:|----:|----------:|--------:|------------------:|:-------------|:---------------|
|          0 |   3 |     2.706 |   3.608 |          0.485675 | lag          | lags           |
|          1 |   9 |     8.28  |   9.2   |          0.338044 | burger eat   | BURGERS EATING |

## Results

|   clip_idx | tier              |   gt |   ocr_windows |   weighted_ocr_score |   weighted_token_coverage |   weighted_phrase_coverage |
|-----------:|:------------------|-----:|--------------:|---------------------:|--------------------------:|---------------------------:|
|          0 | tier3_va11y       |    3 |             0 |                nan   |                       nan |                        nan |
|          0 | tier2_vatex_long  |    2 |             0 |                nan   |                       nan |                        nan |
|          0 | tier1_vatex_short |    1 |             0 |                nan   |                       nan |                        nan |
|          0 | tier0_cross       |    0 |             0 |                nan   |                       nan |                        nan |
|          1 | tier3_va11y       |    3 |             1 |                  1   |                         1 |                          1 |
|          1 | tier2_vatex_long  |    2 |             1 |                  0.4 |                         1 |                          0 |
|          1 | tier1_vatex_short |    1 |             1 |                  0.4 |                         1 |                          0 |
|          1 | tier0_cross       |    0 |             1 |                  0   |                         0 |                          0 |

## Summary

| metric                   |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   tier3_gt_tier2_vatex_long_wins |   tier3_gt_tier2_vatex_long_total |   tier3_gt_tier1_vatex_short_wins |   tier3_gt_tier1_vatex_short_total |   tier3_gt_tier0_cross_wins |   tier3_gt_tier0_cross_total |   pairwise_wins |   pairwise_total |
|:-------------------------|---------------:|-------------:|--------------:|------------:|---------------------------------:|----------------------------------:|----------------------------------:|-----------------------------------:|----------------------------:|-----------------------------:|----------------:|-----------------:|
| weighted_ocr_score       |       0.948683 |    0.0513167 |      0.912871 |   0.0709515 |                                1 |                                 1 |                                 1 |                                  1 |                           1 |                            1 |               3 |                3 |
| weighted_phrase_coverage |       0.774597 |    0.225403  |      0.707107 |   0.179712  |                                1 |                                 1 |                                 1 |                                  1 |                           1 |                            1 |               3 |                3 |
| weighted_token_coverage  |       0.774597 |    0.225403  |      0.707107 |   0.179712  |                                0 |                                 1 |                                 0 |                                  1 |                           1 |                            1 |               1 |                3 |

## Verdict

This is useful as a specialized content layer, not as a universal description metric. It detects the clip 01 title-card requirement that the neural need curve underweighted: the best description explicitly contains `BURGER EATING`, while shorter same-scene captions only mention eating/burgers generally.

Final stack after this test:

- TRIBE AccessibilityGap: when the viewer needs visual information.
- TRIBE VisualOnlyEvent: secondary trigger for visual transitions/title cards.
- Need-weighted CLIP/PAC-S/SigLIP: whether the description matches important frames.
- OCR coverage: whether visible text is read or paraphrased.
