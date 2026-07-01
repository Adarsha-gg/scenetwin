---
title: SceneTwin paper corpus — 37 papers, clusters, takeaways
category: research
tags: [scenetwin, related-work, paper-corpus, synthesis]
sources: [cursor/research/papers/CROSS-PAPER-SYNTHESIS.md, cursor/research/papers/INDEX.md, cursor/research/papers/sources/]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

We surveyed 37 papers across AD generation, AD evaluation, video understanding, BLV accessibility, and brain encoding. They cluster into 6 thematic batches (semantic alignment, narrative coverage, user agency, identity/domain/soundscape, assistant behavior, evidence loop). Together they imply a stronger product framing than "another AD scorer": **a routing layer over access surfaces under viewer, audio, identity, emotion, risk, latency, and compute constraints**. The full deep-dives per paper live in `cursor/research/papers/`; this page consolidates the corpus-level takeaways for paper Related Work sections.

## Cluster structure (Paper A Related Work)

Six clusters by what they optimize. Empirical correlations measured on our 18-clip benchmark in [[research/scenetwin-metric-landscape]].

### Cluster A — Semantic / reference alignment (rho 0.79-0.93 with our ensemble)

| Paper | arXiv | What it adds |
|---|---|---|
| ADQA | 2510.00808 | Frame-grounded MCQ scoring (our backbone) |
| AutoAD III | 2404.14412 | LLM-AD-Eval, CRITIC entity, multi-ref R@k |
| AVBench | 2605.24652 | VT consistency (text-video similarity) |
| ViDscribe | 2603.14662 | Query-coverage scoring |
| SemVideo | 2602.21819 | Hierarchical semantic similarity |

**Takeaway:** These metrics measure overlapping goals ("does the AD say what the video shows?"). Our ensemble integrates two of them (CLIP + frame-grounded ADQA) and beats the others by +0.030 on the benchmark. Adding more semantic-similarity metrics yields diminishing returns.

### Cluster B — Narrative / coverage (rho 0.60-0.70)

| Paper | arXiv | What it adds |
|---|---|---|
| CoAD / StoryRecall | 2510.25440 | Narrative beat recall + repetition penalty |
| TRIBE v2 | 2605.04326 | Brain-aligned counterfactual need curves |
| CA3D | 2412.10002 | Shot-level event detection |
| VideoA11y / G7G8 | 2502.20480 | Timing rubric for AD slots |
| IRT scalable QC | 2602.01390 | 6-dimension rubric scoring |

**Takeaway:** Narrative-and-timing measures correlate moderately with ensemble but add complementary signal on clips where pro AD is verbose-but-wrong. Our negative-results experiments showed fusing them does not lift ensemble rho; they help in failure analysis rather than headline ranking. TRIBE separately drives our binary review-triage flag.

### Cluster C — Conflicting / inverted on tier ranking

| Paper | Issue |
|---|---|
| CoAD repetition (alone) | Pro AD is longer + more repetitive; anti-correlates with tier GT |
| Multi-ref R@3/N | Trivial when T3 is one of the references (reference-leakage) |
| CRITIC entities (alone) | VATEX clips lack proper names; entity proxy is noisy |

**Takeaway:** These are valid generation metrics but bad **audit** metrics under our tier-ordered GT. Worth citing as "we tried and identified the mismatch" rather than as competing baselines.

### Cluster D — Audio sufficiency / longform / variation (post-2025 batch)

| Paper | arXiv | Pressure on SceneTwin |
|---|---|---|
| AudioCapBench | 2602.23649 | Split audio judgment into accuracy / completeness / hallucination |
| LVOmniBench | 2603.19217 | Short-clip metrics don't prove long-form access |
| DescribePro | 2508.01092 | AD quality is a versioned authoring workflow, not single string |
| Describe Now | 2411.11835 | BLV users want control over *when* / *how much* AD |

**Takeaway:** Audio sufficiency is the missing variable in current reference-free metrics. Long-form generalization is unknown for any of them, including ours. Paper A's discussion section should cite these as motivating future work.

## Cluster E -- User agency / customization (Paper B positioning)

| Paper | arXiv | What it adds |
|---|---|---|
| CustomAD | 2408.11406 | User controls over length / emphasis / speed / voice |
| SPICA | 2402.07300 | Layered object exploration on demand |
| ADCanvas | 2602.07266 | BLV creator verification & configurable automation |
| WorldScribe | UIST 2024 | Live description policy under intent / sound / latency |

**Synthesis quote (paper B opening):**

> Visual access is not a sentence generation problem. It is a state-reduction problem under viewer goal, audio budget, identity memory, emotion, risk, latency, and compute constraints.

**Takeaway:** These papers individually solve narrow surfaces (custom AD, object explorer, creator QC, live description). Together they imply a routing layer that decides **whether, when, how much, and on which interface** visual information should be delivered. This is the Access Surface OS thesis.

## Cluster F -- Identity / domain / deployment

| Paper | arXiv | Pressure |
|---|---|---|
| FocusedAD | 2504.12157 | Character identity is a memory problem, not object inventory |
| MCAD Soccer | 2511.09448 | Sports AD must avoid repeating commentary |
| Scene2Audio | 2603.27295 | Aesthetic / spatial experience needs nonverbal sound |
| Lightweight VLM | 2511.10615 | Access systems must run under privacy / latency / cost limits |
| Emotive AD | Nature 2025 | Neutral objectivity can erase emotion; some scenes need style |

**Takeaway:** Each breaks a different hidden assumption ("objects are enough", "more context is always good", "speech is the only output", "neutral is always better", "use the biggest model"). Together they imply a **surface and compute router** for BLV access — Paper B's primary contribution.

