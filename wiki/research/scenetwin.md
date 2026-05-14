---
title: "SceneTwin: TRIBE v2 Audio Description Fidelity Scoring"
category: research
tags: [NJBDA-2026, TRIBE-v2, accessibility, audio-description, blind, low-vision, brain-encoding]
sources:
  - https://huggingface.co/facebook/tribev2
  - https://www.nature.com/articles/s41597-025-06077-3
  - https://francescasetti.github.io/101-Dalbraintians/
  - https://github.com/giacomohandjaras/101_Dalmatians
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12413206/
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12398407/
  - https://huggingface.co/papers/2104.08718
  - https://aclanthology.org/2025.emnlp-main.1199/
  - https://katha-ai.github.io/projects/adqa/
  - https://github.com/facebookresearch/tribev2
  - https://sciety.org/articles/activity/10.1101/2025.04.15.646250
  - https://huggingface.co/papers/2507.17958
  - https://njbda.org/2026-symposium/
created: 2026-04-11
updated: 2026-05-02
---

SceneTwin uses TRIBE v2 to score how well audio descriptions preserve the predicted cortical response of the original video scene. The core metric is cosine similarity between the predicted cortical map of the video and the predicted cortical map of the audio/text description. Higher similarity means the description better preserves the scene's predicted cross-modal semantic response.

## Current Status (2026-05-02)

### What is actually novel

Literature search (2026-05-02) confirms:

- **CLIPScore** already does reference-free image/video-caption grounding. The CLIP part of SceneTwin is not novel by itself.
- **VideoA11y** already covers BLV-focused AD generation and sighted/BLV user evaluation. SceneTwin cannot claim "first AI AD evaluation for BLV users."
- **ADQA** (EMNLP 2025) is the strongest competing evaluation framework: QA-based AD scoring on multi-minute coherent segments. Probably the closest competitor on the evaluation side.
- **TRIBE v2** is new and powerful, but it is a general brain-encoding model, not an AD-quality metric.
- **Naturalistic movie fMRI / neurocinematics**: well-established field (VALOR, Algonauts 2025, VIBE, CineBrain, 101 Dalmatians). "Brain encoding for movies" is not new.

What was **not** found: a system that combines (1) AD accessibility evaluation, (2) video/text/audio brain-response prediction, (3) hallucination/visual grounding, and (4) a Description Gain metric that tests whether the AD restores predicted scene experience missing from audio alone. That combination is the possible breakthrough.

### The defensible contribution

> SceneTwin is a neural accessibility audit metric: it combines visual grounding with predicted brain-response gain to evaluate whether audio descriptions are not only accurate, but **experience-preserving**.

The key claim is not "CLIP checks whether captions match video" — that is CLIPScore. The key claim is:

> **Description Gain** = how much predicted cortical signal a description recovers for a listener who only has audio, compared to a viewer who has full audiovisual experience.

Formula:
```
P_AV  = TRIBE(original_video)          # what the full scene activates
P_A   = TRIBE(audio_only)              # what the soundtrack activates alone
P_AD  = TRIBE(text_description)        # what the AD activates

DescriptionGain = cos(P_AV, P_AD) - cos(P_AV, P_A)
```

A positive DG means the description recovers visual/semantic cortical signal that the audio track cannot. A near-zero DG means the AD is redundant with the soundtrack. A negative DG means the AD actively diverges from the scene.

### Evidence hierarchy (current)

1. **Lead evidence**: real VideoA11y/VATEX evaluation (20 clips × 4 tiers). CLIP-L14 ρ=0.723***. CLIP strongly rejects cross-category (20/20) but only beats generic VATEX captions 11-14/20 — exactly the gap where TRIBE Description Gain is needed.
2. **Proof of concept**: Sintel `TRIBE × CLIP` fixes original hallucination failure (TRIBE-only rewarded vivid beach description). Shows the combination works.
3. **Supporting**: temporal/ROI-restricted TRIBE analyses on saved tensors. Useful but margins too small to replace grounding.
4. **Superseded**: synthetic truncation tiers, self-written multi-clip retrieval. Useful diagnostics but the VideoA11y/VATEX result is the honest one.

