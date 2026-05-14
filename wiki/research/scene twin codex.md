---
title: "SceneTwin Codex Notes"
category: research
tags: [SceneTwin, TRIBE-v2, CLIP, accessibility, audio-description, NJBDA-2026, codex-notes]
created: 2026-04-11
updated: 2026-04-11
---

# SceneTwin Codex Notes

This note captures the current state of the SceneTwin project after the first proof-of-concept experiment and metric fix.

## Project

**SceneTwin** is a proposed NJBDA 2026 poster project that uses TRIBE v2 to evaluate audio/text descriptions for video accessibility.

Core idea:

> Accessibility is not just adding words to video. It is preserving the experience across senses.

SceneTwin compares:

1. the predicted cortical response to a video scene
2. the predicted cortical response to a candidate audio/text description
3. the visual grounding between the description and sampled video frames

The goal is to score whether an audio description preserves the original scene without being vague, overloaded, or hallucinated.

## Why It Matters

Audio descriptions help blind and low-vision users access video content. AI can generate descriptions at scale, but AI descriptions can be:

- too vague
- too long
- fluent but wrong
- visually hallucinated
- mismatched to important scene content

SceneTwin proposes an audit layer for AI-generated accessibility tools.

## Scientific Anchor

The **101 Dalmatians multimodal fMRI dataset** is the scientific anchor, not the first runnable demo dependency.

It matters because it includes real fMRI and multimodal movie annotations for:

- typical-development participants
- congenitally blind participants
- congenitally deaf participants
- audiovisual, auditory, and visual movie conditions
- audio-description-related annotations and computational features

Important distinction:

> The 101 Dalmatians dataset does not mean SceneTwin has already been done. It gives scientific grounding and a later validation path. SceneTwin's novel piece is using TRIBE v2 predicted cortical response maps as an automatic fidelity signal for candidate descriptions.

## Runnable Demo Strategy

The first demo uses an open video clip instead of the full Dalmatians movie/fMRI pipeline.

Reason:

- Dalmatians fMRI data is large.
- The movie stimulus/access path is cumbersome.
- NJBDA needs a working prototype quickly.
- Open clips let us test the metric without being blocked by dataset logistics.

Current proof of concept:

- Video: first 30 seconds of the Sintel open movie/trailer.
- Model: TRIBE v2 on Google Colab T4 GPU.
- Video prediction shape: `(30, 20484)`.
- Descriptions tested:
  - accurate concise
  - accurate detailed
  - bad vague
  - hallucinated beach scene

## First Metric: TRIBE-Only Scene Preservation Score

Original metric:

```text
Scene Preservation Score = cosine(TRIBE_description, TRIBE_video)
```

Implementation:

```python
video_avg = video_preds.mean(axis=0)
desc_avg = desc_preds.mean(axis=0)
score = cosine(video_avg, desc_avg)
```

Results:

| Description | TRIBE Score |
|---|---:|
| accurate_concise | 0.7446 |
| accurate_detailed | 0.7602 |
| bad_vague | 0.3850 |
| hallucinated | 0.7908 |

## What The TRIBE-Only Result Means

TRIBE-only cosine successfully separated a vague, low-information description from richer descriptions.

However, the hallucinated description scored highest.

That means raw whole-cortex cosine similarity is not enough. It rewards vivid, scene-like language even when the description is factually wrong.

The hallucinated description described a tropical beach, palm trees, children, ocean, sun, and heat. Even though this did not match the snowy Sintel scene, it was still a rich visual narrative, so TRIBE predicted a high cross-modal response similarity.

Conclusion:

> TRIBE-only scoring captures descriptive richness, but it does not reliably detect factual scene grounding.

This is not a failure of the whole project. It is the first methodological finding.

## Metric Fix: Add CLIP Visual Grounding

To fix hallucinated descriptions, SceneTwin now combines two signals:

1. **TRIBE Brain Alignment**: whether the description produces a predicted cortical response similar to the video.
2. **CLIP Visual Grounding**: whether the description actually matches sampled video frames.

Definitions:

```text
BrainAlignment(v, d) = cosine(TRIBE_video(v), TRIBE_description(d))
VisualGrounding(v, d) = CLIP(video_frames(v), description(d))
SceneTwinScore(v, d) = normalized(BrainAlignment) * normalized(VisualGrounding)
```

