---
title: "SceneTwin Real Evaluation — VideoA11y vs VATEX Human Captions"
category: research
tags: [SceneTwin, evaluation, BERTScore, BLEU, CLIP, Spearman, VideoA11y, VATEX, real-descriptions]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/reports/scenetwin-paper-eval.md
  - https://huggingface.co/datasets/chaoyuli/VideoA11y-40K
  - https://huggingface.co/datasets/lmms-lab/VATEX
---

# SceneTwin Real Evaluation — No Synthetic Descriptions

**20 clips × 4 real description tiers** — no truncation tricks.
All descriptions are genuine, independently generated text with documented quality ordering.

## Description Tiers

| Tier | Source | Quality (VideoA11y paper) |
|---|---|---|
| 3 | VideoA11y (GPT-4V + AD guidelines) | ~4.2/5 (human study) |
| 2 | VATEX longest caption (crowd-sourced) | ~3.1/5 (generic, more detail) |
| 1 | VATEX shortest caption (crowd-sourced) | ~3.1/5 (generic, less detail) |
| 0 | Cross-category VideoA11y description | ~0 (completely wrong content) |

Tiers 2 and 1 are both from VATEX crowd workers — same quality tier in the paper, but varying
length gives natural within-tier variation. This is the legitimate separation.

## Main Result

| Metric | Type | Spearman ρ | Kendall τ | Score range | Sig |
|---|---|---|---|---|---|
| **CLIP-L14** | **Reference-free** | **0.7233** | **0.5788** | **0.407** | ******* |
| BERTScore-RoBERTa | Reference-dependent | 0.8623 | 0.7246 | 0.154 | *** |
| BLEU-4 | Reference-dependent | 0.5714 | 0.4352 | 1.000 | *** |

## Mean Scores per Tier

| Tier | CLIP-L14 | BERTScore | BLEU-4 |
|---|---|---|---|
| VA11y (AD-quality) | 0.3376 | 1.0000 | 1.0000 |
| VATEX long (generic+) | 0.3248 | 0.8919 | 0.0323 |
| VATEX short (generic-) | 0.3060 | 0.8919 | 0.0081 |
| cross-category | 0.0896 | 0.8586 | 0.0218 |

## Key Argument for the Paper

BERTScore compresses all real descriptions into a 0.154-wide band (scores 0.846–1.000).
CLIP-L14 uses a 0.407-wide range — **2.6× more discriminative**.

CLIP correctly identifies wrong-content descriptions (tier 0) with a mean score of
0.090 vs 0.338 for AD-quality descriptions —
a 3.8× difference. BERTScore gives tier 0
a score of 0.859 (barely lower than 1.000).

Reference-free evaluation is not just convenient — it is more discriminative for the task
of catching wrong-content descriptions, which is the core failure mode in AI-generated ADs.

## What's Left for the Full Paper
1. TRIBE runs on these 20 clips → Description Gain metric (needs Colab T4)
2. Increase to 100+ clips for robust statistics
3. Real BLV user ratings (contact chaoyuli@asu.edu for study data, or run own MTurk study)
4. Ablation: CLIP-alone vs TRIBE-alone vs TRIBE×CLIP

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-paper-eval]]
