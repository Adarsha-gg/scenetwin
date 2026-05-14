---
title: "SceneTwin Working Stack — Timing Layer Survives, Typing Layer Killed"
category: research
tags: [SceneTwin, TRIBE, audio-description, BLV, grounding, OCR]
created: 2026-05-02
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/neural_description_need_curve.csv
  - output/scenetwin_description_gain/neural_event_test_results.csv
  - output/scenetwin_description_gain/need_weighted_grounding_summary.csv
  - output/scenetwin_description_gain/ocr_coverage_test_summary.csv
  - output/scenetwin_description_gain/coarse_need_windows.csv
  - output/scenetwin_description_gain/hrf_lag_sensitivity_summary.csv
  - output/scenetwin_description_gain/metric_null_baselines.csv
  - output/scenetwin_description_gain/trajectory_metrics_summary.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
  - output/scenetwin_description_gain/roi_gap_analysis.csv
  - output/scenetwin_description_gain/roi_content_typing_windows.csv
  - output/scenetwin_description_gain/roi_content_typing_descriptions.csv
  - output/scenetwin_timing_20clip/aggregate_results.csv
  - output/scenetwin_timing_20clip/aggregate_nulls.csv
  - output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv
  - output/scenetwin_timing_20clip/need/coarse_need_windows.csv
  - output/scenetwin_timing_20clip/adqa/adqa_aggregate_results.csv
  - output/scenetwin_timing_20clip/adqa/adqa_tier_scores.csv
  - https://huggingface.co/papers/2507.22229
  - https://huggingface.co/facebook/tribev2
  - https://aclanthology.org/2025.emnlp-main.1199/
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12398407/
  - https://pubmed.ncbi.nlm.nih.gov/40918301/
  - https://huggingface.co/papers/2104.08718
  - https://www.sciencedirect.com/science/article/pii/S1053811921003621
  - https://repository.hkust.edu.hk/ir/Record/1783.1-146950
---

# SceneTwin Working Stack — Timing Layer Survives, Typing Layer Killed

## Honest Verdict

After ~10 days of falsification, the SceneTwin architecture is settled:

- **TRIBE** is the timing layer. It picks AD-need windows via the
  audio-vs-audiovisual cortical gap. On the 20-clip scale-up it produced
  need curves across all 20 clips and 126 coarse windows.
- **CLIP** (or PAC-S / SigLIP) is the content layer inside those windows.
  On 18 complete clips, CLIP-L14 window grounding ranks description tiers
  robustly: Spearman ρ≈0.73, permutation-null p<0.0005.
- **OCR** is a supplementary layer for clips with on-screen text.
- **LLM-ADQA** is the functional comprehension layer. It asks whether the
  description lets a listener answer key visual/narrative questions.
- **ROI content typing**, **counterfactual neural fidelity scoring**, and
  **closed-loop TRIBE-in-loop AD generation** were tested and falsified.
  Documented in the "What Has Been Tested and Killed" section below.

Important update from the 20-clip run: TRIBE need-weighting does **not** show
a large aggregate ranking lift over plain CLIP on this dataset. Need-weighted
CLIP has ρ=0.7328; plain window-mean CLIP has ρ=0.7251; top-3-window CLIP has
ρ=0.7346. TRIBE remains the accessibility-motivated timing/windowing layer,
not a proven aggregate CLIP booster.

The useful direction is:

```text
TRIBE decides when audio is missing important visual brain-state signal.
Grounding/OCR/ADQA metrics decide whether the description covers that visual content.
```

That is a better scientific claim and a better engineering design.

## What Worked

### 1. TRIBE AccessibilityGap

```text
AccessibilityGap(t) = distance(P_AV[t], P_A[t])
```

Purpose: decide when a BLV viewer needs visual information beyond the soundtrack.

Observed on 2 clips:

- clip 00: high-need low-speech windows line up with chef/tomato/knife action.
- clip 01: high-need high-speech windows correctly become extended/integrated AD candidates.

This is the strongest TRIBE-only signal so far.

### 2. TRIBE VisualOnlyEvent

```text
VisualOnlyEvent(t) = max(AVShift(t) - AudioShift(t), 0)
```

Purpose: catch neural state changes that appear in audiovisual input but not in audio-only input.

Observed on 2 clips:

