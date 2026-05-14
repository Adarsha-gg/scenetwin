---
title: "SceneTwin Revolutionary Implementation Plan"
category: research
tags: [SceneTwin, novelty, implementation, Description-Gain, event-boundaries, accessibility]
sources:
  - https://aclanthology.org/2025.emnlp-main.1199/
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC12398407/
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC11872226/
  - https://www.nature.com/articles/s41597-025-06077-3
  - https://jatjournal.org/index.php/jat/article/view/245
  - https://portal.research.lu.se/en/publications/event-boundary-perception-among-the-visually-impaired-in-audio-de
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC11493368/
  - https://pubmed.ncbi.nlm.nih.gov/40918301/
  - https://huggingface.co/facebook/tribev2
created: 2026-05-02
updated: 2026-05-02
---

# SceneTwin Revolutionary Implementation Plan

## Bottom Line

Do not frame SceneTwin as "we combine TRIBE and CLIP." That is not enough.

The original contribution should be:

> **Counterfactual neural accessibility**: estimate what visual/narrative brain signal is missing when a listener only has audio, then measure whether an audio description restores that missing signal at the right moments and in the right cortical systems.

This moves SceneTwin away from "caption scoring" and toward a new class of accessibility metric.

## What Existing Work Already Owns

- **CLIPScore / visual grounding**: reference-free image/video-caption matching already exists.
- **VideoA11y**: BLV-focused AD generation and human/user evaluation already exists.
- **ADQA**: QA-based AD evaluation on coherent multi-minute segments already exists and is the closest evaluation competitor.
- **TRIBE v2 / movie brain encoding**: predicted fMRI for video/audio/text already exists.
- **101 Dalmatians / neurocinematics**: real fMRI for audiovisual, auditory, visual, sensory-loss movie experience already exists.

SceneTwin becomes new only if it contributes a **new metric family** and **counterfactual experiment design**.

## New Metric 1 — Missing Visual Residual Recovery

Current Description Gain:

```text
DG = cos(P_AV, P_D) - cos(P_AV, P_A)
```

Better original metric:

```text
MVR = P_AV - P_A
MVRR = cos(MVR, P_D)
```

Where:

- `P_AV`: TRIBE prediction for full audiovisual video
- `P_A`: TRIBE prediction for audio-only soundtrack
- `P_D`: TRIBE prediction for description text/TTS
- `MVR`: the predicted cortical response missing from the soundtrack alone
- `MVRR`: how much the description recovers the missing visual/narrative residual

Why this is more original:

- It directly asks what the AD adds beyond the original soundtrack.
- It penalizes descriptions that merely restate audible content.
- It reframes AD evaluation as **restoration of inaccessible signal**, not caption similarity.

Implementation:

1. Run TRIBE on video clip: `P_AV`
2. Extract soundtrack and run TRIBE audio-only: `P_A`
3. Run TRIBE on each candidate description: `P_D`
4. Compute whole-cortex MVRR first.
5. Then compute ROI-restricted MVRR for scene/action/social/narrative systems.

This can be implemented immediately with the Description Gain notebook outputs.

## New Metric 2 — Auditory Redundancy Penalty

Good AD should describe what cannot be understood from the soundtrack. It should not waste listener bandwidth repeating audible information.

```text
ARP = cos(P_D, P_A)
UsefulDescriptionScore = MVRR - alpha * ARP
```

Interpretation:

- High `MVRR`: the description recovers missing audiovisual information.
- High `ARP`: the description overlaps too much with what audio already provides.
- The best AD has high missing-signal recovery and low redundancy.

This directly operationalizes the AD guideline "focus on visual content, avoid audible content unless the sound source is ambiguous."

Implementation:

- Start with `alpha = 0.25`.
- Tune only after seeing whether `ARP` actually separates VideoA11y from VATEX.
- Report ablation: `MVRR`, `ARP`, `MVRR - ARP`.

## New Metric 3 — Event Boundary Recovery Score

AD is not just what is said. It is when the description updates the listener's event model.

Relevant literature:

- AD researchers show professional descriptions are structured around event segmentation and event boundaries.
- Cognitive neuroscience shows event boundaries create measurable cortical pattern shifts during movie viewing.
- ADQA argues short trimmed clips are inadequate because AD must preserve narrative understanding over coherent segments.

SceneTwin version:

```text
boundary_curve(X)[t] = 1 - cos(mean(X[t-k:t]), mean(X[t:t+k]))
EBRS = corr(boundary_curve(P_AV), boundary_curve(P_D_resampled))
```

Optional missing-signal version:

```text
EBRS_residual = corr(boundary_curve(P_AV - P_A), boundary_curve(P_D_resampled))
```

Why this is new:

- It measures whether the description causes predicted neural state transitions when the movie itself changes events.
- It moves beyond text similarity, object matching, and mean-vector cosine.
- It connects AD evaluation to event cognition.

Implementation:

1. Keep full TRIBE time series; do not average first.
2. Resample each description tensor to the video tensor length.
3. Compute pattern-shift curves with window sizes `k = 2, 4, 8`.
4. Score Pearson/Spearman correlation between video and description boundary curves.
5. Report top event-boundary misses: video had a strong boundary, description did not.

Poster-friendly line:

> SceneTwin checks whether the description updates the listener's predicted event model when the scene actually changes.

## New Metric 4 — Neuro-Accessibility Profile

Do not collapse SceneTwin into one scalar too early. Audio description quality has dimensions:

- scene/spatial layout
- character identity and faces
- body/action
- emotion/social intent
- narrative/event transitions
- auditory redundancy

