# Round 068 — claude

**Angle:** `wrong_content_gate`

BREAKTHROUGH: wrong-content catch survives as a single-AD GLOBAL raw-CLIP gate (LOCO 98% catch / 2% false-alarm) — not a per-clip-normalization tautology

## gate_outcome.py (free, as mandated)

| scorer | catch | ship-best | false-reject | n | vs random 25% |
|---|---:|---:|---:|---:|---:|
| ensemble | 100% | 90% | 0% | 60 | +75pp |
| adqa_only | 100% | 88% | 0% | 60 | +75pp |
| clip_only | 100% | 53% | 0% | 60 | +75pp |

## New angle (different from peer + my prior rounds)

`gate_outcome.py` catch is computed by ranking a 4-candidate pool and rejecting the
lowest, on **per-clip min-max-normalised** columns that force `tier0_cross` to 0.0 when
it is the pool min. That makes the 100% partly tautological and undeployable on a single
AD. I tested whether the catch survives on the **raw** CLIP score with a **single global
absolute threshold** (no pool, no normalization), validated leave-one-clip-out.

| operating point | catch | false-alarm |
|---|---:|---:|
| reject-AUC (raw CLIP) | **0.999** | — |
| leave-one-clip-out (honest) | **98.3%** | **2.2%** |
| fixed a-priori T=0.15 | 90% | 0.0% |

Raw separation: wrong-content mean 0.074 (max 0.217) vs legit mean ~0.31 (expert min
0.223) — ~4x gap. The headline catch is real in substance; it should be reported as a
global absolute-threshold gate (LOCO 98/2), deployable on single ADs, not a pool minimum.

Honest scope: catches catastrophic wrong-clip mismatch only; blind to the
relational/action/count lies from round 3 (those stay in the legit raw-CLIP band). The
two gate limitations are complementary.

New script `cursor/pipeline/wrong_content_global_gate.py` +
`cursor/output/wrong_content_global_gate.json` + chart + findings.

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_outcome.py, .venv/bin/python (raw score dist by tier), .venv/bin/python (global threshold AUC sweep), .venv/bin/python (leave-one-clip-out CV + fixed thresholds), .venv/bin/python cursor/pipeline/wrong_content_global_gate.py
MISTAKE_AVOIDED: peer (codex) leaned on per-clip-normalised pool columns and accepted the relative pool-min catch at face value; I checked whether the 100% is a normalization artifact instead of restating it, and validated leave-one-clip-out so the threshold is never fit on the clip it scores.
NEW_APPROACH: convert the relative 4-candidate pool-ranking gate into a single global ABSOLUTE threshold on RAW (un-normalised) CLIP, validated leave-one-clip-out — different from codex's two-scorer CLIP consensus floor, from my round-2 per-clip-tau single-AD gate on the human-lies jsonl, and from my round-3 relational-lie stratum. This is the deployment-mode (no pool) version of gate_outcome.

PR: https://github.com/Adarsha-gg/scenetwin/pull/4
