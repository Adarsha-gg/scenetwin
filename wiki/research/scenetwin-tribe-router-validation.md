---
title: "TRIBE Router Validation"
category: research
tags: [SceneTwin, TRIBE, routing, validation, negative-results]
created: 2026-05-31
updated: 2026-05-31
sources:
  - cursor/research/output/tribe_router_validation_summary.json
  - cursor/research/output/tribe_necessity_perq.csv
  - cursor/research/output/tribe_necessity_rematch_perq.csv
  - cursor/research/output/tribe_crossjudge_gpt5_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_17_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_subset_perq.csv
  - cursor/research/output/tribe_surgical_adqa_perq.csv
  - cursor/research/output/tribe_vs_pro_priority.csv
---

# TRIBE Router Validation

## Bottom Line

The paper-worthy TRIBE claim is **not** global score improvement. The tiny rho
lift is the wrong story.

The defensible claim is narrower: TRIBE-derived blind-spot targets improve the
questions/windows they explicitly target. This survives several judging runs,
especially on matched questions. The claim does **not** extend to predicting the
overall content distribution of professional AD; that test is negative.

## Router Inventory

- Clips: 78 total, 60 external.
- Windows: 334.
- Cases: 133.
- External clips with scene/action time correlation < 0.5: 17/60.
- External clips with scene/action peaks at different timesteps: 31/60.
- Mean external top-1 concentration: 2.69x uniform timing.

| case_id | count |
| --- | --- |
| scene_layout_replay | 37 |
| low_gap_skip | 26 |
| dynamic_type_shift | 20 |
| moment_level_authoring | 20 |
| agent_action_cue | 15 |
| audio_language_confound_check | 15 |

## Matched-Target Evidence

These are the strongest rows: only questions/windows whose required evidence
matches the TRIBE-selected target type.

| experiment | n_clips | n_questions | delta | wins | losses | ties | sign_p_one_sided |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TRIBE target vs VLM target (vision-only VLM) | 44 | 62 | 0.07258 | 9 | 0 | 53 | 0.001953 |
| TRIBE target vs VLM target (VLM gets transcript) | 44 | 62 | 0.06452 | 8 | 1 | 53 | 0.01953 |
| Gap-targeted AD vs generic AD (GPT-5 judge, 60 clips) | 44 | 62 | 0.1129 | 11 | 0 | 51 | 0.0004883 |
| Gap-targeted AD vs generic AD (Opus judge, 17 clips) | 17 | 24 | 0.1667 | 8 | 1 | 15 | 0.01953 |
| Gap-targeted AD vs generic AD (Opus judge, 15-clip subset) | 15 | 18 | 0.3056 | 8 | 0 | 10 | 0.003906 |
| Surgical TRIBE ADQA target vs generic AD | 43 | 60 | 0.1667 | 20 | 2 | 38 | 6.056e-05 |

## Whole-Question Evidence

Whole-question averages are weaker, which is expected. The router is surgical:
it should move targeted questions more than unrelated questions.

| experiment | n_clips | n_questions | delta | wins | losses | ties | sign_p_one_sided |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TRIBE target vs VLM target (vision-only VLM) | 44 | 220 | 0.01818 | 11 | 2 | 207 | 0.01123 |
| TRIBE target vs VLM target (VLM gets transcript) | 44 | 220 | 0.02045 | 13 | 5 | 202 | 0.04813 |
| Gap-targeted AD vs generic AD (GPT-5 judge, 60 clips) | 60 | 300 | 0.03667 | 42 | 24 | 234 | 0.01779 |
| Gap-targeted AD vs generic AD (Opus judge, 17 clips) | 17 | 85 | 0.04706 | 14 | 6 | 65 | 0.05766 |
| Gap-targeted AD vs generic AD (Opus judge, 15-clip subset) | 15 | 75 | 0.09333 | 13 | 3 | 59 | 0.01064 |
| Surgical TRIBE ADQA target vs generic AD | 59 | 295 | 0.07458 | 68 | 30 | 197 | 7.808e-05 |

## Negative Result: Professional AD Priority

TRIBE does **not** beat the VLM at matching the overall content-type profile of
professional AD.

| comparison | value |
| --- | ---: |
| n clips | 55 |
| mean cosine(TRIBE, pro AD) | 0.361 |
| mean cosine(VLM, pro AD) | 0.503 |
| mean cosine(uniform, pro AD) | 0.616 |
| TRIBE - VLM | -0.142 |
| TRIBE wins/losses/ties | 16/39/0 |
| top-type exact match: TRIBE | 15% |
| top-type exact match: VLM | 20% |

Interpretation: TRIBE is not a general replacement for a VLM or human describer.
Its useful role is localized blind-spot targeting, not global AD topic modeling.

## Paper Framing

Use this as a Paper B / systems-routing result:

> A brain-predictive audiovisual encoder can expose typed, time-localized
> accessibility blind spots that are invisible to global score metrics. When AD
> generation or ADQA is conditioned on those blind spots, matched visual-evidence
> questions improve consistently across judges. The effect is surgical, not a
> global metric lift.

Do not claim:

- TRIBE improves global rho.
- TRIBE predicts the full professional AD content distribution.
- TRIBE replaces VLM scoring.

Do claim:

- TRIBE identifies when and what kind of visual access intervention is needed.
- Matched-question gains replicate across independent judge runs.
- The router can decide where to spend expensive human/VLM review budget.