- useful as a secondary trigger;
- noisy as a main metric;
- caught the Burger King/title-card transition that the need curve underweighted.

Verdict: keep it as an inspection trigger, not the headline score.

### 3. Need-Weighted Grounding

```text
NeedWeightedGrounding(d) = sum_t CLIP(frame_t, d) * ADNeed(t)
```

Purpose: score whether a description matches the frames where TRIBE says AD matters.

On the 2 saved clips:

| Metric | Spearman | Pairwise tier3 wins | Full-order clips |
|---|---:|---:|---:|
| need_weighted_clip | 0.9759 | 6/6 | 2/2 |
| critical_weighted_clip | 0.9759 | 6/6 | 2/2 |
| clip_top3 | 0.8783 | 6/6 | 1/2 |

This is the first version where TRIBE adds a clean role instead of fighting the grounding metric.

20-clip scale-up on 2026-05-03:

| Metric | Spearman | Kendall | Pairwise tier3 wins | Full-order clips | Null p |
|---|---:|---:|---:|---:|---:|
| need_weighted_clip | 0.7328 | 0.5877 | 48/54 | 11/18 | <0.0005 |
| critical_weighted_clip | 0.7274 | 0.5841 | 48/54 | 11/18 | <0.0005 |
| clip_mean | 0.7251 | 0.5805 | 48/54 | 11/18 | <0.0005 |
| clip_top3 | 0.7346 | 0.5877 | 48/54 | 10/18 | <0.0005 |

Verdict after scaling: visual grounding is robust, but need-weighting is not
clearly better than plain CLIP aggregation. Keep TRIBE for window selection and
accessibility framing; do not claim a large score lift unless a future
window-level or human-validation analysis proves it.

### 4. OCR Coverage

Purpose: catch visible text on screen, a known AD requirement that image-text cosine can blur.

On clip 01, OCR detected:

```text
BURGERS EATING
```

Weighted OCR score:

| Tier | Score |
|---|---:|
| tier3_va11y | 1.0 |
| tier2_vatex_long | 0.4 |
| tier1_vatex_short | 0.4 |
| tier0_cross | 0.0 |

Summary on OCR-positive windows:

| Metric | Spearman | Pairwise tier3 wins |
|---|---:|---:|
| weighted_ocr_score | 0.9487 | 3/3 |
| weighted_phrase_coverage | 0.7746 | 3/3 |

Verdict: OCR is not universal, but it fills a real gap: readable text must be quoted or explicitly covered.

20-clip scale-up: OCR-positive windows appeared in only 2 clips / 8 rows.
The OCR aggregate did not beat the permutation null (`rho=0.225`, p=0.357).
Keep OCR as a targeted visible-text layer, not as a global headline metric.

### 5. LLM-ADQA Functional Comprehension

Purpose: test whether AD text lets a listener answer concrete visual/narrative
questions, instead of only asking whether text and frames are similar.

Stage 4 v1 on 2026-05-03 used professional VideoA11y AD as the question source
and answer key. It ranked tiers strongly (`rho=0.9417`) but was circular at the
top tier because tier3 was also the reference.

Stage 4 frame-grounded rerun on 2026-05-03:

- Input: 18 complete 20-clip timing-stack clips.
- Question source: 8 sampled frames per clip via Claude vision.
- Grading: anonymized A/B/C/D candidate descriptions, shuffled per clip.
- Model: `claude-haiku-4-5-20251001`.
- Output: 90 questions, 360 candidate-question grades.

| Metric | Spearman | Kendall | Pairwise tier3 wins | Full-order clips | Null p |
|---|---:|---:|---:|---:|---:|
| adqa_v2_score, unfiltered | 0.8029 | 0.6959 | 51/54 | 8/18 | <0.0005 |
| adqa_v2_score, floor-zero filtered | 0.8038 | 0.7127 | 51/54 | 8/18 | <0.0005 |

Mean unfiltered frame-grounded ADQA score by tier:

| Tier | Score |
|---|---:|
| tier3_va11y | 0.650 |
| tier2_vatex_long | 0.422 |
| tier1_vatex_short | 0.244 |
| tier0_cross | 0.039 |

