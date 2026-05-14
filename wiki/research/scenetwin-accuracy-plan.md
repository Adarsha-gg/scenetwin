---
title: "SceneTwin Accuracy Plan: From Whole-Cortex Cosine to Scene-Specific Fidelity"
category: research
tags: [SceneTwin, TRIBE-v2, accuracy, NJBDA-2026, experiments]
sources:
  - wiki/research/scenetwin.md
  - wiki/research/scene twin codex.md
  - /Users/adarsha/njbda/tribev2/tribev2/model.py
  - /Users/adarsha/njbda/tribev2/README.md
created: 2026-04-21
updated: 2026-04-21
---

## TL;DR

The current SceneTwin score is throwing away almost all the information TRIBE actually produces. Whole-cortex, time-averaged cosine collapses a `(30 timesteps, 20484 cortical vertices)` tensor into a single scalar, which destroys the two things that make TRIBE special: **anatomical specificity** and **temporal structure**. This plan identifies where the real signal lives and proposes four experiments, ordered by expected impact, that should dramatically improve the separation between accurate and hallucinated descriptions — potentially enough to drop CLIP as a crutch entirely.

---

## What TRIBE v2 Actually Predicts

Before improving anything, understand the output.

### The architecture (from `model.py`)

TRIBE v2 is a Transformer that takes three pretrained feature streams and projects them onto a cortical surface:

1. **Video features**: pretrained video encoder (likely V-JEPA or similar), per-frame or per-chunk embeddings
2. **Audio features**: pretrained audio encoder (likely Wav2Vec2 or AudioMAE)
3. **Text features**: pretrained LLM embeddings (per-word, with sentence/context annotations)

Each modality is projected to a shared hidden dimension (`hidden=256`), concatenated, passed through a multi-layer Transformer encoder with temporal position embeddings, then projected via a `SubjectLayers` predictor to `n_outputs=20484` cortical vertices. Output shape is `(batch, n_outputs, n_timesteps)`, where each timestep is one TR (repetition time, default 1.49 seconds — the fMRI sampling rate).

### What the outputs mean

- **Spatial axis (20,484 vertices)**: the fsaverage5 cortical surface mesh, a standard Freesurfer template. Each vertex maps to a **known anatomical location** in the cortex. This is not a black-box embedding — vertex *i* corresponds to a specific point in, say, left ventral temporal cortex.
- **Temporal axis (one step per TR)**: per-timepoint predicted BOLD signal, offset **5 seconds into the past** to compensate for the hemodynamic response function. So a prediction at time `t` corresponds to stimulus content around time `t + 5s`.
- **Subject**: the model was trained with subject-specific layers, but `TribeModel.from_pretrained` sets `average_subjects=True`, so what we get is the average-subject response.

### Why this matters for scoring

The cortex is not uniform. Different regions respond to different features:

| Region | Responds to |
|---|---|
| V1 / V2 / V3 / V4 | Low-level vision: edges, color, motion, contrast |
| MT / MST | Motion, optical flow |
| FFA (fusiform face area) | Faces |
| PPA (parahippocampal place area) | Scenes, places, landscapes |
| EBA (extrastriate body area) | Bodies |
| LOC (lateral occipital complex) | Object shape |
| STS (superior temporal sulcus) | Voices, speech, social motion |
| Heschl's gyrus / A1 | Low-level audio |
| Broca / Wernicke / AG | Language, semantics |
| RSC (retrosplenial cortex) | Scene navigation, spatial context |

**The hallucinated beach description and the real snow video both produce high average activity across "stuff happens in visual/scene/language cortex" regions**, which is why raw whole-cortex cosine scored them similarly (0.79). But they should produce **very different activation patterns within scene-selective regions** (PPA, RSC) because "snowy mountain" and "tropical beach" are both scenes, but different scenes.

Current SceneTwin is measuring "is this description evocative of something visual" instead of "is this description evocative of *this* scene." Restricting similarity to scene-selective cortex should fix this without CLIP.

---

## The Four Experiments

Ordered by expected impact. Each is small, self-contained, and testable on the existing Sintel + 4-description setup before adding new stimuli.

### Experiment 1 — ROI-Restricted Scoring (biggest lever)

