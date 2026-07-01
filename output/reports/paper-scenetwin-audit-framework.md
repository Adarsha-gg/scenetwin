---
title: "SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Safety Gates"
status: SUPERSEDED (old 4-tier / n=18-primary numbers) — canonical manuscript is output/papers/scenetwin-submission.tex (60-clip primary, corrected 3-tier)
created: 2026-06-09
updated: 2026-06-19
author: Adarsha Mishra, William Paterson University
bibliography: ../papers/scenetwin-audit-framework.bib
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
  - output/reports/scenetwin-citation-map.md
---

# SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Safety Gates

Adarsha Mishra · William Paterson University

## Abstract

Audio description (AD) makes video accessible to blind and low-vision viewers by narrating visual information not carried by the soundtrack. As multimodal systems begin to generate AD at scale, the deployment bottleneck shifts from authoring to **auditing**: a system must decide whether a candidate AD preserves visible content, whether it is hallucinated or describing the wrong clip, and which clips require human review. Existing AD evaluation methods are useful but incomplete for this setting. Reference-based methods such as LLM-AD-Eval can be strong when a professional reference AD is available, but newly generated AD for undescribed videos usually lacks that reference. Holistic VLM judges are flexible, but in our measurements they trail structured grounding. User studies remain the gold standard, but they cannot be run for every candidate at deployment time.

We present **SceneTwin**, a human-reference-free AD audit framework with three layers: (1) a two-signal score combining CLIP visual grounding and frame-grounded ADQA; (2) safety gates for hallucination and wrong-content failures; and (3) a TRIBE-v2 neural side-car for review triage. We first audit our benchmark construction and remove an invalid rung: the old “long VATEX” tier is simply the longest of several equal-status crowd captions and therefore measures verbosity rather than quality. On the corrected three-tier ladder — cross-decoy < crowd caption < professional AD — SceneTwin reaches Spearman ρ = 0.954 on 18 in-benchmark clips and ρ = 0.947 on 60 external clips, with 17/18 and 58/60 clips fully ordered respectively. Professional AD beats lower tiers in 36/36 in-benchmark and 118/120 external comparisons.

The ranking result is strong but not a claim of large industry dominance. A reference-style LLM-AD-Eval proxy nearly ties SceneTwin on the corrected ladder (ρ = 0.941 in-benchmark, ρ = 0.942 external), because it compares candidates to the trusted professional AD. SceneTwin’s contribution is therefore deployability rather than raw rank-correlation superiority: competitive scoring without a human reference AD, plus operational gates. A CLIP grounding-drop hallucination gate reaches AUC = 0.835 with 70% recall at 10% false-positive rate; a raw-CLIP single-AD wrong-content gate catches 98.3% of catastrophic wrong-clip descriptions at 2.2% false alarm. Three frontier VLM judges trail the corrected-ladder task by roughly 0.10–0.13 ρ externally. TRIBE is not used as a score — a per-clip neural scalar cannot change within-clip ranking — but as review triage it flags ADQA-failure clips externally at AUC = 0.79. SceneTwin is an audit layer for hybrid AI+human AD workflows, not a replacement for professional describers.

**Keywords:** audio description; blind and low-vision accessibility; video understanding; reference-free evaluation; hallucination detection; human-AI authoring

## 1. Introduction

Audio description translates visual content into speech so blind and low-vision viewers can access video information that the soundtrack alone does not convey. Automated AD generation is improving rapidly, driven by video-language models and AD-specific systems such as AutoAD III and newer collaborative authoring workflows [Han et al., 2024; Do et al., 2026]. But generation quality alone does not solve deployment. A generated AD can be fluent, grammatical, and visually plausible while still omitting a key action, misidentifying a person, over-describing a scene that has no timing slot, or describing the wrong clip entirely.

This is not a speculative risk. RNIB’s 2025 study of AI-generated audio description found that AI outputs often had good fluency and sentence structure but still lacked accuracy, cohesion, and contextual awareness; blind and partially sighted participants welcomed AI-expanded AD coverage, but agreed that human review remains essential [RNIB, 2025]. Recent human-AI AD systems make the same point from a workflow perspective: AI drafts can reduce labor, but expert review, user control, and adaptive interfaces remain necessary [Cheema et al., 2025; Do et al., 2026].

