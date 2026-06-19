# StreetReaderAI

Source: `sources/arxiv_2508.08524.pdf`
arXiv: 2508.08524
Date read: 2026-05-27

## Why they did it

Street View-style tools are visually immersive but inaccessible to blind users.
This blocks remote route planning, destination preview, entrance finding,
landmark inspection, and virtual exploration.

StreetReaderAI turns streetscape imagery into a context-aware conversational map
with accessible navigation controls.

## System

StreetReaderAI combines:

- Street View imagery
- contextual geographic metadata
- accessible movement/panning controls
- AI descriptions
- AI chat
- voice/screen-reader interaction
- movement commands such as turn left/right and move forward/back

The system distinguishes description from navigation. Users can ask questions,
move through panoramas, inspect POIs, and build a spatial mental model.

## Evidence

The study involved 11 blind participants.

Reported signals:

- all 11 completed POI investigations
- 10 of 11 completed at least one open-world navigation task
- participants moved through 356 panoramas
- they made 568 movements
- they used AI 1,053 times
- spatial orientation was a major question category
- participants valued route planning and destination preview

The paper also surfaces core risks:

- users must maintain a mental model of virtual movement
- panoramic imagery can be stale
- spatial orientation from MLLMs is not yet robust enough
- command/control and description must be tightly coupled

## First-principles challenge

This paper breaks the assumption that spatial access can be delivered as prose.
Spatial access is interaction over a coordinate system.

The useful unit is:

```text
location + heading + movement graph + landmarks + uncertainty
```

Without that, a description can sound useful while leaving the user disoriented.

## What I would do if I were them

Make every answer spatially grounded:

- current panorama ID
- heading
- movement edge
- landmark reference
- image age
- confidence in direction

Then audit answerability separately for static POI questions and route-rehearsal
questions.

## Relevance to SceneTwin

SceneTwin should treat spatial/navigation clips as requiring an orientation
state, not just a `detail_chip`.

Implemented proxy:

- `cursor/methods/task_assistant_affordance.py`

The `route_or_spatial_rehearsal` mode marks clips needing:

```text
geospatial_context + orientation_state + depth_or_obstacle_guard
```

## Correlation to test

```text
navigation/spatial terms + depth_guarded_guidance
  vs
wrong or insufficient orientation answers
```

This pairs directly with GuideDog: GuideDog supplies the depth/obstacle standard;
StreetReaderAI supplies the interactive spatial control loop.
