# Guiding MLLMs with BLV Visual Questions

Source: `sources/arxiv_2510.01576.pdf`  
arXiv: 2510.01576  
Date read: 2026-05-27

## Why they did it

Current MLLM visual interpretation apps often answer with a broad, lengthy
description. That is inefficient for BLV users because the real need is often a
specific latent question: read this label, identify this product, explain this
control, or say whether a visual condition holds.

The paper asks whether historical BLV visual questions can guide a model to
anticipate the user's likely information need without requiring the user to type
extra context.

## Method

They use VizWiz-LF image-question-answer pairs:

- 491 pairs as a context retrieval set
- 92 pairs as the test set
- multimodal embeddings with top-k retrieval (`k=4`)
- Gemini 2.5 Pro using a Be My AI-style prompt

For each test image, they compare:

- context-free visual interpretation
- context-aware interpretation guided by similar historical BLV questions

## Key results

- Context-aware accuracy: 76.1%
- Context-free accuracy: 63.0%
- Context-aware descriptions anticipated the hidden user question in 15.2% of
  cases where the baseline did not.
- Human labelers preferred context-aware responses in 54.3% of comparisons.
- Context-free responses were still preferred in 20.7%, usually when broader
  scene context was better than targeted focus.

## First-principles challenge

This paper is right that "question prior" is a missing variable. A visual scene
does not imply one description; it implies a distribution over likely user
questions.

But equal-weight top-k retrieval is too weak. It assumes visually similar images
produce equally useful questions. In practice, the useful prior depends on:

- user goal
- location/task context
- risk level
- whether text/labels are present
- whether the user is consuming video, navigating, cooking, or inspecting an
  object

Also, the benchmark is image-based and small. SceneTwin needs this idea over
time-indexed video states, not one still image.

## What I would do if I were them

Turn question retrieval into a calibrated policy:

```text
P(question type | visual state, audio state, user goal, history)
```

Then expose only the top one or two question chips when the expected utility
beats interaction cost. The output should not always be a longer answer; often
it should be a small prompt like:

```text
Likely useful: ask who changed position, ask what text is visible, ask what step
is happening now.
```

## Relevance to SceneTwin

This strengthens the Access Surface OS direction. SceneTwin should not merely
route to `identity_chip` or `detail_chip`; it should attach the likely question
that surface exists to answer.

Implemented proxy:

- `cursor/methods/visual_assistant_skill_policy.py`

This adds `question_prior` and `proactive_question_chip` to the 58 external
clips.

## Correlation to test

```text
question_prior_confidence + social_collision_boundary
  vs
user follow-up demand / pro-not-best external labels
```

If the correlation holds, SceneTwin can become a proactive question-prior engine,
not just an AD metric.
