---
title: SceneTwin metric landscape — where 2-signal ensemble sits vs paper baselines
category: research
tags: [scenetwin, paper-section, baselines, related-work]
sources: [cursor/papers/output/metric_leaderboard.csv, cursor/research/output/external_paper_baselines_leaderboard.csv, cursor/papers/output/paper_fusion_leaderboard.csv]
created: 2026-05-29
updated: 2026-06-27
---

> **The leaderboards below are the retired 4-tier sweep.** On the **corrected 3-tier ladder** the
> **60-clip set is primary**: SceneTwin ρ = **0.952** vs LLM-AD-Eval **0.942** (lift **+0.010**);
> 18-clip pilot SceneTwin **0.957** vs LLM-AD-Eval **0.941** (lift **+0.016**). The corrected-ladder
> claim is **near-tie with the reference-style LLM-AD-Eval**, reframed as deployability without a
> human reference AD (see manuscript). Per-baseline corrected values for the other eight metrics
> need regenerating; the 4-tier numbers here are superseded.

## Headline (retired 4-tier sweep)

We implemented and ran ten paper-derived reference-free metrics on the 18-clip benchmark. Across all of them, the 2-signal CLIP+ADQA ensemble achieves rho = 0.929 -- **+0.030 over the closest published competitor (LLM-AD-Eval proxy at 0.899)**. We then ran the same baselines on the 60-clip external corpus; the lift held at **+0.016** (ensemble 0.873 vs LLM-AD-Eval 0.857). Five additional metrics did not beat the ensemble even with grid-searched blends.

## In-benchmark leaderboard (18 clips x 4 tiers, n=72)

| Metric | rho | p | Origin |
|---|---:|---:|---|
| **SceneTwin ensemble (CLIP + ADQA)** | **0.929** | 1.0e-31 | this work |
| LLM-AD-Eval (sentence-emb similarity to T3) | 0.899 | 8.4e-27 | AutoAD III, arxiv 2404.14412 |
| ADQA v4 (alone) | 0.789 | 1.9e-16 | this work |
| VT consistency (T3-video text-vision similarity) | 0.768 | 3.4e-15 | AVBench-style, arxiv 2605.24652 |
| Need-weighted CLIP (TRIBE-need-curve weighting) | 0.733 | 2.5e-13 | TRIBE-inspired, this work |
| Story recall (CoAD beat-driven recall) | 0.703 | 6.0e-12 | CoAD, arxiv 2510.25440 |
| CRITIC entity proxy (proper noun + role match) | 0.638 | 1.6e-9 | AutoAD III, arxiv 2404.14412 |
| Action coverage (ADQA action-question split) | 0.601 | 2.4e-8 | AutoAD III, arxiv 2404.14412 |
| Multi-ref R@3/N (token recall vs 3-tier union) | 0.532 | 1.5e-6 | this work |
| CoAD repetition penalty (inverse) | -0.064 | 0.595 | CoAD, arxiv 2510.25440 |

## Fusion experiments (paper-stack blends)

We grid-searched and hand-engineered blends of the above metrics. None beat the 2-signal ensemble:

| Fusion | rho | Construction |
|---|---:|---|
| **Ensemble (baseline)** | **0.929** | mean(CLIP_norm, ADQA_norm) |
| semantic_core | 0.887 | mean(z(llm_ad_eval), z(adqa), z(vt_consistency)) |
| entity_action | 0.816 | 0.55*ADQA + 0.20*CRITIC + 0.25*action_coverage |
| grid_best (5d grid search) | 0.810 | 0.75*ADQA + 0.25*vt_consistency |
| paper_stack_v1 (6-feature blend) | 0.794 | weighted: 0.35 ADQA, 0.20 story, 0.20 vt, 0.10 action, 0.10 need_weighted, 0.05 timing |
| timing_semantic | 0.785 | 0.40*ADQA + 0.35*timing_g7g8 + 0.25*need_weighted |
| narrative_ground | 0.781 | 0.50*ADQA + 0.30*story_recall + 0.20*action_coverage |
| audit_no_ref | 0.776 | 0.45*ADQA + 0.40*vt_consistency - 0.15*coad_repetition |

**Finding:** Adding more paper-derived metrics to the ensemble does not raise rho. The two signals (CLIP visual grounding + frame-grounded ADQA MCQs) are sufficient. This is a paper contribution in itself -- it argues for parsimony over the metric zoo.

## Pairwise metric correlations (n=72)

Cluster A (semantic / reference-similar, rho > 0.85 with ensemble):
- `llm_ad_eval` <-> `ensemble`: 0.887
- `vt_consistency` <-> `adqa_v4`: 0.814
- `adqa_v4` <-> `ensemble`: 0.779

Cluster B (narrative / temporal, weaker correlations with ensemble):
- `story_recall` <-> `vt_consistency`: 0.902
- `need_weighted` <-> `ensemble`: 0.802

Cluster C (weak signals):
- `coad_repetition` anti-correlates with all Cluster A (pro AD is longer + more repetitive)
- `multi_ref_r3` collapses (trivial when T3 is in reference set)

## External replication of the top baselines (60 clips x 4 tiers, n=240)

| Metric | In-bench rho | External rho | Delta |
|---|---:|---:|---:|
| **SceneTwin ensemble** | **0.929** | **0.873** | -0.056 |
| LLM-AD-Eval | 0.899 | 0.857 | -0.042 |
| CRITIC entity | 0.638 | 0.613 | -0.025 |
| CoAD repetition (inv) | -0.064 | -0.011 | +0.053 |
| word_count (control) | -- | 0.339 | -- |

The ensemble lift (+0.030 in-bench, +0.016 external) holds in both settings. See [[research/scenetwin-external-baselines]] for the reference-leakage caveat affecting multi_ref_r3 and token_overlap.

## What the paper's Related Work / Baselines section should say

```
We compare against ten reference-free AD evaluation metrics
covering semantic similarity (LLM-AD-Eval), entity coverage
(CRITIC), action coverage and story recall (AutoAD III, CoAD),
audio-visual consistency (AVBench), reference-token recall
(multi-ref R@k), and length-and-repetition baselines. We also
grid-searched and hand-engineered six fusion strategies blending
up to six paper-derived metrics. Across all configurations the
two-signal CLIP+ADQA ensemble achieves the highest rho on the
18-clip benchmark (+0.030 over the strongest published
competitor) and the strongest external replication (+0.016 on a
60-clip cross-category corpus). Fusion experiments suggest the
two-signal design is at a local optimum within the explored
metric space.
```

## See Also

- [[research/scenetwin-external-baselines]] - external (60-clip) replication of the top baselines
- [[research/scenetwin-external-validation]] - external ensemble rho
- [[research/scenetwin-statistical-power]] - power defense including baseline rho comparisons

## Sources

- `cursor/papers/output/metric_leaderboard.csv` (in-bench 18-clip leaderboard)
- `cursor/papers/output/paper_fusion_leaderboard.csv` (fusion experiments)
- `cursor/papers/output/metric_correlations.csv` (pairwise metric rho)
- `cursor/research/output/external_paper_baselines_leaderboard.csv` (external 60-clip)
- `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md` (literature-level analysis)
