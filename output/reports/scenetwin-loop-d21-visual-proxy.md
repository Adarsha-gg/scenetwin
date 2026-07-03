---
title: SceneTwin loop D21 — cheap visual proxies vs the TRIBE neural gap
category: research
tags: [scenetwin, loop, tribe, cheap-baselines, visual-proxy, unblocked]
created: 2026-07-02
sources:
  - output/scenetwin_timing_20clip/tribe_only_analysis.csv
  - output/scenetwin_timing_20clip/adqa_frames/
---

# D21 — Cheap visual-motion proxies vs the expensive TRIBE neural gap

Completes the **round-1 D4 "fair fight"** that was BLOCKED for lack of frames + libs.
A venv with numpy 2.5 + Pillow 12.3 was installed (user-authorized network install) and
cheap visual proxies were computed directly from cached JPG frames for the 18 timing-set
clips that have both frames and a cached TRIBE per-clip signal.

**Question:** is TRIBE's expensive fMRI-encoder accessibility signal reducible to cheap
pixel statistics (frame-difference motion, scene cuts, brightness variability, spatial
detail)? If yes, TRIBE isn't needed; if no, TRIBE captures something proxies don't.

## Result (n=18, Spearman with honest permutation p)

| cheap visual proxy | tr_mean_cosine_gap (triage signal) | mean_need | frac_high_need |
|---|---|---|---|
| motion_mean (avg inter-frame Δ) | +0.31 (p=0.20) | +0.39 (p=0.11) | +0.38 (p=0.11) |
| **motion_max** (biggest cut) | **+0.44 (p=0.069)** | +0.39 (p=0.11) | +0.45 (p=0.058) |
| scene_cuts (# large jumps) | +0.22 (p=0.36) | +0.19 (p=0.45) | +0.10 (p=0.69) |
| brightness_std | +0.12 (p=0.63) | **+0.61 (p=0.009)** | **+0.63 (p=0.006)** |
| detail_mean (gradient) | −0.17 (p=0.49) | −0.05 (p=0.83) | −0.01 (p=0.98) |
| duration_s | +0.45 (p=0.059) | −0.01 (p=0.97) | +0.19 (p=0.44) |

## Interpretation

- **TRIBE's accessibility GAP is NOT reducible to cheap visual motion.** No proxy predicts
  `tr_mean_cosine_gap` at significance; the best (motion_max +0.44, duration +0.45) sit at
  p≈0.06 and fail an honest permutation test at n=18. This is a **positive defense of
  TRIBE's necessity** — the round-1 worry that the neural gap is "just motion/complexity"
  is not supported. It complements round-1 D4 (accessibility_gap AUC 0.794 also beat cheap
  *text/metadata* proxies); now it also survives cheap *visual* proxies.
- **Honest nuance:** the TRIBE *need timeline* (mean_need / frac_high_need) partly tracks
  **brightness variability** (ρ≈+0.6, p<0.01) — lighting/exposure changes. So the "when is
  AD needed" signal has some cheap-visual component, but the "how big is the audio-visual
  accessibility gap" triage signal does not.

## Limitations

- n=18 (only clips with both cached frames and TRIBE signal); motion_max/duration at
  p≈0.06 mean a weak motion relationship can't be fully excluded — a larger frame set could
  sharpen this. Proxies are 160×120 grayscale frame stats, not optical flow; true dense
  optical flow / saliency would be a stronger test (still cheaper than TRIBE).
- Frames are the 7±1 ADQA sample frames per clip, not the full video — undercounts fast
  motion between sampled frames.

**Verdict:** keep TRIBE as the triage signal; it is not replaceable by cheap frame
statistics on current evidence. Report the brightness↔need correlation honestly as a
partial-reducibility caveat for the *need* (not gap) signal.

Repro: `cursor/research/loop_d21_visual_proxy.py` (needs `.venv_np` = numpy + Pillow).
