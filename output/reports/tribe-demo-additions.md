---
title: "TRIBE demo additions"
category: planning
tags: [scenetwin, tribe, demo, design]
created: 2026-05-14
---

# TRIBE demo additions

Goal: make TRIBE feel vital in the demo. Right now the TRIBE page shows the
failure forecast and a brain map. The data files contain four more findings
that no other module (CLIP, ADQA) can produce. This doc lists them, where
to slot each one into the existing TRIBE page, and the data wiring needed.

## What is already in the TRIBE page

File: `web/pages/tribe.jsx`. API: `api/server.py:/api/tribe-risk`.

Currently shown:

- 4 stat cards: Recall@2, p value, Risk clips, Review budget.
- Big brain map image for the selected clip, swappable.
- Sidebar: 18 clips ranked by `risk_score`, click to select.
- Selected clip card: risk_score, mean_need, high_need_seconds_frac,
  tier3_margin, tribe_route, quality_risk, pro AD text.

What the API already returns but the UI does not use:

- `correlations[:8]` from `tribe_native_correlations.csv`. This is the
  biggest one. Includes ro = -0.751 p = 0.0003 for
  `mean_standard_slot_score` vs `all4_mean_full_order`.

## New TRIBE-only findings to surface

Five candidates, ranked by demo impact.

### 1. Judge agreement correlation (ro = -0.751, p = 0.0003)

**The headline that is sitting unused.** TRIBE pressure inversely predicts
whether the 4-judge ADQA panel agrees on tier order. This is the strongest
statistically clean TRIBE-only signal in the dataset.

- Source: `output/scenetwin_timing_20clip/tribe_native/tribe_native_correlations.csv`
- Already in API response under `correlations`, not rendered.
- Where to put it: top of the TRIBE page, as a fifth stat card or a
  one-line subtitle under the existing 4 cards. Format:
  `ro = -0.75, p = 0.0003 (TRIBE pressure vs ADQA judge agreement, n=18)`.
- Selling line: "TRIBE predicts how reliable your AD audit will be from
  video and audio alone, before any AD is written."

### 2. Per-clip cortical fingerprint (the brain story)

For each clip with a full TRIBE tensor, we have per-ROI accessibility
gaps on the Glasser HCP-MMP1.0 atlas. Retrosplenial cortex (scene
context) shows the biggest gap, then scene PPA, then early V1. Motion
and auditory ROIs are near zero.

- Source: `output/scenetwin_timing_20clip/tribe_only_per_roi.csv`
- Columns: `clip_idx, roi, av_a_gap_cos, av_a_residual_norm_per_t`
- 10 ROIs: auditory_control, body_eba_region, early_visual_v1, face_ffc,
  higher_visual_v2v3v4, language_control, lateral_object_loc,
  motion_mt_complex, retrosplenial_pos, scene_ppa.
- Caveat: only 2 clips (00 and 01) have full tensors. Frame this honestly
  as a "deep dive" for the 2 fully reconstructed clips, not a 20 clip
  result.
- Where to put it: under the selected clip card, a small horizontal bar
  chart of per-ROI cosine gap. Highlight retrosplenial and PPA.
- API change: extend `/api/tribe-risk` clip entries with
  `per_roi: [{roi, cos_gap}]` for the 2 clips that have it; null for
  the rest.

### 3. AD need curve over time

TRIBE outputs a per-1.49s-TR need score across the entire clip,
plus 3s coarse windows labeled `low_ad_need / standard_ad_slot /
extended_or_integrated_ad / inspect_visual_event`. This is the
timing story that nothing else in the stack produces.

- Sources:
  - `output/scenetwin_timing_20clip/need/neural_description_need_curve.csv`
    (per-TR, fine grained)
  - `output/scenetwin_timing_20clip/need/coarse_need_windows.csv`
    (3s windows with labels)
- Where to put it: dedicated panel on the selected clip card, below
  the 4 stat tiles. A simple area chart of need vs time, with the
  coarse-window labels as colored bands underneath.
