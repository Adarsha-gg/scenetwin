---
title: TRIBE New Findings — Cached-Data Round 2
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_round2.py
  - cursor/research/output/new_findings_round2/
---

# TRIBE New Findings — Cached-Data Round 2

Second no-API/no-GPU sweep. This turns more backlog items into actual local evidence.

## Finding 6 — cross-judge matched-question effect survives cluster bootstrap, but matched>unmatched is not uniformly strong

| Run | Group | videos | questions | mean delta | video-bootstrap 95% CI | W/L/T | sign p |
|---|---|---:|---:|---:|---:|---:|---:|
| haiku_surgical | matched | 43 | 60 | 0.167 | [0.093, 0.243] | 20/2/38 | 0.0001 |
| haiku_surgical | unmatched | 59 | 235 | 0.051 | [0.004, 0.099] | 48/28/159 | 0.0143 |
| haiku_surgical | matched_minus_unmatched | 43 | 43 | 0.154 | [0.049, 0.263] | 21/12/10 | 0.0814 |
| gpt5_crossjudge | matched | 44 | 62 | 0.113 | [0.055, 0.183] | 11/0/51 | 0.0005 |
| gpt5_crossjudge | unmatched | 60 | 238 | 0.017 | [-0.021, 0.054] | 31/24/183 | 0.2094 |
| gpt5_crossjudge | matched_minus_unmatched | 44 | 44 | 0.133 | [0.046, 0.224] | 19/8/17 | 0.0261 |
| opus17_crossjudge | matched | 17 | 24 | 0.167 | [0.036, 0.333] | 8/1/15 | 0.0195 |
| opus17_crossjudge | unmatched | 17 | 61 | 0.000 | [-0.062, 0.067] | 6/5/50 | 0.5000 |
| opus17_crossjudge | matched_minus_unmatched | 17 | 17 | 0.228 | [0.074, 0.407] | 9/1/7 | 0.0107 |
| opus15_subset | matched | 15 | 18 | 0.306 | [0.147, 0.500] | 8/0/10 | 0.0039 |
| opus15_subset | unmatched | 15 | 57 | 0.026 | [-0.053, 0.112] | 5/3/49 | 0.3633 |
| opus15_subset | matched_minus_unmatched | 15 | 15 | 0.319 | [0.133, 0.525] | 8/2/5 | 0.0547 |

Interpretation: the matched-question lift is real across judges. However, the **matched-minus-unmatched** contrast is strongest in the surgical/Opus subsets and weaker in the GPT-5 all-clip run, so paper language should say “targeted questions improve reliably” rather than “all unmatched questions are unaffected in every run.”

Artifact: `crossjudge_meta.csv`.

## Finding 7 — full-window gap-targeted AD gains are not explained by extra length alone, but length is a confound to report

Full-window generated AD is longer by an average of **5.288 words/clip** (median **5.000**) and improves ADQA by **0.080**.

- Spearman(word delta, ADQA delta): **0.049**
- Linear slope: **0.0011 ADQA per extra word**
- Low length-increase half ADQA delta: **0.074**
- High length-increase half ADQA delta: **0.086**
- Non-longer cases: n=14, mean ADQA delta **0.050**
- Win/loss/tie by clip: 31/13/15

Interpretation: targeted AD is somewhat longer, but more words do not explain the gain; if anything the low length-increase half has stronger gains. Still, every paper/demo statement should mention word-count control.

Artifact: `length_control_full_adqa.csv`.

## Finding 8 — review-budget curves support TRIBE as a triage queue, especially with mean visual gap

| Feature | Budget | ADQA failures caught | Recall | Precision |
|---|---:|---:|---:|---:|
| mean_visual_gap | 10% | 2/10 | 0.200 | 0.333 |
| mean_visual_gap | 20% | 3/10 | 0.300 | 0.250 |
| mean_visual_gap | 30% | 4/10 | 0.400 | 0.222 |
| max_visual_gap | 10% | 0/10 | 0.000 | 0.000 |
| max_visual_gap | 20% | 2/10 | 0.200 | 0.167 |
| max_visual_gap | 30% | 4/10 | 0.400 | 0.222 |

