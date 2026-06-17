# Vid2Coach

Source: `sources/arxiv_2506.00717.pdf`  
arXiv: 2506.00717  
Date read: 2026-05-27

## Why they did it

How-to videos are visually dense. BLV users may hear narration but still miss
demonstrated hand motion, completion criteria, tool placement, and visual
progress. The paper observes vision rehabilitation therapists (VRTs) because
they are the closest expert model for teaching BLV users new physical skills.

## System

Vid2Coach transforms a how-to video into a wearable-camera task assistant:

- segments video into high-level steps
- augments narration with demonstration details
- extracts tools, materials, mistake criteria, and completion criteria
- retrieves BLV-specific workarounds with RAG
- monitors user progress through smart-glasses video
- gives proactive feedback and answers questions
- suggests moving on when completion criteria appear satisfied

## Evidence

The formative study used 3 VRTs and 3 BLV participants. VRTs did not merely
describe visuals; they rewrote recipes, added workarounds, converted visual
criteria into non-visual cues, monitored progress, and adapted to skill level and
kitchen setup.

In the user study with 8 BLV participants:

- Vid2Coach users made 58.5% fewer mistakes than their usual workflow.
- 5 participants using Vid2Coach completed the task, compared with 1 in the
  baseline condition.
- Participants reported lower cognitive load and valued step granularity,
  workarounds, and hands-free feedback.

## First-principles challenge

This paper breaks the "video access = watching" assumption. In how-to contexts,
access means successful action.

The required unit is not a caption:

```text
step state + completion criteria + current user state + safe workaround
```

A beautiful description of a cooking step can still fail if it does not tell the
user whether their own pan, knife, ingredient, or shape is currently correct.

## What I would do if I were them

Model task guidance as a dependency graph:

- core steps that cannot be skipped
- optional/parallelizable steps
- visible completion criteria
- non-visual alternatives
- safety-critical interventions

Then evaluate task success and error recovery, not description preference.

## Relevance to SceneTwin

SceneTwin should identify clips where static AD should be replaced with a task
coach affordance:

```text
step_index + completion_criteria + progress_feedback
```

Implemented proxy:

- `cursor/methods/task_assistant_affordance.py`

The `stepwise_task_coach` mode marks clips where the access problem is executing
or tracking a task, not understanding a scene.

## Correlation to test

```text
how-to/task terms + need/speech conflict
  vs
pro-not-best labels and task-following errors
```

The real validation target should be physical-task error rate, not caption
ranking.
