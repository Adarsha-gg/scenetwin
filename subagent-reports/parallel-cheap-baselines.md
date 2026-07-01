# Parallel Research — Cheap Baseline Gauntlet for TRIBE Routing/Triage

Local-only pass. No external APIs were called. Inputs were cached CSV/JSON/txt artifacts under `cursor/research/output/`, including external transcripts.

## Data and targets

- External corrected-ladder triage rows: **60 clips**.
- External labels: ADQA failures **10**, ensemble failures **2**, any clip failure **20**, tier-3 pairwise losses **6**.
- Transcript cache coverage: **56 / 60** external clips.
- Route-label check: **18 in-benchmark clips**, extended-route positives **10**.

## Headline comparison: TRIBE vs cheap baselines

Higher feature values are interpreted as higher risk unless `direction` says the best discrimination is the reverse. `category_shuffle_p` tests whether the observed AUC survives shuffling feature values within category.

| target | family | best_feature | auc_high_value_bad | best_direction_auc | direction | category_shuffle_p |
|---|---|---|---|---|---|---|
| adqa_fail | tribe_gap_route | accessibility_gap | 0.794 | 0.794 | high_bad | 0.003 |
| adqa_fail | category_only | category_loo_adqa_fail_rate | 0.700 | 0.700 | high_bad | 1.000 |
| adqa_fail | transcript_speech | transcript_char_count | 0.267 | 0.733 | low_bad | 0.995 |
| adqa_fail | duration_word_count | tier3_word_count | 0.286 | 0.714 | low_bad | 0.990 |
| ensemble_fail | tribe_gap_route | accessibility_gap | 1.000 | 1.000 | high_bad | 0.008 |
| ensemble_fail | category_only | category_loo_ensemble_fail_rate | 0.241 | 0.759 | low_bad | 1.000 |
| ensemble_fail | transcript_speech | transcript_available | 0.276 | 0.724 | low_bad | 1.000 |
| ensemble_fail | duration_word_count | tier3_word_count | 0.082 | 0.918 | low_bad | 0.993 |
| clip_fail | tribe_gap_route | scene_agent_peak_apart | 0.637 | 0.637 | high_bad | 0.073 |
| clip_fail | category_only | category_loo_clip_fail_rate | 0.305 | 0.695 | low_bad | 1.000 |
| clip_fail | transcript_speech | transcript_available | 0.475 | 0.525 | low_bad | 0.586 |
| clip_fail | duration_word_count | tier3_word_count | 0.448 | 0.552 | low_bad | 0.725 |
| t3_lost_any | tribe_gap_route | description_loss | 0.731 | 0.731 | high_bad | 0.042 |
| t3_lost_any | category_only | category_loo_t3_lost_any_rate | 0.753 | 0.753 | high_bad | 1.000 |
| t3_lost_any | transcript_speech | transcript_char_count | 0.338 | 0.662 | low_bad | 0.958 |
| t3_lost_any | duration_word_count | tier3_word_count | 0.236 | 0.764 | low_bad | 0.963 |

### Top-k review queue sanity check

- ADQA failures sorted by `mean_visual_gap`: top 20% catches **3 / 10** failures, recall **0.300** vs random expected 0.200.
- Ensemble failures sorted by `mean_visual_gap`: top 20% catches **2 / 2** failures, recall **1.000** vs random expected 0.200.

## Route-label gauntlet

The cached in-benchmark `tribe_route` label is mostly a TRIBE-derived target, so this is a leakage/cheap-proxy sanity check rather than independent validation. Best route-label discriminator:

```json
{
  "dataset": "inbench20",
  "target": "extended_route_label",
  "feature_group": "tribe_route",
  "feature": "extended_seconds_frac",
  "n": 18,
  "positives": 10,
  "auc_high_value_bad": 1.0,
  "best_direction_auc": 1.0,
  "best_direction": "high_route",
  "random_shuffle_p_ge_auc": 0.0001999600079984003,
  "category_shuffle_p_ge_auc": 0.0007998400319936012
}
```

