---
title: Parallel Research — Access Surface Triage
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/parallel_access_surface_triage.py
  - cursor/research/output/tribe_blind_spot_cases.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/new_findings_round3/review_worksheet_rows.csv
  - cursor/output/external_ensemble_eval.csv
  - cursor/research/output/parallel_research/access_surface/
---

# Parallel Research — Access Surface Triage

Local-only pass for EXPERIMENTS 5-7: low-gap early-exit/review-budget, top-25 review worksheet validation prep, and Access Surface OS mapping. No external APIs or humans were called.

## Data coverage

- External clips with corrected-ladder ensemble labels joined to TRIBE summaries: **60**.
- Total router windows: **334**.
- Total router cases: **133**.
- Top worksheet rows enriched for validation: **25**.

## Experiment 5 — low-gap early-exit and review budget

Budget curves continue to support TRIBE as a **review-priority queue**, not an automatic AD omission policy.

| Queue | Budget frac | k clips | ADQA failures caught | Recall | Precision |
|---|---:|---:|---:|---:|---:|
| mean_visual_gap | 0.10 | 6 | 2/10 | 0.200 | 0.333 |
| mean_visual_gap | 0.20 | 12 | 3/10 | 0.300 | 0.250 |
| mean_visual_gap | 0.25 | 15 | 4/10 | 0.400 | 0.267 |
| mean_visual_gap | 0.33 | 20 | 5/10 | 0.500 | 0.250 |
| case_priority_non_low_gap | 0.10 | 6 | 0/10 | 0.000 | 0.000 |
| case_priority_non_low_gap | 0.20 | 12 | 1/10 | 0.100 | 0.083 |
| case_priority_non_low_gap | 0.25 | 15 | 2/10 | 0.200 | 0.133 |
| case_priority_non_low_gap | 0.33 | 20 | 3/10 | 0.300 | 0.150 |

Selected early-exit checks using bottom/top max visual gap:

| Gap feature | group | frac | n | ADQA fail rate | Ensemble fail rate | ADQA/ensemble agreement |
|---|---|---:|---:|---:|---:|---:|
| max_visual_gap | low | 0.25 | 15 | 0.067 | 0.000 | 0.933 |
| max_visual_gap | high | 0.25 | 15 | 0.200 | 0.133 | 0.933 |
| max_visual_gap | low | 0.33 | 20 | 0.050 | 0.000 | 0.950 |
| max_visual_gap | high | 0.33 | 20 | 0.250 | 0.100 | 0.850 |

Interpretation: low-gap clips can lower human/frontier-review pressure after normal scoring. CLIP-only replacement remains unsafe enough to avoid deployable skip language.

Artifacts: `review_budget_curves.csv`, `low_gap_early_exit.csv`, `external_joined_failure_rows.csv`.

## Experiment 6 — top-25 review worksheet validation prep

Prepared reviewer-ready top cases with deterministic surface labels, validation targets, existing fail flags, and blank reviewer pass/fail columns.

| Rank | Video | Case | Priority | Surface | Window | ADQA fail | Ensemble fail |
|---:|---|---|---:|---|---|---:|---:|
| 1 | iGmGQxox43I_000000_000010 | moment_level_authoring | 5.965 | peak_window_review_card | 0.0-3.6s | 0 | 0 |
| 2 | kOf-vl-GmVI_000115_000125 | moment_level_authoring | 5.360 | peak_window_review_card | 13.4-16.4s |  |  |
| 3 | 9fuIpQgnNEQ_000049_000059 | moment_level_authoring | 5.250 | peak_window_review_card | 0.0-3.6s | 0 | 0 |
| 4 | 09dQut5GJ68_000049_000059 | moment_level_authoring | 4.921 | peak_window_review_card | 10.4-13.4s |  |  |
| 5 | S-C86j0keqc_000217_000227 | moment_level_authoring | 4.668 | peak_window_review_card | 6.4-9.1s | 0 | 0 |
| 6 | 0HEi6q3bGaw_000011_000021 | moment_level_authoring | 4.491 | peak_window_review_card | 16.3-17.9s |  |  |
| 7 | dlBeUWrse3I_000019_000029 | moment_level_authoring | 4.247 | peak_window_review_card | 0.0-3.0s | 0 | 0 |
| 8 | iEAWgsSvJAE_000023_000033 | moment_level_authoring | 4.060 | peak_window_review_card | 6.4-9.1s | 0 | 0 |
| 9 | F-mRnL_XmJU_000000_000010 | moment_level_authoring | 3.977 | peak_window_review_card | 0.0-3.0s | 0 | 0 |
| 10 | eb-ufaFcUas_000008_000018 | moment_level_authoring | 3.929 | peak_window_review_card | 0.0-3.6s | 0 | 0 |

Artifacts: `top25_reviewer_cases.csv`, `top25_reviewer_cases.md`.

## Experiment 7 — Access Surface OS mapping counts

### Window route counts

| Corpus | Route | Windows |
|---|---|---:|
| all | action_state_or_agent_cue | 38 |
| all | layout_replay_or_scene_cue | 78 |
| all | static_ad_ok_low_gap | 218 |

### Window-level access-surface mapping

| Route | Access surface | Surface family | Windows |
|---|---|---|---:|
| action_state_or_agent_cue | action_state_or_agent_cue | concise_cue | 38 |
| layout_replay_or_scene_cue | layout_replay_or_keyframe | defer_replay | 78 |
| static_ad_ok_low_gap | static_ad_low_pressure | static_ad | 218 |

### Case-level access-surface mapping

| Case ID | Access surface | Surface family | Cases |
|---|---|---|---:|
| agent_action_cue | action_state_or_agent_cue | concise_cue | 15 |
| audio_language_confound_check | evidence_sidecar_qc | creator_qc | 15 |
| dynamic_type_shift | segmented_scene_action_surface | defer_replay | 20 |
| low_gap_skip | static_ad_low_pressure | static_ad | 26 |
| moment_level_authoring | peak_window_review_card | creator_qc | 20 |
| scene_layout_replay | layout_replay_or_keyframe | defer_replay | 37 |

Interpretation: the router is already shaped like an Access Surface OS input: static low-pressure windows dominate, while non-low-gap cases route to layout replay/keyframe, action-state cue, peak-window QC, segmented scene/action treatment, or evidence-sidecar QC.

Artifacts: `route_counts.csv`, `route_dominant_type_counts.csv`, `case_surface_counts.csv`, `window_surface_counts.csv`, `surface_mapping_rules.json`.

## Actionable next use

Use `top25_reviewer_cases.csv` as the reviewer/VLM worksheet. Each row has a concrete validation target; the next pass should fill only the prepared blank columns rather than re-ranking the queue.
