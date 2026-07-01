---
title: TRIBE NCR Hidden Patterns and Guardrails
category: research
updated: 2026-06-23
sources:
  - cursor/research/output/ncr_query_metrics.csv
  - cursor/research/output/ncr_hidden_patterns/
---

# TRIBE NCR Hidden Patterns and Guardrails

This analyzes the full 60-clip NCR run after the first headline pass. The run used the robust **TTS-audio-only AD query** variant because the full TRIBE text extractor requires gated Llama access; video references used video+audio with text stages disabled.

## Bottom line

NCR is **not a revolutionary ranking metric** in this form: tier means stay near chance and global Spearman is ~0.03. The useful signal is weaker and narrower: professional AD beats the short crowd caption on 36/57 non-tie clips (sign p=0.031), and wrong-content AD retrieves its source clip more often than its target (37/60). That is a mechanism hint, not a headline result.

## Retrieval hubness / top-1 rates

| Tier | self top-1 hits | rate |
|---|---:|---:|
| tier0_cross | 1/60 | 0.017 |
| tier1_vatex_short | 0/60 | 0.000 |
| tier2_vatex_long | 1/60 | 0.017 |
| tier3_va11y | 1/60 | 0.017 |

Wrong-content source top-1: **1/60** (0.017). Source rank > target rank: **37/60**, one-sided sign p=0.0462.

Most common top-reference attractors across all queries:

- `0m0-Q0zz_-c_000112_000122`: 158 top-1 assignments
- `xW6hpK-DBMY_000080_000090`: 31 top-1 assignments
- `GOH6fBhoi2o_000010_000020`: 30 top-1 assignments
- `EA3HCx0yTIY_000281_000291`: 10 top-1 assignments
- `S-C86j0keqc_000217_000227`: 6 top-1 assignments
- `_TKzyWZHjm8_000002_000012`: 3 top-1 assignments
- `zTJ0Zbv1jBo_000045_000055`: 2 top-1 assignments

Interpretation: top-1 retrieval is sparse and hubbed; a few references attract many AD queries. Use rank-percentile/margins and source controls, not top-1 accuracy alone.

## Category splits

| Category | n | mean T3-T1 rank pct | T3>T1 W/L/T | mean source-target | source>target |
|---|---:|---:|---:|---:|---:|
| Education, Seminar & Talks | 1 | 0.356 | 1/0/0 | 0.136 | 1/1 |
| Music | 2 | 0.161 | 2/0/0 | -0.144 | 1/2 |
| Food & Cooking | 3 | 0.153 | 3/0/0 | -0.079 | 2/3 |
| How-to & Instructional | 21 | 0.145 | 16/3/2 | -0.039 | 14/21 |
| Event | 3 | 0.000 | 2/1/0 | 0.040 | 2/3 |
| Sports | 6 | -0.059 | 3/3/0 | 0.444 | 5/6 |
| Entertainment | 10 | -0.075 | 4/5/1 | 0.144 | 7/10 |
| Film & Animation | 2 | -0.076 | 1/1/0 | -0.322 | 0/2 |
| Health & Wellness | 4 | -0.097 | 2/2/0 | 0.097 | 1/4 |
| People & Vlogs | 8 | -0.100 | 2/6/0 | -0.178 | 4/8 |

## Existing-failure correlations

| Feature | Target | Spearman | AUC(high=>fail) | positives/n |
|---|---|---:|---:|---:|
| tier3_rank_pct | adqa_fail | 0.027 | 0.521 | 10/60 |
| tier3_rank_pct | ensemble_fail | 0.188 | 0.802 | 2/60 |
| tier3_minus_tier0 | adqa_fail | 0.088 | 0.568 | 10/60 |
| tier3_minus_tier0 | ensemble_fail | 0.207 | 0.832 | 2/60 |
| tier3_minus_tier1 | adqa_fail | 0.309 | 0.739 | 10/60 |
| tier3_minus_tier1 | ensemble_fail | 0.121 | 0.694 | 2/60 |
| tier0_source_minus_target | adqa_fail | 0.043 | 0.533 | 10/60 |
| tier0_source_minus_target | ensemble_fail | -0.064 | 0.397 | 2/60 |

Failure labels use the corrected 3-tier ladder (cross < short crowd caption < pro AD), excluding the fake long-VATEX rung. NCR does not obviously predict existing ADQA/ensemble failure labels. That supports keeping TRIBE's current role as blind-spot routing/triage rather than replacing the scoring stack.

## Strongest T3-vs-short positives

- `dlBeUWrse3I_000019_000029` (How-to & Instructional): T3-T1=0.390, source-target=-0.441
- `1-jIze6gy0g_000026_000036` (How-to & Instructional): T3-T1=0.373, source-target=-0.373
- `yBO8rAMeqjc_000007_000017` (Education, Seminar & Talks): T3-T1=0.356, source-target=0.136
- `N-LZPc27kjM_000229_000239` (How-to & Instructional): T3-T1=0.322, source-target=0.017
- `Ccgwurislg8_000082_000092` (How-to & Instructional): T3-T1=0.288, source-target=0.458
- `ShSSAEfnyDs_000000_000010` (Entertainment): T3-T1=0.254, source-target=0.203
- `Xdz1cxEjLYc_000007_000017` (Food & Cooking): T3-T1=0.254, source-target=-0.831
- `crjesEwF0Ks_000197_000207` (How-to & Instructional): T3-T1=0.254, source-target=0.237

## Strongest T3-vs-short negatives

- `1HUWWCLza0w_000000_000010` (Sports): T3-T1=-0.424, source-target=0.763
- `21T1JDdJgsM_000047_000057` (Entertainment): T3-T1=-0.424, source-target=0.441
- `3su234u58DA_000172_000182` (Entertainment): T3-T1=-0.322, source-target=0.203
- `BcW6Y7eufQE_000239_000249` (People & Vlogs): T3-T1=-0.322, source-target=0.102
- `zTJ0Zbv1jBo_000045_000055` (Health & Wellness): T3-T1=-0.322, source-target=0.831
- `HpRmj5ce32c_000001_000011` (Sports): T3-T1=-0.305, source-target=0.695
- `Bss3WwpDdS8_000041_000051` (People & Vlogs): T3-T1=-0.288, source-target=0.034
- `iEAWgsSvJAE_000023_000033` (Film & Animation): T3-T1=-0.271, source-target=-0.034

## Paper implication

Do **not** claim NCR solves AD-dependent brain scoring. The publishable value is a negative/guardrail plus a small source-specificity hint: when the wrong AD is a professional description from another clip, its TTS-audio TRIBE response weakly points to the source more than the target. The next scientifically clean version would require authenticated/gated text extractor access and a pre-registered text-vs-audio ablation, not more post-hoc thresholding.
