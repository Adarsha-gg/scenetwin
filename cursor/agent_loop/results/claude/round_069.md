# Round 069 — claude

**Angle:** `wrong_content_gate`

BREAKTHROUGH: the locked wrong-content catch is a low-PRECISION safety screen — at a realistic 1% base rate PPV is only 31% (base-rate fallacy), but cost asymmetry justifies it down to 0.2% prevalence

## gate_outcome.py (free, as mandated)

| scorer | catch | ship-best | false-reject | n | vs random 25% |
|---|---:|---:|---:|---:|---:|
| ensemble | 100% | 90% | 0% | 60 | +75pp |
| adqa_only | 100% | 88% | 0% | 60 | +75pp |
| clip_only | 100% | 53% | 0% | 60 | +75pp |

## New angle (different from peer + my prior rounds)

Every prior round reported catch/false-alarm at (near-)**balanced** prevalence
(gate_outcome 1:3 pool; my r68 LOCO at 25% positives). None asked the operator's real
question: at the **rare** base rate wrong-content actually occurs in production, what is
the gate's PRECISION and alert burden? I propagated the **already-locked** LOCO operating
point (TPR=0.983, FPR=0.022) through realistic base rates via Bayes — no re-fit, no model
calls, no pool re-ranking.

| base rate | precision | recall | alert% | NNR | missed/10k |
|---|---:|---:|---:|---:|---:|
| 0.10 | 83.1% | 98.3% | 11.8% | 1.2 | 16.7 |
| 0.05 | 70.0% | 98.3% | 7.0% | 1.4 | 8.3 |
| 0.02 | 47.4% | 98.3% | 4.1% | 2.1 | 3.3 |
| 0.01 | **30.9%** | 98.3% | 3.2% | 3.2 | 1.7 |
| 0.005 | 18.2% | 98.3% | 2.7% | 5.5 | 0.8 |

At 1% prevalence **2 of every 3 alerts are false** — the "100% catch" headline hides a
base-rate fallacy nobody in this loop stated.

**What rescues it — cost asymmetry.** Break-even cost ratio (cost_miss / cost_review for
the gate to beat shipping unreviewed): 2.2x at 1% prevalence, 11.3x at 0.2%. A wrong AD
shipped to a blind viewer (the exact failure SceneTwin prevents) costs far more than a few
minutes of re-review, so the gate stays net-beneficial to ~0.2% prevalence. Conclusion:
it is a **low-precision, correctly-calibrated asymmetric-cost safety screen**, not a
high-precision classifier — and should be reported as such.

New script `cursor/pipeline/gate_deployment_precision.py` +
`cursor/output/gate_deployment_precision.json` + chart + findings.

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_outcome.py, .venv/bin/python cursor/pipeline/gate_deployment_precision.py, .venv/bin/python output/charts/scenetwin_gate_deployment_precision.py
MISTAKE_AVOIDED: peer (codex) and my own prior rounds reported the catch/false-alarm at balanced prevalence and implicitly treated it as the deployment number; I refused to restate 98%/2% as a deployment guarantee and exposed that precision is base-rate dependent (31% PPV at 1%), then showed why the gate is still justified (cost asymmetry) rather than overclaiming.
NEW_APPROACH: Bayesian base-rate precision + decision-theoretic break-even propagation of the LOCKED LOCO operating point — different from codex's two-scorer CLIP consensus floor, my r68 global absolute threshold, my r2 per-clip tau, and my r3 relational-lie stratum. First round to characterise the gate's PRECISION/alert-burden/cost economics rather than its recall.

PR: pending
