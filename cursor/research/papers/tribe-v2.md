# TRIBE v2 — Tri-modal Foundation Model for Neuroscience (Meta 2026)

**Source:** [arxiv_2605.04326.pdf](sources/arxiv_2605.04326.pdf) · See also `cursor/research/tribe-v2-deep-dive.md`, [[research/scenetwin-tribe-role-analysis]]

## What the paper does

TRIBE v2 (Defossez et al., Meta 2026) is a deep multimodal brain encoding model that predicts fMRI BOLD responses to naturalistic stimuli. It unifies three previously-separate paradigms (vision-only, audio-only, language-only encoders) into a single Transformer trained on **1000+ hours of fMRI from 720 subjects** watching/listening to naturalistic content. Architecturally it integrates frozen state-of-the-art feature extractors — **LLaMA-3.2** for text, **V-JEPA2** for video, **Wav2Vec-BERT** for audio — and maps them onto the cortical surface (fsaverage5 mesh) via a learned projection.

The contribution most relevant to our work is in-silico counterfactual ablation: given a video, TRIBE can predict brain response to (i) the full audio+visual clip (P_AV), (ii) audio-only (P_A) by zeroing the visual stream, (iii) text-only (P_AD) by feeding AD text through the language path. Differences between these predictions identify *which modality carries which information* at each time step.

## Why this matters for AD evaluation

Audio description exists because audio alone does not carry all visual information for blind/low-vision viewers. Operationalizing that statement at clip-level requires measuring **what audio leaves out**. Existing reference-free AD metrics (LLM-AD-Eval, ADQA, etc.) measure whether the AD text matches what's *in the video*, but they do not measure whether the AD is *needed* — i.e., whether the audio track already conveys the visual content. TRIBE's modality counterfactual gives a direct measurement of this.

We define two derived signals on top of TRIBE's counterfactual capability:

- **accessibility_gap** = 1 − cos(P_AV, P_A). High = video carries visual information that audio does not. This is the BLV viewer's residual need.
- **description_gain** = cos(P_AV, P_AD) − cos(P_AV, P_A). High = AD text restores brain-predicted response toward the full AV condition. This is the AD's measurable contribution.

Both signals come from the same encoder; they are not separate models. The encoder is frozen; we extract per-clip features without fine-tuning.

## What we agree with

1. **Counterfactual modality ablation is the right primitive** for asking "when is AD needed?" Most prior AD-evaluation work either assumes AD is always needed (then scores its quality) or routes by heuristic (speech density, scene complexity). TRIBE makes need a measured quantity.
2. **fMRI training is broader than text-language alignment.** LLM-AD-Eval-style metrics anchor to one professional reference; TRIBE anchors to 720 brains. Different stability under distribution shift, in principle.
3. **Cortical-surface output is interpretable.** Visual cortex activation can be inspected; we use only the global cosine but the option exists.

## What we think is wrong / limited

1. **fMRI predictivity ≠ AD utility for BLV viewers.** TRIBE is trained on subjects who are watching the video — not on blind/low-vision subjects listening with AD. We are extrapolating from a "sighted brain watching video" encoder to "what a blind viewer needs from AD." This extrapolation is reasonable as a *risk forecaster* (which clips contain visual information that audio omits) but cannot directly score AD quality.
2. **Text injection ≠ TTS AD delivery.** TRIBE's language path uses written text fed through LLaMA. Real AD is spoken at narration speed with prosody and is interleaved with the audio track. We approximate by feeding the AD text alone (no audio mixing); this captures *what was said* but not *when and how*.
3. **No audio-only experiments in the paper.** TRIBE v2 is trained on full naturalistic stimuli. We use its prediction on the extracted audio track as P_A; the paper does not explicitly test whether the model preserves brain alignment under pure-audio inputs. Two of our 18 clips returned `audio_only_ok=False` during the Colab run (silent audio extraction failed); the rest produced valid P_A.
4. **Live TRIBE infrastructure is heavy.** TRIBE v2 + LLaMA-3.2 + V-JEPA2 + Wav2Vec-BERT requires ~600 MB checkpoint plus a GPU runtime. Cannot run inline with our metric pipeline; must be batched. This is acceptable for failure forecasting (computed once per clip) but rules out real-time deployment.

## Our alternative

We use TRIBE in two complementary roles:

### Role 1 — Binary failure-triage flag (locked, paper-ready)

Need-window features derived from TRIBE (`mean_standard_slot_score`, `mean_speech_density`, `high_need_seconds_frac`, `tribe_pressure`) form a binary classifier for the `all4_fail` event (all-4-judge ADQA ensemble fails full ordering). On the 18-clip benchmark:

