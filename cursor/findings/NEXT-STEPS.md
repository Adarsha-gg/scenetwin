---
title: SceneTwin Next Steps / Pending Experiments
category: research
tags: [SceneTwin, todo, pending, reproducibility]
updated: 2026-06-23
---

# SceneTwin Next Steps — current research queue

Status after the 2026-06-23 Colab/TRIBE + parallel cached-data run. Old “NCR needs Colab” instructions are superseded: the L4 TTS-audio NCR run completed and was near-null as a ranker.

## What is now locked

- **CLIP+ADQA remains the scorer.** TRIBE should not be framed as a ranker, rho booster, or continuous calibration layer.
- **TRIBE survives as review triage / blind-spot routing / Access Surface input.** The best new external support is the cheap-baseline gauntlet: `accessibility_gap` predicts corrected external ADQA failures at AUC `0.794` with category-shuffle p=`0.003`.
- **NCR is a negative/guardrail result for now.** Full 60-clip L4 TTS-audio NCR produced near-chance tier separation: 4-tier Spearman `0.035`, corrected 3-tier Spearman `0.031`. Keep the weak T3>short and source-leakage hints as exploratory only.
- **Low-gap should reduce review pressure, not skip scoring.** Bottom-third max-gap clips show low fail rates, but this is not enough to claim “no AD needed” or CLIP-only replacement.

## Highest-priority next actions

### 1. Run type-swapped prompt control when scoring is approved

**Why:** This is the cleanest test that TRIBE route type matters rather than “more detailed prompt helps.”

**Current state:** No cached result exists for same-clip/same-question `generic`, `matched`, and `swapped` conditions. A fixed future batch was prepared:

- `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl`
- report: `output/reports/parallel-research-type-swapped.md`

**Next:** Use the JSONL as the frozen candidate set; run generation/judging only after explicit approval for external API/human scoring.

### 2. Fill the top-25 reviewer worksheet

**Why:** The Access Surface queue is ready; the next useful evidence is review labels, not another re-rank.

Inputs:

- `cursor/research/output/parallel_research/access_surface/top25_reviewer_cases.csv`
- `cursor/research/output/parallel_research/access_surface/top25_reviewer_cases.md`
- report: `output/reports/parallel-research-access-surface-triage.md`

Fill the blank reviewer fields with VLM or human review. Do not call it BLV validation unless actual BLV participants are approved and recruited.

### 3. Promote the cheap-baseline gauntlet into paper/demo evidence

**Why:** This is the strongest confound-controlled external TRIBE triage result.

Key numbers:

- ADQA failure target: `accessibility_gap` AUC `0.794`, category-shuffle p=`0.003`.
- Top-20% mean-gap queue catches `3/10` ADQA failures vs random expected `2/10`.
- Ensemble-failure result catches `2/2`, but n=2, so use only as corroboration.

Report/artifacts:

- `output/reports/parallel-research-cheap-baseline-gauntlet.md`
- `cursor/research/output/parallel_research/cheap_baselines/`

### 4. Fix TRIBE-guided frame sampling before any new scoring claim

**Current result is mixed-to-negative:** high-need coverage improves (`70.8%` vs `57.4%`), but action-route coverage does not (`18.6%` vs `20.9%`), and cached ADQA rho drops slightly (`0.782` vs `0.801`). Existing TRIBE frame folders also have budget mismatch.

Before rerunning ADQA, regenerate parity-matched frame sets: 8 uniform frames and 8 TRIBE-window frames per clip.

Report:

- `output/reports/parallel-research-tribe-frame-sampling.md`

### 5. Treat route-specific hallucination as appendix/triage context

The cached join is complete and useful, but not detector-grade:

- 60/60 hallucination clips joined to TRIBE summaries.
- Best high-gap AUC for top-quartile CLIP hallucination drop: `0.659`.
- Action-route top windows have the largest mean CLIP hallucination drop.

Use as stratified analysis, not a standalone hallucination detector.

Report:

- `output/reports/parallel-research-route-hallucination-gate.md`

## Approval-gated work

### BLV micro-study packet

Highest value for credibility, but human-subjects/recruitment approval is required before collecting data. Local prep is safe:

- protocol
- consent draft
- stimuli CSV
- randomization CSV
- screen-reader/playback dry-run notes

Reference plan: `output/reports/parallel-research-blocked-next-steps.md`.

### `P_silence` condition

Do not spend GPU until the method is defined. Decide whether `P_silence` means same-duration silent audio-only, black-video+silence, or another control. Then create a Colab runner and manifest.

### Full text-extractor NCR

Lower priority unless a reviewer specifically challenges TTS-audio NCR. Requires explicit approval to use gated Hugging Face/Llama access via a secure runtime secret plus GPU. Do not use pasted chat tokens.

## Superseded / de-prioritized

- **Old NCR runbook:** completed on L4 as TTS-audio; results are near-null. See `cursor/findings/neural-contrastive-retrieval.md`, `output/reports/tribe-ncr-results.md`, and `output/reports/tribe-ncr-hidden-patterns.md`.
- **TRIBE as global AD ranker / rho lift:** structurally wrong for clip-level features and empirically unsupported.
- **TRIBE-guided frame sampling as solved temporal blind spot:** not supported until frame-budget parity and action coverage improve.

## See Also

- `output/reports/new-findings.md`
- `output/reports/parallel-research-cheap-baseline-gauntlet.md`
- `output/reports/parallel-research-access-surface-triage.md`
- `output/reports/parallel-research-type-swapped.md`
- `output/reports/parallel-research-blocked-next-steps.md`
