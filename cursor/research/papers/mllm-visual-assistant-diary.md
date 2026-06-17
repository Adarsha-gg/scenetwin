# MLLM Visual Assistant Diary Study

Source: `sources/arxiv_2602.13469.pdf`  
arXiv: 2602.13469  
Date read: 2026-05-27

## Why they did it

Benchmarks say MLLMs can describe images well, but BLV users use visual
interpretation apps in messy daily contexts: reading labels, checking safety,
locating objects, preparing food, confirming appearance, and asking follow-up
questions.

The paper studies real use over two weeks with 20 BLV participants, collecting
551 diary entries from an MLLM-enabled visual interpretation app.

## Key results

- Initial photo descriptions were strong: mean 2.91/3, with 91.8% receiving the
  highest no-hallucination score.
- Users were somewhat satisfied: mean 4.13/5.
- Users rated outputs as trustworthy: mean 3.76/5.
- Participants opened follow-up conversations in 375 of 551 entries: 68.1%.
- They asked 626 total questions.
- Follow-up answers were much weaker: 122 of 549 responses contained false
  information (22.2%).
- Text and graphics requests were especially risky: 54 of 156 contained false
  information (34.6%), and 28 of 156 abstained (17.9%).

## Their core concept

They define a "visual assistant" skill beyond captioning. The nine behaviors are:

- neutral factual communication
- adaptive communication protocols
- goal-oriented collaboration
- content quality guidance
- comprehensive information provision with caveats
- contextual self-awareness
- privacy protection
- transparent uncertainty handling
- graceful handoff

## First-principles challenge

This paper breaks the assumption that "better captioning" equals "better visual
assistance."

Captioning is a one-turn perception task. Visual assistance is a multi-turn
task under uncertainty, privacy, and action consequences. The failure mode is not
only hallucination; it is overconfident helpfulness in situations where the user
cannot cheaply verify the answer.

The sharpest result is the gap:

```text
initial description accuracy is high
follow-up answer reliability is materially worse
```

That means SceneTwin should not only score generated descriptions. It needs to
score whether a system is safe to continue into a conversational assistant mode.

## What I would do if I were them

Separate the model into explicit modes:

- describe
- ask user goal
- verify before answer
- guide camera capture
- answer with uncertainty
- hand off to human / safer source

Then evaluate the mode decision, not only the final text.

## Relevance to SceneTwin

This creates a new axis for the Access Surface OS:

```text
caption quality != assistant readiness
```

Implemented proxy:

- `cursor/methods/visual_assistant_skill_policy.py`

It adds `verify_before_answer` for text/spatial/safety-like situations with weak
grounding, and `plain_description_target_misses` to measure where plain AD is
probably underpowered.

## Correlation to test

```text
hallucination_sensitive + weak grounding margin
  vs
pro-not-best labels and user trust loss
```

The next dataset should collect user follow-up labels, not only caption
preferences.
