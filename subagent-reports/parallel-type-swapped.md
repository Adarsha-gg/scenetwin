# Parallel research subagent — type-swapped prompt control

Verdict: no true cached type-swapped prompt-control result is available locally.

Concrete outputs:
- Full report: `output/reports/parallel-research-type-swapped.md`
- Future no-API batch: `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl` (15 records)

High-severity blocker: cached files contain baseline/gap-targeted or tribe/vlm comparisons only; none contain same-clip/same-question `generic`, `matched`, and `swapped` prompt conditions.

Key paths inspected:
- `cursor/research/output/tribe_surgical_adqa_perq.csv`
- `cursor/research/output/tribe_crossjudge_gpt5_perq.csv`
- `cursor/research/output/tribe_crossjudge_opus_17_perq.csv`
- `cursor/research/output/tribe_necessity_rematch_perq.csv`
- `cursor/research/output/tribe_blind_spot_windows.csv`
- `cursor/research/output/tribe_gap_targeted_external_full_scores.csv`

Residual risks: future scoring needs approved LLM/human generation and original/recovered question text or regenerated frame-grounded questions; only 8/15 batch records have cached q_idx refs aligned to the selected window type.
