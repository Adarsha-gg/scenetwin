# Label audit — is tier3 always the best AD?

Clips with **any ADQA inversion** vs pro AD: **2/18**

## Inversions by metric (pro AD not top)

|   clip_idx |   pro_score |   tier2_score |   tier1_score |   tier0_score | inversions                                                 |   n_inversions |
|-----------:|------------:|--------------:|--------------:|--------------:|:-----------------------------------------------------------|---------------:|
|          0 |         0.2 |           0.1 |           0.1 |           0.2 | tier0_cross>tier1_vatex_short;tier0_cross>tier2_vatex_long |              2 |
|         12 |         0.8 |           0.2 |           0.3 |           0   | tier1_vatex_short>tier2_vatex_long                         |              1 |
|          1 |         0.9 |           0.5 |           0.1 |           0   | clean                                                      |              0 |
|         18 |         0.5 |           0.3 |           0.1 |           0.1 | clean                                                      |              0 |
|         17 |         0.5 |           0.4 |           0.4 |           0.4 | clean                                                      |              0 |
|         16 |         0.3 |           0.2 |           0   |           0   | clean                                                      |              0 |
|         15 |         0.5 |           0.5 |           0.3 |           0   | clean                                                      |              0 |
|         14 |         1   |           0.6 |           0.6 |           0   | clean                                                      |              0 |
|         13 |         0.9 |           0.7 |           0.4 |           0   | clean                                                      |              0 |
|         11 |         0.8 |           0.6 |           0.3 |           0   | clean                                                      |              0 |
|          9 |         0.9 |           0.7 |           0.4 |           0   | clean                                                      |              0 |
|          8 |         0.8 |           0.4 |           0.1 |           0   | clean                                                      |              0 |
|          7 |         0.4 |           0.1 |           0.1 |           0   | clean                                                      |              0 |
|          6 |         0.4 |           0.2 |           0.1 |           0   | clean                                                      |              0 |
|          5 |         0.8 |           0.8 |           0.4 |           0   | clean                                                      |              0 |
|          4 |         0.8 |           0.4 |           0.4 |           0   | clean                                                      |              0 |
|          3 |         0.5 |           0.3 |           0.1 |           0   | clean                                                      |              0 |
|         19 |         0.7 |           0.6 |           0.2 |           0   | clean                                                      |              0 |

## Metric correlation with original tier GT (0=cross … 3=pro)

| metric                    |   spearman_rho |   spearman_p |   pairwise_wins |   pairwise_total |   full_order |   n_clips |
|:--------------------------|---------------:|-------------:|----------------:|-----------------:|-------------:|----------:|
| adqa_v2_score             |       0.802928 |  2.19288e-17 |              51 |               54 |            0 |        18 |
| clip_top3                 |       0.734623 |  2.06146e-13 |              48 |               54 |            0 |        18 |
| clip_mean                 |       0.725059 |  5.93888e-13 |              48 |               54 |            0 |        18 |
| ensemble_mean_clip_top3   |       0.928491 |  7.84041e-32 |              54 |               54 |            0 |        18 |
| adqa_critical_mean        |       0.781183 |  5.74028e-16 |              48 |               54 |            0 |        18 |
| clip_top3_vs_adqa_rank_gt |       0.717886 |  1.27627e-12 |              48 |               54 |            0 |        18 |

## Findings

- clip_00: tier0_cross>tier1_vatex_short;tier0_cross>tier2_vatex_long (pro=0.20, tier2=0.10)
- clip_12: tier1_vatex_short>tier2_vatex_long (pro=0.80, tier2=0.20)

## Critical-only ADQA inversions: 5/18

If this count exceeds full ADQA inversions, **importance weighting** may fix label noise.