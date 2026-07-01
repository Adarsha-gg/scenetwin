---
title: SceneTwin Submission Package
status: SUPERSEDED (old 4-tier / n=18-primary numbers) — canonical manuscript is output/papers/scenetwin-submission.tex (60-clip primary, corrected 3-tier)
created: 2026-06-26
sources:
  - output/reports/paper-scenetwin-submission-draft.md
  - output/reports/scenetwin-paper-evidence-check.md
  - output/reports/parallel-research-synthesis.md
  - output/reports/tribe-claims-audit.md
---

# SceneTwin Submission Package

## Canonical draft

Use this as the current paper draft:

- `output/reports/paper-scenetwin-submission-draft.md`

Older drafts remain useful source material but should not be treated as the current submission target if they headline TRIBE AUC=1.00, calibration, or 4-tier claims.

## Title

Primary:

> SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Review Triage

Shorter option:

> SceneTwin: Human-Reference-Free Auditing for Audio Description

More systems/HCI option:

> SceneTwin: An Audit Stack for AI-Assisted Audio Description Workflows

## One-sentence claim

SceneTwin audits candidate audio descriptions against video evidence, not a professional reference script, and combines competitive CLIP+ADQA ranking with safety gates and review triage for hybrid AI+human accessibility workflows.

## Abstract for submission form

Audio description (AD) makes video accessible to blind and low-vision viewers by narrating visual information that the soundtrack alone does not convey. As multimodal systems begin to generate AD at scale, the deployment bottleneck shifts from authoring to auditing: systems must determine whether a candidate AD is visually grounded, whether it omits or fabricates important scene evidence, and which clips require scarce human review. We present SceneTwin, a human-reference-free AD audit framework with three layers: CLIP + frame-grounded ADQA scoring, safety gates for hallucination and wrong-content failures, and TRIBE-v2 neural review triage. After removing an invalid verbosity rung from an earlier benchmark, SceneTwin reaches Spearman ρ = 0.954 on 18 in-benchmark clips and ρ = 0.947 on 60 external clips on the corrected ladder. A reference-style LLM-AD-Eval proxy nearly ties the ranking result but requires the trusted professional AD reference that SceneTwin intentionally avoids. SceneTwin’s contribution is therefore deployability, not a large leaderboard win: competitive scoring without human reference AD, plus operational safety gates and review prioritization. A CLIP grounding-drop hallucination gate reaches AUC = 0.835 with 70% recall at 10% FPR, a wrong-content gate catches 98.3% of catastrophic wrong-clip descriptions at 2.2% false alarm, and external cached TRIBE/gap-route features triage ADQA failures at AUC = 0.794 beyond cheap category, transcript/speech, duration, and word-count baselines. SceneTwin is an audit layer for hybrid AI+human AD workflows, not a replacement for professional describers or BLV user validation.

## Contribution bullets

1. Corrects the benchmark ladder by removing the invalid long-caption verbosity rung.
2. Introduces a human-reference-free CLIP+ADQA score for ranking candidate AD against source-video evidence.
3. Shows strong corrected-ladder ranking: ρ = 0.954 in-benchmark and ρ = 0.947 on 60 external clips.
4. Compares honestly to a strong reference-style LLM-AD-Eval proxy that nearly ties but needs trusted T3/pro AD.
5. Adds deployment gates: hallucination grounding-drop and catastrophic wrong-content detection.
6. Reframes TRIBE as review triage/access-surface routing, not an AD ranker or calibration layer.
7. Reports negative results directly: no-anchor hallucination gate fails; TRIBE frame sampling and NCR are not headline-ready.

## Safe claim checklist

Use:

- “human-reference-free” rather than “no reference of any kind” when discussing all gates.
- “competitive with reference-style LLM-AD-Eval proxy” rather than “dominates.”
- “TRIBE review triage / routing side-car” rather than “TRIBE scorer.”
- “external cached triage AUC = 0.794, category-shuffle p = 0.003” for TRIBE.
- “wrong-content gate catches 98.3% at 2.2% false alarm” for catastrophic wrong-clip AD.
- “grounding-drop hallucination gate needs a clip-relevant anchor.”

Avoid:

- “TRIBE improves ranking rho.”
- “TRIBE is a standalone hallucination detector.”
- “TRIBE AUC=1 proves triage” without n=2/family-wise caveat.
- “low-gap means no AD needed” or “skip scoring.”
- “VLM baselines are bad” — say they trail this structured task.
- “human validation” unless actual BLV participants are recruited and approved.

## Main tables to include

### Table 1 — Corrected-ladder results

