# Describe Now — User-Driven Audio Description for BLV Individuals

**Source:** [arxiv_2411.11835.pdf](sources/arxiv_2411.11835.pdf) · [arXiv](https://arxiv.org/abs/2411.11835)

## Why they did it

Traditional AD is fixed: somebody decides what to describe, when, and how much
detail to give. Describe Now tests a different model: BLV viewers request
descriptions while watching by pressing keys for concise or detailed AD.

Study:

- 20 BLV participants
- 7 short online video genres
- two levels of detail: concise and detailed
- participants could trigger descriptions at any time

The prototype paused playback, read the selected description, and resumed.
Descriptions were pre-generated with GPT-4V using AD guidelines.

Key findings:

- Users wanted different description frequencies by genre.
- Film/animation needed shorter intervals than education, health/fitness, and
  beauty.
- Concise descriptions were requested more often than detailed ones.
- Users reported more control and active watching, but also more cognitive load.
- Extended/paused descriptions helped comprehension but could reduce enjoyment.
- Needs varied strongly across BLV individuals, especially between blind and
  low-vision participants.

## What we agree with

- User agency is not a nice-to-have. It is part of accessibility quality.
- A single fixed AD schedule cannot satisfy all viewers or all genres.
- Concise-first with optional detail is probably the correct default.

## What we think is wrong / limited

1. **Manual user triggering is costly.** The paper proves demand for control but
   also introduces cognitive load. The product should infer when to offer detail,
   not make the user drive every decision.
2. **Extended pause is blunt.** Pausing solves timing but harms enjoyment. A
   mature system needs inline, deferred, replayable, and query modes.
3. **Generated AD is pre-baked.** The system does not adapt descriptions based on
   prior requests or viewer state.

## If I were them

I would turn the key presses into training labels for a policy:

```text
request type = f(video state, audio state, prior requests, user profile)
```

Then the system could predict when to surface a concise cue, when to offer a
detail chip, and when to stay silent.

## SceneTwin relevance

Describe Now is direct support for the SceneTwin pivot:

```text
static AD track -> adaptive access layer
```

TRIBE provides one missing signal the paper did not have: an upstream estimate
of where audio-only comprehension diverges from audiovisual comprehension.

Combined policy:

- high TRIBE debt + low speech: proactive concise AD
- high TRIBE debt + high speech: optional detail, not interruption
- repeated user detail requests: increase depth for this genre/user
- low TRIBE debt: stay silent unless queried

## Proposed prototype

`cursor/methods/user_driven_policy_sim.py`

Use existing external clips as simulated sessions:

1. Treat high ADQA critical miss windows as latent "would request detail."
2. Use TRIBE/proxy need, speech density, and category as policy inputs.
3. Compare static AD, proactive AD, and optional-detail policies.

Hypothesis: optional-detail policy wins on social-collision clips because it
preserves audio flow while giving the viewer agency over visual debt.