The deployment question is therefore not simply, “Can a model write AD?” It is:

> Given one or more candidate descriptions for a clip, can we audit whether they are visually grounded, detect unsafe failures, and decide what should be shipped or reviewed — without already having a professional reference AD for that clip?

Existing evaluation paradigms only partially answer this question. Reference-based metrics such as LLM-AD-Eval can compare a candidate against a professional reference AD [Han et al., 2024], but that reference is usually absent for newly generated AD. ADQA moves evaluation toward frame-grounded comprehension questions and explicitly criticizes the instability of single-reference matching [Kala et al., 2025], but it is still typically treated as a benchmark score rather than a deployment gate. VLM-as-judge evaluation is flexible, but our experiments show that frontier VLM judges systematically trail structured visual grounding on our controlled tier task. User studies and professional review remain indispensable, but they are scarce resources; an audit system should route clips to them, not assume they are available for every candidate.

SceneTwin reframes AD evaluation as an **audit stack**. Instead of asking only for a scalar score, a deployable AD audit system should answer three operational questions:

1. **Score:** Which candidate best preserves the clip’s visible content without comparing to a human reference AD?
2. **Gate:** Is the candidate unsafe because it hallucinates visible facts or describes the wrong clip?
3. **Triage:** Which clips should be sent to scarce human or expensive model review?

### Contributions

This paper makes five contributions.

1. **A corrected three-tier AD audit benchmark.** We identify and remove an invalid verbosity rung from our earlier tier construction. The active benchmark is cross-decoy < crowd caption < professional AD.
2. **A human-reference-free CLIP+ADQA scoring stack.** SceneTwin combines CLIP visual grounding [Radford et al., 2021] with frame-grounded ADQA-style questions [Kala et al., 2025], reaching ρ = 0.954 in-benchmark and ρ = 0.947 externally on the corrected ladder.
3. **An honest baseline comparison.** SceneTwin only slightly exceeds a reference-style LLM-AD-Eval proxy on rank correlation. We therefore position the contribution as deployability and safety, not as a large leaderboard win.
4. **Deployment safety gates.** SceneTwin adds a hallucination grounding-drop gate and a single-AD wrong-content gate, reporting operating points rather than only correlations.
5. **Review triage with TRIBE.** We use TRIBE-v2 [d’Ascoli et al., 2026] as a clip-level review-priority signal, not as a ranker.

## 2. Related Work

### 2.1 Automated audio description generation

AutoAD III develops large-scale video-aligned AD datasets and AD-specific evaluation dimensions including LLM-AD-Eval, CRITIC, multi-reference recall, and action coverage [Han et al., 2024]. ADx3 similarly frames AD creation as a collaborative workflow combining model generation, human refinement, and adaptive user queries [Do et al., 2026]. VideoA11y and timing-guideline work emphasize that AD quality also depends on synchronization, brevity, and delivery constraints, not only semantic correctness [Li et al., 2025].

These systems motivate SceneTwin but do not make the same claim. SceneTwin is not an AD generator. It is an audit layer that can be applied to generated, crowd, or professional-style candidate descriptions.

### 2.2 Reference-based and frame-grounded evaluation

LLM-AD-Eval scores candidate AD against a reference professional AD [Han et al., 2024]. This is a useful offline QA setting: if a reference exists, candidate-reference comparison can be highly predictive. However, this same strength creates a deployment limitation. A newly generated description for an undescribed video usually has no professional reference. In our proxy, LLM-AD-Eval is implemented as semantic similarity to T3, the professional AD; it nearly ties SceneTwin but has access to the reference text that SceneTwin deliberately does not use.

ADQA argues that single-reference text matching is unstable for AD because describers differ in when, whether, and what they describe [Kala et al., 2025]. It evaluates whether AD supports answers to visual and narrative questions. SceneTwin adopts the frame-grounded QA idea but repurposes it for candidate ranking and audit decisions. Rather than comparing the candidate to one professional phrasing, ADQA asks whether the candidate contains frame-evidenced information.

CoAD and StoryRecall broaden the evaluation target from local sentence quality to narrative coherence [Khandelwal et al., 2025]. AVBench similarly argues for fine-grained audio-video/text-video consistency scores rather than coarse holistic judgments [Yang et al., 2026]. We implement proxies for these ideas as baselines and fusion candidates. They inform our analysis, but the final audit stack remains parsimonious: CLIP plus ADQA is sufficient for headline ranking in our explored metric space.