TRIBE gives cortical surface predictions, so compute a profile:

```text
SceneScore       = MVRR(PPA/RSC/OPA/LOC)
ActionScore      = MVRR(MT+/EBA)
CharacterScore   = MVRR(FFA/STS)
NarrativeScore   = MVRR(DMN/TPJ/mPFC if usable)
RedundancyScore  = cos(P_D, P_A)
GroundingScore   = CLIP or PAC-S
```

Then report:

```text
SceneTwinProfile = {
  grounding,
  missing_visual_recovery,
  event_boundary_recovery,
  character_social_recovery,
  redundancy_penalty
}
```

Why this is stronger:

- BLV users do not want one universal AD style.
- Describe Now shows timing and detail preferences vary by video/user.
- A profile supports personalization: sports may weight action; film may weight character/emotion; travel may weight scene layout.

Implementation:

1. Start with Glasser/functional ROI masks already explored.
2. Add a simple category-dependent weight table:
   - sports/action: MT+/EBA > PPA
   - film/animation: FFA/STS/DMN > PPA
   - travel: PPA/RSC/OPA > MT+
   - food/how-to: hand/body/action + object/scene
3. Report both raw profile and weighted score.

## New Metric 5 — Counterfactual Stress Tests

Current evals compare existing descriptions. To make the contribution ours, generate controlled counterfactual ADs:

For each clip, create:

1. `correct_full`: accurate VideoA11y description
2. `audible_only`: describes only sounds/dialogue
3. `object_only`: names objects but misses action/event
4. `wrong_event_order`: same facts, wrong temporal order
5. `wrong_emotion`: correct objects/actions, wrong affect/social intent
6. `wrong_spatial`: correct objects, wrong layout
7. `hallucinated`: visually rich but wrong scene

Expected metric behavior:

| Perturbation | Grounding | MVRR | EBRS | ARP |
|---|---:|---:|---:|---:|
| correct_full | high | high | high | low/moderate |
| audible_only | low/moderate | low | low | high |
| object_only | moderate | moderate | low | low |
| wrong_event_order | moderate | moderate | low | low |
| wrong_emotion | moderate/high | lower in social/narrative ROIs | maybe low | low |
| wrong_spatial | moderate | low in PPA/RSC | moderate | low |
| hallucinated | low | low/negative | low | low |

This is the cleanest way to show SceneTwin is not just CLIPScore.

Implementation:

- Use GPT/Claude to generate perturbations from each VideoA11y description with strict templates.
- Save all perturbations as JSON.
- Run CLIP, MVRR, ARP, EBRS, profile scores.
- Show that each metric catches different failure modes.

## New Metric 6 — Event-Aware Listener Burden

AD quality is not only "more detail is better." BLV users may want control over timing and detail. The score should punish excessive description when the listener's event model is already stable.

```text
Burden(t) = words_per_second(t) * low_boundary_need(t)
low_boundary_need(t) = 1 - normalized(boundary_curve(P_AV - P_A)[t])
```

Meaning:

- If a scene is neurally stable and audio already carries the event, heavy description is burden.
- If a strong missing visual boundary occurs, description is valuable.

Implementation:

1. Timestamp descriptions if available; otherwise sentence-align evenly.
2. Estimate `boundary_need` from `P_AV - P_A`.
3. Penalize high word density in low-need windows.

This gives SceneTwin a personalization path: different users can choose low, medium, high burden tolerance.

## Implementation Order

### Phase 1 — Immediate, With Current Colab

Implement from the existing Description Gain notebook outputs:

1. `MVR = P_AV - P_A`
2. `MVRR = cos(MVR, P_D)`
3. `ARP = cos(P_D, P_A)`
4. `UsefulDescriptionScore = MVRR - 0.25 * ARP`

This requires no new TRIBE runs beyond the notebook already planned.

### Phase 2 — Time-Series Metrics

Add:

1. `boundary_curve`
2. `EBRS`
3. `EBRS_residual`

This uses saved tensors only. No extra GPU after tensors exist.

### Phase 3 — Counterfactual Dataset

Create `output/scenetwin_counterfactual_descriptions.json` with perturbations for each real clip.

Run:

- CLIP grounding
- MVRR
- ARP
- EBRS
- SceneTwinProfile

This becomes the core "our own new shit" experiment.

### Phase 4 — Personalization

Create category/user profiles:

```text
profile_sports = action 0.45, scene 0.20, character 0.20, narrative 0.15
profile_film   = character 0.35, narrative 0.30, scene 0.20, action 0.15
profile_travel = scene 0.45, action 0.15, character 0.15, narrative 0.25
```

Then report how rankings change by profile.

## Poster/Paper Claim If This Works

Weak claim:

> SceneTwin combines TRIBE and CLIP to score audio descriptions.

Strong claim:

> SceneTwin introduces counterfactual neural accessibility metrics that estimate which visual/narrative signals are absent from the soundtrack and test whether an audio description restores those signals without adding redundant burden.

This is the version that can be called new.

## What To Build Next

1. Extend `output/scenetwin_description_gain_colab.ipynb` to compute and export `MVRR`, `ARP`, and `UsefulDescriptionScore`.
2. Add a local post-processing script:
   `njbda/scenetwin_neural_accessibility_metrics.py`
3. Generate counterfactual descriptions for 20 clips.
4. Run all metrics on real + counterfactual descriptions.
5. Make one table showing failure-mode coverage:
   - CLIP catches hallucination
   - MVRR catches missing visual restoration
   - ARP catches redundant audible descriptions
   - EBRS catches wrong timing/order
   - Profile catches dimension-specific AD quality

