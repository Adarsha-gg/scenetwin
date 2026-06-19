---
title: "SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Safety Gates"
status: polished submission draft — corrected 3-tier primary version
created: 2026-06-09
updated: 2026-06-19
author: Adarsha Mishra, William Paterson University
sources:
  - cursor/output/external_ensemble_eval.csv
  - cursor/output/fake_rung_analysis.json
  - cursor/output/corrected_ladder_robustness.json
  - cursor/output/gate_summary.json
  - cursor/output/wrong_content_global_gate.json
  - cursor/output/ref_subst/reference_substitution.json
  - cursor/output/best_of_n_rerank.json
  - cursor/output/gate_shipbest_selective.json
  - cursor/research/output/vlm_as_judge_leaderboard.csv
  - output/reports/scenetwin-paper-evidence-check.md
---

# SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Safety Gates

Adarsha Mishra — William Paterson University

## Abstract

Audio description (AD) makes video accessible to blind and low-vision viewers by narrating visual information not carried by the soundtrack. As multimodal models begin to generate AD at scale, the bottleneck shifts from authoring to **auditing**: a deployment system must decide whether a candidate AD preserves visible content, whether it is hallucinated or describing the wrong clip, and which clips require human review. We present **SceneTwin**, an AD audit framework with three layers: (1) a two-signal score combining CLIP visual grounding and frame-grounded ADQA; (2) safety gates for hallucination and wrong-content failures; and (3) a TRIBE-v2 neural side-car for review triage.

We first audit the benchmark construction and remove an invalid rung: the “long VATEX” tier is the longest of several equal-status crowd captions, so it measures verbosity rather than quality. On the corrected three-tier ladder — cross-decoy < crowd caption < professional AD — SceneTwin reaches Spearman ρ = 0.954 on 18 in-benchmark clips and ρ = 0.947 on 60 external clips, with 17/18 and 58/60 clips fully ordered respectively. Professional AD beats lower tiers in 36/36 in-benchmark and 118/120 external comparisons.

The ranking result is strong, but the paper does not claim large leaderboard dominance. A reference-style LLM-AD-Eval proxy nearly ties the corrected-ladder score (ρ = 0.941 in-benchmark, ρ = 0.942 external). That proxy does not require a live human reviewer at scoring time, but it does require a trusted reference/professional AD for the clip; in our proxy, candidates are compared to T3. SceneTwin’s contribution is therefore deployability rather than raw rho dominance: competitive ranking without a human reference AD, plus operational gates. A CLIP grounding-drop hallucination gate reaches AUC = 0.835 with 70% recall at 10% false-positive rate; a raw-CLIP single-AD wrong-content gate catches 98.3% of catastrophic wrong-clip descriptions at 2.2% false alarm. Three frontier VLM judges trail the corrected-ladder task by roughly 0.10–0.13 ρ externally. TRIBE is not used as a score — a per-clip neural scalar cannot change within-clip ranking — but as review triage it flags ADQA-failure clips externally at AUC = 0.79. SceneTwin is an audit layer for hybrid AI+human AD workflows, not a replacement for professional describers.

## 1. Introduction

AI-generated audio description is becoming technically plausible, but deployment remains unsafe without auditing. A candidate AD can be fluent and still be incomplete, visually wrong, or about the wrong clip. For blind and low-vision viewers, such failures are not cosmetic: a hallucinated visual fact can become the only visual account the viewer receives.

Most current evaluation setups are mismatched to this deployment problem. Reference-based metrics can compare a candidate against a professional AD, but newly generated AD for undescribed videos usually has no such reference. Holistic VLM judgment is attractive, but our measurements show that frontier VLM judges trail structured visual grounding on this task. User studies remain the gold standard, but they cannot be run for every candidate description at deployment time.

SceneTwin reframes AD evaluation as an **audit stack** rather than a single leaderboard score. A deployable audit stack must answer three questions:

1. **Score:** Which candidate best preserves the clip’s visual content without a human reference AD?
2. **Gate:** Is the candidate unsafe because it hallucinates visible facts or describes the wrong clip?
3. **Triage:** Which clips should be sent to scarce human or expensive model review?

### Contributions

