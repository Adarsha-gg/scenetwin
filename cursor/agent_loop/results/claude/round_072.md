# Round 072 — claude

**Angle:** `wrong_content_gate`

BREAKTHROUGH: the **ship-best** gate decision has a free, near-perfect confidence
signal — **ADQA's own decision margin**. Abstaining the lowest-margin 20% of clips
to human review makes ship-best **100%** reliable, and **6 of the 7** ship-best
errors are *exact ADQA ties* (margin = 0). Cross-signal agreement (CLIP↔ADQA)
is the WRONG confidence signal here and FAILS.

## gate_outcome.py (free, as mandated)

| scorer | catch | ship-best | false-reject | n | vs random 25% |
|---|---:|---:|---:|---:|---:|
| ensemble | 100% | 90% | 0% | 60 | +75pp |
| adqa_only | 100% | 88% | 0% | 60 | +75pp |
| clip_only | 100% | 53% | 0% | 60 | +75pp |

Catch is saturated (100% all signals — covered r68–r71). The open axis is
**ship-best** (90 / 88 / 53). Every prior wrong_content_gate round probed the
REJECT decision; this round probes ship-best, as a **selective-prediction** problem.

## Two free confidence signals for the ship-best decision

`cursor/pipeline/gate_shipbest_selective.py`

**[1] Cross-signal agreement (CLIP pick == ADQA pick)** — codex's consensus idea,
applied to ship-best:

- CLIP and ADQA agree on the best AD on only **34/60 (57%)**.
- Abstain on disagreement → ship-best **88.2%** at 57% coverage — *worse* than
  full-coverage ensemble (90%). **Agreement is useless.**
- On the 26 disagreements: **ADQA right 23, CLIP right 2** (ensemble 24). The
  minority signal (CLIP) is almost always the wrong one, so "they disagree" carries
  no information about which to trust. CLIP is near-random for ranking (53% alone).

**[2] ADQA intra-signal margin (best − 2nd-best)** — this round's signal:

| coverage | ship-best acc | n shipped |
|---:|---:|---:|
| 100% | 88.3% | 60 |
| 90%  | 98.1% | 54 |
| **80%** | **100.0%** | **48** |
| 70%  | 100.0% | 42 |
| 50%  | 100.0% | 30 |

- **6/7** ship-best errors are exact ADQA ties (margin = 0; 6 tie clips, all wrong).
  The 7th is the next-smallest margin → abstain 20% lowest-margin = 0 errors.
- The abstention trigger is **free** (ADQA's own yes-rate margin, no extra model/LLM).

## Why this matters (synthesis with prior rounds)

The two gate jobs have **inverted** signal structure and **inverted** confidence signals:

| job | best signal | needs ensemble? | good confidence signal |
|---|---|---|---|
| REJECT wrong-content (catch) | ensemble (r70: single signals 0σ margin) | **yes** | per-signal z-margin (r70) |
| SHIP-BEST | **ADQA alone** (CLIP near-random) | **no** (ens ≈ adqa, +1 clip) | **ADQA intra-signal margin** (this round) |

So: cross-signal *consensus* (codex) is the right idea for catch but the wrong idea
for ship-best; for ship-best, the correct confidence signal is *intra*-signal margin,
and CLIP should be dropped from the ranking entirely. This converts a hard 90% gate
into a deployable selective-prediction policy: auto-ship 80% at 100% ship-best,
route the 20% lowest-ADQA-margin clips (mostly ties) to a human.

## Files

- `cursor/pipeline/gate_shipbest_selective.py` (new)
- `cursor/output/gate_shipbest_selective.json` (new)
- `output/charts/scenetwin_gate_shipbest_selective.{py,png}` (new)

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_outcome.py, inspect external_ensemble_eval.csv + gate_outcome.json (python), replicate ship-best argmax, CLIP/ADQA agreement structure, ADQA-margin risk-coverage, tie/non-tie error breakdown, .venv/bin/python cursor/pipeline/gate_shipbest_selective.py, .venv/bin/python output/charts/scenetwin_gate_shipbest_selective.py
MISTAKE_AVOIDED: codex applied cross-signal agreement (consensus floor) as a universal confidence/decision signal; I tested it on the ship-best job and showed it FAILS here because the minority signal (CLIP) is the wrong one — agreement only helps when the disagreeing signals are equally skilled. I did not assume the consensus idea transfers across the two gate jobs.
NEW_APPROACH: selective-prediction / risk-coverage analysis of the SHIP-BEST decision (not the reject decision every prior round used), comparing CROSS-signal agreement vs INTRA-signal ADQA margin as abstention triggers — different from codex's consensus floor (a catch decision rule), my r68 global threshold, r69 base-rate precision, r70 noise margin, r71 confounder separability. First round to make ship-best deployable as an abstaining gate and to show its errors are concentrated in ADQA ties.
NEW_APPROACH: selective-prediction on ship-best via intra-signal ADQA margin (80% coverage -> 100% ship-best; 6/7 errors are ADQA ties); cross-signal agreement fails because CLIP is the near-random minority.
