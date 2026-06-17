# SPICA — Spatial Interactive Captioning

**Source:** [arxiv_2402.07300.pdf](sources/arxiv_2402.07300.pdf) · [arXiv](https://arxiv.org/abs/2402.07300)

## Why they did it

SPICA argues that static audio descriptions omit too much spatial detail and
force BLV viewers to hold a heavy mental model. The system adds two layers on
top of ordinary video access:

- temporal navigation over frame captions
- spatial exploration of objects inside selected key frames

The paper evaluates object detection/description quality and runs a 14-person
BLV user study. The reported object label precision is high, recall is lower,
and object-level descriptions outperform a baseline. Participants rated the
system useful and easy to use, with improved understanding and immersion.

## What we agree with

- Layering is the right abstraction. A static AD track should not carry every
  object; optional spatial detail belongs behind a deliberate interaction.
- Object exploration solves a different problem from caption scoring. It answers
  "what else is here?" rather than "is this sentence close to the reference?"
- Spatial audio can encode layout without forcing more words into the dialogue
  gap.

## What we think is wrong / limited

1. **Object detection is not access priority.** A detected object is not
   necessarily worth describing. SceneTwin needs a priority function over
   narrative role, user intent, and timing.
2. **The study is short-video oriented.** Long videos need memory: which objects
   were already introduced, which changed state, and which are newly relevant.
3. **The interface can become a second task.** Exploration is valuable when the
   viewer asks for it, but harmful if the system pushes too much inventory.

## If I were them

I would replace "object list" with "object affordance map." Each object should
carry:

- visual salience
- narrative salience
- whether it is audio-obvious
- whether it changed since last mention
- whether the user has shown interest in that class

The product should then expose the highest-value objects first and leave the
full inventory searchable.

## SceneTwin relevance

SPICA gives SceneTwin the surface for cases where TRIBE says there is visual
debt but CustomAD-style lengthening would collide with speech. Instead of a
longer sentence, route to:

```text
concise default AD + optional object explorer
```

This is especially relevant for the new external clips with dense speech and
many social/environmental details. A linear description cannot mention every
face, prop, gesture, and room detail without stepping on the soundtrack.

## Proposed prototype

`cursor/methods/layered_object_explorer.py`

Inputs:

- key frames from `cursor/data/external_clips/frames`
- object/region captions from a local or API VLM
- SceneTwin need curve and speech density
- ADQA critical miss nouns

Outputs:

- `base_caption`
- `optional_object_chips`
- `spatial_priority_score`
- `already_audio_obvious`

Hypothesis: object exploration should be triggered by residual visual questions,
not by object count alone.