1. **Corrected three-tier AD audit benchmark.** We remove the invalid verbosity-only long-caption rung and evaluate the valid ladder: cross-decoy < crowd caption < professional AD.
2. **Human-reference-free CLIP+ADQA scoring.** SceneTwin reaches ρ = 0.954 in-benchmark and ρ = 0.947 externally on the corrected ladder without comparing candidates to a professional reference AD.
3. **Conservative baseline comparison.** SceneTwin only slightly exceeds a reference-style LLM-AD-Eval proxy on ranking; its stronger advantage is deployment without a human reference and explicit safety gates.
4. **Deployment safety gates.** A CLIP grounding-drop gate catches many same-length hallucinations; a raw-CLIP gate catches nearly all wrong-content failures at low false alarm.
5. **Review triage.** TRIBE is scoped as triage, not scoring: it routes high-risk clips to review rather than improving rank correlation.

## 2. Related Work and Positioning

### 2.1 Generation systems are not audit systems

Systems such as AutoAD III and VideoA11y focus on generating or improving audio descriptions. VideoA11y is stronger than SceneTwin as a user-validated generation paper: it includes blind/low-vision participants and professional describers. SceneTwin should not claim to beat those systems as a generator. It addresses the next layer: how to audit generated or candidate AD before deployment.

### 2.2 Reference metrics are strong but not always deployable

LLM-AD-Eval-style scoring is competitive. On our corrected ladder, the reference-style proxy nearly ties SceneTwin: ρ = 0.941 vs 0.954 in-benchmark and 0.942 vs 0.947 externally. The ranking margin over this baseline is small.

The key distinction is not whether a human manually reviews every candidate. LLM-AD-Eval does not need a live human reviewer at scoring time. It needs a trusted reference AD to compare against. That is useful offline when a professional AD already exists; it is not available for newly generated AD on undescribed videos. SceneTwin’s ranking score and raw wrong-content gate operate without a human reference AD.

### 2.3 VLM judges are weaker than structured grounding here

Three frontier VLM judges — Claude Sonnet 4.6, GPT-5, and Gemini 2.5 Pro — were evaluated on identical clips and labels. On the corrected three-tier task, the best external VLM judge reaches ρ = 0.847, while SceneTwin reaches ρ = 0.947. The VLMs are useful, but structured visual grounding and frame-grounded questions are better aligned with this tier task.

### 2.4 Safety gates are under-addressed

Industry and accessibility guidance repeatedly note that AI AD can be fluent while inaccurate. SceneTwin fits a hybrid workflow by converting scores into review triggers: hallucination gate, wrong-content gate, and selective auto-ship confidence.

## 3. Method

### 3.1 CLIP visual grounding

For each candidate AD and clip, we sample frames, embed text and frames with CLIP, and compute `clip_top3`, the mean of the top three frame-text similarities. CLIP is deterministic and grader-free, which makes it useful for safety gates.

### 3.2 Frame-grounded ADQA

For each clip, SceneTwin generates a fixed set of visual multiple-choice questions from frames. Candidate ADs are anonymized and graded by whether the text answers each question. The ADQA score is the fraction of frame-grounded questions the AD answers.

### 3.3 Two-signal ensemble

Within each clip, CLIP and ADQA are normalized over candidate tiers and averaged:

```text
SceneTwinScore = 0.5 * CLIP_norm + 0.5 * ADQA_norm
```

This is a within-clip ranking metric. It does not compare absolute scores across unrelated videos, and it does not compare candidates to a professional reference AD.

### 3.4 Safety gates

The hallucination gate computes a CLIP grounding drop between a clip-relevant anchor and a candidate:

```text
drop = CLIP(anchor AD, frames) - CLIP(candidate AD, frames)
```

The anchor can be a trusted AD or a machine-generated clip-relevant reference. The fully no-anchor version is a negative result and is reported as such. The wrong-content gate uses raw, unnormalized CLIP grounding for a single AD, with no candidate pool and no anchor.

### 3.5 TRIBE triage side-car

TRIBE-v2 predicts cortical responses to video+audio (`P_AV`) and audio-only (`P_A`). SceneTwin uses the gap between them as an accessibility-risk signal:

```text
gap(t, roi) = 1 - cos(P_AV[t, roi], P_A[t, roi])
```

This signal is not a scoring metric. Since it is constant for all candidate ADs of the same clip, it cannot reorder candidates within that clip. It is used only for review triage.

