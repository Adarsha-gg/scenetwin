# Peer learnings (Claude ↔ Codex)

Both agents **must read this file** every round and append their own mistakes/approaches.
Do not repeat mistakes listed here. Propose a **different** approach than the peer's last round.

## Shared mistakes (do not repeat)

| Agent | Mistake | Do instead |
|---|---|---|
| codex | Probed `.venv39` instead of `.venv` | Only `.venv/bin/python` |
| codex | `ls cursor/pipeline/` + `sed` whole files | Read skills; run copy-paste commands |
| codex | Re-ran `best_of_n_rerank.py` on cached clips | Check cache count; only uncached clip IDs |
| both | Re-computed locked gate numbers | Read `cursor/output/gate_*.json`; analyze or extend |

## Last round summaries

_(supervisor appends after each worker finishes)_

## Novel approaches tried

_(agents append: `NEW_APPROACH: <one line>` in their result file)_

### 2026-06-09T09:49:36Z — claude round 1
- Summary: # Round 001 — claude **Angle:** Expand the self-consistency gate. Instead of caching more best-of-N ADs (blocked by API credits), I diagnosed the real bottleneck and broke it for free. ## Diagnosis The n=5 self-consistency gate from `gate_review_holes.py` was **not** limited by available references — 9 clips already have an independent model-generated AD (`machine_ad_tier.csv`, frames→AD). It was limited by the...

### 2026-06-09 — claude round 2 (angle wrong_content_gate)
- NEW_APPROACH: single-AD absolute-threshold wrong-content gate, leave-one-clip-out tau calibration on RAW scores (no per-clip normalisation, no candidate pool). New script `cursor/pipeline/wrong_content_threshold_gate.py`.
- Caught artifact: `gate_outcome.py` "ensemble" column is per-clip min-max normalised → forces tier0_cross to 0.0 → its 100% min-of-pool catch is partly tautological + assumes a clean pool.
- Outcome: CLIP-only raw catches 98% wrong-content @ 2% false-reject, AUC 0.999, single-AD no-reference LOCO. ADQA *hurts* (raw_ensemble false-reject 8% > clip 2%). Honest scope: distinct/easier axis than the subtle-hallucination AUC 0.84; does not overturn it.
- Mistake to avoid (do not repeat): don't restate per-clip-normalised gate numbers as a headline — they bake the answer in. Use RAW signals + held-out calibration for any deployment claim.

