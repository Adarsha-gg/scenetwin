---
title: SceneTwin paper B draft skeleton
status: scaffold — fill in prose; numbers and figures locked
created: 2026-05-29
---

# From Audio Description to Access Surface Routing: A Policy Layer for Blind Video Access

## Abstract

We argue that blind and low-vision (BLV) video accessibility is not a captioning problem but a **state-reduction problem under viewer, audio, identity, emotion, risk, latency, and compute constraints**. We contribute the **Access Surface OS**: a five-dimensional routing layer that, given a video and existing AD quality scores, decides whether each clip should be served as static AD, identity chip, defer/replay, concise cue, creator-QC queue, or task-loop coach. Each routing dimension is grounded in a distinct cluster of prior accessibility work. We evaluate the router on **58 external clips across 10 categories** and report target-recall per routing claim: surface (92%), assistant mode (96.3%), task loop (88.9%), evidence sidecar (100%), commentary residual (qualitative). Cross-claim consistency shows the five dimensions are not redundant: they identify the same high-risk clips from different angles without shared parameters or supervision. We position this work as complementary to AD scoring (Paper A): the scorer tells you how good an AD is; the router tells you whether AD is the right surface at all.

**Keywords:** blind and low-vision accessibility, audio description, access routing, assistive AI policy, multimodal evaluation.

## 1. Introduction

[Static audio description is the dominant access surface for BLV viewers, but recent work spans many surfaces (identity chips, soundscapes, depth guidance, task-loop coaches, evidence sidecars). The literature is fragmented; no single artifact treats them as a routing space.]

[Three observations:]

1. **A reference-free AD scorer (Paper A) is necessary but insufficient.** A high-scoring AD on the wrong access surface still fails the BLV viewer.
2. **The literature has converged on 5 distinct surfaces / behaviors** without explicitly naming the union (see §2).
3. **Routing-correctness against prior-art-derived labels** is a tractable empirical target without requiring a BLV user study at this scale.

[Our contributions:]

- The **Access Surface OS** framework: 5 routing dimensions × 4 compute tiers
- An empirical instantiation on 58 external clips with target-recall ≥ 88% per dimension
- **Cross-claim consistency**: the 5 dimensions identify overlapping high-risk clip sets without shared supervision, evidence that they are views of the same underlying access need rather than 5 independent heuristics

## 2. Related Work

> Full corpus survey: [[research/scenetwin-paper-corpus]] — 37 papers across 6 thematic clusters. This paper's Related Work uses clusters E–I (user agency, identity/deployment, assistant behavior, task/evidence loops, answerability sidecars). Cluster A (AD scoring) is summarized; Paper A provides the deep treatment.

### 2.1 Reference-free AD scoring (Cluster A — summarized)

[CLIP-grounded ADQA, LLM-AD-Eval, VT consistency, story recall. The scoring substrate. Cite Paper A for details.]

### 2.2 User agency and customization (Cluster E)

- **CustomAD** (arXiv 2408.11406) — user controls over length, emphasis, speed, voice
- **SPICA** (arXiv 2402.07300) — layered on-demand object exploration
- **ADCanvas** (arXiv 2602.07266) — BLV creator verification and configurable automation
- **WorldScribe** (UIST 2024) — live description policy under intent, sound, latency
- **Describe Now** (arXiv 2411.11835) — user-driven when/how-much AD requests
- **DescribePro** (arXiv 2508.01092) — versioned authoring workflow, not single string

### 2.3 Identity, domain, deployment (Cluster F)

- **FocusedAD** (arXiv 2504.12157) — character identity as memory problem
- **MCAD Soccer** (arXiv 2511.09448) — sports AD must avoid repeating commentary
- **Scene2Audio** (arXiv 2603.27295) — nonverbal sound for aesthetic/spatial scenes
- **Lightweight VLM accessibility** (arXiv 2511.10615) — privacy, latency, bandwidth, cost
- **Emotive AD** (Nature 2025) — emotion-bearing style policy

### 2.4 Visual assistant behavior contracts (Cluster G)

- **Proactive BLV visual questions** (arXiv 2510.01576) — question priors, not single description
- **MLLM visual assistant diary** (arXiv 2602.13469) — caption strong but follow-up hallucinates
- **MAVP — Multimodal Agent Video Player** (arXiv 2602.04104) — stateful player control
- **GuideDog** (arXiv 2503.12844) — depth-guarded spatial guidance

