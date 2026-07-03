---
title: "SceneTwin Loop D7/D8 — Fused Error Detector & Operating Points"
category: research
tags: [scenetwin, error-detection, fusion, operating-points, decision-curve, halluc-gate]
created: 2026-07-02
---

# D7/D8 — Fused Error Detector & Operating Points

Cached-data-only analysis (Python stdlib), on the 60-clip halluc-gate set
(`cursor/output/halluc_gate/halluc_gate.csv`). Detection framing:
**positives = fabrication drops (60)**, **negatives = paraphrase drops (60)**;
AUC = P(fab drop > para drop). Regenerate with
`cursor/research/loop_d7d8_fusion_oppoints.py`.

## D7 — Fused error detector

Each drop signal was z-normalized over its own pooled fab+para values (120
points/signal), then fused per clip.

| Detector | fab-vs-paraphrase AUC |
|---|---|
| CLIP-drop (single) | **0.835** |
| ADQA-drop (single) | **0.801** |
| Fusion (a) MEAN | **0.904** |
| Fusion (b) MAX = shared-threshold OR | 0.902 |

- **Best fusion = MEAN, AUC 0.904**, label-permutation p < 1e-4 (20k shuffles,
  best-direction).
- **Fusion beats the best single signal (CLIP 0.835) by +0.069 AUC** — a real
  but modest gain. MAX/OR is essentially tied with MEAN (0.902).
- Note: MAX fusion and a *shared-threshold* OR rule are algebraically identical
  (`max(a,b) > t` iff `a > t or b > t`), so they yield one ROC.

**OR rule with independent per-signal thresholds** (flag if either drop exceeds
its own chosen threshold, each set at its own target FPR on the paraphrase
negatives):

| per-signal FPR target | OR recall | combined FPR |
|---|---|---|
| 5% | 70.0% (42/60) | 8.3% (5/60) |
| 10% | 85.0% (51/60) | 18.3% (11/60) |
| 20% | 91.7% (55/60) | 33.3% (20/60) |

The OR rule confirms the D1 complementarity story: recall climbs steeply (up to
91.7%) because the two signals miss different clips — but the false-alarm rate
roughly doubles because each signal's alarms add. For a *matched* false-alarm
budget the smooth MEAN-fusion score (below) is the better operating detector.

## D8 — Operating points / decision curve

Best detector for the decision curve = **MEAN fusion**. FPR is measured on the
60 paraphrase negatives.

### Recall (sensitivity) at fixed FPR

| Detector | FPR=5% | FPR=10% | FPR=20% |
|---|---|---|---|
| CLIP-drop | 51.7% | 71.7% | 76.7% |
| ADQA-drop | 40.0% | 53.3% | 70.0% |
| **MEAN fusion** | **66.7%** | **75.0%** | **86.7%** |

Fusion dominates both single signals at every operating point (e.g. +15 pts of
recall over CLIP and +22 pts over ADQA at 5% FPR).

### PPV (precision) at the 10% FPR operating point

Formula: **PPV = (π·TPR) / (π·TPR + (1−π)·FPR)**, π = real-world AD-fabrication
base rate.

| Detector | TPR@10% | FPR | PPV@π=5% | PPV@π=15% | PPV@π=30% |
|---|---|---|---|---|---|
| CLIP-drop | 71.7% | 10% | 27.4% | 55.8% | 75.4% |
| ADQA-drop | 53.3% | 10% | 21.9% | 48.5% | 69.6% |
| **MEAN fusion** | 75.0% | 10% | **28.3%** | **57.0%** | **76.3%** |

Precision is base-rate-driven: if only 5% of AD is fabricated, ~7 in 10 flags at
this operating point are false alarms even for the best detector. The tool is a
review-triage aid, not an autonomous gate.

### Net-benefit / decision-curve read

Net benefit at harm-threshold probability pt (odds O = pt/(1−pt)):
`NB(model)=TPR·π − FPR·(1−π)·O`; `NB(review-all)=π − (1−π)·O`;
`NB(review-none)=0`. Flagging (MEAN fusion, TPR 75% / FPR 10%) is the best of
the three strategies for pt inside the window below:

| base rate π | pt_low | pt_high |
|---|---|---|
| 5% | 1.4% | 28.3% |
| 15% | 4.7% | 57.0% |
| 30% | 10.6% | 76.3% |

**One-line read:** below pt_low the harm threshold is so low you should just
*review everything*; above pt_high it is so high you should *review nothing*;
between them **flagging with the fused detector is the highest-net-benefit
strategy** — and that useful window widens as the fabrication base rate rises
(only ~1.4–28% at π=5%, but ~11–76% at π=30%).

## Honest interpretation

- Fusion is a genuine, permutation-significant improvement (+0.069 AUC → 0.904)
  and dominates every single-signal operating point. The gain is real but
  incremental, not transformational.
- MEAN and MAX/OR fusions are statistically indistinguishable here (0.904 vs
  0.902); MEAN is preferred as a smooth score with a single tunable threshold.
- Precision at deployment is dominated by the true base rate, not the detector:
  at a realistic low base rate the majority of flags are false alarms, so this
  is triage, not adjudication.

## Limitations

- n = 60 clips; AUC differences of ~0.03 (MEAN vs MAX) are within noise.
- Negatives are *paraphrase* controls, not naturally occurring correct AD; the
  fab/para contrast may overstate separability vs. real-world review streams.
- z-normalization uses the pooled fab+para values (in-sample); a deployed
  detector would need held-out normalization constants.
- Base rates (5/15/30%) are assumed, not measured — PPV/net-benefit numbers are
  scenarios, not observed precision.
- Real-world fabrication base rate for professional AD is unknown; the
  decision-curve windows are the actionable output, not a single point estimate.

## Sources
- `cursor/output/halluc_gate/halluc_gate.csv`
- `cursor/research/loop_d7d8_fusion_oppoints.py`
- Baselines & complementarity: `cursor/research/new_directions_run.py` (D1)