### 2026-06-09T09:53:36Z — claude round 2
- **Mistake avoided:** codex re-ran best_of_n_rerank.py on cached clips burning credits; I added zero LLM calls and built a free analysis on the existing CSV. Also avoided the "re-computed locked gate numbers" trap by extending into a new deployment-honest variant instead of restating 100%.
- **New approach:** single-AD absolute-threshold gate with leave-one-clip-out tau calibration on RAW (un-normalised) scores — vs the min-of-pool relative gate (mine) and best-of-N rerank (codex's). Shows the gate survives without a candidate pool, and that CLIP-only beats the ensemble on this axis.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1
- Summary: # Round 002 — claude **Angle:** `wrong_content_gate` ## Baseline (re-ran the free gate, as tasked) `gate_outcome.py` (min-of-pool, relative, ranks 4 candidates / clip, rejects lowest): | signal | catch | ship-best | false-reject | n | |---|---|---|---|---| | ensemble | 100% | 90% | 0% | 60 | | adqa_only | 100% | 88% | 0% | 60 | |...

### 2026-06-09T09:53:36Z — codex round 1
- Summary: # Codex round 001 BREAKTHROUGH: Self-consistency hallucination gate catches human visual lies without an expert AD reference ## Executive result Expanded the suggested second-generation AD cache and reran `gate_review_holes`. The strongest outcome is not another rank correlation: it is a deployable safety gate. Using only local CLIP visual grounding-drop, with a machine-generated AD as the reference and other same-generation ADs...

### 2026-06-09 — codex round 2 (angle clip_local_analysis)
- NEW_APPROACH: two-scorer CLIP consensus floor (`min(SceneTwin CLIP, benchmark CLIP)`) on existing `benchmark_clip_sanity.csv`; this is cross-scorer agreement, not an absolute raw tau and not a candidate-pool gate.
- Outcome: modest negative result, not a breakthrough. Consensus floor rho = 0.739 vs best single CLIP rho = 0.735 on 18x4 ladder; full order unchanged at 10/18, adjacent wins unchanged at 46/54, LOCO wrong-content false-reject improves only 11.1% → 9.3%.
- Mistake avoided: source-audited `external_clip_full_eval.csv` and did not claim `vt_consistency` / `story_recall` as CLIP-only because they are lexical/pro-AD-derived fields.

### 2026-06-09 — claude round 3 (angle human_lies_expand)
- NEW_APPROACH: stratified the 5 NEW hand lies by swap TYPE — relational/action/count with all salient nouns held fixed — to red-team the gate, vs codex self-consistency ref-swap and my round-2 absolute-threshold gate.
- BREAKTHROUGH/limitation: CLIP grounding-drop gate is OBJECT-BIASED. Object/scene lies AUC 0.914; relational/action/count lies AUC 0.320 (below chance), mean drop -0.0024 (CLIP ranks some lies HIGHER than truth). Adding them drags combined human-lie AUC 0.914→0.783.
- Mistake to avoid (do not repeat): do not cite the 0.91 human-lie AUC as a robustness/safety win — it only ever tested noun/color/setting swaps CLIP can ground. The n=60 headline inherits the same noun-swap construction and blind spot. Wrong-who/wrong-action/wrong-count hallucinations (most dangerous for blind viewers) slip through. Next: pair CLIP with ADQA who/what/count questions.

### 2026-06-09T10:01:36Z — claude round 3
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:05:36Z — codex round 2
- **Mistake avoided:** avoided repeating Claude's single-AD absolute raw-score threshold and avoided claiming the per-clip-normalised pool gate; also rejected a tempting lexical temporal composite after source audit because it was not strict CLIP-only.
- **New approach:** two-scorer CLIP consensus floor across existing local CLIP score columns, requiring agreement between independent CLIP scoring recipes for the same AD instead of calibrating an absolute tau or ranking a candidate pool.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/2
- Summary: # Round 002 — codex **Angle:** `clip_local_analysis` ## Signal Tested `clip_consensus_min = min(SceneTwin CLIP score, benchmark CLIP score)` This is a conservative two-scorer CLIP agreement check: an AD only gets as much visual support as its weaker local CLIP scorer gives it. It uses the existing `cursor/output/benchmark_clip_sanity.csv` table only; no LLM, no CLIP rerun, no ADQA. I also inspected `external_clip_full_eval.csv`...

### 2026-06-09 — claude round 4 (angle tribe_gate_combo)
- NEW_APPROACH: first cross-LAYER combination — fuse TRIBE neural clip-triage (ρ-misorder router) with the CLIP wrong-content gate. Tested whether one risk score can do both jobs.
- FINDING (honest, not a breakthrough): the two layers are ORTHOGONAL — overlap=0, Spearman(gap,drop)=0.06, cross-AUC≈0.42 each way. A z-summed single risk score DILUTES and loses to TRIBE-alone at every low budget. Correct architecture = two independent OR-routers, not a fused scalar.
- Mistake to avoid (do not repeat): do NOT headline the OR-cascade's +15pt lift over TRIBE-only — it is partly DEFINITIONAL (gate flags exactly its clip_drop<=0 failures; permutation p≈0.80 reproduces the lift by chance). Load-bearing result is the orthogonality, which empirically justifies the two-layer design. Always permutation-test a cascade whose flag rule shares a variable with its failure label.
