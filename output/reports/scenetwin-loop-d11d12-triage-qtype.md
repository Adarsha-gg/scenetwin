---
title: "SceneTwin Loop D11+D12 — Triage Fusion & Question-Type Reliability"
category: research
tags: [scenetwin, triage, tribe, adqa, question-types, fusion, cached-analysis]
created: 2026-07-02
---

# SceneTwin Loop D11+D12

Cached-data-only analysis (Python stdlib). Script:
`cursor/research/loop_d11d12_triage_qtype.py`. Console dump:
`cursor/research/output/loop_d11d12_console.txt`.

---

## D11 — Combined review-triage queue

**Question:** does fusing multiple cached signals beat the single best predictor
(`accessibility_gap`, AUC 0.794) at flagging clips whose ADQA fails?

Data: `cursor/research/output/parallel_research/cheap_baselines/external_features.csv`
— 60 clips, 10 ADQA-failure positives.

### Individual predictors (best-direction AUC)

| feature | AUC | dir |
|---|---|---|
| **accessibility_gap** (TRIBE neural) | **0.794** | high |
| tier3_word_count / words_per_sec | 0.714 | low |
| category_loo_adqa_fail_rate* | 0.700 | high |
| transcript_word_count / wps | 0.695 | low |
| mean_scene_spatial_gap | 0.684 | high |
| mean_visual_gap | 0.672 | high |
| description_loss / alignment_loss | 0.622 | high |
| mean_agent_action_gap | 0.588 | high |
| transcript_unique_ratio | 0.558 | low |
| transcript_sound_cue_count | 0.500 | — |

`accessibility_gap` alone: **AUC 0.794, label-permutation p = 0.0023** (20k perms).
*`category_loo_adqa_fail_rate` is derived from the ADQA labels themselves
(leave-one-out), so it is excluded from the honest fusion to avoid leakage.

### Fusion results (rank-average, direction-aligned)

| fusion | features | AUC |
|---|---|---|
| acc + best partner | accessibility_gap + tier3_word_count | **0.800** |
| acc + top-3 | + tier3_words_per_sec, transcript_word_count | 0.797 |
| acc + top-2 | + tier3_words_per_sec | 0.782 |
| acc + neural + cheap (11 feats) | kitchen sink | 0.774 |
| acc + all neural gaps | 5 TRIBE/visual gaps | 0.696 |

Best fusion (accessibility_gap + tier3_word_count) = **AUC 0.800**
(z-score-sum variant 0.798), **label-perm p = 0.0021**,
**Δ = +0.006 AUC** over `accessibility_gap` alone. (Leaky context: adding the
label-derived `category_loo` feature reaches 0.823 — not a fair comparison.)

### Recall at review budgets

| budget | k clips | accessibility_gap | fusion (acc+tier3_word_count) | random (exp.) |
|---|---|---|---|---|
| 10% | 6 | **4/10 (0.40)** | 3/10 (0.30) | 0.10 |
| 20% | 12 | **6/10 (0.60)** | 5/10 (0.50) | 0.20 |
| 30% | 18 | **7/10 (0.70)** | 6/10 (0.60) | 0.30 |

### D11 verdict — fusion does NOT help; `accessibility_gap` alone is best

The best honest fusion improves AUC by a trivial +0.006, and on the operationally
meaningful metric (recall at 10/20/30% review budgets) `accessibility_gap` alone
**beats every fusion** at every budget. Both single-signal and fusion crush the
random baseline (3-4x recall at a 10-20% budget). Adding word-count / transcript /
extra-gap features does not add complementary signal for this task. With only
**n = 10 positives**, all AUC differences are within permutation noise; there is
no evidence a fused queue is worth the extra plumbing. **Recommendation: ship
`accessibility_gap` as the single triage signal.**

---

## D12 — Question-type ADQA reliability (UNBLOCKED)

Per-question correctness **is** cached: every ADQA variant directory under
`output/scenetwin_timing_20clip/…` carries a `grades.csv` with per-question
`score` (0 / 0.5 / 1) and `tier`. Joining `adqa_question_types.csv`
(684 tagged questions, 8 variants) to those grades on `(source, video_id, q_idx)`
yields **2 736 graded question-instances, 0 unmatched.**

Reliability = how well each question type separates professional AD (tier3) from
cross-category decoys (tier0). Discrimination = mean(T3 score) − mean(T0 score);
AUC = P(T3 instance scored > T0 instance).

| question type | n | yes-rate | T0 | T1 | T3 | T3−T0 | AUC(T3 vs T0) |
|---|---|---|---|---|---|---|---|
| **action_relation** | 444 | 49% | 0.00 | 0.49 | 0.83 | +0.83 | **0.959** |
| **count** | 164 | 47% | 0.12 | 0.26 | 0.85 | +0.73 | **0.920** |
| **other** | 608 | 39% | 0.01 | 0.31 | 0.78 | +0.76 | 0.917 |
| **who_role** | 408 | 37% | 0.01 | 0.28 | 0.73 | +0.72 | 0.899 |
| spatial_relation | 380 | 23% | 0.01 | 0.14 | 0.53 | +0.52 | 0.818 |
| object_attr | 732 | 27% | 0.03 | 0.17 | 0.56 | +0.52 | 0.811 |

Scene-model rollup: scene-model questions (relation/action/count/who,
n = 1 396) discriminate slightly better than non-scene-model (n = 1 340):
AUC 0.898 vs 0.860; T3−T0 +0.70 vs +0.63.

### D12 verdict

**Every** question type discriminates tiers well above chance (AUC 0.81-0.96) —
the ADQA ladder is broadly healthy. The **most reliable** types are
`action_relation` (AUC 0.959), `count` (0.920), `other` (0.917) and `who_role`
(0.899): near-zero yes-rate on decoys and high yes-rate on professional AD.
The **weakest** (still useful) are `spatial_relation` (0.818) and `object_attr`
(0.811): their professional-AD yes-rate is only ~0.53-0.56, meaning even the
gold AD frequently omits fine spatial layout and object attributes, so these
questions are answerable less than half the time even for good descriptions —
they add noise, not signal, at the top of the ladder. Scene-model questions
(the SceneTwin motivation) are marginally the more discriminating half.

---

## Limitations

- **D11:** n = 10 positives → wide CIs; all AUC deltas are inside label-permutation
  noise. `adqa_fail` is a binary threshold on the ADQA score; results may shift
  with a different cut. `category_loo_*` features are label-derived and excluded
  from honest fusion.
- **D12:** grades pooled across 8 ADQA variants (different question generators /
  graders: haiku, gpt-4o, tribe, v2, v4) — this maximizes n but mixes pipelines;
  type-level effects are averages, not a single controlled run. Discrimination
  uses tier0 (cross-category) as the negative; tier2_vatex_long is excluded
  (deprecated verbosity rung). `score` is an LLM grader judgment, not human GT.
