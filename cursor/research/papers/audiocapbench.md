# AudioCapBench — Quick Evaluation on Audio Captioning across Sound, Music, and Speech

**Source:** [arxiv_2602.23649.pdf](sources/arxiv_2602.23649.pdf) · [arXiv](https://arxiv.org/abs/2602.23649)

## Why they did it

Audio captioning is not ASR. A useful caption must capture the acoustic scene:
sound sources, music attributes, speaker emotion, and temporal relationships. The
paper argues existing captioning benchmarks mostly stress environmental sounds
and are not designed to evaluate general multimodal models.

They build a 1,000-sample benchmark:

- 400 environmental sound samples from Clotho and AudioCaps
- 300 music samples from MusicCaps
- 300 speech samples from an emotional speech caption dataset

They evaluate 13 OpenAI/Gemini models with reference metrics and an LLM judge
scoring three dimensions:

- **Accuracy** — semantic correctness
- **Completeness** — coverage of reference content
- **Hallucination** — absence of fabricated content

Their key finding is a precision/recall tradeoff: conservative models hallucinate
less but say too little; more detailed models cover more but fabricate more.
Speech is easiest, music is hardest.

## What we agree with

- The accuracy/completeness/hallucination triad is cleaner than one fused
  "quality" score. SceneTwin needs the same split for AD: correct, sufficient,
  and non-fabricated are different axes.
- Audio cannot be reduced to transcript. For SceneTwin, music, affect, crowd
  sound, tempo, and non-speech cues explain why some clips need no AD while
  others need extra visual context.
- Conservative-but-empty is a real failure mode. A short AD that avoids errors
  can still be useless to a BLV viewer.

## What we think is wrong / limited

1. **References still define truth.** Hallucination is judged against references,
   but a reference caption may omit real sounds. That can punish true but
   unmentioned detail.
2. **No user task.** The benchmark scores caption quality, not whether the audio
   helps someone make a decision, follow a story, or know whether visual
   description is still needed.
3. **No audio-visual conflict.** SceneTwin's hard cases are often "the audio says
   something, but the visual tells the real state." AudioCapBench is audio-only.

## If I were them

I would add an **audio sufficiency** task: after hearing the audio caption, ask
what visual questions remain unanswered. That would turn audio captioning into a
bridge toward accessibility rather than a standalone caption leaderboard.

I would also make hallucination reference-aware but not reference-bound:
distinguish "contradicts reference" from "unsupported by reference." The latter
is not always false.

## SceneTwin relevance

AudioCapBench suggests a new SceneTwin leg: **Audio Sufficiency QA**.

For each clip:

1. Summarize the raw audio in the AudioCapBench dimensions.
2. Generate ADQA questions from frames.
3. Predict which ADQA questions are already answerable from audio.
4. Route only the remaining questions to AD or interactive detail.

This pairs naturally with TRIBE:

```text
TRIBE P_AV - P_A  = neural visual debt
AudioCap triad    = what the soundtrack already carries
ADQA              = viewer questions still unanswered
```

## Proposed prototype

`cursor/methods/audio_sufficiency_qa.py`

Inputs:

- existing transcript/speech density
- optional audio caption from an audio LMM
- frame-grounded ADQA questions

Outputs:

- `audio_answerable_rate`
- `audio_hallucination_risk`
- `residual_visual_question_count`

Hypothesis: social/entertainment clips with high speech but low audio
sufficiency are exactly where the new social-collision boundary should route to
interactive access instead of longer static AD.
