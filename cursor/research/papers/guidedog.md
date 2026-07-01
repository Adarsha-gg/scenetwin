# GuideDog

Source: `sources/arxiv_2503.12844.pdf`
arXiv: 2503.12844
Date read: 2026-05-27

## Why they did it

BLV navigation needs are not generic scene captioning. A safe assistant must
orient the user, identify hazards, and summarize direction using intuitive
spatial references.

GuideDog builds a real-world egocentric dataset and benchmark for
accessibility-aware guidance.

## Dataset

- 22,084 image-description pairs
- 2,106 human-verified gold labels
- 269 source walking videos
- 291 hours of source footage
- 183 cities across 46 countries
- GuideDogQA: 818 QA samples
- 435 object recognition questions
- 383 relative depth questions

The standards:

- S1: describe surroundings
- S2: provide obstacle information
- S3: provide summary and direction

Their construction pipeline shifts annotation from free-form generation to
AI-generated silver labels plus human verification.

## Key results

GuideDogQA shows a split:

- Open-source models can do object recognition surprisingly well.
- Depth comparison remains weak.
- GPT-4o leads depth comparison at 67.1 and object recognition at 74.7.
- Gemini 2.0 Flash gets 53.0 depth and 65.7 object recognition.
- Qwen2.5-VL fine-tuning improves depth from 22.2 to 41.5 while keeping object
  recognition high at 83.9.

Human evaluation on standard adherence:

- GPT-4o: average 3.90/5
- Gemini 2.0 Flash: average 3.60/5
- fine-tuned Qwen2.5-VL: average 3.59/5
- filtered silver labels: average 4.63/5

Obstacle information (S2) is hardest, consistent with the depth results.

## First-principles challenge

This paper breaks another hidden assumption:

```text
object presence is not enough for assistance.
relative depth and actionability are the hard parts.
```

For SceneTwin, this means spatial descriptions should not be treated as normal
caption tokens. A wrong "near/far/left/right/ahead" claim can be worse than
omitting detail.

## What I would do if I were them

Split guidance into two confidence channels:

- semantic confidence: what object is present
- spatial confidence: where it is, how far, and whether it is actionable

Then forbid high-stakes guidance unless spatial confidence clears a stricter
threshold or a human/verified sensor confirms it.

## Relevance to SceneTwin

GuideDog adds a safety gate to Access Surface OS:

```text
spatial/depth guidance is not just another description surface
```

Implemented proxy:

- `cursor/methods/visual_assistant_skill_policy.py`

The `depth_guarded_guidance` mode marks clips where a response should require
depth/object/spatial verification before giving directional guidance.

## Correlation to test

```text
depth_guarded_guidance + weak margin
  vs
wrong spatial/detail answers and user safety risk
```

The next hard prototype should add an object/depth sidecar for external clips and
measure whether spatial confidence is independent from CLIP/text grounding.