**Hypothesis**: Hallucinated descriptions score high on whole-cortex cosine because they activate scene/visual/language cortex broadly, but score low when we restrict comparison to **scene-selective regions** (PPA, RSC, LOC), where the pattern within those regions should differ between "snow mountain" and "beach."

**Method**:
1. Obtain an fsaverage5 parcellation. Options:
   - **Glasser HCP-MMP1.0** (360 parcels) — use `neuromaps` or `brainspace` to load and resample to fsaverage5
   - **Yeo 7 / 17 networks** — coarser, simpler, available in Freesurfer
   - **Visual ROI atlas** (Wang et al. 2015) — retinotopic + category-selective visual regions, ideal for this project
2. Build vertex masks for scene-selective ROIs: PPA, RSC, LOC, MT+, V1–V4, OPA (occipital place area).
3. For each description, compute cosine similarity **restricted to those vertices only**, averaged per ROI.
4. Also compute a "language ROI" score (Broca, Wernicke, AG) as a control — hallucinated and accurate descriptions should score similarly here, confirming the signal is scene-specific, not general.

**Success criterion**:
- Scene-ROI cosine for hallucinated description < 0.3 (was 0.79 on whole cortex).
- Language-ROI cosine for hallucinated description stays high (≈ accurate descriptions), confirming the metric is isolating scene specificity, not just global response.
- Scene-ROI separation between accurate and hallucinated ≥ 2× what whole-cortex cosine gave us.

**Why this is the biggest lever**: we go from one scalar over 20,484 mixed vertices to targeted scalars over a few hundred scene-selective vertices. Signal-to-noise should jump.

---

### Experiment 2 — Per-TR Temporal Alignment (second lever)

**Hypothesis**: Time-averaging destroys temporal structure. A good description should produce a brain response trajectory that **tracks the video's trajectory over time**, not just matches its mean. A hallucinated description describes events that do not happen in the video, so its per-TR activation should desynchronize from the video.

**Method**:
1. Keep the full `(T, V)` prediction tensor — don't collapse the time axis.
2. Compute **per-timestep** cosine: for each TR `t`, similarity between `video_preds[t]` and `desc_preds[t]`. Returns a vector of length T.
3. Derived metrics:
   - **Mean per-TR cosine** (should beat time-averaged cosine because it punishes temporal drift)
   - **Canonical correlation (CCA)** between the two trajectories over time within an ROI
   - **Dynamic time warping distance** — allows slight temporal slack
4. Critical detail: TRIBE predictions are offset 5s into the past. Description TTS may not be time-aligned to the video. Need to either:
   - Time-stretch the description audio to match video duration, or
   - Align at sentence-chunk level rather than frame level

**Success criterion**:
- Accurate descriptions show positive per-TR cosine sustained across the clip.
- Hallucinated descriptions show per-TR cosine that drops or goes negative in the middle of the clip, where scene-specific content is strongest.
- Mean per-TR score separates accurate from hallucinated by ≥ 2× the time-averaged score.

---

### Experiment 3 — Description Gain (contrast against audio-only)

**Hypothesis** (already proposed in the codex notes but not tested): the real question is not "does description alone predict the video's brain response," but "does adding the description **on top of the soundtrack** get us closer to the audiovisual response than the soundtrack alone?"

**Method**:
1. Run TRIBE three times:
   - `P_AV = TRIBE(audio + video)` — full stimulus
   - `P_A  = TRIBE(audio only)` — soundtrack alone
   - `P_AD = TRIBE(audio + description_as_additional_text)` — can we pass text and audio together? Check `get_events_dataframe` — currently takes only one path. May need to construct events manually via the `events` DataFrame API (see `demo_utils.py`).
2. Compute:
   - `DescriptionGain = cos(P_AV, P_AD) − cos(P_AV, P_A)`
3. A good description makes `P_AD` closer to `P_AV` than `P_A` is. A hallucination drags `P_AD` further from `P_AV` — **negative gain**.

**Success criterion**:
- Accurate descriptions: `DescriptionGain > 0`, ideally > 0.05.
- Vague descriptions: `DescriptionGain ≈ 0` (doesn't help, doesn't hurt).
- Hallucinated descriptions: `DescriptionGain < 0` (actively misleads the brain model).

**Why this matters**: it reframes the metric from "similarity" to **"does the description add the missing visual information the soundtrack doesn't already carry?"** That is the actual clinical question for BLV accessibility.

