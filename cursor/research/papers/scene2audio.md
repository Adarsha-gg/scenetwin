# Scene2Audio — Generative Soundscapes for BLV Vista Experiences

**Source:** [arxiv_2603.27295.pdf](sources/arxiv_2603.27295.pdf) · [arXiv](https://arxiv.org/abs/2603.27295)

## Why they did it

Scene2Audio challenges the assumption that visual access must be spoken prose.
For distant landscape "vista" scenes, the authors generate nonverbal soundscapes
from visual content using psychoacoustic and sound-design principles. They test
four output styles:

- speech-only
- audio-only nonverbal sound
- overlay of speech plus sound
- overlay-concat, with sequential object-level speech and sound

In a lab study with 11 BLV participants, overlay was the most preferred. A
week-long mobile app study with 7 BLV users found that sound effects can enhance
outdoor scene experiences, but mismatched or artificial sounds damage trust.

## What we agree with

- Speech is not the only access channel. Aesthetic experience can require sound,
  mood, and spatial presence.
- Sound-only is ambiguous. The paper correctly keeps speech as a disambiguating
  layer instead of replacing description entirely.
- The surface should depend on context. Outdoor vista/leisure scenes and utility
  scenes need different policies.

## What we think is wrong / limited

1. **The use case is narrower than the title sounds.** It is strongest for
   vistas and aesthetic scenes, not generic video or safety-critical navigation.
2. **Generated sound can hallucinate emotionally.** A wrong soundscape may feel
   persuasive while being false.
3. **No relation to existing audio.** For videos, the soundtrack already has
   music, speech, ambience, and effects. Adding generated audio may collide.

## If I were them

I would turn Scene2Audio into an optional **aesthetic layer**, gated by:

- visual scene type
- existing audio density
- user intent: utility vs ambience
- hallucination risk
- replay context, not live interruption

The system should default to speech-only for utility tasks and offer soundscape
only when the goal is experience, memory, or immersion.

## SceneTwin relevance

Scene2Audio expands SceneTwin's access surfaces beyond text and TTS. It pairs
with WorldScribe and CustomAD:

```text
TRIBE/audio debt says visual information is missing.
WorldScribe asks whether to speak now.
Scene2Audio asks whether prose is the wrong modality.
```

For social-collision clips, generated sound is usually wrong. For landscape,
travel, museum, or aesthetic clips, an optional soundscape can be a better
surface than verbose description.

## Proposed prototype

`cursor/methods/soundscape_surface_gate.py`

Inputs:

- scene category and object density
- existing speech/music/ambience density
- user intent: utility, narrative, aesthetic, orientation
- model confidence in sonic objects

Outputs:

- `allow_soundscape`
- `speech_required`
- `soundscape_risk`
- `recommended_mix`

Hypothesis: nonverbal sound should be treated as an optional access surface, not
as an AD replacement.
