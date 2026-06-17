# SceneTwin Scene-Model Correctness Gap

## Thesis

For AI audio description, **object grounding is not scene understanding**. A blind viewer can hear all the right nouns and still form the wrong mental model if the AD flips who did what, how many people there are, or the spatial/action relation between entities.

This is the strongest paper direction because it reframes AD safety around viewer comprehension, not caption similarity.

## Local novelty check

Repo search shows the object-bias negative result already existed, and the new relational probe-set artifact now exists. What was missing is the consolidated paper claim: connect CLIP failure, targeted scene-model probes, and generic ADQA question coverage into one argument. This script does that.

## Evidence 1 — CLIP gate catches object lies, not scene-model lies

| hallucination slice | clips | targeted probes | CLIP gate caught |
|---|---:|---:|---:|
| object / scene substitutions | 18 | 54 | 16/18 (88.9%) |
| who/action/count/spatial relation flips | 5 | 22 | 2/5 (40.0%) |

Interpretation: the safety gate is strong for wrong objects/scenes but weak exactly where the viewer's scene model can be inverted while nouns remain plausible.

## Evidence 2 — current ADQA is not guaranteed to probe the failure mode

Across `684` cached ADQA questions, scene-model questions are `349` (`51.0%`). Distribution:

- `action_relation`: 111
- `count`: 41
- `object_attr`: 183
- `other`: 152
- `spatial_relation`: 95
- `who_role`: 102

This does not mean ADQA is bad. It means generic question generation is opportunistic. If the risk is relation/action/count hallucination, the evaluator must force those probes instead of hoping they appear.

## Evidence 3 — targeted probes express the viewer mental model

Examples from the hard slice:

| clip | probe type | swap that must be tested |
|---|---|---|
| ShSSAEfnyDs_000000_000010 | action_relation | dozing->laughing |
| ShSSAEfnyDs_000000_000010 | action_relation | stir and react->grin and relax |
| ShSSAEfnyDs_000000_000010 | who_role | pushes person away->pulls person closer |
| ShSSAEfnyDs_000000_000010 | action_relation | covers camera/blocking->points camera/widening view |
| wbOD_G3ttgU_000083_000093 | count | three couples->two couples |
| wbOD_G3ttgU_000083_000093 | count | move in sync->move out of step |
| wbOD_G3ttgU_000083_000093 | count | occasionally twirling->rarely twirling |
| wbOD_G3ttgU_000083_000093 | count | changing partners->never changing partners |
| 3su234u58DA_000172_000182 | who_role | snowball fight->build a snowman |
| 3su234u58DA_000172_000182 | who_role | woman foreground->man foreground |
| 3su234u58DA_000172_000182 | action_relation | energetically throws snowballs->calmly rolls snowballs |
| 3su234u58DA_000172_000182 | action_relation | playful and bustling->focused and patient |

These are not cosmetic details. They decide whether the viewer understands the event: pushed away vs pulled closer, two vs three couples, snowball fight vs snowman building, saw cutting vs saw jamming.

## Paper-worthy claim

> SceneTwin shows that AD safety cannot be reduced to object-level visual grounding. Existing grounding catches object substitutions but misses scene-model errors. We introduce targeted scene-model probes for who/action/count/spatial relations, turning hallucination detection into a comprehension-safety benchmark for BLV viewers.

## What to run next

1. Give a VLM/video model and a text-only LLM these exact probes on truth vs hallucinated ADs.
2. Report by stratum: object/scene vs who/action/count/spatial.
3. If possible, ask BLV/proxy raters the probe questions after hearing each AD. Primary outcome: wrong mental model rate, not rho.

## Files

- `cursor/pipeline/scene_model_correctness_gap.py`
- `cursor/output/scene_model_correctness_gap/hallucination_clips.csv`
- `cursor/output/scene_model_correctness_gap/scene_model_probes.csv`
- `cursor/output/scene_model_correctness_gap/adqa_question_types.csv`
- `cursor/output/scene_model_correctness_gap/summary.json`
