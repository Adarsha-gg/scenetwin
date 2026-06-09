# Wrong-content gate: deployment base-rate precision (round 69, claude)

**Date:** 2026-06-09
**Angle:** `wrong_content_gate`

## Claim

The locked wrong-content catch (gate_outcome 100% / 0%; LOCO single-AD 98.3% / 2.2%)
is measured at **balanced** prevalence. In deployment, catastrophic wrong-content ADs
are rare, and a 2.2% false-alarm rate then dominates: **precision collapses** even though
recall stays at 98%. But the cost asymmetry (a wrong AD shipped to a blind viewer >> a
wasted re-review) keeps the gate net-beneficial down to very low prevalence.

## Method (no model calls, no re-fit)

Read the already-locked single-AD operating point from `wrong_content_global_gate.json`
(leave-one-clip-out, never fit on the scored clip): **TPR = 0.983, FPR = 0.022**. Propagate
through realistic base rates via Bayes' rule:
`PPV = pi·TPR / (pi·TPR + (1-pi)·FPR)`. No pool re-ranking, no threshold re-fit — this is a
pure deployment-realism propagation of the locked numbers.

## Result

| base rate | precision (PPV) | recall | alert rate | NNR | missed/10k |
|---|---:|---:|---:|---:|---:|
| 0.50 | 97.8% | 98.3% | 50.3% | 1.0 | 83.3 |
| 0.10 | 83.1% | 98.3% | 11.8% | 1.2 | 16.7 |
| 0.05 | 70.0% | 98.3% | 7.0% | 1.4 | 8.3 |
| 0.02 | 47.4% | 98.3% | 4.1% | 2.1 | 3.3 |
| 0.01 | **30.9%** | 98.3% | 3.2% | 3.2 | 1.7 |
| 0.005 | 18.2% | 98.3% | 2.7% | 5.5 | 0.8 |

At a 1% wrong-content base rate, **2 of every 3 alerts are false** (PPV 31%, NNR 3.2):
the headline "100% catch" hides a classic base-rate fallacy that no prior round in this
loop stated.

## What rescues it: cost asymmetry

Break-even cost ratio (min cost(miss)/cost(review) for the gate to beat shipping
everything unreviewed):

| base rate | min cost ratio |
|---|---:|
| 0.05 | 0.4x |
| 0.01 | 2.2x |
| 0.005 | 4.5x |
| 0.002 | 11.3x |

A wrong-content AD shipped to a blind/low-vision viewer (the entire failure mode SceneTwin
exists to prevent) plainly costs far more than a few minutes of human re-review. So even at
0.2% prevalence the gate is justified as long as one missed error is worth >=11 wasted
reviews — a threshold it clears by orders of magnitude. The gate is **low-precision but
correctly-calibrated for an asymmetric-cost safety screen**, not a high-precision classifier.

## Honest scope

- Recall (catch) is the locked, validated number; only precision is base-rate dependent.
- Conservative fixed T=0.15 (FPR=0 in-sample) gives PPV~100% at any prevalence but drops
  recall to 90% — a precision/recall operating-point choice the deployer can pick per cost
  ratio.
- Still blind to relational/action/count lies (round 3) — those sit inside the legit raw-CLIP
  band and never trip this gate at any prevalence.

## Artifacts

- `cursor/pipeline/gate_deployment_precision.py`
- `cursor/output/gate_deployment_precision.json`
- `output/charts/scenetwin_gate_deployment_precision.png`
