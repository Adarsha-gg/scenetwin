---
title: TRIBE Neural Contrastive Retrieval Results
category: research
updated: 2026-06-23
sources:
  - cursor/research/output/ncr_similarity.csv
  - cursor/research/output/ncr_query_metrics.csv
  - cursor/research/output/ncr_summary.json
---

# TRIBE Neural Contrastive Retrieval Results

Analyzed **240** query vectors across **60** clips. This Colab run used TTS-audio-only AD queries and video+audio references with text stages disabled, because the full TRIBE text extractor requires gated Llama access.

| Tier | n | mean correct-rank pct | 95% bootstrap CI | median rank | mean cosine margin |
|---|---:|---:|---:|---:|---:|
| tier0_cross | 60 | 0.495 | [0.419, 0.569] | 32.0 | -0.002 |
| tier1_vatex_short | 60 | 0.488 | [0.418, 0.562] | 29.5 | -0.015 |
| tier2_vatex_long | 60 | 0.516 | [0.440, 0.589] | 32.0 | 0.010 |
| tier3_va11y | 60 | 0.518 | [0.444, 0.596] | 29.5 | 0.012 |

## Aggregate signal

- Spearman(tier, correct-rank percentile), 4-tier: **0.035**
- Spearman(tier, cosine margin), 4-tier: **0.026**
- Spearman(tier, correct-rank percentile), corrected 3-tier: **0.031**
- Spearman(word count, rank pct): **-0.008**
- Spearman(tier, length-residual rank pct): **0.035**

## Tier-3 pairwise wins by clip

| Comparison | n | mean diff | W/L/T | one-sided sign p |
|---|---:|---:|---:|---:|
| tier3_gt_tier0_cross | 60 | 0.022 | 32/20/8 | 0.0632 |
| tier3_gt_tier1_vatex_short | 60 | 0.029 | 36/21/3 | 0.0314 |
| tier3_gt_tier2_vatex_long | 60 | 0.002 | 34/23/3 | 0.0924 |

## Wrong-content source leakage check

For tier0_cross, mean target-rank pct = **0.495** and mean source-rank pct = **0.518**; source rank beat target rank on **37/60** clips.

## Alignment quarantine sensitivity

High-alignment queries: 156, low-alignment queries: 84.
High-alignment Spearman = **0.033**; low-alignment Spearman = **0.044**.

## Interpretation guardrail

This score is AD-dependent, but this run is the TTS-audio-only variant rather than the full gated text-extractor variant. Treat the small positive pairwise/source-specificity signals as pilot evidence only; do not market NCR as a working brain-grounded ranker without a pre-registered text-vs-audio ablation.
