---
title: "SceneTwin QuerYD Video-Native ADQA Eval"
category: research
tags: [SceneTwin, QuerYD, Gemini, video-native, ADQA, human-AD]
created: 2026-05-13
updated: 2026-05-13
sources:
  - https://www.robots.ox.ac.uk/~vgg/data/queryd/
  - https://github.com/oncescuandreea/QuerYD_downloader
  - output/live_held_out_queryd_gemini.csv
---

# SceneTwin - QuerYD Video-Native ADQA Eval

## Why This Exists

The VATEX held-out tests used caption-style candidates, not real audio description scripts.
That made video-native grading look worse than frame-based grading because the grader asked
valid temporal questions that short captions were never meant to answer.

This run switches to QuerYD, a YouDescribe-derived dataset with human audio description
transcripts and timestamps. It is a better test for video-native ADQA because the top tier is
actual human AD text aligned to a real video segment.

Important caveat: QuerYD is real human AD, but it is not guaranteed to be professionally
authored studio AD. It is still much closer to the intended target than VATEX captions or
VideoA11y one-sentence descriptions.

## Method

Downloaded QuerYD v2 captions, timestamps, and YouTube links from the Oxford VGG QuerYD
release and downloader repo.

For each selected clip:

- Picked a compact 8-16 second window with several human AD utterances.
- Downloaded the source YouTube video and trimmed the segment with ffmpeg using the AD
  timestamp window.
- Extracted 8 frames for CLIP scoring.
- Uploaded the real MP4 segment to Gemini Flash for video-native question generation and
  grading.

Candidate tiers:

| Tier | Candidate |
|---|---|
| tier0_cross | Full human AD from a different QuerYD clip |
| tier1_min | First human AD utterance only |
| tier2_partial | First half of the human AD utterances |
| tier3_full | Full human AD window |

## Result

Run output: `output/live_held_out_queryd_gemini.csv`

| Metric | Spearman rho | p |
|---|---:|---:|
| CLIP top-3 frame score | 0.617 | 0.0038 |
| Gemini video-native ADQA | 0.865 | 0.0000 |
| CLIP + ADQA ensemble | 0.932 | 0.0000 |

Ordering:

- Pairwise ordered wins: 13/15
- Fully ordered clips: 3/5
- n = 5 clips, 20 tier observations

## Interpretation

This is the result we were looking for: when the candidate set actually contains human AD
transcript windows, video-native ADQA stops collapsing and becomes the strongest signal.

The previous Gemini/VATEX failure was a dataset mismatch, not proof that video-native grading
is worse. VATEX captions are too short and caption-like, so Gemini correctly penalizes them
for missing temporal AD details. QuerYD gives the grader the kind of input it was designed to
score.

## Poster-Safe Claim

Use this framing:

> On caption-style held-out candidates, the live 8-frame ensemble reached rho = 0.840. A
> follow-up video-native eval on real human QuerYD audio-description windows reached rho =
> 0.932 (n = 5), showing that video-native ADQA helps when the candidates are actual AD
> transcripts rather than short video captions.

Do not call QuerYD "professional studio AD" unless we replace it with a licensed professional
script corpus.