- The demo already has `need_curve_plot` rendered server-side as a
  matplotlib Figure in `demo/scenetwin_demo.py:159`. For the web,
  expose the raw rows from the API and render with the existing
  chart library on the frontend.
- API change: add `need_curve: [{t, start_s, need_score}]` and
  `coarse_windows: [{start_s, end_s, recommendation}]` per clip.

### 4. AD-type routing as a visual badge

The data has `tribe_route` for every clip: `extended/integrated AD
likely needed` (12 clips), `standard AD priority` (2), `low/normal
AD pressure` (5). Currently shown as plain text in a card.

- Source: already in `/api/tribe-risk` clip rows.
- Where to put it: replace plain text with a colored badge at the
  top of each clip in the sidebar list, so the user sees the
  routing at a glance. Three colors:
  - extended/integrated -> red/accent
  - standard -> amber
  - low/normal -> green
- This costs zero new data and turns a hidden field into a strong
  visual signal.

### 5. Speech density story

`mean_speech_density` has AUC 0.94 for predicting full-order failures
(inverse direction: silent clips are at-risk). This is a great
secondary signal because it is easy to explain: "when the clip has
no speech, AD is doing all the work, so it is harder to score."

- Source: `tribe_failure_forecast_feature_scores.csv` row 3
  (`mean_speech_density, low, 0.9375, 0.5833`).
- Where to put it: small badge next to the risk score in the
  sidebar list, e.g. `silent` or `talky` chip when speech density
  is < 0.3 or > 0.8.
- API change: add `mean_speech_density` to clip rows. Already in
  `tribe_failure_forecast.csv`, just needs to be passed through.

## Suggested cut

If we ship two of the five, do **#1 + #2**. Together they tell the
story: TRIBE predicts evaluator fragility statistically, and shows
you where in the brain the gap lives. Everything else is gravy.

If we ship three, add **#3** (need curve over time). That is the
single most "demo-able" visual: a timeline graph with TRIBE-labeled
peaks.

## Data wiring checklist

All five shipped on 2026-05-14.

API extensions in `/api/tribe-risk` (`api/server.py:221`):

- [x] Pass through `mean_speech_density` per clip.
- [x] `correlations[:8]` returned; new `headline_correlation` field
  surfaces the ro = -0.751 / p = 0.0003 finding directly.
- [x] `per_roi` per clip (10 ROIs for clips 00 and 01, empty for the rest).
- [x] `need_curve` (per-TR rows) and `coarse_windows` (3s bands) per clip.

Frontend changes in `web/pages/tribe.jsx`:

- [x] Fifth stat card for ro = -0.75 judge-agreement finding, plus
  an accent-bordered callout explaining what it means.
- [x] Per-clip ROI horizontal bar chart in the selected clip card,
  with a fallback message for clips without full tensors.
- [x] Inline SVG need curve over time with colored coarse-window
  bands underneath (extended / standard / inspect / low).
- [x] Colored route badge ("extended AD" / "standard AD" /
  "low pressure") on every sidebar row.
- [x] Speech density chip ("silent" / "talky" / "mixed") on
  sidebar rows and as a fifth selected-clip stat tile.

Demo (Gradio) changes in `demo/scenetwin_demo.py`:

The Gradio app already shows the need curve plot via
`need_curve_plot`. To match the web TRIBE page, mirror only the
items the web side adopts so the two stay in sync.

## What I am intentionally not adding

- The need-weighted CLIP grounding ro = 0.976 lift result. n = 2.
  Too small a sample to claim a lift; would not survive a reviewer.
- The TRIBE policy validation / LOOCV scores. They are real but
  paragraph-heavy, not visual.
- The closure metric. Killed on 2026-05-11, do not resurrect.

## Source files referenced

- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv`
- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast_summary.csv`
- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast_feature_scores.csv`
- `output/scenetwin_timing_20clip/tribe_native/tribe_native_correlations.csv`
- `output/scenetwin_timing_20clip/tribe_only_per_roi.csv`
- `output/scenetwin_timing_20clip/need/neural_description_need_curve.csv`
- `output/scenetwin_timing_20clip/need/coarse_need_windows.csv`
