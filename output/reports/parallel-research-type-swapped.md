# EXPERIMENT 1 — Type-swapped TRIBE prompt control (local-only pass)

Date: 2026-06-23

## Verdict

A **true type-swapped prompt-control result is not possible from the cached data currently present**. The cache supports generic/baseline vs TRIBE-matched gap-targeted comparisons, and it supports TRIBE-vs-VLM target rematches, but it does not contain a third **swapped prompt** condition generated under the same visual context, word budget, generator family, and question set.

Generated future no-API batch artifact: `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl` (15 JSONL records).

## Evidence inspected

| Path | rows | relevant conditions | blocking note |
|---|---:|---|---|
| `cursor/research/output/tribe_surgical_adqa_perq.csv` | 590 | baseline:295, gap_targeted:295 | paired per-question baseline/gap_targeted only; has q_type/tribe_type but no swapped condition |
| `cursor/research/output/tribe_crossjudge_gpt5_perq.csv` | 600 | baseline:300, gap_targeted:300 | cross-judge baseline/gap_targeted only; no swapped condition; most lack q_type/tribe_type |
| `cursor/research/output/tribe_crossjudge_opus_17_perq.csv` | 170 | baseline:85, gap_targeted:85 | cross-judge baseline/gap_targeted only; no swapped condition; most lack q_type/tribe_type |
| `cursor/research/output/tribe_crossjudge_opus_subset_perq.csv` | 150 | baseline:75, gap_targeted:75 | cross-judge baseline/gap_targeted only; no swapped condition; most lack q_type/tribe_type |
| `cursor/research/output/tribe_necessity_rematch_perq.csv` | 660 | baseline:220, vlm:220, tribe:220 | baseline/vlm/tribe target comparison; VLM is not a type-swapped prompt control |
| `cursor/research/output/tribe_gap_targeted_external_full_scores.csv` | 625 | baseline:316, gap_targeted:309 | generated AD text for baseline/gap_targeted only; no swapped AD text |
| `cursor/research/output/tribe_blind_spot_windows.csv` | 334 | no condition column | route/window inventory only; no generated ADQA scores for swapped prompts |
| `cursor/research/output/tribe_blind_spot_clip_summary.csv` | 78 | no condition column | route/window inventory only; no generated ADQA scores for swapped prompts |
| `cursor/research/output/tribe_blind_spot_cases.csv` | 133 | no condition column | route/window inventory only; no generated ADQA scores for swapped prompts |

## Local quantitative checks

- `tribe_surgical_adqa_perq.csv` contains 295 paired cached questions: 60 matched and 235 unmatched. Mean cached lift is matched +0.167, unmatched +0.051. This is useful prior evidence, but it is only `gap_targeted - baseline`.
- `tribe_necessity_rematch_perq.csv` has 200 question rows where TRIBE and VLM target types differ, but those rows compare a TRIBE-targeted candidate to a transcript-armed VLM-targeted candidate. That confounds target-selection method, prompt text, and possibly visual evidence; it is not a swapped prompt control.
- Existing `tribe_blind_spot_*` files provide the route labels and windows needed to construct controls, not the generated swapped outputs.

## Findings

| ID | Severity | Finding | Affected paths |
|---|---|---|---|
| F1 | HIGH | True type-swapped result is blocked: no local cache has conditions `generic/matched/swapped` for the same clips/questions. | `cursor/research/output/tribe_surgical_adqa_perq.csv`, `cursor/research/output/tribe_crossjudge_gpt5_perq.csv`, `cursor/research/output/tribe_gap_targeted_external_full_scores.csv` |
| F2 | MEDIUM | Do not use VLM rematch as the swapped control. It is a necessity/fair-baseline comparison, not a prompt-type swap. | `cursor/research/output/tribe_necessity_rematch_perq.csv` |
| F3 | MEDIUM | Full cached ADQA question text was not available locally; candidate batch therefore references cached `q_idx/q_type` when usable (8/15 records have selected-window-type q refs) and includes a question-generation prompt for future recovery/regeneration. | expected by scripts as `cursor/output/external_adqa/external_adqa_questions.csv` (absent), cached refs in `cursor/research/output/tribe_surgical_adqa_perq.csv` |
| F4 | INFO | Future experiment batch is ready without API calls: 15 candidate records with concrete clip/window metrics, matched/generic/swapped AD prompts, and scoring plan. Type mix: {'motion_action': 9, 'scene_spatial': 6}. | `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl` |

## Future experiment design encoded in JSONL

Each JSONL record contains:

- `video_id`, `clip_key`, category, and exact TRIBE window.
- `matched_type` from the TRIBE route and `swapped_type` control.
- cached question references where available (`q_idx`, `q_type`, cached baseline and matched scores), selected by window type when the cache supports it.
- three AD-generation prompts: `generic`, `matched`, and `swapped`.
- a scoring plan: blind-grade the same ADQA questions and test `matched > swapped`, with `generic` as baseline.

## Residual risks

- Future execution still needs an approved generator/judge or human evaluation; this pass intentionally made no external/API calls.
- Candidate prompts include cached AD snippets only as context hints, not ground-truth visual evidence. The future runner must supply actual frames/video/transcript.
- If the original external ADQA question CSV cannot be recovered, questions must be regenerated before final prompt-control scoring; this is required for the 7/15 records without selected-window-type cached q refs.
