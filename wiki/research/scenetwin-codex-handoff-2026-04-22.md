---
title: "SceneTwin Codex Handoff — 2026-04-22"
category: research
tags: [SceneTwin, TRIBE-v2, codex-handoff, ROI, temporal-alignment, accessibility]
created: 2026-04-22
updated: 2026-04-22
sources:
  - wiki/research/scenetwin.md
  - wiki/research/scene twin codex.md
  - wiki/research/scenetwin-accuracy-plan.md
  - output/scenetwin_desc_preds_colab.ipynb
  - /Users/adarsha/Downloads/video_preds.npy
  - output/scenetwin_preds/desc_accurate_concise_preds.npy
  - output/scenetwin_preds/desc_accurate_detailed_preds.npy
  - output/scenetwin_preds/desc_bad_vague_preds.npy
  - output/scenetwin_preds/desc_hallucinated_preds.npy
  - https://www.nature.com/articles/s41597-025-06077-3
  - https://arxiv.org/abs/2411.11835
  - https://media.rnib.org.uk/documents/AI-Generated_Audio_Description_Report_August_2025.pdf
  - https://arxiv.org/abs/2011.11071
  - https://arxiv.org/abs/2208.11144
---

# SceneTwin Codex Handoff — 2026-04-22

This note captures the actual state of the SceneTwin follow-up analysis after regenerating the missing description tensors and testing alternatives to the original whole-cortex mean-map cosine.

## Files Generated / Located

The missing description prediction tensors were successfully regenerated in Colab and downloaded.

Local files now available:

- `/Users/adarsha/Downloads/video_preds.npy`
- `/Users/adarsha/Knowledge/output/scenetwin_preds/desc_accurate_concise_preds.npy`
- `/Users/adarsha/Knowledge/output/scenetwin_preds/desc_accurate_detailed_preds.npy`
- `/Users/adarsha/Knowledge/output/scenetwin_preds/desc_bad_vague_preds.npy`
- `/Users/adarsha/Knowledge/output/scenetwin_preds/desc_hallucinated_preds.npy`

Shapes:

- `video_preds.npy`: `(30, 20484)`
- `desc_accurate_concise_preds.npy`: `(14, 20484)`
- `desc_accurate_detailed_preds.npy`: `(34, 20484)`
- `desc_bad_vague_preds.npy`: `(7, 20484)`
- `desc_hallucinated_preds.npy`: `(14, 20484)`

## Original Baseline Confirmed

Whole-cortex mean-map cosine remains the same story as before:

- `hallucinated`: `0.7906`
- `accurate_detailed`: `0.7584`
- `accurate_concise`: `0.7405`
- `bad_vague`: `0.3880`

Interpretation: the raw TRIBE mean-map cosine still rewards vivid scene-like description rather than the correct scene.

## Experiment 1 Tried First: Coarse Anatomical ROI Restriction

I fixed a corrupted local Destrieux fsaverage5 atlas cache and reran the test using anatomical surface ROIs on fsaverage5.

Tested masks:

- broad `scene_roi`
- `visual_core`
- `parahip_only`
- `language_roi`

### Result

This did **not** solve the hallucination problem.

Mean-map cosine by ROI:

| Description | Whole | Scene ROI | Visual Core | Parahip Only | Language ROI |
|---|---:|---:|---:|---:|---:|
| accurate_concise | 0.7405 | 0.8236 | 0.8340 | 0.7066 | 0.5152 |
| accurate_detailed | 0.7584 | 0.8690 | 0.8943 | 0.8017 | 0.2416 |
| bad_vague | 0.3880 | 0.1652 | 0.1264 | 0.2841 | 0.2809 |
| hallucinated | 0.7906 | 0.8858 | 0.8981 | 0.8337 | 0.5285 |

Conclusion:

> A coarse Destrieux anatomical "scene-ish" mask is too blunt. It still ranks the hallucinated beach description above the accurate snow description.

This means the original idea was not wrong in spirit, but the anatomical atlas / parcel choice is too coarse to recover scene specificity.

## Experiment 1 Retried Properly: Functional Glasser Parcels on fsaverage5

The user correctly objected that Destrieux was the wrong atlas class for this question. I then downloaded the HCP-MMP1 / Glasser surface annotations (`lh.HCPMMP1.annot`, `rh.HCPMMP1.annot`) from the `ggsegGlasser` data source on GitHub, downsampled them from full `fsaverage` to `fsaverage5` via spherical nearest-neighbor mapping, and rebuilt functional masks directly on the TRIBE vertex space.

Important detail:

- the downsampling was exact at the spherical-coordinate level (`maxdist = 0.0`), because `fsaverage5` vertices are a subset of `fsaverage`

### Functional masks tested

