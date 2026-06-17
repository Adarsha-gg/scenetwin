---
title: SceneTwin method inventory — what to keep, defer, or kill per paper
category: research
tags: [scenetwin, paper-planning, inventory]
sources: [cursor/methods/, cursor/discover/, cursor/papers/, cursor/research/papers/INDEX.md]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

After running this audit: of 28 method scripts across `cursor/methods`, `cursor/discover`, and `cursor/papers`, **22 have measured outputs** and 12 paper-derived methods remain unrun stubs. The 22 are not interchangeable -- they split cleanly across **two distinct paper contributions**: (A) the metric benchmark and (B) the Access Surface OS framing. The audit below assigns each to a paper or marks it for kill/defer.

## Paper A: Metric + benchmark (ML/CV / ACM MM / WACV)

Reference-free AD audit. Headline ρ=0.929 in-bench / 0.873 external. CLIP + ADQA two-signal ensemble.

### Keep (ran, paper-relevant)

| Script | Lives in | What it measures | Paper section |
|---|---|---|---|
| `papers/llm_ad_eval_proxy.py` | papers | LLM-AD-Eval (sentence embedding sim to T3) | Baselines table |
| `papers/critic_entity.py` | papers | CRITIC entity proxy (AutoAD III) | Baselines table |
| `papers/coad_repetition.py` | papers | CoAD repetition penalty | Baselines table |
| `papers/multi_ref_r_at_k.py` | papers | Multi-reference R@k | Baselines table + caveat |
| `papers/action_coverage.py` | papers | Action-question subset of ADQA | Baselines table |
| `papers/timing_overlap_g7g8.py` | papers | VideoA11y G7/G8 timing | Baselines table |
| `papers/paper_fusion_v1.py` | papers | 6 fusion strategies | Negative results subsection |
| `papers/metric_correlation.py` | papers | Pairwise metric rho matrix | Cluster figure |
| `papers/metric_leaderboard.py` | papers | Headline leaderboard | Baselines table |
| `discover/story_recall_proxy.py` | discover | StoryRecall (CoAD beat-driven) | Baselines table |
| `discover/generalization_gap.py` | discover | In-bench vs external rho gap | Generalization section |
| `discover/subjectivity_index.py` | discover | Subjectivity / ranking margin | Failure analysis |
| `discover/maverix_audio_gate.py` | discover | MAVERIX modality dependence | Discussion / limitations |
| `discover/motion_from_video.py` | discover | Motion proxy from video | Need-curve ablation |
| `discover/slot_iou_tribe.py` | discover | CA3D slot IoU vs TRIBE windows | TRIBE discussion |
| `discover/mdci_edit_distance.py` | discover | MDCI edit burden | Failure analysis |
| `methods/six_dim_rubric.py` | methods | IRT 6-dim rubric proxy | Baselines / orthogonal axes |
| `methods/hierarchical_semantic_eval.py` | methods | SemVideo hierarchical sim | Baselines table |
| `methods/vidscribe_query_coverage.py` | methods | ViDscribe query coverage | Discussion |

### Defer to paper A v2 (run-but-uncertain-paper-value)

| Script | Why defer |
|---|---|
| `methods/adqa_va_nu_eval.py` | VA/NU question-type split; intriguing but no clean rho story yet |
| `methods/adx3_slot_generator.py` | Generative slot-filling; not an evaluation metric |
| `methods/av_consistency_eval.py` | AVBench-style VT consistency; covered already in baselines table |

### Kill (scope-out of Paper A)

None -- all the above either belong in Paper A or Paper B. Nothing is true dead weight.

## Paper B: Access Surface OS (HCI / ASSETS / W4A)

The product reframe. BLV access is a routing problem across surfaces (static AD, identity chip, defer/replay, creator QC, object explorer, etc.) under compute / authorship / safety constraints.

### Keep -- this is the actual paper B evidence

| Script | What it measures | n_clips | Target recall |
|---|---|---:|---:|
| `methods/access_surface_router.py` | Routes 60 clips into 5 surface types | 58 | 92% high-collision not-static |
| `methods/access_surface_router_eval.py` | Evaluates router decisions | 58 | -- |
| `methods/access_surface_cost_eval.py` | Cost model for surface routing | 58 | -- |
| `methods/commentary_residual_ad.py` | MCAD-style residual; transcript overlap | 58 | -- |
| `methods/visual_assistant_skill_policy.py` | Assistant mode routing (5 modes) | 58 | **96.3%** (assistant-not-plain) |
| `methods/task_assistant_affordance.py` | Task-loop routing (Vid2Coach / AROMA / StreetReader / CoSight) | 58 | **88.9%** (task-loop) |
| `methods/evidence_sidecar_readiness.py` | Evidence-bill-of-materials per clip | 58 | **100%** (target has any sidecar) |

