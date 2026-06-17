---
title: SceneTwin paper outline — Papers A and B
category: research
tags: [scenetwin, paper-planning, outline, master-doc]
sources: [wiki/research/*]
created: 2026-05-29
updated: 2026-05-29
---

## Two papers, shared substrate

Same 78-clip dataset (18 in-bench + 60 external), same pipeline. Two distinct contributions, two distinct venues.

---

# Paper A: Reference-free AD evaluation benchmark

**Title (placeholder):** *A Two-Signal Reference-Free Audio Description Evaluation Framework with Brain-Aligned Failure Forecasting*

**Venue cluster:** ACM MM / EMNLP / WACV

## A.1 Abstract claims (locked numbers)

- ρ = **0.929** on 18-clip controlled benchmark (n=72, p < 1e-31)
- ρ = **0.873** on 60-clip external (n=240, 10 unseen categories, p < 3e-76)
- ρ = **0.886** on combined 78-clip corpus (n=312, p < 1e-100)
- T3 pairwise wins: **54/54** in-bench, **173/180 (96.1%)** external
- TRIBE risk forecast: **AUC = 1.00**, recall@2/18 = **100%**, 11% review budget
- Outperforms LLM-AD-Eval (AutoAD III's closest reference-free proxy): **+0.030** in-bench, **+0.016** external

## A.2 Sections

### 1. Introduction
- AD evaluation needs reference-free metrics (live deployment, unseen content)
- Reference-based metrics dominate (CIDEr, BLEU, LLM-AD-Eval) but require human AD
- Reference-free metrics exist but are scattered; no benchmark compares them under identical protocol
- Our contribution: 2-signal ensemble + 78-clip benchmark + 10-baseline comparison + brain-aligned failure forecaster

### 2. Related Work
**Evidence**: [[research/scenetwin-metric-landscape]]
- 10 reference-free metrics with rho on common protocol
- Cluster correlations identify 3 distinct semantic groupings

### 3. Method
- CLIP frame grounding (top-3 frame aggregation)
- Frame-grounded ADQA: per-clip MCQ generation against sampled frames
- Ensemble: `mean(CLIP_norm, ADQA_norm)` per clip
- TRIBE side-car: brain-aligned failure forecaster (separate)

### 4. Benchmark Construction
- 18 controlled clips with 4-tier AD ladder (T0 cross-decoy, T1 short, T2 long, T3 pro)
- 60 external clips, 10 categories, same 4-tier construction
- Tier-ordering as GT defended via permutation + binomial + bootstrap (see §6.1)

### 5. Results
**Evidence**: [[research/scenetwin-external-validation]], [[research/scenetwin-statistical-power]]

#### 5.1 Headline (in-bench)
- ρ = 0.929, CI [0.881, 0.962], 54/54 T3 wins, perm p < 1e-4
- Single-signal: CLIP-only 0.801, ADQA-only 0.789

#### 5.2 External generalization (n=60)
- ρ = 0.873, CI [0.836, 0.902], 173/180 T3 wins
- Per-category rho range [0.81, 0.93], all 10 categories' lower CI >= 0.665
- Drop from in-bench: -0.056

#### 5.3 Combined corpus
- 78 clips, 312 obs, ρ = 0.886, p < 1e-100
- Min detectable r = 0.158; margin +0.729

### 6. Baselines and Negative Results
**Evidence**: [[research/scenetwin-metric-landscape]], [[research/scenetwin-external-baselines]], [[research/scenetwin-negative-results]]

#### 6.1 Power and significance defense
**Evidence**: [[research/scenetwin-statistical-power]]
- 4 significance tests at p < 1e-15
- Cluster bootstrap CI
- Power analysis: rho_min = 0.180 at n=240
- External replication on 60 unseen clips

#### 6.2 Comparison to published metrics (Table)
| Metric | In-bench | External |
|---|---:|---:|
| **Ours (CLIP+ADQA)** | **0.929** | **0.873** |
| LLM-AD-Eval | 0.899 | 0.857 |
| ADQA alone | 0.789 | 0.867 |
| CRITIC entity | 0.638 | 0.613 |
| (...6 more) | | |

#### 6.3 Negative results (fusion ablation)
- 6 fusion strategies with up to 6 paper-derived metrics
- Grid-searched weights
- **None beat the 2-signal baseline** (max: semantic_core at 0.887)
- Argument for parsimony

#### 6.4 Signal decomposition (honesty)
**Evidence**: [[research/scenetwin-signal-decomposition]]
- CLIP lift over ADQA: +0.14 in-bench, +0.006 external
- ADQA is the workhorse on external distributions
- CLIP adds +0.034 on How-to (largest external category)

### 7. Failure Analysis
**Evidence**: [[research/scenetwin-tier-ordering-failures]], [[research/scenetwin-external-t3-losses]]

#### 7.1 In-benchmark (3/18 mis-orderings)
- All 3 at T1->T2 boundary
- Pattern: ensemble penalises length-without-specificity
- T3 wins every clip

#### 7.2 External (7/180 T3 pairwise losses)
- 5/7 within margin 0.04 (ties)
- 2/7 are real editorial framing losses (foreground vs background)
- Concentrate in Entertainment + Health & Wellness

### 8. TRIBE Side-Car: Brain-Aligned Failure Forecaster
**Evidence**: [[research/scenetwin-tribe-failure-forecast]], [[research/scenetwin-tribe-role-analysis]]

#### 8.1 The forecast claim
- AUC = 1.00, recall@2/18 = 100%, 11% review budget
- Drives `mean_standard_slot_score` from TRIBE need-window features

#### 8.2 What TRIBE does NOT do (honesty)
- 12 TRIBE features tested against continuous ensemble noise: all p > 0.16
- TRIBE is a **binary review-triage flag**, not a continuous calibration layer
- Without TRIBE: 100% review required for deployment safety
- With TRIBE: 11% review budget catches all severe failures

#### 8.3 New counterfactual proxy (post-Colab)
*To be filled when notebook returns:*
- `accessibility_gap`, `description_gain`, `alignment_cosine`
- Head-to-head AUC vs `mean_standard_slot_score`
- 60-clip generalization

### 9. Discussion
- Two-signal ensemble at local optimum in 10-metric space
- ADQA backbone robust across distributions; CLIP adds controlled-benchmark stability
- TRIBE provides deployment safety via binary triage, not score adjustment
- Limitations: tier-construction GT (no BLV human ratings); reference-free design diverges from editorial authorship conventions on ~5% of external clips

### 10. Conclusion
- 78-clip cross-category benchmark
- Two-signal ensemble with brain-aligned failure triage
- Reference-free, deployable, parsimonious

## A.3 What's blocked / waiting

| Section | Blocker |
|---|---|
| §8.3 (TRIBE counterfactual) | Colab run completing |
| §6 VLM-as-judge baseline | Task #8 (needs API budget decision) |

## A.4 Figures + tables we have ready

| Figure / Table | Source data | Wiki page |
|---|---|---|
| Tier ladder example | benchmark roster | -- |
| Headline rho comparison | combined_corpus.csv | scenetwin-statistical-power |
| Per-category rho with CIs | external_power_stats.json | scenetwin-statistical-power |
| Metric cluster heatmap | metric_correlations.csv | scenetwin-metric-landscape |
| Baseline leaderboard (10 metrics) | metric_leaderboard.csv | scenetwin-metric-landscape |
| Fusion negative results | paper_fusion_leaderboard.csv | scenetwin-negative-results |
| Signal decomposition (per-cat) | per_clip_clip_vs_adqa.csv | scenetwin-signal-decomposition |
| T3-loss failure examples | external_t3_pairwise_losses.csv | scenetwin-external-t3-losses |
| TRIBE risk-coverage curve | tribe_failure_forecast.csv | scenetwin-tribe-role-analysis |

---

# Paper B: Access Surface OS for BLV video accessibility

**Title (placeholder):** *From Audio Description to Access Surface Routing: A Policy Layer for Blind Video Access*

**Venue cluster:** ASSETS / W4A / CHI / UIST / TACCESS

## B.1 Lead claim

BLV video access is not a captioning problem; it is a **state-reduction problem under viewer, audio, identity, emotion, risk, latency, and compute constraints**. We contribute a routing layer (the *Access Surface OS*) that decides whether each clip should be served as static AD, identity chip, defer/replay, concise cue, creator-QC queue, or task-loop coach -- and on which compute tier.

## B.2 Evidence in hand

**Evidence**: [[research/scenetwin-method-inventory]] -- Paper B section
**Synthesis**: `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md` (sections "Customization / user-agency batch" through "Evidence sidecar / answerability batch")

| Routing claim | Script | Target recall |
|---|---|---:|
| Surface routing (5 surfaces) | access_surface_router | 92% high-collision not-static |
| Assistant mode routing (5 modes) | visual_assistant_skill_policy | **96.3%** |
| Task-loop routing (Vid2Coach / AROMA / StreetReader / CoSight) | task_assistant_affordance | **88.9%** |
| Evidence sidecar bill | evidence_sidecar_readiness | **100%** (target has any sidecar) |
| Commentary residual (MCAD-style) | commentary_residual_ad | -- (qualitative) |

All measured on **58 external clips** with explicit target-recall numbers.

## B.3 Sections (sketch)

1. Introduction
   - Reference-free AD scoring is necessary but insufficient: the question is *what surface to serve*, not just *how good is this AD*.
2. Related work (papers consolidated into the synthesis)
   - 37 papers reviewed in [[research/scenetwin-paper-corpus]] (need to promote synthesis here)
3. The Access Surface OS framework
   - 5 surfaces × 4 compute tiers
   - Routing decision pipeline
4. Empirical evaluation (58 external clips)
   - Routing target recall per claim
   - Cross-claim consistency
5. Limitations and future surfaces (the 12 deferred methods)
6. Conclusion

## B.4 What's blocked

| Section | Blocker |
|---|---|
| §2 Related work | Promote synthesis from cursor/ to wiki/research/scenetwin-paper-corpus.md |
| §4 User study | Out of scope (no human data possible per session constraints) |
| Multi-paper venue tuning | Each venue wants different framing emphasis |

---

# Cross-paper shared assets

| Asset | Both papers use |
|---|---|
| 78-clip dataset | Yes |
| Tier construction protocol | Yes |
| Benchmark CSV schema | Yes |
| External corpus registry | Yes |
| Methods code in `cursor/methods/` | Paper B leans heavier |
| Methods code in `cursor/papers/` | Paper A leans heavier |

# Writing order (recommendation)

1. **Paper A first** because all evidence is locked except §8.3 (TRIBE counterfactual) and the optional VLM baseline. ~2-3 weeks of writing, low new-experiment overhead.
2. **Paper B second**, drafted while Paper A is under review. The synthesis is already 460 lines; the routing evaluations exist; the gap is paper-structure prose + a Related Work section that survives venue review.

## See Also

- [[research/scenetwin-statistical-power]]
- [[research/scenetwin-external-validation]]
- [[research/scenetwin-metric-landscape]]
- [[research/scenetwin-negative-results]]
- [[research/scenetwin-signal-decomposition]]
- [[research/scenetwin-tier-ordering-failures]]
- [[research/scenetwin-external-t3-losses]]
- [[research/scenetwin-tribe-role-analysis]]
- [[research/scenetwin-external-baselines]]
- [[research/scenetwin-method-inventory]]
