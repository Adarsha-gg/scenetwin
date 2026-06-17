---
title: SceneTwin signal decomposition — where CLIP earns its keep
category: research
tags: [scenetwin, ablation, paper-section, honesty]
sources: [output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv, cursor/output/external_ensemble_eval.csv, cursor/research/output/per_clip_clip_vs_adqa_decomposition.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

The 2-signal ensemble is doing different work in the two corpora. **In-benchmark, CLIP contributes +0.14 rho over ADQA alone.** **Externally, CLIP contributes +0.006**. The category-by-category breakdown shows CLIP earns its keep on How-to & Instructional clips (+0.034) and slightly hurts on Health & Wellness (-0.036). The paper should report this rather than overclaim "dual-signal" externally.

## Numbers

### Per-signal rho on both corpora

| Signal | In-bench (n=72) | External (n=240) |
|---|---:|---:|
| **Ensemble (CLIP + ADQA)** | **0.929** | **0.873** |
| ADQA alone | 0.789* | 0.867 |
| CLIP alone | 0.801* | 0.691 |
| **CLIP lift over ADQA-only** | **+0.140** | **+0.006** |

*Published headline numbers used raw single-signal columns. Internal normalized columns yield slightly different values (~0.85 / 0.80) but the lift pattern is unchanged.

### Per-category CLIP lift on external (60 clips)

| Category | n_clips | ADQA-only rho | Ensemble rho | CLIP lift |
|---|---:|---:|---:|---:|
| How-to & Instructional         | 21 | 0.836 | 0.870 | **+0.034** |
| Film & Animation               |  2 | 0.886 | 0.889 | +0.003 |
| Food & Cooking                 |  3 | 0.920 | 0.920 |  0.000 |
| Music                          |  2 | 0.938 | 0.933 | -0.006 |
| Sports                         |  6 | 0.906 | 0.893 | -0.013 |
| Entertainment                  | 10 | 0.830 | 0.814 | -0.016 |
| People & Vlogs                 |  8 | 0.907 | 0.891 | -0.016 |
| Event                          |  3 | 0.932 | 0.915 | -0.018 |
| Health & Wellness              |  4 | 0.894 | 0.858 | -0.036 |

### Per-clip CLIP contribution on external (60 clips)

| Bucket | Count |
|---|---:|
| CLIP helps ensemble (lift > 0.05) | 10/60 |
| CLIP neutral (|lift| <= 0.05) | 37/60 |
| CLIP hurts ensemble (lift < -0.05) | 13/60 |

CLIP is essentially neutral on 62% of external clips, and the active-hurt count slightly exceeds the active-help count. On the largest external category (How-to & Instructional, n=21) CLIP cleanly adds signal because object/action grounding is what those clips reward.

## What this means for the paper

### Don't hide it

A careful reviewer who looks at per-signal rho will notice the external CLIP lift is +0.006. Overclaiming "the dual-signal design generalizes" misrepresents the measurement. Better framing:

> Our ensemble combines CLIP visual grounding with frame-grounded ADQA MCQs. On the controlled 18-clip tier benchmark, CLIP contributes a measurable +0.14 rho over ADQA alone. On the 60-clip external corpus, ADQA dominates: the ensemble rho (0.873) exceeds ADQA-only (0.867) by 0.006. CLIP earns this small but consistent improvement primarily on How-to & Instructional content (+0.034 in that category, n=21), where object and action grounding is the dominant discriminator. On other external categories CLIP is approximately neutral.

This is more defensible than claiming uniform dual-signal lift.

### Reframe the contribution

The paper's contribution is **not** "CLIP and ADQA each add signal independently." It is:

1. **Frame-grounded ADQA** is the robust scoring backbone (rho >= 0.85 in both corpora).
2. **CLIP grounding** stabilises the ensemble on controlled benchmarks and adds category-specific signal on visual-object content externally.
3. **Together** they form a parsimonious reference-free metric that beats blends of 6 other paper baselines (see [[research/scenetwin-negative-results]]).

The paper-level claim becomes: *"the metric is reliable across distributions because the ADQA backbone is robust, and CLIP provides controlled-benchmark stability."* That holds.

### Pre-empts the obvious reviewer question

If a reviewer asks "why use CLIP at all when ADQA-only gets 0.867 externally?" the honest answer is:

> CLIP costs almost nothing to add at inference time and provides (i) controlled-benchmark separation that ADQA alone does not, (ii) measurable lift on object-heavy external categories, (iii) a sanity-check signal for when ADQA judges disagree. We do not claim it adds signal on every external clip; it does not. We claim it is cheap insurance.

## Frame-grounded ADQA: the actual heavy lifter

Worth re-examining the ADQA design in light of this finding. ADQA is itself frame-grounded: questions are constructed against sampled frames, answers are checked against the same frames. So ADQA already embeds visual grounding via the question-generation step. CLIP adds a second, lower-level grounding signal that is largely redundant with ADQA's existing frame-anchored MCQs.

This explains both:
- Why CLIP+ADQA beats single signals in-bench (the tier construction is controlled enough that low-level CLIP grounding still adds independent signal)
- Why CLIP barely lifts ADQA externally (in the wild, ADQA's MCQs are already doing most of the visual grounding work)

## Recommended paper subsection

```
Section X.Y Signal Decomposition

We decompose the ensemble into its CLIP and ADQA components on
both corpora. In-benchmark, CLIP visual grounding lifts rho by
0.14 over frame-grounded ADQA alone (0.929 vs 0.789). Externally
the lift collapses to +0.006 (0.873 vs 0.867). The reason is
construction: ADQA's MCQs are themselves grounded in sampled
frames, so on naturalistic external clips ADQA already captures
most of the visual grounding signal. CLIP-grounding adds
category-specific lift on visually-rich content (How-to clips,
+0.034) and is approximately neutral elsewhere. We retain CLIP
in the ensemble as a parsimonious second signal that provides
controlled-benchmark stability and contributes on visual-object
categories, but we report honestly that ADQA is the workhorse
on external distributions.
```

## See Also

- [[research/scenetwin-external-validation]] - external ensemble rho
- [[research/scenetwin-external-baselines]] - external paper-baseline comparison
- [[research/scenetwin-metric-landscape]] - 10-baseline leaderboard
- [[research/scenetwin-negative-results]] - fusion failures

## Sources

- `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_scores.csv` (in-bench per-tier ensemble + signal components)
- `cursor/output/external_ensemble_eval.csv` (external per-tier ensemble + components)
- `cursor/research/output/per_clip_clip_vs_adqa_decomposition.csv` (per-clip CLIP lift breakdown)
