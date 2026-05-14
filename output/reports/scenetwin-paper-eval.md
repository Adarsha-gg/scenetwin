---
title: "SceneTwin Paper Evaluation — CLIP vs BERTScore vs BLEU"
category: research
tags: [SceneTwin, evaluation, BERTScore, BLEU, CLIP, Spearman, VideoA11y]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/reports/scenetwin-videoa11y.md
  - https://huggingface.co/datasets/chaoyuli/VideoA11y-40K
---

# SceneTwin Paper Evaluation

Systematic comparison of reference-free (CLIP-L14) vs reference-dependent (BERTScore, BLEU-4) metrics
for audio description quality evaluation. 19 clips × 4 description quality tiers.

## Setup

**Clips:** 19 YouTube clips from VideoA11y-40K test set
**Categories:** Film & Animation, Pets & Animals, Sports, Travel
**Total data points:** 76 (19 clips × 4 tiers)

**Quality tiers (ground truth):**
| Tier | Label | Description | Quality score |
|---|---|---|---|
| 3 | full | Complete VideoA11y description (GPT-4V + AD guidelines) | 3 (best) |
| 2 | first_sentence | First sentence only | 2 |
| 1 | truncated_10w | First 10 words only | 1 |
| 0 | cross_category | Description from different category | 0 (worst) |

## Main Result: Spearman Correlation

| Metric | Type | Spearman ρ | p-value | Sig |
|---|---|---|---|---|
| **CLIP-L14** | **Reference-free** | **0.7752** | **0.0000** | ******* |
| BERTScore-RoBERTa | Reference-dependent | 0.9510 | 0.0000 | *** |
| BLEU-4 | Reference-dependent | 0.8111 | 0.0000 | *** |

## Mean Scores per Quality Tier

| Tier | CLIP-L14 | BERTScore | BLEU-4 |
|---|---|---|---|
| full (3) | 0.3345 | 1.0000 | 1.0000 |
| first_sentence (2) | 0.3220 | 0.9404 | 0.2586 |
| truncated_10w (1) | 0.2819 | 0.9036 | 0.1015 |
| cross_category (0) | 0.0767 | 0.8498 | 0.0176 |

## Key Findings

1. **Reference-free advantage**: CLIP-L14 evaluates all 4 tiers directly against video content. BERTScore and BLEU assign tier 3 a trivial score of 1.0 (it is the reference), artificially inflating their correlation.

2. **Cross-category rejection**: CLIP correctly assigns the lowest scores to cross-category descriptions (tier 0). BERTScore/BLEU detect these as off-topic only through text similarity to the reference.

3. **TRIBE + CLIP next**: The current metric is CLIP-only (grounding). Adding TRIBE's neural gain signal (Description Gain = cos(AV, audio+desc) − cos(AV, audio)) is the planned upgrade — see Colab notebook for TRIBE inference.

## What's Still Needed for Publication
- TRIBE runs on these 19 clips → Description Gain metric (needs Colab T4)
- Human ratings (BLV users or professional describers) for Spearman validation
- More clips (100+) for robust statistics
- Ablation: CLIP-alone vs TRIBE-alone vs TRIBE×CLIP

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
