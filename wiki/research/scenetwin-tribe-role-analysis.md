---
title: TRIBE's actual role in the SceneTwin pipeline (honest analysis)
category: research
tags: [scenetwin, tribe, paper-section, calibration, abstention, triage]
sources: [output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv, output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv]
created: 2026-05-29
updated: 2026-06-23
---

## Headline

After measurement: **TRIBE-derived per-clip features do NOT correlate significantly with continuous ensemble noise**. TRIBE's role is **review triage / blind-spot routing**, not continuous calibration or AD ranking. The original in-benchmark `all4_fail` forecast remains pilot/supporting evidence (AUC=1.00 on n=2 positives, with family-wise caveat), while the stronger current external support is the 60-clip cheap-baseline gauntlet: `accessibility_gap` predicts corrected ADQA failures at AUC=0.794 and survives within-category shuffling (p=0.003).

## 2026-06-23 update — current safe role

- **Use TRIBE as a side-car queue/router.** It can prioritize review and expose typed access windows before a candidate AD exists.
- **Do not call it a scorer.** Per-clip TRIBE features cannot change within-clip AD rank order; TTS-audio NCR also landed near chance globally.
- **Do not call it necessary or VLM-superior.** The fair wording is: distinct, competitive, and useful for triage/authoring hypotheses that CLIP+ADQA or humans/VLMs verify.
- **Report operational metrics.** External ADQA failure triage by `accessibility_gap` (AUC=0.794, category-shuffle p=0.003) and mean-gap review-budget curves are safer than the old in-benchmark AUC=1.00 headline.

## What we tested

For each of 18 benchmark clips, computed:

- `within_clip_rho` = Spearman rho of `ensemble_mean_clip_mean` against `gt` *within* that clip (4 tier observations per clip). High = ensemble correctly orders tiers; low = noisy/wrong.

Then swept 12 per-clip TRIBE features against `within_clip_rho`:

| feature | corr with within_clip_rho | p | direction |
|---|---:|---:|---|
| `need_entropy` | -0.342 | 0.165 | mixed |
| `extended_seconds_frac` | -0.229 | 0.361 | weak |
| `risk_score` | -0.187 | 0.458 | weak |
| `mean_standard_slot_score` | -0.187 | 0.458 | weak |
| `tribe_pressure` | -0.178 | 0.479 | weak |
| `max_need` | +0.229 | 0.361 | weak (wrong sign) |
| `mean_speech_density` | +0.157 | 0.533 | weak (wrong sign) |
| `high_need_seconds_frac` | -0.138 | 0.585 | weak |
| `high_need_frac` | -0.139 | 0.583 | weak |
| `mean_need` | -0.119 | 0.637 | weak |
| `mean_extended_need_score` | +0.078 | 0.759 | weak (wrong sign) |
| `duration_s` | +0.074 | 0.770 | weak (wrong sign) |

**None reach p < 0.15.** The strongest negative correlation is need_entropy at r=-0.34, still p=0.17. TRIBE does not predict continuous ensemble quality.

## Path 2 gated pipeline simulation (existing features)

Tried gating the ensemble: high-pressure clips -> ADQA only; low-pressure clips -> CLIP+ADQA.

| Threshold (tribe_pressure quantile) | Gated rho | Routed obs to ADQA-only |
|---|---:|---:|
| q25 | 0.848 | 52/72 |
| q33 | 0.850 | 48/72 |
| q50 | 0.848 | 36/72 |
| q67 | 0.892 | 24/72 |
| q75 | 0.902 | 16/72 |
| baseline ungated | **0.929** | n/a |

Inverted gating reaches 0.918 at best. **Every gating threshold hurts the headline rho.** Path 2 is not viable.

## Path 3 selective-prediction curve

Abstain on the top-k highest-TRIBE-risk clips; compute rho on the remaining (kept) clips:

| abstain_k | coverage | rho_kept |
|---:|---:|---:|
| 0 | 1.00 | 0.929 |
| 2 | 0.89 | 0.931 |
| 4 | 0.78 | 0.928 |
| 6 | 0.67 | 0.916 |
| 8 | 0.56 | 0.927 |

Curve is flat within 0.013. Abstaining does not reliably improve rho.

## Where TRIBE actually works

The original TRIBE forecast targets `all4_fail` (all-4-judge ADQA ensemble fails full ordering). This is a *binary* pilot event affecting only 2/18 clips: clips 12 and 15.

- `mean_standard_slot_score` ranks clip 12 #1 and clip 15 #2 -> recall@2 = 100%, AUC = 1.00 on n=2 positives.
- Review budget: 2/18 = 11.1%.
- Treat as pilot/supporting evidence because feature-family correction weakens the claim; the external 60-clip ADQA-failure triage result is the safer current headline.

This is useful triage evidence. It's just *not* the same task as continuous ranking quality calibration.

## The mismatch: TRIBE's target vs the ensemble's failure mode

The 3 clips mis-ordered by `ensemble_mean_clip_mean` are {0, 12, 14}. The 2 clips flagged by `all4_fail` are {12, 15}. **Overlap = 1**. TRIBE forecasts a different failure mode than the headline rho measures.

This is not a contradiction or a failure; it just means the two artifacts in the pipeline address different deployment risks:

- **CLIP+ADQA ensemble**: continuous ranking quality across the 4-tier ladder
- **TRIBE forecast**: binary "this clip will defeat ANY all-4-judge ensemble" event

A deployable AD audit pipeline cares about both: the metric tells you which AD to ship; the forecast tells you which clip's metric output to second-guess.

## Recommended paper framing (replaces earlier "calibration layer" framing)

