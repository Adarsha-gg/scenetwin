# TRIBE counterfactual re-run on SceneTwin benchmarks

## 18-clip benchmark: head-to-head vs published top features

| target | existing top | existing AUC | new top | new AUC | delta |
|---|---|---:|---|---:|---:|
| low_tier3_margin | `max_need` | 1.000 | `description_gain` | 1.000 | +0.000 |
| tier2_tier1_inversion | `mean_standard_slot_score` | 1.000 | `description_gain` | 0.941 | -0.059 |

## 60-clip external corpus: calibration test (n=60)

| feature | r vs within_clip_rho | p |
|---|---:|---:|
| `accessibility_gap` | +0.025 | 0.849 |
| `description_gain` | -0.145 | 0.269 |
| `alignment_cosine` | -0.004 | 0.976 |

## 60-clip external: AUC predicting T3 pairwise loss

| feature | direction | AUC | AP |
|---|---|---:|---:|
| `accessibility_gap` | high_bad | 0.583 | 0.419 |
| `description_gain` | low_bad | 0.731 | 0.230 |
| `alignment_cosine` | low_bad | 0.605 | 0.137 |

## Decision criterion

- If any new feature hits **r < -0.5, p < 0.05** on the 60-clip calibration test: calibration-layer paper framing is viable.
- If new features also match published AUC >= 0.85 on the 18-clip head-to-head: paper claim becomes "directly measured neural counterfactual matches and explains heuristic slot scoring."
- Otherwise: binary review-triage framing is final.