## 4. Corrected Benchmark

The valid benchmark has three tiers:

- **T0:** cross-decoy AD from another clip.
- **T1:** crowd caption / short visual description.
- **T3:** professional or professional-style AD.

We exclude the old T2 long-VATEX rung because it is built as the longest of several equal-status crowd captions. It is a verbosity control, not a quality label. Both CLIP and ADQA score the T1→T2 step near chance, confirming that it is not a reliable quality rung.

The benchmark contains:

- **18 in-benchmark clips** → 54 observations on the corrected ladder.
- **60 external clips** → 180 observations on the corrected ladder.

## 5. Scoring Results

### 5.1 Corrected-ladder headline

| Corpus | Clips | Observations | Spearman ρ | Fully ordered | T3-vs-lower wins | All pairwise wins |
|---|---:|---:|---:|---:|---:|---:|
| In-benchmark | 18 | 54 | 0.954 | 17/18 | 36/36 | 53/54 |
| External | 60 | 180 | 0.947 | 58/60 | 118/120 | 178/180 |

SceneTwin generalizes on this corrected task: out-of-domain performance is essentially the same as in-benchmark performance once the invalid verbosity rung is removed.

### 5.2 Robustness

The corrected-ladder result is not a tuned spike. It holds across ensemble weights 0.2–0.8, three normalizations, cluster bootstrap, and within-clip permutation. At 0.5/0.5 weighting, robustness runs report approximately ρ = 0.957 in-benchmark and ρ = 0.952 external under the robustness script’s normalization sweep.

## 6. Baselines

### 6.1 Corrected-ladder metric comparison

| Metric | In-benchmark ρ | External ρ | Deployment note |
|---|---:|---:|---|
| **SceneTwin CLIP+ADQA** | **0.954** | **0.947** | no human reference AD |
| LLM-AD-Eval proxy | 0.941 | 0.942 | needs trusted reference/pro AD |
| ADQA alone | 0.856 | 0.869 | no human reference AD; model grader |
| CLIP alone | 0.835 | 0.747 | grader-free; useful for gates |
| Best frontier VLM judge | 0.863 | 0.847 | no reference, but weaker here |
| CRITIC entity | 0.625 | 0.688 | weaker |

The rank-correlation margin over the strongest reference-style metric is small. SceneTwin’s stronger claim is that it achieves comparable ranking while removing the need for a human reference AD and adding calibrated safety gates.

### 6.2 Reference leakage in text baselines

The LLM-AD-Eval proxy and token-overlap-style baselines compare candidates to T3, the professional AD. This is a useful offline QA setting, but it gives the T3 candidate privileged access to itself. Pairwise T3 wins for these baselines are therefore not comparable to SceneTwin’s T3 wins. SceneTwin scores the AD against the video and frame-grounded questions, not against the professional reference text.

### 6.3 Fusion negative result

Several metric fusions improve neither clarity nor headline value. On the corrected in-benchmark ladder, some fusions also perform strongly because the task is easier after removing the fake rung, but they do not change the deployment story: adding more metrics does not produce a safer fieldable system unless it also provides gates and review policy.

## 7. Deployment Safety Gates

### 7.1 Hallucination grounding-drop gate

For 60 external clips, expert ADs are compared to same-length corrupted twins with 2–3 changed visual facts and faithful paraphrase controls. The mean length delta is 0.83 words.

| Gate | Signal | n | AUC | Recall @ 10% FPR |
|---|---|---:|---:|---:|
| Grounding-drop vs clip-relevant anchor | CLIP only | 60 | 0.835 | 70.0% |
| Fused drop vs clip-relevant anchor | CLIP + ADQA | 60 | 0.904 | 71.7% |
| Absolute weakest-claim grounding | CLIP only, no anchor | 60 | 0.585 | 16.9% |

The headline is the grader-free CLIP grounding-drop result. The fused result is secondary because the ADQA arm uses a model grader. The no-anchor result is a negative control: absolute CLIP grounding alone is too noisy for reliable hallucination detection.

### 7.2 Human-reference-free anchor path