### 2.3 Human-AI workflows and user agency

Recent accessibility systems show that a single static AD string cannot satisfy every viewer, genre, and moment. CustomAD reports that blind and low-vision users want control over length, emphasis, voice, speed, and format [Natalie et al., 2024]. Describe Now shows that user-triggered concise versus detailed descriptions increase agency but can also increase cognitive load [Cheema et al., 2024]. DescribePro shows that describers value AI drafts, forks, tags, and human editorial control rather than fully automatic replacement [Cheema et al., 2025]. WorldScribe studies live visual description and emphasizes intent, sound context, latency, and uncertainty [Chang et al., 2024].

These works define the deployment setting SceneTwin targets. The right outcome is not automatic replacement of professional describers. The right outcome is a hybrid workflow: automatic scores and gates handle obvious failures and confidence estimates, while uncertain or high-impact cases go to human review.

### 2.4 Neural side-cars for review triage

TRIBE-v2 is a multimodal brain-encoding model that predicts cortical responses to vision, audio, and language streams [d’Ascoli et al., 2026]. SceneTwin uses TRIBE as a side-car because AD exists precisely where audio alone does not convey visual information. However, we do not claim TRIBE directly measures BLV user utility. It is trained on naturalistic audiovisual responses and is used here only as a risk signal: clips with large audio-vs-audiovisual gaps may deserve more review.

## 3. Task and Benchmark

### 3.1 Corrected three-tier ladder

The active benchmark contains three ordered tiers per clip:

- **T0 — cross-decoy:** an AD/caption from another clip.
- **T1 — crowd caption:** a short visual description.
- **T3 — professional AD:** a professional or professional-style description.

The earlier four-tier construction included a “long VATEX” rung. We exclude it from the paper benchmark. That rung was created by choosing the longest of several equal-status crowd captions; it therefore measures verbosity, not known quality. Both CLIP and ADQA score the T1→old-T2 step near chance, confirming that the rung is structurally invalid as a quality label. The corrected benchmark evaluates the valid ladder: wrong clip < crowd caption < professional AD.

The corrected benchmark includes:

- **18 in-benchmark clips** with 54 candidate-tier observations.
- **60 external clips** with 180 candidate-tier observations across broader categories.

### 3.2 Evaluation metrics

The primary statistic is Spearman rank correlation between candidate score and tier label. Because the audit task is within-clip selection, we also report:

- **fully ordered clips:** T0 < T1 < T3 for a clip;
- **T3-vs-lower wins:** professional AD scores above both lower tiers;
- **all pairwise wins:** every ordered pair within the corrected ladder is correctly ranked.

These pairwise counts are meaningful for SceneTwin because it scores candidates against video and questions, not against T3 text. For reference-style text baselines, T3-vs-lower wins are partly privileged because T3 is the reference.

## 4. Method

### 4.1 CLIP visual grounding

SceneTwin samples frames from each clip and computes text-frame similarity using CLIP [Radford et al., 2021]. For a candidate AD, the CLIP leg is:

```text
clip_top3 = mean(top 3 frame-text similarities)
```

CLIP is useful because it is deterministic, fast, and grader-free. It is also limited: it is strong on objects and scenes but weaker on counts, relations, and fine-grained actions. SceneTwin therefore does not use CLIP alone for ranking.

### 4.2 Frame-grounded ADQA

The ADQA leg follows the principle of frame-grounded question answering [Kala et al., 2025]. For each clip, SceneTwin generates a fixed set of visual multiple-choice questions from frames. Candidate ADs are anonymized and graded by whether the text answers each question. The ADQA score is the fraction of frame-grounded questions answered by the candidate.

This design shifts evaluation away from matching one professional sentence. A candidate earns credit for preserving visible information, regardless of whether it uses the same wording as T3.

### 4.3 Two-signal score

Within each clip, CLIP and ADQA scores are normalized across candidate tiers and averaged:

```text
SceneTwinScore = 0.5 * CLIP_norm + 0.5 * ADQA_norm
```

The score is intentionally within-clip. It is used to rank candidates for the same video, not to compare absolute accessibility quality across unrelated videos.

### 4.4 Safety gates

