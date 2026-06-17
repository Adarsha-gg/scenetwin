# FocusedAD — Character-Centric Movie Audio Description

**Source:** [arxiv_2504.12157.pdf](sources/arxiv_2504.12157.pdf) · [arXiv](https://arxiv.org/abs/2504.12157)

## Why they did it

FocusedAD attacks a failure that generic video captioners hide: movie AD is often
about **who** did the action, not only what happened. The system builds a
character-centric pipeline with:

- a Character Perception Module for tracking active character regions
- a character query bank built from cast images
- a Dynamic Prior Module using prior AD and subtitles
- a Focused Caption Module that attends to character regions, scene tokens, and
  text context

Their ablation shows that injecting character names matters. On MAD-eval-Named,
the full model reports SPICE 7.4, METEOR 8.1, and BERTScore 57.7, better than
versions without character names or without the focused region module.

## What we agree with

- Character identity is an access primitive. "A man walks away" and "Max walks
  away" can carry completely different narrative value.
- Prior AD and subtitles are not extra context; they are the memory layer needed
  to keep a viewer oriented.
- Redundancy is a real AD failure. Object inventory is often less useful than
  named, plot-relevant action.

## What we think is wrong / limited

1. **Movie-specific identity assumptions leak into the method.** IMDb/cast banks
   work for films, but not for arbitrary web clips, livestreams, education, or
   user-uploaded social video.
2. **The evaluation is still reference-bound.** Better SPICE/METEOR does not
   prove the character mention was the one a BLV viewer needed at that moment.
3. **Identity confidence is not surfaced.** A wrong name is worse than a generic
   noun; the product should expose uncertainty.

## If I were them

I would make character naming a **memory service** with confidence levels:

- known recurring identity
- visually similar but uncertain
- role-only identity
- first mention needed
- do-not-name because evidence is weak

The AD generator should consume that state, but the viewer/creator interface
should also see it.

## SceneTwin relevance

FocusedAD gives SceneTwin a missing leg for social and narrative clips. The
current social-collision boundary says when static AD is likely the wrong
surface. FocusedAD says one reason why: social clips fail when the system loses
identity and relation state.

This should connect to ADQA miss types. If critical questions ask "who", "which
person", or "relationship", the router should choose identity memory or creator
verification rather than simply adding longer prose.

## Proposed prototype

`cursor/methods/character_identity_memory.py`

Inputs:

- frame/person crops
- transcript/subtitles
- prior AD or previous generated descriptions
- ADQA critical questions containing people/relationship terms

Outputs:

- `identity_state`
- `identity_confidence`
- `first_mention_needed`
- `unsafe_to_name`

Hypothesis: identity memory will explain a meaningful slice of social-collision
clips where pro AD is not best by generic CLIP grounding.
