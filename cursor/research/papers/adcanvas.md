# ADCanvas — Accessible Audio Description Authoring for BLV Creators

**Source:** [arxiv_2602.07266.pdf](sources/arxiv_2602.07266.pdf) · [arXiv](https://arxiv.org/abs/2602.07266)

## Why they did it

ADCanvas targets a different user than most AD generation papers: BLV creators
who want to author, inspect, and revise descriptions themselves. Existing AD
authoring tools rely on visual timelines and waveforms, so the paper builds a
conversational authoring environment with keyboard playback, screen-reader
friendly plain-text editing, VQA, script generation, and script modification.

In the 12-person study, participants acted less like passive recipients of AI
output and more like directors or curators. They wanted AI help, but they also
wanted verification, uncertainty, multiple candidates, and configurable levels
of automation.

## What we agree with

- BLV users are not only consumers. A serious SceneTwin product should support
  BLV authoring and review, not just automatic caption generation.
- Trust is an interaction design problem. The paper's "trust but verify" result
  is more useful than another automatic quality score.
- The interface needs modes. Suggest-only, verification-required, and automatic
  generation are distinct authoring contracts.

## What we think is wrong / limited

1. **The paper under-measures model failure.** It notes verification burden but
   does not build a systematic accuracy benchmark around that burden.
2. **Conversation is not enough.** Professional editing also needs dense state:
   gaps, timing, audio ducking, narration length, candidate versions, and
   unresolved uncertainties.
3. **The agent boundary is underspecified.** The key product question is not
   "can AI write AD?" It is "which claims may the AI commit without human
   confirmation?"

## If I were them

I would make every generated sentence carry a verification state:

- grounded in frame evidence
- inferred from audio
- uncertain
- user-confirmed
- contradicted by another model or frame

Then the BLV creator can edit the script as a fact graph, not a blob of prose.

## SceneTwin relevance

ADCanvas turns SceneTwin from evaluator into authoring QA. The current project
already has ADQA, CLIP grounding, TRIBE/proxy need, and external clip artifacts.
Those can become a verification layer inside an authoring tool:

```text
sentence -> evidence frames -> audio support -> timing slot -> risk label
```

This is a more defensible use case than "generate the best AD." SceneTwin can
show creators where the generated AD is unsupported, too long for the gap, or
likely to miss a critical question.

## Proposed prototype

`cursor/methods/blv_authoring_agent_qc.py`

Inputs:

- candidate AD script
- frame evidence
- audio transcript/caption
- need curve and gap timing
- ADQA critical questions

Outputs:

- `claim_grounding_status`
- `verification_queue`
- `candidate_revision`
- `automation_level_recommendation`

Hypothesis: the highest-value BLV creator feature is not generation; it is a
screen-reader accessible uncertainty and verification queue.
