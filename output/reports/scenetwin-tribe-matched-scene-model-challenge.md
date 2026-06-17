# TRIBE Matched Scene-Model Challenge

## What this checks

On the 20 local TRIBE timing clips, select the highest-need TRIBE-routed scene-model question per clip. Treat each as the exact relation/action/count/spatial fact a hallucination could corrupt. Then ask whether generic ADQA would independently ask a sufficiently similar question.

This is not final hallucination grading. It is the required precursor: a detector cannot catch a scene-model hallucination if it never asks about the corrupted relation.

## Result

TRIBE produced `14` high-need scene-model targets across the timing clips.

| question source | strict target coverage | loose target coverage |
|---|---:|---:|
| generic_claude | 4/14 | 11/14 |
| generic_gpt4o | 3/14 | 10/14 |

Strict = same scene-model type and enough lexical overlap with the TRIBE high-need target. Loose = any partially overlapping scene-model question.

## Interpretation

TRIBE-routed probes cover the selected high-need scene-model risks by construction (`14/14`). Generic ADQA often asks broad scene questions, but it frequently misses the exact high-need relation/action/count/spatial fact. This supports TRIBE as a router: it tells the evaluator which scene-model fact to ask about, rather than hoping generic questions land there.

## Example generic misses against TRIBE targets

| clip | TRIBE target type | TRIBE target | best generic Claude question | overlap |
|---:|---|---|---|---:|
| 6 | spatial_relation | What vehicles are visible on the snowy surface, and what are they doing? | What is the terrain like where the snowmobiler is riding? | 0.00 |
| 7 | action_relation | What is the person doing in the snow, and what equipment are they using? | What is the main subject doing in these frames? | 0.17 |
| 9 | spatial_relation | What sport or activity is the person performing on the snow-covered surface? | What sport or activity is the person performing? | 0.57 |
| 11 | action_relation | What is the person attempting to do with the high jump bar? | What is the young person in the yellow shirt doing in these video clips? | 0.10 |
| 12 | count | How many players are visible on the court at the moment shown in these frames? | What structures or barriers are visible around the court? | 0.14 |
| 13 | spatial_relation | Describe the main player's position and movement during the opening seconds. | What is the setting where this activity takes place? | 0.00 |
| 14 | action_relation | What happens to the curler between the first and final frames shown? | What happens to the player after releasing the stone? | 0.14 |
| 15 | spatial_relation | What is the person doing with the wooden fence as they move along the path? | What is visible on the fence in the background? | 0.12 |

## What this proves / does not prove

Proves: TRIBE high-need routing identifies specific scene-model facts that generic ADQA does not reliably target.

Does not yet prove: a full end-to-end hallucination catch-rate win, because we still need graded truth-vs-hallucinated ADs on these exact targets.

## Next direct run

For each target, create or hand-author one AD that flips that exact fact, then grade truth vs lie with the TRIBE target question and generic ADQA. If the target-question grade catches the flips that generic ADQA/CLIP miss, the central claim is locked.

## Files

- `cursor/pipeline/tribe_matched_scene_model_challenge.py`
- `cursor/output/tribe_matched_scene_model_challenge/targets.csv`
- `cursor/output/tribe_matched_scene_model_challenge/comparisons.csv`
- `cursor/output/tribe_matched_scene_model_challenge/summary.json`
