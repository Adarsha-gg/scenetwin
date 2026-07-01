# All-Clip Scene-Model Audit

## Question

Does the scene-model thesis hold beyond the small TRIBE/hallucination subsets? Across all local VideoA11y/VATEX overlap clips, do professional ADs encode more who/action/count/spatial structure than ordinary captions?

## Scope

Checked all `338` clips in `workspace/vatex_overlap.json` (`3718` total texts: one professional AD plus VATEX captions per clip).

Important limitation: this is a text-side corpus audit, not a TRIBE result. Full TRIBE tensors for all 338 clips are not present in this checkout, so TRIBE routing remains validated on the cached 20-clip timing stack only.

## Result

Professional ADs cover more scene-model axes than the average VATEX caption on `314/338` clips, with `18` losses and `6` ties. Exact sign-test p = `5.69e-71`.

Mean scene-model axes: professional AD `3.03` vs average caption `1.93`; mean delta `+1.10` axes per clip.

Professional AD has at least as many scene-model axes as the strongest individual caption on `269/338` clips.

| axis | pro presence | any caption presence | average caption presence |
|---|---:|---:|---:|
| who_role | 93.5% | 100.0% | 84.1% |
| action_relation | 92.6% | 97.9% | 57.9% |
| spatial_relation | 80.8% | 89.1% | 29.3% |
| count | 35.8% | 56.8% | 21.2% |

Density note: professional ADs are longer and more complete, so term density per 100 words is not the right headline; categorical coverage is. The thesis is that AD must preserve multiple scene-model axes, not maximize keyword density.

## Category breakdown

| category | n | mean pro-minus-caption axes | wins | losses |
|---|---:|---:|---:|---:|
| Event | 16 | 1.26 | 16 | 0 |
| Food & Cooking | 22 | 1.22 | 21 | 1 |
| Health & Wellness | 30 | 1.18 | 29 | 0 |
| How-to & Instructional | 93 | 1.15 | 85 | 6 |
| Sports | 46 | 1.12 | 43 | 2 |
| People & Vlogs | 29 | 1.04 | 26 | 3 |
| Entertainment | 50 | 0.99 | 48 | 1 |
| Pets & Animals | 19 | 0.88 | 16 | 2 |
| Film & Animation | 5 | 0.88 | 5 | 0 |
| Music | 18 | 0.87 | 15 | 3 |

## Interpretation

This supports the central thesis at corpus scale: professional ADs are not merely longer object captions. They systematically add scene-model structure — who is involved, what actions unfold, counts/groups, and spatial relations. That is exactly the information that relation/action/count hallucinations corrupt and object grounding misses.

## How this connects to TRIBE

- All-clip text audit: professional ADs encode richer scene-model axes across 338 clips.
- Hallucination audit: object grounding catches object/scene swaps but misses scene-model flips.
- TRIBE timing subset: high neural access-gap moments are enriched for scene-model probes (`79.5%` scene-model questions).

Together: scene-model information is what professional AD adds; object grounding misses when it is wrong; TRIBE helps decide where to probe it.

## Files

- `cursor/pipeline/all_clip_scene_model_audit.py`
- `cursor/output/all_clip_scene_model_audit/clips.csv`
- `cursor/output/all_clip_scene_model_audit/texts.csv`
- `cursor/output/all_clip_scene_model_audit/summary.json`
