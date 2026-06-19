# Cross-paper synthesis — correlations, conflicts, combinations

Generated after reading PDFs in `sources/` and running all paper-metric prototypes on the 18-clip × 4-tier benchmark (n=72).

## Metric correlation clusters (Spearman on tier scores)

Run `cursor/papers/metric_correlation.py` to refresh. Observed structure:

### Cluster A — semantic / reference alignment (ρ 0.79–0.93, mutually r>0.85)

| Metric | ρ vs tier GT | Role |
|--------|-------------:|------|
| SceneTwin ensemble | 0.928 | CLIP + ADQA + need-weighted CLIP (our SOTA) |
| LLM-AD-Eval proxy | 0.899 | Embedding sim to pro AD (AutoAD III) |
| ADQA v4 | 0.789 | Frame-grounded QA |
| VT consistency | 0.768 | AVBench-style text↔video |

**Interpretation:** These papers optimize overlapping goals — “does the AD say what the video shows?” LLM-AD-Eval and ADQA are **partially redundant** with ensemble; adding both to a blend yields diminishing returns unless one is split by question type (VA vs NU).

**Our take:** AutoAD III’s LLM-AD-Eval is the wrong primary metric for audit — it anchors to **one pro reference**, reproducing ADQA’s subjectivity problem in a softer form. ADQA fixes this with independent questions but still assumes a single acceptable answer per MCQ.

### Cluster B — narrative / sequence (ρ 0.60–0.70)

| Metric | ρ | Papers |
|--------|--:|--------|
| StoryRecall (fixed) | 0.703 | CoAD |
| Need-weighted CLIP | 0.733 | TRIBE-inspired |
| Action coverage | 0.601 | AutoAD III action split |

**Interpretation:** CoAD’s StoryRecall and action coverage measure **coverage over time**, not pixel grounding. They correlate moderately with Cluster A but add signal on clips where pro AD is verbose-but-wrong (clip_01/03 closure failures).

**Combination worth testing:** `0.6 * ADQA + 0.25 * story_recall + 0.15 * action_coverage` — narrative without full redundancy.

### Cluster C — weak or inverted on tier ranking

| Metric | ρ | Issue |
|--------|--:|-------|
| CRITIC entities | 0.638 | VATEX clips lack character names; entity proxy is noisy |
| R@3/N multi-ref | 0.532 | Tier3 always best reference — metric collapses |
| CoAD repetition (inv) | -0.064 | **Longer AD repeats more** — anti-correlates with our tier GT |

**Conflict:** CoAD penalizes repetition; our tier3 pro AD is often **longer** and repeats scene context. Repetition is a **generation** metric, not an **audit** metric unless GT is sequence-level CoAD outputs.

### Cluster D — not yet on leaderboard (methods only)

| Method | Paper | Hypothesis |
|--------|-------|------------|
| IRT 6-dim rubric | Scalable QC | Delivery/timing dimensions orthogonal to CLIP |
| MAVERIX gate | MAVERIX | Clips needing A+V should down-weight VT-only |
| ViDscribe query coverage | ViDscribe | User-specific; population ρ may be low |
| SemVideo static/motion split | SemVideo | Motion bucket explains Sports tier2>3 |
| MDCI slot IoU | ADx3 / GenAD | Measures **where** not **what** |

## Paper-to-paper agreement matrix

|  | ADQA | AutoAD III | CoAD | ADx3 | AVBench | TRIBE | IRT |
|--|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **ADQA** | — | Both eval; ADQA rejects single-ref MC on short clips | CoAD sequence vs ADQA segment QA | ADx3 GenAD could feed ADQA | AVBench VT ≈ CLIP grounding | TRIBE need ≠ QA correctness | IRT adds delivery dim ADQA skips |
| **AutoAD III** | LLM-AD-Eval redundant with semantic sim | — | CRITIC + StoryRecall vs per-interval CIDEr | Same authors ecosystem as ADx3 workflow | VT evaluator similar spirit | MAD movies vs our short clips | R@k/N assumes refs exist |
| **CoAD** | StoryRecall needs GT narrative; ADQA doesn't | Repetition hurts AutoAD metrics | — | RefineAD could fix repetition post-hoc | N/A | Need windows for interval selection | N/A |
| **TRIBE** | Need curve ≠ comprehension | Counterfactual routing for GenAD | When to describe | AdaptAD query timing | P_AV vs P_A ablation | — | Neural delivery proxy |

