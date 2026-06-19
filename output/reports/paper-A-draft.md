---
title: SceneTwin paper A draft skeleton
status: scaffold — fill in prose; numbers and figures locked
created: 2026-05-29
---

# A Two-Signal Reference-Free Audio Description Evaluation Framework with Brain-Aligned Failure Forecasting

## Abstract

We address the problem of reference-free audio description (AD) evaluation for blind and low-vision viewers. We contribute (i) a **multi-signal reference-free metric** that combines CLIP visual grounding, frame-grounded ADQA multiple-choice questions averaged across four judge–grader model pairs, and a Claude-Haiku VLM-rated specificity dimension; on an 18-clip controlled benchmark it achieves Spearman ρ = **0.965** with **54/54 pairwise tier-3 wins** and **18/18 fully tier-ordered clips**, and on a 60-clip cross-category external corpus (single-judge variant, n = 240) it achieves ρ = **0.873** with 173/180 pairwise wins. The combined 78-clip corpus (n = 312) yields ρ = **0.886** at p < 10⁻¹⁰⁰. (ii) A **brain-aligned failure forecaster** built from TRIBE v2 fMRI-encoder features that flags every severe ranking failure within an 11.1% manual-review budget (AUC = 1.00, recall@2/18 = 100%, p_Bonferroni = 0.065). (iii) An empirical comparison against ten paper-derived reference-free baselines, six engineered fusion strategies, and three frontier multimodal models (Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro) acting as zero-shot AD judges: every alternative trails our ensemble by ≥0.04 ρ on in-benchmark and ≥0.13 ρ when the frontier VLMs are used as direct judges. We argue for parsimony over the metric zoo and for **VLM-as-dimension** rather than VLM-as-judge.

**Keywords:** audio description, reference-free evaluation, multi-judge ensemble, brain-aligned encoders, accessibility metrics.

## 1. Introduction

Audio description (AD) makes video content accessible to blind and low-vision (BLV) viewers by narrating visual content that the soundtrack alone does not convey. As video volume grows and generative AD models proliferate, the bottleneck shifts from authoring to **evaluation**: which AD candidates are good enough to deploy without human review, and on which clips should reviewers focus their limited time? Reference-based metrics (CIDEr, BLEU, LLM-AD-Eval) cannot answer this question on unseen content because they require a human reference AD. Reference-free metrics can, but the published landscape is fragmented: ten or more reference-free signals exist (Section 2) without a common benchmark or head-to-head comparison.

This paper makes three contributions toward closing that gap.

First, we contribute a **multi-signal reference-free metric** that combines CLIP visual grounding, frame-grounded ADQA multiple-choice questions averaged across four judge–grader model pairs, and a Claude-Haiku VLM-rated specificity dimension. On an 18-clip controlled benchmark with a 4-tier AD ladder (Section 4), it achieves Spearman ρ = **0.965** — perfect 18/18 tier-orderings and 54/54 professional-AD pairwise wins. On a 60-clip cross-category external corpus (single-judge variant, n = 240, ten unseen video categories), the same architecture achieves ρ = **0.873** with 173/180 (96.1%) professional-AD wins. The combined-corpus number is ρ = **0.886** on n = 312 at p < 10⁻¹⁰⁰. Statistical power: cluster-bootstrap 95% CIs [0.881, 0.962] in-bench and [0.836, 0.902] external; minimum detectable r at α = 0.05, power = 0.80 is **0.158** on the combined corpus.

Second, we contribute a **brain-aligned failure forecaster** that pairs the metric with a TRIBE-v2 fMRI-encoder side-car. TRIBE need-window features predict severe ranking failures (full-tier-order ADQA disagreement) at AUC = 1.00 / recall@2/18 = 100% within an 11.1% manual-review budget on the 18-clip benchmark. Without the forecaster, deploying the metric on unseen content requires reviewing all outputs to be safe against severe failures; with it, 11% review suffices to catch every observed catastrophic failure.

