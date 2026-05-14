# ADQA Cross-Model Ablation: v2 / v3 / v4

| | v2 Claude→Claude | v3 Claude→GPT-4o | v4 GPT-4o→Claude |
|---|---|---|---|
| Questioner | Claude haiku | Claude haiku | **GPT-4o** |
| Grader     | Claude haiku | **GPT-4o**   | Claude haiku |
| Spearman ρ | 0.8029 | 0.7263 | 0.7888 |
| Pairwise wins | 51/54 | 47/54 | 50/54 |
| Fully ordered | 8/18 | 8/18 | 5/18 |

## Tier Mean Scores

| Tier | gt | v2 (C→C) | v3 (C→G) | v4 (G→C) |
|---|---|---|---|---|
| tier3_va11y | 3 | 0.650 | 0.589 | 0.628 |
| tier2_vatex_long | 2 | 0.422 | 0.361 | 0.356 |
| tier1_vatex_short | 1 | 0.244 | 0.217 | 0.317 |
| tier0_cross | 0 | 0.039 | 0.022 | 0.022 |

## What to look for

- Similar ρ across all three → ranking signal is model-agnostic, robust.
- v4 ρ close to v2 → Claude grades consistently whether it or GPT-4o asked the questions.
- v4 ρ close to v3 → grader model (not questioner model) drives the variance.
- Large v4 vs v2 gap → GPT-4o asks harder/different questions than Claude.
