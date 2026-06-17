---
title: External Ensemble Generalization
category: research
tags: [SceneTwin, ensemble, generalization, ADQA, CLIP]
created: 2026-05-28
updated: 2026-05-28
---

# External Ensemble Generalization

Does headline **ensemble_mean_clip_top3 ρ≈0.93** hold on 58 held-out YouTube clips?

## Method

- Frame-grounded ADQA (5Q, blind A/B/C/D grading) — same protocol as benchmark adqa_v2
- CLIP ViT-L-14 top3 from `external_clip_full_eval.csv`
- Min-max normalize ADQA + CLIP within clip; ensemble = 50/50

## Results

| Split | Metric | ρ | full order | pairwise |
|-------|--------|---|------------|----------|
| External | 0.873 | 30/60 | 173/180 |
| External CLIP-only | 0.631 | 16/60 | 142/180 |
| External ADQA-only | 0.785 | 23/60 | 171/180 |
| Benchmark (recomputed) | 0.928 | 15/18 | 54/54 |

## Verdict

External ensemble ρ=0.873 vs benchmark ρ=0.928 (Δρ=0.055). CLIP-only external ρ=0.631. Partial generalization — ensemble lifts over CLIP-only on external.

## See Also

- [[research/GROUND-UP-THESIS]]
- [[findings/ground-up-reframe]]
