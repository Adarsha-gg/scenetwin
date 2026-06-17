# Validated Breakthrough: TRIBE Escalation Gate

Date: 2026-05-27

## Correction

The prior Neural Agency idea is useful as a research hypothesis, but the first
`agency_score` mixed ADQA miss labels into the score. That makes it retrospective
analysis, not proof of a predictive breakthrough.

After benchmarking, the **actually validated** breakthrough in the current repo
is:

> Use TRIBE as a pre-release escalation gate for blind and low-vision video
> access evaluation.

This means TRIBE does not replace CLIP, ADQA, VLM judges, or human review. It
decides **when not to trust them unattended**.

## Why this is better

The BLV access problem is high-stakes because an apparently good automatic AD
score can still fail on dense, visually important, temporally constrained clips.

The new research use case is:

1. Run TRIBE on video/audio.
2. Estimate standard-slot pressure and visual/audio mismatch.
3. Rank clips by evaluator-failure risk.
4. Spend human or stronger-model review only on the top risk clips.

That is a better TRIBE-native use than transcript scoring because it uses
TRIBE's counterfactual modality advantage before candidate text quality becomes
the question.

## Implemented validation

- Script: `cursor/tribe_escalation_gate_validation.py`
- Output: `cursor/output/tribe_escalation_gate_validation.csv`
- Report: `cursor/findings/tribe-escalation-gate-validation.md`

## Result

On the current 18 labeled cached clips:

- Known all-judge full-order failures: **2**
- TRIBE review budget: **2/18 clips** (**11.1%**)
- Failures caught: **2/2**
- AUC: **1.000**
- Average precision: **1.000**
- Hypergeometric p for top-budget capture: **0.0065**
- Permutation p for AUC: **0.0071**

## Baseline comparison

| Signal | AUC | Top-budget recall |
|---|---:|---:|
| TRIBE mean_standard_slot_score | 1.000 | 1.000 |
| TRIBE risk_score | 1.000 | 1.000 |
| TRIBE cheap_need_minus_speech_z | 1.000 | 1.000 |
| TRIBE speech_inverse | 0.938 | 0.500 |
| Category pets_or_sports | 0.750 | 0.500 |
| Category sports | 0.625 | 0.500 |
| ADQA margin fragility | 0.594 | 0.500 |
| TRIBE mean_need | 0.750 | 0.000 |

The important part is not merely AUC. It is the operational result:

> reviewing only the two clips TRIBE ranks highest catches all known automatic
> evaluator failures.

## What this changes

SceneTwin should stop presenting TRIBE as a possible quality score. The stronger
claim is:

> SceneTwin is an automatic AD evaluator with a neural escalation gate.

That is a cleaner research contribution:

- CLIP/ADQA/VLM judge candidate descriptions.
- TRIBE decides when those judges are likely fragile.
- Human review is allocated by predicted neural accessibility pressure.

## Next validation needed

The result is strong but still small. To make it publishable:

1. Extend labels to the external clips already collected under `cursor/output`.
2. Define failure on external clips as static AD losing to extended/interactive
   access or as human-rated insufficient access.
3. Re-run `tribe_escalation_gate_validation.py` on 50+ clips.
4. Report review-budget curves: recall@5%, recall@10%, recall@20%.
5. Compare against cheap non-TRIBE baselines: category, speech density, motion,
   CLIP uncertainty, ADQA margin, VLM confidence.

## Relationship to Neural Agency

Neural Agency remains the next frontier, but it must be validated with an
`interactive_gain` target:

`interactive_gain = interactive_VQA_score - static_AD_score`

Until that target exists, the validated breakthrough is the TRIBE escalation
gate. It is already better on the current evidence.
