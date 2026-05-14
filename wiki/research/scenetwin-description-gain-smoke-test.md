---
title: "SceneTwin Description Gain Smoke Test"
category: research
tags: [SceneTwin, TRIBE, Description-Gain, MVRR, smoke-test, VideoA11y, VATEX]
sources:
  - output/scenetwin_description_gain/description_gain_results.csv
  - output/scenetwin_description_gain/scenetwin-description-gain-report.md
  - output/scenetwin_description_gain/preds/
  - wiki/research/scenetwin.md
  - wiki/research/scenetwin-revolutionary-implementation-plan.md
created: 2026-05-02
updated: 2026-05-02
---

# SceneTwin Description Gain Smoke Test

## Bottom Line

The 2-clip Colab smoke test was worth running because it caught the failure mode early.

Plain `DescriptionGain` and the first residual metrics are **not strong enough to run as the headline metric alone**. They recover some same-scene richness ordering, but they fail the wrong-content control. The next serious SceneTwin metric should be:

```text
GroundedNeuralScore = visual_grounding_gate * neural_recovery_or_richness_score
```

In practice, that means CLIP/SigLIP/PAC-S must gate out wrong-content descriptions before TRIBE-derived scores are trusted.

## What Ran

Runtime:

- Google Colab L4 GPU
- TRIBE v2 loaded from Hugging Face
- 2 VideoA11y/VATEX overlap clips
- 4 tiers per clip:
  - `tier3_va11y`: VideoA11y AD-style description
  - `tier2_vatex_long`: longest same-scene VATEX caption
  - `tier1_vatex_short`: shortest same-scene VATEX caption
  - `tier0_cross`: cross-category wrong description

Files downloaded locally:

- `output/scenetwin_description_gain/description_gain_results.csv`
- `output/scenetwin_description_gain/description_gain_partial.csv`
- `output/scenetwin_description_gain/scenetwin-description-gain-report.md`
- `output/scenetwin_description_gain/description_gain_tiers.png`
- `output/scenetwin_description_gain/preds/*.npy`
- `output/scenetwin_description_gain/audio/*`
- `output/scenetwin_description_gain/texts/*`

## Timing / Bottleneck Insight

The bottleneck was not just GPU compute. The first clip spent time on:

- model downloads and cache warmup
- audio extraction
- speech/word extraction from audio
- text embeddings
- audio embeddings
- video encoding

For clip 00, `P_AV` took several minutes, including downloads. Video encoding itself took roughly 1:47 on L4. Later steps became faster after model caches warmed.

Implication:

- A100/H100 helps model forward/video encoding, but not downloads, TTS, ASR-like word extraction, ffmpeg, or event construction.
- L4 is a reasonable compromise for this experiment.
- Do not spend more compute on raw TRIBE-only metrics until the scoring formula is fixed.

## Plain Description Gain Result

Metric:

```text
DescriptionGain = cos(P_AV, P_D) - cos(P_AV, P_A)
```

Where:

- `P_AV`: audiovisual TRIBE prediction
- `P_A`: audio-only TRIBE prediction
- `P_D`: description-only TRIBE prediction

2-clip aggregate:

| Tier | Description Gain | AV-desc cosine | AV-audio cosine | Avg words |
|---|---:|---:|---:|---:|
| tier3_va11y | -0.196809 | 0.685539 | 0.882348 | 51 |
| tier2_vatex_long | -0.334480 | 0.547869 | 0.882348 | 22 |
| tier1_vatex_short | -0.368515 | 0.513833 | 0.882348 | 12 |
| tier0_cross | -0.185436 | 0.696912 | 0.882348 | 35 |

Correlation:

| Metric | Value |
|---|---:|
| Spearman rho | 0.0488 |
| Spearman p | 0.9087 |
| Kendall tau | 0.0772 |
| Kendall p | 0.7984 |

Pairwise:

| Comparison | Wins | Total | Accuracy |
|---|---:|---:|---:|
| tier3_va11y > tier2_vatex_long | 2 | 2 | 1.0 |
| tier3_va11y > tier1_vatex_short | 2 | 2 | 1.0 |
| tier3_va11y > tier0_cross | 1 | 2 | 0.5 |

Interpretation:

- Good: DG correctly ranks real AD above same-scene VATEX long/short on both clips.
- Bad: DG fails the wrong-content control. Cross-category mean score beats the real AD mean score.
- Root issue: `cos(P_AV, P_A)` is extremely high (`0.8415`, `0.9232`). Subtracting audio-only makes every DG negative, and rich wrong text can still look close to the audiovisual response.

## Residual Metrics Tested

Post-processing was run on saved tensors; no extra TRIBE inference required.

Metrics:

```text
MVR = P_AV - P_A
MVRR = cos(MVR, P_D)
ARP = cos(P_D, P_A)
UsefulScore = MVRR - 0.25 * ARP
```

Per-row result:

| Clip | Tier | MVRR | ARP | UsefulScore |
|---:|---|---:|---:|---:|
| 0 | tier3_va11y | -0.065329 | 0.770814 | -0.258032 |
| 0 | tier2_vatex_long | 0.074605 | 0.627231 | -0.082202 |
| 0 | tier1_vatex_short | 0.125803 | 0.569917 | -0.016676 |
| 0 | tier0_cross | -0.000253 | 0.685617 | -0.171658 |
| 1 | tier3_va11y | 0.212798 | 0.648342 | 0.050713 |
| 1 | tier2_vatex_long | -0.127514 | 0.555516 | -0.266393 |
| 1 | tier1_vatex_short | -0.066207 | 0.485525 | -0.187588 |
| 1 | tier0_cross | -0.020796 | 0.807156 | -0.222585 |

Mean by tier:

