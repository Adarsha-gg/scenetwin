---
title: "SceneTwin Loop D9/D10 — Paraphrase False-Alarm Audit & Severity-Weighted Error Score"
category: research
tags: [halluc-gate, paraphrase, false-alarm, severity, clip, adqa, deployability]
created: 2026-07-02
---

# D9/D10 — Paraphrase False-Alarm Audit & Severity Weighting

Cached-data-only analysis. Data: `cursor/output/halluc_gate/halluc_gate.csv` (60
clips, faithful-paraphrase + fabrication variants of each professional AD) and
`cursor/output/relational_hallucination_probe_set/probes.csv` (76 probes over 23
clips). Script: `cursor/research/loop_d9d10_falsealarm_severity.py`. Stdlib only.

Signed "drop" = `expert − variant` (higher ⇒ the variant looks worse ⇒ flag).
Paraphrases are **faithful** and should NOT be flagged (false alarms).
Fabrications SHOULD be flagged (true positives / recall).

---

## D9 — Paraphrase false-alarm audit

### 1. Naive SIGN rule is undeployable for CLIP

Flag whenever drop > 0:

| Signal | Paraphrase false-alarm | Fabrication recall |
|---|---|---|
| CLIP sign | **65.0%** (39/60) | 95.0% |
| ADQA sign | 18.3% (11/60) | 70.0% |

Raw-sign CLIP flags **two-thirds of faithful paraphrases** — it fires on almost
any wording change, so its 95% recall is meaningless in isolation. ADQA's sign
rule looks better only because ADQA is a coarse 0.1-grid score: on paraphrases it
is a tie 41/60 times, drops 8/60, and actually *rises* 11/60 (paraphrase can
nudge frame-QA up). The 18.3% is really "the 11 clips where re-wording happened to
cost an ADQA point," not a principled signal.

### 2. MAGNITUDE threshold calibrated to a 10% paraphrase false-alarm budget

Pick the drop threshold that flags only ~10% (6/60) of paraphrases, then measure
fabrication recall at that operating point:

| Signal | Threshold | Achieved para FA | Fabrication recall |
|---|---|---|---|
| CLIP magnitude | 0.0256 | 10.0% (6/60) | **65.0%** (39/60) |
| ADQA magnitude | 0.1000 | 10.0% (6/60) | 53.3% (32/60) |

Threshold-free separability (AUC of fabrication-drop > paraphrase-drop):
**CLIP 0.835, ADQA 0.801** — both signals genuinely separate real fabrications
from faithful paraphrase by *magnitude*, which the sign rule throws away.

### 3. Drop distributions (mean / median / max)

| Signal | Paraphrase drop | Fabrication drop |
|---|---|---|
| CLIP | +0.0077 / +0.0060 / +0.0473 | +0.0369 / +0.0339 / +0.1089 |
| ADQA | −0.0183 / +0.0000 / +0.2000 | +0.1683 / +0.2000 / +0.6000 |

Fabrication drops are ~5x (CLIP) and much larger (ADQA) than paraphrase drops in
the mean, and the paraphrase *max* (CLIP 0.047, ADQA 0.20) sets the natural
false-alarm floor a magnitude gate must clear. ADQA's paraphrase median is exactly
0 (mean slightly negative), confirming faithful re-wording is essentially
score-neutral for frame-QA.

### D9 conclusion — what is deployable

- **Sign rules are not deployable**, especially CLIP (65% false-alarm). The known
  caveat is real and severe.
- **Magnitude-thresholding is the deployable signal.** At a fixed 10% paraphrase
  false-alarm budget, **CLIP magnitude is the single best deployable gate (65%
  recall)**, beating ADQA magnitude (53%). CLIP recovers its full 95% sign-rule
  recall only by accepting 65% false alarms; forcing a sane FA budget shows its
  real usable recall is ~65%.
- Recommended deployment: a CLIP-magnitude gate at ~0.026, optionally OR'd with an
  ADQA-magnitude gate, rather than any sign-based rule.

---

## D10 — Severity-weighted error score

### Severity proposal & justification

Using `probe_type` as a severity proxy. Errors that change *who/what is acting or
how things relate* mislead a blind/low-vision listener about the event itself,
whereas miscounts are less catastrophic and pure object-attribute swaps least so:

- **High (3):** `who_role`, `action_relation`, `spatial_relation`
- **Medium (2):** `count`
- **Low (1):** object attribute — *not present as a probe_type in this set*

Per-clip severity = mean probe weight. Probe-level type counts (76 probes):
`action_relation` 37, `spatial_relation` 16, `count` 13, `who_role` 10.

### Does higher severity predict larger detector drops? (23 clips)

Spearman, per-clip mean severity vs fabrication drop magnitude:

| Correlation | rho | perm p |
|---|---|---|
| severity vs CLIP drop | +0.148 | 0.498 |
| severity vs ADQA drop | +0.010 | 0.966 |

Group means, natural high-vs-low split (`is_relation_action_count`: 5 relation/
action/count clips vs 18 object/scene clips):

| Signal | High-severity (n=5) | Low-severity (n=18) | AUC(high>low) |
|---|---|---|---|
| CLIP drop | +0.0364 | +0.0474 | 0.356 |
| ADQA drop | +0.1200 | +0.1333 | 0.544 |

The `probe_type` weighting is **near-constant**: 3 of 4 types map to "high", so
17/23 clips are all-high (mean severity distribution min 2.0, median 3.0, max
3.0). Splitting all-high (n=17) vs contains-a-count-probe (n=6): CLIP +0.0471 vs
+0.0391, ADQA +0.1353 vs +0.1167.

### D10 conclusion — honestly, severity weighting is NOT supported

The cached signals do **not** support severity weighting. Correlations are ~0 and
non-significant (rho +0.15 / +0.01, p ≥ 0.50). If anything the direction is
*backwards*: the 5 high-severity relation/action/count clips show slightly
*smaller* CLIP and ADQA drops than object/scene clips (AUC 0.36 / 0.54, i.e. ≤
chance). This matches the D1 finding that CLIP/ADQA are relatively blind to
relational/action/count errors — exactly the errors we deem most severe. So a
severity-weighted error score built from these two signals would upweight the
cases they detect *worst*, not best.

---

## Limitations

- **Small n for D10:** 23 probe-labelled clips, only 5 in the relation/action/
  count group; group means rest on n=5. Treat D10 as directional, not conclusive.
- **Severity proxy is coarse:** probe_type collapses to two effective levels here
  (high/medium); no object-attribute (low) probes exist, and the weighting is
  near-constant across clips, limiting resolution.
- **ADQA is a 0.1-grid score**, producing many ties (paraphrase drop == 0 for
  41/60), which inflates its apparent sign-rule specificity.
- Fabrication and paraphrase variants are model-generated; false-alarm rates are
  specific to this variant construction and 60-clip set.
- Thresholds are in-sample (calibrated on the same 60 paraphrases used to measure
  FA); a held-out split would give a less optimistic operating point.