### Paper B claims supported by these scripts

1. **Routing target recall**: For each routing target (collision-needs-identity-chip, needs-assistant-mode, needs-task-loop, needs-evidence-sidecar), the corresponding script's routing decision achieves >= 88% recall. This is the "metric flags right" claim.

2. **Surface distribution**: Across 58 external clips: 19 static AD, 18 identity chip, 12 defer/replay, 6 concise cue, 3 creator QC. The router doesn't trivially pick one surface; it spreads.

3. **Risk-and-compute joint routing**: each clip gets BOTH a surface and a compute tier (human/cloud/local/cached). This is the "Access Surface OS" thesis.

## Unrun-paper-derived stubs (12 methods)

These are listed in `cursor/research/papers/INDEX.md` as "proposed `methods/...`" but the script files do not exist. **For the paper push these all get DEFERRED to follow-up work.** None are blockers for either Paper A or Paper B.

| Proposed | Paper origin | Defer rationale |
|---|---|---|
| `audio_sufficiency_qa` | AudioCapBench (2602.23649) | Adds audio dimension; orthogonal to current paper claims |
| `longform_access_state_probe` | LVOmniBench (2603.19217) | Long-form video; corpus mismatch with our 10-30s clips |
| `variation_pack_router` | DescribePro (2508.01092) | AD variation packs; product-side, not metric |
| `user_driven_policy_sim` | Describe Now (2411.11835) | Needs user-study data we don't have |
| `customization_policy_router` | CustomAD (2408.11406) | Subsumed by access_surface_router |
| `layered_object_explorer` | SPICA (2402.07300) | Implementation requires interactive UI |
| `blv_authoring_agent_qc` | ADCanvas (2602.07266) | BLV creator workflow; out of scope |
| `context_aware_description_policy` | WorldScribe (2408.06627) | Live description policy; product-side |
| `character_identity_memory` | FocusedAD (2504.12157) | Identity memory; not a per-clip metric |
| `soundscape_surface_gate` | Scene2Audio (2603.27295) | Aesthetic sound; out of scope for both papers |
| `edge_model_feasibility_gate` | Lightweight VLM (2511.10615) | Compute routing; partially subsumed by access_surface_router |
| `emotive_style_policy` | Emotive AD (Nature 2025) | Authoring style; out of scope |

### Recommended INDEX.md cleanup

The cursor/research/papers/INDEX.md currently lists these 12 proposed methods next to paper writeups. For honest paper-prep, the INDEX should say:

```
| Paper                  | Status   |
|------------------------|----------|
| AudioCapBench          | Discussed; method deferred to follow-up |
| LVOmniBench            | Discussed; method deferred to follow-up |
| DescribePro            | Discussed; method deferred to follow-up |
... etc
```

So reviewers / advisors see clearly that we **discussed** the paper in the synthesis but did **not** implement+measure it.

## Two-paper roadmap

### Paper A (metric / benchmark) -- ready to write

All evidence in hand. Wiki pages cover:
- Headline numbers + power
- External generalization
- Baselines (10 metrics + 6 fusions)
- Failure analyses (both corpora)
- Signal decomposition
- TRIBE role (honest)
- Negative results

Pending: TRIBE counterfactual numbers from your Colab run, then expand `cursor/research/papers/tribe-v2.md` (task #5).

### Paper B (Access Surface OS) -- evidence in hand, needs structure

All 5 routing scripts ran on 58 external clips with target-recall numbers >= 88%. The case is empirical, not hand-wavy. Needs a paper-structure pass:
- Position the contribution: not "another AD scorer" but "a router over access surfaces"
- Justify the 5 surface types
- Report target recall as the deployment claim
- Cross-reference Paper A for the scoring backbone

This is its own paper. Recommended next: a wiki page `scenetwin-access-surface-os.md` that consolidates the 5 routing analyses into a single paper-ready section.

## See Also

- [[research/scenetwin-metric-landscape]] - Paper A baselines
- [[research/scenetwin-negative-results]] - Paper A negative results
- `cursor/research/papers/INDEX.md` - the 39 paper writeups
- `cursor/research/papers/CROSS-PAPER-SYNTHESIS.md` - 460-line synthesis (Paper B positioning material)

## Sources

- `cursor/methods/output/*.json` (summary JSONs for 5 routing scripts on n=58)
- `cursor/papers/output/*.csv` (10 baseline metrics on n=72)
- `cursor/discover/output/*.csv` (orthogonal axes measurements)