SceneTwin adds gates because a scalar ranker is not enough for deployment.

The **hallucination gate** computes CLIP grounding drop between a clip-relevant anchor and a candidate:

```text
drop = CLIP(anchor AD, frames) - CLIP(candidate AD, frames)
```

The anchor can be a trusted AD or a generated clip-relevant reference. The fully no-anchor hallucination gate is a negative result: absolute weakest-claim grounding is too noisy for reliable hallucination detection.

The **wrong-content gate** uses raw, unnormalized CLIP grounding for a single candidate AD. It requires no candidate pool, no T3 reference, and no generated anchor. This gate targets catastrophic cases where the AD describes the wrong video.

### 4.5 TRIBE review triage

TRIBE-v2 predicts neural responses to audiovisual and audio-only inputs [d’Ascoli et al., 2026]. SceneTwin derives a clip-level accessibility gap:

```text
gap = 1 - cos(P_AV, P_A)
```

where `P_AV` is the predicted response to full audiovisual input and `P_A` is the predicted response to audio-only input. This gap is constant for all candidate ADs of a clip. It cannot change within-clip ranking, so it is not included in the score. Instead, it is used to prioritize clips for review.

## 5. Results

### 5.1 Corrected-ladder ranking

| Corpus | Clips | Observations | Spearman ρ | Fully ordered | T3-vs-lower wins | All pairwise wins |
|---|---:|---:|---:|---:|---:|---:|
| In-benchmark | 18 | 54 | 0.954 | 17/18 | 36/36 | 53/54 |
| External | 60 | 180 | 0.947 | 58/60 | 118/120 | 178/180 |

SceneTwin generalizes on the corrected task. Removing the invalid verbosity rung closes the apparent generalization gap and yields a stable three-tier result across the in-benchmark and external corpora.

### 5.2 Robustness

The corrected-ladder result is not a narrow tuned spike. It holds across ensemble weights from 0.2 to 0.8, multiple normalizations, cluster bootstrap, and within-clip permutation. At 0.5/0.5 weighting, robustness scripts report approximately ρ = 0.957 in-benchmark and ρ = 0.952 external under the normalization sweep.

## 6. Baselines

### 6.1 Corrected-ladder metric comparison

| Metric | In-benchmark ρ | External ρ | Deployment note |
|---|---:|---:|---|
| **SceneTwin CLIP+ADQA** | **0.954** | **0.947** | no human reference AD |
| LLM-AD-Eval proxy | 0.941 | 0.942 | needs trusted T3/pro reference |
| ADQA alone | 0.856 | 0.869 | no human reference AD; model grader |
| CLIP alone | 0.835 | 0.747 | grader-free; useful for gates |
| Best frontier VLM judge | 0.863 | 0.847 | no reference, but weaker here |
| CRITIC entity | 0.625 | 0.688 | weaker |

The strongest baseline is the LLM-AD-Eval proxy from AutoAD III [Han et al., 2024]. It nearly ties SceneTwin, which is important: SceneTwin should not be framed as a large rank-correlation win. But the comparison is not deployment-equivalent. The LLM-AD-Eval proxy compares each candidate to the professional AD reference for that clip. SceneTwin does not.

### 6.2 VLM-as-judge baselines

We also evaluated three frontier VLMs as direct AD-quality judges on the same clips and labels. On the corrected three-tier task, the best external VLM judge reaches ρ = 0.847, compared with SceneTwin’s ρ = 0.947. This suggests that structured frame-grounded scoring is better aligned with this audit task than asking a general VLM for a holistic quality judgment.

### 6.3 Reference leakage in text baselines

Reference-style baselines are useful but can be misleading in tier benchmarks. If T3 is the professional reference, then the T3 candidate is compared to itself. This makes pairwise T3 wins for LLM-AD-Eval and token-overlap baselines partly tautological. SceneTwin’s T3 wins are different: it scores the AD against video frames and frame-grounded questions, not against T3 text.

### 6.4 Fusion negative result

We tested multiple fusions inspired by AutoAD III, ADQA, CoAD, AVBench, timing rubrics, and TRIBE. None improved the headline result enough to justify the extra complexity. This negative result matters. The best deployment architecture in our explored space is not a metric zoo; it is a small score plus explicit gates.

## 7. Deployment Safety Gates