Interpretation: `mean_visual_gap` is a better triage queue than `max_visual_gap` for ADQA failures in this cached external check. Use budget curves, not only AUC.

Artifact: `external_triage_budget_curves.csv`.

## Finding 9 — low-pressure early exit is plausible for review reduction, not for CLIP-only replacement

| Gap group | frac | n | ADQA fail rate | Ensemble fail rate | ADQA/ensemble full-order agreement |
|---|---:|---:|---:|---:|---:|
| low | 0.25 | 15 | 0.067 | 0.000 | 0.933 |
| high | 0.25 | 15 | 0.200 | 0.133 | 0.933 |
| low | 0.33 | 20 | 0.050 | 0.000 | 0.950 |
| high | 0.33 | 20 | 0.250 | 0.100 | 0.850 |

Interpretation: bottom-gap clips are safer under ensemble, but CLIP-only still fails often (see artifact). Early exit should mean “less human/frontier review,” not “drop to CLIP-only scoring.”

Artifact: `low_pressure_early_exit.csv`.

## Finding 10 — old all4_fail targets are not a strict-tie artifact

Fail-kind counts from the in-benchmark TRIBE target audit:

```json
{
  "tier2_tier1_inversion": 1,
  "t3_margin_inversion": 1,
  "ok": 16
}
```

Both positive clips are true inversions: one tier2/tier1 inversion and one negative T3 margin. This is important because a previous dual-signal claim was retracted for strict-tie artifacts; this TRIBE target does **not** appear to have that problem.

Artifact: `tie_target_audit_inbench.csv`.

## Finding 11 — simple/category confounds are not enough to explain the in-bench risk queue, but n=18 remains too small

| Feature | AUC high=bad | AUC low=bad |
|---|---:|---:|
| mean_standard_slot_score | 1.000 | 0.000 |
| mean_speech_density | 0.062 | 0.938 |
| duration_s | 0.719 | 0.281 |
| need_entropy | 0.500 | 0.500 |
| category_eq_Food & Cooking | 0.344 | 0.656 |
| category_eq_Pets & Animals | 0.625 | 0.375 |
| category_eq_Sports | 0.625 | 0.375 |
| category_eq_Travel | 0.406 | 0.594 |
| category_sports_or_pets | 0.750 | 0.250 |

Interpretation: `mean_standard_slot_score` remains the clean best feature, while category/duration/speech alternatives do not match it. But because family-wise p is only ~0.092 from round 1, this stays pilot/supporting evidence.

Artifact: `inbench_simple_confound_auc.csv`.

## Finding 12 — low AD-response alignment does not invalidate AV-vs-A triage, but it should quarantine P_AD/NCR claims

External rows split by `alignment_cosine > 0.5` from the TRIBE tensor manifest:

- All rows: n=60, mean-gap AUC vs ADQA fail **0.672**
- High-alignment rows: n=39, AUC **0.650**, fail rate **0.103**
- Low-alignment rows: n=21, AUC **0.600**, fail rate **0.286**

Interpretation: AV-vs-A triage does not depend directly on P_AD alignment, so the triage result can stand. But any AD-dependent TRIBE score, especially NCR/P_AD claims, must quarantine or separately analyze low-alignment clips.

## Round-2 action changes

1. Use `mean_visual_gap`, not `max_visual_gap`, for external review-budget plots unless a later run beats it.
2. Keep “low-gap early exit” as a review-cost claim only.
3. Add length-control sentence to gap-targeted generation claims.
4. Add tie-audit sentence to defend `all4_fail` target labels.
5. Quarantine low `alignment_cosine` clips for future P_AD/NCR experiments.
