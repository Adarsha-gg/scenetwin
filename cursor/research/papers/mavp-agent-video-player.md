# Multimodal Agent Video Player

Source: `sources/arxiv_2602.04104.pdf`  
arXiv: 2602.04104  
Date read: 2026-05-27

## Why they did it

Static audio description only provides what the author included. BLV viewers
cannot ask for clarification, jump to relevant moments, change detail level, or
inspect objects and characters that matter to them.

MAVP reframes video accessibility as a conversational, agentic player
experience.

## System features

The player supports:

- adaptive audio description detail
- pausing and asking scene-specific questions
- questions about broader context beyond the video
- voice control over playback and settings
- interactive guidance about available controls

Implementation uses:

- offline dense AD generation as a video content index
- transcript + metadata
- cached video index for faster retrieval
- query interpretation/refinement
- relevant timestamp search
- storyboard generation from selected frames
- intent classification for answer vs playback control vs settings
- speech output and customizable low-vision captions

## Study signal

The qualitative study had 8 participants after an 18-session co-design process.
Important reported signals:

- 7 of 8 participants had increased satisfaction after adding interactivity.
- The balanced/expansive default was a good detail level for 6 of 8, but 2 found
  it too much or irrelevant.
- Proactivity was appreciated by all participants if it could be turned off.
- Some users asked questions before or after the video, not only at the current
  frame.
- Voice settings control mattered because opening settings is burdensome.
- Users wanted control over speed, pitch, and descriptiveness.
- Metadata like title/description mattered for answering some questions.

## First-principles challenge

MAVP is closer to the right product than most AD papers because it treats video
as stateful media, not a sequence of caption windows.

But the architecture still looks prompt-heavy. The core product invariant should
be formal:

```text
answer(user_question, video_state, transcript, visual_index, history, risk)
```

If any part is missing, the assistant should say what it lacks or route to a
different surface. A player agent cannot be evaluated only by satisfaction; it
needs audit logs for which evidence source answered each question.

## What I would do if I were them

Make the player evidence-first:

- every answer cites the frame range / transcript segment / metadata source
- every playback action has a deterministic command parse
- every high-risk answer declares confidence and evidence gaps
- every proactive interruption has a reversible user setting

## Relevance to SceneTwin

This paper expands Access Surface OS into **Access Player OS**.

SceneTwin should produce the index MAVP needs:

- when the visual state changes
- what likely user question it answers
- which timestamp or frame range supports it
- whether the answer needs current-frame, multi-frame storyboard, transcript, or
  metadata

Implemented proxy:

- `cursor/methods/visual_assistant_skill_policy.py`

The `stateful_video_agent` mode marks clips where a video index/storyboard/history
is more appropriate than plain static AD.

## Correlation to test

```text
stateful_video_agent mode
  vs
clips where current-frame AD loses to a temporal or identity-aware answer
```

The right next experiment is a timestamped evidence index, not another caption
similarity score.
