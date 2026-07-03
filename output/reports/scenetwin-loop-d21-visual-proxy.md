---
title: SceneTwin loop D21 — cheap visual proxies vs the TRIBE neural gap (n=57)
category: research
tags: [scenetwin, loop, tribe, cheap-baselines, visual-proxy, unblocked]
created: 2026-07-02
updated: 2026-07-02
sources:
  - cursor/research/output/parallel_research/cheap_baselines/external_features.csv
  - cursor/research/output/ext60_frames/ (downloaded)
---

# D21 — Cheap visual-motion proxies vs the expensive TRIBE neural gap (n=57)

Completes the **round-1 D4 "fair fight"** at the primary external scale. Installed
yt-dlp + ffmpeg (user-authorized), downloaded the 60 external clips by parsing YouTube
id + timestamps from each clip id, extracted 8 frames each, and computed cheap visual
proxies with numpy+Pillow. **57/60 clips** succeeded (3 unavailable on YouTube:
2kJxrcNRS9w, A0e7Z55s8pE, 1HUWWCLza0w). Joined to `external_features.csv`, which has
`accessibility_gap`, `mean_visual_gap`, `mean_scene_spatial_gap`, and the real
`adqa_fail` label for all clips.

## (1) Do cheap proxies reproduce the neural signal? Spearman (perm p)

| proxy | accessibility_gap | mean_visual_gap | mean_scene_spatial_gap |
|---|---|---|---|
| motion_mean | −0.21 (0.108) | **−0.38 (0.004)** | **−0.42 (0.002)** |
| motion_max | −0.11 (0.416) | −0.27 (0.039) | −0.31 (0.022) |
| scene_cuts | −0.20 (0.124) | **−0.37 (0.005)** | **−0.42 (0.002)** |
| brightness_std | −0.06 (0.65) | −0.02 (0.90) | −0.03 (0.85) |
| detail_mean | −0.09 (0.53) | −0.28 (0.035) | −0.30 (0.023) |
| duration_s | n/a (constant 10s) | — | — |

## (2) Do cheap proxies predict real ADQA failure? AUC vs the neural baseline

| signal | AUC(adqa_fail) |
|---|---|
| **accessibility_gap (NEURAL)** | **0.796** |
| detail_mean | 0.628 |
| motion_mean | 0.583 |
| motion_max | 0.566 |
| brightness_std | 0.538 |
| scene_cuts | 0.517 |
| duration_s | 0.500 (constant) |

## Interpretation

- **The TRIBE triage signal is not replaceable by cheap visual proxies.** For predicting
  actual ADQA failure — the deployable target — `accessibility_gap` (0.796) beats every
  cheap frame proxy by ≥0.17 AUC. Combined with round-1 D4 (it also beat cheap
  text/metadata proxies), TRIBE survives the fair fight on both text and visual cheap
  baselines **at the full external scale**.
- **New finding, only visible at scale:** raw visual motion / scene-cut density
  **negatively and significantly** predicts the TRIBE visual gap (ρ≈−0.4, p≈0.002–0.005).
  High-motion clips have *lower* AV-vs-A gap — plausibly because continuous action is
  redundant/trackable from audio+context, whereas static, detail-dense scenes open the
  largest accessibility gaps. This is a genuine, sign-stable relationship, not noise.
- **The neural gap itself (`accessibility_gap`)** shows only a weak, non-significant
  negative tie to motion — it is *not* a motion statistic in disguise.

## Why this supersedes the earlier n=18 run

The first pass used the only frames then cached (18 timing-set clips, disjoint from these
60). It reported motion_max **+0.44** vs `tr_mean_cosine_gap` — a weak *positive* trend.
At n=57 the motion relationship is **negative and significant** for the mean gaps: the
small sample was both underpowered and **wrong-signed**. Treat n=57 as canonical; the n=18
numbers are retained only as a cautionary example of small-sample instability.

## Limitations

- n=57 (3 clips unavailable on YouTube); 8 sampled frames/clip at 160×120 grayscale —
  frame-difference stats, not dense optical flow (a stronger but still-cheap proxy).
- `duration_s` is constant (10s) for the external set, hence uninformative here.
- `adqa_fail` has 10 positives; AUCs are directional with wide CIs, but the ≥0.17 gap
  between the neural signal and every visual proxy is consistent.

Repro: `cursor/research/loop_d21b_fetch_frames.py` (download+extract) then
`cursor/research/loop_d21c_visual_proxy_n60.py` (needs `.venv_np` = numpy+Pillow;
`.venv_np` + yt-dlp/ffmpeg for the fetch). Frames in `cursor/research/output/ext60_frames/`.
