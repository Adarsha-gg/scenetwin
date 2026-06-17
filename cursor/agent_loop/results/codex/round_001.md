# Codex round 001

BREAKTHROUGH: Self-consistency hallucination gate catches human visual lies without an expert AD reference

## Executive result

Expanded the suggested second-generation AD cache and reran `gate_review_holes`. The strongest outcome is not another rank correlation: it is a deployable safety gate.

Using only local CLIP visual grounding-drop, with a machine-generated AD as the reference and other same-generation ADs as clean controls, SceneTwin separates human-authored visual fabrications from clean second-generation alternatives:

- Self-consistency reference gate: AUC = 0.903 on 14 clips, 42 clean pairs.
- Operating point: 78.6% recall at 11.9% FPR.
- Cluster bootstrap over clips: AUC 95% CI = [0.760, 0.993].
- Within-clip permutation control: p ~= 0.0001.
- Mean grounding drop: human lie +0.0767 vs clean second-gen alternative -0.0024.
- Median grounding drop: human lie +0.0798 vs clean -0.0016.

This closes the most important review hole in the hallucination-gate story: the gate no longer needs the expert AD as the reference. It can use a second model-generated description as the consistency anchor and still catch human-authored false visual claims.

## Honest controls

Expert-reference gate remains the stronger and larger result:

- n = 60 CLIP-only expert-reference gate: AUC = 0.835, 70% recall at 10% FPR.
- Human-authored lies against expert reference: AUC = 0.914 on n = 18.
- Gemini-generated lies against expert reference: AUC = 0.938 on n = 18.

The expanded self-consistency gate is smaller than the n=60 expert-reference gate but is more paper-relevant as a deployment outcome: it shows the hallucination gate can operate without a human reference AD.

Verbosity control from the local audit:

- Mean word delta vs reference: human lies +1.79 words, clean second-gen alternatives +2.60 words.
- Drop-length Spearman rho = -0.194, p = 0.152.

So the signal is not explained by longer alternatives being penalized; if anything, the length association is weak and negative.

## Negative result from the suggested best-of-N reranker

I expanded the best-of-N cache from 5 usable clips to 17 usable clips with 4 candidates per clip. The re-ranking outcome is negative and should not be claimed:

- Ensemble top-1 similarity to expert AD: 0.704.
- Random candidate expected similarity: 0.711.
- Length-matched baseline: 0.706.
- Oracle best candidate: 0.755.
- Gain over random: -0.0076.
- Gain over length-matched: -0.0026.
- Win rate vs random: 41%.
- Wilcoxon p vs random: 0.771.

ADQA-only and CLIP-only were also negative. This is useful as a red-team result: SceneTwin's current score should not be sold as a best-of-N AD optimizer.

## Commands run

```bash
.venv/bin/python cursor/pipeline/best_of_n_rerank.py --limit 18 --n 4 --provider gemini
.venv/bin/python cursor/pipeline/gate_review_holes.py
```

I also ran a local one-off audit script to recompute self-consistency CLIP drops and estimate clustered bootstrap CIs/permutation p-values. No API calls were needed for the audit.

## Files updated by experiments

- `cursor/output/best_of_n/best_of_n_candidates.csv`
- `cursor/output/best_of_n_rerank.json`
- `cursor/output/gate_review_holes.json`
- `output/charts/scenetwin_best_of_n.png`
- `output/charts/scenetwin_gate_review_holes.png`

## Paper framing

Candidate claim:

> A CLIP grounding-drop gate detects human-authored hallucinated visual claims without a reference AD by comparing a candidate description against an independently generated machine AD. On 14 held-out overlap clips, the self-consistency gate reaches AUC 0.90 and 79% recall at 12% FPR, with clean same-model alternatives as false-positive controls.

Recommended wording caveat:

This is a promising subsection or ablation, not yet the sole headline. Keep the n=60 expert-reference CLIP gate as the primary safety result, and present self-consistency as the deployment-compatible extension.
