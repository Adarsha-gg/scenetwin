# MAVERIX — Multimodal Audio-Visual Evaluation (2025)

**Source:** [arxiv_2503.21699.pdf](sources/arxiv_2503.21699.pdf)

## Why they did it

MLLM benchmarks test vision **or** audio separately; humans integrate both. MAVERIX has 2,556 questions on 700 videos where **both modalities are necessary** (agentic scenarios). SOTA ~64% vs humans ~93%.

## What we agree with

- AD audit on **silent-frame CLIP** fails when answer requires **sound source disambiguation** (who spoke off-screen, which object made noise).
- A **modality-dependence gate** should up-weight AV metrics vs VT-only on those clips.

## What we think is wrong / limited

1. **QA benchmark for models**, not for AD text ranking — we adapt as clip-level “needs audio” flag.
2. **700 curated videos** — our 18 clips are mostly visual-dominant VATEX.
3. Full MAVERIX eval needs their question set per clip — we use **heuristic gate** (speech density + off-screen cues in pro AD).

## Our alternative

- `maverix_modality_dependence.py` + `discover/maverix_gate.py` — binary or continuous gate per clip.
- Fusion: `score = vt * (1 + α·gate) + adqa` — only boosts AV-sensitive clips.
- For external clips with rich audio, gate should correlate with **tier0_cross** failures (audio-only leakage in AD).

## Implementation

| Script | Status |
|--------|--------|
| `cursor/methods/maverix_modality_dependence.py` | Gate prototype |
| `cursor/discover/maverix_gate.py` | Discovery experiments |

## Takeaway

Orthogonal to Cluster A **when gate≈0** (most VATEX). High value for **movie/generalization** clips in external registry — implement before trusting VT on dialogue-heavy scenes.
