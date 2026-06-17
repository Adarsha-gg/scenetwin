# Static Surface Weak-Spot Audit

Date: 2026-05-27

## Question

The MCAD-inspired residual proxy flagged several `static_ad` clips as needing a
`residual_concise_cue`. Before broadening the router, we checked whether those
flags were real static failures or proxy noise.

## What changed

The original residual proxy warning was too broad: 9 clips routed as `static_ad`
were flagged as `residual_concise_cue`, but 8 of those 9 had `target=0`. Since
all rows currently use `audio_context_source=tier_summary_proxy`, that was a
warning about the proxy, not proof that static AD was wrong.

The router was updated with one narrow deployable rule:

```text
negative CLIP grounding margin
  + dense speech
  + low standard AD slot score
  -> concise_cue, secondary defer_replay
```

This fired on exactly one clip:

| Clip | Target | Category | Margin | Speech | Slot | Surface |
|------|-------:|----------|-------:|-------:|-----:|---------|
| `8vkNr_eysXY_000002_000012` | 1 | How-to & Instructional | -0.009 | 1.000 | 0.000 | concise_cue |

## Result

After the change:

- `surface_router_v1` catches 25 of 27 pro-not-best clips.
- Avoidable static misses dropped from 3 to 2.
- Static safety rose to 0.857 because only 2 of 14 static clips are target=1.
- The weak residual proxy still flags 8 `static_ad` clips as
  `residual_concise_cue`, but all 8 are `target=0`.

Remaining static misses:

| Clip | Category | Margin | Need | Speech | Slot | Collision |
|------|----------|-------:|-----:|-------:|-----:|----------:|
| `iZP6gjlr_nM_000113_000123` | How-to & Instructional | -0.033 | 0.165 | 0.709 | 0.159 | 0.117 |
| `0m0-Q0zz_-c_000112_000122` | How-to & Instructional | -0.008 | 0.052 | 0.455 | 0.244 | 0.024 |

## First-principles read

This is the line between a product rule and overfitting:

```text
dense audio + no slot + negative grounding margin
is a real presentation conflict.

low collision + some slot + low need
is not enough evidence to interrupt.
```

The next improvement should not be another broad heuristic. The corrected
residual rerun shows why: the proxy keeps flagging low-collision static clips
that the external label says are safe. The next evidence should be either real
ASR/commentary sidecars or user labels for low-collision instructional clips.
Without that, the router should leave those two misses as known residual risk
instead of creating noisy interruptions.