This means a description must pass both tests:

- it must evoke a rich cross-modal response
- it must be visually grounded in the actual scene

## CLIP Grounding Results

CLIP was run on 12 sampled frames from the same video.

Scores used top-3 average frame similarity.

| Description | CLIP Top-3 Score |
|---|---:|
| accurate_concise | 0.2525 |
| accurate_detailed | 0.2931 |
| bad_vague | 0.2335 |
| hallucinated | 0.1737 |

This fixed the hallucination problem:

- accurate detailed scored highest
- hallucinated scored lowest

## Corrected SceneTwin Scores

Final score:

```text
SceneTwinScore = normalized(TRIBE Score) * normalized(CLIP Score)
```

Results:

| Description | TRIBE | CLIP | TRIBE_n | CLIP_n | Final |
|---|---:|---:|---:|---:|---:|
| accurate_detailed | 0.7602 | 0.2931 | 0.9245 | 1.0000 | 0.9245 |
| accurate_concise | 0.7446 | 0.2525 | 0.8860 | 0.6599 | 0.5847 |
| bad_vague | 0.3850 | 0.2335 | 0.0000 | 0.5009 | 0.0000 |
| hallucinated | 0.7908 | 0.1737 | 1.0000 | 0.0000 | 0.0000 |

## What We Proved

The proof of concept shows:

1. TRIBE can produce comparable predicted cortical response maps for video and descriptions.
2. TRIBE-only cosine detects descriptive richness.
3. TRIBE-only cosine fails on vivid hallucinations.
4. CLIP visual grounding detects when the description does not match the actual video frames.
5. The combined SceneTwin score separates:
   - accurate detailed descriptions
   - accurate concise descriptions
   - vague low-information descriptions
   - vivid hallucinated descriptions

The strongest finding:

> TRIBE alone was fooled by a vivid hallucination. SceneTwin fixes this by requiring both predicted cortical alignment and visual grounding.

## What We Did Not Prove

Do not claim:

> Watching the video and hearing the description produce the same brain activity.

Better claim:

> TRIBE predicts partially overlapping cortical response patterns for video scenes and rich descriptions, but scene-specific fidelity requires an additional visual grounding signal.

Also do not claim:

> SceneTwin measures blind or low-vision users' real experience.

Better claim:

> SceneTwin is a scalable proxy metric for cross-modal semantic preservation that should complement, not replace, human accessibility testing.

## Current Best Framing

SceneTwin is no longer just:

> cosine similarity between video and description brain maps.

It is now:

> a two-stage audio-description fidelity metric combining predicted cortical alignment with visual grounding.

Best one-line explanation:

> SceneTwin asks whether an audio description both feels scene-like to a brain model and actually matches the scene on screen.

## Poster Story

The poster should show a failure-and-fix narrative:

1. Naive TRIBE cosine gives high score to vivid descriptions.
2. A hallucinated beach description fools TRIBE-only scoring.
3. CLIP grounding catches the visual mismatch.
4. Combined SceneTwin scoring ranks the accurate description highest and hallucination lowest.

This is stronger than pretending the first metric worked perfectly.

## Next Steps

1. Save the CLIP grounding code and corrected score table in the Colab notebook.
2. Generate a corrected bar chart comparing:
   - TRIBE-only score
   - CLIP grounding score
   - final SceneTwin score
3. Run the same experiment on 3-5 open clips, not just one.
4. Use a contrastive matrix:

```text
rows = videos
columns = descriptions
cell = SceneTwinScore(video_i, description_j)
```

5. Check whether the correct description ranks highest for each video.
6. Use 101 Dalmatians as the scientific validation reference after the open-clip prototype is stable.

## Three Gaps To Fill Before Submission

These are the three holes a skeptical NJBDA judge could poke in the current prototype.

### 1. Test Real AI-Generated Descriptions

Current limitation:

> All four descriptions in the first test were hand-written.

But the project pitch is about auditing AI-generated accessibility descriptions at scale. The next experiment needs actual model outputs.

Plan:

