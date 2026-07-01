# TRIBE Scene-Model Probe Routing

## Question

Can TRIBE help with the stronger SceneTwin paper claim — AD safety as scene-model correctness — rather than just object grounding?

## Honest answer

**Promising yes, but narrow:** TRIBE does not directly detect relation/action/count hallucinations here. What it can do is route evaluation toward high audiovisual-need moments, and those moments are much more likely to demand scene-model questions: who/action/count/spatial relation, not just object labels.

## Local novelty check

Existing repo work had TRIBE timing, TRIBE-need ADQA, and CLIP object-bias negatives. I did not find a test explicitly asking whether TRIBE high-need routing enriches scene-model probes. This script runs that consolidation test from cached local questions only.

## Result

| source | n questions | scene-model questions | rate | 95% CI |
|---|---:|---:|---:|---:|
| generic_gpt4o | 90 | 41 | 45.6% | [35.7, 55.8] |
| generic_claude | 90 | 52 | 57.8% | [47.5, 67.5] |
| tribe_prompted_all | 90 | 56 | 62.2% | [51.9, 71.5] |
| tribe_high_need_matched | 44 | 35 | 79.5% | [65.5, 88.8] |

Comparisons against TRIBE high-need matched questions:

- `tribe_high_need_vs_generic_claude`: delta `21.8 pp`, permutation p `0.0089`
- `tribe_high_need_vs_generic_gpt4o`: delta `34.0 pp`, permutation p `0.0002`
- `tribe_high_need_vs_tribe_prompted_all`: delta `17.3 pp`, permutation p `0.0327`

Clip-level: `14/14` clips with high-need questions get at least one scene-model probe; `7/14` get a count/spatial probe.

## Examples of TRIBE-routed scene-model probes

| clip_idx | type | TRIBE need | question |
|---:|---|---:|---|
| 0 | who_role | 0.47 | What is the man in the white shirt holding and demonstrating? |
| 0 | who_role | 0.47 | What type of setting or environment is the man in? |
| 0 | count | 0.47 | How many times does the man's facial expression or gesture change across the frames? |
| 1 | who_role | 0.85 | What is the man in the gray hoodie doing with his hands in the opening seconds? |
| 1 | who_role | 0.85 | What is the man holding or consuming in the high-need opening sequence? |
| 4 | who_role | 0.57 | What is the child holding and doing with it at the kitchen counter? |
| 4 | who_role | 0.50 | What is the child's apparent emotional state during this activity? |
| 6 | action_relation | 0.76 | What vehicles are visible on the snowy surface, and what are they doing? |
| 6 | spatial_relation | 0.53 | What is the relative position of the snowmobiles as the sequence progresses? |
| 7 | who_role | 0.94 | What is the person doing in the snow, and what equipment are they using? |
| 7 | spatial_relation | 0.74 | What is the setting or terrain where this activity is taking place? |
| 7 | spatial_relation | 0.54 | What is the perspective or camera angle showing in these frames? |

## Paper implication

This gives TRIBE a real role in the scene-model paper: **not** as the final hallucination detector, but as a neural router that decides where the evaluator must ask scene-model questions. The final detector should be targeted ADQA/VLM/human probes over those TRIBE-routed moments.

Possible central claim:

> SceneTwin combines neural need routing with targeted scene-model probes: TRIBE selects moments where audio under-specifies the visual scene, and the probe layer tests whether the AD preserves who/action/count/spatial relations rather than merely naming objects.

## Next hard validation

Run the targeted probes on truth vs hallucinated ADs with a video-capable VLM and a text-only judge. If TRIBE-routed probes catch relation/action/count lies better than generic ADQA, that becomes the paper's strongest result.

## Files

- `cursor/pipeline/tribe_scene_model_probe_routing.py`
- `cursor/output/tribe_scene_model_probe_routing/question_routing.csv`
- `cursor/output/tribe_scene_model_probe_routing/summary.json`
