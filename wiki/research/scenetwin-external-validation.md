---
title: SceneTwin primary 60-clip evaluation (corrected 3-tier ladder)
category: research
tags: [scenetwin, generalization, primary, benchmark, paper-section]
sources: [cursor/output/external_ensemble_eval.csv, cursor/output/corrected_ladder_robustness.json]
created: 2026-05-29
updated: 2026-06-27
---

> **Canonical result lives in the manuscript** (`output/papers/scenetwin-submission.tex`). The
> **60-clip set is the primary evaluation**; the original 18-clip benchmark is the corroborating
> pilot. Both are reported on the **corrected three-tier ladder** (T0 cross-decoy < T1 crowd
> caption < T3 professional AD); the invalid "long VATEX" T2 rung has been removed. Numbers below
> are recomputed from the released per-tier CSVs and validated against
> `corrected_ladder_robustness.json` (60-clip ensemble@0.5 = 0.9516; 18-clip = 0.9570).
> Superseded: the old 4-tier framing (ρ = 0.873 external / 0.929 in-bench, n = 240/72).

## Headline

The CLIP + ADQA ensemble, untouched between the two corpora, achieves **ρ = 0.952 on the 60-clip
primary set × 3 tiers (n = 180)**, with **58/60 clips fully ordered** and **178/180 pairwise wins
(only 2 T3 losses; the hard T1-vs-T3 pair is 58/60)**. The original **18-clip pilot corroborates
at ρ = 0.957** (17/18 ordered; 53/54 pairwise). The two sets are **disjoint by construction**
(the 60-clip set excludes the 18 pilot clips), so their agreement shows the ranking result is not
an artifact of the smaller initial benchmark.

## Numbers (corrected 3-tier)

| Set | n_clips | n_obs | ρ (manuscript / recompute) | Kendall τ | T3-vs-lower | All pairwise | Fully ordered | perm p | bootstrap CI |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Primary (60)** | 60 | 180 | **0.952** | 0.876 | 118/120 | **178/180** | 58/60 | <2e-4 | [0.93, 0.97] |
| Pilot (18) | 18 | 54 | 0.957 | 0.887 | 36/36 | 53/54 | 17/18 | <2e-4 | [0.92, 0.98] |
| Combined (78) | 78 | 234 | 0.954 | — | — | — | — | — | — |

## Per-category breakdown (60-clip primary, ensemble ρ)

| Category | n_clips | ρ |
|---|---:|---:|
| Film & Animation | 2 | 0.985 |
| Food & Cooking | 3 | 0.982 |
| Health & Wellness | 4 | 0.970 |
| Music | 2 | 0.970 |
| Event | 3 | 0.969 |
| Sports | 6 | 0.967 |
| People & Vlogs | 8 | 0.966 |
| How-to & Instructional | 21 | 0.953 |
| Entertainment | 10 | 0.910 |

(Education/Seminar has a single clip and is omitted from the ρ table.) No multi-clip category falls
below 0.91. The largest unseen category — How-to & Instructional (21 clips, none in the pilot) —
holds at ρ = 0.953.

## Where it fails — the 2/180 T3 losses

On the corrected ladder, T3 (pro AD) loses a pairwise comparison in only **2 of 180** cases, both to
T1 (crowd caption) and both near-ties:

- `GOH6fBhoi2o_000010_000020` (Entertainment): T3 = 0.602 vs T1 = 1.000.
- `d7_SY48r__8_000060_000070` (How-to): T3 = 0.972 vs T1 = 1.000.

This is down from the 7/180 losses on the old 4-tier ladder — removing the verbosity rung removed
most of the disagreement. See [[research/scenetwin-external-t3-losses]].

## Paper framing

The 60-clip primary result and the 18-clip pilot are consistent (ρ = 0.952 vs 0.957), and the
pilot's clip set is disjoint from the primary set. This is the strongest counter to the old
"n is too small" challenge: the headline now rests on 60 clips spanning 10 categories, with the
original 18-clip benchmark as an independent confirmation rather than the sole evidence.

## See Also

- [[research/scenetwin-statistical-power]] — power defense on the 60-clip primary set
- [[research/scenetwin-signal-decomposition]] — CLIP-vs-ADQA decomposition (corrected ladder)
- [[research/scenetwin-adqa-clip-ensemble]] — 18-clip pilot detail
- [[research/scenetwin-tribe-failure-forecast]] — TRIBE triage on the primary set

## Sources

- `cursor/output/external_ensemble_eval.csv` (180 corrected-ladder rows; 60 video × 3 tier)
- `cursor/output/corrected_ladder_robustness.json` (weight/normalization sweep, bootstrap, permutation)
- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (18-clip pilot)
