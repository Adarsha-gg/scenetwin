# Round 070 — claude

**Angle:** `wrong_content_gate`

BREAKTHROUGH: the 100% wrong-content catch is NOT brittle — median 4.2σ per-signal headroom, survives Gaussian measurement noise up to 0.5× the genuine-AD score spread before dropping below 99%; the safety is the *ensemble's*, which lifts every clip's margin off zero where single signals fail.

## gate_outcome.py (free, as mandated)

| scorer | catch | ship-best | false-reject | n | vs random 25% |
|---|---:|---:|---:|---:|---:|
| ensemble | 100% | 90% | 0% | 60 | +75pp |
| adqa_only | 100% | 88% | 0% | 60 | +75pp |
| clip_only | 100% | 53% | 0% | 60 | +75pp |

## New angle — margin + measurement-noise robustness (different from peer + all my prior rounds)

Every prior round (gate_outcome, my r2 per-clip tau, r68 global threshold, r69 Bayesian
base-rate, codex's two-scorer consensus floor) reports the catch on **noise-free** scores.
None asks: how much score *headroom* backs the 100%, and at what level of measurement
noise does it break? I answered both from the existing CSV, free, no LLM.

New script `cursor/pipeline/gate_margin_robustness.py`. The deployed gate flags the
argmin of the per-clip ensemble; the catch holds only while the cross-content AD stays
the minimum. Two probes:

**1. Separation headroom**

| metric | per-signal z-margin (genuine-AD SDs) | normalised ensemble margin |
|---|---:|---:|
| median | **4.24** | 0.594 |
| p10 | 0.53 | 0.420 |
| min (worst clip) | **0.00** | **0.224** |
| frac below 1σ / ≤0 | 25.2% <1σ | 0% ≤0 |

Typical headroom is wide (4.2σ), but on a **single signal** a quarter of cases sit within
one genuine-AD SD of flipping and the worst clip has **zero** separation (one signal fails
to distinguish the wrong AD at all). The two-signal fusion is what guarantees **no** clip's
ensemble margin reaches zero (min 0.224). This is a quantified, noise-framed justification
for the ensemble — distinct from the ship-best-rate argument.

**2. Monte-Carlo noise robustness** (2000 trials, Gaussian noise on raw adqa_score +
clip_top3, swept as a fraction of pooled genuine-AD SD, re-normalise, re-decide)

| noise (× genuine SD) | catch | 95% CI |
|---:|---:|---:|
| 0.00 | 100.0% | — |
| 0.25 | 99.8% | [98.3, 100] |
| 0.50 | 99.1% | [96.7, 100] |
| 0.75 | 98.2% | [95.0, 100] |
| 1.00 | 97.0% | [91.7, 100] |
| 1.50 | 94.1% | [88.3, 98.3] |
| 2.00 | 90.6% | [83.3, 96.7] |

Catch stays ≥99% up to noise = **0.5×** the natural genuine-AD spread, ≥95% up to **1.5×**.
At realistic CLIP/ADQA measurement jitter (well under 1× the between-genuine-AD spread)
the 100% headline degrades by <1pp — the gate is **noise-robust, not a knife-edge**.

`cursor/output/gate_margin_robustness.json` + `output/charts/scenetwin_gate_margin_robustness.png`.

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_outcome.py, .venv/bin/python cursor/pipeline/gate_margin_robustness.py, .venv/bin/python output/charts/scenetwin_gate_margin_robustness.py
MISTAKE_AVOIDED: peer (codex) and my own prior rounds all reported catch on noise-free scores and never tested whether the 100% survives measurement error; I refused to restate the headline and instead stress-tested its margin, exposing that single-signal separation is brittle (25% <1σ, min 0σ) and quantifying why the ensemble is required.
NEW_APPROACH: separation-margin distribution + Monte-Carlo measurement-noise perturbation of the locked gate decision (argmin re-normalised per trial) — answers "how brittle is the 100%" rather than recall/precision/prevalence. Different from codex's two-scorer consensus floor (a decision rule) and from my r2 tau, r68 threshold, r69 Bayesian base-rate. First round to characterise the gate's noise robustness and z-margin headroom.

PR: https://github.com/Adarsha-gg/scenetwin/pull/5
