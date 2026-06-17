# First-Principles TRIBE Reframe

Date: 2026-05-27

## Thesis

The better use case for TRIBE in SceneTwin is not AD transcript scoring.

The stronger use case is **forecasting the accessibility intervention required
by a video before any candidate audio description exists**.

SceneTwin should become a research system for answering:

> Given a video and its original audio, what accessibility intervention is
> required: no AD, standard inserted AD, extended/integrated AD, interactive
> queryable AD, or mandatory human review?

That is the native TRIBE problem. TRIBE predicts cortical response to video,
audio, and language, so the unique signal is counterfactual modality debt:
`P_AV - P_A`. A caption evaluator asks “is this text good?” TRIBE asks a more
primitive question: “what does the original audio fail to carry from the visual
world, and is there room to say it?”

## What I read

Repository and current research artifacts:

- `README.md`: SceneTwin is currently an AD audit workspace using CLIP grounding,
  frame-grounded ADQA, and cached TRIBE risk.
- `workspace/tribev2/README.md`: TRIBE v2 predicts fMRI responses on fsaverage5
  cortical mesh and supports video, audio, and text inputs.
- `workspace/tribev2/tribev2/model.py`: the core model projects modality
  features, combines them, runs a Transformer, and predicts cortical outputs.
- `workspace/tribev2/tribev2/eventstransforms.py`: audio/text paths are timing
  sensitive; text is not just inert text, it becomes timed language events.
- `demo/live_pipeline.py`: the live proxy already moved toward paper-aligned
  `P_AV`, `P_A`, and `P_AD`, but live/demo is not the research priority here.
- `tools/scenetwin_tribe_failure_forecast.py`: the current best TRIBE result is
  failure forecasting, not direct scoring.
- `cursor/research/tribe-v2-deep-dive.md`, `cursor/research/literature-scan-2026-05-27.md`,
  and today’s `cursor/findings/*`: prior experiments already killed raw
  Description Gain and weak ROI content typing.

External context checked on 2026-05-27:

- [TRIBE v2 arXiv 2605.04326](https://arxiv.org/abs/2605.04326): tri-modal
  brain encoding for in-silico neuroscience; this supports modality
  counterfactuals as the correct abstraction.
- [ADQA, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.1199/): audio
  description evaluation should cover visual appreciation and narrative
  understanding over coherent segments, not just caption similarity.
- [Scalable AD QC with VLM raters, 2026](https://arxiv.org/abs/2602.01390):
  evaluation should be multidimensional and keep human oversight in the loop.
- [ADx3, 2026](https://arxiv.org/abs/2602.02684): the field is moving toward
  collaborative generation, refinement, and on-demand adaptation, which matches
  a TRIBE-driven intervention router better than a single score.

## First-principles decomposition

The BLV access problem is not “produce more words.”

It has four constraints:

1. **Missing visual state**: the viewer does not receive visual facts from the
   original audio.
2. **Temporal scarcity**: AD can only be inserted where there is time, unless
   the experience is modified.
3. **Semantic priority**: not all missing visual information matters equally for
   story, action, space, emotion, or task success.
4. **Evaluator fragility**: automatic judges fail exactly where the media is
   dense, subjective, or temporally constrained.

TRIBE is uniquely useful for the first two constraints because it can compare
predicted brain response for audiovisual input against audio-only input. CLIP
and ADQA are better for content correctness after a candidate AD exists.

## Evidence from current data

Existing strongest TRIBE finding:

- `mean_standard_slot_score` ranks both known all-judge full-order failures
  #1 and #2 out of 18.
- Top-2 review recall on known failures is **2/2**.
- Current digest reports `mean_standard_slot_score` vs all-judge tier ordering:
  rho approximately **-0.75**, p approximately **0.00033**.
- A local dependency-free recomputation gives rho **-0.599** against the
  binary full-order column in `tribe_failure_forecast.csv`; direction is the
  same and the top-2 capture remains the core evidence.

New artifact added in this pass:

- Script: `cursor/neural_accessibility_debt.py`
- Output: `cursor/output/neural_accessibility_debt.csv`
- Report: `cursor/findings/neural-accessibility-debt.md`

It splits TRIBE need windows into:

- **slotable debt** = high visual need during low speech density,
- **collision debt** = high visual need during high speech density.

Current results:

- Need-window clips analyzed: **20**
- Clips with cached evaluator/failure labels: **18**
- Debt modes: **14 collision**, **5 balanced**, **1 slotable**
- Known all-judge failures caught by top-2 existing TRIBE risk rank: **2/2**
- Slotable debt vs full tier order: rho **-0.599**

Interpretation: the hard cases are not merely “visually rich.” They are videos
where visual need and audio occupancy create a policy conflict. Standard AD
cannot simply be inserted without colliding with the original audio.

## The better use case

Build SceneTwin around **Neural Accessibility Debt**:

| Debt state | Intervention |
|---|---|
| low debt | no AD or lightweight summary |
| slotable debt | standard inserted AD |
| collision debt | extended AD, integrated AD, pauseable playback, or interactive query |
| high debt + low evaluator margin | human review before release |

This is more groundbreaking than another metric because it changes the research
object. The project stops asking “which AD text scores higher?” and starts
asking “what kind of accessibility experience does this video require?”

## Why this beats the current framing

Current framing:

- Score candidate AD with CLIP + ADQA.
- Use TRIBE as a cached benchmark-side risk signal.
- Keep trying to squeeze TRIBE into a text-quality score.

Better framing:

- Use TRIBE before candidate text exists.
- Forecast where the original audio fails as an accessibility carrier.
- Separate standard-slot opportunities from collision cases.
- Route each clip/window to the correct access policy.
- Then use CLIP, ADQA, VLM judges, and human review only after the policy is
  known.

This also explains why prior TRIBE directions failed:

- Raw Description Gain failed because text-only cortical similarity is not the
  same as useful AD.
- ROI content typing failed because atlas-level region labels are too coarse
  for semantic slot assignment.
- Need-weighted CLIP did not generalize strongly because “where to look” is not
  the same as “what intervention is possible.”

## Research program

Next research should prioritize these tests:

1. **Debt-policy validation**: label cached and external clips as no AD,
   standard AD, extended/integrated AD, or interactive AD. Test whether TRIBE
   debt predicts expert policy better than motion, speech density, CLIP, or
   category.
2. **Collision-specific evaluation**: for high collision debt clips, compare
   standard AD against extended/pauseable/interactive variants. The target is
   not tier order; it is BLV answer accuracy plus listener burden.
3. **Slot placement benchmark**: treat AD slot timing as first-class. Current
   slot IoU F1 is **0.55**, meaning placement itself is unsolved.
4. **External generalization**: the external set shows full tier order only
   **3/28** in the current heuristic run, so future claims must validate outside
   the 18 cached clips.
5. **Narrative understanding gap**: current ADQA is mostly visual-appreciation
   questions. Add multi-minute narrative-understanding questions before making
   broad claims about story access.

## Concrete next artifact

Create a `debt_policy_eval.py` research script that joins:

- `neural_accessibility_debt.csv`,
- external clip metadata,
- slot IoU,
- ADQA/CLIP/VLM scores,
- human or proxy policy labels.

The output should be a policy confusion matrix, not a single rho:

`none | standard | extended/integrated | interactive | human_review`.

That would make TRIBE the first-pass accessibility policy model for video,
which is a cleaner and more defensible research contribution than trying to
make it a better caption scorer.
