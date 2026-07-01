---
title: TRIBE New Findings — Cached-Data Round 3
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - cursor/research/tribe_new_findings_round3.py
  - cursor/research/output/new_findings_round3/
  - output/reports/tribe-review-worksheet.md
---

# TRIBE New Findings — Cached-Data Round 3

Third no-API/no-GPU sweep. This adds ROI/profile checks, fair VLM-rematch analysis, and a review worksheet artifact.

## Finding 13 — ROI/profile evidence is dominated by scene/spatial regions; rare ROI types are underpowered

Dominant visual ROI counts on external clips:

```json
{
  "early_visual_v1": 17,
  "retrosplenial_pos": 30,
  "scene_ppa": 9,
  "lateral_object_loc": 2,
  "body_eba_region": 1,
  "higher_visual_v2v3v4": 1
}
```

| Dominant ROI | n | ADQA fail rate | Ensemble fail rate | mean visual-control gap |
|---|---:|---:|---:|---:|
| retrosplenial_pos | 30 | 0.233 | 0.033 | 0.076 |
| early_visual_v1 | 17 | 0.176 | 0.059 | 0.083 |
| scene_ppa | 9 | 0.000 | 0.000 | 0.178 |
| lateral_object_loc | 2 | 0.000 | 0.000 | 0.418 |
| body_eba_region | 1 | 0.000 | 0.000 | -0.296 |
| higher_visual_v2v3v4 | 1 | 0.000 | 0.000 | -0.016 |

Interpretation: current ROI-derived paper claims should lead with **scene/spatial accessibility gaps**. Body/face/motion/object-specific claims are too sparse in this corpus to stand alone.

Artifacts: `roi_profile_rows.csv`, `roi_dominant_failure_rates.csv`.

## Finding 14 — category-residual gap does not improve external ADQA-failure triage

- Raw `mean_visual_gap` AUC vs ADQA fail: **0.672**
- Category-residual mean gap AUC: **0.646**
- Category z-scored mean gap AUC: **0.684**

Interpretation: category normalization does not strengthen the failure-triage signal here. Keep the raw mean-gap queue unless a later larger corpus says otherwise.

Artifact: `category_residual_gap_rows.csv`.

## Finding 15 — fair transcript-armed VLM rematch confirms: TRIBE is competitive/different, not decisively superior

TRIBE/VLM type disagreement rate across question rows: **0.909**.

Most common type pairings:

```json
{
  "scene_spatial vs motion_action": 110,
  "scene_spatial vs object_body": 50,
  "visual_form vs motion_action": 15,
  "scene_spatial vs face_character": 15,
  "scene_spatial vs scene_spatial": 10,
  "motion_action vs motion_action": 10,
  "scene_spatial vs visual_form": 5,
  "face_character vs motion_action": 5
}
```

| Comparison | Group | videos | questions | mean delta | video-bootstrap 95% CI | W/L/T | sign p |
|---|---|---:|---:|---:|---:|---:|---:|
| tribe_minus_vlm | all | 44 | 220 | 0.020 | [-0.002, 0.043] | 13/5/202 | 0.0481 |
| tribe_minus_vlm | matched | 44 | 62 | 0.065 | [0.017, 0.113] | 8/1/53 | 0.0195 |
| tribe_minus_vlm | unmatched | 44 | 158 | 0.003 | [-0.016, 0.025] | 5/4/149 | 0.5000 |
| tribe_minus_baseline | all | 44 | 220 | 0.005 | [-0.011, 0.020] | 7/4/209 | 0.2744 |
| tribe_minus_baseline | matched | 44 | 62 | 0.008 | [0.000, 0.027] | 1/0/61 | 0.5000 |
| tribe_minus_baseline | unmatched | 44 | 158 | 0.003 | [-0.019, 0.025] | 6/4/148 | 0.3770 |
| vlm_minus_baseline | all | 44 | 220 | -0.016 | [-0.041, 0.007] | 7/12/201 | 0.9165 |
| vlm_minus_baseline | matched | 44 | 62 | -0.056 | [-0.109, -0.008] | 2/8/52 | 0.9893 |
| vlm_minus_baseline | unmatched | 44 | 158 | 0.000 | [-0.026, 0.022] | 5/4/149 | 0.5000 |

Interpretation: this supports the honest wording from the previous log: TRIBE picks different targets and is at least competitive with a transcript-armed VLM, but the superiority claim is not locked. The contribution is brain-grounded routing + non-redundant targets.

Artifact: `necessity_rematch_bootstrap.csv`.

## Finding 16 — review worksheet is now a concrete artifact, not just a product idea

Generated `output/reports/tribe-review-worksheet.md` with the top 25 non-low-gap blind-spot cases. Top case:

```json
{
  "clip_key": "external_iGmGQxox43I_000000_000010",
  "corpus": "external",
  "video_id": "iGmGQxox43I_000000_000010",
  "category": "How-to & Instructional",
  "case_id": "moment_level_authoring",
  "priority_score": "5.964753580129161",
  "window": "0.0-3.6s",
  "why": "Gap is temporally concentrated; spend AD/review budget on the peak window."
}
```

This is directly usable for human/VLM review: each card lists priority score, suggested window, why it was routed, existing fail flags when available, and top router windows.

Artifacts: `output/reports/tribe-review-worksheet.md`, `review_worksheet_rows.csv`.

## Round-3 action changes

1. Lead ROI/profile sections with scene/spatial; mark body/face/motion/object as underpowered.
2. Do not spend time on category-residual thresholds yet.
3. Keep fair VLM-rematch wording conservative: “competitive and different,” not “beats VLM.”
4. Use the generated review worksheet as the next manual/human/VLM validation queue.
