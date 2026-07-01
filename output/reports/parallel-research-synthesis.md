---
title: Parallel Research Synthesis — Go-Forward Changes
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - output/reports/parallel-research-type-swapped.md
  - output/reports/parallel-research-route-hallucination-gate.md
  - output/reports/parallel-research-tribe-frame-sampling.md
  - output/reports/parallel-research-cheap-baseline-gauntlet.md
  - output/reports/parallel-research-access-surface-triage.md
  - output/reports/parallel-research-blocked-next-steps.md
---

# Parallel Research Synthesis — Go-Forward Changes

## Decision changes

1. **Promote cheap-baseline triage evidence.** The strongest current external TRIBE result is no longer the in-benchmark AUC=1 pilot. It is corrected external ADQA-failure triage: `accessibility_gap` AUC `0.794`, category-shuffle p=`0.003`, stronger than category/transcript/duration baselines.
2. **Use review-budget wording.** `mean_visual_gap` catches 4/10 ADQA failures at 25% review budget and 5/10 at one-third. Claim review prioritization, not automatic skipping.
3. **Keep route-specific hallucination as an appendix.** Route/high-gap stratifies cached hallucination-gate behavior, but best simple AUC is only about `0.659`.
4. **Do not claim TRIBE frame sampling fixes temporal action.** It increases high-need coverage but not action-route coverage; cached ADQA rho is lower than uniform.
5. **Treat type-swapped prompt control as pending.** No cached result exists; the JSONL batch is a staged future experiment, not evidence.
6. **Gate lower-priority work.** Full text-extractor NCR requires approved gated HF access + GPU; `P_silence` requires a method decision + GPU/media; BLV study requires human-study approval.

## Paper-safe wording

Use:

> TRIBE is a brain-grounded side-car for clip/window review triage and access-surface routing. In cached external validation, `accessibility_gap` provides confound-checked ADQA-failure triage beyond category, transcript/speech, and duration baselines. CLIP+ADQA remains the scoring layer; TRIBE proposes where to inspect or author, and ADQA/VLM/humans verify.

Avoid:

- TRIBE improves AD ranking rho.
- TRIBE is a standalone hallucination detector.
- Low-gap means no AD/scoring needed.
- TRIBE-guided frame sampling solves temporal blind spots.
- Type-swapped controls have already passed.
- NCR is a working AD-dependent brain-grounded scorer.

## Immediate implementation targets

1. Update paper/demo claims to foreground the cheap-baseline gauntlet and Access Surface routing.
2. Fill `cursor/research/output/parallel_research/access_surface/top25_reviewer_cases.csv` reviewer columns.
3. Run type-swapped prompt-control only after explicit generator/judge/human approval.
4. Regenerate parity-matched TRIBE/uniform frame sets before any new frame-sampling ADQA scoring.
5. Draft BLV study materials locally, but do not recruit or collect data without explicit approval.
