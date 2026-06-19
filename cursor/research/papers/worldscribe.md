# WorldScribe — Context-Aware Live Visual Descriptions

**Source:** [worldscribe_uist2024.pdf](sources/worldscribe_uist2024.pdf) · [arXiv](https://arxiv.org/abs/2408.06627)

## Why they did it

WorldScribe studies live visual description for BLV users. Its core argument is
that live description cannot be a stream of generic captions. It must adapt to:

- user intent
- visual context
- sound context
- latency

The system lets users specify intent, generates object/attribute descriptions,
prioritizes by relevance and proximity, then adapts presentation around sound
events such as speech or ringtone-like audio. Their studies found that users
liked dynamic granularity and customized attributes, but remained skeptical
about hallucinations, omissions, camera aiming, and high-stakes navigation.

## What we agree with

- Intent is the correct live-access primitive. "Describe the scene" is too vague
  for real-time use.
- Sound context is part of the output policy. A live system should know when to
  pause, raise volume, shorten, or avoid interrupting.
- Latency is not a backend detail. Richness and timeliness trade off directly.

## What we think is wrong / limited

1. **Intent is still too static.** In real use, intent changes as the viewer
   learns the scene. The system needs memory and intent revision.
2. **Accuracy is treated as a known risk, not a routing variable.** If the model
   is uncertain, the description policy should change.
3. **Live navigation is under-separated from live awareness.** The paper is
   careful about high-stakes navigation, but the product boundary should be
   explicit: awareness, not safety-critical guidance.

## If I were them

I would make the live agent maintain an access state:

- current user intent
- known scene entities
- unresolved visual questions
- recent audio interruptions
- model uncertainty
- latency budget

Descriptions would then be emitted only when they reduce uncertainty enough to
justify interrupting the user's audio environment.

## SceneTwin relevance

WorldScribe gives SceneTwin the live-mode version of the same first-principles
idea:

```text
description is a policy decision, not a caption string
```

For stored clips, SceneTwin can choose between static AD, concise cues,
detail-on-request, and object exploration. For live clips, it can choose between
pause, speak, shorten, ask for intent, or wait.

The new 58 external clips strengthen this use case because many are speech-dense
social or instructional videos. A live policy must account for speech density
and visual need together; caption quality alone is not enough.

## Proposed prototype

`cursor/methods/context_aware_description_policy.py`

Inputs:

- user intent
- speech density and non-speech audio events
- TRIBE/proxy visual need
- object/person/action salience
- latency budget

Outputs:

- `emit_now`
- `description_granularity`
- `presentation_action`
- `ask_user_intent`
- `defer_reason`

Hypothesis: SceneTwin's most novel product use case is a policy engine that
decides **whether, when, and on which surface** visual information should be
delivered.
