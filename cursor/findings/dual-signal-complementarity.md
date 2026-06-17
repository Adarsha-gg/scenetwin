---
title: "[CORRECTED/RETRACTED] Dual-Signal on Hard Completeness — a Tie-Handling Artifact"
category: research
tags: [SceneTwin, ensemble, ADQA, CLIP, retraction, methodology, ties]
updated: 2026-06-07
---

# RETRACTED: "the dual signal strictly dominates ADQA on completeness"

An earlier version of this page claimed the ensemble strictly dominates ADQA-only on
the hard completeness ladder (half<full 55%->74%, "fixes 11, breaks 0", McNemar
p=0.0005). **That claim is wrong — it was an artifact of scoring ordering with a strict
inequality in the presence of ties.** Caught by adversarial self-audit. Kept here as a
cautionary methodological finding.

## Why it was wrong

ADQA scores are discrete (0/0.5/1 averaged over 10 questions), so on the half-vs-full
rung it produces **26 exact ties out of 58** and **zero genuine inversions** (full ⊇
half by construction, so ADQA(full) ≥ ADQA(half) always).

A strict `>` test counts every tie as an ADQA **failure**. The continuous ensemble
breaks those ties, so it *looks* like it "fixes" 11 clips — but:

- On the 26 ADQA-tie clips, **CLIP breaks the tie correctly only 11 times, wrong 15
  (42%, below chance, p=0.84).**
- Under **fair tie-aware scoring** (tie = 0.5): ADQA **0.776**, ensemble **0.741** —
  the ensemble is **worse**.
- "breaks 0" is near-automatic: a break needs ADQA strictly-correct AND ensemble wrong,
  but ADQA's strictly-correct cases have clear margins the ensemble rarely overturns,
  while all ambiguous ties can only ever count for the ensemble. The test was rigged by
  tie handling, not by signal quality.

The 1-sentence<half rung is a weak wash (tie-aware 0.879 vs 0.853; CLIP tie-breaks 59%,
not significant).

## Honest conclusion

On the genuinely hard completeness rungs, **the dual signal does not add discrimination
over ADQA-only.** CLIP cannot tell a half-length truncation from the full expert AD
(it breaks those ties at chance or below). This is consistent with the broader picture:
ADQA is the workhorse; CLIP's value is in-domain ρ lift and regime-specific content
(How-to), not fine-grained completeness.

## What DOES survive (3-tier ladder, separately audited)

On the corrected 3-tier ladder {cross<crowd<pro}, ADQA ties tier1-vs-tier3 on only
**2/60** clips, so the strict 50/60 -> 58/60 ensemble ordering gain is **not** a tie
artifact; it survives tie-aware scoring (0.954 -> 0.983). But it is **small** and lives
at the easy cross/crowd boundary, not the hard pro boundary. Modest, real, not dramatic.

## Methodological lesson (worth a sentence in the paper)

Report ordering with **tie-aware** scoring (ties = 0.5). Strict-inequality "full order"
or pairwise-win counts silently over-credit any continuous signal that breaks a discrete
signal's ties — even when it breaks them at chance. Several earlier "full_order"
numbers in this project use strict `<`; the 3-tier result was re-checked and holds, but
the completeness result did not.

## See Also

- [[findings/completeness-ladder]]
- [[findings/corrected-ladder-robustness]]
- [[research/scenetwin-signal-decomposition]]
