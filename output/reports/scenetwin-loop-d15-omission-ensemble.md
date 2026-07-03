---
title: "D15 - Omission-Aware Ensemble: Fold Omission into Ranking, or Keep it Separate?"
category: research
tags: [scenetwin, ensemble, omission, ranking, ablation, null-result]
created: 2026-07-02
---

# D15 - Omission-Aware Ensemble

**Question.** Round-2 synthesis flagged omission as the biggest untapped signal (D6
clip-level detection AUC 0.945; D2: gold ADs state the key visual fact only 61.8% of
the time). Does adding an omission-sensitivity term to the CLIP+ADQA **ranking** score
(a) improve the corrected three-tier ladder Spearman rho, and (b) recover the two known
T1-beats-T3 pairwise losses? Or is omission better kept as a separate **detection**
signal?

Script: `cursor/research/loop_d15_omission_ensemble.py` (stdlib only, deterministic
seed=7). Reproduces the headline via the same method as
`cursor/research/recompute_corrected_ladder.py`.

## Setup

- Data: `cursor/output/external_ensemble_eval.csv` (60-clip ladder). Drop the invalid
  `tier2_vatex_long` rung; order **T0 (cross-decoy) < T1 (vatex short) < T3 (pro AD)**.
- Per-clip min-max normalise `clip_top3` and `adqa_score` over the 3 tiers;
  `ensemble = 0.5*clip_n + 0.5*adqa_n`. n = 60 clips, 180 observations.
- **Omission proxy (labelled proxy).** No true per-tier omission score is cached for the
  ladder tiers - D6's omission labels live on the halluc-gate expert-vs-hallucinated
  set, not on T0/T1/T3. We use **`adqa_yes_rate`** = fraction of the 5 frame-grounded
  visual questions the AD answers "yes" = **coverage** of probed visual facts. Low
  yes-rate => the AD omitted the probed content. Penalising omission == rewarding
  coverage: `score(w) = (1-w)*ensemble + w*coverage_norm`, where `coverage_norm` is the
  per-clip min-max of `adqa_yes_rate` (same scheme as the other signals).

## Task 1 - Baselines (reproduced)

| signal | rho vs gt |
|---|---|
| **ensemble (0.5 clip + 0.5 adqa)** | **0.9516** (target 0.9516) |
| adqa_norm alone | 0.9462 |
| clip_norm alone | 0.8283 |
| coverage proxy (adqa_yes_rate) alone | 0.8005 |

Bootstrap 95% CI on the ensemble rho is **[0.927, 0.968]** (from the headline recompute);
min detectable rho at n=180 is ~0.21. **Pearson(coverage_norm, adqa_norm) = 0.847** - the
proxy is drawn from ADQA, so folding it in is close to re-weighting ADQA.

## Task 2 - Omission-aware weight sweep

| w | rho | delta vs baseline |
|---|---|---|
| 0.00 | 0.9516 | +0.0000 |
| 0.05 | 0.9587 | +0.0071 |
| **0.10** | **0.9597** | **+0.0081** |
| 0.15 | 0.9591 | +0.0075 |
| 0.20 | 0.9581 | +0.0065 |
| 0.25 | 0.9548 | +0.0032 |
| 0.30 | 0.9533 | +0.0017 |
| 0.40 | 0.9514 | -0.0002 |
| 0.50 | 0.9501 | -0.0015 |

There is a shallow bump peaking at **w=0.10 (rho 0.9597, +0.0081)**, then monotone decline;
by w>=0.4 it is net negative. The peak gain (**+0.008**) is roughly **1/5 of the bootstrap
CI half-width (~0.02)** and does not move the permutation p (0.0002 at both w=0 and w=0.1).
**The improvement is not statistically distinguishable from baseline.**

## Task 3 - T3-loss recovery

Corrected-ladder pairwise set (T0<T1, T0<T3, T1<T3) = 180 pairs; baseline **178/180**
correct. The two losses are exactly the known ones, both T1-beats-T3:
`GOH6fBhoi2o` and `d7_SY48r__8` (these match the in-ladder tier1 rows of the cached
`external_t3_pairwise_losses.csv`).

| w | recovered | newly broken | net | pairwise correct |
|---|---|---|---|---|
| 0.05-0.50 | **0** | **0** | **0** | 178/180 |

**Zero recovered, zero broken at every weight.** Reason: on both failure clips the pro AD
*and* the crowd caption have `adqa_yes_rate = 0` on the probed facts, so `coverage_norm = 0`
for both tiers - the omission term contributes nothing, and the `(1-w)` factor shrinks T1
and T3 proportionally so T3 never overtakes T1. These are **CLIP-driven flips, not
omission-driven**, so a coverage/omission term is structurally blind to them.

## Verdict

**Keep omission as a separate DETECTION signal (D6); do not fold it into the RANKING
score.**

1. **No real ranking gain.** The best fold (+0.008 rho at w=0.1) is inside bootstrap
   noise and vanishes/reverses by w>=0.4. The ladder is already saturated (rho 0.95,
   178/180 pairwise) - little headroom to buy.
2. **Redundant.** The proxy correlates 0.85 with adqa_norm; the nudge is essentially
   ADQA re-weighting, not new information. Parsimony says leave the two-signal core alone.
3. **Fails on the target failures.** It recovers 0/2 known T3 losses because those are
   zero-coverage CLIP flips - the exact cases an omission term cannot see.
4. Omission's demonstrated value (D6 clip-AUC 0.945, D2 38% key-fact omission) is as a
   **standalone reference-free error detector / review flag**, not as a ranking
   ingredient.

### Caveats / BLOCKED

- **Proxy, not ground truth.** `adqa_yes_rate` is a coverage proxy for omission. A true
  per-tier omission score (D6-style key-fact mention detection run over T0/T1/T3 of the
  60-clip ladder) is **not cached** - producing one needs new probe/mention labels per
  ladder AD (blocked: no API/model calls). Spec if pursued: for each of the 180 ladder
  ADs, run the D6 phrase-match mention detector against the clip's key-fact probe set to
  get a real omission rate, then repeat this sweep. Given the null here, low priority.
- AD word-length as an alternative proxy is only partially cached
  (`all_clip_scene_model_audit/texts.csv` has `professional_ad` + `vatex_caption` word
  counts but not the `tier0_cross` decoy), so it cannot cover the full 3-tier ladder;
  not used.

## See Also

- [[research/scenetwin-loop-d6-omission]] - the standalone omission detector this defers to
- [[research/scenetwin-directions-loop]] - round-2/3 synthesis (D15 listed there)

## Sources

- `cursor/output/external_ensemble_eval.csv`
- `cursor/research/output/external_t3_pairwise_losses.csv`
- `cursor/research/recompute_corrected_ladder.py`
- `cursor/research/loop_d15_omission_ensemble.py`
