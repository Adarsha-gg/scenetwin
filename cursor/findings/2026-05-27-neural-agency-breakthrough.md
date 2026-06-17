# Neural Agency Breakthrough

Date: 2026-05-27

## Validation note

Follow-up validation found that the first `agency_score` mixed ADQA miss labels
into the score. Treat this memo as a hypothesis and study design, not as the
validated breakthrough. The validated current breakthrough is the TRIBE
Escalation Gate in `cursor/findings/2026-05-27-validated-breakthrough.md`.

## One-line breakthrough

Use TRIBE to predict **when blind and low-vision viewers need agency**, not just
when a video needs audio description.

The research move is:

> from “score this AD transcript” to “decide when passive narration is the
> wrong interface.”

## Why this is a breakthrough direction

Recent BLV video-access work is moving beyond one static AD track:

- ViDscribe shows the value of customizable AD and conversational VQA for BLV
  YouTube access.
- ADCanvas shows BLV creators need accessible authoring tools where they retain
  agency over AI-generated information.
- VideoA11y shows MLLMs can generate higher-quality BLV-oriented descriptions,
  but it is still primarily about description quality.
- TRIBE v2 is different: it predicts neural responses to video, audio, and
  language, enabling counterfactual modality experiments.

SceneTwin can connect these threads. TRIBE can be the missing scheduler that
answers: **where should a viewer be offered control, a question interface,
pauseable detail, or human-reviewed description?**

## New artifact

- Script: `cursor/neural_agency_map.py`
- Clip-level output: `cursor/output/neural_agency_map.csv`
- Window-level output: `cursor/output/neural_agency_windows.csv`
- Report: `cursor/findings/neural-agency-map.md`

## Current result

The script combines:

- TRIBE visual debt (`P_AV - P_A`) split into collision/slotable debt,
- original-audio speech occupancy,
- professional-AD misses on critical ADQA questions,
- existing TRIBE evaluator-fragility risk.

On current cached data:

- Clips with TRIBE debt: **20**
- Clips with evaluator labels: **18**
- Recommended interventions:
  - extended/integrated AD: **10**
  - interactive VQA first: **4**
  - human review: **3**
  - standard inserted AD: **2**
  - lightweight/no AD: **1**
- `agency_score` vs professional AD critical miss rate: Spearman rho **0.617**
- `agency_score` vs pro AD miss rate: rho **0.377**
- `agency_score` vs full tier order: rho **-0.375**

This is the first result in the repo that directly supports the statement:

> TRIBE can predict where passive AD is likely to leave important viewer
> questions unanswered.

That is stronger than “TRIBE improves CLIP” because it defines a new research
task where TRIBE is naturally upstream and causal: **agency allocation**.

## What the top cases mean

Top `interactive_vqa_first` clips:

1. `clip_18`, Pets & Animals: collision debt = 1.0, critical miss rate = 1.0.
2. `clip_17`, Pets & Animals: collision debt = 0.922, critical miss rate = 0.5.
3. `clip_00`, Food & Cooking: collision debt = 1.0, critical miss rate = 1.0.
4. `clip_07`, Travel: collision debt = 1.0, critical miss rate = 0.667.

These are not simply “bad AD” cases. They are clips where the original audio is
occupied, visual debt is high, and passive/professional AD misses important
questions. That is exactly where an interactive BLV interface should beat a
single static narration.

## Falsifiable hypothesis

For high-agency clips, **TRIBE-scheduled interactive VQA** should outperform
standard inserted AD and ordinary generated AD on:

1. BLV answer accuracy for critical visual questions,
2. perceived control,
3. listener burden,
4. story/task comprehension,
5. trust in the accessibility layer.

For low-agency clips, static AD should be enough.

## Research protocol

1. Select high-agency and low-agency clips from `neural_agency_map.csv`.
2. For each clip, create three access conditions:
   - standard inserted AD,
   - extended/integrated AD,
   - interactive VQA/pauseable detail.
3. Ask BLV users or a strong proxy evaluator to answer critical questions and
   rate burden/control.
4. Test whether TRIBE agency score predicts the condition where interactive
   access provides the largest gain.

The headline metric should be:

`interactive_gain = VQA_condition_score - static_AD_condition_score`

Then test:

`corr(TRIBE agency_score, interactive_gain) > 0`

## Why this keeps the project core

The project remains:

- BLV video access,
- TRIBE-based neural counterfactuals,
- ADQA/CLIP/VLM evaluation as downstream checks,
- SceneTwin as the research workspace.

But the contribution becomes larger:

- not a better AD metric,
- not a better caption generator,
- a neural policy for when accessibility should become interactive.

## Next script

Build `cursor/interactive_gain_protocol.py`.

It should output a study table with:

- clip id,
- high/low agency stratum,
- selected windows,
- critical missed questions,
- required intervention,
- prompts for static AD, extended AD, and VQA condition,
- expected evaluation questions.

That would turn this from a finding into a publishable experimental design.

## Sources checked

- TRIBE v2: https://arxiv.org/abs/2605.04326
- ViDscribe: https://arxiv.org/abs/2603.14662
- ADCanvas: https://arxiv.org/abs/2602.07266
- VideoA11y: https://arxiv.org/abs/2502.20480
