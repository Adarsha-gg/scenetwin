# TRIBE v2 — how it works (for SceneTwin)

Sources: [Meta blog](https://ai.meta.com/blog/tribe-v2-brain-predictive-foundation-model/), [arXiv 2605.04326](https://arxiv.org/html/2605.04326), [GitHub facebookresearch/tribev2](https://github.com/facebookresearch/tribev2)

## Architecture

TRIBE v2 is a **tri-modal brain encoding foundation model**:

| Modality | Encoder |
|----------|---------|
| Video | V-JEPA2 |
| Audio | Wav2Vec-BERT |
| Text | LLaMA 3.2 (TTS + word timings for naturalistic input) |

A unified **Transformer** maps multimodal latents → **fsaverage5 cortical mesh (~20k vertices)**.
Trained on **720 subjects, 1000+ hours fMRI** (CNeuroMod, BoldMoments, Lebel2023, Wen2017 train; NNDb, LPP, Narratives, HCP test).

## Key mechanics SceneTwin must respect

1. **Hemodynamic lag**: predictions are offset **5 seconds** into the past relative to stimulus.
2. **TR resolution**: ~1.49s per fMRI time point (matches our need curves).
3. **Average subject**: HuggingFace weights predict group-mean brain, not individual fMRI.
4. **Counterfactual modalities**: the paper ablates video/audio/text separately — this is exactly our `P_AV`, `P_A`, `P_AD` gap story.
5. **In-silico experiments**: GLM contrasts on predicted time series recover FFA, PPA, EBA, language network — validates TRIBE for **routing**, not literal pixel attention maps.

## What TRIBE is good for in SceneTwin

| Use | Status |
|-----|--------|
| Pre-scoring risk forecast (judge fragility) | **Validated** ρ=-0.75, recall@2=100% |
| AD need timing (per-TR gap + speech) | **Surviving** contribution |
| Description Gain (P_AD restores P_AV−P_A) | **Killed** — unstable on short clips |
| ROI content typing for closed-loop AD | **Blocked** — 4.8–19% agreement |
| Literal “brain score” for AD text quality | **Wrong framing** — TRIBE is not ADQA |

## Efficiency opportunities

- **Unimodal ablation**: paper shows video-only encodes occipital; audio-only temporal; text semantic/PFC. SceneTwin could use **cheap unimodal proxies** before full TRIBE.
- **Zero-shot group model**: no per-subject finetune needed for routing (finetune only for individual clinical use).
- **Linear baseline gap**: TRIBE beats Deep FIR but margins vary by region — **speech density + CLIP** may suffice for 80% of clips.

## SceneTwin experiments to run from this doc

1. Test HRF lag sensitivity on saved tensors (0 vs 2.5 vs 5s) — already partially done.
2. Unimodal proxy sweep: `speech_density`, `frame_motion`, `clip_top3` vs full TRIBE need.
3. Counterfactual Description Gain with **video+audio** as baseline instead of audio-only.
4. ADQA **critical-only** grades as alternative label — tier order may change.
