---
title: Parallel Research: Route-Specific Hallucination Gate
category: research
tags: [SceneTwin, hallucination, TRIBE, routing, local-only]
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/output/parallel_research/hallucination_gate/summary.json
  - cursor/research/output/parallel_research/hallucination_gate/joined_clip_rows.csv
---

## Question

Can cached TRIBE blind-spot routes explain where the cached hallucination gate is strongest? This pass is local-only: it reads existing CSV/JSON artifacts and uses only Python stdlib.

## Join and overall gate

- Hallucination rows: 60; joined to TRIBE clip summary: 60; unmatched hallucination clips: 0.
- Mean CLIP hallucination drop: 0.0369; paraphrase drop: 0.0077; hallucination-specific CLIP margin: 0.0292.
- Mean ADQA hallucination drop: 0.1683; paraphrase drop: -0.0183; ADQA-blind clips: 17/60.

## Route/type summaries

### Top TRIBE window route

| top_window_route | n_clips | clip_halluc_drop_mean | clip_para_drop_mean | clip_specific_margin_mean | adqa_halluc_drop_mean | adqa_blind_rate | max_visual_gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| layout_replay_or_scene_cue | 26 | 0.03473 | 0.007169 | 0.02756 | 0.1654 | 0.1923 | 0.6927 |
| action_state_or_agent_cue | 18 | 0.04068 | 0.00821 | 0.03247 | 0.2 | 0.3333 | 0.9551 |
| static_ad_ok_low_gap | 16 | 0.03611 | 0.00808 | 0.02803 | 0.1375 | 0.375 | 0.1904 |

### Clip-level TRIBE dominant type

| dominant_clip_type | n_clips | clip_halluc_drop_mean | clip_specific_margin_mean | adqa_halluc_drop_mean | adqa_blind_rate | max_visual_gap |
| --- | --- | --- | --- | --- | --- | --- |
| scene_spatial | 46 | 0.03418 | 0.02666 | 0.1565 | 0.2826 | 0.5724 |
| agent_action | 14 | 0.04574 | 0.03737 | 0.2071 | 0.2857 | 0.8513 |

## Category summaries

| category | n_clips | clip_halluc_drop_mean | clip_specific_margin_mean | adqa_halluc_drop_mean | adqa_blind_rate | max_visual_gap |
| --- | --- | --- | --- | --- | --- | --- |
| How-to & Instructional | 21 | 0.03194 | 0.01986 | 0.1333 | 0.2857 | 0.6926 |
| Entertainment | 10 | 0.03601 | 0.02727 | 0.17 | 0.3 | 0.6497 |
| People & Vlogs | 8 | 0.0491 | 0.04685 | 0.15 | 0.5 | 0.4389 |
| Sports | 6 | 0.03357 | 0.02776 | 0.2 | 0.1667 | 0.643 |
| Health & Wellness | 4 | 0.02003 | 0.01565 | 0.175 | 0.25 | 0.9376 |
| Event | 3 | 0.04486 | 0.04174 | 0.1333 | 0.3333 | 0.6535 |
| Food & Cooking | 3 | 0.02022 | 0.01231 | 0.2667 | 0.3333 | 0.2559 |
| Film & Animation | 2 | 0.04474 | 0.03877 | 0.25 | 0 | 0.9094 |
| Music | 2 | 0.06569 | 0.07044 | 0.3 | 0 | 0.637 |
| Education, Seminar & Talks | 1 | 0.09148 | 0.07508 | 0.2 | 0 | 0.2667 |

## Probe category summaries

### Swap class

| swap_class | n_clips | clip_halluc_drop_mean | clip_specific_margin_mean | adqa_halluc_drop_mean | adqa_blind_rate |
| --- | --- | --- | --- | --- | --- |
| object_scene | 18 | 0.0474 | 0.04215 | 0.1333 | 0.4444 |
| action_relational | 2 | 0.06964 | 0.05414 | 0.15 | 0 |
| count_action | 1 | 0.02744 | 0.03724 | 0.1 | 0 |
| count_relational | 1 | 0.009831 | -0.02831 | 0.2 | 0 |
| relational_action | 1 | 0.005343 | 0.00619 | 0 | 1 |

### Probe type

| probe_type | n_clips | clip_halluc_drop_mean | clip_specific_margin_mean | adqa_halluc_drop_mean | adqa_blind_rate |
| --- | --- | --- | --- | --- | --- |
| action_relation | 18 | 0.0474 | 0.04215 | 0.1333 | 0.4444 |
| spatial_relation | 9 | 0.04616 | 0.04036 | 0.1111 | 0.3333 |
| who_role | 9 | 0.04447 | 0.03729 | 0.1222 | 0.3333 |
| count | 6 | 0.03913 | 0.03447 | 0.1167 | 0.3333 |

