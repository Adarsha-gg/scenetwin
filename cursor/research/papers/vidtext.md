# VidText

Source: `sources/arxiv_2505.22810.pdf`  
arXiv: 2505.22810  
Date read: 2026-05-27

## Why they did it

Video understanding benchmarks often underweight text in the scene: signs,
subtitles, labels, scoreboards, menus, captions, app screens, and other written
context. Static OCR benchmarks do not cover the temporal and multimodal setting.
VidText fills that gap with a video-text benchmark.

## Benchmark

VidText spans multilingual video text and evaluates eight tasks:

- holistic OCR
- holistic reasoning
- local OCR
- local reasoning
- text localization
- temporal causal reasoning
- text tracking
- spatial reasoning

The benchmark intentionally covers video-level, clip-level, and instance-level
understanding. That matters because a model can read one frame and still fail to
track where text appeared, how it changed, or what it meant in context.

## Evidence

The authors evaluate 18 large multimodal models. Their central result is that
current models are far below human performance: the reported human average is
89.5 percent, while all evaluated models remain substantially lower. The paper
also reports that all video multiple-choice reasoning tasks are below 60 percent
accuracy.

The ablations point to a practical lesson: resolution, OCR capability, language
backbone, auxiliary OCR/transcript information, and chain-of-thought prompting
all matter.

## First-principles challenge

For accessibility, missing text is not a small caption error. Text often carries
the actual state:

```text
scoreboard, warning label, street sign, price, username, timer, dosage, setting
```

A model that sees "a person cooking" but misses "medium heat for 5 minutes" has
failed the useful part of the scene.

The first-principles issue is that visual text is a separate sensor channel. It
should not be compressed into generic image embeddings and hoped for.

## What I would do if I were them

I would make the benchmark answerability-focused:

- require each answer to identify the text span or frame evidence
- score whether OCR evidence was sufficient for the final answer
- include "no reliable OCR evidence" as a valid output

That would make it closer to a production contract for BLV assistance.

## Relevance to SceneTwin

SceneTwin should attach an OCR sidecar whenever text terms, overlays, or
hallucination-sensitive categories appear. The router should not ask an LMM to
answer from pixels alone when scene text is likely decisive.

Implemented proxy:

- `cursor/methods/evidence_sidecar_readiness.py`

The proxy marks 28 of 58 external clips as needing a video-text/OCR sidecar.

## Correlation to test

```text
video_text_ocr_required
  vs
ADQA misses involving labels, signs, score, UI, subtitles, or written objects
```

If strong, OCR becomes a first-class evidence sidecar for SceneTwin rather than a
fallback detail in prompts.
