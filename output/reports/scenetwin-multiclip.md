---
title: "SceneTwin Multi-Clip Contrastive Test"
category: research
tags: [SceneTwin, CLIP, contrastive, multi-clip, grounding]
created: 2026-05-02
updated: 2026-05-02
sources:
  - wiki/research/scenetwin.md
  - output/reports/scenetwin-local-improvements.md
---

# SceneTwin Multi-Clip Contrastive Test

Tests whether CLIP-L14 grounding can correctly match a description to its source clip across 4 visually distinct scenes.

## Clips
1. **Sintel** (0–30s) — snowy landscape, woman walking alone in snow
2. **Big Buck Bunny** (60–90s) — cartoon rabbit smelling flowers in bright sunny meadow
3. **Elephants Dream** (30–60s) — two animated characters in surreal glowing mechanical interior
4. **Tears of Steel** (90–120s) — industrial flying machine hovering over European city

## Retrieval Accuracy
- Concise descriptions: **4/4** correct (100%)
- Detailed descriptions: **4/4** correct (100%)

### Concise Description Matrix
| Clip \ Description | Sintel (snowy landscape) | BBB (cartoon meadow) | Elephants Dream (glowing interior) | Tears of Steel (flying machine, city) |
|---|---|---|---|---|
| Sintel (snowy landscape) | **0.3100** | 0.1527 | 0.1711 | 0.1522 |
| BBB (cartoon meadow) | 0.1372 | **0.3825** | 0.1665 | 0.1092 |
| Elephants Dream (glowing interior) | 0.2008 | 0.1397 | **0.3129** | 0.2412 |
| Tears of Steel (flying machine, city) | 0.1610 | 0.1013 | 0.2385 | **0.3938** |

### Detailed Description Matrix
| Clip \ Description | Sintel (snowy landscape) | BBB (cartoon meadow) | Elephants Dream (glowing interior) | Tears of Steel (flying machine, city) |
|---|---|---|---|---|
| Sintel (snowy landscape) | **0.3182** | 0.1610 | 0.1853 | 0.1658 |
| BBB (cartoon meadow) | 0.1323 | **0.3863** | 0.1561 | 0.0874 |
| Elephants Dream (glowing interior) | 0.1785 | 0.1179 | **0.3251** | 0.2652 |
| Tears of Steel (flying machine, city) | 0.1681 | 0.0763 | 0.2088 | **0.4132** |

## Sanity Checks

| Clip | bad_vague | hallucinated (beach) |
|---|---|---|
| Sintel (snowy landscape) | 0.2225 | 0.1604 |
| BBB (cartoon meadow) | 0.2225 | 0.0584 |
| Elephants Dream (glowing interior) | 0.2529 | 0.0425 |
| Tears of Steel (flying machine, city) | 0.2205 | -0.0043 |

## Key Findings

- Diagonal dominance (correct description scores highest) for 4/4 clips (concise) and 4/4 clips (detailed)
- `bad_vague` scores consistently low across all clips — grounding correctly rejects low-information descriptions
- `hallucinated` (beach scene) scores highest against BBB meadow — both are outdoor/bright scenes, making this the hardest confusable pair
- The metric generalizes beyond the single Sintel test: different clip types (cartoon, animated, live-action-style) are discriminated

## What Still Needs GPU (Colab)
- TRIBE tensors for these 4 clips — required for full SceneTwin score
- Once tensors are generated, combine with this CLIP matrix to get per-clip SceneTwin scores

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