### Honest skeptic check

A skeptical reviewer reading the current results could say:

> "This is CLIPScore plus an undervalidated TRIBE add-on."

That critique is fair. It stops being fair if Description Gain shows DescriptionGain(VideoA11y AD) > DescriptionGain(VATEX same-scene captions). That result would prove TRIBE catches something CLIP cannot: that ADs restore experiential signal specifically because they describe what a sighted viewer sees, not just what sounds like a visually-rich sentence.

### Next decisive experiment

Run Description Gain on all 20 VATEX-overlap clips. Test:
```
DescriptionGain(tier3_va11y) > DescriptionGain(tier2_vatex_long)
                              > DescriptionGain(tier1_vatex_short)
                              > DescriptionGain(tier0_cross)
```
Notebook: `output/scenetwin_description_gain_colab.ipynb`

The important distinction:

- **101 Dalmatians** is the scientific anchor because it contains real fMRI data and multimodal movie annotations for typical-development, congenitally blind, and congenitally deaf participants.
- **The first runnable demo** should use an open video clip, not the full Dalmatians movie stimulus, because the dataset is large and the movie stimulus/access path should not block the proof of concept.
- **SceneTwin itself has not already been done**: prior work has real fMRI and audio-description/accessibility studies, but the novel piece is using TRIBE v2 as an automatic fidelity metric for candidate audio/text descriptions.

## Abstract

Video accessibility for blind and low-vision users relies on audio descriptions that translate visual scenes into spoken language. Current AI-generated descriptions are evaluated through human ratings, accessibility guidelines, or text-similarity metrics, but none of these directly measure whether the description preserves the semantic experience of the original scene. We propose SceneTwin, a framework that uses TRIBE v2, a multimodal brain-encoding model, to map both video scenes and their candidate audio or text descriptions into a shared predicted cortical response space over approximately 20,000 surface vertices. We define a Scene Preservation Score as the cosine similarity between the predicted response to the original video and the predicted response to the description, and an Accessibility Efficiency Score that balances preserved scene information against description length and predicted cognitive load. We use the 101 Dalmatians multimodal fMRI dataset as the scientific validation reference, because it contains real fMRI and multimodal annotations for movie perception across typical development and congenital sensory loss. For the first runnable proof of concept, we use open video clips with controlled human-written, AI-generated, vague, hallucinated, and overloaded descriptions. This work frames audio description evaluation as a cross-modal alignment problem in predicted neural space, providing a scalable audit layer for AI-generated media accessibility systems. SceneTwin connects accessible AI, multimodal data, and computational ethics by offering a reproducible, brain-model-grounded metric for a problem that currently lacks one.

## Conference

NJBDA 13th Annual Symposium, May 20, 2026, Rowan University.
Theme: Building Accessible & Sustainable AI Ecosystems: People, Data, Ethics, & Infrastructure.

- **Abstract deadline:** April 17, 2026
- **Digital poster deadline:** May 15, 2026

## Core Metric

```
Scene Preservation Score = cosine(TRIBE_description, TRIBE_video)
Accessibility Efficiency Score = Scene Preservation Score / description_length
Neural Accessibility Score = Scene Preservation Score - λ * Cognitive_Load_Proxy
```

## Dataset Strategy

### Scientific Anchor: 101 Dalmatians

Use 101 Dalmatians as the credibility anchor, not as the first blocking dependency. It is valuable because it already studies movie perception across visual, auditory, and audiovisual conditions, including typical-development and congenital sensory-loss groups.

Useful pieces:

- real fMRI data in BIDS format
- analysis code on GitHub
- scene, cut, subtitle, dialogue, soundtrack, and audio-description annotations
- auditory descriptors such as VGGish
- visual descriptors such as VGG-19
- semantic embeddings generated with GPT-4

