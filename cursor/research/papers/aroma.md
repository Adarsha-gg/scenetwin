# AROMA

Source: `sources/arxiv_2507.10963.pdf`
arXiv: 2507.10963
Date read: 2026-05-27

## Why they did it

Cooking videos contain rich audiovisual information, but real cooking state is
multisensory. BLV cooks rely on touch, smell, sound, taste, memory, and kitchen
layout. A video recipe cannot know whether the user's actual onions, sauce, pan,
or dough match the demonstrated state unless the system bridges video evidence
with the physical environment.

## System

AROMA is a mixed-initiative cooking assistant that grounds three streams:

- user-provided non-visual cues
- wearable first-person camera feed
- structured video recipe knowledge

It supports:

- on-demand user questions
- proactive monitoring
- alerts when the current physical state diverges from the video recipe
- replaying relevant recipe segments
- guidance that incorporates smell/touch/taste descriptions supplied by the user

## Evidence

The paper evaluates AROMA with 8 BLV participants in their own kitchens. The
study emphasizes realistic cooking constraints and shows participants using the
system to maintain procedural flow, ask what to do next, compare their current
state against the recipe, and combine AI feedback with their embodied
non-visual strategies.

Important design pressure:

- proactive feedback was useful when precise and timely
- poorly timed alerts were frustrating
- users intentionally adapt recipes, so deviation is not always an error
- BLV sensory knowledge is not a fallback; it is part of the evidence model

## First-principles challenge

AROMA goes further than Vid2Coach on agency. It says the user is not a passive
executor of video instructions. The user owns sensory evidence the AI does not
have.

The correct representation is therefore:

```text
task state = video demonstration + camera state + user non-visual report
```

If the AI treats every mismatch as a mistake, it undermines autonomy.

## What I would do if I were them

Add an explicit deviation model:

- accidental deviation
- deliberate adaptation
- safe substitution
- unsafe divergence
- unknown, ask user

Then make proactive alerts consent-aware and reversible.

## Relevance to SceneTwin

SceneTwin should separate ordinary how-to clips from **reality-video alignment**
clips: cases where the useful product is not a better video description but a
loop comparing the viewer's current physical state to the source video.

Implemented proxy:

- `cursor/methods/task_assistant_affordance.py`

The `reality_video_task_coach` mode marks clips needing:

```text
step_index + completion_criteria + wearer_camera + nonvisual_user_cues
```

## Correlation to test

```text
cooking/task state cues + weak grounding
  vs
need for current-state monitoring and user-reported sensory cues
```

This is an access product that SceneTwin can help route but cannot solve with
video-only scoring.
