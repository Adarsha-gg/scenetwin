---
title: SceneTwin NJBDA Poster — Copy Deck
created: 2026-05-11
canvas: 36in W × 48in H portrait
---

# SceneTwin NJBDA Poster — Copy Deck

Format-agnostic prose, headings, and stats for every poster section.
Drop into Marp / HTML / PPT as-is. Lengths chosen to read comfortably at 36×48.

---

## Header / Title

**Title (one line, large):**
> SceneTwin: A Reference-Free Audit for Audio Description Quality

**Sub-title (one line, smaller, italic):**
> Two complementary signals — visual grounding and frame-grounded comprehension — score whether AD preserves the visual content blind and low-vision viewers can't access.

**Byline:**
> Adarsha Subedi · West Liberty University · adarsha.zz.work@gmail.com
> NJBDA 13th Annual Symposium, Rowan University · May 20 2026

---

## Band 2A — Problem  (~120 words)

**Heading:** *Audio description is uneven, and nobody can scale a quality check.*

Audio description (AD) is the spoken narration that lets blind and low-vision
viewers follow visual content — characters, actions, scenes that the audio
track alone never carries. Professional AD is expensive and slow to produce;
AI-generated AD is cheap but inconsistent. Reference-based metrics like
BLEU and ROUGE don't apply because there is no single "correct" description
for a given clip — two skilled describers will write very different but
equally valid scripts.

The field needs an automated audit that runs on any clip and any candidate
description, with no reference text required, and that catches both the
common failure modes: *hallucinated content* (describing a different scene)
and *vague content* (technically correct but uninformative).

---

## Band 2B — Approach  (~110 words)

**Heading:** *Two reference-free signals, ensembled.*

SceneTwin combines two signals that nothing else does well alone.

**CLIP-L14 visual grounding** computes the cosine similarity between each
sampled video frame and the candidate AD text. It catches the
*hallucinated* failure mode — AD that describes the wrong scene scores low.

**Frame-grounded ADQA** uses a vision-language model to generate
comprehension questions from the frames (no reference AD), then asks a
separate LLM to grade each candidate description blind. It catches the
*vague* failure mode — generic AD answers fewer questions.

Per-clip CLIP↔ADQA correlation is ρ=0.76 — they agree on direction
but capture different errors. Equal-weight ensemble combines them.

---

## Band 3 — Headline result  (callouts)

**Giant callout (top of band):**
> **ρ = 0.929**   [95% CI 0.90 – 0.96]
>
> 54/54 pairwise tier wins · 15/18 fully ordered · permutation p < 0.0005
>
> *18 clips × 4 quality tiers, bootstrap N = 2000*

**One-line interpretation under the figure:**
> Professional AD ranks above VATEX long, which ranks above VATEX short,
> which ranks above cross-category descriptions, on nearly every clip.

**Multi-judge robustness mini-table** *(small, beside strip plot):*

| Variant | ρ | wins | full order |
|---|---|---|---|
| All-judge fair mean | 0.933 | 53/54 | 16/18 |
| Selected-judge optimized | 0.944 | — | — |
| VLM-augmented (upper bound) | 0.965 | 54/54 | 18/18 |

---

## Band 4A — Bias check  (~80 words)

**Heading:** *The signal is not just word count.*

A length-only baseline — ranking AD by raw word count — gets ρ = 0.318
and zero fully-ordered clips. Verbosity correlates with quality but cannot
explain the ranking on its own. After residualizing word count from the
ensemble score, the result drops to ρ = 0.874 with permutation p ≈ 0.
The comprehension signal survives.

---

## Band 4B — Cross-model validation  (~70 words + table)

**Heading:** *The result is model-agnostic.*

We swapped the LLM used to generate ADQA questions and the LLM used
to grade them, holding everything else fixed.

| Question model → Grader | ρ | wins |
|---|---|---|
| Claude → Claude | 0.803 | 51/54 |
| Claude → GPT-4o | 0.726 | 47/54 |
| GPT-4o → Claude | 0.789 | 50/54 |

No combination falls below ρ = 0.7. Signal is not an artifact of one model.

---

## Band 5 — TRIBE failure forecast  (secondary finding, ~120 words)

**Heading:** *Brain-grounded risk forecast — flags fragile evaluations before scoring AD.*

TRIBE is a published fMRI encoder that predicts visual cortex activity from
video and audio. We compute its **accessibility gap** — P_AV − P_A, the
predicted brain response that audio alone fails to recreate. This is *where
AD is needed* (see brain image).

We then ask: does the magnitude of that gap predict where automatic AD
*scoring* itself struggles? Yes. Using `mean_standard_slot_score` from the
TRIBE gap, the two clips where the all-judge ADQA ensemble fails to order
the tiers correctly land in the **top 2 / 18 risk ranks**.

