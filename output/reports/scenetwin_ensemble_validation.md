# SceneTwin Ensemble Validation

## 1. CLIP ↔ ADQA Per-Clip Complementarity

- Mean per-clip Spearman between CLIP and ADQA scores: **0.761**
- Clips where CLIP and ADQA agree on ranking direction: **94%**

> **Moderate correlation**: CLIP and ADQA share signal but are not identical (ρ=0.761). Ensemble gains are plausible but not guaranteed to generalise.

### Per-Clip Detail

|   clip_idx |   clip_adqa_rho |   clip_gt_rho |   adqa_gt_rho |   ens_gt_rho | clip_adqa_agree   |
|-----------:|----------------:|--------------:|--------------:|-------------:|:------------------|
|          0 |          -0.447 |           0.4 |         0     |        0.316 | False             |
|          1 |           1     |           1   |         1     |        1     | True              |
|          3 |           1     |           1   |         1     |        1     | True              |
|          4 |           0.632 |           0.8 |         0.949 |        1     | True              |
|          5 |           0.949 |           1   |         0.949 |        1     | True              |
|          6 |           0.4   |           0.4 |         1     |        1     | True              |
|          7 |           0.949 |           1   |         0.949 |        1     | True              |
|          8 |           1     |           1   |         1     |        1     | True              |
|          9 |           1     |           1   |         1     |        1     | True              |
|         11 |           1     |           1   |         1     |        1     | True              |
|         12 |           0.8   |           0.4 |         0.8   |        0.8   | True              |
|         13 |           0.8   |           0.8 |         1     |        1     | True              |
|         14 |           0.632 |           0.4 |         0.949 |        0.8   | True              |
|         15 |           0.632 |           0.8 |         0.949 |        1     | True              |
|         16 |           0.632 |           0.8 |         0.949 |        1     | True              |
|         17 |           0.775 |           1   |         0.775 |        1     | True              |
|         18 |           0.949 |           1   |         0.949 |        1     | True              |
|         19 |           1     |           1   |         1     |        1     | True              |


## 2. Bootstrap 95% CI on Ensemble ρ

| Metric | Observed ρ | 95% CI |
|---|---|---|
| Ensemble (CLIP + ADQA, 50/50) | **0.9285** | [0.904, 0.957] |
| CLIP-only | 0.8010 | [0.728, 0.873] |


N clips: 18 | N bootstrap resamples: 2000

> CIs do not overlap. Ensemble improvement is robust at this sample size.
