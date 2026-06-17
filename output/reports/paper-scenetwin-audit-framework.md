---
title: "SceneTwin full paper draft — audit framework"
status: consolidated full draft v1 — supersedes paper-A-draft.md and paper-combined-draft.md as the active writing target
created: 2026-06-09
updated: 2026-06-09
sources:
  - output/reports/paper-A-draft.md
  - output/reports/paper-ad-safety-gate.md
  - cursor/findings/fake-tier-rung.md
  - cursor/findings/corrected-ladder-robustness.md
  - cursor/findings/tribe-clip-level-triage.md
  - cursor/findings/marginal-description-value.md
  - cursor/findings/dual-signal-complementarity.md
  - wiki/research/scenetwin-vlm-as-judge-results.md
  - wiki/research/scenetwin-negative-results.md
  - wiki/research/scenetwin-statistical-power.md
---

# SceneTwin: A Reference-Free Audit Framework for Audio Description — Scoring, Safety Gates, and Neural Review Triage

## Abstract

Audio description (AD) makes video accessible to blind and low-vision (BLV)
viewers by narrating the visual content the soundtrack does not convey. As
generative AD systems proliferate, the bottleneck shifts from authoring to
auditing: which candidate descriptions are safe to ship without a human
reference, and which clips deserve scarce review budget? We present
**SceneTwin**, a reference-free AD audit framework with three layers.

**Scoring.** A two-signal ensemble of CLIP visual grounding and frame-grounded
ADQA ranks AD candidates without any reference description. In the process of
validating it we found that the standard 4-tier evaluation ladder contains a
structurally invalid rung — the "long crowd caption" tier grades word count,
not quality — and that correcting the ladder closes the apparent
generalization gap: Spearman rho = 0.954 in-benchmark and **rho = 0.947 with
58/60 (97%) fully ordered clips on a held-out 60-clip out-of-distribution
corpus**. The result is flat across ensemble weights (0.2–0.8), three
normalization schemes, cluster-bootstrap resampling, and a within-clip
permutation null (p = 0.0002). Ten published reference-free baselines, six
engineered fusions, and three frontier VLMs used as zero-shot judges (Claude
Sonnet 4.6, GPT-5, Gemini 2.5 Pro) all trail the ensemble; the best VLM judge
loses by +0.13 to +0.17 rho on identical clips.

**Safety gates.** Rank correlation is not deployment safety, so we evaluate
SceneTwin as a set of operating-point gates. A grader-free CLIP grounding-drop
gate catches 70% of hallucinated descriptions at 10% false-positive rate
(AUC 0.84) against same-length lie controls; a raw-CLIP threshold catches
98.3% of catastrophic wrong-content descriptions at 2.2% false alarms with no
candidate pool or reference; and an ADQA-margin selective-prediction policy
ships the best candidate with 100% accuracy at 80% coverage. We report the
boundaries honestly: a zero-reference per-claim gate is near chance (AUC
0.585), and the grounding gate is object-biased — it fails on relational and
count lies that keep the salient nouns (AUC 0.32 on that stratum).

**Neural review triage.** A TRIBE v2 fMRI-encoder side-car computes a per-clip
audio-vs-audiovisual accessibility gap. We show structurally why such a
per-clip scalar cannot improve within-clip ranking — and that its real,
externally validated role is triage: on the 60 out-of-distribution clips the
gap separates the clips the metric misorders from those it ranks correctly
(AUC = 0.79, p = 0.0018), so a 20% highest-gap review budget catches 60% of
all scoring failures.

Together these results argue that a parsimonious two-signal metric, wrapped in
calibrated safety gates and brain-aligned triage, is a deployable audit stack
for reference-free AD evaluation — and that benchmark-ladder validity, not
metric capacity, was the binding constraint on measured generalization.

**Keywords:** audio description, reference-free evaluation, accessibility,
hallucination detection, selective prediction, brain encoders.

## 1. Introduction

Audio description has two distinct failure surfaces. The first is **quality**:
a description can be vague, incomplete, or simply wrong about what is on
screen. The second is **deployment risk**: a fluent, plausible description can
hallucinate visual facts, or describe the wrong clip entirely, and a
rank-correlation metric reports nothing about either until it is too late.
Reference-based metrics (CIDEr, BLEU, LLM-AD-Eval) cannot address unseen
content at all, because they require a human reference AD that live and
creator-facing systems do not have.

This paper contributes a reference-free audit framework evaluated end to end
on 78 clips (a controlled 18-clip benchmark plus a 60-clip cross-category
external corpus), organized as four contributions:

1. **A two-signal reference-free metric and a benchmark-validity finding.**
   The ensemble combines CLIP visual grounding with frame-grounded ADQA
   multiple-choice questions. While validating it we discovered that the
   conventional 4-tier ladder {cross-decoy < short caption < long caption <
   professional AD} contains a fake rung: the "long caption" tier is
   constructed as the *longest* of ~10 equal-status crowd captions, so the
   tier1-to-tier2 step grades word count, not quality. Two independent signals
   score that step at chance. Removing the invalid rung lifts out-of-
   distribution performance from rho = 0.873 (50% fully ordered) to
   **rho = 0.947 (97% fully ordered)** — the apparent generalization gap was
   mostly an artifact of grading against an invalid label.

2. **A head-to-head comparison** against ten paper-derived reference-free
   baselines, six engineered fusions, and three frontier VLMs as zero-shot
   judges. Nothing beats the two-signal ensemble; the strongest VLM judge
   trails by +0.13 to +0.17 rho on identical clips with identical labels.

3. **AD safety gates.** We reframe deployment as operating-point decisions
   with controls: a grader-free hallucination gate (CLIP grounding-drop,
   AUC 0.84, 70% recall at 10% FPR), a single-AD wrong-content gate (raw-CLIP
   threshold, 98.3% catch at 2.2% false alarm, leave-one-clip-out), and a
   selective ship-best policy (ADQA margin, 100% ship-best at 80% coverage).
   We report the honest negatives that bound the claims.

4. **Brain-aligned review triage.** A TRIBE v2 side-car computes a per-clip
   accessibility gap (predicted cortical response to video+audio vs audio
   alone). We give the structural argument for why a per-clip scalar cannot
   move within-clip rank correlation — closing a line of analysis that
   repeatedly produced nulls — and validate its actual role externally: the
   gap flags the clips the metric will misorder (AUC = 0.79, p = 0.0018,
   n = 60), concentrating failures into a small review budget.

The framing throughout is deliberately audit-shaped. We do not claim BLV
user-utility validation (that is the necessary next study); we claim that on
tier-constructed ground truth with adequate statistical power, a cheap
two-signal metric scores, gates, and triages AD candidates at deployable
operating points, and that every stronger-sounding alternative we tested —
metric zoos, fusions, frontier VLM judges, brain-encoder calibration — failed
to beat it under measurement.

## 2. Related Work

We