---
title: "SceneTwin Fusion Smoke Test"
category: research
tags: [SceneTwin, CLIP, TRIBE, fusion, smoke-test, VideoA11y, VATEX]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/fusion_smoke_test_results.csv
  - output/scenetwin_description_gain/fusion_smoke_test_summary.csv
  - wiki/research/scenetwin-description-gain-smoke-test.md
---

# SceneTwin Fusion Smoke Test

## Result

The 2-clip fusion smoke test confirms the next direction: raw TRIBE scores need a visual grounding gate.

CLIP-L14 alone fixes the cross-category failure on the two smoke-test clips. Multiplying CLIP by raw TRIBE richness/recovery does **not** yet prove added value on this tiny sample; the priority is to test whether fused scores improve same-scene quality separation on the full 20-clip set.

## Top Metrics

| metric                |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   tier3_gt_tier2_vatex_long_wins |   tier3_gt_tier2_vatex_long_total |   tier3_gt_tier1_vatex_short_wins |   tier3_gt_tier1_vatex_short_total |   tier3_gt_tier0_cross_wins |   tier3_gt_tier0_cross_total |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:----------------------|---------------:|-------------:|--------------:|------------:|---------------------------------:|----------------------------------:|----------------------------------:|-----------------------------------:|----------------------------:|-----------------------------:|----------------:|-----------------:|-------------------:|-------------------:|
| clip_l14              |       0.9759   |  3.4364e-05  |     0.92582   |  0.00218017 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  2 |                  2 |
| clip_x_av_desc_global |       0.859041 |  0.00628254  |     0.74639   |  0.0145571  |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  1 |                  2 |
| clip_x_av_desc_clip   |       0.935775 |  0.000630791 |     0.870388  |  0.00626203 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  0 |                  2 |
| clip_x_dg_clip        |       0.935775 |  0.000630791 |     0.870388  |  0.00626203 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  0 |                  2 |
| gated_av_desc_clip    |       0.935775 |  0.000630791 |     0.870388  |  0.00626203 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  0 |                  2 |
| gated_dg_clip         |       0.935775 |  0.000630791 |     0.870388  |  0.00626203 |                                2 |                                 2 |                                 2 |                                  2 |                           2 |                            2 |               6 |                6 |                  0 |                  2 |
| av_desc_cos           |       0.048795 |  0.908654    |     0.0771517 |  0.798432   |                                2 |                                 2 |                                 2 |                                  2 |                           1 |                            2 |               5 |                6 |                  0 |                  2 |
| description_gain      |       0.048795 |  0.908654    |     0.0771517 |  0.798432   |                                2 |                                 2 |                                 2 |                                  2 |                           1 |                            2 |               5 |                6 |                  0 |                  2 |
| arp                   |      -0.09759  |  0.818177    |     0         |  1          |                                2 |                                 2 |                                 2 |                                  2 |                           1 |                            2 |               5 |                6 |                  0 |                  2 |
| gated_useful_clip     |       0.543045 |  0.164259    |     0.509525  |  0.128968   |                                1 |                                 2 |                                 1 |                                  2 |                           1 |                            2 |               3 |                6 |                  0 |                  2 |
| clip_x_mvrr_clip      |       0.337919 |  0.412983    |     0.304636  |  0.338664   |                                1 |                                 2 |                                 1 |                                  2 |                           1 |                            2 |               3 |                6 |                  0 |                  2 |
| clip_x_useful_clip    |       0.337919 |  0.412983    |     0.304636  |  0.338664   |                                1 |                                 2 |                                 1 |                                  2 |                           1 |                            2 |               3 |                6 |                  0 |                  2 |

## Mean Scores By Tier

| tier              |   clip_l14 |   av_desc_cos |   description_gain |       mvrr |      arp |   useful_score |   clip_x_av_desc_clip |   clip_x_dg_clip |   clip_x_useful_clip |
|:------------------|-----------:|--------------:|-------------------:|-----------:|---------:|---------------:|----------------------:|-----------------:|---------------------:|
| tier3_va11y       |  0.359163  |      0.685539 |          -0.196809 |  0.0737347 | 0.709578 |      -0.10366  |              0.903202 |         0.903202 |             0.5      |
| tier2_vatex_long  |  0.312764  |      0.547869 |          -0.33448  | -0.0264545 | 0.591374 |      -0.174298 |              0.181608 |         0.181608 |             0.292477 |
| tier1_vatex_short |  0.293312  |      0.513833 |          -0.368515 |  0.0297981 | 0.527721 |      -0.102132 |              0        |         0        |             0.48785  |
| tier0_cross       |  0.0819035 |      0.696912 |          -0.185436 | -0.0105248 | 0.746387 |      -0.197122 |              0        |         0        |             0        |

## Interpretation

- Raw `DescriptionGain`, `MVRR`, and `UsefulScore` are unstable as standalone metrics.
- CLIP-L14 is the necessary correctness gate because it suppresses wrong-content descriptions.
- The plausible SceneTwin v1 metric is not pure counterfactual TRIBE. It is grounded neural scoring:

```text
GroundedScore = normalize(visual_grounding) * normalize(TRIBE_richness_or_recovery)
```

On the two smoke-test clips, the metric to carry into the full run is:

```text
CLIP-L14 baseline + CLIP x av_desc_cos + CLIP x DescriptionGain + CLIP x UsefulScore
```

The full 20-clip run is worth doing only if it reports the ablation honestly:

1. CLIP-L14 alone
2. TRIBE-only metrics
3. grounded TRIBE fusion metrics

The paper/poster claim should be that grounding is the correctness filter and TRIBE is a second-stage accessibility/richness/recovery signal, unless full-run fusion beats CLIP alone.

## Files

- `fusion_smoke_test_results.csv`
- `fusion_smoke_test_summary.csv`
- `scenetwin-fusion-smoke-test.md`
