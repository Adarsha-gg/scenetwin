# CustomAD — Audio Description Customization

**Source:** [arxiv_2408.11406.pdf](sources/arxiv_2408.11406.pdf) · [arXiv](https://arxiv.org/abs/2408.11406)

## Why they did it

The paper starts from a simple accessibility failure: one professionally written
audio description cannot fit every BLV viewer, every task, and every moment in a
video. Their formative study with 15 BLV participants found that viewers wanted
control over description length, emphasis, speed, voice, format, tone, and
language. The prototype then lets users change content controls such as length
and emphasis, plus presentation controls such as speed, voice, tone, gender, and
syntax.

In the 12-participant evaluation, customization improved prompt accuracy
substantially, but it also increased completion time. The most frequently used
control was emphasis, then length, then speed.

## What we agree with

- Customization is not decoration. The empirical result says controls can
  improve understanding, not only satisfaction.
- Length is a risky control. More detail can help a task but interrupt the flow,
  which is exactly the conflict SceneTwin sees in speech-dense social clips.
- Emphasis is the useful primitive. Activity/person/object/setting maps more
  cleanly to viewer intent than a generic "verbose" slider.

## What we think is wrong / limited

1. **The system asks the user to do too much policy work.** If every clip asks
   for manual tuning, the interface moves cognitive burden from the author to
   the viewer.
2. **Controls are treated as global preferences.** The right setting changes
   inside a video: a cooking step, a social reaction, and a setting transition
   need different emphasis.
3. **No predictive router.** The paper shows users want controls, but it does
   not ask when a system should proactively offer a control versus stay quiet.

## If I were them

I would make customization conditional, not constant. First predict the moment's
failure mode:

- missing action
- missing object
- missing person/relation
- missing setting
- delivery/timing conflict

Then expose only the one or two controls that match that failure. That preserves
agency without making the user operate a full authoring console while watching.

## SceneTwin relevance

CustomAD is the missing user-control layer for the TRIBE social-collision result.
TRIBE/proxy collision tells us when linear AD is likely the wrong surface;
CustomAD tells us which knobs users actually value when the surface changes.

The 58 external clips make this concrete. The late-arriving clips lowered the
social-collision AUC from the earlier 54-clip result, but the boundary still beat
need-only, speech-only, and slotability baselines. That means we should not claim
"social collision solves AD." The stronger claim is:

```text
social collision -> offer the right control, not a longer static caption
```

## Proposed prototype

`cursor/methods/customization_policy_router.py`

Inputs:

- SceneTwin ADQA miss type or critical evidence noun bucket
- TRIBE/proxy need, speech density, and social-collision boundary
- candidate controls: length, emphasis, speed, concise/detail

Outputs:

- `recommended_control`
- `control_confidence`
- `expected_user_burden`
- `fallback_static_ad_ok`

Hypothesis: controls should be offered only when the predicted understanding
gain exceeds the interaction burden.