## Cluster G -- Visual assistant behavior / answerability contract

| Paper | arXiv | Pressure |
|---|---|---|
| Proactive BLV visual questions | 2510.01576 | A visual state implies likely questions, not one description |
| MLLM visual assistant diary | 2602.13469 | Initial descriptions strong; follow-up answers hallucinate |
| MAVP (multimodal agent video player) | 2602.04104 | BLV wants stateful player control + storyboards |
| GuideDog | 2503.12844 | Spatial/depth guidance is safety-critical |

**Synthesis quote:**

> Visual access is an answerability contract: what the user likely wants to ask, what evidence is available, what confidence is needed, what interaction mode is allowed, when to verify / defer / hand off.

## Cluster H -- Task / evidence loop

| Paper | arXiv | Pressure |
|---|---|---|
| Vid2Coach | 2506.00717 | How-to video access means task execution, not watching |
| AROMA | 2507.10963 | Real task state includes wearer-camera + non-visual user cues |
| StreetReaderAI | 2508.08524 | Spatial access requires orientation + movement controls |
| CoSight | 2508.08582 | Human attention can supply social context (community layer) |

**Takeaway:** Once we move beyond "describe the video", BLV access becomes an evidence loop: watch -> ask -> do -> compare state -> plan route -> contribute context. Each loop type maps to a different assistant skill (Paper B's task_assistant_affordance routing).

## Cluster I -- Answerability sidecars (evidence bill of materials)

| Paper | arXiv | Pressure |
|---|---|---|
| UniTime | 2506.18883 | Answers need timestamp windows, not ungrounded prose |
| T* Temporal Search | 2504.02259 | Sparse keyframes needed for long video |
| VidText | 2505.22810 | Scene text (OCR) is a separate evidence channel |
| VideoMind | 2503.13444 | Hard video Q needs planner + grounder + verifier + answerer |

**Synthesis quote:**

> SceneTwin should compile the evidence a video assistant needs before it is allowed to describe, answer, guide, replay, or escalate.

## Paper-level conflicts we accept (we don't try to resolve)

1. **Subjectivity (ADQA)** vs **single-reference tiers (SceneTwin)** — ADQA shows 40% temporal misalignment between two human AD tracks; our tier3 is one track. Acknowledged in failure analysis.
2. **Length / repetition (CoAD)** vs **tier3 pro** — pro AD wins on semantic clusters but loses on repetition. Reported in baselines table.
3. **Emotive AD** vs **neutral pro AD** — not measured in our setup; cited as discussion.
4. **External generalization** — our ensemble drops -0.056; some competitors drop more. Quantified in [[research/scenetwin-external-baselines]].

## How this corpus maps onto our two papers

### Paper A (metric + benchmark)
- Cluster A: direct baselines table
- Cluster B: narrative/timing measures cited in discussion + negative results
- Cluster C: cited as "tried and explicitly rejected"
- Cluster D: cited as motivating future work
- Clusters E-I: out of scope (paper B)

### Paper B (Access Surface OS)
- Cluster A: cited briefly as the "scoring backbone" (paper A handles details)
- Cluster B: TRIBE narrative-coverage cited for accessibility_gap motivation
- Clusters E-I: **the spine of the Related Work section**

## Recommended Paper B Related Work skeleton

```
Section 2. Related work

Recent BLV video accessibility work spans five concerns we
treat as orthogonal access surfaces:

(a) Reference-free AD scoring [Cluster A: ADQA, AutoAD III,
    AVBench, ViDscribe, SemVideo]. These measure how well a
    description matches video content but do not decide whether
    a static description is the right access surface to begin
    with.

(b) User agency and customization [Cluster E: CustomAD, SPICA,
    ADCanvas, WorldScribe, Describe Now, DescribePro]. These
    show BLV users want control over what, when, and how much,
    but customization adds interaction cost. Our router uses
    static-AD scores to decide when a control is worth offering.

(c) Identity, domain, and deployment [Cluster F: FocusedAD,
    MCAD Soccer, Scene2Audio, Lightweight VLM, Emotive AD].
    Each breaks a different assumption about static AD. We
    integrate these as additional routing dimensions: identity
    memory, commentary residual, soundscape gating, edge
    compute, style policy.

(d) Visual assistant behavior contracts [Cluster G: Proactive
    BLV questions, MLLM visual diary, MAVP, GuideDog]. Once we
    leave static AD, the assistant must declare what behavior
    it will execute. Our visual_assistant_skill_policy maps
    visual state to one of five assistant modes.

(e) Task and evidence loops [Cluster H, I: Vid2Coach, AROMA,
    StreetReaderAI, CoSight, UniTime, T*, VidText, VideoMind].
    Video access enables physical action and spatial
    navigation. We route clips to step coaching, reality-video
    alignment, route rehearsal, community context, or watch-
    only, and we compile evidence sidecars per clip before
    allowing answer generation.

We contribute the first explicit routing layer over these
surfaces, validated on 58 external clips with target-recall
greater than 88% per routing claim.
```

## See Also

- `cursor/research/papers/INDEX.md` -- per-paper notes table
- `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md` -- 460-line corpus synthesis (source for this page)
- [[research/scenetwin-method-inventory]] -- which routing scripts realize each cluster
- [[research/scenetwin-paper-outline]] -- both papers' Section 2 mappings to this corpus

## Sources

- 37 paper PDFs at `cursor/research/papers/sources/`
- Per-paper notes at `cursor/research/papers/*.md` (excluding INDEX.md and CROSS-PAPER-SYNTHESIS.md)
- Cross-paper synthesis at `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md`
