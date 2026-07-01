---
title: TRIBE New Findings — Local Cached-Data Run
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_local.py
  - cursor/research/output/new_findings_local/
  - output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_surgical_adqa_perq.csv
  - cursor/research/output/tribe_crossjudge_gpt5_perq.csv
  - cursor/research/output/tribe_crossjudge_opus_17_perq.csv
  - cursor/output/external_ensemble_eval.csv
---

# TRIBE New Findings — Local Cached-Data Run

This is the first actual cached-data pass after the 100-item backlog. It uses no new API calls and no GPU/TRIBE inference.

## Finding 1 — the in-benchmark AUC=1.00 survives feature-selection correction only as pilot evidence

The old in-benchmark result had 2 positives out of 18 clips. I re-tested it as a **family-wise max-statistic null** over 14 plausible TRIBE/simple features, enumerating all 153 possible 2-positive label assignments.

- Best observed feature: `mean_standard_slot_score` (high_bad)
- Best observed AUC: **1.000**
- Selected feature top-2 hypergeometric p: **0.0065**
- Family-wise max-stat p across candidate features: **0.0915**

Interpretation: the recall@2/AUC=1.00 story remains real as a pilot, but the corrected p is weaker than the single-feature hypergeometric number. Use it as supporting evidence, not as a standalone headline.

Artifact: `cursor/research/output/new_findings_local/feature_selection_null_features.csv`.

## Finding 2 — external low-gap clips look safer, but max visual gap is only a modest failure predictor

On the corrected external ladder, joined `external_ensemble_eval.csv` to the 60 external TRIBE blind-spot summaries.

- n clips: 60
- ADQA full-order failures: 10/60
- Ensemble full-order failures: 2/60
- Bottom 25% by `max_visual_gap`: ADQA fail rate **0.067**, ensemble fail rate **0.000**
- Top 25% by `max_visual_gap`: ADQA fail rate **0.200**, ensemble fail rate **0.133**

| Feature | AUC vs ADQA fail | AUC vs ensemble fail | Spearman vs ADQA fail |
|---|---:|---:|---:|
| mean_visual_gap | 0.672 | 0.914 | 0.222 |
| max_visual_gap | 0.616 | 0.845 | 0.150 |
| top1_vs_uniform | 0.452 | 0.422 | -0.062 |
| top1_share | 0.508 | 0.448 | 0.010 |
| scene_agent_peak_apart | 0.490 | 0.491 | -0.015 |

Interpretation: this supports **low-gap early-exit / lower-review priority** as a hypothesis, but not an automatic skip policy. Max/mean visual gap are modest predictors; concentration (`top1_vs_uniform`) is weaker for failure prediction.

Artifacts: `external_low_gap_failure_rows.csv`, `external_low_gap_failure_metrics.csv`.

## Finding 3 — route-confidence features are not yet calibrated predictors of targeted-generation lift

I joined per-video TRIBE route features to matched-question deltas from the cached Haiku, GPT-5, and Opus judge runs.

| Run | videos | mean matched delta | ρ dominance-margin | ρ visual-minus-control | ρ top control-ratio | ρ top1-vs-uniform |
|---|---:|---:|---:|---:|---:|---:|
| surgical_haiku | 59 | 0.184 | -0.194 | -0.423 | 0.299 | -0.179 |
| crossjudge_gpt5 | 60 | 0.140 | -0.137 | -0.265 | 0.182 | -0.283 |
| crossjudge_opus17 | 17 | 0.225 | -0.522 | -0.269 | 0.015 | -0.188 |

Interpretation: the route works as a **target selector**, but the current confidence fields (`dominance_margin`, `visual_minus_control`, `top1_vs_uniform`) are not a reliable calibrated estimate of how much a generated AD will improve. That is a new negative/guardrail: do not present dominance margin as a probability-of-success until a better calibration model exists.

Artifacts: `route_confidence_*.csv`, `route_confidence_metrics_*.csv`.

## Finding 4 — matched surgical gains are concentrated in scene/spatial and visual-form targets; non-scene types are underpowered

From `tribe_surgical_adqa_perq.csv`, matched-question deltas by TRIBE type:

| TRIBE type | n matched qs | mean delta | wins/losses/ties | one-sided sign p |
|---|---:|---:|---:|---:|
| face_character | 3 | 0.333 | 2/0/1 | 0.2500 |
| motion_action | 3 | 0.333 | 1/0/2 | 0.5000 |
| scene_spatial | 50 | 0.150 | 16/2/32 | 0.0007 |
| visual_form | 4 | 0.125 | 1/0/3 | 0.5000 |

Interpretation: the current positive surgical result is mostly a **scene/spatial + visual-form** story. Action/body/face/object subclaims need more examples before they should be described as equally validated.

Artifact: `surgical_matched_delta_by_tribe_type.csv`.

## Finding 5 — tensor manifest is mostly healthy, with specific caveats to quarantine/mention

Tensor manifest audit:

- Manifest rows: 78
- JSON files: 78
- Missing JSON files: 0
- Extra JSON files: 0
- Bad shape count: 0
- `audio_only_ok != True`: 0
- `alignment_cosine <= 0.5`: 23 clips — inbench_clip_09_TF4q9y0rJoc_000000_000010, inbench_clip_15_OGWuj_FtaQc_000010_000020, external_0t0DB1B1w8Y_000000_000010, external_1-jIze6gy0g_000026_000036, external_1kLhK8KfIEw_000020_000030, external_2kJxrcNRS9w_000047_000057, external_BHxn3qfPAl4_000018_000028, external_Ccgwurislg8_000082_000092, external_EA3HCx0yTIY_000281_000291, external_GOH6fBhoi2o_000010_000020, external_OASCPKazLIM_000132_000142, external_RjPp0ZPW0yc_000000_000010, external_RlfVK8z5wJ0_000000_000010, external__TKzyWZHjm8_000002_000012, external_c_gQ9CSaZY4_000000_000010, external_d7_SY48r__8_000060_000070, external_g8Idd47kGqo_000037_000047, external_h8wsO9A9v_c_000016_000026, external_iEAWgsSvJAE_000023_000033, external_j6CgiNeWQwM_000842_000852, external_jeweRSnAJeo_000050_000060, external_rGQ64NXktF8_000006_000016, external_v2Hr1CH-yb0_000076_000086
- P_AV vs P_A temporal length mismatches: 35
- JSON/manifest value mismatches: 0

Interpretation: the cached tensor-derived metadata is usable, but the 23 low-alignment AD-response rows and frequent one-TR AV/A length mismatches should be explicitly treated as data-quality caveats rather than silently hidden.

Artifact: `tensor_health_rows.csv`.

## What changed in the research plan

1. Prioritize external low-gap early-exit as a **conservative review-priority** experiment, not an AD omission claim yet.
2. Add a reviewer-defense sentence: in-bench TRIBE AUC=1.00 has family-wise p≈0.092 across tested features, so external OOD triage should carry more weight.
3. Do not expose route confidence as calibrated probability in the UI yet.
4. Split matched-target claims by type: scene/spatial is best-supported; action/face/object need targeted data generation.
5. Run a small data-quality quarantine before any next TRIBE tensor-derived paper figure.
