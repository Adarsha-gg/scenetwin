# Round 071 — claude

**Angle:** `wrong_content_gate`

BREAKTHROUGH: the wrong-content gate's real false-reject driver is the **thin-but-genuine confounder**, and only CLIP separates it. Wrong-content vs the *weakest truthful* class (vatex_short) is 2-class AUC 0.998 / 98.3% global-threshold accuracy on CLIP, but only 0.928 / 91.7% on ADQA — and ADQA puts a genuine short AD **at-or-below** the wrong-content AD on 7/60 clips. CLIP rescues all 7 (min gap +0.090). This *inverts* the ship-best ranking, where ADQA leads (88% vs 53%): each signal is load-bearing for a different deployment property, so the ensemble is non-redundant.

## gate_outcome.py (free, as mandated)

| scorer | catch | ship-best | false-reject | n | vs random 25% |
|---|---:|---:|---:|---:|---:|
| ensemble | 100% | 90% | 0% | 60 | 4.0× |
| adqa_only | 100% | 88% | 0% | 60 | 4.0× |
| clip_only | 100% | 53% | 0% | 60 | 4.0× |

## New analysis: wrong-content vs thin-but-genuine separability

`gate_outcome` reports catch against the per-clip **argmin** (tier0 vs the *best* tier) and false-reject 0% — but that 0% is only because the genuine tiers always sit above tier0 *within a clip*. Deployment uses a fixed threshold across clips, where the hard case is a sparse-but-correct AD (tier1_vatex_short). If a thin genuine AD can score below a wrong-content one, a deployable threshold falsely rejects correct ADs. New script measures that 2-class separability directly.

| signal | 2-class AUC (short>cross) | best global-thr acc | thr | inversions (short≤cross) |
|---|---:|---:|---:|---:|
| CLIP | **0.998** | **0.983** | 0.224 | **0/60** |
| ADQA | 0.928 | 0.917 | 0.100 | **7/60** |
| fused (raw clip+adqa) | 0.993 | 0.975 | 0.225 | 0/60 |

**Complementary failure structure:** ADQA's binary yes-rate floors at 0 for *both* wrong content and very sparse genuine content, so it cannot tell them apart on 7 clips. On every one of those 7, CLIP's continuous grounding gives a positive gap (min +0.090) and rescues the decision. Zero clips fail both signals.

**The inversion that matters:** ADQA is the *better* ship-best signal (88% vs CLIP 53% — it picks the richest correct AD), but the *worse* confounder-rejecter (it confuses thin-correct with wrong). CLIP is the reverse. So the two signals are not redundant safety copies — each covers the other's deployment blind spot. This is a mechanistic reason the ensemble is required, distinct from r70's noise-margin argument.

## Honest limits

- 60 clips, single weakest-genuine class (vatex_short); inversion count is small-n.
- Raw fusion is an equal-weight sum of differently scaled signals; reported only as a sanity check, not a tuned operating point.
- This characterises false-reject risk against sparse-but-correct ADs; it does not revisit relational/action/count lie blindness (round 3) or base-rate precision (round 69) — complementary limitations.

## Files
- `cursor/pipeline/wrong_content_confounder.py` (new)
- `cursor/output/wrong_content_confounder.json` (new)
- `output/charts/scenetwin_wrong_content_confounder.py` + `.png` (new)

COMMANDS_RUN: cat skills + peer_learnings + codex/latest, .venv/bin/python cursor/pipeline/gate_outcome.py, python3 inspect external_ensemble_eval.csv, .venv/bin/python cursor/pipeline/wrong_content_confounder.py, .venv/bin/python output/charts/scenetwin_wrong_content_confounder.py
MISTAKE_AVOIDED: peer (codex two-scorer consensus floor) and all my prior rounds measured wrong-content against the BEST tier or against noise and reported false-reject 0% as a deployment guarantee; that 0% is a per-clip-argmin artifact. I refused to restate it and instead tested the cross-clip fixed-threshold case against the hardest genuine class, exposing that ADQA alone false-rejects 7/60 thin-but-correct ADs.
NEW_APPROACH: 2-class separability of wrong-content vs the weakest TRUTHFUL class (vatex_short) plus per-signal complementary-failure decomposition — different from codex's CLIP-consensus floor, my r2 per-clip tau, r68 global threshold, r69 base-rate precision, r70 noise margin. First round to characterise the gate's FALSE-REJECT confounder (sparse-but-correct) rather than its catch/recall, and to show CLIP↔ADQA cover opposite deployment blind spots (confounder vs ship-best).
