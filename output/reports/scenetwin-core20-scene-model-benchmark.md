# SceneTwin-Core-20 Scene-Model Benchmark

## What changed

This consolidates the confusing `23` hallucination clips and `13` valid TRIBE targets into one canonical `N=20` benchmark: the existing local TRIBE timing clips. It is not claiming all 20 targets are TRIBE-generated: 13 are TRIBE-derived and 7 are manual scene-model gap targets used to fill the canonical benchmark.

Each clip now has:

1. the professional AD,
2. one controlled object/scene lie,
3. one controlled scene-model lie,
4. one canonical scene-model target question,
5. generic ADQA target-coverage comparison.

The four scene-model axes remain a taxonomy, not sample size: who/role, action/relation, count, spatial relation.

## Core-20 composition

| axis | clips |
|---|---:|
| action_relation | 13 |
| count | 1 |
| spatial_relation | 4 |
| who_role | 2 |

| target source | clips |
|---|---:|
| manual_gap | 7 |
| tribe | 13 |

## Target-coverage result

| probe source | exact scene-model target coverage | loose related coverage |
|---|---:|---:|
| Core-20 canonical target | 20/20 | 20/20 |
| generic_claude | 3/20 | 13/20 |
| generic_gpt4o | 1/20 | 11/20 |

Strict means the generic question asks the same scene-model axis with enough lexical overlap to plausibly catch the exact controlled flip. Loose means it asks a related scene-model question but may not isolate the corrupted fact.

## Interpretation

This gives the paper a clean main benchmark: `N=20` throughout the TRIBE mechanism. Core-20 canonical targets define the exact scene-model fact to protect. Thirteen targets come directly from TRIBE high-need questions; seven are manual scene-model gap targets added only to make the benchmark a clean N=20. Generic ADQA often asks broad visual questions but does not reliably hit the exact protected fact.

The old `23`-clip hallucination set should now be framed as a red-team diagnostic. The old `13` valid-target result is superseded by this Core-20 authored benchmark.

## Example generic misses

| clip | axis | canonical target | best generic Claude question | overlap |
|---:|---|---|---|---:|
| 0 | action_relation | What does the chef throw at the wall, and what happens after the knife is thrown? | What is the man in the white shirt holding and demonstrating? | 0.00 |
| 2 | action_relation | What is the person doing with the bottle and glass? |  | 0.00 |
| 3 | action_relation | What is the man doing to the food in the skillet? | What is the person cooking in the skillet? | 0.17 |
| 5 | action_relation | What are the two people doing with the garlic and spinach? | What is the main subject doing? | 0.17 |
| 6 | spatial_relation | What vehicles are visible on the snowy surface, and what are they doing? | What is the terrain like where the snowmobiler is riding? | 0.00 |
| 7 | action_relation | What is the person doing in the snow, and what equipment are they using? | What is the main subject doing in these frames? | 0.17 |
| 8 | action_relation | How does the scene change from the ranch sign to the people on horses? |  | 0.00 |
| 9 | spatial_relation | What sport or activity is the person performing on the snow-covered surface? | What sport or activity is the person performing? | 0.57 |
| 10 | who_role | Who is spotting the young gymnasts as they flip on the mat? |  | 0.00 |
| 11 | action_relation | What is the person attempting to do with the high jump bar? | What is the young person in the yellow shirt doing in these video clips? | 0.10 |

## Files

- `cursor/pipeline/core20_scene_model_benchmark.py`
- `cursor/output/core20_scene_model_benchmark/core20_truth_lies.csv`
- `cursor/output/core20_scene_model_benchmark/generic_target_coverage.csv`
- `cursor/output/core20_scene_model_benchmark/summary.json`