| Corpus | Clips | Observations | Spearman ρ | Fully ordered | T3-vs-lower wins | All pairwise wins |
|---|---:|---:|---:|---:|---:|---:|
| In-benchmark | 18 | 54 | 0.954 | 17/18 | 36/36 | 53/54 |
| External | 60 | 180 | 0.947 | 58/60 | 118/120 | 178/180 |

### Table 2 — Baseline comparison

| Metric | In-benchmark ρ | External ρ | Deployment note |
|---|---:|---:|---|
| SceneTwin CLIP+ADQA | 0.954 | 0.947 | no human reference AD |
| LLM-AD-Eval proxy | 0.941 | 0.942 | needs trusted T3/pro reference |
| ADQA alone | 0.856 | 0.869 | model grader |
| CLIP alone | 0.835 | 0.747 | grader-free |
| Best frontier VLM judge | 0.863 | 0.847 | weaker on this task |
| CRITIC entity | 0.625 | 0.688 | weaker |

### Table 3 — Safety gates

| Gate | Signal | n | AUC | Operating point |
|---|---|---:|---:|---|
| Hallucination grounding drop | CLIP only | 60 | 0.835 | 70% recall @ 10% FPR |
| Fused hallucination drop | CLIP + ADQA | 60 | 0.904 | 71.7% recall @ 10% FPR |
| No-anchor hallucination | CLIP only | 60 | 0.585 | negative result |
| Wrong-content raw CLIP | CLIP only | 60 | 0.999 | 98.3% catch, 2.2% false alarm |

### Table 4 — TRIBE cheap-baseline gauntlet

| Target | Family | Best feature | AUC | Category-shuffle p |
|---|---|---|---:|---:|
| ADQA failure | TRIBE/gap-route | accessibility_gap | 0.794 | 0.003 |
| ADQA failure | category-only | category_loo_adqa_fail_rate | 0.700 | 1.000 |
| ADQA failure | transcript/speech | transcript_char_count | 0.733 | 0.995 |
| ADQA failure | duration/word count | tier3_word_count | 0.714 | 0.990 |

## Figure plan

1. **Method overview:** CLIP frames + ADQA questions + gates + TRIBE triage. Existing chart: `output/charts/scenetwin_methodology.png`.
2. **Corrected-ladder heatmap:** show tier ordering. Existing chart: `output/charts/scenetwin_per_tier_heatmap.png`.
3. **Bootstrap/robustness:** existing chart `output/charts/scenetwin_bootstrap_ci.png` or corrected-ladder robustness chart if preferred.
4. **Wrong-content/hallucination gate:** existing safety-gate charts under `output/charts/scenetwin_gate_*` and `output/charts/scenetwin_wrong_content_*`.
5. **TRIBE triage/access-surface:** use `output/charts/scenetwin_failure_forecast.png` as a pilot visualization but caption it carefully; add external cheap-baseline table for the safer claim.

## Reviewer objections and answer stubs

### “Isn’t this just a reference metric?”

No. The main SceneTwin score uses source-video frames and frame-grounded questions, not a professional reference AD. The paper explicitly compares to a reference-style LLM-AD-Eval proxy and reports that it nearly ties when the reference exists.

### “Why remove the long VATEX tier?”

Because it is not a quality tier. It was constructed by selecting the longest among equal-status captions. Both CLIP and ADQA scored the short-to-long step near chance. Keeping it would measure verbosity and punish/benefit arbitrary caption length, not AD quality.

### “Does this prove BLV users prefer SceneTwin’s chosen AD?”

No. The paper says that directly. SceneTwin is an audit/proxy layer. BLV user studies and professional review remain necessary.

### “Why use TRIBE if it does not improve ranking?”

Because ranking and triage are different tasks. A clip-level neural gap cannot affect within-clip AD ranking, but it can prioritize which clips/windows deserve review. The strongest current support is external ADQA-failure triage beyond cheap confounds, not the old in-benchmark AUC=1 pilot.

### “Does the hallucination gate work without a reference?”

The fully no-anchor hallucination gate does not work well and is reported as a negative result. The deployable path uses a clip-relevant anchor, which can be trusted AD or generated/reference-substitution. The wrong-content gate is the no-anchor catastrophic-failure check.

## Immediate next writing tasks

1. Convert the Markdown draft to target venue format once venue is chosen.
2. Decide whether to submit as accessibility/HCI systems paper or multimedia evaluation paper.
3. Add figure numbers and captions after selecting final figures.
4. If page-limited, cut Access Surface routing to appendix and keep TRIBE cheap-baseline table in main text.
5. Prepare a supplementary appendix with killed branches / negative results.
6. Optional future work: BLV micro-study packet, but do not claim user validation yet.
