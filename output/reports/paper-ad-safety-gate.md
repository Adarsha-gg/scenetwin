---
title: Paper subsection - AD safety gate
status: definitive agent-loop synthesis for paper subsection
created: 2026-06-08
updated: 2026-06-09
sources:
  - cursor/output/gate_review_holes.json
  - cursor/output/gate_summary.json
  - cursor/output/gate_outcome.json
  - cursor/output/hallucination_gate.json
  - cursor/output/ref_subst/reference_substitution.json
  - cursor/output/wrong_content_global_gate.json
  - cursor/output/gate_deployment_precision.json
  - cursor/output/gate_margin_robustness.json
  - cursor/output/wrong_content_confounder.json
  - cursor/output/gate_shipbest_selective.json
  - cursor/findings/human-lies-relational-stratum.md
---

# X. AD Safety Gate: From Ranking Scores to Deployment Decisions

## X.1 Motivation

SceneTwin's paper-level claim is not simply that an audio-description metric correlates with ordered quality tiers. The deployment question is sharper: can the system prevent a harmful AD from shipping when the text is fluent but visually wrong? For blind and low-vision viewers, two failures are especially costly. First, a hallucinated AD can state unsupported visual facts while sounding plausible. Second, a catastrophic wrong-content AD can describe the wrong clip entirely. Both failures are safety outcomes, not rank-correlation outcomes.

The agent-loop work therefore reframed SceneTwin as a set of gates. A gate is evaluated by catch rate, false-positive rate, ship-best behavior, and deployment precision, with honest controls for base rate, reference dependence, and object-bias. All results below use existing cached artifacts; no new experiments were run for this synthesis.

The defensible headline is the grader-free CLIP result: a CLIP-only grounding-drop hallucination gate reaches AUC 0.84 and 70% recall at 10% false-positive rate on 60 held-out clips. We lead with this number because the decision uses only local CLIP visual grounding, not a VLM grader. The stronger fused result, AUC 0.90, is useful but is footnoted as grader-dependent because the ADQA arm uses a model grader.

## X.2 Hallucination Grounding-Drop Gate

The primary hallucination gate compares the visual grounding of a candidate AD to a clip-relevant anchor AD:

```text
drop = CLIP(anchor AD, frames) - CLIP(candidate AD, frames)
```

The detector flags a candidate when this drop exceeds a threshold calibrated on faithful paraphrase controls. On 60 external clips, each clip has an expert AD, a same-length corrupted twin with 2-3 concrete visual facts changed, and a faithful paraphrase. Mean length delta is 0.83 words, so the gate is not detecting verbosity.

The locked CLIP-only operating point is:

| gate | decision signal | n | AUC | recall @ 10% FPR | threshold |
|---|---|---:|---:|---:|---:|
| grounding-drop | CLIP only | 60 | 0.835 | 0.700 | 0.0238 |

This is the main paper claim: a deterministic local visual-grounding signal catches 70% of hallucinated descriptions while falsely flagging 10% of faithful rewrites. The raw sign of "expert beats candidate" is not enough: CLIP also ranks the expert above faithful paraphrases 65% of the time. The useful signal is magnitude. Corrupted twins lose about five times more CLIP grounding than faithful paraphrases (+0.0369 vs +0.0077; paired p = 3.1e-8).

The result also explains why CLIP is load-bearing. ADQA catches 70% of hallucinations, but it ties the lie with the truth on 17/60 clips when the fabricated fact is not one of the probed frame questions. On exactly those ADQA-blind clips, CLIP catches 100% by grounding-drop magnitude (+0.0348 for hallucinations vs +0.0058 for paraphrases; p = 7.6e-5). This is a construct-validity result: the gate reacts to unsupported visual content rather than wording.

Two controls define the boundary. The zero-reference weakest-claim gate fails: AUC 0.585 and only 16.9% recall at 10% FPR. Absolute claim grounding is too noisy. Conversely, CLIP+ADQA fusion reaches AUC 0.904 and 71.7% recall at 10% FPR, but that number should be reported as secondary because the ADQA component is grader-dependent. The paper should therefore headline the 0.84 CLIP-only gate and mention fusion as optional lift.

## X.3 Wrong-Content Catastrophic-Failure Gate

The second safety problem is not a subtle hallucination but a catastrophic mismatch: a `tier0_cross` AD describes another clip. In the original four-candidate gate, the ensemble rejects the wrong-content item on all 60 clips, with no false rejection of the genuine expert/pro AD and 90% ship-best accuracy:

| scorer | catches `tier0_cross` | false reject | ship-best | n |
|---|---:|---:|---:|---:|
| ensemble | 100% | 0% | 90.0% | 60 |
| ADQA only | 100% | 0% | 88.3% | 60 |
| CLIP only | 100% | 0% | 53.3% | 60 |

