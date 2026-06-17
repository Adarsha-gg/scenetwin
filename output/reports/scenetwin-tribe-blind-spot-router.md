---
title: "TRIBE Blind Spot Router"
category: research
tags: [SceneTwin, TRIBE, tensors, accessibility, routing, audio-description]
created: 2026-05-31
updated: 2026-05-31
sources:
  - cursor/research/output/tribe_tensors/
  - output/scenetwin_description_gain/glasser_roi_mask.csv
  - cursor/research/output/tribe_blind_spot_timesteps.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_blind_spot_cases.csv
---

# TRIBE Blind Spot Router

## Claim

The surviving use case for TRIBE in SceneTwin is not direct AD scoring. It is a
typed blind-spot router: compare TRIBE's audiovisual prediction (`P_AV`) against
audio-only prediction (`P_A`) to identify **when** audio drops visual information
and **what kind** of visual information is lost.

This makes TRIBE operationally necessary because CLIP+ADQA can rank candidate
descriptions, but it cannot expose cortical, time-localized, ROI-typed access
gaps before a description exists.

## Outputs

- `tribe_blind_spot_timesteps.csv`: per-TR scene/spatial, agent/action, and control gaps.
- `tribe_blind_spot_windows.csv`: 3s authoring/review windows with a route.
- `tribe_blind_spot_clip_summary.csv`: per-clip concentration and type-shift features.
- `tribe_blind_spot_cases.csv`: deployment cases SceneTwin can act on.

## Case Inventory

| case_id | clips |
| --- | --- |
| scene_layout_replay | 37 |
| low_gap_skip | 26 |
| dynamic_type_shift | 20 |
| moment_level_authoring | 20 |
| agent_action_cue | 15 |
| audio_language_confound_check | 15 |

## Window Routes

| route | windows |
| --- | --- |
| static_ad_ok_low_gap | 218 |
| layout_replay_or_scene_cue | 78 |
| action_state_or_agent_cue | 38 |

## External Generalization Check

On the 60 external clips:

- Scene/action temporal correlation < 0.5 in 17/60 clips.
- Scene and action peaks occur at different TRIBE timesteps in 31/60 clips.
- Mean top-1 concentration is 2.69x a uniform-timing null.

These are exactly the conditions where a single scalar or one generic AD prompt
is insufficient: the access need is typed and moment-specific.

## Highest-Priority Cases

| case_id | corpus | video_id | category | priority_score | window | why |
| --- | --- | --- | --- | --- | --- | --- |
| moment_level_authoring | external | iGmGQxox43I_000000_000010 | How-to & Instructional | 5.965 | 0.0-3.6s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | inbench | kOf-vl-GmVI_000115_000125 | Pets & Animals | 5.360 | 13.4-16.4s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | 9fuIpQgnNEQ_000049_000059 | Event | 5.250 | 0.0-3.6s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | inbench | 09dQut5GJ68_000049_000059 | Travel | 4.921 | 10.4-13.4s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | S-C86j0keqc_000217_000227 | Event | 4.668 | 6.4-9.1s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | inbench | 0HEi6q3bGaw_000011_000021 | Travel | 4.491 | 16.3-17.9s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | dlBeUWrse3I_000019_000029 | How-to & Instructional | 4.247 | 0.0-3.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | iEAWgsSvJAE_000023_000033 | Film & Animation | 4.060 | 6.4-9.1s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | F-mRnL_XmJU_000000_000010 | Entertainment | 3.977 | 0.0-3.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | eb-ufaFcUas_000008_000018 | Entertainment | 3.929 | 0.0-3.6s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | 3su234u58DA_000172_000182 | Entertainment | 3.913 | 9.1-10.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | inbench | PbGvLf7HvXQ_000063_000073 | Food & Cooking | 3.912 | 0.0-4.5s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | v2Hr1CH-yb0_000076_000086 | How-to & Instructional | 3.871 | 9.0-10.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | d7_SY48r__8_000060_000070 | How-to & Instructional | 3.842 | 9.0-10.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | 0m0-Q0zz_-c_000112_000122 | How-to & Instructional | 3.744 | 0.0-3.6s | Gap is temporally concentrated; spend AD/review budget on the peak window. |
| moment_level_authoring | external | 1HUWWCLza0w_000000_000010 | Sports | 3.698 | 6.7-10.0s | Gap is temporally concentrated; spend AD/review budget on the peak window. |

## Highest-Gap Windows

| corpus | video_id | category | start_s | end_s | dominant_type | peak_visual_gap | route |
| --- | --- | --- | --- | --- | --- | --- | --- |
| external | v2Hr1CH-yb0_000076_000086 | How-to & Instructional | 9.000 | 10.000 | agent_action | 1.643 | action_state_or_agent_cue |
| external | F-mRnL_XmJU_000000_000010 | Entertainment | 0.000 | 3.000 | scene_spatial | 1.440 | layout_replay_or_scene_cue |
| external | dlBeUWrse3I_000019_000029 | How-to & Instructional | 0.000 | 3.000 | agent_action | 1.378 | action_state_or_agent_cue |
| external | 1HUWWCLza0w_000000_000010 | Sports | 6.667 | 10.000 | agent_action | 1.368 | action_state_or_agent_cue |
| external | _TKzyWZHjm8_000002_000012 | Health & Wellness | 0.000 | 3.636 | scene_spatial | 1.321 | layout_replay_or_scene_cue |
| external | iEAWgsSvJAE_000023_000033 | Film & Animation | 6.364 | 9.091 | agent_action | 1.304 | action_state_or_agent_cue |
| external | d7_SY48r__8_000060_000070 | How-to & Instructional | 9.000 | 10.000 | agent_action | 1.290 | action_state_or_agent_cue |
| external | 8vkNr_eysXY_000002_000012 | How-to & Instructional | 9.000 | 10.000 | scene_spatial | 1.267 | layout_replay_or_scene_cue |
| external | EA3HCx0yTIY_000281_000291 | Music | 0.000 | 3.636 | agent_action | 1.174 | action_state_or_agent_cue |
| inbench | 09dQut5GJ68_000049_000059 | Travel | 10.430 | 13.410 | agent_action | 1.163 | action_state_or_agent_cue |
| external | S-C86j0keqc_000217_000227 | Event | 6.364 | 9.091 | agent_action | 1.154 | action_state_or_agent_cue |
| external | iGmGQxox43I_000000_000010 | How-to & Instructional | 0.000 | 3.636 | agent_action | 1.086 | action_state_or_agent_cue |
| external | BHxn3qfPAl4_000018_000028 | Health & Wellness | 6.000 | 9.000 | agent_action | 1.081 | action_state_or_agent_cue |
| inbench | kOf-vl-GmVI_000115_000125 | Pets & Animals | 13.410 | 16.390 | agent_action | 1.079 | action_state_or_agent_cue |
| external | 8vkNr_eysXY_000002_000012 | How-to & Instructional | 6.000 | 9.000 | scene_spatial | 1.035 | layout_replay_or_scene_cue |
| external | zTJ0Zbv1jBo_000045_000055 | Health & Wellness | 0.000 | 3.636 | scene_spatial | 1.026 | layout_replay_or_scene_cue |

## Product Use

The router should sit upstream of scoring:

1. Run TRIBE once per clip to get `P_AV` and `P_A`.
2. Convert tensor gaps into typed 3s windows.
3. Use top windows to create targeted ADQA questions, AD authoring prompts,
   replay/keyframe surfaces, or human-review queues.
4. Leave CLIP+ADQA as the scoring layer.

Recommended product name: **Neural Blind Spot Map**.
