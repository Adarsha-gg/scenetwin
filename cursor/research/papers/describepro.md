# DescribePro — Collaborative Audio Description with Human-AI Interaction

**Source:** [arxiv_2508.01092.pdf](sources/arxiv_2508.01092.pdf) · [arXiv](https://arxiv.org/abs/2508.01092)

## Why they did it

Professional AD is high quality but slow. Fully automated AD is scalable but
flattens style, context, and editorial judgment. DescribePro is a collaborative
authoring system that gives describers AI-generated drafts, prompt-based edits,
manual edits, forking, tags, and multiple AD variations.

Study:

- 18 describers
- 9 professionals, 9 novices
- Participants edited AI-generated and human-written descriptions
- Average SUS usability score: 72.6

Key findings:

- AI drafts reduce blank-page/repetitive work.
- Professionals focus on clarity, tone, rhythm, and personal style.
- Novices focus on adding details and avoiding missing visual information.
- Forking/variations were especially valued.
- Tags can expose style, purpose, or focus and could let BLV users choose the
  kind of AD they want.

## What we agree with

- AD quality is partly editorial and stylistic. A single "best" reference AD is
  not a stable target.
- Versioning is not cosmetic. Forks and tags are a real product primitive for
  customization.
- The authoring workflow should distinguish novice, professional, and BLV modes.

## What we think is wrong / limited

1. **No BLV evaluation of revised outputs.** The strongest claim is about
   author experience, not viewer benefit.
2. **Timing is still conventional.** Their timing module uses silence,
   no-speech, and scene changes. That misses the neural/accessibility debt signal
   SceneTwin is building with TRIBE.
3. **Tags are under-specified.** Open-ended tags are useful for authors but can
   become incoherent for BLV selection unless grounded in a controlled taxonomy.

## If I were them

I would make tags operational:

- `objective`
- `cinematic`
- `instructional`
- `emotion/body-language`
- `spatial/layout`
- `on-screen-text`
- `shortest-sufficient`
- `deep-detail`

Then evaluate whether BLV users choose different tags by genre, task, and visual
acuity. I would also use model/metric signals to recommend which variations are
worth forking instead of showing a flat list.

## SceneTwin relevance

DescribePro makes the social-collision boundary concrete. If TRIBE says static
linear AD is the wrong surface, DescribePro shows the alternative surface:
multiple tagged variations and human-AI iteration.

SceneTwin should stop treating tier3/pro AD as the final answer. For collision
clips, it should produce a **variation pack**:

- concise default
- critical-state detail
- social/body-language detail
- on-screen text detail
- query-ready structured facts

## Proposed prototype

`cursor/methods/variation_pack_router.py`

Inputs:

- `social_collision_boundary`
- ADQA critical misses
- TRIBE need windows
- external category

Outputs:

- recommended variation tags
- whether a static AD track is enough
- whether to ask for human/pro review
- which existing description should be forked

Hypothesis: on external clips where pro AD is not best, tagged variation packs
will outperform one longer generated AD because the problem is preference and
context selection, not just missing words.