| Tier | MVRR | ARP | UsefulScore |
|---|---:|---:|---:|
| tier3_va11y | 0.073735 | 0.709578 | -0.103660 |
| tier2_vatex_long | -0.026455 | 0.591373 | -0.174298 |
| tier1_vatex_short | 0.029798 | 0.527721 | -0.102132 |
| tier0_cross | -0.010525 | 0.746387 | -0.197121 |

Correlations:

| Metric | Spearman rho | Spearman p | Kendall tau | Kendall p |
|---|---:|---:|---:|---:|
| MVRR | 0.0976 | 0.8182 | 0.0772 | 0.7984 |
| ARP | -0.0976 | 0.8182 | 0.0000 | 1.0000 |
| UsefulScore | 0.0488 | 0.9087 | 0.0772 | 0.7984 |

Pairwise tier3 wins:

| Metric | tier3 > tier2 | tier3 > tier1 | tier3 > tier0 |
|---|---:|---:|---:|
| MVRR | 1/2 | 1/2 | 1/2 |
| UsefulScore | 1/2 | 1/2 | 1/2 |

Interpretation:

- MVRR does not rescue the metric on this smoke test.
- UsefulScore does not rescue it either.
- Clip 00 is especially damaging: the real AD has worse MVRR/UsefulScore than same-scene VATEX captions.
- Clip 01 is promising, but one good clip is not enough.

## Main Insight

TRIBE is still behaving like a semantic/richness brain-response model, not a reliable correctness detector. That repeats the original Sintel hallucination failure in a more realistic setting.

The right interpretation is not:

```text
Counterfactual neural accessibility is dead.
```

The better interpretation is:

```text
Counterfactual neural accessibility needs visual grounding before neural recovery is meaningful.
```

TRIBE-derived metrics may still be useful for:

- richness
- cognitive/description burden
- recovery beyond audio
- experience profile dimensions
- event-boundary alignment

But they should not be trusted to reject wrong scene content by themselves.

## Decision

Do **not** run all 20 clips with raw DG/MVRR as the lead metric.

Do run all 20 only after adding one of these:

1. CLIP-L14 or SigLIP grounding gate
2. PAC-S caption grounding
3. Region/temporal grounding variant
4. Counterfactual perturbation set where failure modes are controlled

## Follow-up Fusion Test

A local fusion script was added after this smoke test:

- `tools/scenetwin_fusion_smoke_test.py`
- `output/scenetwin_description_gain/fusion_smoke_test_results.csv`
- `output/scenetwin_description_gain/fusion_smoke_test_summary.csv`
- `output/reports/scenetwin-fusion-smoke-test.md`

It recomputed CLIP-L14 grounding on the same 2 clips and tested:

- CLIP-L14 alone
- `av_desc_cos`
- `DescriptionGain`
- `MVRR`
- `UsefulScore`
- `CLIP x av_desc_cos`
- `CLIP x DescriptionGain`
- `CLIP x MVRR`
- `CLIP x UsefulScore`
- median-gated CLIP variants

Result:

| Metric | Spearman rho | Pairwise wins | Full-order clips |
|---|---:|---:|---:|
| CLIP-L14 | 0.9759 | 6/6 | 2/2 |
| CLIP x av_desc_cos, global norm | 0.8590 | 6/6 | 1/2 |
| CLIP x av_desc_cos, per-clip norm | 0.9358 | 6/6 | 0/2 |
| CLIP x DescriptionGain, per-clip norm | 0.9358 | 6/6 | 0/2 |
| CLIP x UsefulScore, per-clip norm | 0.3379 | 3/6 | 0/2 |

Interpretation:

- CLIP-L14 alone fully fixes the two smoke-test clips.
- CLIP-grounded richness/fusion fixes the wrong-content control but does not beat CLIP alone here.
- CLIP-grounded `MVRR` / `UsefulScore` still fails on this smoke test.
- Therefore the full 20-clip run is only worthwhile as an honest ablation:
  `CLIP alone` vs `TRIBE-only` vs `CLIP x TRIBE richness/recovery`.

The next scientific question is narrower and sharper:

> Does TRIBE add anything beyond CLIP for same-scene AD quality, after CLIP has already handled wrong-content grounding?

## Next Metric

Recommended immediate metric:

```text
GroundedUsefulScore =
    normalize(CLIP_L14(video, description))
    *
    normalize(UsefulScore)
```

Alternative if UsefulScore remains unstable:

```text
GroundedRichnessScore =
    normalize(CLIP_L14(video, description))
    *
    normalize(cos(P_AV, P_D))
```

This is less revolutionary than pure MVRR, but more honest and likely to work.

## Poster/Paper Framing Update

Do not claim:

> SceneTwin's raw counterfactual TRIBE score solves AD evaluation.

Claim:

> Raw predicted cortical alignment captures description richness but remains vulnerable to semantically rich wrong descriptions. SceneTwin therefore uses visual grounding as a necessary correctness gate and TRIBE-derived neural scores as a second-stage accessibility/richness/recovery signal.

If later grounded residual scores outperform CLIP alone on same-scene AD quality, then the stronger revolutionary claim becomes plausible again.

## Next Work

1. Add CLIP-L14 scores to the Colab output rows.
2. Compute `GroundedUsefulScore = norm(CLIP) * norm(UsefulScore)`.
3. Compare against:
   - CLIP-L14 alone
   - DG alone
   - MVRR alone
   - UsefulScore alone
   - `CLIP x DG`
   - `CLIP x UsefulScore`
4. Only then run all 20 clips.
5. Build counterfactual descriptions:
   - audible-only
   - object-only
   - wrong event order
   - wrong emotion/social intent
   - wrong spatial layout
   - hallucinated
6. Validate against ADQA or real human/BLV/pro describer ratings if available.
