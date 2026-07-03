---
title: SceneTwin hardening audit — red-team pass on the research
category: research
tags: [scenetwin, hardening, audit, reproducibility, statistics, overclaim]
created: 2026-07-02
---

# SceneTwin hardening audit (2026-07-02)

A red-team pass over the manuscript and the directions-loop findings, prioritizing
**verification** (re-running the source scripts) over opinion. Repro:
`cursor/research/loop_harden_cis.py` plus re-runs of `recompute_corrected_ladder.py`,
`loop_d6_omission.py`, `loop_d7d8_fusion_oppoints.py`.

## What reproduces cleanly (verified this pass)

| Claim | Re-run result | Status |
|---|---|---|
| Primary ladder ρ = 0.952 | recompute → 0.9516, fully-ordered 58/60 | ✅ exact |
| Pilot ladder ρ = 0.957 | recompute → 0.957, 17/18 | ✅ exact |
| Fused fabrication AUC 0.904 | loop_d7d8 → 0.904 (CLIP 0.835, ADQA 0.801) | ✅ exact |
| Omission clip-AUC 0.945 | loop_d6 → 0.945 | ✅ exact |
| Recall @10% FPR 75% (fusion) | loop_d7d8 → 75.0% | ✅ exact |
| min detectable ρ = 0.207 | recompute | ✅ supports power |

**New CIs computed** (clustered bootstrap over clips, B=5000): CLIP-drop 0.835 **[0.755, 0.906]**;
mean-fusion 0.904 **[0.845, 0.951]**; omission 0.945 **[0.872, 1.00]**.

## Findings (things hardened)

**H1 — Omission "grader-free" overclaim (I introduced it; FIXED).** The 0.945 omission AUC
is computed against the cached `*_ad_mentions_true` labels, which are **model-annotated**.
The strict lexical substring detector reproduces those labels at 94.7% / 0 FP (a feasibility
signal), but its *end-to-end separation* AUC was never measured; the only lexical detector
turned into a separation score is the loose token-overlap variant at **0.671**, not 0.945.
The manuscript's "so omission detection needs no model grader" was therefore not established.
Fixed: attributed 0.945 to model labels, added the CI, downgraded the claim to "grader-free
detector is *feasible*, end-to-end number not yet established," and added a limitation.

**H2 — Missing confidence intervals (FIXED).** Detector AUCs were reported as point
estimates. Added clustered-bootstrap CIs to the manuscript. The fusion CI [0.85, 0.95]
**overlaps** the CLIP-only CI [0.76, 0.91], so the +0.069 fusion gain is consistent but
not decisive — now stated as such. The omission CI [0.87, 1.00] is wide (n=23) and hits the
ceiling, reinforcing "pilot."

**H3 — Omission ground-truth circularity (FIXED via caveat).** The key-fact mention labels
are model-generated and may share model lineage with ADQA grading; the omission result is
validated against model labels, not human ground truth. Added to Limitations.

**H4 — Visual-proxy claim was loosely worded (FIXED).** The significant negative motion
correlation is with the *mean visual gap* (ρ≈−0.4), not the triage signal itself;
`accessibility_gap` is only weakly, non-significantly motion-correlated (ρ=−0.21). Reworded
to be precise — which actually *strengthens* the "not motion in disguise" argument.

**H5 — Multiple-comparisons transparency (FIXED via caveat).** ~20 directions were swept;
the positive detection results are the survivors. Added an explicit Limitations bullet noting
the selection and that the many nulls are reported alongside (they already are).

**H6 — D21 dropped-clip robustness (CHECKED, PASSES).** 3/60 clips failed to download.
Verified all **10 ADQA-failure positives were retained** (the 3 dropped are negatives), so
the n=57 triage AUC 0.796 is not inflated by dropping hard cases. No action needed.

## Standing weaknesses NOT fixable here (honest register)

- **Synthetic ground truth.** Ranking rests on tier construction; ADQA uses model grading;
  the hallucination gate's anchor is the expert AD and its positives are corruptions of that
  same expert (deployment lacks the anchor — the no-anchor gate is a reported negative at
  0.585). These are already caveated; they remain the core validity threat and need a BLV /
  human-labeled study (gated: no budget).
- **Small positive counts.** Triage AUC 0.794 has 10 positives; gate CIs are wide. Robust to
  permutation/bootstrap but underpowered for fine comparisons.
- **Grader dependence** of ADQA (Gemini/Claude/GPT) — cross-model gen/grade mitigates but
  does not eliminate circularity.

## Net

No headline number failed to reproduce. One overclaim I had introduced (omission = grader-free)
is corrected; CIs and multiple-comparison / label-provenance caveats are added. The paper's
honest claim boundary is intact and now tighter.