### 7.1 Hallucination grounding-drop gate

For 60 external clips, expert ADs are compared to same-length corrupted twins with two to three changed visual facts and faithful paraphrase controls. The mean length delta is 0.83 words.

| Gate | Signal | n | AUC | Recall @ 10% FPR |
|---|---|---:|---:|---:|
| Grounding-drop vs clip-relevant anchor | CLIP only | 60 | 0.835 | 70.0% |
| Fused drop vs clip-relevant anchor | CLIP + ADQA | 60 | 0.904 | 71.7% |
| Absolute weakest-claim grounding | CLIP only, no anchor | 60 | 0.585 | 16.9% |

The headline is the CLIP-only grounding-drop gate because it is grader-free. The fused result is secondary because the ADQA arm uses a model grader. The no-anchor result is a negative control and should not be hidden: absolute CLIP grounding alone is not sufficient for reliable hallucination detection.

### 7.2 Generated-anchor deployment path

A strict deployment objection is that the grounding-drop gate appears to require a human expert anchor. Reference-substitution experiments show that the gate needs a clip-relevant anchor, not necessarily a human one. A model paraphrase anchor matches the human-anchor result, and an independent generated-AD anchor still separates hand-authored lies from truthful ADs on the available subset. This evidence is smaller-sample, so it is not the headline. It supports a practical deployment path: use generated anchors for consistency checks, not as proof of automatic AD optimization.

### 7.3 Wrong-content catastrophic-failure gate

The cross-decoy tier simulates a catastrophic AD describing the wrong clip. For deployment, the strongest test is a single-AD raw-CLIP threshold with no candidate pool and no anchor. Wrong-content ADs average raw `clip_top3` 0.074 versus 0.311 for legitimate ADs. Leave-one-clip-out thresholding catches 98.3% of wrong-content ADs at 2.2% false alarm.

This is a high-recall review trigger, not an autonomous rejection oracle. At low base rates, precision can fall, so flagged cases should route to review.

### 7.4 Selective ship-best policy

ADQA margin is a useful confidence signal. Abstaining on the lowest-margin 20% sends 12/60 clips to review and ships the remaining 48 at 100% ship-best accuracy. This supports a three-way deployment policy:

- **Reject/review** when CLIP evidence indicates wrong-content or large grounding drop.
- **Ship** when ADQA margin is high and gates are clean.
- **Review** when margin is low or TRIBE indicates high risk.

## 8. TRIBE Review Triage

TRIBE is not a ranking metric. A per-clip scalar is identical for every candidate AD of a clip, so it cannot change within-clip rank correlation. Earlier attempts to use TRIBE as a calibration layer failed for this reason.

The useful role is review triage. On 60 external clips, the TRIBE audio-vs-audiovisual accessibility gap separates ADQA failures from successes:

| Layer | Misordered clips | Gap on failures | Gap on successes | AUC | p |
|---|---:|---:|---:|---:|---:|
| ADQA-only | 10/60 | 0.267 | 0.158 | 0.79 | 0.0018 |

This is a review-routing claim. TRIBE helps decide where to spend human or expensive model review; it does not improve the candidate-ranking score.

## 9. Discussion

SceneTwin’s main result is deliberately narrow. It does not show that a small audit metric dominates all AD evaluation. It shows that a human-reference-free score can approach a strong reference-style evaluator while adding safety gates that reference-style rankers do not provide.

This distinction matters for deployment. If a broadcaster already has a professional AD track and wants to compare an alternate draft, LLM-AD-Eval-style reference comparison is appropriate. If a platform is generating AD for undescribed clips, that reference does not exist. SceneTwin is designed for the latter setting: score against the video, gate unsafe failures, and route uncertain cases to review.

The results also support a conservative hybrid-workflow view. RNIB’s AI AD study, DescribePro, Describe Now, CustomAD, and WorldScribe all point away from full automation and toward human-AI collaboration, user agency, and context-aware description policies [RNIB, 2025; Cheema et al., 2024; Cheema et al., 2025; Natalie et al., 2024; Chang et al., 2024]. SceneTwin supplies one missing infrastructure piece for that workflow: automatic evidence about whether a candidate is visually grounded and whether it should be shipped, rejected, or reviewed.

## 10. Threats to Validity and Limitations

