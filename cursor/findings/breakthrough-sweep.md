# Breakthrough sweep — all singles, all pairs, top triples

**Singles:** 95 | **Pairs:** 22325 | **Triples:** 1140

## Top 15 singles (any research target)

| metric | best target | AUC | tier ρ |
|--------|-------------|----:|-------:|
| `disc:mut_inv_diff(need_mean,speech_mean)` | auc_judge_disagree | 1.000 | 0.000 |
| `disc:mut_log_ratio(read_s,adqa_t3_minus_t0)` | auc_critical_miss | 1.000 | 0.242 |
| `disc:ratio(read_s,adqa_t3_minus_t0)` | auc_critical_miss | 1.000 | 0.242 |
| `disc:mut_tier_scale_diff(need_mean,speech_mean)` | auc_judge_disagree | 1.000 | -0.685 |
| `disc:diff(need_mean,speech_mean)` | auc_judge_disagree | 1.000 | 0.000 |
| `disc:mut_tier_scale_ratio(read_s,adqa_t3_minus_t0)` | auc_critical_miss | 1.000 | 0.929 |
| `disc:mut_ext_scale_diff(need_mean,speech_mean)` | auc_judge_disagree | 1.000 | 0.000 |
| `disc:mut_need_scale_ratio(read_s,adqa_t3_minus_t0)` | auc_critical_miss | 0.978 | 0.197 |
| `disc:spread_x_need(clip_top3)` | auc_low_margin | 0.964 | 0.000 |
| `disc:spread_diff(clip_top3,crit_w)` | auc_critical_miss | 0.956 | 0.000 |
| `clip_top3` | auc_low_margin | 0.946 | 0.735 |
| `disc:diff(clip_norm,speech_mean)` | auc_judge_disagree | 0.938 | 0.706 |
| `disc:diff(adqa_norm,speech_mean)` | auc_judge_disagree | 0.938 | 0.756 |
| `disc:diff(need_std,speech_mean)` | auc_judge_disagree | 0.938 | 0.000 |
| `disc:ratio(adqa_v4_score,crit_w)` | auc_gt_dispute | 0.922 | 0.593 |

## Top 20 pairwise combos

| combo | blend | best target | AUC | tier ρ |
|-------|-------|-------------|----:|-------:|
| `disc:lex_spread_proxy` + `disc:mut_ext_scale_diff(n` | max | auc_judge_disagree | 1.000 | 0.081 |
| `disc:diff(adqa_norm,speec` + `disc:skew_per_ext` | abs_diff | auc_judge_disagree | 1.000 | 0.052 |
| `disc:mut_ext_scale_peak_o` + `disc:lex_minus_clip` | harmonic | auc_ensemble_violation | 1.000 | -0.387 |
| `disc:mut_ext_scale_peak_o` + `disc:lex_minus_clip` | product | auc_ensemble_violation | 1.000 | -0.609 |
| `disc:mut_ext_scale_peak_o` + `disc:lex_minus_clip` | mean_mm | auc_ensemble_violation | 1.000 | -0.815 |
| `disc:product(read_s,exten` + `disc:ratio(read_s,adqa_t3` | harmonic | auc_critical_miss | 1.000 | 0.241 |
| `disc:diff(need_mean,speec` + `disc:product(need_mean,n_` | harmonic | auc_judge_disagree | 1.000 | 0.000 |
| `disc:std_ratio(clip_top3,` + `disc:mut_inv_diff(need_me` | max | auc_judge_disagree | 1.000 | 0.000 |
| `disc:lex_spread_proxy` + `disc:diff(adqa_v4_score,n` | abs_diff | auc_gt_dispute | 1.000 | -0.010 |
| `disc:std_ratio(clip_top3,` + `disc:mut_inv_diff(need_me` | mean_mm | auc_judge_disagree | 1.000 | 0.000 |
| `disc:product(read_s,exten` + `disc:mut_log_ratio(read_s` | harmonic | auc_critical_miss | 1.000 | 0.258 |
| `disc:diff(adqa_norm,speec` + `disc:lex_x_vt` | abs_diff | auc_judge_disagree | 1.000 | 0.252 |
| `disc:mut_ext_scale_peak_o` + `disc:mut_tier_scale_diff(` | product | auc_judge_disagree | 1.000 | -0.363 |
| `disc:diff(need_mean,speec` + `disc:cond_ext_crit` | mean_mm | auc_judge_disagree | 1.000 | -0.427 |
| `disc:lex_spread_proxy` + `disc:mut_inv_diff(need_me` | harmonic | auc_judge_disagree | 1.000 | 0.053 |
| `disc:lex_spread_proxy` + `disc:mut_inv_diff(need_me` | max | auc_judge_disagree | 1.000 | 0.285 |
| `disc:diff(adqa_norm,speec` + `disc:lex_per_need` | abs_diff | auc_judge_disagree | 1.000 | 0.509 |
| `disc:lex_spread_proxy` + `disc:mut_inv_diff(need_me` | product | auc_judge_disagree | 1.000 | 0.146 |
| `disc:lex_spread_proxy` + `disc:mut_inv_diff(need_me` | mean_mm | auc_judge_disagree | 1.000 | 0.297 |
| `disc:diff(adqa_norm,speec` + `disc:mut_inv_diff(need_me` | mean_mm | auc_judge_disagree | 1.000 | 0.596 |

