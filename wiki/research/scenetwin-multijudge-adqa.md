---
title: "SceneTwin Multi-Judge ADQA + VLM Rater"
category: research
tags: [SceneTwin, ADQA, multi-judge, VLM, TRIBE, audio-description, NJBDA-2026]
created: 2026-05-06
updated: 2026-05-06
sources:
  - output/scenetwin_timing_20clip/adqa_v2/adqa_v2_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa_v3/adqa_v3_tier_scores.csv
  - output/scenetwin_timing_20clip/adqa_v4/adqa_v4_tier_scores.csv
  - output/scenetwin_description_gain/tribe_text_feel_audit.csv
  - output/reports/scenetwin-tribe-text-feel-audit.md
---

# SceneTwin Multi-Judge ADQA + VLM Rater

Extension of the single-pair ADQA ablation. All 4 non-Gemini model pairs are
averaged to produce a fair multi-judge score, removing cherry-picking risk.
A direct VLM rater baseline is added for comparison. TRIBE is re-integrated
as a diagnostic/controller layer, not a quality scorer.

## Scoring Stack — Current Best

| Result | ρ | Pairwise wins | Fully ordered |
|---|---|---|---|
| ADQA all-judge mean (fair primary) | **0.933** | 53/54 | 16/18 |
| ADQA optimized selected-judge | 0.944 | — | — |
| VLM-augmented tuned | 0.965 | 54/54 | 18/18 |
| Direct VLM rater baseline alone | ~0.880 | — | — |
| VLM rater best single dimension | 0.935–0.960 | — | — |

**Poster-safe primary claim:** all-judge mean ρ=0.933, 53/54 pairwise wins,
16/18 fully ordered, permutation p=0. No cherry-picking — all non-Gemini pairs
averaged.

## Bias Checks

| Check | Result | Interpretation |
|---|---|---|
| Length-only baseline | ρ=0.318, 0/18 full order | Word count alone cannot explain ranking |
| Length-residualized all-judge score | ρ=0.874, perm p=0 | Verbosity contributes some signal but does not explain the result |

Verbosity is a partial confounder (pro AD is longer) but the comprehension
signal survives after controlling for length. The result is not just a word-
count proxy.

## TRIBE Text-Feel Audit

TRIBE re-framed as a diagnostic/controller: it identifies **when and what type
of visual content** needs description, not whether the text is correct.

**Method:**
- Video feel = TRIBE ROI gap profile from `P_AV − P_A` projected into 6
  content-type dimensions: `motion_action`, `scene_spatial`, `face_character`,
  `object_body`, `visual_form`, `language_auditory`
- Text feel = generated AD text projected into the same content-type space
- Alignment = cosine between video feel and text feel vectors

**Results (baseline vs TRIBE-guided generation):**

| Metric | Baseline | TRIBE-guided | Delta |
|---|---|---|---|
| Feel alignment | 0.505 | 0.564 | +0.059 |
| Dominant TRIBE type match | 0.000 | 0.619 | **+0.619** |
| Target type hit | 0.381 | 0.714 | **+0.333** |
| Specificity | 0.893 | 0.500 | -0.393 |

**Interpretation:** TRIBE successfully steers generated AD toward the right
type of missing visual/neural content. The large dominant-type-match gain
(+0.619) confirms TRIBE is doing real work as a controller. The specificity
drop (-0.393) is a prompt engineering problem: 4-word window budgets push
the LLM toward generic "vibe matching" text instead of concrete nouns/actions.

## Recommended Next Steps

### Prompt fix (near-term, no GPU)
Revise the TRIBE-guided generation prompt to:
1. Keep the dominant TRIBE content type
2. Require at least one concrete noun/action from visual context
3. Preserve the second missing type when budget allows
4. Ban generic vibe-matching phrases

Then rerun the text-feel audit to see if specificity recovers.

### Neural closure validation (Colab, GPU)
Run TRIBE on `audio + generated AD` and compute:
- `P_AV` = audiovisual video response
- `P_A` = audio-only response
- `P_A+AD` = audio + TRIBE-guided generated AD

If `P_A+AD` moves closer to `P_AV` than `P_A` does, that proves TRIBE-guided
AD actually closes the neural accessibility gap — not just matches a text-feel
profile. This is the strongest possible validation of the TRIBE controller role.

## See Also
- [[research/scenetwin-adqa-clip-ensemble]]
- [[research/scenetwin-stage4-frame-grounded-adqa]]
- [[research/scenetwin-tribe-only-analysis]]
- [[research/scenetwin]]