- `ppa_func`: `PHA1`, `PHA2`, `PHA3`, `ProS`
- `rsc_func`: `RSC`, `POS1`, `POS2`
- `loc_func`: `LO1`, `LO2`, `LO3`
- `mtplus_func`: `MT`, `MST`, `FST`
- `early_visual_func`: `V1`, `V2`, `V3`, `V4`, `V3A`, `V3B`, `V3CD`, `V4t`, `V8`
- `ventral_scene_func`: union of `ppa_func + rsc_func + loc_func + mtplus_func`
- `ventral_scene_plus_early`: `ventral_scene_func + early_visual_func`

### Mean-map cosine with Glasser

| Description | Whole | PPA Func | RSC Func | LOC Func | MT+ Func | Early Visual | Scene Func | Scene+Early |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| accurate_concise | 0.7405 | 0.7427 | 0.7372 | 0.8834 | 0.7081 | 0.8845 | 0.6747 | 0.8495 |
| accurate_detailed | 0.7584 | 0.8995 | 0.7357 | 0.8917 | 0.7088 | 0.9166 | 0.7802 | 0.8896 |
| bad_vague | 0.3880 | -0.6058 | 0.2180 | -0.5529 | -0.2233 | 0.4338 | -0.3700 | 0.2850 |
| hallucinated | 0.7906 | 0.8959 | 0.7569 | 0.8988 | 0.7171 | 0.9261 | 0.7486 | 0.8933 |

Interpretation:

- The ROI hypothesis is **not dead**.
- In `PPA` and in the combined `Scene Func` mask, the accurate detailed description now beats the hallucination on mean-map cosine.
- The margin is small in `PPA` (`0.8995 > 0.8959`) but real.
- `LOC` and `Early Visual` still favor the hallucination, so not every functional mask helps.

### Temporal mean per-TR cosine with Glasser

After resampling each description tensor to the video length (`30 TR`) and averaging per-TR cosine:

| Description | Whole | PPA Func | RSC Func | LOC Func | MT+ Func | Early Visual | Scene Func | Scene+Early |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| accurate_concise | 0.6794 | 0.7372 | 0.7472 | 0.7796 | 0.7774 | 0.7240 | 0.6944 | 0.7278 |
| accurate_detailed | 0.6339 | 0.7685 | 0.6241 | 0.6839 | 0.6625 | 0.7376 | 0.6650 | 0.7179 |
| bad_vague | 0.3076 | -0.3869 | 0.3614 | -0.3581 | 0.0553 | 0.3090 | -0.0991 | 0.2396 |
| hallucinated | 0.6584 | 0.7235 | 0.5399 | 0.7857 | 0.7646 | 0.7030 | 0.6367 | 0.6908 |

Interpretation:

- `PPA Func` is the strongest clean result so far.
- In `PPA Func`, temporal alignment gives:
  - `accurate_detailed = 0.7685`
  - `hallucinated = 0.7235`
  - `bad_vague = -0.3869`
- In `Scene Func`, temporal alignment also gets the order right:
  - `accurate_concise > accurate_detailed > hallucinated > bad_vague`
- In `Scene+Early`, temporal alignment gets:
  - `accurate_detailed = 0.7179`
  - `hallucinated = 0.6908`

Updated conclusion:

> The Destrieux result did not kill the ROI idea. A functional atlas rerun shows real scene-selective signal, especially in Glasser-derived PPA parcels and in temporal alignment within functional scene masks.

### Useful sub-finding

A few individual parcels slightly favored the accurate detailed description over the hallucination, including:

- `G_occipital_middle`
- `G_cuneus`
- `G_oc-temp_med-Lingual`

But the effect is small and gets washed out when pooled over a broad ROI.

## Alternative Tried: Centered / Z-scored Mean-map Similarity

I also tested centered pattern correlation and z-scored cosine across vertices instead of raw cosine.

This did **not** materially fix the issue. Hallucinated remained too competitive, and often still won.

Conclusion:

> The problem is not just global activation bias. Mean-map comparison itself is still too lossy.

## Experiment 2 Partial Success: Temporal Alignment

I then kept the time axis and compared per-TR trajectories after resampling each description tensor to the video length (`30 TR`).

Best-performing variant tested:

- compute per-TR cosine
- average across time
- restrict to a `visual_core` fsaverage5 mask

### Temporal Visual-Core Scores

- `accurate_detailed`: `0.7336`
- `accurate_concise`: `0.7181`
- `hallucinated`: `0.7008`
- `bad_vague`: `0.1089`

This is the first TRIBE-only metric that gave a better ordering:

`accurate_detailed > accurate_concise > hallucinated > bad_vague`

### Visual Gain Over Whole Cortex

I also computed:

`visual_temporal - whole_temporal`

Results:

- `accurate_detailed`: `+0.0998`
- `hallucinated`: `+0.0424`
- `accurate_concise`: `+0.0386`
- `bad_vague`: `-0.1987`

