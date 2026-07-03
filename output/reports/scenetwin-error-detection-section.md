---
title: Reference-Free Audio-Description Error Detection
category: research
tags: [scenetwin, error-detection, omission, fabrication, triage, reference-free, negative-results]
created: 2026-07-02
---

# Reference-Free Audio-Description Error Detection

## Motivation: from ranking near-tie to a detection contribution

On the corrected three-tier ladder (T0 cross-decoy < T1 crowd caption < T3
professional AD), SceneTwin's CLIP+ADQA ensemble reaches Spearman rho = 0.952 on
the 60-clip primary set (0.957 on the disjoint 18-clip pilot). That number is
excellent, but it is only marginally ahead of a strong reference-style baseline: a
LLM-AD-Eval proxy scores rho = 0.942, roughly +0.005 to +0.013 behind. Ranking, in
short, is a near-tie, and a near-tie is not a paper's headline contribution.

The reframe is that ranking is not where SceneTwin is differentiated. The
reference-style baseline that ties us on ranking requires a trusted professional
reference AD for the clip. That requirement is exactly what disqualifies it from the
real problem: catching errors in machine-generated descriptions of *undescribed*
video, where no reference exists. SceneTwin's contribution is **reference-free error
detection** -- flagging fabricated and omitted content without a human reference --
which is a capability reference-based metrics structurally cannot provide, not a
capability where they are merely a few points behind.

Two independent findings make omission the anchor of this reframe. First, even
gold-standard professional ADs state the probed key visual fact only 61.8% of the
time (76 relational probes), so a reference-*keyed* ADQA inherits the reference's
~38% blind spots and cannot see them. Second, the weakest ADQA question types are
`spatial_relation` (AUC 0.818) and `object_attr` (0.811), whose professional-AD
yes-rates are only ~0.53-0.56 -- again, gold ADs simply omit fine spatial and
attribute detail. Detecting omission requires scoring whether the AD *conveys* a
fact, not whether it *matches* a reference; only a reference-free design can do it.

## The deployable stack: three modules, three jobs

The audit layer decomposes into three modules, each doing a different job with a
different signal. Fusion helps detection but not triage; omission is a detector, not
a ranking term -- so the modules are kept separate (see Negative Results).

### 1. DETECTION (reference-free)

**Omission detector.** For each clip, the score is the fraction of its probed key
facts the AD fails to mention. Treating the hallucinated AD as the higher-omission
positive, this separates gold from hallucinated ADs at **clip-level AUC 0.945**
(21/23 clips, 0 reversals; probe-level AUC 0.789, capped by binary 0/1 ties). The
detector is genuinely reference-free: a strict whole-phrase substring matcher
reproduces the cached mention labels at **94.7% agreement with 0 false positives**
(bag-of-token overlap over-fires -- use phrase matching). Its four misses are
paraphrase/synonym cases, so a production detector needs synonym handling. Omission
is the broader signal -- it flags all 73 hallucinated dropped-fact cases, whereas a
fabrication check catches only the 53 that assert a foil.

**Fused fabrication gate.** Fabrication is the complementary signal. z-normalizing
CLIP grounding-drop and ADQA-drop and taking the mean per clip yields a
fab-vs-paraphrase detector at **AUC 0.904**, beating CLIP alone (0.835) and ADQA
alone (0.801) by +0.069 (permutation p < 1e-4) -- a real but modest gain that
validates the complementarity (on the 18 clips where ADQA is blind, CLIP catches
18/18). The deployable operating point is **CLIP-magnitude, not sign**: a naive sign
rule flags 65% of faithful paraphrases and is undeployable, whereas a magnitude gate
at a 10% paraphrase false-alarm budget delivers **75% recall (fused) / 65% (CLIP
alone)**. Precision is base-rate-limited -- PPV at 10% FPR is 28% / 57% / 76% at
fabrication base rates of 5% / 15% / 30% -- so this is a **triage flag, not an
auto-reject gate**. A decision-curve analysis confirms flagging beats
review-all/review-none across harm thresholds of ~1.4-28% (base rate 5%), widening to
~11-76% (base rate 30%).

### 2. RANKING (reference-free)

The CLIP+ADQA ensemble scores the three-tier ladder at **rho = 0.952** (60-clip
primary; components ADQA-only 0.869, CLIP-only 0.747). This is competitive with the
reference-style baseline (0.942) at ~$1/clip versus ~$50 for a frontier VLM judge
(rho 0.847) and with no human reference required.

### 3. TRIAGE (risk forecasting)

The TRIBE fMRI-encoder `accessibility_gap` predicts corrected ADQA failures at
**AUC 0.794** (label-permutation p = 0.0023, 10 positives in 60 clips), and at
review budgets of 10/20/30% recovers 40%/60%/70% of failures -- 3-4x random. This is
review triage, not a scorer.

## Compact results table

