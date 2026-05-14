---
title: "SceneTwin QuerYD Video-Native ADQA Eval"
category: research
tags: [SceneTwin, QuerYD, Gemini, video-native, ADQA, human-AD]
created: 2026-05-13
updated: 2026-05-13
sources:
  - output/reports/scenetwin-queryd-video-native-eval.md
  - https://www.robots.ox.ac.uk/~vgg/data/queryd/
  - https://github.com/oncescuandreea/QuerYD_downloader
---

# SceneTwin - QuerYD Video-Native ADQA Eval

VATEX held-out candidates were captions, not real AD scripts. Gemini video-native grading
asked valid temporal AD questions, but the captions were too short to pass them.

QuerYD fixes the candidate mismatch by using YouDescribe-derived human AD transcripts with
timestamps. I built `tools/scenetwin_queryd_gemini_eval.py` to download transcript-aligned
YouTube segments, trim the real MP4 with ffmpeg, and grade four transcript-derived tiers:

- `tier0_cross`: full human AD from another clip
- `tier1_min`: first human AD utterance only
- `tier2_partial`: first half of the human AD utterances
- `tier3_full`: full human AD window

## Result

Output CSV: `output/live_held_out_queryd_gemini.csv`

| Metric | Spearman rho | p |
|---|---:|---:|
| CLIP top-3 frame score | 0.617 | 0.0038 |
| Gemini video-native ADQA | 0.865 | 0.0000 |
| CLIP + ADQA ensemble | 0.932 | 0.0000 |

Pairwise ordered wins: 13/15. Fully ordered clips: 3/5. n = 5 clips, 20 tier observations.

## Interpretation

Video-native ADQA works when the candidate set is actually AD-like. The earlier Gemini/VATEX
drop was a dataset mismatch, not a model ceiling. For poster wording, say "real human QuerYD
audio-description windows," not "professional studio AD."

