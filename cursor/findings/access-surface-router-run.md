# Access Surface Router — First External Run

Date: 2026-05-27

## What ran

Implemented `cursor/methods/access_surface_router.py` and ran it on the 58
external clips using:

- `cursor/output/tribe_social_collision_external_rows.csv`
- `cursor/data/external_clips/registry.jsonl`
- existing per-clip category/text/need/speech/collision fields

Outputs:

- `cursor/methods/output/access_surface_router.csv`
- `cursor/methods/output/access_surface_router_summary.json`

This is a heuristic prototype, not a trained model. The point is to make the
paper synthesis falsifiable on the current clip corpus. The router was revised
after the first pass to avoid using the evaluation `target` field in routing.
`target` now appears only in the separate evaluation script.

## Router result

Surface counts over 58 clips:

| Surface | Count |
|---------|------:|
| identity_chip | 18 |
| defer_replay | 12 |
| static_ad | 19 |
| concise_cue | 6 |
| creator_qc | 3 |

The router sent 25 of 27 pro-not-best clips away from `static_ad`
(`pro_not_best_not_static_rate = 0.926`).

High collision clips were also mostly routed away from static AD:
22 of 24 high-collision clips were non-static
(`high_collision_not_static_rate = 0.917`).

## Surface diagnostics

| Surface | n | Pro-not-best rate | Mean collision | Mean speech | Mean need |
|---------|--:|------------------:|---------------:|------------:|----------:|
| creator_qc | 3 | 1.000 | 1.346 | 1.000 | 0.346 |
| identity_chip | 18 | 0.667 | 1.521 | 0.752 | 0.689 |
| concise_cue | 6 | 0.667 | 0.597 | 0.953 | 0.625 |
| defer_replay | 12 | 0.500 | 0.872 | 0.975 | 0.808 |
| static_ad | 19 | 0.105 | 0.299 | 0.639 | 0.342 |

This is exactly the shape we wanted from the cross-paper argument:

```text
static_ad is mostly low-risk / low-collision
identity_chip absorbs social high-collision clips
defer_replay absorbs high-need clips with no speech slot
creator_qc catches small high-risk uncertain cases
```

## First-principles challenge

The current router is useful but not yet good enough:

1. **Identity is lexical, not visual.** FocusedAD says identity must be tracked
   visually. This prototype only counts person words in the pro text.
2. **Commentary is proxied, not transcribed.** MCAD says overlap with actual
   commentary matters. This prototype uses tier text overlap only.
3. **Soundscape and object explorer are under-tested.** The 58-clip external set
   has few true vista/spatial-exploration cases, so those surfaces are not
   validated yet.
4. **Risk is heuristic.** It combines pro-not-best, collision, speech+need, and
   margin, but lacks calibrated user harm or human labels.

## Next improvement

Built `cursor/methods/access_surface_router_eval.py` to compare routing policies:

- `all_static`
- `need_only`
- `speech_need`
- `social_collision`
- `surface_router_v1`

Result: `surface_router_v1` routed 25/27 pro-not-best clips away from static AD,
compared with 15/27 for need-only and 16/27 for social-collision. It left only 2
avoidable static misses, compared with 12 for need-only and 11 for
social-collision.

The latest narrow weak-spot fix is documented in
`cursor/findings/static-surface-weakspot-audit.md`. Then add a transcript pass
for `commentary_residual_ad.py`, a person-region pass for
`character_identity_memory.py`, and a cost model that separates passive surfaces
from interruptions.