## New 2026/2025 additions: what they change

| Paper | New pressure on SceneTwin | Combination |
|-------|---------------------------|-------------|
| AudioCapBench | Split audio judgment into **accuracy / completeness / hallucination** instead of one caption score | Use it to estimate what the soundtrack already communicates before asking ADQA |
| LVOmniBench | Short-clip metrics do not prove long-form access; long videos fail on temporal localization and A/V alignment | Convert SceneTwin from clip ranking into a running BLV viewer-state probe |
| DescribePro | AD quality is a **versioned authoring workflow**, not a single generated string | Route collision clips to tagged variation packs and human-AI forks |
| Describe Now | BLV users want control over **when** and **how much** AD, but manual triggering adds workload | Use TRIBE to predict when to offer concise/detail options instead of forcing constant user requests |

These additions reinforce the 2026-05-27 social-collision result:

```text
TRIBE debt + dense audio + social clip
  -> static linear AD likely becomes the wrong product surface
  -> offer adaptive access: concise default, optional detail, tags/forks, user-state memory
```

The papers also expose a new missing variable: **audio sufficiency**. Speech
density is a crude proxy. AudioCapBench suggests judging whether the soundtrack
is accurate, complete, and non-hallucinated with respect to what the viewer needs
to know. LVOmniBench then asks whether that sufficiency holds over time.

## Customization / user-agency batch

The second paper batch changes the product direction more than the metric stack:

| Paper | Pressure on SceneTwin | Combination |
|-------|------------------------|-------------|
| CustomAD | BLV users want controls over length, emphasis, speed, voice, tone, and format, but customization adds interaction cost | Use SceneTwin to decide when a control is worth offering |
| SPICA | Static AD cannot carry every spatial/object detail | Route residual visual questions to optional object exploration |
| ADCanvas | BLV creators need verification and configurable automation, not blind generation | Turn SceneTwin metrics into an authoring QC queue |
| WorldScribe | Live description must account for user intent, visual context, sound context, and latency | Convert need scoring into an emit/defer/presentation policy |

Core synthesis:

```text
TRIBE tells us where audio-only brain state diverges from audio+visual state.
CustomAD and Describe Now tell us which controls users actually want.
SPICA tells us the optional-detail surface.
ADCanvas tells us BLV creators need verification, not autonomous prose.
WorldScribe tells us live access is a policy under intent, sound, and latency.
```

The product implication is sharper than "generate better AD":

```text
SceneTwin should become a policy engine over access surfaces:
static AD, concise cue, detail chip, object explorer, creator QC, live mode.
```

This also answers the "not new enough" concern. Another semantic caption metric
is not a new use case. A cross-surface router is new enough to matter because it
decides **whether, when, how much, and on which interface** visual information
should be delivered.

### New clip check: 58 external clips

The external corpus now has 58 downloaded `clip.mp4` files in
`cursor/data/external_clips`, 58 registry rows, and 58 regenerated need curves.
Four late-arriving clips had CLIP rows but no need curves until this pass:

- `9eBhetL8n5Q_000222_000232`
- `crjesEwF0Ks_000197_000207`
- `iZP6gjlr_nM_000113_000123`
- `zTJ0Zbv1jBo_000045_000055`

After including them, the all-available plain external track reports:

