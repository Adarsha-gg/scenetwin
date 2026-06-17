# ADx3 + Making AI Drafts Count (GenAD / RefineAD / AdaptAD)

**Sources:** [arxiv_2602.02684.pdf](sources/arxiv_2602.02684.pdf) · [arxiv_2605.05348.pdf](sources/arxiv_2605.05348.pdf)

## Why they did it

**ADx3:** Scale accessible AD via GenAD (VLM + guideline prompts) → RefineAD (human edit UI) → AdaptAD (on-demand user queries). Specialists rated VLM output “good” but not “excellent” without edits.

**Making AI Drafts Count:** Same group — **draft quality threshold** matters. Unguided prompts barely help; guideline-rich GenAD cuts time 50%+ and cognitive load. Threshold rises with visual complexity.

## What we agree with

- Evaluation should include **timing and delivery**, not text alone (aligns with IRT 6-dim work).
- Human-in-the-loop is not optional for “excellent” AD — automated tiers (tier1/2) are **drafts**, tier3 is **refined**.
- **MDCI** (human-AI contribution index) is the right meta-metric for workflows, wrong for clip-tier ranking.

## What we think is wrong / limited

1. **Studies use novice describers** — our tier3 is professional; comparing tier2→tier3 as “draft→refined” overstates GenAD gap.
2. **No reference-free audit metric** — papers measure workflow efficiency, not “does this AD match the video?”
3. **Quality threshold is qualitative** — we need quantitative gate: e.g. ADQA score > τ before RefineAD.

## Our alternative

- **Slot IoU + MDCI proxy** — measure whether AI drafts cover the right **time windows** (`discover/mdci_slot_iou.py`).
- Use TRIBE **need curves** to trigger AdaptAD-style queries at high P_AV−P_A gaps.
- Tier mapping: tier1/2 = GenAD drafts, tier3 = RefineAD output; audit = “how much edit was needed?” via embedding distance tier2→tier3 vs tier1→tier3.

## Implementation

| Script | Purpose |
|--------|---------|
| `cursor/methods/adx3_slot_generator.py` | Slot proposal prototype |
| `cursor/discover/mdci_slot_iou.py` | Timing/slot overlap |

## Takeaway

These papers justify **why tier2 exists** but don’t replace SceneTwin’s grounding metrics. Best hook: **need-triggered refinement** + **MDCI for workflow eval**, not Spearman on tiers.