1. **No BLV user-utility study.** The corrected ladder measures agreement with tier construction, not viewer preference or comprehension.
2. **Professional AD is not a universal gold standard.** ADQA and related work show that human ADs vary substantially in timing and content [Kala et al., 2025].
3. **The corrected ladder is easier than the excluded construction.** This is intentional because the old rung was invalid, but reviewers should not compare the corrected result to the old construction as if they were the same task.
4. **LLM-AD-Eval nearly ties ranking.** SceneTwin’s advantage is deployment without a human reference AD and the addition of gates, not raw score dominance.
5. **ADQA uses model grading.** It inherits model bias and prompt sensitivity.
6. **CLIP misses relation/count/action errors.** The hallucination gate is strongest for object/scene grounding and weaker for relational lies.
7. **The hallucination gate needs an anchor.** The no-anchor version fails; generated-anchor evidence is promising but smaller-sample.
8. **TRIBE is triage-only and indirect.** It is trained on naturalistic brain responses, not BLV user outcomes.
9. **Short clips.** Long-form narrative AD, character memory, and timing constraints remain future work.

## 11. Reproducibility

The active manuscript is `output/reports/paper-scenetwin-audit-framework.md`. The main evidence files are:

- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` — in-benchmark corrected-ladder scores.
- `cursor/output/external_ensemble_eval.csv` — external 60-clip tier scores.
- `cursor/output/corrected_ladder_robustness.json` — robustness analysis.
- `cursor/output/gate_summary.json` — hallucination gate.
- `cursor/output/ref_subst/reference_substitution.json` — anchor substitution.
- `cursor/output/wrong_content_global_gate.json` — wrong-content gate.
- `cursor/output/gate_shipbest_selective.json` — selective ship-best.
- `cursor/research/output/vlm_as_judge_leaderboard.csv` — VLM-as-judge comparison.

The manuscript-specific citation map is `output/reports/scenetwin-citation-map.md`; the BibTeX file is `output/papers/scenetwin-audit-framework.bib`.

## 12. Conclusion

SceneTwin is a human-reference-free audit framework for audio description. On a corrected three-tier ladder, it ranks AD candidates strongly and generalizes to 60 external clips. But the central contribution is not overwhelming leaderboard superiority. The central contribution is a deployable audit stack: competitive ranking without a professional reference AD, safety gates for hallucination and wrong-content failures, and review triage for uncertain clips. This is the layer AI-assisted AD workflows need before generated descriptions can be shipped responsibly at scale.

## References

[1] Alec Radford et al. 2021. *Learning Transferable Visual Models From Natural Language Supervision*. ICML.

[2] Tengda Han et al. 2024. *AutoAD III: Back to the Pixels*. arXiv:2404.14412.

[3] Divy Kala et al. 2025. *ADQA: What You See Is What You Ask*. arXiv:2510.00808.

[4] Chaoyu Li et al. 2025. *VideoA11y and G7/G8 Timing Guidelines for Audio Description*. arXiv:2502.20480.

[5] RNIB. 2025. *Exploring AI-generated audio description: can emerging technologies help expand access to broadcast media?* Research report, 1 September 2025.

[6] Eshika Khandelwal et al. 2025. *CoAD: Coherent Audio Description and StoryRecall*. arXiv:2510.25440.

[7] Jialiang Yang et al. 2026. *AVBench: Audio-Video Evaluation Benchmark*. arXiv:2605.24652.

[8] Stéphane d’Ascoli et al. 2026. *TRIBE: A Foundation Model of Vision, Audition, and Language for In-Silico Neuroscience*. arXiv:2605.04326.

[9] Ruei-Che Chang et al. 2024. *WorldScribe: Toward Context-Aware Live Visual Descriptions*. UIST 2024 / arXiv:2408.06627.

[10] Rosiana Natalie et al. 2024. *CustomAD: Audio Description Customization*. arXiv:2408.11406.

[11] Maryam Cheema et al. 2024. *Describe Now: User-Driven Audio Description for BLV Individuals*. arXiv:2411.11835.

[12] Maryam Cheema et al. 2025. *DescribePro: Collaborative Audio Description with Human-AI Interaction*. arXiv:2508.01092.

[13] Lana Do et al. 2026. *ADx3: A Collaborative Workflow for High-Quality Accessible Audio Description*. arXiv:2602.02684.