1. Use the same video clip.
2. Ask at least two systems to describe it:
   - Claude
   - GPT
   - optionally Gemini or a local vision-language model
3. Prompt them at multiple detail levels:
   - concise audio description
   - detailed audio description
   - accessibility-focused description
4. Score all outputs with:
   - TRIBE Brain Alignment
   - CLIP Visual Grounding
   - final SceneTwin Score

Best poster moment:

> If a real AI-generated description sounds good but misses or hallucinates scene details, and SceneTwin catches it, that becomes the strongest demo.

### 2. Add Baseline Metrics

Current limitation:

> We have not shown why SceneTwin is better than existing text metrics.

Baselines to test:

- BLEU
- ROUGE-L
- BERTScore
- CLIP-only
- TRIBE-only
- final SceneTwin Score

Important nuance:

BLEU, ROUGE, and BERTScore compare a candidate description to a reference text. They do **not** directly compare a description to the video. If the reference description is strong, these metrics may catch some hallucinations. But they still cannot answer the full SceneTwin question:

> Does this description preserve the original video scene in a cross-modal response space?

Fair baseline table:

| Metric | Uses video? | Uses predicted cortical response? | Catches vague? | Catches hallucinated? |
|---|---:|---:|---:|---:|
| BLEU | no | no | maybe | maybe |
| ROUGE-L | no | no | maybe | maybe |
| BERTScore | no | no | yes/no | maybe |
| CLIP-only | yes | no | maybe | yes |
| TRIBE-only | indirectly | yes | yes | no |
| SceneTwin | yes | yes | yes | yes |

Best poster claim:

> Existing text metrics evaluate similarity to a reference sentence. SceneTwin evaluates whether the description is both visually grounded and aligned with the video's predicted cortical response.

### 3. Add One Real fMRI Validation Point

Current limitation:

> TRIBE is a model. A judge may ask why its predicted maps should be trusted.

The 101 Dalmatians dataset is the best validation anchor because it contains real fMRI responses to naturalistic movie stimuli across sensory conditions.

Ideal validation:

1. Select one accessible stimulus segment from 101 Dalmatians.
2. Run TRIBE on the matching video/audio/text stimulus.
3. Compare TRIBE prediction to the real fMRI response or published derived maps.
4. Report a simple correlation or qualitative overlay.

Practical warning:

This is the hardest of the three because TRIBE outputs fsaverage5 cortical surface vertices, while the available 101 Dalmatians result files may be volumetric NIfTI maps in MNI space. Direct comparison may require surface/volume alignment and careful preprocessing.

Fallback if full validation is too slow:

> Cite TRIBE v2's own validation as the model-level justification, and use 101 Dalmatians as a domain-specific scientific anchor showing that movie/audio-description fMRI is a real measurable phenomenon.

Best version for the poster:

> We validate at two levels: TRIBE is validated as a brain-encoding model in prior work, and SceneTwin is stress-tested against accessibility-specific failure cases such as vague and hallucinated descriptions.

## Priority Order

For the fastest path to a strong poster:

1. **Run real AI-generated descriptions first.** This most directly supports the project pitch.
2. **Add baselines second.** This answers "why not just use existing metrics?"
3. **Attempt one fMRI validation point third.** High credibility, but highest implementation risk.

If time is limited before the abstract:

> Submit with the TRIBE+CLIP result and promise the AI-output/baseline/validation experiments as ongoing work for the poster.

## Useful Files

- Main project note: `wiki/research/scenetwin.md`
- Colab notebook: `/Users/adarsha/njbda/scenetwin_test.ipynb`
- CLIP cells: `/Users/adarsha/njbda/clip_cells.md`
- Current downloaded outputs:
  - `/Users/adarsha/Downloads/brain_video.png`
  - `/Users/adarsha/Downloads/brain_accurate_concise.png`
  - `/Users/adarsha/Downloads/brain_accurate_detailed.png`
  - `/Users/adarsha/Downloads/brain_bad_vague.png`
  - `/Users/adarsha/Downloads/brain_hallucinated.png`
  - `/Users/adarsha/Downloads/scenetwin_barchart.png`
  - `/Users/adarsha/Downloads/scenetwin_results.png`
  - `/Users/adarsha/Downloads/video_preds.npy`