This dataset supports the claim that cross-modal movie accessibility is a real neuroscience/data problem. It does **not** mean SceneTwin has already been solved.

### Runnable Demo: Open Clips

The proof of concept should use open clips first:

- Sintel / Blender Open Movie clips
- short public-domain video scenes
- self-recorded scenes if needed

Reason: the NJBDA abstract/poster needs a working demo, and the full Dalmatians fMRI/movie workflow is too heavy to make the first milestone depend on it.

## Method

1. Select 10-15 short open video clips for the proof of concept
2. For each clip, prepare multiple descriptions:
   - Human-written concise
   - Human-written detailed
   - AI-generated concise
   - AI-generated detailed
   - Bad/hallucinated (control)
   - Overloaded with excessive detail
3. Run TRIBE v2 on video clip and each description
4. Compute Scene Preservation Score for each pair
5. Rank descriptions by fidelity and efficiency
6. Use 101 Dalmatians as the validation/reference dataset once the proof of concept works

## Novel Claim

Prior work evaluates audio descriptions using human ratings, accessibility guidelines, and multimodal model metrics. This project proposes a new evaluation layer: using TRIBE v2 predicted cortical response maps to estimate how well an audio or text description preserves the response profile of the original video scene.

## Key Limitation

TRIBE v2 predicts an "average" fMRI-like response, not specifically a blind or low-vision user's experience. SceneTwin uses TRIBE as a scalable proxy for cross-modal semantic preservation, grounded in BLV audio-description research and the 101 Dalmatians sensory-loss fMRI dataset.

## Poster Visual

For one scene, show:

1. original video frame
2. TRIBE video cortical map
3. concise description map and score
4. detailed description map and score
5. AI description map and score
6. hallucinated description map and score
7. fidelity-vs-burden plot

The judge-facing question:

> Which description best preserves the scene without overloading the listener?

## Final Line

> Accessibility is not just adding words to video. It is preserving the experience across senses.

## Proof of Concept Results (2026-04-11)

### Setup
- Video: Sintel trailer (first 30 sec, Blender open movie)
- Model: TRIBE v2 on Google Colab T4 GPU
- Video predictions shape: (30, 20484) — 30 time points, 20484 cortical vertices
- Four text descriptions written manually, run through TRIBE text modality (TTS → audio → brain map)

### Scene Preservation Scores (cosine similarity to video)

| Description | Score | Words |
|---|---|---|
| accurate_concise | 0.7446 | ~40 |
| accurate_detailed | 0.7602 | ~70 |
| bad_vague | 0.3850 | ~15 |
| hallucinated | 0.7908 | ~40 |

### Key Findings

1. **bad_vague scored much lower (0.38)** — the metric clearly separates low-effort descriptions from substantive ones. Raw cosine has signal for descriptive richness.

2. **hallucinated scored highest (0.79)** — a vivid beach description scored higher than the accurate snow scene description. The naive metric rewards "rich visual/narrative description," not "correct description of this exact scene."

3. **Why hallucinated scored high**: the beach description is vivid ("man, red suit, tropical beach, palm trees, children, ocean, sun") and activates broad visual-semantic / narrative regions. Whole-cortex averaging over the full time window loses scene-specific details like snow vs beach.

4. **Honest conclusion**: TRIBE predicts partially overlapping cortical response patterns for video scenes and rich natural-language descriptions, but naive whole-cortex similarity is insufficient for detecting hallucinated descriptions.

5. **Important**: 0.79 does NOT mean "79% same brain activity." It is cosine similarity between predicted response vectors — the vectors point in a similar direction in high-dimensional space, not that actual brain activity is 79% identical.

### Next Metric: Contrastive Scene Preservation Score

The naive metric asks "is this a rich visual description?" not "is this the correct description for this video?" The fix is contrastive evaluation.

Use multiple clips:
- video_1 = snow scene, video_2 = beach scene, video_3 = city scene, etc.
- Each has its own correct description
- Compute a full similarity matrix (all videos x all descriptions)