> We contribute two reference-free components: (1) a CLIP + frame-grounded ADQA ensemble that ranks AD candidates at Spearman rho = 0.929 in-benchmark and 0.873 on 60 external clips, and (2) a brain-aligned binary review-triage flag derived from TRIBE need-window features that recalls 100% of all-4-judge ranking failures at an 11% review budget (AUC = 1.00). Together they constitute a deployable AD audit pipeline: the ensemble scores AD candidates, and the triage flag identifies the small subset where ranking confidence cannot be inferred from the ensemble alone. Without the triage flag, safe deployment requires exhaustive human review; with it, 11% review suffices to catch all severe failures observed in the benchmark.

This framing is partly superseded by the 2026-06-23 update above: keep the two-component audit-pipeline framing, but avoid “structurally necessary” language. TRIBE should be presented as a useful, distinct review-priority and routing side-car whose claims are strongest in external ADQA-failure triage and matched-window mechanisms.

## Open question — RESOLVED 2026-05-29 (Colab notebook returned)

The new TRIBE counterfactual proxy (`accessibility_gap`, `description_gain`, `alignment_cosine`) was computed on all 18 in-benchmark clips. Results:

### Calibration test (the key measurement)

Spearman correlation with per-clip continuous ensemble noise (`within_clip_rho`):

| feature | r | p | notes |
|---|---:|---:|---|
| `accessibility_gap` | **-0.453** | 0.059 | strongest TRIBE-calibration signal observed; just misses p<0.05 |
| `alignment_cosine` | -0.392 | 0.108 | direction correct; weaker |
| `description_gain` | -0.192 | 0.444 | not significant |

**Superseded interim result.** At this point, `accessibility_gap` looked promising on n=18 (`|r| = 0.453`, p=0.059), but the later 60-clip external rerun below killed the calibration-layer interpretation. Keep this paragraph only as methodological history, not as active paper framing.

### AUC vs existing failure targets

| Target | Feature | AUC | vs existing top |
|---|---|---:|---|
| `all4_fail` | accessibility_gap | 0.875 | below `mean_standard_slot_score` at 1.000 |
| `low_tier3_margin` | **description_gain** | **1.000** | **ties** `max_need` (the existing top) |
| `tier2_tier1_inversion` | description_gain | 0.941 | below `mean_standard_slot_score` at 1.000 |
| `quality_risk_fail` | accessibility_gap | 0.875 | (same as all4_fail by construction) |

**Headline:** `description_gain` matches the published top forecast feature on `low_tier3_margin`. This is a theoretically motivated brain-counterfactual replacement for a slot-score heuristic, at parity AUC.

### What this meant before external validation

At the n=18 stage, calibration looked borderline and `description_gain` matched existing features on `low_tier3_margin`. The external 60-clip rerun below supersedes this: calibration framing is closed, and counterfactual features should be described only as moderate triage/interpretability signals.

### External 60-clip re-run — RESOLVED 2026-05-29 (calibration story closed)

The Colab notebook returned external counterfactual features for all 60 clips. The calibration test at n=60 with min detectable r = 0.36:

| Feature | r vs within_clip_rho_ext | p |
|---|---:|---:|
| accessibility_gap | **+0.025** | 0.849 |
| description_gain | -0.145 | 0.269 |
| alignment_cosine | -0.004 | 0.976 |

**The calibration correlation vanishes externally.** The 18-clip r = -0.453 was a small-sample artifact, not a real effect. Direction even flips for accessibility_gap (from -0.453 to +0.025). At n=60 with proper power, none of the new TRIBE counterfactual features predict continuous ensemble noise.

### External 60-clip T3 pairwise loss forecast

The 60-clip external corpus has 6 T3 pairwise loss events. AUC of each new feature:

| Feature | AUC | AP | Direction |
|---|---:|---:|---|
| description_gain | **0.731** | 0.230 | low_bad |
| alignment_cosine | 0.605 | 0.137 | low_bad |
| accessibility_gap | 0.583 | 0.419 | high_bad |

The strongest external signal is `description_gain` at AUC=0.731 — a moderate signal but well below the 18-clip `mean_standard_slot_score` AUC=1.000 baseline. **No external feature matches the binary all4_fail forecast that drives our published 11% review budget claim.**

### Final paper framing (decision locked)

The honest TRIBE contribution is:

1. **On the 18-clip benchmark**: binary review-triage flag at AUC=1.00, recall@2/18=100%, 11.1% review budget. Driven by `mean_standard_slot_score` (heuristic slot-score feature, not counterfactual).

2. **On the 60-clip external corpus**: counterfactual features (accessibility_gap, description_gain) provide moderate T3-pairwise-loss prediction (best AUC=0.731 from description_gain) but do NOT calibrate continuous ensemble noise.

3. **Calibration-layer paper framing is closed.** The 18-clip emerging signal did not generalize.

The paper claim is the binary triage flag on in-bench, with honest acknowledgement that the counterfactual features provide a theoretically motivated alternative at parity AUC on `low_tier3_margin` but do not extend to continuous calibration externally.

## See Also

- [[research/scenetwin-tribe-failure-forecast]] -- the AUC=1.00 / recall@2 forecast (this analysis confirms it)
- [[research/scenetwin-tier-ordering-failures]] -- the 3 mis-ordered clips (different from the 2 all4_fail clips)
- [[research/scenetwin-external-validation]] -- external generalization (ensemble-only, no TRIBE)

## Sources

- `cursor/research/output/scenetwin_per_clip_tribe_calibration.csv` (per-clip table)
- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (per-tier ensemble)
- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv` (per-clip TRIBE features)
