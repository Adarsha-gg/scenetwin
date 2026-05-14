---
title: "SceneTwin Stage 4 LLM-ADQA"
category: research
tags: [SceneTwin, ADQA, Claude, audio-description, evaluation]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_timing_20clip/adqa/adqa_questions.csv
  - output/scenetwin_timing_20clip/adqa/adqa_grades.csv
  - output/scenetwin_timing_20clip/adqa/adqa_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa/adqa_aggregate_results.csv
  - output/scenetwin_timing_20clip/adqa/adqa_nulls.csv
---

# SceneTwin Stage 4 LLM-ADQA

## Question

Can SceneTwin add a functional-comprehension audit layer after TRIBE timing,
CLIP grounding, and OCR coverage?

## Method

For each complete 20-clip timing result, Stage 4 generated ADQA-style questions
from the professional VideoA11y description, then graded every candidate
description tier against those questions. This tests whether a listener could
answer concrete visual/narrative questions from the AD text.

Provider: `anthropic`  
Model: `claude-haiku-4-5-20251001`  
Complete clips: 18  
Questions: 54  
Candidate-question grades: 216

This run used Anthropic for generation/grading.

## Aggregate Results

| metric     |   spearman_rho |   spearman_p |   kendall_tau |   kendall_p |   pairwise_wins |   pairwise_total |   full_order_clips |   full_order_total |
|:-----------|---------------:|-------------:|--------------:|------------:|----------------:|-----------------:|-------------------:|-------------------:|
| adqa_score |       0.941679 |  7.81884e-35 |      0.889349 | 4.62887e-20 |              53 |               54 |                 11 |                 18 |

## Permutation Null

| metric     |   observed_rho |   null_mean_rho |   null_p_ge_observed |   n_permutations |
|:-----------|---------------:|----------------:|---------------------:|-----------------:|
| adqa_score |       0.941679 |      -0.0052353 |                    0 |             2000 |

## Mean ADQA Score By Tier

| tier              |   adqa_score |
|:------------------|-------------:|
| tier3_va11y       |     1        |
| tier2_vatex_long  |     0.472222 |
| tier1_vatex_short |     0.231481 |
| tier0_cross       |     0        |

## Sample Questions

|   clip_idx |   q_idx | question                                                                                      | answer_key                                                                                                                                                              |
|-----------:|--------:|:----------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|          0 |       0 | What object does the chef throw at the wall, and what happens to it?                          | The chef throws a cherry tomato at the wall, and a knife pins it in place.                                                                                              |
|          0 |       1 | What language does the chef use when counting down before throwing?                           | Spanish                                                                                                                                                                 |
|          0 |       2 | What does the chef's facial expression convey after the tomato is pinned?                     | The chef smiles, showcasing his skill and confidence.                                                                                                                   |
|          1 |       0 | What is the man in the gray hoodie doing, and what physical signs of difficulty does he show? | He is rapidly eating a hamburger and taking quick bites, but he appears to struggle and coughs at times.                                                                |
|          1 |       1 | How are the people around the man reacting to what he is doing?                               | People are laughing and clapping, encouraging him to finish.                                                                                                            |
|          1 |       2 | What text is written on the tray liner, and what is used to write it?                         | The text 'BURGER EATING' is written on a tray liner using ketchup.                                                                                                      |
|          3 |       0 | What color is the man's shirt and what type of cookware is he using?                          | The man wears a grey shirt and uses a black cast iron skillet                                                                                                           |
|          3 |       1 | What ingredients are being cooked together in the skillet?                                    | Spaghetti and eggs are being cooked together in an omelette                                                                                                             |
|          3 |       2 | What utensil does the man use to cook, and what cooking technique does he demonstrate?        | He uses a fork to stir the mixture and moves the pan back and forth for even cooking                                                                                    |
|          4 |       0 | What is the girl doing with the eggs, and what utensil is she using?                          | She is stirring scrambled eggs in a frying pan with a spatula.                                                                                                          |
|          4 |       1 | Who does the girl say the eggs are for?                                                       | The eggs are for her and her mother, if her mother wants some.                                                                                                          |
|          4 |       2 | Describe the kitchen setting and the girl's demeanor while cooking.                           | The kitchen is cozy and warm with granite countertop and wooden cabinets. The girl is focused, enjoys the process, and occasionally glances at the camera with a smile. |

## Interpretation

Stage 4 is the missing user-comprehension layer in the SceneTwin audit stack. It
does not replace BLV validation: the questions are generated from professional
AD text, not from human participants or timestamped visual QA annotations. Its
value is that it turns "does the text look similar?" into "does the text answer
the visual questions a listener needs answered?" at corpus scale.

The Anthropic run preserves the expected tier order, so the system pitch becomes
stronger: TRIBE prioritizes windows, CLIP/OCR catch visual grounding obligations,
and LLM-ADQA checks functional comprehension. The strongest caveat is circularity
at the top tier: professional AD is used as the answer key, so `tier3_va11y`
should score near 1.0 by construction. The useful signal is how sharply the same
questions separate tier2, tier1, and cross-category descriptions.
