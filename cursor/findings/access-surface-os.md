# Access Surface OS — SceneTwin's Stronger Use Case

Date: 2026-05-27

## Claim

SceneTwin should stop trying to be mainly an AD scorer or generator. The stronger
use case is an **access surface operating system** for BLV video access.

It should decide:

```text
whether to describe
when to describe
what residual state to describe
which surface to use
which compute tier to trust
when to ask the user or creator
```

## Why this is new relative to the papers

No single ingested paper builds this complete router:

- TRIBE supplies visual-vs-audio neural debt.
- AudioCapBench supplies audio sufficiency and hallucination framing.
- ADQA supplies residual viewer questions.
- CustomAD and Describe Now supply user controls.
- SPICA supplies object/spatial exploration.
- ADCanvas supplies creator verification.
- WorldScribe supplies intent/sound/latency live policy.
- FocusedAD supplies identity memory.
- MCAD supplies commentary residualization.
- Scene2Audio supplies optional nonverbal sound.
- Emotive AD style research supplies style/prosody as a policy choice.
- Lightweight VLM work supplies local/cloud/human compute routing.

The combination is the product:

```text
Residual visual state
  + audio sufficiency
  + viewer intent
  + identity/emotion/domain state
  + interruption risk
  + model uncertainty
  -> access surface + compute choice
```

## Access surfaces

| Surface | When it is right | When it is wrong |
|---------|------------------|------------------|
| Static AD | clear gap, low speech collision, low uncertainty | dense dialogue/social collision |
| Concise cue | viewer needs orientation but audio is busy | critical visual evidence is missing |
| Detail chip | user may want more without forced interruption | user cannot interact right now |
| Object explorer | spatial/object inventory matters | narrative/action is the real gap |
| Identity chip | who/relationship changed | identity confidence is low |
| Emotive style | emotion/reaction is central | utility/navigation/high uncertainty |
| Soundscape | aesthetic vista/leisure scene | speech-dense, utility, or safety context |
| Creator QC | model uncertainty or high-stakes claim | low-risk obvious scenes |
| Live defer/replay | visual event matters but now is a bad time | immediate hazard or plot-critical state |

## Evidence from current workspace

The refreshed external proxy run covers 58 clips. The current headline row in
`cursor/output/tribe_social_collision_external_metrics.csv` is:

```text
external_proxy_clip_top3 / social_collision_boundary:
n=58, positives=27, AUC=0.723, AP=0.698
```

That is not enough to claim a solved ranking metric. It is enough to justify a
router trigger: social/audio collision is a warning that the static-AD surface
may be wrong.

## First prototype built

Built and ran `cursor/methods/access_surface_router.py`.

Inputs:

- `social_collision_boundary`
- speech density
- need score
- category
- candidate CLIP grounding margin
- ADQA critical miss types
- optional transcript overlap
- optional identity/emotion flags

Outputs:

- `surface`: static_ad, concise_cue, detail_chip, object_explorer,
  identity_chip, creator_qc, soundscape, defer
- `reason`
- `risk`
- `compute_tier`: local, cloud, cached, human

Run artifacts:

- `cursor/methods/output/access_surface_router.csv`
- `cursor/methods/output/access_surface_router_summary.json`
- `cursor/findings/access-surface-router-run.md`

First result: the router sent 25 of 27 pro-not-best external clips away from
`static_ad`, and 22 of 24 high-collision clips away from `static_ad`. This does
not prove user value, but it proves the paper synthesis can be expressed as a
testable routing policy over the existing 58 clips.

Baseline comparison:

- `need_only`: 15/27 pro-not-best clips routed away from static AD
- `social_collision`: 16/27 pro-not-best clips routed away from static AD
- `surface_router_v1`: 25/27 pro-not-best clips routed away from static AD

See `cursor/findings/access-surface-policy-comparison.md`.

Cost-aware follow-up:

- `surface_router_v1` mean presentation cost: 0.272
- `all_static` mean presentation cost: 0.582
- `need_only` mean presentation cost: 0.374
- `social_collision` mean presentation cost: 0.403

This is the sharper use case: catch visual misses while reducing spoken-now
burden. See `cursor/findings/access-surface-cost-model.md`.