| Signal | n | Positives | AUC | AP |
|--------|--:|----------:|----:|---:|
| social_collision_boundary | 58 | 27 | 0.723 | 0.698 |
| social_need_boundary | 58 | 27 | 0.707 | 0.665 |
| social_only | 58 | 27 | 0.667 | 0.599 |
| speech_z | 58 | 27 | 0.628 | 0.612 |
| need_z | 58 | 27 | 0.626 | 0.583 |

The result is weaker than the earlier 54-clip check but still ranks the
social-collision boundary above need-only, speech-only, and social-only
baselines. The right claim is therefore not "TRIBE solves AD ranking." The right
claim is:

```text
social collision is a useful trigger for a different access surface.
```

### Correlation experiments to run next

| Hypothesis | Observable |
|------------|------------|
| User control demand rises when pro AD loses on social-collision clips | `social_collision_boundary` vs pro-not-best labels |
| Emphasis setting can be predicted from failure type | CustomAD emphasis buckets vs ADQA miss nouns / critical evidence |
| Optional object exploration is most useful when caption debt is spatial | SPICA-style object density vs residual ADQA questions |
| Sound context should decide presentation, not only need | speech density / AudioCap sufficiency vs emit/defer policy |
| Creator QC is more valuable than autonomous generation on uncertain clips | ADCanvas verification queue size vs CLIP/ADQA disagreement |

## Identity / domain / soundscape / deployment batch

The third batch fills a different gap: once SceneTwin is a policy engine, it must
choose **what kind of access surface** and **what compute tier** to use.

| Paper | Pressure on SceneTwin | Combination |
|-------|------------------------|-------------|
| FocusedAD | Character identity, not object inventory, often carries the plot | Add identity memory and confidence to social/narrative routing |
| MCAD Soccer | Sports AD must avoid repeating commentary and must use domain context | Treat transcript/commentary as both evidence and output budget |
| Scene2Audio | Some visual experiences are aesthetic and spatial, not only propositional | Add optional soundscape as a gated surface for vista/leisure scenes |
| Lightweight VLMs | Accessibility systems must run under privacy, latency, bandwidth, and cost limits | Route clips across local, cloud, cached, and human-review compute |
| Emotive AD styles | Neutral objectivity can erase emotion; emotive AD helps some drama/social scenes | Add style/prosody as a user- and genre-conditioned policy |

New first-principles frame:

```text
Visual access is not a sentence generation problem.
It is a state-reduction problem under constraints:
viewer goal, audio budget, identity memory, emotion, risk, latency, and compute.
```

This makes SceneTwin's better use case more concrete:

```text
Access Surface OS
  1. sense residual visual state
  2. infer viewer/task need
  3. choose surface: prose, identity chip, object explorer, soundscape, style, replay, creator QC
  4. choose compute: cheap local, expensive cloud, cached, or human verification
  5. emit only if it beats interruption and hallucination risk
```

### Why this is more novel than another AD scorer

Each paper breaks a different hidden assumption:

- FocusedAD breaks "objects are enough" by making identity a memory problem.
- MCAD breaks "more context is always good" by making commentary an anti-echo
  constraint.
- Scene2Audio breaks "speech is the only output" by adding nonverbal sound.
- Emotive AD breaks "neutral is always better" by making style a preference and
  genre policy.
- Lightweight VLMs break "use the biggest model" by making deployment a routing
  decision.

Together they imply a product that no single paper builds: a **surface and
compute router** for BLV access.

### Correlations to test from this batch

| Hypothesis | Observable |
|------------|------------|
| Identity debt predicts social-collision failures | person/relationship ADQA misses vs `social_collision_boundary` |
| Commentary residual beats raw description length on sports/action clips | transcript overlap penalty vs pro-not-best labels |
| Soundscape should be gated to low-utility aesthetic clips | category + speech density + object density vs `allow_soundscape` |
| Emotive style should be offered when emotion/reaction is the missing visual signal | emotion/reaction ADQA misses vs social/drama categories |
| Edge model should run only as triage, not final answer, on high-risk clips | local uncertainty vs CLIP/ADQA disagreement and creator-QC queue size |

