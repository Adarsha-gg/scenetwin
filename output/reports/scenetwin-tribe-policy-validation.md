---
title: "SceneTwin TRIBE Policy Validation"
category: research
tags: [SceneTwin, TRIBE, routing, validation, VLM, ADQA]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/tribe_native/tribe_policy_loocv_scores.csv
  - output/scenetwin_timing_20clip/tribe_native/tribe_policy_validation_summary.csv
---

# SceneTwin TRIBE Policy Validation

## Why This Test Exists

TRIBE is strongest as a multimodal brain encoder, not a standalone text-quality
metric. This test uses TRIBE clip features as a policy router: choose which
SceneTwin scorer to trust for each clip type, then evaluate the held-out clip.

## Held-Out Results

| kind     | metric                       |      rho |      tau | wins   | full   |
|:---------|:-----------------------------|---------:|---------:|:-------|:-------|
| baseline | claude_vlm_completeness_norm | 0.960184 | 0.89401  | 54/54  | 16/18  |
| baseline | vlm_best_dims_mean           | 0.959021 | 0.887647 | 54/54  | 16/18  |
| baseline | claude_vlm_specificity_norm  | 0.956675 | 0.889652 | 53/54  | 16/18  |
| baseline | selected3_mean               | 0.944489 | 0.865052 | 53/54  | 16/18  |
| baseline | all4_mean                    | 0.932661 | 0.849919 | 53/54  | 16/18  |
| baseline | strict_all4_80adqa_20clip    | 0.926012 | 0.834183 | 54/54  | 16/18  |
| baseline | clip_mean_norm               | 0.798568 | 0.689487 | 48/54  | 11/18  |
| loocv    | tribe_policy_loocv           | 0.943293 | 0.863532 | 53/54  | 15/18  |

## Same-Set Upper Bound

These are useful for exploration only; they are tuned on the same 18 clips.

| kind                 | metric                                                                                      |      rho |      tau | wins   | full   |
|:---------------------|:--------------------------------------------------------------------------------------------|---------:|---------:|:-------|:-------|
| same_set_upper_bound | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm                   | 0.968336 | 0.904634 | 54/54  | 17/18  |
| same_set_upper_bound | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm                    | 0.96783  | 0.902006 | 54/54  | 16/18  |
| same_set_upper_bound | soft:mean_standard_slot_score:all4_mean:claude_vlm_specificity_norm                         | 0.967477 | 0.9      | 54/54  | 16/18  |
| same_set_upper_bound | gate:mean_speech_density>=0.874:claude_vlm_completeness_norm:strict_all4_80adqa_20clip      | 0.966665 | 0.897657 | 54/54  | 17/18  |
| same_set_upper_bound | gate:mean_standard_slot_score>=0.085:strict_all4_80adqa_20clip:claude_vlm_completeness_norm | 0.966665 | 0.897657 | 54/54  | 17/18  |
| same_set_upper_bound | blend:selected3_mean:claude_vlm_specificity_norm:0.55                                       | 0.965948 | 0.897242 | 54/54  | 18/18  |
| same_set_upper_bound | blend:claude_vlm_specificity_norm:selected3_mean:0.45                                       | 0.965948 | 0.897242 | 54/54  | 18/18  |
| same_set_upper_bound | gate:mean_speech_density>=0.874:vlm_best_dims_mean:strict_all4_80adqa_20clip                | 0.965578 | 0.892345 | 54/54  | 17/18  |

## LOOCV Selected Policies

| selected_policy                                                                  |   folds |
|:---------------------------------------------------------------------------------|--------:|
| soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |       8 |
| soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |       5 |
| soft:mean_speech_density:claude_vlm_specificity_norm:all4_mean                   |       1 |
| gate:mean_standard_slot_score>=0.117:selected3_mean:claude_vlm_completeness_norm |       1 |
| gate:mean_need>=0.388:claude_vlm_completeness_norm:selected3_mean                |       1 |
| gate:mean_extended_need_score>=0.263:claude_vlm_completeness_norm:selected3_mean |       1 |
| gate:mean_speech_density>=0.844:claude_vlm_specificity_norm:selected3_mean       |       1 |

## Fold Choices

|   holdout_clip | selected_policy                                                                  |   train_rho |   train_tau | train_wins   | train_full   |
|---------------:|:---------------------------------------------------------------------------------|------------:|------------:|:-------------|:-------------|
|              0 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.969277 |    0.906342 | 51/51        | 16/17        |
|              1 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.968928 |    0.905583 | 51/51        | 16/17        |
|              3 | soft:mean_speech_density:claude_vlm_specificity_norm:all4_mean                   |    0.972183 |    0.908936 | 51/51        | 17/17        |
|              4 | gate:mean_standard_slot_score>=0.117:selected3_mean:claude_vlm_completeness_norm |    0.968947 |    0.906032 | 50/51        | 15/17        |
|              5 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.967209 |    0.902686 | 51/51        | 16/17        |
|              6 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |    0.967429 |    0.901482 | 51/51        | 15/17        |
|              7 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.972677 |    0.911689 | 51/51        | 16/17        |
|              8 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |    0.967429 |    0.901482 | 51/51        | 15/17        |
|              9 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.968928 |    0.905583 | 51/51        | 16/17        |
|             11 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |    0.96675  |    0.900417 | 51/51        | 15/17        |
|             12 | gate:mean_need>=0.388:claude_vlm_completeness_norm:selected3_mean                |    0.972239 |    0.911959 | 51/51        | 17/17        |
|             13 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.967237 |    0.903134 | 51/51        | 16/17        |
|             14 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |    0.968108 |    0.902547 | 51/51        | 15/17        |
|             15 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.969213 |    0.907811 | 51/51        | 16/17        |
|             16 | gate:mean_extended_need_score>=0.263:claude_vlm_completeness_norm:selected3_mean |    0.967823 |    0.905211 | 51/51        | 16/17        |
|             17 | gate:mean_speech_density>=0.844:claude_vlm_specificity_norm:selected3_mean       |    0.968918 |    0.905583 | 50/51        | 15/17        |
|             18 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_completeness_norm        |    0.967199 |    0.902463 | 51/51        | 16/17        |
|             19 | soft:mean_standard_slot_score:selected3_mean:claude_vlm_specificity_norm         |    0.969466 |    0.904677 | 51/51        | 15/17        |

## Verdict

TRIBE helps most as a router when the policy is allowed to be tuned on the same
set. The stricter leave-one-clip-out test is the number to trust, and here it
does **not** beat the best non-TRIBE single scorer.

The honest conclusion is therefore:

- Keep TRIBE native to SceneTwin as an accessibility-pressure, timing, and
  scorer-routing analysis layer.
- Do not claim TRIBE as the main score booster yet.
- Treat the same-set `rho=0.968` policy result as an exploration target that
  needs more clips or an external validation split before it becomes a headline.
