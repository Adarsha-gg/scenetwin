---
title: SceneTwin signal decomposition — where CLIP earns its keep (corrected ladder)
category: research
tags: [scenetwin, ablation, paper-section, honesty]
sources: [cursor/output/external_ensemble_eval.csv, output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv]
created: 2026-05-29
updated: 2026-06-27
---

> Corrected three-tier ladder. The **60-clip set is primary**; 18-clip is the pilot. All ρ are
> per-clip min-max-normalized (apples-to-apples ensemble vs single-signal), recomputed from the
> released per-tier CSVs. Superseded: old 4-tier decomposition (CLIP lift +0.14 in-bench / +0.006
> external).

## Headline

ADQA is the scoring backbone; CLIP is cheap insurance that earns its keep on visual-object content.
On the **60-clip primary set CLIP lifts the ensemble +0.005 over ADQA alone** (0.952 vs 0.946).
On the **18-clip pilot CLIP lifts +0.069** (0.957 vs 0.888). The category breakdown shows the
external lift is concentrated on How-to & Instructional (+0.024) and Entertainment (+0.013).

## Per-signal ρ (per-clip normalized)

| Signal | Primary (60, n=180) | Pilot (18, n=54) |
|---|---:|---:|
| **Ensemble (CLIP + ADQA)** | **0.952** | **0.957** |
| ADQA alone | 0.946 | 0.888 |
| CLIP alone | 0.828 | 0.900 |
| **CLIP lift over ADQA-only** | **+0.005** | **+0.069** |

(Pooled-raw single-signal ρ — as reported in the manuscript baseline table — is lower: ADQA
0.869/0.856, CLIP 0.747/0.835. The lift *direction* is unchanged under either definition.)

## Per-category CLIP lift (60-clip primary)

| Category | n_clips | ADQA-only ρ | Ensemble ρ | CLIP lift |
|---|---:|---:|---:|---:|
| How-to & Instructional | 21 | 0.929 | 0.953 | **+0.024** |
| Entertainment | 10 | 0.896 | 0.910 | +0.013 |
| Film & Animation | 2 | 0.985 | 0.985 | 0.000 |
| Food & Cooking | 3 | 0.982 | 0.982 | 0.000 |
| Health & Wellness | 4 | 0.981 | 0.970 | −0.011 |
| Event | 3 | 0.982 | 0.969 | −0.013 |
| Sports | 6 | 0.980 | 0.967 | −0.013 |
| People & Vlogs | 8 | 0.980 | 0.966 | −0.014 |
| Music | 2 | 0.985 | 0.970 | −0.015 |

## Per-clip CLIP contribution (60-clip primary)

| Bucket | Count |
|---|---:|
| CLIP helps ensemble (lift > 0.05) | 8/60 |
| CLIP neutral (\|lift\| ≤ 0.05) | 51/60 |
| CLIP hurts ensemble (lift < −0.05) | 1/60 |

CLIP is neutral on 85% of primary clips and actively hurts only one. Its measurable contribution
is concentrated where object/action grounding is the dominant discriminator (How-to clips).

## What this means for the paper

The contribution is **not** "two independent signals each add lift everywhere." It is:

1. **Frame-grounded ADQA** is the robust backbone (ρ ≈ 0.89–0.95 across both corpora and signal
   definitions).
2. **CLIP grounding** stabilises the ensemble and adds category-specific lift on visual-object
   content (How-to +0.024); it is approximately neutral elsewhere.
3. **Together** they form a parsimonious reference-free metric. CLIP costs almost nothing at
   inference and acts as a sanity-check signal — we do not claim it lifts every clip; it does not.

This is more defensible than claiming uniform dual-signal lift on the primary set.

## See Also

- [[research/scenetwin-external-validation]] — 60-clip primary ρ + per-category
- [[research/scenetwin-external-baselines]] — paper-baseline comparison
- [[research/scenetwin-metric-landscape]] — baseline leaderboard

## Sources

- `cursor/output/external_ensemble_eval.csv` (60-clip per-tier ensemble + components)
- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (18-clip pilot)
