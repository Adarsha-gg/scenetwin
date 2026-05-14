---
title: SceneTwin Technical Methodology
created: 2026-05-11
---

# SceneTwin technical methodology

The implementation details behind the numbers. Datasets, tier
construction, model choices, validation protocol, statistical tests.
Written for someone who wants to know exactly how we got to
ρ = 0.929 and whether they could reproduce it.

---

## 1. Dataset

**Source clips.** 20 short clips (roughly 10 to 20 seconds each) drawn
from the VideoA11y benchmark, which itself is built on top of VATEX.
Categories present in the 20 clip subset: Food and Cooking, Sports, Pets
and Animals, Travel.

**Per-clip artefacts available:**

| Artefact | Source |
|---|---|
| MP4 video | VideoA11y bundle |
| Aligned audio track | extracted with ffmpeg |
| Professional audio description | VideoA11y human writers |
| Short caption | VATEX (about 10 to 15 words) |
| Long caption | VATEX (about 20 to 30 words) |
| Cross-category AD | a different clip's professional AD, used as wrong scene control |

**Coverage on which the headline result is computed:** 18 of the 20
clips produced a complete CLIP row across all four tiers. The two
dropped clips had encoder issues during the original 20 clip run and
are excluded from primary metrics.

---

## 2. Tier construction (the four candidate descriptions per clip)

For every clip we score four candidate descriptions. The tiers are
designed so that any reasonable audit should rank them in this order:

**Tier 3   Professional AD.** Human written audio description from
VideoA11y. Roughly 45 to 75 words. Describes characters, actions, and
environment. This is the highest quality reference behaviour and the
top of the ground truth ranking.

**Tier 2   VATEX long caption.** The longer of the two human captions
in the VATEX annotation for this clip. Roughly 20 to 30 words.
On topic, more specific than the short caption, but written as a
general video caption rather than as accessibility-grade audio
description.

**Tier 1   VATEX short caption.** The shorter VATEX caption. Roughly
10 to 15 words. On topic but very generic, often a single sentence
summary.

**Tier 0   Cross category control.** The professional audio description
from a different clip in a different category. For example, a kitchen
scene receives the AD written for a skiing clip. This is the
hallucination floor: fluent, professionally written, but for the
wrong video. Any audit that cannot distinguish tier 0 from tier 3 is
not doing visual grounding at all.

Ground truth rank for evaluation: tier 0 = 0, tier 1 = 1, tier 2 = 2,
tier 3 = 3.

---

## 3. Models used

| Component | Model | Provider |
|---|---|---|
| Image and text embeddings (Signal 1) | CLIP ViT-L/14 | OpenAI |
| Question generation (Signal 2, vision) | GPT-4o | OpenAI |
| Question grading (Signal 2, text only) | claude-haiku-4-5-20251001 | Anthropic |
| Brain encoder (risk forecast) | TRIBE v2 | Meta FAIR |
| Cortical surface for TRIBE outputs | fsaverage5 (20 484 vertices) | FreeSurfer |
| ROI atlas (for the side analyses, not the headline) | Glasser HCP-MMP1.0 | Glasser et al. 2016 |

All API calls are cached on disk; a full rerun on cached results
takes under one minute. A cold run hitting the OpenAI and Anthropic
endpoints takes about 15 minutes for the full 18 clip benchmark.

---

## 4. Pipeline parameters

**Frame sampling.** Each clip is decoded with OpenCV. Eight evenly
spaced frames are extracted across the clip duration. The same eight
frames are used for both signals.

**Signal 1   CLIP visual grounding.**

```
for each clip:
    for each tier:
        candidate_text = description string
        text_emb  = CLIP_text(candidate_text)
        for each of 8 frames:
            frame_emb = CLIP_image(frame)
            sims.append(cos(frame_emb, text_emb))
        clip_score = mean(sims)
```

Reported column: `clip_mean`. Within-clip min max normalisation is
applied before the ensemble.

**Signal 2   Frame grounded ADQA.**

Step A, question generation. The eight frames are sent in a single
multimodal call to GPT-4o with a fixed instruction: write three
specific yes-or-no comprehension questions whose answer must be
visually evident in the frames. The model does not see any candidate
description while writing questions. Output includes:

- the question text
- the expected answer key
- the required visual evidence
- an importance label (`critical` or otherwise)
- a short rationale (kept for debugging only)

Step B, grading. For each candidate description, the same three
questions are sent to Claude haiku 4.5 in a separate call. The grader
sees only:

- the question text
- the candidate description text

The grader does not see the frames, the answer key, the tier label,
the other candidates, or the ground truth rank. All four candidates
for a clip are anonymised as shuffled IDs A, B, C, D, and the
shuffle order is regenerated per clip to prevent any ordering effect.

The grader returns yes or no per question with a one-line evidence
quote drawn from the candidate description. Signal score = fraction
of yes answers.

Three ablation runs were performed swapping which model wrote
questions and which graded:

| Run | Question model | Grader model | ρ alone |
|---|---|---|---|
| v2 | Claude haiku 4.5 | Claude haiku 4.5 | 0.803 |
| v3 | Claude haiku 4.5 | GPT-4o | 0.726 |
| v4 | GPT-4o | Claude haiku 4.5 | 0.789 |

All three pass the basic sanity check (ρ > 0.7) and the signal is
not specific to one model pairing.

**Ensemble.**

