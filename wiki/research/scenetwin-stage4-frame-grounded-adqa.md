---
title: "SceneTwin Stage 4 Frame-Grounded ADQA"
category: research
tags: [SceneTwin, ADQA, vision, Claude, audio-description, evaluation]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_questions.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_grades.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores_filtered.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_aggregate_results.csv
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_nulls.csv
---

# SceneTwin Stage 4 Frame-Grounded ADQA

## What Changed From v1

In Stage 4 v1, ADQA questions were generated FROM the professional VideoA11y AD,
so tier3 scored 1.0 by construction. This version generates questions by a
vision LLM looking at sampled video frames. Tier3 is no longer the answer key;
it has to earn its score the same way every other tier does.

This iteration also fixes leakage problems flagged by review:
- Candidates are passed to the grader as anonymized IDs (A/B/C/D) shuffled
  per-clip. The grader sees no tier name, no ground-truth rank, no category,
  and no hint about which candidate is professional.
- The grading rubric no longer specifies a target score distribution; scores
  fall where the evidence puts them.

## Method

For each complete clip:

1. Extract 8 frames evenly spaced across the clip.
2. Send frames to Claude vision; receive 5 ADQA-style
   questions whose answer keys come from what Claude sees in the frames.
3. Anonymize the 4 candidate descriptions (A/B/C/D, shuffled per clip).
4. Grade all four candidates blind against the questions.
5. Decode IDs back to tiers locally and aggregate.

Provider: `anthropic`
Model: `claude-haiku-4-5-20251001`
Complete clips: 18
Questions per clip: 5
Total questions: 90
Candidate-question grades: 360

## Aggregate

| metric        |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total | filter                      |
|:--------------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|:----------------------------|
| adqa_v2_score |       0.802928 |  2.19288e-17 |      0.695932 | 1.17337e-13 |              51 |               54 |                  8 |                 18 | unfiltered                  |
| adqa_v2_score |       0.803787 |  1.91151e-17 |      0.712693 | 1.22684e-14 |              51 |               54 |                  8 |                 18 | filtered_floor_zero_dropped |

## Permutation Null

| metric        |   observed_rho |   null_mean_rho |   null_p_ge_observed |   n_permutations | filter                      |
|:--------------|---------------:|----------------:|---------------------:|-----------------:|:----------------------------|
| adqa_v2_score |       0.802928 |     -0.00367672 |                    0 |             2000 | unfiltered                  |
| adqa_v2_score |       0.803787 |      0.00256851 |                    0 |             2000 | filtered_floor_zero_dropped |

## Mean Frame-Grounded ADQA Score By Tier

| tier              |   adqa_v2_score |
|:------------------|----------------:|
| tier3_va11y       |       0.65      |
| tier2_vatex_long  |       0.422222  |
| tier1_vatex_short |       0.244444  |
| tier0_cross       |       0.0388889 |

## Sample Questions (frame-grounded)

|   clip_idx |   q_idx | question                                                                    | answer_key                                                                    |
|-----------:|--------:|:----------------------------------------------------------------------------|:------------------------------------------------------------------------------|
|          0 |       0 | What is the man in the white shirt holding and demonstrating?               | A small insect or specimen, appears to be holding it between his fingers      |
|          0 |       1 | What type of setting or location is shown in most of the frames?            | A laboratory or scientific workspace with equipment, tanks, and workstations  |
|          0 |       2 | What is visible on the wooden board or surface in one of the frames?        | Papers, documents, and sticky notes with writing or markings on them          |
|          0 |       3 | How many people are clearly visible as the main focus throughout the video? | One man, the primary subject demonstrating or presenting the specimen         |
|          0 |       4 | What is the man's apparent role or activity in this setting?                | Scientist or researcher demonstrating or explaining a specimen to an audience |
|          1 |       0 | What is the man in the gray hoodie doing in the first sequence?             | Eating food, appearing to bite or chew on something                           |
|          1 |       1 | Where does this video take place?                                           | Indoors in what appears to be a cafeteria or institutional setting            |
|          1 |       2 | What restaurant or brand is visible on the packaging shown?                 | Burger King                                                                   |
|          1 |       3 | What text appears on the Burger King packaging?                             | Burger eating                                                                 |
|          1 |       4 | What is the man wearing?                                                    | A gray or blue-gray hoodie or sweatshirt                                      |
|          3 |       0 | What is the person cooking in the skillet?                                  | An omelet or egg dish with red peppers                                        |
|          3 |       1 | What liquid is being poured into the pan?                                   | Oil from a bottle                                                             |

## Interpretation

The strict tier3 = 1.0 result from Stage 4 v1 was a known artifact of using the
professional AD as the answer key. This run grounds the answer key in sampled
video frames and grades anonymized candidate descriptions blind. The unfiltered
result is the primary number; the floor-zero-question filter is reported only
as a diagnostic and produces nearly the same rank result.

Tier3 no longer gets a free perfect score. It averages about 0.65, which is a
more realistic ceiling for short 30-60 word AD against frame-derived questions.
The ordering still holds: professional AD > long VATEX > short VATEX >
cross-category control. That makes Stage 4 useful as a scalable comprehension
proxy, while keeping the caveat that it is still LLM-generated/LLM-graded rather
than BLV-user-validated.

## Caveats

- Questions are generated from 8 sampled frames, not the full
  trajectory. Action/event questions may still miss off-frame moments.
- The same model generates questions and grades. A separate grader model
  (e.g. GPT-4V or human) is the obvious next ablation.
- This still does not replace BLV user validation; it is a scalable proxy
  for that validation.