Verdict: this makes the system pitch stronger. SceneTwin is not just
"TRIBE plus CLIP"; it is a four-stage AD audit pipeline: TRIBE timing,
CLIP grounding, OCR coverage, and LLM-ADQA comprehension. Caveat: the same
model still generates questions and grades answers, and the frame sample can
miss off-frame actions. It still needs BLV user validation or independent
visual QA labels.

### 5b. CLIP + ADQA Ensemble

Implemented on 2026-05-04:

- Inputs: the 18 complete clips with both CLIP grounding and corrected
  frame-grounded ADQA scores.
- Fusion: normalize each score within clip, then average ADQA with each CLIP
  variant. This evaluates per-clip tier ranking, not absolute cross-video
  quality.
- Best single normalized baseline: `adqa_norm_clip`, rho=0.854.
- Best simple ensemble: equal-weight `ADQA + clip_mean`, rho=0.929.

| Metric | Spearman | Kendall | Pairwise tier3 wins | Full-order clips | Null p |
|---|---:|---:|---:|---:|---:|
| adqa_norm_clip | 0.854 | 0.788 | 51/54 | 8/18 | <0.0005 |
| clip_mean_norm_clip | 0.799 | 0.689 | 48/54 | 11/18 | <0.0005 |
| ensemble_mean_clip_mean | 0.929 | 0.836 | 54/54 | 15/18 | <0.0005 |

Verdict: this is the cleanest system-level scoring result. Do not frame it as
"ADQA barely beats CLIP." Frame it as complementary evidence: CLIP measures
video-text grounding, ADQA measures listener answerability, and their simple
ensemble ranks tiers better than either signal alone. Caveat: the weights are
not learned on a held-out set, and ADQA still needs BLV validation.

### 6. Temporal Sanity Upgrades

Implemented on 2026-05-03:

- Coarse 3s need windows: use these for reports instead of raw sub-second-looking TR rows.
- HRF lag sensitivity: `0.0s` frame alignment beats `2.5s` and `5.0s` on the current 2 clips.
- Exact permutation nulls: need-weighted grounding has Spearman null p=0.0017 on the 2-clip exact within-clip shuffle.
- Trajectory metrics: DTW/resampled TRIBE trajectory metrics are weaker than need-weighted grounding, so keep them diagnostic.
- ROI gap curve: script exists, but ROI scoring is blocked until we have a real fsaverage5 ROI mask/atlas.

### 7. Destrieux ROI Proxy Smoke Test

Implemented on 2026-05-03:

- Built a real fsaverage5 ROI mask from Nilearn's Destrieux surface atlas.
- Ran ROI-restricted gap curves with visual proxy ROIs plus language/auditory controls.
- Result: clip 00 visual/scene proxies sharpen the silent tomato/knife action windows, but clip 01 also shows strong control-region spikes around title-card/speech-heavy moments.

Verdict: ROI pipeline is unblocked, but Destrieux anatomical proxies are not clean enough to become the headline. Replace with a functional Glasser/Wang/localizer mask before making strong brain-region claims.

### 8. ROI Content Typing — Tested and Killed (2026-05-03)

Tried and falsified. Kept here as documentation of the dead branch so future
work does not retry it without the upstream fixes called out below.

The pitch: convert TRIBE per-ROI gap into a content-type distribution
(motion/scene/face/object/visual-form/language) and use the dominant type as
a prescription for what the AD slot should describe.

What was tested:

1. **Destrieux anatomical proxies.** Pro-AD agreement (lexicon classifier):
   4.8% on 21 windows, below 16.7% chance.
2. **Glasser HCP-MMP1.0 functional parcellation** resampled to fsaverage5.
   Pro-AD agreement (lexicon): 19.0%, marginal. High-need windows: 14.3%,
   below chance.
3. **Glasser + Claude-haiku-4-5 pro-AD classifier** (decisive). Pro-AD
   agreement: 4.8%. High-need: 0.0%. Claude classified 18/21 pro-AD windows
   as motion_action; TRIBE typed those windows as face_character or
   scene_spatial. The lexicon was hiding how broken the typing was.

Confusion: TRIBE per-ROI AV-A gap on Glasser ROIs does not track what
professional AD writers actually describe. Atlas resolution helped but did
not fix it. The signal is not present at this granularity for short clips.

Verdict: drop ROI content typing from the headline and from the closed-loop
plan. SceneTwin is a TRIBE-as-window-selector + CLIP/OCR-as-content-scorer
pipeline. Do not run a closed-loop AD generator conditioned on the typing
output.