The random pool baseline is 25%, so the 100% catch is not just a rank-order convenience. A reviewer concern remained: the pool version uses per-clip normalized columns, which can make the wrong-content item the minimum by construction. Claude round 68 closed that hole by converting the result to a single-AD global threshold on raw, unnormalized CLIP scores. Wrong-content ADs have raw `clip_top3` mean 0.074, while legitimate ADs average 0.311. Leave-one-clip-out thresholding reaches 98.3% catch at 2.2% false alarm over 60 wrong-content positives and 180 legitimate negatives. The threshold is stable across folds (median 0.223; range 0.199-0.224), and a fixed a-priori threshold of 0.15 catches 90% with 0% false alarm in sample.

This makes the wrong-content gate deployable on a single AD: no candidate pool, no per-clip normalization, and no human reference. The result is best described as "global raw-CLIP LOCO 98%/2%" rather than only the original "100% pool catch."

The deployment caveat is base rate. At balanced prevalence the LOCO operating point has high precision, but catastrophic wrong-content ADs should be rare in production. Propagating TPR = 0.983 and FPR = 0.022 through Bayes' rule yields:

| wrong-content base rate | precision | recall | alert rate | reviews per true catch |
|---:|---:|---:|---:|---:|
| 10% | 83.1% | 98.3% | 11.8% | 1.2 |
| 5% | 70.0% | 98.3% | 7.0% | 1.4 |
| 2% | 47.4% | 98.3% | 4.1% | 2.1 |
| 1% | 30.9% | 98.3% | 3.2% | 3.2 |
| 0.5% | 18.2% | 98.3% | 2.7% | 5.5 |

At a 1% base rate, roughly two of three alerts are false. That does not invalidate the gate; it reframes it as an asymmetric-cost safety screen. The gate beats "ship all" at 1% prevalence if one missed wrong-content AD costs at least 2.2 wasted reviews, and at 0.2% prevalence if it costs at least 11.3 wasted reviews. For accessibility QA, that cost asymmetry is plausible, but the paper should not imply high PPV at low base rates.

The wrong-content ensemble is also not a knife-edge. Its per-clip normalized ensemble margin has median 0.594 and minimum 0.224. Under Monte Carlo Gaussian noise on raw ADQA and CLIP scores, catch remains 99.1% at noise equal to 0.5 times the genuine-AD score spread, 97.0% at 1.0 times, and 94.1% at 1.5 times. Single signals are weaker: the raw per-signal z-margin has median 4.24 genuine-AD SDs but 25.2% of signal-specific margins are below 1 SD and the minimum is 0. The ensemble lifts every clip off zero margin.

## X.4 Reference-Free Variants: Self-Consistency and Anchor Substitution

A strict reviewer objection is that a grounding-drop gate seems to require a human expert AD anchor. The reference-substitution experiments show that the gate needs a clip-relevant anchor, not a human one.

| anchor | description | n | AUC | recall @ 10% FPR |
|---|---|---:|---:|---:|
| A1 human expert | baseline anchor | 60 | 0.835 | 70.0% |
| A2 model paraphrase | model rewrite of anchor | 60 | 0.849 | 73.3% |
| A3a independent model AD | frames-to-AD vs Gemini lie | 9 | 0.728 | 55.6% |
| A3b independent model AD | frames-to-AD vs hand-authored lie | 9 | 0.815 | 66.7% |
| A4 cross-clip null | another clip's AD | 60 | 0.602 mean | 20.8% |
| A0 no anchor | absolute grounding only | 60 | 0.664 | 33.3% |

The A2 model-paraphrase anchor matches or slightly improves the human anchor (0.85 vs 0.84), showing that anchor wording and authorship are not the source of the lift. The A3 independent model-AD anchor is the cleaner reference-free result: no human text is used in the comparison, and it still catches hand-authored lies at AUC 0.81, albeit at n = 9 with wide confidence intervals. The cross-clip null collapses to 0.60, close to the no-anchor absolute floor of 0.66, so the anchor must describe this clip.

The best-of-N self-consistency expansion gives the same conclusion with a larger generated-reference cache. Codex round 1 reported self-consistency AUC 0.903 on 14 clips and 42 clean pairs. After cache expansion in round 3, the locked result is 16 clips, 48 clean pairs, AUC 0.895, 68.8% recall at 10.4% FPR, mean lie drop +0.0724 vs clean drop +0.0016. The slight drop from 0.903 to 0.895 is a stability cost, not a failure. Generated references help turn the hallucination gate into a reference-free deployment story, but they do not make SceneTwin a good best-of-N selector: the same cache expansion found ensemble top-1 similarity to expert below random candidate expectation (0.701 vs 0.707; p = 0.729). Generated ADs should be used as anchors for consistency checks, not sold as an automatic AD optimizer.

## X.5 Dual-Signal Complementarity and Selective Prediction

The agent loop found a sharper dual-signal story than "fusion improves rho." CLIP and ADQA are load-bearing for different deployment properties.

For hallucination detection, ADQA is vulnerable to question coverage: it misses fabrications it never asks about. CLIP covers those omissions through grounding-drop magnitude. For catastrophic wrong-content detection, CLIP is the better confounder separator. Against the hardest truthful confounder, `tier1_vatex_short`, CLIP separates sparse-but-correct ADs from wrong-content ADs with AUC 0.998 and 98.3% best global-threshold accuracy. ADQA reaches AUC 0.928 and 91.7% accuracy, but it puts a genuine short AD at or below the wrong-content AD on 7/60 clips. CLIP rescues all seven, with minimum raw gap +0.090.

