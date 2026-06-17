# AVBench — Audio-Video Evaluation Benchmark (2026)

**Source:** [arxiv_2605.24652.pdf](sources/arxiv_2605.24652.pdf)

## Why they did it

AV generation eval used coarse MLLM VQA. AVBench builds **10 human-centric dimensions** (video quality, audio quality, AV/AT/VT consistency) with **specialized evaluators** trained on perturbation pairs, outputting **continuous confidence scores** not binary VQA.

## What we agree with

- **VT consistency** (text vs video) is a first-class signal — maps directly to CLIP-style AD audit.
- Probabilistic scoring beats discrete LLM judgments for ranking.
- Fine-grained dimensions let you **down-weight** irrelevant ones (e.g. audio aesthetics for silent VATEX clips).

## What we think is wrong / limited

1. **Target is generative AV**, not AD — metrics assume synchronized generated audio; AD text is **not** the soundtrack.
2. **Human-centric bias** — wildlife/sports clips may score oddly on “speech clarity” dimensions.
3. We only implemented **VT leg** — full AVBench needs their checkpoints.

## Our alternative

- `vt_consistency` = embedding alignment AD sentence ↔ sampled frames (proxy for their VT evaluator).
- For clips with **ambiguous audio** (MAVERIX-positive), add **AT consistency** leg when we have audio captions.
- Do **not** blend audio quality dims into AD audit — AD must not describe audible dialogue.

## Implementation

| Script | ρ |
|--------|--:|
| `cursor/methods/av_consistency_eval.py` → `vt_consistency` | 0.768 |

## Takeaway

AVBench VT is **Cluster A** (r>0.85 with ADQA/LLM proxy). Useful as lightweight CLIP alternative with different failure surface; not additive unless weighted low in fusion.
