---
title: Gate review-hole closure (human lies + self-consistency)
category: research
tags: [hallucination, gate, construct-validity, self-consistency, circularity]
sources: [cursor/data/human_hallucinations.jsonl, cursor/pipeline/gate_review_holes.py]
created: 2026-06-08
updated: 2026-06-08
---

## What we closed (before the paper subsection)

Two reviewer-killers, both zero API credits:

1. **Same-family circularity** — 18 hand-authored fabrications (`cursor/data/human_hallucinations.jsonl`). CLIP grounding-drop vs expert reference: **AUC 0.91**, mean drop +0.069 (lie) vs +0.005 (paraphrase). Gemini lies on same 18 clips: AUC 0.94. Human lies separate *more*, not less.

2. **Reference-free identity** — self-consistency gate: reference = second model generation (machine AD / bon c0), clean = alternate candidates c1–c3. n = 5 clips (15 clean pairs): **AUC 0.76**, 60% recall @ 13% FPR. Preliminary; cache expansion queued.

## Headline for the paper (defensible)

**CLIP-only grounding-drop gate, expert reference, n = 60: AUC 0.84, 70% recall @ 10% FPR.** Grader-free in the decision. Fusion 0.90 is a footnote (ADQA inherits Gemini grader dependence).

Paper subsection: `output/reports/paper-ad-safety-gate.md`

## See Also

- [[research/hallucination-gate]] — sensitivity + complementarity
- [[research/claim-level-gate]] — zero-reference negative + fusion ROC

## Sources

- `cursor/output/gate_review_holes.json`
- `output/charts/scenetwin_gate_review_holes.png`
