# Task Assistant Affordance Probe

Date: 2026-05-27

## Why this exists

The latest papers shift the project again:

```text
video access is sometimes not watching or asking.
it is doing, planning, aligning, or contributing.
```

Vid2Coach and AROMA turn how-to videos into task assistants. StreetReaderAI turns
street imagery into route rehearsal and POI investigation. CoSight turns viewer
comments into a community evidence layer.

`cursor/methods/task_assistant_affordance.py` maps those ideas onto the 58
external clips.

## Outputs

- `cursor/methods/output/task_assistant_affordance.csv`
- `cursor/methods/output/task_assistant_affordance_summary.json`

## Affordances

| Affordance | Evidence/action loop |
|------------|----------------------|
| `reality_video_task_coach` | step index + completion criteria + wearer camera + nonvisual user cues |
| `stepwise_task_coach` | step index + completion criteria + progress feedback |
| `route_or_spatial_rehearsal` | geospatial context + orientation state + depth/obstacle guard |
| `community_context_layer` | timeline comments + caption references + quality gate |
| `evidence_indexed_video_agent` | timestamp index + storyboard + transcript + metadata |
| `watch_only_access` | surface router output only |

## Result on 58 clips

| Affordance | n | Pro-not-best rate | Mean task score |
|------------|--:|------------------:|----------------:|
| `community_context_layer` | 14 | 0.643 | 0.194 |
| `stepwise_task_coach` | 13 | 0.462 | 0.494 |
| `watch_only_access` | 12 | 0.250 | 0.227 |
| `evidence_indexed_video_agent` | 7 | 0.571 | 0.281 |
| `route_or_spatial_rehearsal` | 7 | 0.429 | 0.343 |
| `reality_video_task_coach` | 5 | 0.400 | 0.477 |

Summary:

- 46 of 58 clips need an evidence/action loop beyond watch-only access.
- 18 clips need current-state monitoring.
- 18 clips need a human/community layer or safety-sensitive escalation.
- Task-loop recall on pro-not-best clips: 24/27 = 0.889.
- 3 pro-not-best clips remain `watch_only_access`.

## First-principles interpretation

This is the next product boundary:

```text
SceneTwin should decide what kind of evidence loop the user needs,
not only what kind of description they need.
```

The loop may be:

- video-to-real-world task alignment
- route rehearsal
- timestamp/storyboard retrieval
- community-context retrieval
- plain watching

## Challenge

The current probe is lexical and category-based. It proves the concept is
expressible over the current corpus, not that the chosen affordance is correct.

The next hard evidence should be sidecars:

- step segmentation and completion criteria for how-to clips
- ASR/transcripts for action timing
- OCR/text and object/depth for safety guidance
- community/comment simulation or real timeline comments

## New use case

The project's stronger use case is now:

```text
Evidence Loop Router for BLV video access:
choose the minimum evidence/action loop that lets the user watch, ask, do,
plan, verify, or contribute without unnecessary burden.
```
