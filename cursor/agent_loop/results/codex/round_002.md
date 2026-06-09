# Round 002 — codex

**Angle:** `clip_local_analysis`

## Signal Tested

`clip_consensus_min = min(SceneTwin CLIP score, benchmark CLIP score)`

This is a conservative two-scorer CLIP agreement check: an AD only gets as much visual support as its weaker local CLIP scorer gives it. It uses the existing `cursor/output/benchmark_clip_sanity.csv` table only; no LLM, no CLIP rerun, no ADQA.

I also inspected `external_clip_full_eval.csv` and found a tempting temporal composite, but source audit showed `vt_consistency` and `story_recall` are lexical/pro-AD-derived fields, not strict CLIP scores. I did not claim them as CLIP-only.

## Result

New script: `cursor/pipeline/clip_consensus_analysis.py`

Output: `cursor/output/clip_consensus_analysis.json`

Benchmark ladder, 18 clips x 4 tiers:

| signal | rho | full order | adjacent wins | all pairwise wins | pro > short | cross lowest |
|---|---:|---:|---:|---:|---:|---:|
| SceneTwin CLIP | 0.686 | 7/18 | 42/54 | 90/108 | 12/18 | 18/18 |
| benchmark CLIP | 0.735 | 10/18 | 46/54 | 96/108 | 14/18 | 18/18 |
| **CLIP consensus floor** | **0.739** | **10/18** | **46/54** | **96/108** | **14/18** | **18/18** |

Single-AD wrong-content LOCO gate at 10% target false-reject:

| signal | catch | false-reject | AUC bad-low |
|---|---:|---:|---:|
| SceneTwin CLIP | 100.0% | 11.1% | 1.000 |
| benchmark CLIP | 100.0% | 11.1% | 1.000 |
| **CLIP consensus floor** | **100.0%** | **9.3%** | **1.000** |

## Interpretation

This is **not a breakthrough**. The consensus floor is real and reproducible, but the lift is marginal: rho improves only 0.004 over the stronger individual CLIP scorer, with no gain in full ordering or pairwise wins. The main useful takeaway is negative: adding a second local CLIP score as a conservative agreement floor does not unlock a new paper claim on the current 18-clip ladder.

The signal does slightly lower false-reject in the LOCO wrong-content setting (9.3% vs 11.1%), but Claude's raw-score result on the larger 60-clip external table remains the stronger deployment result for wrong-content gating.

COMMANDS_RUN: sed -n skill/context reads, rg --files cursor/output, .venv/bin/python schema-inspection snippets for cached CSV/JSON, rg -n vt_consistency/story_recall source audit, .venv/bin/python cursor/pipeline/clip_consensus_analysis.py
MISTAKE_AVOIDED: avoided repeating Claude's single-AD absolute raw-score threshold and avoided claiming the per-clip-normalised pool gate; also rejected a tempting lexical temporal composite after source audit because it was not strict CLIP-only.
NEW_APPROACH: two-scorer CLIP consensus floor across existing local CLIP score columns, requiring agreement between independent CLIP scoring recipes for the same AD instead of calibrating an absolute tau or ranking a candidate pool.
