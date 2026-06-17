---
title: "TRIBE use-case: the accessibility gap localizes to visual cortex"
category: research
tags: [scenetwin, tribe, roi, fsaverage5, glasser, validity, external-generalization]
sources: [cursor/research/output/tribe_tensors/, output/scenetwin_description_gain/glasser_roi_mask.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

The TRIBE use-case is **typed accessibility gaps**: it tells you not just *how
much* visual information an audio description drops (a scalar already does that
better) but *what kind* — spatial/scene information vs agent/object
information. A single scalar provably cannot do this.

Variance decomposition of the per-(clip, ROI) AV-vs-A gap (8 visual ROIs x 78
clips, sums to 100%):

| component | share | meaning |
|---|---:|---|
| clip global magnitude | 20.5% | what the scalar `accessibility_gap` already captures |
| fixed anatomy | 24.7% | "retrosplenial/V1 always high" — expected, near-tautological |
| **clip x ROI interaction** | **54.7%** | **clip-specific localization, invisible to any scalar** |

Over half the structure is clip-specific region profile. Supporting evidence
it is real signal, not noise:

- Per-ROI gaps correlate with the scalar only 0.19-0.57 -> not rescaled copies.
- The **dominant lost region varies** across clips: retrosplenial 37, early-V1
  21, scene-PPA 16, object/body 4.
- The **scene-minus-agent gap orders content categories sensibly** (external
  validity): Food & Cooking 0.32, How-to 0.25, Entertainment 0.25, Sports
  0.23, People & Vlogs 0.15, Pets & Animals 0.12. Agent-heavy categories
  (people, pets) sit lowest because faces/bodies push the agent block up.

### What is NOT the headline (a sanity check, not a finding)

"Removing video diverges visual cortex more than auditory cortex" is close to a
tautology — if TRIBE did not show it, the encoder would be broken. It is true
(visual block 0.184 vs auditory/language 0.087 external, paired perm p = 5e-5,
n = 60, holds out of bench) and worth one sentence as a validity check, but it
is not the use-case. Note also that within vision the effect is lopsided: only
scene / spatial / early-visual ROIs move; face, body, motion and object ROIs
sit barely above the auditory control. Audio already conveys agents/actions;
what it cannot carry is spatial layout and scene gist.

## What was computed

Full per-vertex counterfactual tensors for all 78 clips (18 in-bench + 60
external) were dumped from Colab (`tribe_tensors_all78.zip`) and loaded via
`cursor/research/tribe_tensors_load.py`. For each clip and each functional ROI
(HCP-MMP1 Glasser projected to fsaverage5, see [[research/scenetwin-glasser-roi-mask]]):

    roi_gap = 1 - cos( mean_t P_AV[:, roi_verts], mean_t P_A[:, roi_verts] )

ROIs are grouped into a **visual block** (early V1, higher visual V2-V4, scene
PPA, retrosplenial/spatial, face FFC, body EBA, motion MT+, object) and a
**control block** (auditory, language). Script:
`cursor/research/tribe_roi_gap_usecase.py` -> `output/tribe_roi_gap_per_clip.csv`.

## Per-ROI mean gap (external, n=60)

| ROI | block | gap |
|---|---|---:|
| retrosplenial / spatial | VIS | 0.440 |
| early visual V1 | VIS | 0.348 |
| scene PPA | VIS | 0.263 |
| higher visual V2-V4 | VIS | 0.115 |
| face FFC | VIS | 0.095 |
| language control | CTL | 0.089 |
| auditory control | CTL | 0.085 |
| body EBA | VIS | 0.079 |
| motion MT+ | VIS | 0.076 |
| object | VIS | 0.055 |

- visual-block mean 0.184 vs control-block mean 0.087 (~2x).
- per-clip visual > control in 73% of external clips, 83% in-bench.
- permutation p: external 5e-5, in-bench 9.8e-3, all-78 < 5e-5.

## Why the control block is the control

Audio-only (P_A) should reconstruct **auditory** cortex well, because the
sound is intact. It does: auditory and language ROIs barely move when video is
removed (gap ~0.08-0.11). The same removal strongly perturbs visual ROIs. So
the low control gap is not a magnitude floor problem; it is the expected
null arm, and the visual/control contrast is a within-clip paired effect.

## Interpretation nuance

The largest divergence is in **scene / spatial / early-visual** regions
(retrosplenial, PPA, V1), not in face / motion / object regions. Plausible
reading: spatial layout and scene gist are the hardest things for audio alone
to convey, whereas faces and motion often carry an audio correlate (voices,
sound of movement). This gives a clean qualitative claim for a paper figure.

Chart: `output/charts/scenetwin_tribe_roi_localization.png`
(source `.py` alongside).

## Open follow-ups

- Per-timestep gap trajectory (already in `tribe_tensors_load.per_timestep_gap`)
  -> temporal localization: which second of a clip the AD under-describes.
- ~~Does P_AD restore the visual-ROI signal toward P_AV?~~ **TESTED 2026-05-29,
  NEGATIVE and generalizes.** `cursor/research/tribe_roi_closure.py`: closure =
  (gap_A - gap_AD)/gap_A per ROI. Adding the description moves P_AD *away* from
  P_AV in ~70% of clips, even inside visual cortex (scene-PPA helps in only 27%
  external; auditory/language 0-2%). Reason: P_AD adds spoken-language content
  P_AV never had, so it diverges in language/auditory cortex and does not
  reconstruct the visual response. Per-region neural closure is now closed the
  same way scalar closure was ([[research/scenetwin-negative-results]]).

## See Also

- [[research/scenetwin-tribe-role-analysis]]
- [[research/scenetwin-glasser-roi-mask]]
- [[research/scenetwin-roi-gap-analysis]]
- [[research/scenetwin-negative-results]]

## Sources

- TRIBE tensors: `cursor/research/output/tribe_tensors/` (from `tribe_tensors_all78.zip`)
- ROI mask: `output/scenetwin_description_gain/glasser_roi_mask.csv`
