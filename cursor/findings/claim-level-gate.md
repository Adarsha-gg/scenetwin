---
title: From Sensitivity to a Calibrated Hallucination Gate (what's deployable, what isn't)
category: research
tags: [hallucination, gate, clip, adqa, calibration, deployment, roc]
sources: [cursor/pipeline/claim_level_gate.py, cursor/pipeline/gate_summary.py, cursor/output/gate_summary.json]
created: 2026-06-08
updated: 2026-06-08
---

## Goal

[[research/hallucination-gate]] showed SceneTwin is *sensitive* to fabrication (a 2-3 fact
swap drops CLIP grounding ~5× more than a faithful paraphrase, p<1e-4). This page pushes
that into an actual **gate with an operating point** and is honest about where it works.

All numbers on the same 60 OOD clips: expert AD vs a same-length **hallucinated** twin
(2-3 visual facts swapped) and a same-length **faithful-paraphrase** control (negatives).
Operating point fixed at **10% false-positive rate** (flagging a truthful AD).

## Three gate designs

| gate | reference needed? | AUC | recall @ 10% FPR |
|---|---|---|---|
| zero-reference: weakest CLIP **claim** grounding | none | **0.58** | 17% |
| with-reference: CLIP grounding **drop** vs a trusted AD | 1 reference AD | **0.84** | 70% |
| with-reference: **CLIP-drop + ADQA-drop fused** | 1 reference AD | **0.90** | 72% |

## What works: the reference-comparison gate (AUC 0.90)

In the realistic QA setting you almost always have *something* to compare against — a prior
approved AD, the previous version before a re-edit, or a second independent generation.
Scoring the candidate's **grounding drop** against that reference is a strong gate:
CLIP-drop alone AUC 0.84, and **fusing CLIP-drop with ADQA-drop reaches AUC 0.90, catching
72% of hallucinations while wrongly flagging only 10% of truthful ADs.** The fusion beats
either signal alone (0.84 / 0.80 → 0.90) — the dual-signal design pays off *operationally*,
not just in correlation, and consistently with the complementarity result.

## What doesn't (yet): the zero-reference gate (AUC 0.58)

Decomposing the AD into atomic claims and flagging by the weakest CLIP claim grounding is
**near chance (AUC 0.58, 17% recall)**. Why: absolute per-claim grounding has high baseline
variance — CLIP scores a *true* abstract/action claim ("creating a steady rhythm") as low as
a *fabricated* object, so the weakest claim of an honest AD looks like a lie. A within-AD
standardized-minimum variant was *worse* (AUC 0.46). The reference comparison works precisely
because it cancels this per-claim baseline.

A weaker positive does survive at the **claim** level: fabricated claims are less grounded
than true claims (0.197 vs 0.237, AUC 0.69), so surfacing an AD's lowest-grounded claims
*enriches* fabrications for human review — useful as triage/highlighting, not auto-reject.

## Deployment recommendation

- **Ship it as a reference-comparison gate.** Given any trusted reference AD, flag a new
  AD whose CLIP+ADQA grounding drops past τ (calibrated at 10% FPR): catches ~72% of
  same-length fabrications. Pair with human review on the flagged slice.
- **Do not** ship the zero-reference single-AD gate as auto-reject; use claim grounding only
  to *highlight* suspect claims for a reviewer.

## Honest caveats

- Hallucinations and claim decomposition were produced by Gemini (the grader family);
  an independent grader (Opus/GPT) rerun is still blocked — credits confirmed **empty on
  2026-06-08** (Anthropic balance too low, OpenAI quota exceeded). The *decision* signal is
  CLIP (grader-free), so the gate ROC does not depend on the grader; only the ADQA-drop arm
  and the claim split do.
- n=60 OOD clips, one fabrication per clip. Real-world hallucinations vary in severity; a
  single subtle swap is harder than a gross one.

## See Also

- [[research/hallucination-gate]] — the controlled sensitivity result this gate is built on
- [[research/dual-signal-complementarity]] — retracted tie-artifact version (the wrong way)
- [[research/NEXT-STEPS]] — independent-grader rerun (still credit-blocked)

## Sources

- `cursor/pipeline/claim_level_gate.py`, `cursor/pipeline/gate_summary.py`
- `cursor/output/gate_summary.json`, `cursor/output/claim_level_gate.json`
- `output/charts/scenetwin_gate_summary.png`, `output/charts/scenetwin_claim_gate.png`