## Visual assistant / agency / guidance batch

The fourth batch pushes beyond AD surfaces into assistant behavior contracts.

| Paper | Pressure on SceneTwin | Combination |
|-------|------------------------|-------------|
| Proactive BLV visual questions | A visual state implies likely user questions, not one canonical description | Add question-prior chips to access surfaces |
| MLLM visual assistant diary | Initial descriptions can be strong while follow-up answers hallucinate or abstain | Separate caption quality from assistant readiness |
| MAVP | BLV video access wants stateful player control, timestamp search, storyboards, metadata, and settings | Turn Access Surface OS into an evidence-indexed Access Player OS |
| GuideDog | Spatial/depth guidance is safety-critical and object recognition is insufficient | Add depth/obstacle guard before guidance-like answers |

New first-principles frame:

```text
Visual access is an answerability contract:
  what the user likely wants to ask
  what evidence is available
  what confidence is needed
  what interaction mode is allowed
  when to verify, defer, or hand off
```

This batch upgrades the product idea:

```text
Access Surface OS
  -> Access Player / Assistant OS
```

The router should not only output `surface`. It should output an assistant
behavior:

- plain description
- proactive question chip
- stateful video agent
- verify before answer
- depth-guarded guidance

Implemented in:

- `cursor/methods/visual_assistant_skill_policy.py`
- `cursor/findings/visual-assistant-skill-policy.md`

On the 58 external clips, the policy marks 49 clips as requiring assistant
behavior beyond plain description and catches 26 of 27 pro-not-best clips. This
does not prove user value, but it shows the new papers map cleanly onto a
testable behavior layer above caption scoring.

### Correlations to test from this batch

| Hypothesis | Observable |
|------------|------------|
| Question-prior pressure predicts follow-up demand | `followup_pressure` vs real user question logs |
| Assistant readiness is different from caption quality | `verify_before_answer` vs hallucinated follow-up answers |
| Stateful video agent need tracks temporal/identity failures | `stateful_video_agent` vs pro-not-best on social/action clips |
| Depth guard is orthogonal to CLIP grounding | `depth_guarded_guidance` vs spatial/depth answer errors |
| Plain description should be rare when user agency matters | `plain_description` miss rate vs user satisfaction/trust |

## Task assistant / evidence-loop batch

The fifth batch pushes beyond assistant behavior into the evidence/action loop
needed for the user to do something with video.

| Paper | Pressure on SceneTwin | Combination |
|-------|------------------------|-------------|
| Vid2Coach | How-to video access means successful physical task execution, not watching | Add step index, completion criteria, and progress feedback |
| AROMA | Real task state includes user non-visual cues and intentional deviations | Align video recipe, wearable camera, and user sensory reports |
| StreetReaderAI | Spatial access requires orientation state and movement controls | Add route rehearsal and geospatial context loops |
| CoSight | Human viewer attention can supply social/emotional visual context | Add timeline comment layer with quality gates |

New first-principles frame:

```text
Visual access is an evidence loop:
  watch -> ask -> do -> compare current state -> plan route -> contribute context
```

This extends Access Player / Assistant OS again:

```text
Access Surface OS
  -> Assistant Behavior Contract
  -> Evidence Loop Router
```

Implemented in:

- `cursor/methods/task_assistant_affordance.py`
- `cursor/findings/task-assistant-affordance.md`

On the 58 external clips:

- 46 of 58 clips need an evidence/action loop beyond watch-only access.
- 18 clips need current-state monitoring.
- 18 clips need a human/community layer or safety-sensitive escalation.
- Task-loop recall on pro-not-best clips is 24/27 = 0.889.

### Correlations to test from this batch

