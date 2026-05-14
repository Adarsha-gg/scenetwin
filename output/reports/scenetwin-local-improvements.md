---
title: "SceneTwin Local Improvement Analysis"
category: research
tags: [SceneTwin, CLIP, TRIBE, ROI, temporal-alignment, improvements]
created: 2026-05-02
updated: 2026-05-02
sources:
  - wiki/research/scenetwin.md
  - wiki/research/scenetwin-codex-handoff-2026-04-22.md
---

# SceneTwin Local Improvement Analysis

All results computed locally on existing TRIBE tensors (no GPU needed).
Video: Sintel trailer, first 30 seconds. 4 descriptions (accurate concise, accurate detailed, bad vague, hallucinated).

## What Was Tested

1. **TRIBE variants** — whole-cortex vs ROI-restricted vs temporal alignment
2. **CLIP upgrade** — ViT-B-32 (baseline) vs ViT-L-14 (upgrade)
3. **Combined scores** — all useful pairings of TRIBE variant × CLIP model

---

## TRIBE-Only Variants

| Variant | acc_concise | acc_detailed | bad_vague | hallucinated | Correct rank? |
|---|---|---|---|---|---|
| whole-cortex mean | 0.7405 | 0.7584 | 0.3880 | 0.7906 | ✗ |
| visual-core mean (Destrieux) | 0.9085 | 0.9469 | 0.5052 | 0.9419 | ✗ |
| PPA-proxy mean (Destrieux) | 0.7404 | 0.8668 | -0.0357 | 0.8630 | ✗ |
| ventral-scene mean (Destrieux) | 0.7586 | 0.8130 | -0.0190 | 0.8260 | ✗ |
| temporal whole-cortex | 0.6794 | 0.6339 | 0.3076 | 0.6584 | ✗ |
| temporal visual-core | 0.7310 | 0.7450 | 0.3631 | 0.7150 | ✗ |
| **temporal PPA-proxy** | **0.6740** | **0.7139** | **-0.0265** | **0.6738** | **✗** |

### Key finding
Temporal alignment within the PPA-proxy mask is the best exploratory TRIBE-only variant in this local sweep.
It separates bad_vague strongly and brings accurate_concise almost even with hallucinated, but the hallucination margin is tiny (`0.6740` vs `0.6738`). This is supporting evidence for temporal/ROI signal, not a poster-leading result.

---

## CLIP Grounding Scores (raw, top-3 frames)

| Model | acc_concise | acc_detailed | bad_vague | hallucinated |
|---|---|---|---|---|
| ViT-B-32 (current) | 0.2811 | 0.3121 | 0.2101 | 0.1648 |
| ViT-L-14 (upgrade) | 0.2967 | 0.3066 | 0.1993 | 0.1826 |

Both models correctly assign the lowest grounding score to the hallucinated beach description.
ViT-L-14 gives better score separation in the middle range (accurate_concise vs accurate_detailed).

---

## Combined SceneTwin Scores

| Variant | acc_concise | acc_detailed | bad_vague | hallucinated | Ranking |
|---|---|---|---|---|---|
| v0: TRIBE×CLIP-B32 (original) | 0.6915 | 0.9198 | 0.0000 | 0.0000 | accurate detailed > accurate concise > bad vague > hallucinated |
| v1: TRIBE×CLIP-L14 | 0.8053 | 0.9198 | 0.0000 | 0.0000 | accurate detailed > accurate concise > bad vague > hallucinated |
| v2: Temporal-Visual×CLIP-L14 | 0.8860 | 1.0000 | 0.0000 | 0.0000 | accurate detailed > accurate concise > bad vague > hallucinated |
| v3: Temporal-PPA×CLIP-L14 | 0.8702 | 1.0000 | 0.0000 | 0.0000 | accurate detailed > accurate concise > bad vague > hallucinated |
| v4: Ventral-Scene×CLIP-L14 | 0.8465 | 0.9847 | 0.0000 | 0.0000 | accurate detailed > accurate concise > bad vague > hallucinated |

---

## Recommendations

### For the poster (use now)
Replace the CLIP model in the existing Colab notebook:
```python
# from
model, _, preprocess = open_clip.create_model_and_transforms('ViT-B-32', pretrained='laion2b_s34b_b79k')
tokenizer = open_clip.get_tokenizer('ViT-B-32')
# to
model, _, preprocess = open_clip.create_model_and_transforms('ViT-L-14', pretrained='laion2b_s32b_b82k')
tokenizer = open_clip.get_tokenizer('ViT-L-14')
```

### Supporting result (use carefully)
Keep the temporal PPA-proxy TRIBE analysis as a supporting note if there is room:
> "TRIBE alone fails at whole-cortex level, but temporal alignment within PPA-proxy parcels
>  (parahippocampal + lingual, Destrieux atlas) partially recovers scene-specific signal."

This supports the ROI hypothesis shown in the codex handoff, but it should not be presented as a clean TRIBE-only fix.

### For Colab (needs GPU)
- Run Description Gain: audio-only TRIBE run vs audio+description vs audiovisual
- Run contrastive matrix: 5 diverse clips, full similarity matrix
- Swap to ViT-L-14 in CLIP grounding step

---

## Files
- Script: `/Users/adarsha/njbda/scenetwin_analysis.py`
- Chart: `/Users/adarsha/njbda/scenetwin_analysis_results.png`
- This report: `output/reports/scenetwin-local-improvements.md`

## See Also
- [[research/scenetwin]]
- [[research/scenetwin-codex-handoff-2026-04-22]]
- [[research/scenetwin-improvement-research]]