## TRIBE high-gap / route prediction checks

Labels are simple binary targets: top-quartile CLIP hallucination drop, top-quartile CLIP hallucination-specific margin, ADQA detected (drop > 0), and related controls. AUC is pairwise rank AUC where larger TRIBE feature should imply a stronger gate; recall@top20pct is recall among the top 20% clips by that feature.

| label | feature | positives | auc | recall_at_prevalence_k | recall_at_top20pct | score_mean_positive | score_mean_negative |
| --- | --- | --- | --- | --- | --- | --- | --- |
| clip_halluc_drop_top_quartile | mean_visual_gap | 15 | 0.6593 | 0.4 | 0.3333 | 0.3283 | 0.2195 |
| clip_halluc_drop_top_quartile | max_visual_gap | 15 | 0.6548 | 0.5333 | 0.4667 | 0.8333 | 0.5722 |
| clip_halluc_drop_top_quartile | top_window_peak_visual_gap | 15 | 0.6548 | 0.5333 | 0.4667 | 0.8333 | 0.5722 |
| clip_halluc_drop_top_quartile | mean_agent_action_gap | 15 | 0.6415 | 0.4667 | 0.3333 | 0.1907 | 0.1173 |
| clip_halluc_drop_top_quartile | top_case_priority_score | 15 | 0.6267 | 0.4 | 0.2667 | 1.878 | 1.299 |
| clip_specific_margin_top_quartile | mean_visual_gap | 15 | 0.6178 | 0.4 | 0.2667 | 0.3148 | 0.224 |
| clip_specific_margin_top_quartile | mean_scene_spatial_gap | 15 | 0.6015 | 0.4 | 0.3333 | 0.263 | 0.1927 |
| clip_specific_margin_top_quartile | top_window_visual_minus_control | 15 | 0.5896 | 0.4 | 0.3333 | 0.3746 | 0.2239 |
| clip_specific_margin_top_quartile | top_case_priority_score | 15 | 0.5822 | 0.3333 | 0.2 | 1.644 | 1.377 |
| clip_specific_margin_top_quartile | max_visual_gap | 15 | 0.5793 | 0.4 | 0.3333 | 0.7459 | 0.6013 |
| adqa_detected | mean_agent_action_gap | 42 | 0.5979 | 0.7857 | 0.1905 | 0.1434 | 0.1176 |
| adqa_detected | route_share_layout_replay_or_scene_cue | 42 | 0.578 | 0.6429 | 0.2381 | 0.2937 | 0.1944 |
| adqa_detected | mean_visual_gap | 42 | 0.5754 | 0.7381 | 0.2381 | 0.2636 | 0.2073 |
| adqa_detected | top_route_is_layout_replay_or_scene_cue | 42 | 0.5714 | 0.6667 | 0.2143 | 0.4762 | 0.3333 |
| adqa_detected | route_mean_layout_replay_or_scene_cue | 42 | 0.5688 | 0.6429 | 0.2381 | 0.2253 | 0.1457 |
| adqa_drop_top_quartile | route_peak_action_state_or_agent_cue | 15 | 0.6519 | 0.4 | 0.4 | 0.5685 | 0.2456 |
| adqa_drop_top_quartile | route_mean_action_state_or_agent_cue | 15 | 0.6415 | 0.3333 | 0.3333 | 0.3475 | 0.1723 |
| adqa_drop_top_quartile | mean_agent_action_gap | 15 | 0.64 | 0.4 | 0.4 | 0.1905 | 0.1173 |
| adqa_drop_top_quartile | mean_visual_gap | 15 | 0.637 | 0.2667 | 0.2667 | 0.2954 | 0.2305 |
| adqa_drop_top_quartile | route_share_action_state_or_agent_cue | 15 | 0.6274 | 0.3333 | 0.3333 | 0.1889 | 0.09444 |

## Finding

TRIBE route is useful for stratifying the hallucination gate, but not as a clean high-gap predictor in this cached 60-clip set. The clearest route-level separation is categorical: clips whose top TRIBE window is action-state/agent-cue have the largest mean CLIP hallucination drop and hallucination-specific CLIP margin; layout/scene-cue clips have the lowest ADQA blind rate; static/low-gap clips have the lowest mean TRIBE gap but do not eliminate CLIP hallucination drops. Category effects and small-cell route/category splits remain material, so this should be treated as a routing/triage lens, not a standalone hallucination-risk score.

Artifacts are under `cursor/research/output/parallel_research/hallucination_gate/`.