Future-work conditions for re-attempt:

- Per-sentence-timestamped pro AD on >100 windows
- Longer clips (≥30s) where event/content structure stabilizes
- Possibly subject-specific TRIBE rather than the average-subject head
- Possibly a different counterfactual than AV-A residual

## Research Grounding

- TRIBE is valuable because it predicts whole-brain time series across video, audio, and text, and its multimodal advantage is strongest in high-level associative cortex. That supports using it for audio-vs-audiovisual gap, not as a literal text grader.
- ADQA argues that AD evaluation should test whether a viewer can answer visual/narrative questions over coherent segments, not just match a single reference sentence. SceneTwin should eventually validate against ADQA-style questions.
- VideoA11y and Describe Now both support user-centered AD: descriptions vary by context, timing, and desired detail. This matches the need-curve framing.
- CLIPScore, PAC-S, SigLIP, and G-VEval are better suited to content grounding than TRIBE alone. SceneTwin should use them downstream of TRIBE timing.
- Neural event segmentation literature supports looking for state transitions in time-varying brain activity; our VisualOnlyEvent metric is a small operational version of that idea.

## Current Product Shape

```text
1. Run TRIBE on original video: P_AV
2. Run TRIBE on original audio: P_A
3. Compute AccessibilityGap(t)
4. Compute VisualOnlyEvent(t)
5. Pick AD-required windows:
   - high gap + low speech: standard AD slot
   - high gap + high speech: extended/integrated AD
   - visual event spike: inspect even if gap is moderate
6. Score/generate descriptions only inside those windows:
   - need-weighted CLIP/SigLIP/PAC-S for visual grounding
   - OCR coverage for visible text
   - LLM-ADQA questions for functional comprehension
```

## What Still Has To Be Proven

- Replace CLIP with PAC-S or SigLIP and compare directly.
- Validate against BLV user labels or independent visual QA annotations. The
  current frame-grounded LLM-ADQA layer is a stronger engineering proxy, but
  still model-generated and model-graded.

## What Has Been Tested and Killed

Documented dead branches so future work does not relitigate them:

- Whole-cortex cosine `cos(P_AV, P_D)` — fails the hallucination control.
- Plain `Description Gain = cos(P_AV, P_D) - cos(P_AV, P_A)` — Spearman 0.05
  on the 2-clip smoke test; cross-category descriptions beat real AD.
- `MVRR`, `ARP`, `UsefulScore` (residual recovery family) — same failure
  mode as DG on the smoke test.
- TRIBE trajectory metrics (per-TR cosine, DTW, shift-curve correlation) —
  near-zero Spearman, fails the permutation null.
- HRF-shifted frame matching (2.5s, 5s) — `0s` wins, do not shift.
- Per-ROI content typing on Destrieux proxies — 4.8% pro-AD agreement.
- Per-ROI content typing on Glasser HCP-MMP1.0 (lexicon validator) — 19%,
  marginal; (Claude validator) — 4.8%, decisively below chance.
- Closed-loop TRIBE-in-loop AD generation — blocked by typing failure;
  would amplify a circular metric.

## Bottom Line

The defensible claim, tested and surviving:

> SceneTwin uses a brain-encoding model (TRIBE v2) to identify *when* AD is
> needed by computing the cortical-response gap between audiovisual and
> audio-only stimulus. CLIP grounding, OCR coverage, and LLM-ADQA score AD
> content inside those windows. On the 20-clip scale-up, CLIP grounding reaches
> Spearman ρ≈0.73 with permutation-null p<0.0005, blind frame-grounded
> LLM-ADQA reaches Spearman ρ≈0.80, and a simple clip-normalized CLIP+ADQA
> ensemble reaches Spearman ρ≈0.93 with permutation-null p<0.0005. TRIBE
> need-weighting provides the accessibility-motivated windowing layer, but it
> does not substantially outperform plain CLIP aggregation on this dataset.

The role of TRIBE is **window selection**, not content scoring. That is
narrower than the original pitch but it survives every honest test the
project has run, and no other tool computes the audio-vs-audiovisual cortical
counterfactual that defines AD-need timing. TRIBE is the differentiator at
the timing/prioritization layer; CLIP/OCR/LLM-ADQA are the workhorses at the
content and comprehension layers.
