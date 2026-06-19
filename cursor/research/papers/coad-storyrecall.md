# CoAD — Coherent AD + StoryRecall (2025)

**Source:** [arxiv_2510.25440.pdf](sources/arxiv_2510.25440.pdf)

## Why they did it

Per-interval AD generation repeats phrases (“adjusts the device”) and scores well on **per-clip CIDEr** while failing **narrative coherence**. CoherentAD autoregressively selects candidates across intervals. **StoryRecall** measures whether the **sequence** conveys the GT story. **Repetition metrics** penalize redundant n-grams across intervals.

## What we agree with

- Sequence-level eval is necessary for long-form AD; our 10s clips are a lower bound but repetition still appears across tier2/tier3.
- Independent generation metrics (CIDEr, LLM-AD-Eval) reward local fluency over global coherence.
- StoryRecall is closer to “did the listener get the plot?” than embedding-to-reference.

## What we think is wrong / limited

1. **StoryRecall needs GT narrative** — originally used pro AD as key (tautological ρ≈1). We fixed to ADQA-derived keys; ρ=0.703.
2. **Repetition anti-correlates with tier GT** (ρ=-0.064) — pro AD is longer; repetition penalty **punishes human-quality verbosity**.
3. **Training-free selection** — great for generation routing, not a drop-in audit metric without candidate pools.

## Our alternative

- StoryRecall keyed on **ADQA NU answers**, not pro AD text (`discover/story_recall_fixed.py`).
- Use repetition as **generation penalty only**, not tier ranking (exclude from fusion or invert carefully).
- Combine StoryRecall with **ADQA** for “narrative + grounded” fusion (`narrative_ground` in fusion script).

## Implementation

| Script | ρ |
|--------|--:|
| `cursor/papers/coad_repetition.py` (inverted) | -0.064 |
| `cursor/discover/story_recall_fixed.py` | 0.703 |

## Takeaway

CoAD teaches **process** (coherent selection) more than **evaluation** for SceneTwin. StoryRecall is complementary to Cluster A metrics; repetition is **conflicting** with pro-AD-as-GT.
