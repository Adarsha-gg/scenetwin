---
title: SceneTwin paper submission thesis memo
status: final thesis recommendation for same-day submission — corrected 3-tier version
created: 2026-06-19
updated: 2026-06-19
author: Adarsha Mishra, William Paterson University
sources:
  - output/reports/paper-scenetwin-audit-framework.md
  - output/reports/scenetwin-paper-evidence-check.md
  - cursor/output/fake_rung_analysis.json
  - cursor/output/corrected_ladder_robustness.json
  - cursor/output/gate_summary.json
  - cursor/output/wrong_content_global_gate.json
---

# SceneTwin Submission Thesis — Corrected 3-Tier Version

## Final verdict

Submit **one paper** framed as a **human-reference-free audio-description audit framework**.

Do **not** claim we massively beat the industry on ranking. On the corrected three-tier ladder, SceneTwin is excellent, but the strongest reference-style LLM-AD-Eval proxy nearly ties it. The paper is still worth submitting because the contribution is not just rho; it is **human-reference-free scoring + safety gates + review triage**.

## One-sentence thesis

**SceneTwin is a deployable audit layer for AI audio description: it ranks candidate ADs without a human reference AD, gates fluent-but-wrong descriptions, and routes uncertain clips to review.**

## Primary benchmark

Use the corrected three-tier ladder only:

```text
T0 cross-decoy < T1 crowd caption < T3 professional AD
```

The old long-VATEX tier is excluded because it is not a quality label; it is the longest of several equal-status crowd captions and mostly measures verbosity.

## Locked 3-tier numbers

| Corpus | Clips | Rows | ρ | Fully ordered | T3-vs-lower wins | All pairwise wins |
|---|---:|---:|---:|---:|---:|---:|
| In-benchmark | 18 | 54 | 0.954 | 17/18 | 36/36 | 53/54 |
| External | 60 | 180 | 0.947 | 58/60 | 118/120 | 178/180 |

These are the numbers to use in the abstract.

## Honest market comparison

| Comparator | In-benchmark ρ | External ρ | Honest interpretation |
|---|---:|---:|---|
| SceneTwin CLIP+ADQA | 0.954 | 0.947 | best, reference-free |
| LLM-AD-Eval proxy | 0.941 | 0.942 | nearly tied, but reference-style/offline |
| Best frontier VLM judge | 0.863 | 0.847 | clearly behind structured grounding |
| ADQA alone | 0.856 | 0.869 | strong but lower |
| CLIP alone | 0.835 | 0.747 | useful for gates, weak alone |

So yes: **we are not much better than the strongest reference-style metric on rank correlation.** The ranking improvement is small: about +0.013 in-benchmark and +0.005 external.

But LLM-AD-Eval-style scoring needs a trusted reference/professional AD for the clip. It does not need a live human reviewer at scoring time, but someone already had to produce the reference. SceneTwin is more deployable for undescribed videos because its ranking score and wrong-content gate do not need that professional reference AD. The hallucination grounding-drop gate needs a clip-relevant anchor; the deployment path is a generated anchor, and the no-anchor variant is a negative result. SceneTwin is also meaningfully better than generic frontier VLM judges on this task.

## The real contribution

The paper should say:

> SceneTwin is not a new AD generator and not a claim of overwhelming leaderboard dominance. It is a deployable audit stack. It gives a human-reference-free score competitive with reference-style metrics, then adds safety gates and review policy that rank-only metrics do not provide.

## Safety claims to keep

| Gate | Result | Keep? |
|---|---|---|
| Hallucination CLIP grounding-drop | AUC 0.835, 70% recall @ 10% FPR | Yes, but say it uses a clip-relevant anchor; no-anchor fails |
| Wrong-content raw-CLIP | 98.3% catch, 2.2% false alarm | Yes |
| ADQA margin selective ship-best | 100% at 80% coverage | Yes, shorter |
| TRIBE review triage | ADQA failure AUC 0.79 | Yes, secondary |

## What to remove from the paper

Remove/demote:

1. Old four-tier result tables.
2. Old four-tier professional-vs-lower comparison counts as primary numbers.
3. Claims that SceneTwin beats every industry method by a large margin.
4. Brain-grounded steering as the main story.
5. Access Surface OS.
6. 0.965 tuned/multi-judge headline.

## What to write instead

Abstract sentence:

> On a corrected three-tier ladder that excludes a verbosity-only crowd-caption rung, SceneTwin reaches ρ = 0.954 in-benchmark and ρ = 0.947 on 60 external clips, with 58/60 external clips fully ordered. A strong reference-style LLM-AD-Eval proxy nearly ties this ranking result, so SceneTwin’s main contribution is deployability: human-reference-free scoring plus calibrated safety gates for hallucination and wrong-content failures.

Discussion sentence:

> SceneTwin should not be read as evidence that a small metric crushes all current AD evaluation. The closest reference-style baseline is nearly tied. The contribution is that comparable ranking can be achieved without a human reference, and then converted into deployment decisions: reject, ship, or review.

## Why it is still paper-worthy

Because the field needs exactly this layer:

- VideoA11y and related systems generate better descriptions.
- RNIB-style deployment concerns say human review remains necessary.
- LLM-AD-Eval/reference metrics are good offline but not always available live.
- VLM judges are plausible but weaker than structured grounding in your measurement.
- SceneTwin supplies the missing audit stack: score, gate, triage.

## Final claim boundary

Do claim:

- corrected 3-tier ρ = 0.947 external;
- reference-free scoring is competitive with reference-style baselines;
- VLM judges trail structured grounding;
- gates catch hallucination/wrong-content operating points;
- TRIBE is review triage, not scoring.

Do not claim:

- massive industry domination;
- BLV user utility validation;
- better AD generation than VideoA11y;
- CLIP catches relation/count hallucinations;
- TRIBE improves rho.
