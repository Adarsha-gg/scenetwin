# Cross-Model ADQA: v2 (Claude→Claude) vs v3 (Claude→GPT-4o)

## Aggregate Metrics

| | v2 same-model | v3 cross-model | delta |
|---|---|---|---|
| Spearman ρ | 0.8029 | 0.7263 | -0.0766 |
| Pairwise tier3 wins | 51/54 | 47/54 | -4 |
| Fully ordered clips | 8/18 | 8/18 | +0 |

## Tier Mean Scores

| Tier | gt | v2 (same-model) | v3 (cross-model) |
|---|---|---|---|
| tier3_va11y | 3 | 0.650 | 0.589 |
| tier2_vatex_long | 2 | 0.422 | 0.361 |
| tier1_vatex_short | 1 | 0.244 | 0.217 |
| tier0_cross | 0 | 0.039 | 0.022 |

## Interpretation

- **Question generation**: Claude haiku (vision, frame-grounded) — identical in both runs.
- **Grading**: v2 = Claude haiku (text); v3 = GPT-4o (text).
- A higher ρ in v3 suggests same-model bias inflated v2.
- A similar ρ in v3 confirms the v2 result was not an artifact of the grader knowing the generator's style.
- Tier ordering should be monotonic in both; any flip is a signal worth investigating.
