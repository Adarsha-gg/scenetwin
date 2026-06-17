# CA3D — Context-Aware Automatic AD (Amazon 2024)

**Source:** [arxiv_2412.10002.pdf](sources/arxiv_2412.10002.pdf)

## Why they did it

Movie AD needs **when** to speak (event detection) and **what** to say, end-to-end from pixels without GT timestamps. CA3D: temporal feature enhancement, anchor-based **AD event detector**, self-refinement of boundaries.

## What we agree with

- **Event localization** is as hard as text quality — tier differences may be timing not wording.
- Self-refinement loop mirrors CoAD/ADx3 **edit passes**.
- Long-form movies ≠ our clips, but **overlap with speech gaps** (G7/G8) is universal.

## What we think is wrong / limited

1. **Generation system**, not audit metric — outputs scripts + timestamps, doesn’t score existing AD tiers.
2. Trained with movie metadata priors we don’t have for VATEX.
3. Boundary refinement needs **full movie context**; 10s clips trivialize detection.

## Our alternative

- Adapt as **eval only**: detect speech-free windows in clip audio → measure AD **word overlap** with allowed windows (`papers/timing_overlap_g7g8.py`).
- MDCI-style: score = fraction of AD words placed in valid gaps.
- Low overlap → flag regardless of CLIP score (professional AD can be **right words, wrong time**).

## Implementation

| Script | Purpose |
|--------|---------|
| `cursor/papers/timing_overlap_g7g8.py` | G7/G8 gap overlap proxy |

## Takeaway

CA3D + IRT delivery + TRIBE need curves form a **timing cluster** orthogonal to semantic Cluster A — under-tested in current leaderboard.
