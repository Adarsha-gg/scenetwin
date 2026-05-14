---
title: "SceneTwin Neural Need Visual Validation"
category: research
tags: [SceneTwin, TRIBE, validation, audio-description, timing]
created: 2026-05-02
updated: 2026-05-02
sources:
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_need_validation/
  - wiki/research/scenetwin-neural-description-need-pivot.md
---

# SceneTwin Neural Need Visual Validation

## Verdict

The two-clip visual check supports the pivot enough to justify a 20-clip `P_AV`/`P_A` run, but it is not a clean win yet.

This does **not** prove the metric is validated. It shows that, on the two clips we already processed, the curve is not random:

- clip 00: high need appears in silent visual-action windows, so standard AD slots are plausible.
- clip 01: high need appears during dense eating/speech action, so the model correctly surfaces an extended/integrated AD problem instead of pretending there is room for ordinary narration.
- clip 01 also shows a likely weakness: the later Burger King sign/title-card frames are only moderate/low need (`7.4-9.2s`, need `0.14-0.34`). A human describer might still want to describe that visual text. This means the metric probably needs an OCR/text-on-screen detector or a separate VLM saliency layer.

## Evidence

| clip    | sheet                                                        | top_windows                                                                                    | judgment                                                                                                                                                                                                           |
|:--------|:-------------------------------------------------------------|:-----------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| clip_00 | output/scenetwin_need_validation/clip_00_need_validation.jpg | 7.2-8.1s need=0.78 speech=0.00; 0.0-0.9s need=0.65 speech=0.00; 5.4-6.3s need=0.61 speech=0.00 | High-need windows are mostly silent visual-action windows. This is the behavior we want for standard AD timing: the curve finds places where there is visual change but no dialogue competing for narration.       |
| clip_01 | output/scenetwin_need_validation/clip_01_need_validation.jpg | 0.9-1.8s need=1.00 speech=0.62; 0.0-0.9s need=0.71 speech=0.60; 1.8-2.8s need=0.64 speech=0.87 | Highest-need windows overlap dense speech. This is useful because the curve does not pretend a clean narration slot exists; it flags that the clip likely needs extended/integrated AD or a post-dialogue summary. |

## Manual Inspection Notes

### clip 00

This looks genuinely promising. The curve marks:

- `0.0-0.9s`: visual setup of the chef holding/gesturing with the tomato, before the spoken countdown starts.
- `5.4-6.3s`: the chef turns and prepares/executes the key action.
- `7.2-8.1s`: the camera lands on the wall/door area where the visual result of the throw appears.

Those are exactly the kinds of silent visual-action windows where standard AD can fit.

### clip 01

This is useful but less clean.

The curve marks `0.0-2.8s` as high-need while speech density is high. Visually, the clip is a close-up eating challenge/action sequence while the soundtrack contains dialogue/crowd speech. That is a legitimate "extended/integrated AD" case: the important visual action is happening while there is not a clean narration slot.

But the later sign/title-card frames around `7.4-9.2s` are only moderate/low need. If those words are visually important, TRIBE alone may miss them because text-on-screen is a symbolic/OCR problem, not just a broad audiovisual brain-response gap. Add an OCR or VLM text-detection feature before claiming full AD need coverage.

## Interpretation

This is a better TRIBE use case than text scoring because it only compares the same clip under two conditions:

```text
P_AV = audiovisual scene
P_A = audio-only scene
AccessibilityGap(t) = distance(P_AV[t], P_A[t])
```

The content of the description should still be generated and checked with VLM/CLIP/SigLIP/PAC-S. TRIBE's role is timing and need estimation.

## Next Test

Run all 20 clips for only:

- `P_AV`
- `P_A`
- speech transcript / density

Then create validation sheets and compare top windows against human judgment: should this moment need AD, and is it standard or extended?

Add explicit failure-mode checks:

- visual text / signs / title cards
- faces and expressions
- small object manipulations
- silent camera pans / scene changes
- high-action moments under dialogue
