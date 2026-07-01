# SceneTwin Relational Hallucination Probe Set

## New useful artifact

SceneTwin already proved the CLIP grounding-drop gate is object-biased: it catches object/scene swaps but fails on who-did-what, count, and spatial/action relation errors. Those errors are exactly the ones that can make a blind viewer misunderstand the scene even when all salient nouns are present.

This script converts the red-team into a reusable **targeted comprehension probe set**: every authored hallucination swap becomes a concrete question with a true answer and a hallucinated foil. It is not another metric-number chase; it is the missing benchmark layer for relation/action/count safety.

## Local novelty check

Repo search found the existing relational-lie negative result, but no targeted question/probe set built from the swaps. So this is new: it turns the limitation into an evaluation dataset that future ADQA/VLM/human studies can use.

## Result

Built `76` targeted probes from `23` hand-authored hallucination clips.

| slice | clips | probes | CLIP gate caught clips |
|---|---:|---:|---:|
| object/scene swaps | 18 | 54 | 16/18 |
| relation/action/count swaps | 5 | 22 | 2/5 |

Probe-type distribution:

- `action_relation`: 37
- `count`: 13
- `spatial_relation`: 16
- `who_role`: 10

## Relation/action/count examples

| clip | type | question | true answer | hallucinated foil |
|---|---|---|---|---|
| ShSSAEfnyDs_000000_000010 | spatial_relation | What is the correct spatial/relational fact: dozing? | dozing | laughing |
| ShSSAEfnyDs_000000_000010 | spatial_relation | What is the correct spatial/relational fact: stir and react? | stir and react | grin and relax |
| ShSSAEfnyDs_000000_000010 | who_role | Who is involved or in that role: pushes person away? | pushes person away | pulls person closer |
| ShSSAEfnyDs_000000_000010 | spatial_relation | What is the correct spatial/relational fact: covers camera/blocking? | covers camera/blocking | points camera/widening view |
| wbOD_G3ttgU_000083_000093 | count | What number/count should the AD convey for: three couples? | three couples | two couples |
| wbOD_G3ttgU_000083_000093 | count | What number/count should the AD convey for: move in sync? | move in sync | move out of step |
| wbOD_G3ttgU_000083_000093 | count | What number/count should the AD convey for: occasionally twirling? | occasionally twirling | rarely twirling |
| wbOD_G3ttgU_000083_000093 | count | What number/count should the AD convey for: changing partners? | changing partners | never changing partners |
| 3su234u58DA_000172_000182 | who_role | Who is involved or in that role: snowball fight? | snowball fight | build a snowman |
| 3su234u58DA_000172_000182 | who_role | Who is involved or in that role: woman foreground? | woman foreground | man foreground |
| 3su234u58DA_000172_000182 | spatial_relation | What is the correct spatial/relational fact: energetically throws snowballs? | energetically throws snowballs | calmly rolls snowballs |
| 3su234u58DA_000172_000182 | spatial_relation | What is the correct spatial/relational fact: playful and bustling? | playful and bustling | focused and patient |

## Why this is worth keeping

A BLV viewer often needs the relation, not just the nouns: who pushed whom, how many people danced, whether someone pulled closer or pushed away, whether the saw cut or jammed. CLIP can see the same nouns and still miss the false relation. These probes force evaluators to ask the exact scene-model question that matters.

## How to use next

1. Grade candidate ADs against these probes with a cross-family LLM judge or BLV/proxy raters.
2. Add one relation/action/count probe per clip to ADQA generation prompts.
3. Report safety by stratum: object/scene vs relation/action/count, instead of one inflated hallucination AUC.

## Files

- `cursor/pipeline/relational_hallucination_probe_set.py`
- `cursor/output/relational_hallucination_probe_set/probes.csv`
- `cursor/output/relational_hallucination_probe_set/clips.csv`
- `cursor/output/relational_hallucination_probe_set/summary.json`