A strict deployment objection is that a grounding-drop gate appears to require a human expert anchor. Reference-substitution experiments show that the gate needs a clip-relevant anchor, not necessarily a human one. A model paraphrase anchor matches the human-anchor result (AUC ≈ 0.849 vs 0.835), and an independent generated-AD anchor still separates hand-authored lies from truthful ADs at AUC ≈ 0.815 on the available subset. This is not the main headline because the subset is smaller, but it supports the deployment path: use generated anchors for consistency checks, not as claims of automatic AD optimization.

### 7.3 Wrong-content catastrophic-failure gate

The cross-decoy tier simulates a catastrophic AD describing the wrong clip. For deployment, the strongest test is a single-AD raw-CLIP threshold with no candidate pool and no anchor. Wrong-content ADs average raw `clip_top3` 0.074 versus 0.311 for legitimate ADs. Leave-one-clip-out thresholding catches 98.3% of wrong-content ADs at 2.2% false alarm.

This should be framed as a high-recall review trigger, not an autonomous rejection oracle. At low base rates, precision falls, so human review remains necessary.

### 7.4 Selective ship-best policy

ADQA margin is a useful confidence signal. Abstaining on the lowest-margin 20% sends 12/60 clips to review and ships the remaining 48 at 100% ship-best accuracy. This supports the final policy:

- use CLIP/ensemble evidence for reject decisions;
- use ADQA margin for auto-ship confidence;
- send low-margin or high-risk clips to review.

### 7.5 Gate limitations

CLIP is object/scene strong but relation/count weak. The paper must not claim that it catches every dangerous lie. Relation/action/count hallucinations require explicit question probes or stronger relation models.

## 8. TRIBE Review Triage

TRIBE is not a ranking metric. A per-clip scalar is identical for every candidate AD of a clip, so it cannot change within-clip rank correlation. This explains why TRIBE-as-calibration tests failed.

The useful role is review triage. On 60 external clips, the TRIBE audio-vs-audiovisual accessibility gap separates ADQA failures from successes:

| Layer | Misordered clips | Gap on failures | Gap on successes | AUC | p |
|---|---:|---:|---:|---:|---:|
| ADQA-only | 10/60 | 0.267 | 0.158 | 0.79 | 0.0018 |

This is a review-routing claim: TRIBE helps decide where to spend human or expensive model review, not how to score candidates.

## 9. Discussion

The corrected-ladder results show that SceneTwin is a strong human-reference-free ranker, but the nearest reference-style baseline is close. If the paper claimed only “better metric,” the contribution would be modest.

The stronger contribution is the audit stack:

1. **Human-reference-free score** competitive with reference-style metrics.
2. **Safety gates** for hallucination and wrong-content failures.
3. **Selective review policy** using ADQA margin and TRIBE gap.

This matches the likely real-world workflow: AI drafts descriptions, automatic audit catches obvious and risky failures, and humans review uncertain cases.

## 10. Limitations

1. No blind/low-vision user study; VideoA11y is stronger on user validation.
2. LLM-AD-Eval proxy nearly ties ranking; SceneTwin’s advantage is deployment/gating, not raw rho dominance.
3. Corrected ladder is easier than the old invalid four-tier construction; the exclusion must be justified clearly.
4. ADQA uses model grading and inherits model biases.
5. CLIP gates miss relation/action/count hallucinations.
6. Hallucination grounding-drop uses an anchor; the no-anchor version fails, and generated-anchor evidence is smaller-sample.
7. TRIBE is average-subject and triage-only.
8. Short clips; long-form narrative AD remains future work.

## 11. Conclusion

SceneTwin should be read as a **human-reference-free AD audit framework**, not as a claim of overwhelming leaderboard dominance. On the corrected ladder, it ranks AD candidates very well and generalizes to 60 external clips. Its real value is deployment: it runs without a professional reference AD for ranking, turns visual grounding into hallucination and wrong-content gates, and routes uncertain clips to review. The resulting claim is narrower and stronger: **SceneTwin is a fieldable audit layer for AI-assisted audio description.**

## References to cite in final format

- AutoAD III / LLM-AD-Eval baseline: Han et al., arXiv:2404.14412.
- ADQA: Kala et al., arXiv:2510.00808.
- VideoA11y and G7/G8 timing: Li et al., arXiv:2502.20480.
- TRIBE v2: d’Ascoli et al., arXiv:2605.04326.
- CLIP: Radford et al., 2021.
- RNIB or equivalent accessibility guidance on human review for AI-generated AD.