- Recall @ 11.1 % review budget: **100 %**
- ROC-AUC: **1.00**   ·   uncorrected p = 0.0065
- After Bonferroni (10 features tried): p = 0.065 — pilot evidence, not confirmation

*This means SceneTwin could flag a small queue of clips for human review,
catching its own fragile cases from brain-grounded video features alone,
before any AD text is scored.*

---

## Band 6 — What did not work  (failed branches panel)

**Heading:** *What did not work.*

Branches we explored, measured, and discarded before settling on the
surviving pipeline. Each one looked plausible on paper.

- **Description Gain / MVRR** — counterfactual neural metric. Unstable on
  2-clip smoke test, no visual grounding.
- **ROI content typing** — match TRIBE per-ROI gap to AD content type.
  Glasser atlas: 19.0 % agreement with professional AD vs 16.7 % chance.
  Killed by LLM pro-AD verification.
- **Neural closure** (P_A + AD → P_AV) — all values negative on 2 clips.
  Shorter AD wins; verbosity inflates language ROIs. Tested with five
  different distance metrics, none restored monotonicity.
- **TRIBE-weighted ADQA** — up-weight ADQA questions on high-gap windows.
  Null result. Δρ < 0.002 versus uniform weighting.

*Honest takeaway: the surviving pipeline is the reference-free scoring
ensemble. Counterfactual neural metrics, including any "AD restores the
neural gap" framing, did not generalize at the scale we tested.*

---

## Footer

**Code & data:**
> github.com/Adarsha-gg/scenetwin   (release tag: njbda-2026)

**Acknowledgements:**
> TRIBE v2 (Meta FAIR · Banville et al.) · VideoA11y dataset (Microsoft) ·
> VATEX (Wang et al.) · OpenAI CLIP · Anthropic Claude · OpenAI GPT-4o

**QR code:** link to wiki / poster PDF / repo.

---

## Visual asset inventory  (drop-in PNG paths)

| Slot | File | Notes |
|---|---|---|
| Methodology diagram (top of poster) | `output/charts/scenetwin_methodology.png` | 17×8.4 in, 6-step visual pipeline with TRIBE risk-forecast lane |
| Per-tier strip plot (Band 3) | `output/charts/scenetwin_per_tier_strip.png` | 11×5.2 in |
| Bootstrap CI bars (Band 3 inset) | `output/charts/scenetwin_bootstrap_ci.png` | 7.2×4.8 in |
| Length-bias bars (Band 4A) | `output/charts/scenetwin_length_bias.png` | 7.2×4.5 in |
| TRIBE failure forecast (Band 5) | `output/charts/scenetwin_failure_forecast.png` | 11×4.8 in (ROC + risk bars) |
| Accessibility-gap brain — annotated (Band 5 anchor) | `output/charts/scenetwin_accessibility_gap_brain_annotated.png` | 11.5×9 in, 4-view + region labels |
| Accessibility-gap brain — plain (backup) | `output/charts/scenetwin_accessibility_gap_brain.png` | 11×8.5 in, 4-view cortex, no labels |
| Brain pedagogy strip (optional Band 5 inset) | `output/charts/scenetwin_brain_three_panel.png` | 14.5×5.5 in, P_AV − P_A = gap |
| Failed branches (Band 6) | `output/charts/scenetwin_killed_branches.png` | 13×5.3 in, 4-card row |

## Numbers cited — single source of truth

| Claim | Value | Source |
|---|---|---|
| Ensemble Spearman ρ | 0.929 | `output/scenetwin_timing_20clip/ensemble/adqa_clip_ensemble_results.csv` |
| Ensemble 95% CI | [0.904, 0.957] | `output/reports/scenetwin_ensemble_validation.md` |
| CLIP-only ρ + CI | 0.801 [0.728, 0.873] | same |
| Pairwise wins | 54/54 | same |
| Fully ordered clips | 15/18 | same |
| Length-only ρ | 0.318 | wiki/research/scenetwin-multijudge-adqa.md |
| Length-residualized ρ | 0.874 | same |
| Per-clip CLIP↔ADQA | ρ = 0.76 | `output/reports/scenetwin_ensemble_validation.md` |
| Cross-model robustness | 0.803 / 0.726 / 0.789 | `output/scenetwin_timing_20clip/adqa_v4/adqa_v4_comparison.md` |
| All-judge fair ρ | 0.933 | wiki/research/scenetwin-multijudge-adqa.md |
| VLM-augmented upper bound ρ | 0.965 | same |
| TRIBE failure recall @ 2/18 | 100 % | `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv` |
| TRIBE ROC-AUC | 1.000 | same |
| TRIBE uncorrected p | 0.0065 | same |
| TRIBE Bonferroni p | 0.065 | same |