```
for each (clip, tier):
    adqa_norm   = (adqa_score   - clip_min_adqa)   / (clip_max_adqa   - clip_min_adqa)
    clip_norm   = (clip_score   - clip_min_clip)   / (clip_max_clip   - clip_min_clip)
    ensemble    = 0.5 * adqa_norm + 0.5 * clip_norm
```

Within-clip min max normalisation puts both signals on the same scale
before averaging. Weights are fixed at 50 / 50; no weight tuning on
held out data is performed.

---

## 5. Validation protocol

**Primary metric.** Spearman ρ between the ensemble score and the
ground truth tier rank, computed across all 72 (clip, tier) pairs.

**Secondary metrics.**

- Pairwise wins: for each clip there are six within-clip pairwise tier
  comparisons (tier 0 vs 1, 0 vs 2, 0 vs 3, 1 vs 2, 1 vs 3, 2 vs 3).
  Reported as the count of these comparisons where the ensemble
  correctly ranks the higher tier above the lower.
- Fully ordered clips: count of clips where all four candidates are
  ranked in the correct tier order.
- Permutation null: 2000 within-clip permutations of candidate scores.
  Reports the proportion of permutations whose Spearman ρ meets or
  exceeds the observed ρ.
- Bootstrap 95 percent CI: 2000 resamples drawn with replacement at
  the clip level, each preserving the four candidates per clip.

**Bias controls.**

- Length only baseline: rank by candidate word count. Yields ρ = 0.318.
- Length residualised ensemble: residualise word count out of every
  signal score, then recompute the ensemble. Yields ρ = 0.874,
  permutation p ≈ 0.

If length alone explained the result, the length only baseline would
match the ensemble. It does not. The residualised score does not
collapse, which means the comprehension signal is not a word count
proxy.

**Headline numbers.**

| Quantity | Value |
|---|---|
| Spearman ρ, ensemble vs ground truth tier | 0.929 |
| Bootstrap 95 percent CI | [0.904, 0.957] |
| CLIP only ρ                              | 0.801 [0.728, 0.873] |
| ADQA only ρ (v4 cross model run)         | 0.789 [0.700, 0.880] |
| Pairwise wins                            | 54 / 54 |
| Fully ordered clips                      | 15 / 18 |
| Permutation null p                       | p < 0.0005 (0 of 2000) |
| Tier 3 mean score (after normalisation)  | 0.99 |
| Tier 2                                   | 0.71 |
| Tier 1                                   | 0.55 |
| Tier 0                                   | 0.03 |

---

## 6. TRIBE risk forecast (side analysis)

TRIBE v2 is a published transformer that predicts fMRI cortical
activation from naturalistic video and audio. We do not retrain it.
For each clip:

1. **P_AV.** Feed video and audio together. Output: predicted
   activation per fsaverage5 vertex per TR.
2. **P_A.** Feed audio only (silence in the video channel). Same
   output shape.
3. **Accessibility gap.** Pointwise `|P_AV - P_A|` summarises where
   visual input drives activation that audio alone cannot recreate.
4. **Aggregate features.** Several scalar summaries of the gap are
   computed per clip. The one used for the risk forecast is
   `mean_standard_slot_score`: the mean per-window standard
   accessibility need across the clip.

**As a risk score for the audit.** We test whether
`mean_standard_slot_score` ranks ADQA failure clips at the top.
Define failure as a clip where the all-judge mean ADQA score does not
fully order all four tiers. With two such failures in the 18 clip
benchmark:

| Quantity | Value |
|---|---|
| ROC-AUC of risk score vs all4_fail label | 1.00 |
| Recall at top 2 of 18 reviewed (11.1 % budget) | 100 % |
| Uncorrected p | 0.0065 |
| Bonferroni p (10 features compared) | 0.065 |
| Cross-scorer robustness | catches both ADQA-style failures, weaker on CLIP-only failures (3 of 7) |

This is **pilot evidence**, not a confirmatory result. The headline
poster framing is: TRIBE provides a brain grounded risk forecast for
comprehension evaluation failure. From video and audio alone, it
flags clips where the automatic audit may need stronger adjudication.

---

## 7. Reproducibility checklist

- All clip artefacts: `output/scenetwin_description_gain_bundle.zip`
- Scoring tool: `tools/scenetwin_adqa.py` (accepts `--question-model`
  and `--grader-model` flags)
- Ensemble computation: `tools/scenetwin_adqa_clip_ensemble.py`
- Permutation and bootstrap: `tools/scenetwin_ensemble_validation.py`
- TRIBE failure forecast: `tools/scenetwin_tribe_failure_forecast.py`
- Per-clip CSVs: `output/scenetwin_timing_20clip/`
- API calls are cached; cold run cost is approximately 8 USD across
  both providers for one full benchmark.

## 8. Limitations

- n = 18 clips at the headline. CIs are wide enough to detect the
  result; not wide enough to claim generalisation across all domains
  or styles.
- ADQA grading is LLM judged. Cross-model swap shows the result is
  not specific to one model, but all current graders are commercial
  LLMs.
- TRIBE risk forecast uses post hoc feature selection from 10
  candidates. Pre registration of a single feature on a larger clip
  set is the natural next step.
- Tier 0 is constructed as a wrong scene control, not a real failure
  case from a deployed AD pipeline. Real-world hallucinations may
  differ in form.