| Hypothesis | Observable |
|------------|------------|
| How-to clips need step state more than better prose | `stepwise_task_coach` vs task-following error labels |
| Cooking clips need reality-video alignment | `reality_video_task_coach` vs current-state monitoring demand |
| Spatial clips need orientation state | `route_or_spatial_rehearsal` vs spatial answer failures |
| Social/emotional clips benefit from community context | `community_context_layer` vs BLV usefulness of comments |
| Evidence-loop routing explains pro-not-best better than caption metrics alone | task-loop recall vs static AD miss rate |

## Evidence sidecar / answerability batch

The sixth batch turns the evidence-loop idea into a bill of materials for safe
answers.

| Paper | Pressure on SceneTwin | Combination |
|-------|------------------------|-------------|
| UniTime | Answers need timestamp windows instead of ungrounded video prose | Add temporal grounding sidecars before answer generation |
| T* Temporal Search | Long/dense video needs sparse keyframes, not uniform sampling | Add query-conditioned keyframe search for evidence retrieval |
| VidText | Scene text is a separate video evidence channel | Add OCR/text sidecars for signs, overlays, UI, scoreboards, and subtitles |
| VideoMind | Hard video questions need planner, grounder, verifier, and answerer roles | Require explicit verification on weak-margin or collision-heavy clips |

New first-principles frame:

```text
Visual access is an answerability bill of materials:
  timestamp window
  keyframes
  OCR text
  transcript
  object/depth evidence
  planner/verifier trace
  current-state comparison
  community quality gate
```

This extends the stack again:

```text
Access Surface OS
  -> Assistant Behavior Contract
  -> Evidence Loop Router
  -> Evidence Sidecar Compiler
```

Implemented in:

- `cursor/methods/evidence_sidecar_readiness.py`
- `cursor/findings/evidence-sidecar-readiness.md`

On the 58 external clips, after removing eval-label leakage from urgency
assignment:

- 58 of 58 clips have at least one evidence sidecar.
- 36 clips are high urgency; 24 of those are pro-not-best.
- All 27 pro-not-best clips have at least one required sidecar.
- Required sidecars: ASR 49, planner/verifier 49, temporal grounding 37, OCR 28,
  keyframe search 27, community quality gate 18, current-state monitor 18, depth
  16.

The key product claim is no longer "generate better AD." It is:

```text
SceneTwin should compile the evidence a video assistant needs before it is
allowed to describe, answer, guide, replay, or escalate.
```

### Correlations to test from this batch

| Hypothesis | Observable |
|------------|------------|
| Temporal grounding predicts follow-up and QA failure on dense clips | `needs_temporal_grounding` vs ADQA temporal misses |
| Keyframe search predicts social collision and stateful-agent demand | `needs_keyframe_search` vs pro-not-best labels |
| OCR sidecars explain label/sign/UI failures | `needs_video_text_ocr` vs text-related misses |
| Planner/verifier is the right default for weak-margin answers | `needs_planner_grounder_verifier` vs hallucinated follow-ups |
| Sidecar count is a better cost signal than need score alone | `sidecar_count` vs surface-router cost and user value |

## Conflicts we accept (GT may be wrong)

1. **Subjectivity (ADQA)** vs **single-reference tiers (SceneTwin)** — ADQA shows 40% temporal misalignment between two human AD tracks; our tier3 is one track.
2. **Length/repetition (CoAD)** vs **tier3 pro** — pro AD wins on semantic clusters but loses on repetition and sometimes closure.
3. **Emotive AD (Nature 2025)** vs **neutral pro AD** — not in PDF set but noted in literature scan.
4. **External generalization** — all Cluster A metrics drop ~0.25–0.35 ρ on VATEX-held-out clips; paper metrics trained on movie/domain data may not transfer.

## Recommended combinations (implemented in `paper_fusion_v1.py`)

