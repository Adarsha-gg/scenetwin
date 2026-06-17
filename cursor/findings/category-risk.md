# Category risk analysis

Source: `cursor/output/category_risk_summary.csv`

## Headline

- Spearman(TRIBE standard-slot score, judge fragility) = **0.599** (p = 0.0087, n = 18)
- Highest mean risk category: **Sports** (mean risk 0.112)

## By category

| category       |   n_clips |   mean_risk_score |   mean_tribe_pressure |   mean_high_need_frac |   mean_speech_density |   judge_failures |   tier3_weak_count |   extended_ad_count |
|:---------------|----------:|------------------:|----------------------:|----------------------:|----------------------:|-----------------:|-------------------:|--------------------:|
| Sports         |         5 |         0.112099  |              0.752063 |              0.677727 |              0.809091 |                1 |                  1 |                   3 |
| Pets & Animals |         5 |         0.081625  |              0.739691 |              0.621379 |              0.807992 |                1 |                  1 |                   3 |
| Food & Cooking |         5 |         0.0482486 |              0.61104  |              0.472448 |              0.825175 |                0 |                  2 |                   2 |
| Travel         |         3 |         0         |              0.558769 |              0.439394 |              1        |                0 |                  0 |                   2 |

## Interpretation

Sports clips cluster toward extended-AD routing and higher TRIBE pressure.
Food & Cooking clips often have talky audio (high speech density), lowering
review priority even when visual action is present.