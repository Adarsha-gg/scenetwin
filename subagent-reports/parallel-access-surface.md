# Parallel Access Surface Triage — Implementation Report

Implemented a local-only research pass for EXPERIMENTS 5-7 using cached CSV/JSON data only.

## Outputs

- Main report: `output/reports/parallel-research-access-surface-triage.md`
- Artifact directory: `cursor/research/output/parallel_research/access_surface/`
- Repro script: `cursor/research/parallel_access_surface_triage.py`

## Key results

- Joined 60 external clips from `external_ensemble_eval.csv` with TRIBE clip summaries.
- Recomputed review-budget curves; `mean_visual_gap` catches 4/10 ADQA failures at 25% review budget and 5/10 at one-third budget.
- Low-gap early-exit remains review-pressure-only: bottom third by max visual gap has ADQA fail rate 0.050 and ensemble fail rate 0.000, but CLIP-only agreement is too weak for replacement/skip claims.
- Produced route counts: 218 `static_ad_ok_low_gap`, 78 `layout_replay_or_scene_cue`, 38 `action_state_or_agent_cue` windows.
- Produced Access Surface OS mapping counts across 133 cases and 334 windows.
- Enriched the top-25 worksheet into reviewer-ready CSV/Markdown with access surface, validation target, existing fail flags, top router windows, and blank pass/fail fields.

## Artifacts written

- `external_joined_failure_rows.csv`
- `review_budget_curves.csv`
- `low_gap_early_exit.csv`
- `route_counts.csv`
- `route_dominant_type_counts.csv`
- `case_surface_counts.csv`
- `window_surface_counts.csv`
- `surface_mapping_rules.json`
- `top25_reviewer_cases.csv`
- `top25_reviewer_cases.md`
- `summary.json`

## Notes

- Requested `context.md` and `plan.md` were absent from the repo root; work proceeded from the explicit task and existing cached artifacts.
- No external APIs, network calls, or human review were used.
