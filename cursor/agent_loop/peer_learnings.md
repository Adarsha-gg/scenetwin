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
