# New method results — first run 2026-05-27

These are **different evaluators** from the CLIP+ADQA ensemble, inspired by 2025–2026 papers.

| Method | Paper | ρ vs tier GT | Notes |
|--------|-------|--------------|-------|
| **AVBench VT proxy** | AVBench 2026 | **0.768** | AD covers `required_visual_evidence` terms |
| **ViDscribe query coverage** | ViDscribe 2026 | **0.710** | AD contains ADQA answer-key terms |
| ADQA all (baseline) | ADQA 2025 | 0.789 | Same questions, no split |
| ADQA **NU** (narrative) | ADQA 2025 | 0.516 | Plot questions — tiers barely separate |
| ADQA **VA** (visual facts) | ADQA 2025 | see CSV | Visual appreciation bucket |
| SemVideo **motion** bucket | SemVideo 2026 | 0.775 (n=4) | Too few motion questions |
| SemVideo **holistic** | SemVideo 2026 | 0.696 | |
| **Six-dim rubric** (VideoA11y+IRT) | 2025–2026 | ~0.57 | Heuristic; needs VLM judge upgrade |

## Generation

`adx3_slot_generator.py` produces timed AD **slots** from TRIBE need windows (no LLM):
- clip_12 → 5 slots with extended/standard recommendations
- Output: `cursor/methods/output/generated_ad/clip_NN_slots.jsonl`

## What to build next

1. Wire **VT consistency** (ρ=0.768) as third signal alongside CLIP+ADQA
2. Replace heuristic six-dim rubric with VLM-as-judge (IRT paper protocol)
3. LLM pass on generated slots → gap-targeted AD candidates → score with new metrics
4. Ingest LVOmniBench for long-form eval (beyond 30s clips)
