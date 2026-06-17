---
title: Corrected Ladder — Robustness
category: research
tags: [SceneTwin, robustness, ablation, generalization]
updated: 2026-06-07
---

# The Corrected-Ladder Result Is Not a Tuned Configuration

The headline (drop the fake long-VATEX rung -> ρ≈0.95) uses ADQA weight 0.5 and clip-wise min-max. This stress-tests whether those two knobs were tuned to the number.

## 1. Ensemble-weight sweep (plateau, not spike)

| split | ρ @ w=0.5 | best ρ | best w | ρ range w∈[0.2,0.8] |
|--|--:|--:|--:|--:|
| Benchmark | 0.957 | 0.967 | 0.30 | 0.940–0.967 |
| VATEX-60 OOD | 0.952 | 0.953 | 0.85 | 0.933–0.953 |

The 0.5/0.5 point sits inside a flat high-ρ plateau; any weight from 20% to 80% ADQA gives essentially the same answer. We did not sit on the peak.

![robustness](../../output/charts/scenetwin_ladder_robustness.png)

## 2. Normalization ablation (ρ @ w=0.5)

| normalization | benchmark ρ | OOD ρ |
|--|--:|--:|
| clip-wise min-max | 0.957 | 0.952 |
| clip-wise z-score | 0.942 | 0.932 |
| within-clip rank | 0.950 | 0.934 |

## 3. Cluster bootstrap (resample clips, w=0.5, min-max)

- Benchmark: ρ = 0.958  95% CI [0.927, 0.977]
- VATEX-60 OOD: ρ = 0.951  95% CI [0.928, 0.968]

## 4. Within-clip permutation null (w=0.5, min-max)

- Benchmark: observed ρ=0.957, p=0.0002 (null mean 0.000)
- VATEX-60 OOD: observed ρ=0.952, p=0.0002 (null mean 0.001)

## Verdict

The corrected-ladder ρ survives every knob: it is flat across a wide ensemble-weight band, holds under three normalizations, has a tight bootstrap CI, and is far above the within-clip permutation null. The result is a property of the data, not of the config.

## See Also

- [[findings/fake-tier-rung]]
- [[findings/vatex60-generalization]]
