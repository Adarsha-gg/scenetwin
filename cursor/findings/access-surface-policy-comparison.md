# Access Surface Policy Comparison

Date: 2026-05-27

## What changed

The first router run exposed an evaluation leak: `target` was used inside the
router's risk and creator-QC logic. That is now fixed. `target` is used only in
`access_surface_router_eval.py` for measurement.

Current router inputs are deployable proxy signals:

- need / speech / slotability
- social-collision score
- category
- CLIP grounding margin
- lexical identity/emotion/spatial/aesthetic cues from candidate text

## Policy comparison

Ran `cursor/methods/access_surface_router_eval.py` on the 58 external clips.

| Policy | Non-static n | Non-static rate | Pro-not-best recall | High-collision recall | Static safety | Avoidable static misses |
|--------|-------------:|----------------:|--------------------:|----------------------:|--------------:|------------------------:|
| all_static | 0 | 0.000 | 0.000 | 0.000 | 0.534 | 27 |
| need_only | 27 | 0.466 | 0.556 | 0.542 | 0.613 | 12 |
| speech_need | 21 | 0.362 | 0.444 | 0.333 | 0.595 | 15 |
| social_collision | 24 | 0.414 | 0.593 | 1.000 | 0.676 | 11 |
| surface_router_v1 | 44 | 0.759 | 0.926 | 0.917 | 0.857 | 2 |

Definitions:

- **Pro-not-best recall:** fraction of clips where pro AD was not best by
  external CLIP proxy and the policy routed away from `static_ad`.
- **High-collision recall:** fraction of clips with `social_collision_boundary`
  >= 1.0 routed away from `static_ad`.
- **Static safety:** among clips left as `static_ad`, fraction where pro AD was
  not marked pro-not-best.
- **Avoidable static misses:** pro-not-best clips still left as `static_ad`.

## Interpretation

Need-only and speech+need baselines miss too many pro-not-best clips. Pure
social-collision is more precise and catches every high-collision clip, but it
misses non-social high-need cases.

The cross-paper router catches the most pro-not-best clips: 25 of 27. Its cost
is higher non-static rate: 44 of 58 clips become non-static. That is the right
tradeoff for an accessibility router only if the surfaces are costed correctly:
passive identity chips, queued replay, creator QC, and concise cues should not
all be treated like forced spoken interruptions.

The important result is not "v1 is optimal." It is:

```text
combining paper-derived surfaces beats single-axis policies
for deciding when static AD is likely the wrong surface.
```

A separate cost audit strengthens this: `surface_router_v1` has the lowest mean
presentation cost in the current model (0.272) while catching 25/27 pro-not-best
clips. See `cursor/findings/access-surface-cost-model.md`.

## Next challenge

The router still needs stronger, non-lexical inputs:

1. real transcript/commentary overlap for MCAD-style residual AD
2. person-region or identity tracking for FocusedAD-style identity memory
3. object density and spatial layout for SPICA-style object explorer
4. user preference priors for CustomAD / Describe Now controls
5. a cost model so `non_static` distinguishes passive chips from interruptions

The latest weak-spot audit added one narrow rule for dense-speech, no-slot,
negative-margin clips and left two low-collision instructional misses as known
residual risk. See `cursor/findings/static-surface-weakspot-audit.md`.

The first version of item 5 is now implemented in
`cursor/methods/access_surface_cost_eval.py`. The next prototype should target
item 1 or 2 because those directly test whether the router's largest surfaces,
`identity_chip` and `defer_replay`, are real.
