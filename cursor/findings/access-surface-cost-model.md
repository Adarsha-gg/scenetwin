# Access Surface Cost Model

Date: 2026-05-27

## Why this exists

The first policy comparison counted every route away from `static_ad` as the
same kind of intervention. That hides the core product idea:

```text
identity chip != queued replay != creator QC != spoken interruption
```

So `cursor/methods/access_surface_cost_eval.py` adds a simple cost model over the
58 external clips. It scores presentation burden, not model compute. Dense speech
and low slot availability make spoken-now surfaces more costly; passive chips,
queued replay, and creator review are cheaper.

Outputs:

- `cursor/methods/output/access_surface_cost_eval.csv`
- `cursor/methods/output/access_surface_cost_eval_summary.json`

## Result

| Policy | Mean cost | Spoken-now rate | Passive rate | Queued rate | Pro-not-best recall | Misses | Caught targets / cost |
|--------|----------:|----------------:|-------------:|------------:|--------------------:|-------:|----------------------:|
| all_static | 0.582 | 1.000 | 0.000 | 0.000 | 0.000 | 27 | 0.000 |
| need_only | 0.374 | 0.534 | 0.466 | 0.000 | 0.556 | 12 | 0.692 |
| speech_need | 0.395 | 0.638 | 0.000 | 0.362 | 0.444 | 15 | 0.524 |
| social_collision | 0.403 | 0.586 | 0.414 | 0.000 | 0.593 | 11 | 0.685 |
| surface_router_v1 | 0.272 | 0.431 | 0.362 | 0.207 | 0.926 | 2 | 1.586 |

## Interpretation

This is the strongest current evidence for the Access Surface OS use case.

The router is not better because it "does more AD." It is better because it
separates visual-access demand from interruption:

```text
catch high-risk visual misses
without forcing every miss into spoken narration now
```

That is why a high non-static count can still be a lower-cost product. The
router shifts many risky clips into identity chips, queued replay, and creator
QC, while using concise cues only where dense audio still leaves a negative
grounding margin.

## Challenge

The cost weights are hand-set. They are useful for first-principles comparison,
not a user-validated utility function. To harden this:

1. Collect BLV preference labels for surface burden.
2. Learn the cost weights from pairwise "would this interrupt you?" judgments.
3. Split `spoken_now_rate` into actual timing overlap once ASR or AD timing is
   available.
4. Evaluate per user goal: entertainment, learning, navigation, creator review.

Even with those caveats, the result reframes the project. SceneTwin's
groundbreaking use case is not "score captions." It is:

```text
an interruption-aware access router for choosing the least burdensome surface
that still resolves the viewer's residual visual state.
```