### 2.5 Task and evidence loops (Clusters H & I)

- **Vid2Coach** (arXiv 2506.00717) — how-to access means task execution
- **AROMA** (arXiv 2507.10963) — wearer-camera + non-visual user cues
- **StreetReaderAI** (arXiv 2508.08524) — orientation + movement controls
- **CoSight** (arXiv 2508.08582) — community context layer
- **UniTime** (arXiv 2506.18883) — timestamp grounding for answers
- **T\* Temporal Search** (arXiv 2504.02259) — keyframe search
- **VidText** (arXiv 2505.22810) — scene text as evidence channel
- **VideoMind** (arXiv 2503.13444) — planner/grounder/verifier/answerer roles

### 2.6 Gap addressed by this paper

Each prior work proposes one surface or behavior. None treats them as a routing space. Our contribution is the union: a router that decides which surface(s) to deploy per clip, with measured target-recall against prior-art-derived labels.

## 3. The Access Surface OS Framework

### 3.1 Five routing dimensions

> Evidence: [[research/scenetwin-access-surface-os]]

| Dimension | Routing space | Grounded in |
|---|---|---|
| Surface | 5 surfaces × 3 risk × 4 compute | Cluster E |
| Assistant mode | 5 modes | Cluster G |
| Task-loop affordance | 6 loops | Cluster H |
| Evidence sidecar | 8 sidecar types | Cluster I |
| Commentary residual | 4 residual actions | Cluster F (MCAD) |

### 3.2 Routing inputs

