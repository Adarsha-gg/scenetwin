---
title: Frame sampling rewards composition over temporal action
category: research
tags: [live-demo, evaluation, limitations, future-work, poster]
sources: [demo/scenetwin_demo.py, demo/live_pipeline.py, workspace/vatex_eval_clips.json]
created: 2026-05-13
updated: 2026-05-13
---

## TL;DR

SceneTwin's 8 frame sampling pipeline rewards descriptions that match the *static composition* of the sampled frames over descriptions that capture *temporal action* happening across the full clip. Confirmed on two live runs done on 2026-05-13. The benchmark Spearman rho = 0.929 still stands, this is a limitation of frame sampled VLM evaluation in general, not a regression in our numbers.

## Setup

Live demo pipeline runs.

  1. yt-dlp pulls a YouTube clip, trims to 30 s (or VATEX window).
  2. cv2 samples 8 evenly spaced frames.
  3. GPT-4o-mini generates a candidate AD from those frames.
  4. ViT-B-32 scores CLIP visual grounding (mean and top 3).
  5. Claude Haiku 4.5 generates 3 frame grounded ADQA questions and grades the AD against the frames.

Cross model setup avoids the same model grading its own output. ADs are evaluated only against what is visible in the 8 sampled frames.

## Run 1, VATEX clip 12 (in benchmark, TRIBE risk rank 1 of 18)

Sports, volleyball on dirt court, 23.8 s. TRIBE called this clip fragile (all4_fail = 1).

| Source | CLIP mean | CLIP top3 | ADQA |
|---|---|---|---|
| Live AD (auto) | 0.278 | 0.330 | 0.67 (2 of 3) |
| Pro AD (VideoA11y) | 0.239 | n/a | 0.80 (cached) |

Live AD scored higher on CLIP, lower on ADQA. Live AD was generic ("group of children playing volleyball") which CLIP rewards. Pro AD said "communicating in a foreign language" which CLIP does not align with on the frames. Claude grader docked the live AD for missing the fence/mesh barrier.

## Run 2, VATEX clip "Great beer great glass" (out of benchmark)

Food and Cooking, 12 s, beer being poured into a Samuel Adams glass. Held out from the 18 clip benchmark, downloaded fresh from YouTube.

| Source | CLIP mean | CLIP top3 | ADQA |
|---|---|---|---|
| Live AD (auto) | 0.409 | 0.417 | 0.67 (2 of 3) |
| Pro AD (VideoA11y) | 0.357 | 0.389 | 0.33 (1 of 3) |

Live AD beat the pro AD on every metric. Reason found by reading the AD texts.

  * Pro AD: "A person ... carefully *pours* a drink ... liquid *flows slowly, filling* the tall glass."
  * Live AD: "Dark wooden bar with a bottle of Founders Devil Dancer beer and a clear Samuel Adams glass. A hand reaches for the bottle..."

The 8 sampled frames caught the pre-pour moment. Glass is empty in every frame. ADQA's question "Is the Samuel Adams glass empty or contains liquid?" → pro AD's claim of "filling" is not supported by the frames, so the grader correctly docked it. The pro AD describes what happens across the 12 second clip (temporal). The live AD describes what is in the sampled stills (compositional). Frame sampled scoring favors composition.

## What this says about the benchmark

Benchmark headline (locked).

  * Spearman rho = 0.929, 95 percent CI [0.90, 0.96] on 18 clips x 4 tiers.
  * 54 of 54 pairwise tier wins, 15 of 18 fully ordered, permutation p less than 0.0005.
  * CLIP only rho = 0.801, ADQA only rho = 0.789. Ensemble lifts past either with non overlapping CIs.

These numbers are valid for VATEX style clips where the static composition carries most of the visual story (cooking, animals, travel, slow action). They are **less informative for clips with significant motion between frames** (fight scenes, sports highlights, fast cuts). The benchmark categories (Food and Cooking, Pets and Animals, Sports, Travel) are mostly composition heavy, so the framework matches the benchmark. The live demo on action films would show this gap immediately.

## Implications and future work

  1. **Frame count.** Bumping from 8 to 16 or 24 reduces but does not eliminate the gap.
  2. **Scene change sampling.** Pick frames at cut boundaries instead of evenly. Catches the moments that drive the action.
  3. **Video native models.** Gemini 1.5 takes whole MP4s, has true temporal context. Live demo could swap GPT-4o-mini for Gemini for AD generation. But CLIP scoring stays still frame based unless you swap in X-CLIP or ViCLIP.
  4. **Temporal aware ADQA.** Grader receives the full video, not just frames. Pro AD claims about "pouring" or "punching" would then be checkable.

For NJBDA 2026, frame this as a deliberate scope choice: SceneTwin scores **visual coverage** of what is shown, not **temporal narration** of what happens across the clip. The framework's contribution (reference free, two signal ensemble, TRIBE risk forecaster) is independent of which sampling strategy you plug into the front end.

## Poster talking point

> On a held out VATEX clip, our auto generated AD scored higher than the professional AD. Not because it was better, but because the pro AD captured temporal action while frame sampled scoring rewards static composition. Future work: temporal aware evaluation with video native models.

## See Also

  * [[research/scenetwin-adqa-clip-ensemble]]
  * [[research/scenetwin-need-weighted-grounding]]
  * [[research/scenetwin-tribe-failure-forecast]]
  * [[research/scenetwin-improvement-research]]

## Sources

  * Live demo on clip_12 (volleyball, TRIBE rank 1 of 18), 2026-05-13
  * Live demo on FtBS6OZSGMI_000028_000038 (beer pour, held out VATEX), 2026-05-13
  * [demo/live_pipeline.py](../../demo/live_pipeline.py)
  * [output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv](../../output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv)