For ranking the best genuine AD, the structure reverses. ADQA is the stronger ship-best signal: 88.3% at full coverage, compared with 53.3% for CLIP. The ensemble reaches 90.0%, only one clip above ADQA alone. This means CLIP should not be treated as an equal ranking signal for ship-best, even though it is essential for wrong-content rejection and thin-genuine confounder separation.

Selective prediction makes this deployable. Cross-signal agreement is the wrong confidence signal for ship-best: CLIP and ADQA agree on only 34/60 clips, and shipping only agreements gives 88.2% accuracy, worse than the full ensemble. On the 26 disagreements, ADQA is right 23 times and CLIP only twice. The useful confidence signal is ADQA's own intra-signal margin. Abstaining the lowest-margin 20% of clips sends 12 clips to human review and ships the remaining 48 at 100% ship-best accuracy; at 90% coverage, ship-best is 98.1%. Six of seven ADQA ship-best errors are exact ADQA ties. The practical policy is therefore split: use ensemble/CLIP evidence for reject decisions, and use ADQA margin for selective auto-ship decisions.

## X.6 Honest Limitations

The strongest negative is object bias. The CLIP grounding-drop hallucination gate is good at wrong-object, wrong-color, and wrong-scene lies, but it fails on relational/action/count lies that keep the salient nouns. In the human-lie red team, 18 object/scene swaps had AUC 0.914, while five new relational/action/count swaps had AUC 0.320. The combined human-lie AUC fell to 0.783. In one example, the lie kept objects such as person, basket, and food while changing who does what; CLIP ranked the lie higher than the truthful AD. The paper should state that the gate detects grounded content swaps, not all visually dangerous lies. Relational claims require ADQA-style explicit who/what/count questions or a different visual relation model.

The zero-reference claim gate is also a negative result. It is attractive because it needs no anchor, but the locked AUC is only 0.585 with 16.9% recall at 10% FPR. Absolute CLIP grounding cannot reliably distinguish true abstract claims from fabricated concrete ones. The successful reference-free path is not "no anchor"; it is "machine-generated clip-relevant anchor."

The wrong-content gate has low precision at low base rates. Its LOCO 98.3% recall and 2.2% FPR are real, but at 1% prevalence PPV is 30.9%. It should be deployed as a high-recall review trigger under asymmetric cost, not as a high-precision autonomous rejector.

Finally, the fused hallucination number, AUC 0.904, should be footnoted. It is better than CLIP-only, but the ADQA branch uses a grader. The grader-free headline remains CLIP-only AUC 0.84.

## X.7 Artifacts Table

| artifact | role in subsection | locked numbers |
|---|---|---|
| `cursor/output/gate_summary.json` | hallucination gate summary | CLIP drop AUC 0.835; 70% recall @ 10% FPR; zero-ref AUC 0.585; fusion AUC 0.904 |
| `cursor/output/hallucination_gate.json` | construct-validity and ADQA blind spot | CLIP hallucination drop +0.0369 vs paraphrase +0.0077; ADQA blind 17/60; CLIP catches 100% of blind spots |
| `cursor/output/gate_review_holes.json` | human-lie and self-consistency controls | human lies expert-ref AUC 0.783 after relational red team; self-consistency AUC 0.895 on 16 clips |
| `cursor/output/ref_subst/reference_substitution.json` | anchor substitution | human anchor AUC 0.835; model paraphrase 0.849; independent model AD vs human lies 0.815; cross-clip null 0.602 |
| `cursor/output/gate_outcome.json` | four-candidate wrong-content pool gate | ensemble catch 100%; false reject 0%; ship-best 90%; random catch 25% |
| `cursor/output/wrong_content_global_gate.json` | deployable single-AD wrong-content gate | raw CLIP LOCO catch 98.3%; false alarm 2.2%; reject AUC 0.999 |
| `cursor/output/gate_deployment_precision.json` | base-rate propagation | PPV 30.9% at 1% base rate; break-even miss/review cost 2.2x |
| `cursor/output/gate_margin_robustness.json` | wrong-content noise robustness | ensemble min margin 0.224; catch 99.1% at 0.5x genuine-score noise |
| `cursor/output/wrong_content_confounder.json` | thin-genuine confounder | CLIP AUC 0.998 vs ADQA 0.928; ADQA inversions 7/60; CLIP rescues all |
| `cursor/output/gate_shipbest_selective.json` | selective ship-best policy | ADQA margin: 100% ship-best at 80% coverage; cross-signal agreement fails |
| `cursor/findings/human-lies-relational-stratum.md` | object-bias limitation | object/scene AUC 0.914; relational/action/count AUC 0.320 |
| `cursor/output/best_of_n_rerank.json` | negative optimizer control | ensemble top-1 sim 0.701 vs random 0.707; p = 0.729 |