| Module | Signal | Metric | Value | Operating detail |
|---|---|---|---|---|
| Detection | Omission detector | clip-level AUC | **0.945** | 21/23 clips, 0 reversals; lexical recovery 94.7% / 0 FP |
| Detection | Fused CLIP+ADQA fabrication gate | fab-vs-paraphrase AUC | **0.904** | vs CLIP 0.835 / ADQA 0.801; +0.069, p<1e-4 |
| Detection | CLIP-magnitude gate (operating point) | recall @10% FPR | **75%** (fused) / 65% (CLIP) | sign rule 65% false-alarm -> undeployable |
| Detection | Fused gate precision | PPV @10% FPR | 28 / 57 / 76% | base rate 5 / 15 / 30% -> triage, not gate |
| Ranking | CLIP+ADQA ensemble | Spearman rho | **0.952** | 60-clip primary; ADQA 0.869 / CLIP 0.747 |
| Triage | TRIBE accessibility_gap | ADQA-failure AUC | **0.794** | p=0.0023; recall 0.40/0.60/0.70 @ 10/20/30% budget |

## Negative Results / Parsimony

Four independent attempts to enrich or merge the modules all returned null,
converging evidence that the modular design sits at a local optimum:

- **D10 -- Severity weighting (null).** Weighting errors by probe type (who_role /
  action > object) does not sharpen detection: severity vs drop magnitude gives
  Spearman +0.148 (CLIP, p=0.50) and +0.010 (ADQA, p=0.97). If anything the
  direction is backwards -- high-severity relation/action/count clips show *smaller*
  drops (AUC 0.36/0.54, at or below chance), because CLIP/ADQA are weakest exactly on
  the errors judged most severe. A real severity target needs a video-native signal.
- **D13 -- Combined omission+fabrication scorer (null for fusion).** Merging the two
  detection signals into one score gives AUC 0.941, *below* omission alone (0.945);
  the signals are correlated (Spearman 0.595, co-occur by construction) and combining
  dilutes rather than adds. Keep them as separate detectors.
- **D15 -- Omission-in-ranking (null).** Folding an omission penalty into the ranking
  ensemble peaks at rho 0.9597 (+0.008 over 0.9516), within bootstrap noise, and
  recovers 0/2 of the known T3 pairwise losses (both are zero-coverage CLIP-driven
  flips the omission term is blind to). Omission stays a detector, not a ranking term.
- **D16 -- Question-type reweighting (null).** Reweighting ADQA by per-type
  discrimination gains at most +0.0019 rho (bootstrap CI includes zero); dropping weak
  types *hurts* (-0.0026), and the ablation confirms all-questions (0.932) beats
  scene-model-only (0.915) and non-scene-model-only (0.885). Per-type reliability is a
  diagnostic, not a weight. Ship equal-weight.

The lesson is parsimony: fused CLIP+ADQA for detection, the ensemble for ranking,
`accessibility_gap` for triage, and omission as a standalone detector already
capture the available signal. Added complexity buys <= +0.008 rho/AUC (within noise)
or actively hurts.

## Limitations

- **Synthetic ground truth, no BLV humans.** Tiers and hallucination/paraphrase
  variants are model-generated; error labels are constructed, not validated by blind
  or low-vision users. No BLV-utility claim is made.
- **Small n.** Detection rests on 23-60 clips (76 probes; only 10 triage positives;
  5 clips in the high-severity relation/action/count cell). AUC differences of ~0.03
  are within permutation noise, and thresholds/z-normalization are in-sample.
- **Grader dependence.** ADQA scores and mention labels are LLM-grader judgments
  (pooled across generators/graders for D12), not human ground truth; the lexical
  omission detector under-counts paraphrased coverage.
- **Blocked items needing visual grounding.** Three high-value directions converge on
  the same missing capability -- per-claim / per-sentence / temporal visual grounding
  (GPU or API):
  - *Claim-level localization (D14):* reference-free text-only top-1 localization is
    0.917, but a trivial "pick the first sentence" prior also scores 0.917 (+0.000
    content lift) -- the signal is a positional/boilerplate artifact, so zero-reference
    claim localization is **not demonstrated** and needs per-claim frame grounding.
  - *Video-native scoring (D3):* 51% of ADQA is relation/action/count and ADQA is 30%
    fabrication-blind; a video encoder (vs CLIP-on-8-frames) is specced but blocked.
  - *Severity (D10):* a genuine severity target likely requires a video-native signal.

## Honest claim boundaries

Consistent with the submission thesis, this section claims a **deployable audit
layer**, not leaderboard domination. We claim: reference-free ranking competitive
with reference-style baselines (rho 0.952); reference-free omission and fabrication
detection at operating points reference metrics cannot provide (omission AUC 0.945,
fused fabrication AUC 0.904); and calibrated triage (0.794). We do **not** claim an
autonomous auto-reject gate (precision is base-rate-limited -- this is triage and
flag-for-review), BLV user-utility validation, better AD generation, or demonstrated
zero-reference claim localization.

## Sources

- `output/reports/scenetwin-directions-loop.md`
- `output/reports/scenetwin-new-directions-run.md` (D1-D5)
- `output/reports/scenetwin-loop-d6-omission.md` (D6)
- `output/reports/scenetwin-loop-d7d8-fusion-oppoints.md` (D7/D8)
- `output/reports/scenetwin-loop-d9d10-falsealarm-severity.md` (D9/D10)
- `output/reports/scenetwin-loop-d11d12-triage-qtype.md` (D11/D12)
- `output/reports/scenetwin-paper-submission-thesis.md` (claim boundaries)
