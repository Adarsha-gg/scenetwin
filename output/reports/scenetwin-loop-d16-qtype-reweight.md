---
title: "SceneTwin Loop D16 — Question-Type-Reweighted ADQA"
category: research
tags: [scenetwin, adqa, question-types, reweighting, ranking, cached-analysis, null-result]
created: 2026-07-02
---

# SceneTwin Loop D16 — Question-Type-Reweighted ADQA

Cached-data-only analysis (Python stdlib). Script:
`cursor/research/loop_d16_qtype_reweight.py`. Console dump:
`cursor/research/output/loop_d16_console.txt`.

**Question:** D12 showed ADQA question types differ in tier-discrimination
(tier3-vs-tier0 AUC: action_relation 0.959 … object_attr 0.811). Can weighting
each question's contribution by its type's reliability improve how well the ADQA
score ranks the description tiers — or is equal-weight (parsimony) just as good?

---

## Setup

**Eval task.** The SceneTwin tier ladder on the 20-clip timing set: each clip has
three kept description tiers, T0 (cross-category decoy) < T1 (crowd caption) < T3
(professional AD); tier2 (deprecated verbosity rung) is dropped. A good ADQA score
should rank them in that order. Metric = Spearman rho between tier order and the
per-(clip,tier) ADQA score, pooled over all (clip,tier) observations.

**Data / coverage.** Per-question grades joined to `adqa_question_types.csv` on
`(source, video_id, q_idx)`, pooled over the **8 cached ADQA variants** (the same
pool D12 used to derive the weights). **2 052 graded question-instances, 0
unmatched**, tier2 dropped. Coverage = **18 clips x 3 tiers = 54 (clip,tier)
observations**. Per-(clip,tier) ADQA score = weighted mean of that clip's question
scores (all tiers of a clip share the same question set), so reweighting shifts the
relative contribution of question types.

Type instance counts (kept tiers, pooled): object_attr 549, other 456,
action_relation 333, who_role 306, spatial_relation 285, count 123.

---

## Task 1+2 — equal-weight baseline vs reweighting schemes

| scheme | weight per question | rho | Δ vs equal |
|---|---|---|---|
| **equal (baseline)** | 1 | **+0.9319** | — |
| linear AUC | AUC_type | +0.9338 | +0.0019 |
| AUC² | AUC_type² | +0.9338 | +0.0019 |
| AUC−0.5 (excess) | max(AUC−0.5, 0) | +0.9338 | +0.0019 |
| drop 2 weakest | 0 for spatial_relation & object_attr | +0.9293 | −0.0026 |

All 54-obs. The three "up-weight reliable types" schemes converge on the **same**
tiny gain (+0.0019 rho); sharpening the weights (AUC² vs linear) changes nothing.
Dropping the two weakest types slightly **hurts** (−0.0026).

## Task 3 — scene-model ablation

| subset | rho | Δ vs all |
|---|---|---|
| all questions | **+0.9319** | — |
| scene-model only (relation/action/count/who) | +0.9146 | −0.0174 |
| non-scene-model only | +0.8852 | −0.0467 |

Using **all** questions beats either subset. Scene-model questions rank better than
non-scene-model ones (consistent with D12's discrimination gap), but discarding
half the questions loses signal — more questions win over "purer" questions.

## Task 4 — is any delta meaningful at this n?

Bootstrap over clips (B=5000, resample 18 clips w/ replacement, seed=7; rho and
delta share each resample):

- **Equal-weight rho = +0.9319, 95% CI [+0.9172, +0.9485]** — strong; within-clip
  tier-label permutation p = **0.00005** (20 000 perms). The ladder itself is real.

| scheme | Δρ | 95% CI(Δρ) | P(Δρ>0) |
|---|---|---|---|
| linear AUC | +0.0019 | [−0.0007, +0.0053] | 0.724 |
| AUC² | +0.0019 | [−0.0007, +0.0053] | 0.724 |
| drop 2 weakest | −0.0026 | [−0.0203, +0.0144] | 0.393 |
| scene-model only | −0.0174 | [−0.0449, +0.0141] | 0.133 |
| non-scene-model only | −0.0467 | [−0.0729, −0.0157] | **0.001** |

The reliability-reweighting deltas straddle zero (P≈0.72, CI includes 0) — a
positive lean too small to call. The only CI that clears zero is
**non-scene-model-only, and it is negative** (dropping scene-model questions
reliably hurts).

## Per-variant robustness

Reweighting has no consistent direction across the 8 variants: linear-AUC helps
5 of 8 by ≤+0.014 and hurts 3; drop-2-weakest swings from −0.099 (adqa_v2) to
+0.033 (q-gpt-4o_g-claude). Equal-weight rho ranges 0.825–0.963 by variant — the
across-variant spread (≈0.14) dwarfs any reweighting delta (≤0.02).

---

## Verdict — NULL: keep equal weight

Type-reliability reweighting produces at most **+0.0019 rho** over equal-weight,
with a bootstrap CI that includes zero (P(improvement) ≈ 0.72) and no consistent
sign across variants. Sharper weightings (AUC², excess-AUC) add nothing; dropping
the weakest types slightly hurts. The only reliable effect is that **discarding
questions hurts** — non-scene-model-only is significantly worse (Δρ = −0.047,
P=0.001), and even scene-model-only underperforms using all questions. At n = 18
clips (54 obs, 10 positives-equivalent) all reweighting deltas are inside noise.

**Recommendation:** ship the equal-weight ADQA mean. Per-type reliability is a
useful *diagnostic* (D12) but not a useful *ranking weight* — equal-weight is
already saturated (rho 0.93) and parsimonious. This null supports the current
single-mean design.

---

## Limitations

- **Small n:** 18 clips / 54 (clip,tier) obs; the tier ladder is already near
  ceiling (rho 0.93), leaving little headroom for reweighting to demonstrate gain.
- **Weights are in-sample:** the D12 AUCs were estimated on the same pooled grades
  used here (no held-out split), which if anything *favors* reweighting — yet it
  still doesn't help.
- **Pooled over 8 variants** (different question generators/graders: haiku, gpt-4o,
  tribe, v2, v4). This maximizes n but mixes pipelines; per-variant rho is reported
  for robustness. Pooled per-(clip,tier) score averages instances across variants.
- **`score` is an LLM grader judgment**, not human ground truth; tier2 excluded.
