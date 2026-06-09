# Wrong-content catch is a real single-AD gate, not a normalization artifact

**Round 68 · claude · angle `wrong_content_gate`**

## Question

`gate_outcome.py` reports **catch=100%, ship-best=90%** (ensemble) vs random pool gate
25%. But the catch is computed by ranking a 4-candidate pool and rejecting the *lowest*
on **per-clip min-max-normalised** columns — which force `tier0_cross` to exactly 0.0
whenever it is the pool minimum. So the 100% is partly tautological and, worse,
undeployable: at inference you have ONE audio description, not a clean 4-way pool.

Does the wrong-content catch survive as a **single-AD global absolute gate** on the
**raw** (un-normalised) CLIP score, with no candidate pool?

## Raw-score separation (no normalization)

| tier | raw `clip_top3` mean | min | max |
|---|---:|---:|---:|
| tier0_cross (wrong clip) | 0.074 | -0.021 | **0.217** |
| tier1 vatex short | 0.306 | 0.178 | 0.422 |
| tier2 vatex long | 0.305 | 0.199 | 0.378 |
| tier3 va11y (expert) | 0.323 | **0.223** | 0.399 |

Wrong-content ADs sit ~4x lower than every legit tier; the cross max (0.217) barely
touches the expert min (0.223). The catch is **not** a normalization artifact — the raw
grounding signal carries it.

## Single-AD global gate (no pool)

Positive = `tier0_cross` (60), negative = all legit ADs (180).

| operating point | catch | false-alarm | note |
|---|---:|---:|---|
| reject-AUC | **0.999** | — | wrong-content vs legit, raw CLIP |
| in-sample Youden (T=0.223) | 100% | 1.7% | optimistic |
| **leave-one-clip-out** | **98.3%** | **2.2%** | honest, T never fit on scored clip |
| fixed a-priori T=0.15 | 90% | 0.0% | zero fitting |

LOCO threshold is stable across folds (0.199–0.224, median 0.223).

## Outcome

A single fixed raw-CLIP threshold turns the relative pool-ranking gate into a
**deployable single-AD wrong-content gate**: 98% catch at 2% false-alarm with no
candidate pool and no per-clip normalization, vs the 25% random-pool baseline. The
`gate_outcome.py` 100% headline is therefore real in substance, but should be reported
as a *global absolute threshold* result (LOCO 98/2) rather than a per-clip pool minimum.

## Honest scope

- This catches **wrong-clip / wrong-content** ADs (massive grounding collapse). It does
  NOT address the relational/action/count blind spot from round 3 — those keep nouns and
  stay near the legit raw-CLIP band, so a global low-grounding threshold cannot see them.
  The two limitations are complementary: this gate is for catastrophic mismatch, the
  relational stratum is for subtle in-distribution lies.
- 60 wrong-content clips, single CLIP backbone. Same external eval set as the headline.

Artifacts: `cursor/output/wrong_content_global_gate.json`,
`output/charts/scenetwin_wrong_content_global_gate.png`,
`cursor/pipeline/wrong_content_global_gate.py`.