## Top 15 triple blends (top-20 singles)

| triple | best target | AUC | tier ρ |
|--------|-------------|----:|-------:|
| `triple:disc:mut_tier_scale_diff(need_mean,speech_mean)|disc:spread_dif` | auc_judge_disagree | 1.000 | -0.390 |
| `triple:disc:ratio(read_s,adqa_t3_minus_t0)|disc:mut_tier_scale_diff(ne` | auc_judge_disagree | 1.000 | -0.417 |
| `triple:disc:mut_inv_diff(need_mean,speech_mean)|disc:spread_diff(clip_` | auc_judge_disagree | 1.000 | -0.601 |
| `triple:disc:ratio(read_s,adqa_t3_minus_t0)|disc:mut_tier_scale_diff(ne` | auc_judge_disagree | 1.000 | -0.051 |
| `triple:disc:mut_inv_diff(need_mean,speech_mean)|novel:inversion_mass_a` | auc_judge_disagree | 1.000 | 0.000 |
| `triple:disc:ratio(read_s,adqa_t3_minus_t0)|disc:mut_tier_scale_diff(ne` | auc_judge_disagree | 1.000 | -0.027 |
| `triple:disc:mut_inv_diff(need_mean,speech_mean)|novel:visual_lexicon_p` | auc_judge_disagree | 1.000 | 0.264 |
| `triple:disc:mut_inv_diff(need_mean,speech_mean)|novel:visual_lexicon_p` | auc_judge_disagree | 1.000 | -0.462 |
| `triple:disc:mut_inv_diff(need_mean,speech_mean)|disc:std_ratio(clip_to` | auc_judge_disagree | 1.000 | -0.711 |
| `triple:disc:mut_tier_scale_diff(need_mean,speech_mean)|disc:mut_need_s` | auc_judge_disagree | 1.000 | -0.027 |
| `triple:disc:mut_log_ratio(read_s,adqa_t3_minus_t0)|disc:ratio(read_s,a` | auc_critical_miss | 1.000 | 0.244 |
| `triple:disc:mut_tier_scale_diff(need_mean,speech_mean)|disc:mut_need_s` | auc_judge_disagree | 1.000 | -0.051 |
| `triple:disc:mut_log_ratio(read_s,adqa_t3_minus_t0)|disc:ratio(read_s,a` | auc_critical_miss | 1.000 | 0.238 |
| `triple:disc:spread_x_need(clip_top3)|clip_top3|disc:ratio(adqa_v4_scor` | auc_low_margin | 1.000 | 0.631 |
| `triple:disc:mut_tier_scale_diff(need_mean,speech_mean)|disc:mut_need_s` | auc_judge_disagree | 1.000 | -0.435 |

## Best per target

- **ensemble_violation**: `pair:disc:peak_minus_lex|disc:lex_minus_clip|harmonic` → **1.000** (kind=pair)
- **critical_miss**: `pair:disc:mut_inv_diff(need_mean,speech_mean)|disc:mut_tier_scale_ratio(read_s,a` → **1.000** (kind=pair)
- **judge_disagree**: `disc:mut_inv_diff(need_mean,speech_mean)` → **1.000** (kind=single)
- **gt_dispute**: `pair:disc:ratio(adqa_v4_score,crit_w)|novel:temporal_misalign|mean_mm` → **1.000** (kind=pair)
- **low_margin**: `pair:disc:peak_over_words|disc:spread_x_need(clip_top3)|abs_diff` → **1.000** (kind=pair)

## QC gate

- Gated ensemble tier ρ: **0.890** (baseline ensemble_v4: **0.879**)
- Risk composite AUC violation: **0.822**

## Breakthrough callouts

- `disc:mut_inv_diff(need_mean,speech_mean)` → auc_judge_disagree **1.000**
- `disc:mut_log_ratio(read_s,adqa_t3_minus_t0)` → auc_critical_miss **1.000**
- `disc:ratio(read_s,adqa_t3_minus_t0)` → auc_critical_miss **1.000**
- `disc:mut_tier_scale_diff(need_mean,speech_mean)` → auc_judge_disagree **1.000**
- `disc:diff(need_mean,speech_mean)` → auc_judge_disagree **1.000**
- `disc:mut_tier_scale_ratio(read_s,adqa_t3_minus_t0)` → auc_critical_miss **1.000**
- `disc:mut_ext_scale_diff(need_mean,speech_mean)` → auc_judge_disagree **1.000**
- `pair:disc:lex_spread_proxy|disc:mut_ext_scale_diff(need_mean,speech_mean)|max` → auc_judge_disagree **1.000**
- `pair:disc:diff(adqa_norm,speech_mean)|disc:skew_per_ext|abs_diff` → auc_judge_disagree **1.000**
- `pair:disc:mut_ext_scale_peak_over_words|disc:lex_minus_clip|harmonic` → auc_ensemble_violation **1.000**