| feature_group | feature | n | positives | auc_high_value_bad | best_direction_auc | best_direction | category_shuffle_p_ge_auc |
|---|---|---|---|---|---|---|---|
| tribe_route | mean_need | 18 | 10 | 0.950 | 0.950 | high_route | 0.0014 |
| tribe_route | max_need | 18 | 10 | 0.775 | 0.775 | high_route | 0.0384 |
| tribe_route | high_need_seconds_frac | 18 | 10 | 0.944 | 0.944 | high_route | 0.0010 |
| tribe_route | extended_seconds_frac | 18 | 10 | 1.000 | 1.000 | high_route | 0.0008 |
| tribe_route | tribe_pressure | 18 | 10 | 0.963 | 0.963 | high_route | 0.0008 |
| tribe_route | risk_score | 18 | 10 | 0.450 | 0.550 | low_route | 0.6567 |
| category_only | category_loo_extended_route_rate | 18 | 10 | 0.150 | 0.850 | low_route | 1.0000 |
| duration_word_count | duration_s | 18 | 10 | 0.525 | 0.525 | high_route | 0.5123 |
| duration_word_count | tier3_word_count | 18 | 10 | 0.237 | 0.762 | low_route | 0.9526 |
| transcript_speech | mean_speech_density | 18 | 10 | 0.575 | 0.575 | high_route | 0.3301 |

## Matched-question lift from cached per-question files

This uses cached per-question score tables only; no judging was rerun.

| source | comparison | matched | n_questions | n_videos | mean_delta | wins | losses | ties |
|---|---|---|---|---|---|---|---|---|
| surgical_adqa | gap_targeted_minus_baseline | 1 | 60 | 43 | 0.167 | 20 | 2 | 38 |
| surgical_adqa | gap_targeted_minus_baseline | 0 | 235 | 59 | 0.051 | 48 | 28 | 159 |
| necessity_rematch | tribe_minus_baseline | 1 | 62 | 44 | 0.008 | 1 | 0 | 61 |
| necessity_rematch | tribe_minus_baseline | 0 | 158 | 44 | 0.003 | 6 | 4 | 148 |
| necessity_rematch | vlm_minus_baseline | 1 | 62 | 44 | -0.056 | 2 | 8 | 52 |
| necessity_rematch | vlm_minus_baseline | 0 | 158 | 44 | 0.000 | 5 | 4 | 149 |

## Reviewer-safe interpretation

1. **TRIBE still earns its triage role on the corrected external ADQA target.** The best TRIBE/gap-route feature is not cleanly beaten by category-only, transcript/speech, or duration/word-count baselines, and the top-20% queue catches materially more ADQA failures than random.
2. **The ensemble-failure result remains underpowered.** With only two positives, high AUC/top-k numbers should be described as corroborative, not definitive.
3. **Cheap transcript/speech proxies are useful confounds but not replacements.** They sometimes score respectably, especially when the reverse direction is allowed, but the raw high-risk interpretation is unstable and category-shuffle checks are weaker than the TRIBE gap queue on the key ADQA target.
4. **Route-label numbers are not independent proof.** They confirm cheap proxies do not trivially reproduce the cached TRIBE route labels, but the labels were generated from TRIBE signals.

## Artifacts

- `cursor/research/output/parallel_research/cheap_baselines/external_features.csv`
- `cursor/research/output/parallel_research/cheap_baselines/auc_summary.csv`
- `cursor/research/output/parallel_research/cheap_baselines/topk_curves.csv`
- `cursor/research/output/parallel_research/cheap_baselines/family_winners.csv`
- `cursor/research/output/parallel_research/cheap_baselines/route_label_rows.csv`
- `cursor/research/output/parallel_research/cheap_baselines/route_label_auc.csv`
- `cursor/research/output/parallel_research/cheap_baselines/matched_question_lift.csv`
- `cursor/research/output/parallel_research/cheap_baselines/summary.json`
