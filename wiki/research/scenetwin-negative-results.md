---
title: SceneTwin negative results — what we tried that did NOT beat the ensemble
category: research
tags: [scenetwin, paper-section, negative-results, ablation]
sources: [cursor/papers/output/paper_fusion_leaderboard.csv, cursor/research/output/external_paper_baselines_leaderboard.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

We implemented eight paper-derived metrics, six fusion strategies, two TRIBE-as-calibration mechanisms, and a gated two-stage routing pipeline. **None of them beat the 2-signal CLIP + ADQA ensemble on rho.** The negative results table is itself a contribution: it argues against adding more reference-free metrics to the AD-evaluation zoo, in favor of the parsimony of two complementary signals.

## What we tried

### 1. Single-metric replacements (8 paper baselines)

See [[research/scenetwin-metric-landscape]]. Best single metric: LLM-AD-Eval at rho = 0.899 (0.030 below ensemble). Six other published metrics tested at 0.532 to 0.789. Conclusion: no single published reference-free metric matches the 2-signal ensemble.

### 2. Fusion strategies (6 blends)

| Fusion | rho | beat ensemble? |
|---|---:|:---:|
| **ensemble (baseline)** | **0.929** | -- |
| semantic_core (LLM + ADQA + VT) | 0.887 | no |
| entity_action (ADQA + CRITIC + action) | 0.816 | no |
| grid_best (5d grid search) | 0.810 | no |
| paper_stack_v1 (6-feature) | 0.794 | no |
| timing_semantic | 0.785 | no |
| narrative_ground | 0.781 | no |
| audit_no_ref | 0.776 | no |

Grid search over weights with up to six paper-derived metrics could not exceed 0.929. **Adding more signals to the ensemble does not help.** Two signals at a local optimum.

### 3. TRIBE as continuous calibration layer

See [[research/scenetwin-tribe-role-analysis]]. Tested 12 TRIBE-derived per-clip features against per-clip ensemble noise (within_clip_rho). All correlations weak (max |r| = 0.342), all p > 0.16. TRIBE features do NOT predict continuous ensemble quality. The calibration-layer paper framing is not supported by data.

What DOES work: TRIBE forecasts the binary `all4_fail` event at AUC = 1.00, recall@2/18 = 100% (11% review budget). This is a different task than calibration -- review triage, not score adjustment.

### 4. TRIBE-gated two-stage pipeline

Routed clips by TRIBE pressure quantile: high-pressure -> ADQA only; low-pressure -> CLIP+ADQA ensemble. Result:

| Threshold | Gated rho | vs baseline 0.929 |
|---|---:|---:|
| q25 | 0.848 | -0.081 |
| q33 | 0.850 | -0.079 |
| q50 | 0.848 | -0.081 |
| q67 | 0.892 | -0.037 |
| q75 | 0.902 | -0.027 |
| Inverted (low-pressure -> ADQA) | 0.918 | -0.011 |

Every gating threshold **hurts** the headline rho. TRIBE-routed dual-scoring is not viable.

### 5. Closure metric and its descendants (dead branch)

The 2026-05-11 sweep killed:

- Closure metric: ranks shorter AD above pro AD on clips 01 and 03.
- Description Gain / MVRR: same failure mode.
- ROI content typing: weak signal, no rho lift.
- Neural closure: did not generalize.
- TRIBE-weighted ADQA: confused two orthogonal signals.

These are catalogued in [[research/scene twin codex]] for reference.

## Why the negative results matter for the paper

Three independent reasons:

1. **Argument against the metric zoo.** Reference-free AD evaluation has accumulated 10+ proposed metrics. We show that blending them does not improve over a 2-signal design. This is a position the paper can take: parsimony beats accumulation.

2. **Pre-empts the "did you try X?" reviewer challenge.** For each published metric we implemented and measured it. For each plausible fusion we ran a grid search. Reviewers cannot ask us to try the metrics we already exhausted.

3. **Honest TRIBE role.** Rather than overclaiming TRIBE as a continuous calibration component, we report the measurement (it isn't) and reframe the contribution to what works (binary review triage). Reviewers reward honest negative results when they preempt rather than admit weakness.

## Recommended paper subsection

```
Section X. Negative Results

We implemented eight paper-derived reference-free AD metrics
(Table 4) and constructed six weighted fusions of them
(Table 5). No combination achieved Spearman rho above the
2-signal CLIP+ADQA ensemble. We additionally tested two
TRIBE-as-calibration mechanisms: per-clip ensemble-noise
prediction (all 12 candidate features, p > 0.16) and a
two-stage gated pipeline (every threshold reduced rho by 0.01
to 0.08). The continuous calibration story is not supported
by data; TRIBE's measurable contribution is binary review
triage (Section X.Y), not score calibration.

These negative results argue for parsimony in reference-free
AD evaluation. Two complementary signals -- CLIP visual
grounding and frame-grounded ADQA MCQs -- form a local optimum
in the explored metric space. Adding semantic-similarity,
entity-coverage, narrative-recall, action-coverage, or
neural-counterfactual features does not improve rho.
```

## See Also

- [[research/scenetwin-metric-landscape]] -- positive comparison vs baselines
- [[research/scenetwin-tribe-role-analysis]] -- the TRIBE-calibration negative result
- [[research/scenetwin-external-baselines]] -- external replication of negative results

## Sources

- `cursor/papers/output/paper_fusion_leaderboard.csv` (fusion experiments)
- `cursor/research/output/scenetwin_per_clip_tribe_calibration.csv` (TRIBE calibration test)
- `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md` (literature synthesis)
