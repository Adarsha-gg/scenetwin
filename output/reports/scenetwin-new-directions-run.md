---
title: SceneTwin new research directions — first cached-data run
category: research
tags: [scenetwin, new-directions, error-taxonomy, comprehension-target, cheap-baselines, cost-pareto]
created: 2026-07-02
updated: 2026-07-02
sources:
  - cursor/output/halluc_gate/halluc_gate.csv
  - cursor/output/relational_hallucination_probe_set/probes.csv
  - cursor/output/scene_model_correctness_gap/adqa_question_types.csv
  - cursor/research/output/parallel_research/cheap_baselines/external_features.csv
---

# New research directions — first cached-data run (2026-07-02)

Five candidate directions proposed to move SceneTwin from a ranking-benchmark near-tie
toward a deployable error-detection contribution. Directions 1, 2, 4 were **run on
cached data** (stdlib only, no API/GPU/human). Directions 3 and 5 are **blocked** on
GPU/models and API/generation; for those we computed the motivating evidence from cache
and specced the runnable experiment. All numbers reproduce via
`scratchpad/new_directions.py` (committed under this report's sibling if promoted).

## D1 — AD error-taxonomy detector (RUN)

Fabrication vs faithful-paraphrase detection, using the paraphrase as the false-alarm
control (60 clips):

| Signal | fab-vs-paraphrase AUC | mean fab drop | mean para drop | blind (fab drop ≤ 0) |
|---|---:|---:|---:|---:|
| CLIP grounding-drop | **0.835** | +0.0369 | +0.0077 | 3/60 = 5.0% |
| ADQA drop | 0.801 | +0.1683 | −0.0183 | 18/60 = 30.0% |

- **Complementarity is real and clean:** on the 18 clips where ADQA is blind to the
  fabrication, CLIP catches **18/18 (100%)**.
- **Per-error-type (probe-labelled subset):** CLIP is never blind on either object/scene
  (0/18) or relation/action/count (0/5) swaps; ADQA is blind on 8/18 object/scene and
  1/5 relation/action/count. So the earlier worry that *CLIP misses relations/counts* is
  **not supported** here — the honest story is **ADQA is type-selectively blind, CLIP is
  type-agnostic** on drop magnitude.
- Caveat: the relation/action/count group is only n=5; treat that cell as suggestive.

**Reframe payoff:** this is a per-AD, reference-free *error detector* (AUC 0.835 grader-free),
not a clip-ranker — exactly where reference-based metrics cannot operate.

## D2 — Comprehension-grounded target (RUN) — strongest new finding

Do the *professional* ("truth") ADs actually state the key visual fact a viewer would
need? Measured on 76 relational probes:

| Probe type | n | pro-AD states the true fact |
|---|---:|---:|
| action_relation | 37 | 57% |
| spatial_relation | 16 | 62% |
| count | 13 | 85% |
| who_role | 10 | 50% |
| **Overall** | **76** | **61.8%** |

**~38% of key visual facts are omitted even by the gold-standard AD.** A frame-grounded
ADQA that scores an AD against a *reference key* is structurally blind to these omissions
(the key inherits the same gaps). This is a concrete argument for a **comprehension /
omission target**: score whether the AD *conveys* the fact, not whether it matches a
reference. who_role and action are the weakest-covered — the socially/temporally important
content.

## D3 — Video-native grounding (BLOCKED — motivation computed)

- 51% of ADQA questions (349/684) are scene-model questions (relation / action / count /
  who_role); combined with ADQA's 30% fabrication-blindness (D1), the frame-sampling
  pipeline is measurably weakest exactly on temporal/relational content.
- **Blocked:** no GPU, no video encoder installed, base Python has no numpy/PIL, and only
  18 clips have cached frames. Cannot run a real video-native scorer here.
- **Spec:** swap CLIP-on-8-frames for a video encoder (InternVideo2 / Qwen2-VL-video /
  VideoLLaMA) producing a single clip-level video–AD similarity; hold ADQA fixed; re-score
  the 60-clip ladder and the D1 fabrication set. Success = higher fab-detection AUC on the
  relation/action/count cell and no ranking regression. Needs GPU + one gated model DL.

## D4 — Cheap-proxy fight for TRIBE (RUN) — decisive-ish

Predicting external ADQA failure (60 clips, 10 positives), AUC by best direction:

| Feature | AUC | note |
|---|---:|---|
| **accessibility_gap (neural)** | **0.794** | perm p = 0.0023 |
| mean_scene_spatial_gap (neural) | 0.684 | |
| mean_visual_gap (neural) | 0.672 | |
| tier3_word_count / words_per_sec | 0.714 | best single cheap feature |
| category_loo_adqa_fail_rate | 0.700 | |
| transcript_word_count | 0.695 | |
| duration_s | 0.500 | |
| **cheap-feature ensemble (5 feats)** | **0.778** | z-score sum, direction-aligned |

- TRIBE's `accessibility_gap` **wins** the cheap-proxy fight (0.794 vs best single cheap
  0.714) and survives label permutation (p=0.0023).
- **Honest caveat:** the margin over a simple 5-feature *cheap ensemble* is thin
  (0.794 vs 0.778 = +0.016). TRIBE earns its place, but not by much against cheap text/
  metadata features combined.
- **Still blocked (the fair fight):** the strongest cheap visual proxies —
  optical-flow motion, scene-cut density, saliency — need frames + numpy/PIL, unavailable
  here. Until those are run, "TRIBE beats cheap proxies" is supported for text/metadata
  proxies only, not visual-motion proxies.

## D5 — Cost / quality Pareto (RUN from cache) + real-AI-AD eval (BLOCKED)

Cached corrected-3-tier ρ (60-clip primary) vs known 2026 run cost:

| Method | ρ (60) | approx cost / requirement |
|---|---:|---|
| SceneTwin CLIP+ADQA | 0.952 | ~$1 (Gemini-Flash ADQA gen) |
| LLM-AD-Eval proxy | 0.942 | needs a human reference AD |
| ADQA alone | 0.869 | ~$1 |
| CLIP alone | 0.747 | ~$0 (local encoder) |
| Best frontier VLM judge | 0.847 | ~$50 (Claude Opus, 78 clips) |

- Pareto: SceneTwin matches the best *reference-free* ranking at the lowest cost and with
  no human reference; the frontier VLM judge is ~50× cost and lower ρ. This is the
  deployability claim, now with numbers.
- **Blocked:** evaluating on *real* machine ADs (VideoA11y / AutoAD outputs) needs AD
  generation + grader API credits (the project's standing blocker). Spec: collect 30–60
  real AI-AD outputs, run the D1 detector + ensemble score, report error-detection PR
  curves on the true deployment distribution rather than synthetic tiers.

## Recommended promotion order

1. **D2 (comprehension/omission target)** — cheapest to develop, strongest novelty; turns
   the reference-free design into a capability (catch omissions) reference metrics can't.
2. **D1 (error-taxonomy detector)** — reframes the paper's identity from ranker to
   grader-free error detector at AUC 0.835; already reproducible.
3. **D4 visual-proxy completion** — run optical-flow/saliency baselines once frames+libs
   exist, to finish the TRIBE-vs-cheap defense.
4. **D3 / D5** — gated on GPU / API; specced and ready.