This is currently the strongest TRIBE-only signal found on the saved tensors.

### Limitation

The separation is real but modest. It is not yet strong enough to replace `TRIBE × CLIP` as the main result.

Also, when I looked at some internal windows of the clip, the hallucinated description still won in parts of the middle / late clip. So this is not a clean full fix, only a partial improvement.

## Current Honest Conclusion

1. Whole-cortex mean-map cosine fails.
2. Coarse anatomical ROI restriction fails.
3. Functional ROI restriction with Glasser does better and partially supports the ROI hypothesis.
4. Centered mean-map similarity fails.
5. Per-TR temporal alignment in functional visual / scene cortex rescues more of the signal.
6. `TRIBE × CLIP` is still the cleanest working metric today.

Best current phrasing:

> Whole-cortex average similarity is not enough. Functional scene-selective masks, especially Glasser-derived PPA, recover more scene-specific signal, and temporal alignment improves it further. A grounding signal is still the cleanest way to suppress hallucinations on this clip.

## Broader Direction Discussed

The bigger conceptual shift is that SceneTwin may need to stop being framed purely as:

> "Does text produce the same TRIBE response as video?"

and move toward:

> "Does audio-plus-description preserve the effect of the movie for a blind/low-vision listener?"

That suggests a broader experience-preservation metric rather than a caption-fidelity metric.

Working sketch:

`ExperienceScore = NeuralGain + EventAlignment + SalienceCoverage + RecallAgreement + AffectAgreement - HallucinationPenalty`

Where:

- `NeuralGain`: compare `audio-only` vs `audio+description` against full audiovisual response
- `EventAlignment`: preserve event boundaries and event order
- `SalienceCoverage`: preserve the visually important things at the right times
- `RecallAgreement`: preserve what a listener later remembers / can answer
- `AffectAgreement`: preserve suspense, humor, urgency, sadness, etc.
- `HallucinationPenalty`: punish confident but wrong scene content

This is not implemented yet. It is the likely `SceneTwin v2` framing if the goal is closer to "preserve the same effect as watching the movie."

## Research Directions Worth Pulling In

These sources support broadening the project beyond raw TRIBE similarity:

- `101 Dalmatians` dataset:
  rich multimodal annotations, sensory-loss groups, scene/cut/subtitle/soundtrack structure, category labels
  https://www.nature.com/articles/s41597-025-06077-3

- `Describe Now`:
  BLV users want control over timing and level of detail; one fixed AD style is not enough
  https://arxiv.org/abs/2411.11835

- `RNIB 2025 AI-generated AD report`:
  evaluation should include professional describers, user feedback, richer context, and practical quality criteria
  https://media.rnib.org.uk/documents/AI-Generated_Audio_Description_Report_August_2025.pdf

- `QuerYD`:
  temporally aligned spoken descriptions are useful for event-localized / retrieval-style evaluation
  https://arxiv.org/abs/2011.11071

- `CrossA11y`:
  useful framing around modality asymmetry and what visual content is missing from audio alone
  https://arxiv.org/abs/2208.11144

## What To Do Next

### If the goal is the best current poster result

Use:

- `TRIBE × CLIP` as the primary metric
- temporal / functional-mask TRIBE analysis as a supporting "we also probed inside TRIBE and found scene-selective signal in PPA and temporal visual cortex" result

### If the goal is maximum scientific ambition

Do these next:

1. Implement `Description Gain`:
   compare `audio-only` and `audio+description` against audiovisual, not just `video` vs `text`.
2. Add event-structure scoring:
   event boundaries, retrieval matrix, or event-localized matching.
3. Add human outcome measures:
   comprehension QA, recall, event ordering, affect/tension trace.
4. Replace coarse Destrieux scene ROIs with better masks:
   Wang visual atlas, Glasser/HCP parcels, or a more principled scene-selective mask.
5. Test on multiple clips before claiming a TRIBE-only rescue.

## Code / Environment Notes

- A Colab notebook was created and fixed for regenerating the missing description tensors:
  `output/scenetwin_desc_preds_colab.ipynb`
- The local Destrieux atlas cache at `/Users/adarsha/nilearn_data/destrieux_surface/` was corrupted at first and had to be replaced with fresh `.annot` files from the official NITRC URLs.
- The actual analysis scripts were run ad hoc from the terminal using the working `tribev2` venv at:
  `/Users/adarsha/njbda/tribev2/.venv/bin/python`

## Bottom Line

If another Codex instance picks this up, the most important thing to know is:

> We now have the missing description tensors. Coarse ROI restriction did not fix hallucinations. Temporal visual-core alignment partially helped. The cleanest working result is still `TRIBE × CLIP`, but the project should probably evolve toward an experience-preservation framework rather than pure text-vs-video similarity.
