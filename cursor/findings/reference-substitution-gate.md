---
title: Reference-substitution robustness — the gate needs a clip-relevant anchor, not a human one
category: research
tags: [hallucination, gate, construct-validity, reference-free, self-consistency, controls]
sources: [cursor/pipeline/reference_substitution_gate.py, cursor/output/ref_subst/reference_substitution.json]
created: 2026-06-09
updated: 2026-06-09
---

## The reviewer-killer this closes

The headline gate scores `drop = clip(EXPERT_AD) - clip(candidate)`. Objection: *"That
isn't reference-free, it's reference-substituting — you lean on the human expert AD as the
per-clip anchor, and in deployment there is no expert AD."*

We swap the anchor and re-measure the gate, CLIP-only, **zero API credits** (grader-free in
the decision). `cursor/pipeline/reference_substitution_gate.py`.

## Result (n=60 unless noted)

| Anchor | What it is | AUC | recall@10%FPR |
|---|---|---|---|
| **A1 human expert** | headline baseline | 0.84 [0.76, 0.90] | 70% |
| **A2 model paraphrase** | model rewrite, *no human at scoring time* | **0.85** [0.77, 0.92] | 73% |
| **A3a indep model-AD** | frames→AD, vs Gemini lie (n=9) | 0.73 [0.46, 0.94] | 56% |
| **A3b indep model-AD** | frames→AD, vs **hand-authored** lie (n=9) | 0.81 [0.57, 1.0] | 67% |
| A4 cross-clip (NULL) | another clip's AD as anchor, 20 derangements | 0.60 ± 0.01 | 21% |
| A0 no anchor (absolute) | flag low absolute grounding | 0.66 [0.56, 0.76] | 33% |

Permutation p (A1 vs cross-clip null distribution): **p = 0.0** (0/20 derangements reach 0.84).

## What it means

1. **Anchor authorship is irrelevant.** Human-expert (0.84) ≈ model-paraphrase (0.85) ≈
   independent model-AD (0.73–0.81). The gate does *not* depend on a human reference — the
   system can supply its own anchor by describing the clip a second time.
2. **The anchor must be clip-relevant.** A random (cross-clip) anchor collapses to 0.60,
   which sits at the no-anchor absolute floor (0.66) — i.e. a wrong anchor adds noise, not
   signal. So the lift comes from the anchor *describing this clip*, not from any text being
   present.
3. **Strongest single cell:** independent model-generated anchor (no human text anywhere in
   the pipeline) catches **hand-authored** lies at **AUC 0.81**, grader-free. This breaks the
   human-reference dependency *and* the Gemini same-family circularity simultaneously.

This converts "you cheated with the human reference" from an open hole into a falsified
objection, and makes the reference-free claim honest: SceneTwin audits a candidate AD by
generating its own clip description as the anchor and measuring CLIP grounding drop.

## Honest limitations

- A2's paraphrase is derived from the expert *text*, so it proves "anchor authorship/wording
  is interchangeable," not "no seed description needed." The fully-independent claim rests on
  A3 (frames→AD), which is real but underpowered at **n=9** (wide CIs). Expanding A3 to n=60
  needs API credits to generate one more independent AD per clip.
- The null floor is 0.60, **not** 0.50: the absolute-grounding component (A0=0.66) survives
  anchor randomization. Report the null honestly as "degrades to the no-anchor floor," not
  "collapses to chance."

## See Also

- [[research/gate-review-holes]] — the n=5 self-consistency precursor this supersedes
- [[research/hallucination-gate]] — sensitivity + specificity of the grounding-drop signal
- [[research/claim-level-gate]] — zero-reference negative (AUC 0.58)

## Sources

- `cursor/output/ref_subst/reference_substitution.json`
- `output/charts/scenetwin_reference_substitution.png`
