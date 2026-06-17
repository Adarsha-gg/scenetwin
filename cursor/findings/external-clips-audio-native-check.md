# External Clips Audio-Native Check

Date: 2026-05-27

## What changed

There are more external clips than the earlier 18 cached benchmark:

- external clip directories with `clip.mp4`: **54**
- external registry entries: **54**
- external clips with need-proxy CSVs: **41**
- external clips with frame directories: **45**
- external eval rows: **45 unique videos** in `cursor/output/external_clip_full_eval.csv`
- external need-weighted eval rows: **41 unique videos** in `cursor/output/external_need_weighted_eval.csv`

The previous `tribe_audio_native_coach_validation.py` only used the 18 cached
numeric benchmark clips. It did **not** include these external clips.

## Important caveat

The external `cursor/data/external_clips/need/*.csv` files are not full TRIBE
predictions. They come from `cursor/pipeline/external_need_proxy.py`, which uses
motion plus speech/silence proxy features:

- `motion_score`
- `speech_density`
- `need_score`
- `standard_slot_score`
- `extended_need_score`

So this check is an external proxy stress test, not proof about TRIBE itself.

## Quick result

Using the available external proxy target:

`pro_not_best_any = tier3/pro AD is not best by the available external score`

on the 41 clips with need proxy:

| Signal | AUC | AP |
|---|---:|---:|
| need_only | **0.660** | **0.638** |
| speech_only | 0.620 | 0.602 |
| slotable_inverse | 0.610 | 0.598 |
| audio_native_proxy | 0.605 | 0.611 |
| collision_only | 0.589 | 0.595 |

## Interpretation

This weakens the earlier Audio-Native Coach claim. On the cached 18-clip
benchmark it looked better than baselines, but on the new external proxy set,
the simple `need_only` baseline is stronger for the available target.

The honest conclusion:

- **Audio-Native Coach remains a new use-case idea.**
- **It is not yet validated as “way better.”**
- The external clips should become the main validation set before making any
  strong claim.

## Output

The joined external proxy table was written to:

`cursor/output/external_audio_native_proxy_validation.csv`

## Next step

Run a real external validation target, not this weak proxy:

1. Generate critical ADQA questions for external clips.
2. Grade pro/static AD against those questions.
3. Compute true `critical_any_miss`.
4. Re-run audio-native, need-only, collision-only, speech-only, and category
   baselines.

Until then, the external evidence says: keep searching.
