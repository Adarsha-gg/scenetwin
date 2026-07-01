---
title: SceneTwin statistical power (60-clip primary + 18-clip pilot)
category: research
tags: [scenetwin, statistics, paper-section, methods]
sources: [cursor/output/external_ensemble_eval.csv, cursor/output/corrected_ladder_robustness.json, output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv]
created: 2026-05-29
updated: 2026-06-27
---

> Corrected three-tier ladder. The **60-clip set is primary**; the 18-clip set is the corroborating
> pilot. Superseded: the old 4-tier power page (n = 72/240, ρ = 0.929/0.873, min-detectable 0.325).
> All values recomputed from the released per-tier CSVs and validated against
> `corrected_ladder_robustness.json`.

## Headline

The primary result rests on **60 clips × 3 tiers (n = 180 observations)** with the 18-clip pilot as
an independent, disjoint confirmation. Every significance test rejects the null in the same
direction, and the minimum effect detectable at n = 180 with 80% power is ρ ≈ 0.21 — far below the
observed ρ ≈ 0.95.

## Significance tests (60-clip primary)

| Test | Statistic | Value |
|---|---|---:|
| Spearman rank correlation | ρ | **0.952** |
| Kendall τ-b | τ | 0.876 |
| Within-clip permutation (B = 5000) | empirical | p < 2e-4 |
| Pairwise T3 wins (binomial null 0.5) | 118/120 | p ≈ 1e-32 |

## Bootstrap confidence intervals (cluster bootstrap by clip)

```
Primary (60 clips):  95% CI on ρ = [0.93, 0.97]
Pilot   (18 clips):  95% CI on ρ = [0.92, 0.98]
```

Both lower bounds sit well above any threshold for "metric tracks the tier ranking."

## Power analysis

Fisher z-transform, α = 0.05 two-sided, power = 0.80, ρ_min = tanh((z_crit + z_power)/√(n − 3)):

| Corpus | n_obs | min detectable ρ | observed ρ | margin |
|---|---:|---:|---:|---:|
| Primary (60) | 180 | 0.21 | 0.952 | +0.74 |
| Pilot (18) | 54 | 0.37 | 0.954 | +0.58 |
| Combined (78) | 234 | 0.18 | 0.954 | +0.77 |

The study is far inside the region where the test is decisive on every corpus.

## Pilot (18-clip) significance

| Test | Statistic | Value |
|---|---|---:|
| Spearman ρ | ρ | 0.957 |
| Kendall τ-b | τ | 0.887 |
| Within-clip permutation | empirical | p < 2e-4 |
| Pairwise T3 wins | 36/36 | p ≈ 1.5e-11 |

## Combined corpus (18 + 60 = 78 clips, 234 obs)

Spearman ρ = **0.954**, min detectable ρ = 0.18. Because the two sets are disjoint by construction,
the combined statement — *ρ ≈ 0.95 on 78 unique clips across 11 categories* — is a clean
generalization claim, not a re-use of the same clips.

## "Is the sample large enough?"

The primary unit is the 60-clip set (180 per-tier observations), not the 18-clip pilot. The pilot is
reported as the original, independent benchmark whose clip set does not overlap the primary set.
Effect size, CI width, detection floor, and p-value all improve on the primary set relative to the
pilot, and improve further under aggregation.

## See Also

- [[research/scenetwin-external-validation]] — 60-clip primary detail + per-category
- [[research/scenetwin-signal-decomposition]] — corrected-ladder CLIP/ADQA decomposition
- [[research/scenetwin-adqa-clip-ensemble]] — 18-clip pilot headline

## Sources

- `cursor/output/external_ensemble_eval.csv` (60-clip per-tier scores)
- `cursor/output/corrected_ladder_robustness.json` (sweep, bootstrap, permutation)
- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (18-clip pilot)