- ROC AUC = **1.00**
- Recall @ 2/18 (top of review queue) = **100%**
- Review budget required = **11.1%**
- Hypergeometric p = 0.0065, Bonferroni-corrected p = 0.065

This is a deployable claim: with the metric alone, deploying SceneTwin on unseen content requires reviewing 100% of outputs to be safe against severe failures; with the TRIBE triage flag, 11.1% review captures all observed catastrophic failures.

### Role 2 — Continuous calibration signal (provisional, 2026-05-29 measurement)

We tested whether new TRIBE counterfactual features predict per-clip continuous ensemble noise (`within_clip_rho`). On n=18:

| Feature | r vs within_clip_rho | p |
|---|---:|---:|
| accessibility_gap | -0.453 | 0.059 |
| alignment_cosine | -0.392 | 0.108 |
| description_gain | -0.192 | 0.444 |

The accessibility_gap signal is **33% stronger** than the maximum correlation observed across 12 prior TRIBE need-window features (|r| = 0.342, all p > 0.16). At n=18 the minimum detectable r at α=0.05, power=0.80 is approximately 0.45 — our observation sits at the detection floor. The story is *not* locked at p<0.05 yet, but the direction is clear and the effect size warrants a 60-clip external re-run for power.

We additionally find that `description_gain` matches the existing top forecast feature `max_need` at **AUC = 1.000** on the `low_tier3_margin` target. This is the cleanest paper claim from the counterfactual proxy: a theoretically motivated brain-counterfactual feature replaces a slot-score heuristic at parity AUC.

## What we recommend the paper claim

Conservative (Paper A v1, current evidence):

> We integrate TRIBE v2 as a brain-aligned failure-triage flag. The flag forecasts severe ranking failures (all-judge ADQA disagreement) at AUC = 1.00 with 100% recall on the 18-clip benchmark, enabling deployment at an 11% review budget. We additionally compute a paper-aligned counterfactual proxy (accessibility_gap, description_gain) and report it as an emerging calibration signal that reaches the detection floor at n=18 (r = -0.453, p = 0.059) and warrants external 60-clip replication to lock at p < 0.05.

Aggressive (Paper A v2 after external re-run, conditional on r holding):

> Beyond binary failure forecasting, we show that accessibility_gap — a direct measurement of what the audio track leaves out, derived from TRIBE's counterfactual brain-response prediction — correlates negatively with continuous ensemble ranking quality (r = X, p < 0.05 on external n=60 corpus). This places TRIBE structurally in our metric: clips where audio carries less visual information also produce noisier ensemble rankings, and the brain-aligned counterfactual flags both phenomena from the same neural signal.

## Implementation status

| Component | Status |
|---|---|
| 18-clip in-bench counterfactual run | ✓ complete (2026-05-29) |
| 60-clip external counterfactual run | pending (Colab notebook ready) |
| TRIBE need-window failure forecast (existing) | ✓ AUC = 1.00, recall@2 = 100% |
| Cortical surface visualization | optional, deferred |
| `output/scenetwin_timing_20clip/clip_scores/need_weighted_grounding_results.csv` | ρ = 0.733 |
| `cursor/pipeline/external_clip_pipeline.py` | motion+speech proxy (legacy) |

## How this fits Cluster B of the corpus

TRIBE sits in our [[research/scenetwin-paper-corpus]] cluster B (narrative / temporal). Together with CoAD (StoryRecall), CA3D (event detection), and VideoA11y (timing rubrics), it asks **"when does the AD need to convey what?"** rather than the cluster A question **"does the AD text match the video?"** The two clusters are complementary, not competing: A is what we report at headline ρ; B explains why ranking failures concentrate where they do.

## Open questions for follow-up

1. Does accessibility_gap correlate with within_clip_rho on the 60-clip external corpus? (Power analysis says: if effect size r=-0.45 is stable, n=60 will yield p << 0.05.)
2. Does description_gain stabilise across distributions, or is the 1.000 AUC on low_tier3_margin specific to the 18-clip set?
3. Can we use accessibility_gap as a *gating* feature for routing different ADQA question types (visual vs narrative)?
4. Are there genres where TRIBE's audio path is misleading (e.g. music video clips where the audio is the content)? Our 2 audio-only-failed clips were both Sports/Animals — worth probing.

## Takeaway

TRIBE answers **what audio leaves out for a sighted brain**; ADQA and CLIP answer **whether the AD text matches the video**. The combination is necessary for deployable AD evaluation: ADQA+CLIP for ranking, TRIBE for review triage (and emergently for calibration). Without the brain-aligned forecaster, ranking metrics are correct but unsafe to deploy on unseen content; with it, a small targeted review budget catches the failures that ranking alone would silently report as high scores.
