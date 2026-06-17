# VideoMind

Source: `sources/arxiv_2503.13444.pdf`  
arXiv: 2503.13444  
Date read: 2026-05-27

## Why they did it

Long-video reasoning fails when a single model is asked to plan, localize,
verify, and answer in one pass. VideoMind makes those roles explicit and uses an
agentic workflow for temporal-grounded video reasoning.

## System

VideoMind uses four roles:

- planner: decides which role to call
- grounder: localizes relevant video moments
- verifier: checks candidate moments
- answerer: produces the response using the grounded segment or whole video

The Chain-of-LoRA mechanism lets one backbone switch role adapters during
inference instead of loading separate full models.

## Evidence

The paper evaluates across 15 public benchmarks covering grounded VideoQA,
temporal grounding, and general VideoQA. It reports that VideoMind-2B
outperforms GPT-4o and Gemini-1.5-Pro on several long-video benchmarks, and that
the verifier gives a consistent 3.2 mIoU gain on Charades-STA. The planner also
helps by deciding whether grounding is needed before answering.

The deeper result is not the exact leaderboard position. It is the causal chain:
better moment selection improves downstream answering.

## First-principles challenge

SceneTwin should not treat "answer the user" as one model call. The minimum
contract is:

```text
plan -> retrieve evidence -> verify evidence -> answer or abstain
```

This is especially true for pro-not-best social clips, where the hard part is
often locating the reaction, identity relation, visual contradiction, or subtle
context that the audio does not carry.

## What I would do if I were them

I would add a refusal/verdict role:

- evidence sufficient
- evidence ambiguous
- evidence missing
- answer requires human/community context

That turns VideoMind from a reasoning agent into an answerability agent.

## Relevance to SceneTwin

VideoMind is the backbone pattern for SceneTwin's evidence loop. The router
should output a planner/grounder/verifier requirement whenever the clip is
high-risk, weak-margin, collision-heavy, or query-driven.

Implemented proxy:

- `cursor/methods/evidence_sidecar_readiness.py`

The proxy marks 49 of 58 external clips as needing a planner-grounder-verifier
sidecar.

## Correlation to test

```text
planner_grounder_verifier_required
  vs
follow-up pressure, weak pro margin, social collision, and hallucinated answers
```

If this holds, SceneTwin should present many answers as evidence-backed agents,
not one-shot generated descriptions.
