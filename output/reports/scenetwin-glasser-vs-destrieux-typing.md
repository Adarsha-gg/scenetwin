---
title: "SceneTwin Glasser vs Destrieux Typing Comparison"
category: research
tags: [SceneTwin, TRIBE, ROI, atlas, validation, Glasser, Destrieux]
created: 2026-05-03
updated: 2026-05-03
sources:
  - output/scenetwin_description_gain/phase2_typing_validation_destrieux.csv
  - output/scenetwin_description_gain/phase2_typing_validation_glasser.csv
  - output/scenetwin_description_gain/phase2_typing_confusion_glasser.csv
  - output/scenetwin_description_gain/glasser_roi_mask.csv
  - output/scenetwin_description_gain/destrieux_proxy_roi_mask.csv
---

# SceneTwin Glasser vs Destrieux Typing Comparison

## What changed

Replaced the Destrieux anatomical proxy ROI mask with the Glasser HCP-MMP1.0
functional parcellation (resampled to fsaverage5 via FreeSurfer's nested
subject icosahedron). Re-ran ROI gap curves, content typing, and Phase 2
pro-AD agreement validation.

## Headline

| Metric | Destrieux | Glasser | Chance |
|---|---:|---:|---:|
| Windows scored | 21 | 21 | — |
| Pro-AD vs TRIBE agreement | 4.8% | **19.0%** | 16.7% |
| High-need windows agreement | 0.0% | **14.3%** | 16.7% |
| ROI vertex count (`scene_ppa`) | 1035 | 194 | — |
| ROI vertex count (`motion_mt`) | 1041 | 212 | — |
| ROI vertex count (`face_ffa`) | 223 | 264 | — |

The functional atlas pulled overall agreement up about 4x (4.8% → 19.0%) and
high-need agreement up from zero (0.0% → 14.3%). But 19.0% is barely above
the 16.7% uniform-random floor, and 14.3% is still below it.

## What this means

The atlas was *part* of the problem, not all of it.

Destrieux ROIs were genuinely too coarse: `scene_context_ppa_proxy` covered
the entire parahippocampal gyrus (1035 vertices), so any time-step with broad
visual response would get typed `scene_spatial`. Glasser PHA1+PHA2+PHA3 is
194 vertices — the actual functional parahippocampal place area. Same logic
for motion (5x tighter) and lateral object cortex (8x tighter). That fix
moved the needle.

But not enough. The systematic bias is still visible in the confusion matrix:

| pro AD ↓ / TRIBE → | face_char | motion | object | scene | form |
|---|---:|---:|---:|---:|---:|
| **face_character** | 2 | 0 | 1 | 4 | 1 |
| **motion_action** | 2 | 1 | 0 | 3 | 0 |
| **object_body** | 4 | 0 | 1 | 1 | 0 |

Pro-motion windows still mostly get TRIBE-typed as scene_spatial or
face_character. Pro-object windows still mostly get face_character. The
atlas swap helped scene/face slightly but did not fix the motion blind spot.

## Why the atlas swap was not enough

Two real causes likely remain:

1. **TRIBE's audio-vs-AV gap is not motion-selective at this resolution.**
   Even with tight functional MT/MST/FST, the AV-A residual on those vertices
   may not be large enough to dominate against PPA/RSC residuals which fire on
   any visually-rich frame.
2. **Pro-AD time-alignment is approximate.** With 3-5 sentences over a 9-second
   clip and no per-sentence timestamps, the proportional alignment misses
   asynchronous AD: pros often write the AD slightly before or after the
   action it describes. Some "disagreements" may be the validation lining up a
   pre-action sentence to a peak-action window.

Both effects matter. Without a larger clip set with timed pro AD, we cannot
separate them.

## Decision

Glasser is the right atlas going forward — it is functionally defined,
significantly tighter, and produces better agreement than Destrieux. Keep it
as the SceneTwin default.

But Phase 2 (TRIBE-in-loop with this typing as the controller signal) is still
not justified. 19% agreement means the controller would steer the LLM toward
the wrong content type ~80% of the time on high-need windows. That makes the
closed loop worse than no loop.

## What to do next

Three honest options.

### Option A — Scale the experiment before declaring outcome
Run the typing + validation pipeline on all 20 VideoA11y/VATEX overlap clips
with timed pro AD where available. n=21 windows on 2 clips is too small to
draw conclusions in either direction. The systematic biases above might
disappear or sharpen; either result is informative.

### Option B — Drop typing, keep timing
Reframe the project around what already works: the TRIBE accessibility-gap
need curve (ρ=0.976, p=0.002 on need-weighted CLIP) plus OCR coverage. Drop
per-ROI content typing from the headline. NJBDA poster is achievable today
on this story, and it is the version where every claim survives a null test.

### Option C — Replace lexicon-based pro AD scoring with an LLM classifier
The "pro AD dominant type" comes from a lightweight word-counter. A real
classifier (Claude/GPT prompt that scores each AD sentence on the 6 content
dimensions) would settle whether the lexicon is the failure point. If the
LLM agrees with the lexicon, the typing is broken. If the LLM disagrees,
the lexicon is broken.

C is the cheapest pivot before deciding between A and B.

## Files

- `output/scenetwin_description_gain/glasser_roi_mask.csv`
- `output/scenetwin_description_gain/roi_gap_curve_glasser.csv`
- `output/scenetwin_description_gain/roi_content_typing_windows_glasser.csv`
- `output/scenetwin_description_gain/phase2_typing_validation_glasser.csv`
- `output/scenetwin_description_gain/phase2_typing_confusion_glasser.csv`
- `tools/scenetwin_build_glasser_roi_mask.py`
