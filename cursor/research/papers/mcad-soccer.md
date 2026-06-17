# MCAD — Multimodal Context-Aware Audio Description Generation for Soccer

**Source:** [arxiv_2511.09448.pdf](sources/arxiv_2511.09448.pdf) · [arXiv](https://arxiv.org/abs/2511.09448)

## Why they did it

MCAD moves automated AD beyond movies into sports, where the conditions are
worse for ordinary AD generation: fast cuts, dense commentary, crowd noise,
scarce quiet gaps, and no domain-specific AD training set. The paper fine-tunes
a VideoLLM on movie AD so it learns AD conventions, then injects soccer-specific
context at inference time:

- player identities
- teams/leagues
- soccer actions/events
- commentary transcription
- prior clips

They also propose ARGE-AD, a reference-free metric based on five AD guideline
features: names, actions/events, length, avoiding pronouns, and avoiding
commentary/subtitle overlap. They collect expert AD for roughly 100 ten-second
soccer clips.

## What we agree with

- Domain context matters. Sports AD cannot be scored like movie AD.
- Commentary overlap is a first-class failure. If the main audio already says
  it, AD should not echo it.
- Reference-free guideline checks are useful when multiple valid descriptions
  exist.

## What we think is wrong / limited

1. **ARGE-AD is too rule-like to be a quality metric.** Names, actions, and no
   pronouns are necessary conventions, but not sufficient for understanding.
2. **Commentary is treated mostly as input text.** It should also be a budget:
   dense commentary reduces when and how much AD can be delivered.
3. **No viewer-state model.** A fan tracking one player and a casual viewer
   trying to follow the ball need different descriptions.

## If I were them

I would split the sports problem into two policies:

- **What visual state is missing from commentary?**
- **Is there enough auditory room to say it now?**

The generator should only run after both policies pass. Otherwise it should
queue, summarize, or offer an optional replay/detail surface.

## SceneTwin relevance

MCAD is highly relevant to SceneTwin's external clip corpus because the project
already has speech density, need curves, and category labels. It suggests a new
domain-aware router:

```text
speech/commentary dense + high visual need + sports/action domain
  -> suppress echo
  -> describe only residual state: player, ball, event, score-impact
```

It also adds an evaluation idea: measure how much candidate AD overlaps with the
existing audio transcript. That is more product-relevant than another semantic
similarity score.

## Proposed prototype

`cursor/methods/commentary_residual_ad.py`

Inputs:

- transcript or ASR commentary
- frame/action detections
- category/domain label
- need curve and speech density
- candidate AD text

Outputs:

- `audio_overlap_penalty`
- `residual_visual_state`
- `safe_to_speak_now`
- `queue_for_replay`

Hypothesis: on sports/action clips, residual AD beats longer AD because it avoids
describing what commentary already covers.

## Prototype status

Implemented and run on the 58 external clips:

- `cursor/methods/output/commentary_residual_ad.csv`
- `cursor/methods/output/commentary_residual_ad_summary.json`
- `cursor/findings/commentary-residual-proxy.md`

Caveat: no real ASR transcripts are present yet, and a YouTube auto-caption
fetch attempt hit HTTP 429. Current rows use `audio_context_source =
tier_summary_proxy`, so this validates the residual routing mechanics but not
the true commentary-overlap claim.
