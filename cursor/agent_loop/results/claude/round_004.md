# Round 004 — claude

**Angle:** `tribe_gate_combo`

## Question

Two locked SceneTwin layers live on the same 60 external clips:
- **TRIBE clip-triage** — `accessibility_gap` (one scalar/clip) flags clips the AD metric **misorders** (ADQA-only AUC 0.79).
- **CLIP wrong-content gate** — per-AD grounding drop `clip_expert - clip_halluc` flags **hallucinated content** (ranks expert > lie on 57/60).

The obvious next step is to **fuse them into one clip-level risk score**. I tested whether that is the right architecture. Local only: reads `external_ensemble_eval.csv`, `halluc_gate.csv`, `tribe_counterfactual_external_per_clip.csv`. Zero LLM, zero CLIP rerun. New script `cursor/pipeline/tribe_gate_combo.py` → `cursor/output/tribe_gate_combo.json`.

## Result — the two layers are orthogonal, so you must NOT fuse them

| measure | value |
|---|---|
| ρ-fail clips (ADQA misorders) | 10/60 |
| gate-fail clips (drop ≤ 0) | 3/60 |
| **overlap** | **0** |
| Spearman(gap, drop) | **0.062** |
| AUC TRIBE → gate-fail | 0.415 |
| AUC gate-margin → ρ-fail | 0.418 |

TRIBE is **blind** to the gate's failures and the gate is blind to TRIBE's. Neither subsumes the other.

### Consequence: a summed single risk score *dilutes*

Union-failure recall (n_fail = 13) at a fixed human-review budget:

| budget | oracle | TRIBE-only | **z-summed** | OR-cascade |
|---|---:|---:|---:|---:|
| 10% | 46% | 31% | **23%** | 46% |
| 20% | 92% | 54% | **31%** | 62% |
| 30% | 100% | 62% | **54%** | 77% |

The z-summed score (`z(gap) + z(−drop)`) is **worse than TRIBE-alone** at every low budget — the gate's noise drowns the strong TRIBE signal. The correct architecture is two **independent** routers run in parallel (OR-cascade): the gate auto-flags its own low-grounding clips, TRIBE spends the rest of the budget on high-gap clips.

## Honesty caveat (why this is NOT a breakthrough)

The OR-cascade's *lift over TRIBE-only* is **partly definitional**: `gate_fail` is defined as `clip_drop ≤ 0` and the cascade flags `clip_drop ≤ 0`, so reserving those 3 slots catches them tautologically. A permutation that shuffles `clip_drop` reproduces the same ~+17% lift (p ≈ 0.80). So I do **not** claim the cascade number as a win.

The load-bearing, non-circular finding is the **orthogonality** (overlap = 0, Spearman 0.06, cross-AUC ≈ 0.42): it justifies SceneTwin's two-layer design empirically — a deployment that already runs the wrong-content gate gets **zero** ρ-misorder protection from it and genuinely needs TRIBE as a separate router, and vice versa. The negative architectural result (fuse-by-sum hurts) is the contribution.

## How this differs from peers

- **codex r2** (CLIP consensus floor): fused two CLIP scorers by `min()`; got a marginal ρ result. I tested fusion across two *orthogonal* layers (neural triage × grounding gate) and showed fusion is the *wrong* move here.
- **my r2** (absolute-τ wrong-content gate) and **r3** (object-bias red-team): both single-signal, single-task. This is the first cross-layer combination, and it reports a fusion *anti-result* with the tautology flagged.

## Limits

n = 13 union failures is small; treat recall as directional. Targets the ADQA-backbone deployment (full ensemble misorders only 2/60).

COMMANDS_RUN: .venv/bin/python (join + orthogonality probe on /tmp/combo.csv), .venv/bin/python (OR-cascade vs summed recall curve), .venv/bin/python (permutation + threshold sensitivity), .venv/bin/python cursor/pipeline/tribe_gate_combo.py
MISTAKE_AVOIDED: codex fused two same-family CLIP scores and got a marginal/null lift but still framed it as a candidate metric; I fused two layers, found summing actively *hurts*, and refused to headline the cascade lift after a permutation showed it is definitional.
NEW_APPROACH: cross-layer combination — test whether TRIBE neural clip-triage and the CLIP wrong-content gate can share one risk score; prove they are orthogonal (overlap 0) so the correct design is two independent OR-routers, not a fused scalar. First round to combine the triage and gate layers rather than tune one of them.
PR: https://github.com/Adarsha-gg/scenetwin/pull/3
