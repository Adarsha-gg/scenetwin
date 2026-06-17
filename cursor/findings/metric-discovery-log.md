# Metric discovery leaderboard
Updated 2026-05-27T20:34:11Z. Total recipes tried: **80**

| iteration | recipe | best target | value | tier ρ |
|-----------|--------|-------------|------:|-------:|
| 6 | `(read_s) / (adqa_t3_minus_t0 + 1e-6)` | auc_critical_miss | 1.000 | 0.242 |
| 24 | `((need_mean) - (speech_mean)) * extended_seconds_f` | auc_judge_disagree | 1.000 | 0.000 |
| 24 | `((read_s) / (adqa_t3_minus_t0 + 1e-6)) * tier_idx` | auc_critical_miss | 1.000 | 0.929 |
| 17 | `((need_mean) - (speech_mean)) * tier_idx` | auc_judge_disagree | 1.000 | -0.685 |
| 24 | `1.0 / (abs((need_mean) - (speech_mean)) + 0.01)` | auc_judge_disagree | 1.000 | 0.000 |
| 2 | `(need_mean) - (speech_mean)` | auc_judge_disagree | 1.000 | 0.000 |
| 10 | `log1p(abs((read_s) / (adqa_t3_minus_t0 + 1e-6)))` | auc_critical_miss | 1.000 | 0.242 |
| 17 | `((read_s) / (adqa_t3_minus_t0 + 1e-6)) * need_mean` | auc_critical_miss | 0.978 | 0.197 |
| 28 | `clip_top3_spread * need_mean` | auc_low_margin | 0.964 | 0.000 |
| 28 | `(clip_top3_spread) - (crit_w_spread)` | auc_critical_miss | 0.956 | 0.000 |
| 27 | `(clip_norm) - (speech_mean)` | auc_judge_disagree | 0.938 | 0.706 |
| 26 | `(need_std) - (speech_mean)` | auc_judge_disagree | 0.938 | 0.000 |
| 20 | `(adqa_norm) - (speech_mean)` | auc_judge_disagree | 0.938 | 0.756 |
| 27 | `(adqa_v4_score) / (crit_w + 1e-6)` | auc_gt_dispute | 0.922 | 0.593 |
| 21 | `(clip_top3_spread) - (gain_vs_cross_spread)` | auc_critical_miss | 0.911 | 0.000 |