For each clip we extract:
- Reference-free AD score and per-tier margins (from Paper A's CLIP+ADQA ensemble)
- TRIBE failure-triage flag (from Paper A's brain-aligned forecaster)
- Speech density, audio overlap penalty
- Object/identity signals
- Frame-grounded VQA pressure (from ADQA's question priors)

The router is **hand-engineered** in v1; we do not claim optimality. We claim that the routing space is decomposable into 5 orthogonal-enough dimensions where even a hand-engineered router beats a static-AD-only deployment baseline.

### 3.3 Outputs

Per clip: a `(surface, assistant_mode, task_loop, sidecar_set, residual_action, compute_tier)` tuple.

## 4. Empirical Evaluation on 58 External Clips

> Evidence: [[research/scenetwin-access-surface-os]] (5 routing claims with target-recall numbers)

### 4.1 Corpus

58 unseen YouTube clips spanning 10 categories: How-to & Instructional (21), Entertainment (10), People & Vlogs (8), Sports (6), Health & Wellness (4), Event (3), Food & Cooking (3), Film & Animation (2), Music (2), Education (1). 10–30 s clip length.

Same clips used in Paper A's external generalization study (the 58 subset of 60 with TRIBE need-window features).

### 4.2 Per-dimension target recall

| Dimension | Routing space | Target-recall metric | n_clips | Result |
|---|---|---|---:|---:|
| Surface | 5 surfaces | high-collision clips not-static | 24 | **22/24 (91.7%)** |
| Assistant mode | 5 modes | assistant-not-plain | 27 | **26/27 (96.3%)** |
| Task-loop affordance | 6 loops | needs-task-loop | 27 | **24/27 (88.9%)** |
| Evidence sidecar | 8 types | target-has-any-sidecar | 24 | **24/24 (100%)** |
| Commentary residual | 4 actions | (qualitative) | 58 | mean penalty 0.18; residual term count 23.2 |

> **Figure 1**: surface distribution Sankey diagram on 58 clips.
> `output/charts/scenetwin_access_surface_sankey.png`

> **Figure 2**: per-dimension target-recall bar chart with random/static-only baselines.
> `output/charts/scenetwin_routing_target_recall.png`

### 4.3 Surface distribution

| Surface | n | Compute |
|---|---:|---|
| static_ad | 19 | mostly local |
| identity_chip | 18 | mostly cloud |
| defer_replay | 12 | mostly cached |
| concise_cue | 6 | mostly local |
| creator_qc | 3 | human |

Risk: 36 low, 15 medium, 7 high. Compute: 25 local, 14 cloud, 11 cached, 8 human.

### 4.4 Cross-claim consistency

The five dimensions are NOT redundant:

- High-collision clips (n=24): 18 route to `identity_chip`, 3 to `creator_qc`, 2 to `static_ad`. Surface and risk routers agree.
- `queue_residual_replay` clips (n=21): 12 route to `defer_replay` surface, 7 to `identity_chip`. Residual and surface routers agree.
- `verify_before_answer` (n=19) overlaps heavily with `stateful_video_agent` (n=22): assistant-mode and task-loop routers identify the same hallucination-risk set from different angles.

> **Figure 3**: cross-claim consistency heatmap (dimensions × dimensions, agreement on high-risk clips).
> `output/charts/scenetwin_routing_consistency.png`

### 4.5 Comparison to static-AD-only baseline

The reviewer's null hypothesis: "what's wrong with just static AD?" Answer:

- 92% of high-collision clips route AWAY from static_ad — i.e., a static-AD-only deployment misses the right surface on ~22 of 24 collision-pressure clips.
- 100% of clips needing any evidence sidecar are flagged by the sidecar router — static AD pipelines do not emit sidecars at all.
- Mean evidence sidecar count per clip is 4.8 across 58 clips — static AD ships zero.

The framework's claim is **routing-correctness**, not user-utility. The static-AD-only baseline is empirically wrong about which surface to serve on most of these clips.

## 5. Discussion

[Limitations: no BLV user study; hand-engineered router (no learned weights); single-cohort label derivation; routing-correctness ≠ deployment success.]

[What we explicitly do NOT claim: that the specific router weights are optimal, that the 5 dimensions are exhaustive, that user preferences will follow our routing choices.]

[What we DO claim: that a 5-dimensional routing space is empirically decomposable, that even hand-engineered routers achieve ≥ 88% target recall per dimension, and that the resulting union beats static-AD-only deployment on the routing-correctness target.]

[Future work: replace hand-engineered routers with a learned classifier on labeled BLV preference data, expand to long-form video (Cluster D), incorporate AudioCapBench-style audio sufficiency as a 6th routing dimension.]

## 6. Conclusion

[BLV video access is a routing problem across access surfaces, not a captioning problem. The Access Surface OS instantiates this routing space with 5 dimensions, each grounded in distinct prior work and validated at ≥ 88% target-recall on 58 external clips. Together with Paper A's scoring backbone, it forms a deployable BLV video access stack.]

## Appendix A — Router implementation

> Code references: `cursor/methods/access_surface_router.py`, `cursor/methods/visual_assistant_skill_policy.py`, `cursor/methods/task_assistant_affordance.py`, `cursor/methods/evidence_sidecar_readiness.py`, `cursor/methods/commentary_residual_ad.py`

[Pseudocode for each router; threshold tables; categorical input list.]

## Appendix B — Target-label derivation

[For each routing target, exactly which prior-art signal it's derived from. So reviewers can replicate.]

## Appendix C — Per-clip routing inventory

[Full table of 58 clips × 5 routing decisions, with category + risk label, in supplementary.]

---

## Writing-phase TODO

| Section | What's missing | Blocker |
|---|---|---|
| Abstract | Polish prose; tighten claim wording | none |
| §1 | Introduction prose | none |
| §3 | Architecture diagram + pseudocode | none |
| §4 | Render 3 figures (Sankey, target recall, consistency heatmap) | none — local plotting |
| §5 | Discussion prose | none |
| Appendices | Move tables from wiki page | none |
| Bibliography | Build from arXiv IDs in cluster E–I | none — handled by output/papers/scenetwin-references.bib |

## Figure inventory (rendered, ready to drop in)

1. `output/charts/scenetwin_access_surface_sankey.png` — Section 4.3 (surface × compute distribution)
2. `output/charts/scenetwin_routing_target_recall.png` — Section 4.2 (per-dimension target recall vs static baseline)
3. `output/charts/scenetwin_routing_consistency.png` — Section 4.4 (pairwise Jaccard overlap heatmap)

## See also

- [[research/scenetwin-access-surface-os]] — empirical evidence
- [[research/scenetwin-paper-corpus]] — 37-paper corpus, Section 2 source
- [[research/scenetwin-method-inventory]] — Paper B method roster
- [[research/scenetwin-paper-outline]] — master outline that this draft instantiates
