# Round 002 — claude

**Angle:** `wrong_content_gate`

## Baseline (re-ran the free gate, as tasked)
`gate_outcome.py` (min-of-pool, relative, ranks 4 candidates / clip, rejects lowest):

| signal | catch | ship-best | false-reject | n |
|---|---|---|---|---|
| ensemble | 100% | 90% | 0% | 60 |
| adqa_only | 100% | 88% | 0% | 60 |
| clip_only | 100% | 53% | 0% | 60 |

vs **random gate = 25%**. So far so good — but I dug into *why* it is exactly 100%.

## The artifact I caught
The `ensemble_mean_clip_top3` column is **per-clip min-max normalised**, which forces the
wrong-content AD (`tier0_cross`) to literally **0.0** in every clip. The min-of-pool gate
then "catches" it by construction. It also assumes a clean candidate **pool** to rank
against — not how deployment works (a viewer hears **one** AD, no siblings, no reference).

## NEW_APPROACH — single-AD absolute-threshold gate (LOCO calibrated)
New script `cursor/pipeline/wrong_content_threshold_gate.py`:
- **RAW** signals only (`clip_top3`, `adqa_score`) — no per-clip normalisation leakage.
- Each (clip, tier) candidate scored **independently**, no pool.
- Reject if score < tau; **tau calibrated leave-one-clip-out** (set on 59 clips, applied to
  held-out clip), operating point = lowest tau with false-reject <= 10% maximising catch.
- Honest grader-free ROC AUC reported per signal.
- Baseline: random gate at a 10% reject budget catches **10%**.

### Result (n = 60 cross, 180 good; LOCO)
| signal | catch | false-reject | AUC |
|---|---|---|---|
| **clip_only** | **98%** | **2%** | **0.999** |
| adqa_only | 95% | 6% | 0.961 |
| raw_ensemble | 98% | 8% | 0.998 |

**OUTCOME:** The wrong-content gate does **not** need the candidate pool. Raw CLIP score
alone catches 98% of wrong-content ADs at 2% false-reject in a true single-AD, no-reference
deployment setting (LOCO-calibrated, ~10x over the 10% random budget). This is a *stronger,
honest* claim than the tautological min-of-pool 100%.

**Non-obvious finding:** adding ADQA **hurts** here — `raw_ensemble` false-reject jumps to
8% vs CLIP-only's 2%, because sparse-but-correct short ADs (tier1) score low on ADQA. For
the *wrong-content* failure mode specifically, CLIP-only is the right, cheaper signal.

**Honest control / scope:** AUC ~1.0 looks far above the locked **CLIP-only AUC 0.84** — but
that 0.84 is the *subtle-hallucination* gate (right clip, wrong details). Whole-clip mismatch
(`tier0_cross`) is a genuinely easier, distinct failure mode; this does **not** overturn 0.84,
it bounds a different axis. Both numbers stand side by side.

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_outcome.py, .venv/bin/python cursor/pipeline/wrong_content_threshold_gate.py
MISTAKE_AVOIDED: codex re-ran best_of_n_rerank.py on cached clips burning credits; I added zero LLM calls and built a free analysis on the existing CSV. Also avoided the "re-computed locked gate numbers" trap by extending into a new deployment-honest variant instead of restating 100%.
NEW_APPROACH: single-AD absolute-threshold gate with leave-one-clip-out tau calibration on RAW (un-normalised) scores — vs the min-of-pool relative gate (mine) and best-of-N rerank (codex's). Shows the gate survives without a candidate pool, and that CLIP-only beats the ensemble on this axis.
PR: pending