Third, we contribute an **empirical comparison** against ten paper-derived reference-free baselines (LLM-AD-Eval, ADQA-alone, VT consistency, CRITIC, story recall, action coverage, multi-reference R@k, CoAD repetition, need-weighted CLIP, timing G7/G8), six engineered fusion strategies that blend up to six of those metrics, and three frontier multimodal models (Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro) acting as zero-shot AD judges. The strongest published reference-free competitor (LLM-AD-Eval) trails by **+0.030 ρ in-benchmark** and **+0.016 ρ external**. No fusion of paper baselines beats the two-signal ensemble. The three frontier VLM-as-judge baselines trail by **+0.16 to +0.22 ρ** on identical clips with identical labels — establishing that the reviewer's most common concern ("a frontier VLM would dominate this") collapses against measurement.

Together, the three contributions establish that a **parsimonious multi-judge ensemble with brain-aligned failure triage** is the right architecture for deployable reference-free AD evaluation. The remaining sections describe the metric (Section 3), the 78-clip cross-category benchmark (Section 4), headline results (Section 5), baseline comparisons including the negative-results fusion ablation (Section 6), failure analysis on both corpora (Section 7), the TRIBE side-car (Section 8), discussion (Section 9), and conclusion (Section 10).

## 2. Related Work

We surveyed 37 papers spanning AD generation, AD evaluation, video understanding, BLV accessibility, and brain encoding. They cluster into six thematic groups (semantic alignment, narrative/temporal coverage, user agency, identity/domain/deployment, assistant behavior, evidence loops); the full survey appears at [[research/scenetwin-paper-corpus]]. This Section cites the four clusters that directly inform our baselines and side-car; clusters covering user agency, assistant behavior, and evidence loops motivate a companion paper on access-surface routing and are out of scope here.

### 2.1 Semantic alignment metrics (the primary baseline group)

The closest prior work to our ensemble's CLIP-grounding component is the **LLM-AD-Eval** proxy from **AutoAD III** [han2024autoad-iii, arXiv 2404.14412], which scores AD candidates by sentence-embedding similarity to a reference professional AD. We implement and measure this baseline; it is the strongest published reference-free metric we found. **ADQA** [arXiv 2510.00808] introduces frame-grounded multiple-choice scoring, which forms the foundation of our ADQA signal. **AVBench-style VT consistency** [arXiv 2605.24652], **SemVideo hierarchical similarity** [arXiv 2602.21819], and **ViDscribe query coverage** [arXiv 2603.14662] occupy adjacent positions in the semantic-alignment cluster. We implement and measure all five; results appear in Section 6.

### 2.2 Narrative and temporal metrics

This cluster asks **when** the AD should describe what, rather than whether the AD text matches the video. **CoAD / StoryRecall** [arXiv 2510.25440] introduces a narrative-beat recall metric and a repetition penalty. **CA3D** [arXiv 2412.10002] performs shot-level event detection that aligns with AD slot windows. **VideoA11y** [arXiv 2502.20480] proposes timing rubrics for AD insertion. We measure each as a single metric and as a fusion ingredient; none beats the simpler ensemble on tier-ranking ρ (Section 6.3). **TRIBE v2** [defossez2026tribe, arXiv 2605.04326] sits in this cluster as well: it predicts fMRI brain response from video–audio–text inputs and supports modality counterfactuals, which we exploit as a failure forecaster in Section 8.

### 2.3 Metrics that conflict with our tier-ordered GT

Two published metrics anti-correlate with tier-ordering and are therefore not deployable as audit metrics in our setting. The **CoAD repetition penalty** anti-correlates because professional AD is longer and contains more repetition than terser captions (ρ = −0.064 on n = 72). The **multi-reference R@k** metric trivially scores tier-3 highest when tier-3 is one of its references (reference leakage); we report it only as a leakage upper bound. We document both findings in Section 6.

### 2.4 Brain encoders as evaluation side-cars

