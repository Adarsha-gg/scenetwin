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

### 2026-06-09T10:09:36Z — claude round 4
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:12:24Z — codex round 3
- **Mistake avoided:** avoided repeating Claude's object-bias overclaim and Codex's earlier cache-waste pattern; used no refresh and expanded only the uncached prefix.
- **New approach:** coverage-stability stress test for generated self-consistency references: add uncached best-of-N clips, then check whether self-consistency and best-of-N selection improve out of sample.
- **Outcome:** cache files 85→95; complete best-of-N clips 17→19; self-consistency clips 14→16, but AUC 0.903→0.895 and recall 0.786→0.688. Best-of-N selection remains below random expert-similarity baseline. No PR: output-only negative/guardrail result.

### 2026-06-09T10:13:36Z — claude round 5
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:17:36Z — claude round 6
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:21:36Z — claude round 7
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:25:36Z — claude round 8
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:29:36Z — claude round 9
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:33:36Z — claude round 10
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:37:36Z — claude round 11
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:41:36Z — claude round 12
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:45:36Z — claude round 13
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:49:36Z — claude round 14
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:53:36Z — claude round 15
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T10:57:36Z — claude round 16
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:01:36Z — claude round 17
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:05:36Z — claude round 18
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:09:36Z — claude round 19
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:13:36Z — claude round 20
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:17:36Z — claude round 21
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:21:36Z — claude round 22
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:25:36Z — claude round 23
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:29:36Z — claude round 24
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:33:36Z — claude round 25
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:37:36Z — claude round 26
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:41:36Z — claude round 27
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:45:36Z — claude round 28
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:49:36Z — claude round 29
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:53:36Z — claude round 30
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T11:57:36Z — claude round 31
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:01:36Z — claude round 32
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:05:37Z — claude round 33
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:09:37Z — claude round 34
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:13:37Z — claude round 35
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:17:37Z — claude round 36
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:21:37Z — claude round 37
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:25:37Z — claude round 38
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:29:37Z — claude round 39
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:33:37Z — claude round 40
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:37:37Z — claude round 41
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:41:37Z — claude round 42
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:45:37Z — claude round 43
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:49:37Z — claude round 44
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:53:37Z — claude round 45
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T12:57:37Z — claude round 46
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:01:37Z — claude round 47
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:05:37Z — claude round 48
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:09:37Z — claude round 49
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:13:37Z — claude round 50
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:17:37Z — claude round 51
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:21:37Z — claude round 52
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:25:37Z — claude round 53
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:29:37Z — claude round 54
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:33:37Z — claude round 55
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:37:37Z — claude round 56
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:41:37Z — claude round 57
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:45:37Z — claude round 58
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:49:37Z — claude round 59
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:53:37Z — claude round 60
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T13:57:37Z — claude round 61
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:01:37Z — claude round 62
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:05:37Z — claude round 63
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:09:37Z — claude round 64
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:13:37Z — claude round 65
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:17:37Z — claude round 66
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09T14:21:37Z — claude round 67
- **Mistake avoided:** codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
- **New approach:** stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/1 (round-3 commit 0ed5d67 appended)
- Summary: # Round 003 — claude **Angle:** `human_lies_expand` BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies ## What I did (different from "add 5 generic lies") Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard stratum**: relational / action / count / spatial swaps that keep every salient noun (car, forehead,...

### 2026-06-09 — claude round 68 (angle wrong_content_gate)
- NEW_APPROACH: single-AD GLOBAL absolute threshold on RAW (un-normalised) CLIP, validated leave-one-clip-out — tests whether gate_outcome's 100% pool-min catch is a per-clip-normalization artifact. Result: reject-AUC 0.999, LOCO catch 98.3% / false-alarm 2.2%, fixed T=0.15 -> 90% / 0%. New script cursor/pipeline/wrong_content_global_gate.py.
- Finding: wrong-content catch is REAL (raw CLIP separates ~4x: cross mean 0.074 vs legit ~0.31), deployable on single ADs without a candidate pool. Still blind to relational/action/count lies (round 3) — complementary limitations.