**Implementation risk**: requires constructing multi-modality event DataFrames. Read `tribev2/eventstransforms.py` and `demo_utils.py` to see how the events pipeline composes audio + text. If this is blocked, fall back to the simpler version: `cos(P_AV, P_D) − cos(P_AV, P_A)` where `P_D` is description-only.

---

### Experiment 4 — Contrastive Retrieval (rigor test)

**Hypothesis**: a good metric should rank the *correct* description highest across a pool of candidates. If we give SceneTwin 5 videos and 5 descriptions and ask it to match them, a strong metric retrieves the right pair for each video.

**Method**:
1. Collect 5 distinct open clips with maximally different scenes:
   - Sintel snowy scene (have)
   - Big Buck Bunny forest
   - Tears of Steel cityscape
   - A nature documentary underwater clip
   - An indoor kitchen cooking clip
2. For each clip, write one accurate description.
3. Compute the full 5×5 similarity matrix using each candidate metric (whole-cortex, ROI-restricted, per-TR, Description Gain).
4. Metrics:
   - **Retrieval accuracy @ 1**: fraction of videos whose correct description is top-ranked.
   - **Mean rank of correct description**.
   - **Contrastive margin**: `cos(video_i, correct_desc_i) − mean_{j≠i} cos(video_i, desc_j)` — how much the correct pair beats the wrong pairs on average.

**Success criterion**:
- ROI-restricted or per-TR metric achieves retrieval@1 ≥ 4/5, vs. whole-cortex cosine at or below chance.
- Positive contrastive margin for all 5 clips.

**Why this matters for the poster**: retrieval@1 is a single number judges can grasp immediately. "SceneTwin matches 5/5 descriptions to the right video; whole-cortex cosine matches 1/5" is a much stronger headline than "SceneTwin score is 0.92 for accurate descriptions."

---

## Suggested Order Of Attack

**Week of Apr 21–27 (fastest wins)**:
1. Experiment 1 (ROI-restricted). Biggest expected lift, purely a post-processing change on existing predictions. No new TRIBE runs needed — just apply masks to the saved `predictions.npy`.
2. Experiment 2 (per-TR). Also no new runs. Same saved tensor, different aggregation.

**Week of Apr 28–May 4**:
3. Experiment 3 (Description Gain). Requires constructing multi-modality events. This is the hardest plumbing-wise but the most novel scientifically.

**Week of May 5–11**:
4. Experiment 4 (contrastive retrieval). Requires collecting 4 new clips and writing descriptions. Do this last since it depends on one of experiments 1–3 actually working.

**Poster deadline**: May 15. That leaves a 4-day buffer for figure generation and write-up.

---

## What To Drop If CLIP Becomes Unnecessary

If Experiment 1 or 2 alone gets hallucination separation to match or beat the current TRIBE×CLIP product, **consider dropping CLIP from the metric entirely**. The SceneTwin story becomes much cleaner:

> "Whole-cortex cosine is not enough. Restricting to scene-selective cortex is."

This is a much stronger and more defensible claim than "we need CLIP to patch a hole in TRIBE." It also makes SceneTwin a pure neuroscience contribution rather than a hybrid engineering fix.

Keep CLIP in reserve as a robustness check, but the lead metric should be the one that exploits TRIBE's spatial structure.

---

## Key Files And References

- `/Users/adarsha/njbda/tribev2/tribev2/model.py` — architecture reference
- `/Users/adarsha/njbda/tribev2/tribev2/demo_utils.py` — events API for multi-modality runs
- `/Users/adarsha/njbda/scenetwin_test.ipynb` — current POC notebook, start here
- `/Users/adarsha/Downloads/video_preds.npy` — saved `(T, 20484)` tensor — reuse for Experiments 1 and 2 with no new inference
- [fsaverage5 + Glasser parcellation via neuromaps](https://netneurolab.github.io/neuromaps/)
- [Wang et al. 2015 visual ROI atlas](https://napl.scholar.princeton.edu/resources) — retinotopic + category-selective masks

## See Also

- [[scenetwin]]
- [[scene twin codex]]

## Sources

- TRIBE v2 model code: `/Users/adarsha/njbda/tribev2/tribev2/model.py`
- TRIBE v2 README: `/Users/adarsha/njbda/tribev2/README.md`
- Prior SceneTwin wiki pages and proof-of-concept results