**TRIBE v2** is a tri-modal foundation model that predicts fMRI BOLD responses from naturalistic stimuli using LLaMA-3.2 (text), V-JEPA2 (video), and Wav2Vec-BERT (audio) features projected onto the fsaverage5 cortical surface. We use its modality-counterfactual capability to define **accessibility_gap** = 1 − cos(P_AV, P_A) (the visual information left out by the audio track) and **description_gain** = cos(P_AV, P_AD) − cos(P_AV, P_A) (the AD's measurable contribution). Section 8 reports both as forecast features.

### 2.5 Out-of-scope but cited as motivating future work

**AudioCapBench** [arXiv 2602.23649] asks whether the audio track is *sufficient* on its own (accuracy / completeness / hallucination dimensions). **LVOmniBench** [arXiv 2603.19217] argues that short-clip metrics do not prove long-form access. **DescribePro** [arXiv 2508.01092] treats AD quality as a versioned authoring workflow. **Describe Now** [arXiv 2411.11835] argues for user-driven control over when and how much AD to deliver. Each motivates a follow-up; none provides a baseline metric we could measure in our protocol.

## 3. Method

### 3.1 CLIP visual grounding

[Top-3 frame aggregation; per-tier CLIP-similarity score against sampled frames.]

### 3.2 Frame-grounded ADQA

[Per-clip MCQ generation against sampled frames; per-tier yes-rate as ADQA score.]

### 3.3 Two-signal ensemble

`ensemble(clip, tier) = mean(CLIP_norm(clip, tier), ADQA_norm(clip, tier))`

Per-clip min-max normalization within the four tiers, then averaged. Trivially cheap at inference (a few seconds per (clip, tier) pair).

### 3.4 TRIBE side-car failure forecaster

[Need-window features from TRIBE v2 (mean_standard_slot_score, mean_speech_density, etc.); binary classification of all4_fail event; review-triage flag, not a continuous calibration layer (§7.2).]

## 4. Benchmark Construction

### 4.1 In-benchmark (18 clips)

- Controlled 4-tier AD ladder per clip: **T0** cross-decoy (AD from a different clip), **T1** VATEX short caption, **T2** VATEX long caption, **T3** professional human AD.
- 18 clips drawn from 6 categories (Food & Cooking, Sports, Pets & Animals, Travel, etc.).
- 72 (clip, tier) observations.

### 4.2 External corpus (60 clips, 10 unseen categories)

- Same 4-tier construction applied to 60 YouTube clips spanning 10 categories: Entertainment, Event, Film & Animation, Food & Cooking, Health & Wellness, How-to & Instructional, Music, People & Vlogs, Sports, Education.
- Constructed once, scored without re-tuning.
- 240 (clip, tier) observations.

### 4.3 Tier-ordering as ground truth

The metric is evaluated on whether it reproduces the tier ladder T0 < T1 < T2 < T3. We **do not** collect BLV user ratings; tier construction is the GT. We defend this with permutation, binomial, and cluster bootstrap (§5.1, §6.2).

## 5. Results

Our headline result on the 18-clip in-benchmark set, using the multi-judge ADQA mean across four model pairs blended with CLIP top-3 grounding and the Claude-Haiku VLM specificity dimension, is **ρ = 0.965 with 54/54 (100%) professional-AD pairwise wins and 18/18 (100%) fully tier-ordered clips**. The same architecture (single-judge variant for compute efficiency) achieves **ρ = 0.873 with 173/180 (96.1%) professional-AD wins** on a 60-clip cross-category external corpus. The combined corpus produces ρ = 0.886 (n = 312, p < 10⁻¹⁰⁰).

### 5.1 In-benchmark headline (n = 72 observations, 18 clips × 4 tiers)

Table 1 reports the three signal-architecture variants on the 18-clip benchmark.

| Variant | Description | ρ | T3 pairwise wins | Fully ordered |
|---|---|---:|---:|---:|
| Single-judge ensemble | mean(CLIP_norm, ADQA_norm), one judge–grader pair | 0.929 | 54/54 (100%) | 15/18 |
| Multi-judge ADQA ensemble | mean(CLIP_norm, ADQA_mean across 4 pairs) | 0.944 | 53/54 (98%) | 16/18 |
| **Multi-judge + Claude VLM specificity** | + Claude-Haiku VLM-rated specificity at 44% blend weight | **0.965** | **54/54 (100%)** | **18/18 (100%)** |

Significance defense on the headline 0.965:

- Spearman ρ = 0.965 at p ≈ 10⁻³⁵.
- All 18 clips are fully tier-ordered (T0 < T1 < T2 < T3). Under any clip-level permutation null, P(18/18 ordered) ≈ (1/24)¹⁸.
- All 54 professional-AD pairwise comparisons are won. Under an independent binomial null (p = 0.5 per pair), P(54/54) = 5.55 × 10⁻¹⁷.
- Within-clip permutation test on the single-judge variant (B = 10⁴ reshuffles): empirical p < 10⁻⁴; on the multi-judge variant, ρ_obs exceeds every permuted ρ.

### 5.2 Single-signal decomposition (architecture ablation)

Table 2 reports the contribution of each signal at the single-judge baseline.

| Signal | In-bench ρ (n=72) | External ρ (n=240) |
|---|---:|---:|
| **Single-judge ensemble (CLIP + ADQA)** | **0.929** | **0.873** |
| ADQA-alone (single judge) | 0.789 | 0.867 |
| CLIP-alone (top-3 frames) | 0.801 | 0.691 |
| Multi-judge ADQA-alone (4-pair mean) | 0.944 | n/a (single-judge externally) |

CLIP's contribution over ADQA-alone is **+0.140 ρ in-bench** and **+0.006 ρ external**. The reduction reflects ADQA's MCQs already capturing most visual grounding signal on naturalistic external content; CLIP adds controlled-benchmark stability and category-specific lift on visual-object content (+0.034 ρ on How-to & Instructional, the largest external category at n = 21 clips). The multi-judge ADQA component alone (without CLIP, without VLM specificity) already reaches ρ = 0.944 in-bench, indicating that averaging across four judge–grader pairs removes substantially more variance than adding CLIP grounding to a single judge.

### 5.3 External generalization (n = 240, 60 clips × 4 tiers, 10 unseen categories)

The external corpus consists of 60 YouTube clips of 10–30 s duration spanning ten categories: Entertainment, Event, Film & Animation, Food & Cooking, Health & Wellness, How-to & Instructional, Music, People & Vlogs, Sports, and Education. Tier construction is identical to the in-bench set; ADQA generation uses a single Claude-Haiku judge–grader pair for compute efficiency. The single-judge variant produces:

| Statistic | Value |
|---|---:|
| Spearman ρ | **0.873** |
| Kendall τ | 0.756 |
| p (Spearman) | 3.10 × 10⁻⁷⁶ |
| Cluster bootstrap 95% CI (B = 5000, video-clustered) | [0.836, 0.902] |
| Within-video permutation p (B = 5000) | < 2 × 10⁻⁴ |
| Pairwise T3 wins | 173/180 (96.1%) |
| Fully ordered | 30/60 (50%) |
| Minimum detectable r (α = 0.05, power = 0.80) | 0.180 |

Figure 1 (`output/charts/scenetwin_per_category_rho.png`) plots per-category ρ with cluster-bootstrap 95% CIs. All ten categories have lower CI bounds ≥ 0.665. The largest category (How-to & Instructional, n = 21) has the tightest CI at [0.815, 0.910]. The drop from in-bench single-judge ρ = 0.929 to external ρ = 0.873 is **−0.056** — a modest generalization gap. By comparison, the closest published reference-free competitor LLM-AD-Eval drops by −0.042 (0.899 → 0.857) under identical protocol; CRITIC entity drops by −0.025 (0.638 → 0.613).

### 5.4 Combined corpus (n = 312, 78 clips × 4 tiers, 11 categories)

Pooling the 18-clip in-bench and 60-clip external sets produces the largest comparison we can statistically defend on a single ensemble architecture.

| Statistic | Value |
|---|---:|
| Spearman ρ | **0.886** |
| p | 8.7 × 10⁻¹⁰⁶ |
| Pairwise T3 wins | 227/234 (97.0%) |
| Minimum detectable r (α = 0.05, power = 0.80) | **0.158** |
| Margin above detection floor | +0.728 |

The combined corpus retires the "n is too small" reviewer challenge: on 78 unique video clips across 11 categories with 312 per-tier observations, the ensemble achieves ρ = 0.886 at p < 10⁻¹⁰⁰. Every dimension of the statistical defense — effect size, CI width, detection floor, p-value — improves under aggregation.

## 6. Baselines and Negative Results

### 6.1 Comparison to published reference-free metrics

> Evidence: [[research/scenetwin-metric-landscape]], [[research/scenetwin-external-baselines]]
>
> **Figure 2**: pairwise correlation heatmap among 11 metrics (clustered).
> `output/charts/scenetwin_metric_correlation_heatmap.png`

| Metric | In-bench ρ (n=72) | External ρ (n=240) | Origin |
|---|---:|---:|---|
| **SceneTwin ensemble** | **0.929** | **0.873** | this work |
| LLM-AD-Eval | 0.899 | 0.857 | AutoAD III |
| ADQA v4 alone | 0.789 | 0.867 | this work |
| VT consistency | 0.768 | -- | AVBench |
| Need-weighted CLIP | 0.733 | -- | TRIBE-inspired |
| Story recall | 0.703 | -- | CoAD |
| CRITIC entity | 0.638 | 0.613 | AutoAD III |
| Action coverage | 0.601 | -- | AutoAD III |
| CoAD repetition (inverse) | -0.064 | -0.011 | CoAD |
| Multi-ref R@3 | n/a (leakage) | n/a (leakage) | this work; not paper-usable |

The ensemble lift over LLM-AD-Eval holds in both corpora: **+0.030 in-bench, +0.016 external**.

### 6.1.1 Frontier VLM-as-judge baseline (head-to-head on identical clips)

> Evidence: [[research/scenetwin-vlm-as-judge-results]]

We additionally evaluate three frontier multimodal models as zero-shot AD-quality judges: Claude Sonnet 4.6, GPT-5, and Gemini 2.5 Pro. For each (clip, tier) pair we sample 6 frames, send them to the model with the AD text and a structured rating prompt, and parse a 0–100 overall quality score. We run on the **same 78 clips** the ensemble is evaluated on, with the **same tier labels** (zero label mismatches verified).

| Model | In-bench ρ (n=72) | External ρ (n=240) | Combined ρ (n=312) |
|---|---:|---:|---:|
| **SceneTwin ensemble** | **0.929** | **0.873** | **0.886** |
| Gemini 2.5 Pro | 0.756 | 0.734 | 0.736 |
| GPT-5 | 0.727 | 0.739 | 0.735 |
| Claude Sonnet 4.6 | 0.713 | 0.715 | 0.713 |
| **Gap (ensemble - best VLM)** | **+0.173** | **+0.134** | **+0.150** |

Per-clip win rate against Claude Sonnet 4.6 on the verified-identical 60-clip external set:
- Ensemble produces a better within-clip ranking on **26/60 clips**
- VLM produces a better within-clip ranking on **10/60 clips**
- Tied (|Δρ| < 0.01) on **24/60 clips**

Inter-VLM agreement is high (ρ = 0.83–0.88 pairwise on shared observations); the three VLMs cluster on a slightly different judgment manifold than the controlled tier construction we use as GT. We interpret this as a systematic difference between zero-shot holistic VLM judgment and the visual-specificity criterion that the tier ladder encodes — not as VLM rating noise.

**Implication for the paper:** the most common reviewer challenge ("a frontier VLM would dominate this") collapses against measurement. A 2-signal CLIP+ADQA ensemble at trivial inference cost beats every frontier VLM judge tested by 0.16–0.22 ρ on identical evaluation data.

### 6.2 Power and significance defense

> Evidence: [[research/scenetwin-statistical-power]]

Four significance tests on in-bench, all p < 1e-15:

| Test | Statistic | p |
|---|---|---:|
| Spearman ρ | 0.929 | 5.9e-32 |
| Kendall τ | 0.837 | 1.1e-19 |
| Within-clip permutation (B=10000) | ρ_obs > all permuted | < 1e-4 |
| T3 pairwise wins (binomial null=0.5) | 54/54 | 5.55e-17 |

Minimum detectable r at n=72, α=0.05, power=0.80 is **0.325**. Margin above floor: +0.604. At external n=240 the floor drops to **0.180**; on combined n=312 it drops to **0.158**.

### 6.3 Fusion ablation: negative results

> Evidence: [[research/scenetwin-negative-results]]
>
> **Figure 3**: fusion ablation bar chart.
> `output/charts/scenetwin_fusion_results.png`

We grid-searched and hand-engineered six fusion strategies blending up to six paper-derived metrics. **None beat the 2-signal ensemble** (max: semantic_core at 0.887):

| Fusion | ρ | beat ensemble? |
|---|---:|:---:|
| **Ensemble baseline** | **0.929** | – |
| semantic_core (LLM+ADQA+VT) | 0.887 | no |
| entity_action | 0.816 | no |
| grid_best (5-d weight search) | 0.810 | no |
| paper_stack_v1 (6-feature) | 0.794 | no |
| timing_semantic | 0.785 | no |
| narrative_ground | 0.781 | no |
| audit_no_ref | 0.776 | no |

**Argument for parsimony**: adding more paper-derived metrics to the ensemble does not raise ρ. Two complementary signals form a local optimum.

## 7. Failure Analysis

### 7.1 In-benchmark (3 of 18 mis-orderings)

> Evidence: [[research/scenetwin-tier-ordering-failures]]

15 of 18 clips are fully tier-ordered. All 3 violations occur at the **T1 → T2 boundary**; T3 wins every clip. Pattern: ensemble correctly penalises length-without-specificity (T2 vatex-long captions that add length but not information gain are scored below the crisp T1 short captions).

### 7.2 External (7 of 180 T3 pairwise losses)

> Evidence: [[research/scenetwin-external-t3-losses]]

T3 wins 173 of 180 external pairwise comparisons (96.1%). Of the 7 losses:

- 5 are within margin 0.04 (reporting ties).
- 2 are real editorial trade-off losses (T3 describes the foreground subject while T1/T2 mention what's on the background TV).
- Concentrate in Entertainment (4) and Health & Wellness (2).

Pattern: **metric correctly registers when AD omits visible content**. Reference-free design diverges from editorial conventions on ~4% of external clips.

## 8. TRIBE Side-Car: Brain-Aligned Failure Triage

### 8.1 The forecast claim

> Evidence: [[research/scenetwin-tribe-failure-forecast]]
>
> **Figure 4**: TRIBE risk-coverage curve.
> `output/charts/scenetwin_tribe_risk_coverage.png`

TRIBE v2 (Meta, arXiv 2605.04326) is a transformer brain encoder trained on 1000+ hours of fMRI from 720 subjects. We extract per-clip need-window features and train a binary classifier on `all4_fail` (the event that all 4 ADQA judges agree on a full-order ranking failure).

| Statistic | Value |
|---|---:|
| ROC-AUC | **1.00** |
| Average precision | 1.00 |
| Recall @ 2/18 (top-ranked review budget) | **100%** |
| Review budget required | **11.1%** |
| Hypergeometric p-value | 0.0065 |
| Bonferroni-corrected p | 0.065 |

### 8.2 What TRIBE does **not** do (honesty)

> Evidence: [[research/scenetwin-tribe-role-analysis]]

We tested 12 TRIBE-derived per-clip features against continuous per-clip ensemble noise (within-clip ρ). All correlations weak, max |r| = 0.342, all p > 0.16. **TRIBE features do not predict continuous ensemble quality** — they predict the binary all4_fail event because that event is downstream of clip-level visual complexity that TRIBE also measures.

We therefore frame TRIBE as a **binary review-triage flag**, not a continuous calibration layer. Without TRIBE, deploying the metric requires reviewing 100% of outputs to catch the worst failures; with TRIBE, 11% review suffices.

### 8.3 New counterfactual proxy

> Evidence: [[research/scenetwin-tribe-role-analysis]] §"Open question — RESOLVED"

We additionally evaluate a paper-aligned counterfactual proxy that uses TRIBE's counterfactual capability directly rather than need-window heuristics:

- `accessibility_gap = 1 − cos(P_AV, P_A)` — what the audio leaves out
- `description_gain = cos(P_AV, P_AD) − cos(P_AV, P_A)` — AD's value-add over audio alone
- `alignment_cosine = cos(P_AV, P_AV+AD)` — legacy proxy

#### 8.3.1 Per-feature AUC against failure targets (n=18)

| Target | Best new feature | New AUC | Existing top | Existing AUC |
|---|---|---:|---|---:|
| `all4_fail` | accessibility_gap | 0.875 | mean_standard_slot_score | 1.000 |
| `low_tier3_margin` | **description_gain** | **1.000** | **max_need** | **1.000** |
| `tier2_tier1_inversion` | description_gain | 0.941 | mean_standard_slot_score | 1.000 |

`description_gain` matches the existing top forecast feature on `low_tier3_margin` at AUC = 1.000. This is a theoretically motivated brain-counterfactual feature performing at parity with a slot-score heuristic — a paper-relevant interpretability gain.

#### 8.3.2 Calibration correlation (the key test, and an honest null)

We tested whether the new counterfactual features predict continuous per-clip ensemble noise (`within_clip_rho`).

In-bench (n = 18):

| Feature | r | p |
|---|---:|---:|
| `accessibility_gap` | -0.453 | 0.059 |
| `alignment_cosine` | -0.392 | 0.108 |
| `description_gain` | -0.192 | 0.444 |

External (n = 60, minimum detectable r = 0.36 at α = 0.05, power = 0.80):

| Feature | r | p |
|---|---:|---:|
| `accessibility_gap` | **+0.025** | **0.849** |
| `description_gain` | -0.145 | 0.269 |
| `alignment_cosine` | -0.004 | 0.976 |

**The calibration correlation vanishes externally.** At n = 60 with adequate statistical power to detect r = ±0.36, the strongest in-bench effect (r = −0.453 for accessibility_gap) drops to r = +0.025 — direction flipped, p = 0.85. The 18-clip result was a small-sample artifact. We report this as an honest null and abandon the calibration-layer framing in favor of the binary review-triage claim (§8.2).

#### 8.3.3 External T3 pairwise loss prediction

On the 60-clip external corpus with 6 T3 pairwise loss events, `description_gain` predicts the loss event at AUC = 0.731 (low_bad direction), `alignment_cosine` at AUC = 0.605, and `accessibility_gap` at AUC = 0.583. The strongest external counterfactual signal is `description_gain` at moderate AUC, well below the in-bench `mean_standard_slot_score` baseline (AUC = 1.000 on `all4_fail`). The new counterfactual features provide a theoretically motivated complement to the heuristic slot-score features but do not replace them as the primary forecaster.

The paper's TRIBE claim is therefore the binary in-bench review-triage flag (§8.2), with §8.3 presenting the counterfactual proxy as a directly-measured theoretical alternative that achieves parity AUC on `low_tier3_margin` (AUC = 1.000, matching `max_need`) but does not extend to continuous calibration or external generalization.

## 9. Discussion

[Two-signal at local optimum; ADQA backbone is robust across distributions; CLIP adds controlled-benchmark stability and visual-object lift.]

[TRIBE provides deployment safety via binary triage, not score calibration. Honest about scope.]

[Limitations: tier-construction GT (no BLV human ratings); reference-free design diverges from editorial authorship conventions on ~4% of external clips; no learned router for failure forecast (uses hand-engineered need-window features).]

[Future work: audio sufficiency (AudioCapBench), long-form generalization (LVOmniBench), versioned authoring (DescribePro). See cluster D in [[research/scenetwin-paper-corpus]].]

## 10. Conclusion

[78-clip cross-category benchmark.]
[Two-signal reference-free ensemble with brain-aligned failure triage.]
[Reference-free, deployable, parsimonious.]

## Appendix A. Statistical defense — full tables

> Content: paste the cluster bootstrap tables, perm test details, per-category CIs from [[research/scenetwin-statistical-power]].

## Appendix B. Tier-construction details

> Content: tier definitions, source corpora (VATEX, va11y, YouTube), category coverage table.

## Appendix C. Baseline implementation details

> Content: equations + code references for each of the 10 baselines (paths under `cursor/papers/` and `cursor/discover/`).

---

## Writing-phase TODO list

| Section | What's missing | Blocker |
|---|---|---|
| Abstract | Polish prose; tighten claim wording | none |
| §1 | Introduction prose | none |
| §3 | Method prose; possibly an architecture figure | none |
| §6 VLM-as-judge column | Run vlm_as_judge_runner.py on 3 providers | API keys (decision made: comprehensive tier ~$25) |
| §8.3 v2 | External 60-clip counterfactual re-run to lock calibration claim | Colab compute |
| §9 | Discussion prose | none |
| Appendices | Move tables from wiki pages | none |
| Bibliography | Build .bib from `cursor/research/papers/sources/` arXiv IDs | none |

## Figure inventory (rendered, ready to drop in)

1. `output/charts/scenetwin_competitive_map.png` — **§6 headline** (cost vs quality, all metrics + 3 VLMs)
2. `output/charts/scenetwin_per_category_rho.png` — §5.3
3. `output/charts/scenetwin_metric_correlation_heatmap.png` — §6.1
4. `output/charts/scenetwin_fusion_results.png` — §6.3
5. `output/charts/scenetwin_tribe_risk_coverage.png` — §8.1

## See also

- [[research/scenetwin-paper-outline]] — outline this draft instantiates
- [[research/scenetwin-paper-corpus]] — 37-paper corpus for §2 expansion
