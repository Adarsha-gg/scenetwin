# AutoAD III — Back to the Pixels (VGG 2024)

**Source:** [arxiv_2404.14412.pdf](sources/arxiv_2404.14412.pdf)

## Why they did it

AD generation lacked **video-aligned training data** at scale and used **NLP metrics** (CIDEr, METEOR) ill-suited to AD. They built CMD-AD / HowTo-AD datasets, a Q-Former video→LLM generator, and **domain metrics**:

- **LLM-AD-Eval** — LLM rates AD quality 1–5 vs reference
- **CRITIC** — character naming correctness
- **R@k/N** — multi-reference recall (AutoAD II carryover)
- **Action coverage** — whether described actions match video

## What we agree with

- Pixel-level video grounding beats caption-only pipelines for AD.
- AD-specific metrics beat CIDEr for ranking generations.
- Character and action dimensions capture failures CLIP misses.

## What we think is wrong / limited

1. **LLM-AD-Eval anchors to reference AD** — same subjectivity trap ADQA documents; our proxy ρ=0.899 partly because tier3 is always the reference.
2. **CRITIC on VATEX** — short clips rarely have named characters; our entity proxy ρ=0.638 is ceiling-limited.
3. **R@3/N with one pro ref** — mathematically favors tier3; ρ=0.532 is structural, not informative.
4. **Movie-scale training** — metrics tuned on MAD may not transfer to 10s VATEX (confirmed on external clips).

## Our alternative

- **LLM-AD-Eval proxy without tier3 self-match** — rank tiers 0–2 only; still high but less inflated.
- Replace CRITIC with **role-noun + verb-object** coverage from video tags (no names required).
- Use **action coverage + VT consistency** instead of R@k/N for multi-aspect audit.
- Keep LLM-AD-Eval as **diagnostic**, not ensemble weight, when reference-free ADQA is available.

## Implementation

| Script | ρ |
|--------|--:|
| `cursor/papers/llm_ad_eval_proxy.py` | 0.899 |
| `cursor/papers/critic_entity.py` | 0.638 |
| `cursor/papers/multi_ref_r_at_k.py` | 0.532 |
| `cursor/papers/action_coverage.py` | 0.601 |

## Takeaway

AutoAD III metrics **cluster with semantic grounding** (see CROSS-PAPER-SYNTHESIS). Best independent leg: **action_coverage**. Worst: **multi_ref_r3** on our benchmark design.
