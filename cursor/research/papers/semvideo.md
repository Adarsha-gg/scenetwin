# SemVideo — Hierarchical Semantics from fMRI (2026)

**Source:** [arxiv_2602.21819.pdf](sources/arxiv_2602.21819.pdf)

## Why they did it

fMRI→video models fail on **appearance mismatch** (object identity drifts) and **motion misalignment**. SemVideo uses **SemMiner** hierarchical text:

1. **Static anchor** — first-frame object/scene
2. **Motion narrative** — how things move
3. **Holistic summary** — event-level story

Guides decoders for semantic alignment + temporal coherence.

## What we agree with

- AD should decompose into **static vs motion** buckets — matches BLV “what’s in frame” vs “what changed”.
- Motion-heavy clips (Sports) may need **motion narrative score** more than static CLIP.
- Hierarchical structure mirrors how **TRIBE** separates sustained visual vs dynamic need.

## What we think is wrong / limited

1. **Brain reconstruction ≠ AD eval** — SemMiner text comes from GT video, not from AD hypothesis.
2. **No AD dataset** — we proxy by scoring AD sentences against each hierarchy level via embeddings.
3. Risk of **double-counting** holistic summary with StoryRecall/NU.

## Our alternative

- `hierarchical_semantic_eval.py`: score AD against static/motion/holistic prompts derived from **frames**, not fMRI.
- Hypothesis tested: **motion_score alone** ranks tier2 > tier3 on Sports clips where pro under-describes action.
- Weight motion leg higher when `motion_magnitude > τ` from need proxy.

## Implementation

| Script | Status |
|--------|--------|
| `cursor/methods/hierarchical_semantic_eval.py` | Prototype |

## Takeaway

Conceptual bridge between **SemVideo** and **TRIBE need windows**. Implementation should feed fusion as **conditional weight**, not flat average.