New metric:
```
Contrastive SPS = cos(video_i, correct_desc_i) - mean_j≠i cos(video_i, wrong_desc_j)
```

Or stricter: **Retrieval Rank** = rank of correct_desc_i among all candidate descriptions.

This fixes the hallucination issue because a beach hallucination should match a beach video better than a snow video. The description must uniquely match its source, not just sound visually rich.

### Corrected SceneTwin: TRIBE + CLIP (2026-04-11)

Added CLIP visual grounding score (ViT-B-32, laion2b) to fix the hallucination problem. CLIP compares sampled video frames against description text. Final score = normalized TRIBE * normalized CLIP (product means description must pass both checks).

| Description | TRIBE | CLIP_top3 | TRIBE_norm | CLIP_norm | FINAL |
|---|---|---|---|---|---|
| accurate_detailed | 0.7602 | 0.2931 | 0.9245 | 1.0000 | **0.9245** |
| accurate_concise | 0.7446 | 0.2525 | 0.8860 | 0.6599 | **0.5847** |
| bad_vague | 0.3850 | 0.2335 | 0.0000 | 0.5009 | **0.0000** |
| hallucinated | 0.7908 | 0.1737 | 1.0000 | 0.0000 | **0.0000** |

**Result:** The combined metric correctly ranks all four descriptions. TRIBE alone couldn't catch hallucinations (scored 0.79). CLIP alone couldn't judge descriptive richness. Together they nail it:
- accurate_detailed wins (rich AND grounded)
- accurate_concise second (grounded but less rich)
- bad_vague zeroed out by TRIBE (not rich enough)
- hallucinated zeroed out by CLIP (vivid but wrong scene)

**Final SceneTwin Score formula:**
```
SceneTwin = normalize(TRIBE_cosine) * normalize(CLIP_grounding)
```

Where:
- TRIBE_cosine = cosine(TRIBE_video_avg, TRIBE_description_avg)
- CLIP_grounding = mean of top-3 frame similarities between CLIP(video_frames) and CLIP(description_text)

### Poster Story

> A naive brain-response similarity metric detects descriptive richness but fails on hallucinated descriptions. SceneTwin fixes this by combining TRIBE-predicted cortical alignment with CLIP visual grounding. The product of both scores ensures a description must be both neurally similar AND visually grounded to score high.

### Files
- Notebook: `/Users/adarsha/njbda/scenetwin_test.ipynb`
- Results image: `/Users/adarsha/Downloads/scenetwin_results.png`
- Video predictions from stim.mp4: `/Users/adarsha/Downloads/predictions.npy`
- 101 Dalmatians repo (annotations/code): `/Users/adarsha/njbda/101_Dalmatians/`

### Next Steps
1. Update abstract to include TRIBE + CLIP combined metric
2. Test with more video clips and AI-generated descriptions (Claude/GPT)
3. Run contrastive experiment: 5 diverse clips, full similarity matrix
4. Download 101 Dalmatians fMRI data from Figshare for validation against real brain scans
5. Build poster visuals: brain maps + corrected score bar chart
6. Submit abstract by April 17, 2026

## Sources

- [TRIBE v2 — HuggingFace](https://huggingface.co/facebook/tribev2)
- [101 Dalmatians fMRI dataset](https://www.nature.com/articles/s41597-025-06077-3)
- [101 Dalbraintians project page](https://francescasetti.github.io/101-Dalbraintians/)
- [101 Dalmatians GitHub repository](https://github.com/giacomohandjaras/101_Dalmatians)
- [Describe Now — AI audio descriptions for BLV users](https://pmc.ncbi.nlm.nih.gov/articles/PMC12413206/)
- [VideoA11y — accessible description dataset](https://pmc.ncbi.nlm.nih.gov/articles/PMC12398407/)
- [NJBDA 2026 Symposium](https://njbda.org/2026-symposium/)