### 2026-06-09T14:29:37Z — claude round 68
- **Mistake avoided:** peer (codex) leaned on per-clip-normalised pool columns and accepted the relative pool-min catch at face value; I checked whether the 100% is a normalization artifact instead of restating it, and validated leave-one-clip-out so the threshold is never fit on the clip it scores.
- **New approach:** convert the relative 4-candidate pool-ranking gate into a single global ABSOLUTE threshold on RAW (un-normalised) CLIP, validated leave-one-clip-out — different from codex's two-scorer CLIP consensus floor, from my round-2 per-clip-tau single-AD gate on the human-lies jsonl, and from my round-3 relational-lie stratum. This is the deployment-mode (no pool) version of gate_outcome.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/4
- Summary: # Round 068 — claude **Angle:** `wrong_content_gate` BREAKTHROUGH: wrong-content catch survives as a single-AD GLOBAL raw-CLIP gate (LOCO 98% catch / 2% false-alarm) — not a per-clip-normalization tautology ## gate_outcome.py (free, as mandated) | scorer | catch | ship-best | false-reject | n | vs random 25% | |---|---:|---:|---:|---:|---:| | ensemble | 100% | 90% | 0% | 60 |...

### 2026-06-09T14:33:37Z — claude round 69
- **Mistake avoided:** peer (codex) and my own prior rounds reported the catch/false-alarm at balanced prevalence and implicitly treated it as the deployment number; I refused to restate 98%/2% as a deployment guarantee and exposed that precision is base-rate dependent (31% PPV at 1%), then showed why the gate is still justified (cost asymmetry) rather than overclaiming.
- **New approach:** Bayesian base-rate precision + decision-theoretic break-even propagation of the LOCKED LOCO operating point — different from codex's two-scorer CLIP consensus floor, my r68 global absolute threshold, my r2 per-clip tau, and my r3 relational-lie stratum. First round to characterise the gate's PRECISION/alert-burden/cost economics rather than its recall.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/4 (round-69 commit c752d7f appended)
- Summary: # Round 069 — claude **Angle:** `wrong_content_gate` BREAKTHROUGH: the locked wrong-content catch is a low-PRECISION safety screen — at a realistic 1% base rate PPV is only 31% (base-rate fallacy), but cost asymmetry justifies it down to 0.2% prevalence ## gate_outcome.py (free, as mandated) | scorer | catch | ship-best | false-reject | n | vs random 25% | |---|---:|---:|---:|---:|---:|...

### 2026-06-09 — claude round 70 (angle wrong_content_gate)
- NEW_APPROACH: separation-margin distribution + Monte-Carlo measurement-noise perturbation of the locked argmin gate. Median per-signal z-margin 4.2 genuine-AD SDs; catch ≥99% to 0.5× SD noise, ≥95% to 1.5×. Single-signal min margin = 0σ (25% <1σ) → ensemble fusion is what keeps every clip's margin off zero (min 0.224 norm). New script cursor/pipeline/gate_margin_robustness.py.
- MISTAKE_AVOIDED: all prior rounds (incl. peer consensus-floor) reported catch on noise-free scores; never tested robustness to measurement error. Don't treat 100% as a knife-edge OR as guaranteed — quantify its margin.

### 2026-06-09T14:37:37Z — claude round 70
- **Mistake avoided:** peer (codex) and my own prior rounds all reported catch on noise-free scores and never tested whether the 100% survives measurement error; I refused to restate the headline and instead stress-tested its margin, exposing that single-signal separation is brittle (25% <1σ, min 0σ) and quantifying why the ensemble is required.
- **New approach:** separation-margin distribution + Monte-Carlo measurement-noise perturbation of the locked gate decision (argmin re-normalised per trial) — answers "how brittle is the 100%" rather than recall/precision/prevalence. Different from codex's two-scorer consensus floor (a decision rule) and from my r2 tau, r68 threshold, r69 Bayesian base-rate. First round to characterise the gate's noise robustness and z-margin headroom.
- **PR:** https://github.com/Adarsha-gg/scenetwin/pull/5
- Summary: # Round 070 — claude **Angle:** `wrong_content_gate` BREAKTHROUGH: the 100% wrong-content catch is NOT brittle — median 4.2σ per-signal headroom, survives Gaussian measurement noise up to 0.5× the genuine-AD score spread before dropping below 99%; the safety is the *ensemble's*, which lifts every clip's margin off zero where single signals fail. ## gate_outcome.py (free, as mandated) | scorer | catch...
