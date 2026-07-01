# LVOmniBench — Long Audio-Video Understanding for Omnimodal LLMs

**Source:** [arxiv_2603.19217.pdf](sources/arxiv_2603.19217.pdf) · [arXiv](https://arxiv.org/abs/2603.19217)

## Why they did it

Most audio-video benchmarks are short. LVOmniBench targets real long-form video:
275 Creative Commons videos, 10-90 minutes long, with 1,014 multiple-choice QA
pairs. The benchmark is built to require joint audio-visual reasoning rather
than unimodal shortcuts.

The paper's categories include long-term memory, temporal localization,
fine-grained understanding, multimodal perception, and reasoning. It also
filters questions by testing whether audio-only, video-only, or text-only cues
can answer them.

Headline results:

- Gemini 3 Pro reaches about 65.8% overall.
- Open-source omnimodal models mostly stay below 35%.
- Video-only and audio-only ablations drop sharply.
- Open models often improve when ASR text is provided, suggesting weak long
  audio utilization.
- Error analysis finds perception, localization, cross-modal semantic gaps, and
  reasoning failures. Audio perception errors are a major part of perception
  failures.

## What we agree with

- Long-form access is not a scaled-up 10-second caption problem. Memory and
  temporal localization become first-class.
- Their unimodal filtering is exactly the right benchmark hygiene: questions
  should prove they require A+V, not merely claim it.
- The audio bottleneck matters. SceneTwin's current external clips are short,
  but BLV access in the real world includes lectures, livestreams, tutorials,
  podcasts-with-video, and long entertainment.

## What we think is wrong / limited

1. **Multiple-choice hides access needs.** A model can select the right option
   without producing the explanatory description a BLV viewer would need.
2. **Benchmark difficulty is not user importance.** Some hard questions are
   irrelevant for accessibility; some easy questions are critical for agency.
3. **Long videos need stateful consumption, not one-shot QA.** For BLV use, the
   product question is when to interrupt, summarize, defer, or let the user ask.

## If I were them

I would add a "watching policy" track:

- At which timestamps should the system proactively describe?
- When should it stay silent?
- When should it offer optional detail?
- Which later questions become answerable because of earlier descriptions?

That would evaluate temporal access strategy, not just answer retrieval.

## SceneTwin relevance

LVOmniBench gives SceneTwin the missing long-form north star:

```text
short clip scoring     -> does this AD match this 10s window?
long-form access       -> does the system maintain a useful viewer state?
```

TRIBE can become the compression/routing layer for long videos:

- use P_AV - P_A to mark high-debt intervals
- use speech/audio-caption sufficiency to suppress unnecessary AD
- use ADQA/ViDscribe questions as memory probes
- use LVOmni-style A/V filtering to find questions that static AD cannot solve

## Proposed prototype

`cursor/methods/longform_access_state_probe.py`

Start without long videos:

1. Stitch existing external clips into synthetic 2-5 minute sequences.
2. Maintain a running "BLV viewer state" summary.
3. Probe it with ADQA questions after each segment.
4. Score proactive AD vs optional query vs silence.

Hypothesis: social-collision clips should not be described more often; they
should produce better state checkpoints and optional drill-downs.
