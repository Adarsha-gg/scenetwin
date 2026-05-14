---
title: "SceneTwin Real VideoA11y Description Test"
category: research
tags: [SceneTwin, CLIP, VideoA11y, real-descriptions, contrastive]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/reports/scenetwin-multiclip.md
  - https://huggingface.co/datasets/chaoyuli/VideoA11y-40K
---

# SceneTwin — Real VideoA11y Description Test

Tests CLIP-L14 grounding with **real, independently-generated** audio descriptions from
VideoA11y-40K (GPT-4V generated following proper AD guidelines, zero knowledge of the grounding metric).

This is the legitimate test. Prior multi-clip results used descriptions I wrote after looking at the frames — circular.

## Clips and Real Descriptions

**Waterfall (rocky stream)** (`4ztYgv_AzmY_70.000_80.000`)
> A cascade of water tumbles over rocks, creating a misty veil. The sunlight catches the droplets, casting a shimmer across the scene. Surrounding the waterfall, jagged rocks and branches are sporadically scattered, partially submerged in the frothy pool below.

**Skateboard (street trick)** (`lGf_L6i6AZI_20.000_30.000`)
> A person in a black t-shirt and blue shorts is crouched on the ground, holding a skateboard and flipping it with their hands.

**Bread (food closeup)** (`N-aqYNfr6VA_90.000_100.000`)
> A hand swiftly unpacks a paper bag on a white surface, revealing a large, golden-brown, crusted loaf of bread. The bag crinkles as it's opened. A white oval plate and a pair of red-handled scissors are also on the table, along with a small, clear plastic bag containing green vegetables.

**Dance (game animation)** (`_VDyZ1DwgQE_100.000_110.000`)
> In a spooky nighttime setting, a character dressed as a chef with oversized red gloves performs a dance called the 'Twist-and-Spout.' The character twists their body and raises their hands, as if conducting an orchestra. Suddenly, the character bends forward, and a green, ghostly substance erupts from their mouth, resembling a fountain of eerie energy.

## Contrastive Matrix (CLIP-L14, top-3 frame similarity)

| Clip \ Description | Waterfall (rocky stream) | Skateboard (street trick) | Bread (food closeup) | Dance (game animation) |
|---|---|---|---|---|
| Waterfall (rocky stream) | **0.2665** | 0.1375 | 0.0455 | 0.1560 |
| Skateboard (street trick) | 0.0032 | **0.2994** | 0.0779 | 0.0810 |
| Bread (food closeup) | 0.0694 | 0.0974 | **0.3294** | 0.1220 |
| Dance (game animation) | 0.0823 | 0.1170 | 0.0719 | **0.2802** |

## Retrieval Accuracy: 4/4

### Margin (correct score − best wrong score)
- Waterfall (rocky stream): +0.1105 (✓)
- Skateboard (street trick): +0.2183 (✓)
- Bread (food closeup): +0.2074 (✓)
- Dance (game animation): +0.1632 (✓)

## Interpretation

A positive margin means the correct description scored higher than any wrong description.
A negative margin means the metric failed — a wrong description was more similar to the clip.

This is the honest baseline: real descriptions, real errors possible, no circular self-evaluation.

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