| Fusion name | Formula intuition | Expected |
|-------------|-------------------|----------|
| `semantic_core` | z(llm) + z(adqa) + z(vt) / 3 | High ρ, little gain over ensemble |
| `narrative_ground` | 0.5·z(adqa) + 0.3·z(story) + 0.2·z(action) | Better on narrative-heavy clips |
| `audit_no_ref` | z(adqa) + z(vt) − z(repetition) | Reduces tier3 bias from length |
| `maverix_gated` | vt * (1 + maverix_gate) + adqa | Upweight A+V clips only |
| `paper_fusion_best` | Grid-searched weights on benchmark | **ρ=0.810** (ADQA-heavy; still below ensemble 0.928) |

### Fusion results (measured 2026-05-27)

| Fusion | ρ vs tier GT | Notes |
|--------|-------------:|-------|
| ensemble (baseline) | **0.928** | Still wins — paper stack is mostly redundant |
| semantic_core (llm+adqa+vt) | 0.887 | Confirms Cluster A collapse |
| paper_stack_v1 | 0.794 | Adding timing/story/action doesn't beat ADQA alone |
| narrative_ground | 0.781 | StoryRecall adds little once ADQA in mix |
| audit_no_ref | 0.776 | Repetition penalty doesn't fix GT bias |
| grid_best (adqa 75% + vt 25%) | 0.810 | Simple blend ≈ paper_stack |

**Conclusion:** Implementing every paper metric and blending them **does not beat** the existing SceneTwin ensemble. Value is in **orthogonal legs** (timing IRT, MAVERIX gate, external tuning) not more semantic proxies.


## What to run next (not bootstrap sweeps)

1. **Critical-only ADQA bucket** — ADQA paper splits VA/NU; filter to plot-critical questions only.
2. **IRT delivery + G7/G8 timing** — orthogonal to Cluster A; combine with `timing_overlap_g7g8.py`.
3. **External clip fusion** — same weights rarely transfer; tune on `external_clip_full_eval.json`.
4. **Fix TRIBE live on external** — unlock real need curves for `need_weighted` cluster.
5. **Audio sufficiency QA** — AudioCapBench dimensions against ADQA questions.
6. **Variation pack router** — DescribePro tags/forks for clips where pro AD is not best.
7. **User-driven policy simulator** — Describe Now request model using TRIBE/proxy need + speech + category.
8. **Character identity memory** — FocusedAD-style person state for social/narrative clips.
9. **Commentary residual AD** — MCAD-style transcript overlap suppression for sports/action clips.
10. **Soundscape surface gate** — Scene2Audio-style aesthetic layer only when intent and audio budget fit.
11. **Emotive style policy** — neutral/emotive/prosody routing for emotion-heavy scenes.
12. **Edge model feasibility gate** — local/cloud/human-review compute routing.
13. **Visual assistant skill policy** — question priors, verification mode, stateful player mode, and depth guards.
14. **Evidence-led answerability index** — map each answer to transcript/frame/storyboard/OCR/depth evidence.
15. **Task assistant affordance router** — route clips to step coaching, reality-video alignment, route rehearsal, community context, or watch-only access.
16. **Evidence sidecar cache** — build ASR/OCR/keyframe/timestamp sidecars and measure grounded answer errors.

## See also

- Per-paper notes in this directory
- `cursor/findings/paper-metric-leaderboard.md`
- `cursor/findings/discovery-breakthrough.md`
- `cursor/findings/access-surface-os.md`
- `cursor/findings/access-surface-router-run.md`
- `cursor/findings/access-surface-policy-comparison.md`
- `cursor/findings/commentary-residual-proxy.md`
- `cursor/findings/static-surface-weakspot-audit.md`
- `cursor/findings/access-surface-cost-model.md`
- `cursor/findings/visual-assistant-skill-policy.md`
- `cursor/findings/task-assistant-affordance.md`
- `cursor/findings/evidence-sidecar-readiness.md`

## Auto-generated correlation highlights

| pair | ρ | n |
|------|---:|---:|
| story_recall × vt_consistency | 0.902 | 72 |
| llm_ad_eval × ensemble | 0.887 | 72 |
