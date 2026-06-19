# SceneTwin Paper Evidence Check — Corrected 3-Tier

Date: 2026-06-19

## Paper benchmark

The active paper uses the corrected three-tier ladder:

```text
T0 cross-decoy < T1 crowd caption < T3 professional AD
```

The old long-VATEX tier is excluded because it is the longest of equal-status crowd captions and is not a quality rung.

## Commands run

```bash
uv run --with numpy --with pandas --with scipy --with matplotlib python cursor/pipeline/fake_rung_analysis.py
uv run --with numpy --with pandas --with scipy --with matplotlib python cursor/pipeline/corrected_ladder_robustness.py
uv run --with numpy --with pandas --with matplotlib python cursor/pipeline/gate_outcome.py
uv run --with numpy --with pandas --with matplotlib python cursor/pipeline/wrong_content_global_gate.py
uv run python cursor/pipeline/gate_shipbest_selective.py
uv run --with numpy --with pandas --with scipy python cursor/research/vlm_judge_analyzer.py
```

A pure-Python CSV reader and tie-aware Spearman implementation were also used to verify the corrected-ladder metrics below.

## Verified corrected-ladder metrics

| Corpus | Rows | Clips | Spearman ρ | Fully ordered | T3-vs-lower wins | All pairwise wins |
|---|---:|---:|---:|---:|---:|---:|
| In-benchmark corrected 3-tier | 54 | 18 | 0.953777 | 17/18 | 36/36 | 53/54 |
| External corrected 3-tier | 180 | 60 | 0.947287 | 58/60 | 118/120 | 178/180 |

## Corrected-ladder market/baseline check

| Metric | In-benchmark ρ | External ρ | Note |
|---|---:|---:|---|
| SceneTwin CLIP+ADQA | 0.953777 | 0.947287 | no human reference AD |
| LLM-AD-Eval proxy | 0.941479 | 0.942097 | near tie; needs trusted T3/pro reference |
| ADQA alone | 0.855848 | 0.868929 | no human reference AD; model grader |
| CLIP alone | 0.835286 | 0.747319 | grader-free; useful for gates |
| Best frontier VLM judge | 0.863272 | 0.846791 | no reference, but weaker |
| CRITIC entity | 0.624949 | 0.687988 | weaker |

## VLM-as-judge corrected-ladder baselines

| Judge | In-bench ρ | External ρ | Combined ρ | External all-pair wins |
|---|---:|---:|---:|---:|
| Claude Sonnet 4.6 | 0.822243 | 0.821426 | 0.820116 | 167/180 |
| Gemini 2.5 Pro | 0.863272 | 0.833223 | 0.837012 | 167/180 |
| GPT-5 | 0.834740 | 0.846791 | 0.843371 | 169/180 |

## Safety artifacts verified

- `cursor/output/gate_summary.json`: hallucination grounding-drop gate, CLIP AUC 0.835, 70% recall @ 10% FPR; uses a clip-relevant anchor.
- `cursor/output/ref_subst/reference_substitution.json`: generated/model-anchor checks supporting the human-reference-free deployment path.
- `cursor/output/wrong_content_global_gate.json`: raw-CLIP wrong-content gate, 98.3% catch, 2.2% false alarm; no anchor/reference required.
- `cursor/output/gate_shipbest_selective.json`: ADQA margin selective ship-best, 100% at 80% coverage.

## Paper wording implications

- Do not claim large ranking superiority over the strongest reference-style baseline.
- Say the ranking result is **competitive/nearly tied** with LLM-AD-Eval proxy, not a blowout.
- The contribution is human-reference-free deployment plus gates and triage.
- Be precise: LLM-AD-Eval does not need a live human reviewer, but it needs a trusted reference/professional AD. The hallucination grounding-drop gate needs an anchor; the no-anchor version is a negative result.
