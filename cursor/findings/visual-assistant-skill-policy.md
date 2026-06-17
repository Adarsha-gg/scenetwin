# Visual Assistant Skill Policy

Date: 2026-05-27

## Why this exists

The latest paper batch makes a sharper distinction:

```text
caption quality is not assistant readiness
```

The diary study shows initial MLLM descriptions can be accurate while follow-up
answers still hallucinate, especially for text/graphics and other high-risk
requests. MAVP shows video access wants stateful player control and a video
index. GuideDog shows spatial/depth guidance needs stronger verification than
ordinary scene description. The proactive-question paper shows likely BLV
questions can be anticipated from historical visual contexts.

`cursor/methods/visual_assistant_skill_policy.py` turns those ideas into a first
auditable policy over the 58 external clips.

## Outputs

- `cursor/methods/output/visual_assistant_skill_policy.csv`
- `cursor/methods/output/visual_assistant_skill_policy_summary.json`

## Modes

| Mode | Meaning |
|------|---------|
| `plain_description` | no special assistant behavior needed |
| `proactive_question_chip` | likely follow-up, offer a small optional question |
| `stateful_video_agent` | needs video index/storyboard/history/player state |
| `verify_before_answer` | likely hallucination-sensitive answer; require caution or evidence |
| `depth_guarded_guidance` | spatial/navigation-like answer needs depth/obstacle guard |

## Result on 58 clips

| Mode | n | Pro-not-best rate | Mean follow-up pressure |
|------|--:|------------------:|------------------------:|
| `stateful_video_agent` | 22 | 0.591 | 0.795 |
| `verify_before_answer` | 19 | 0.632 | 0.671 |
| `plain_description` | 9 | 0.111 | 0.307 |
| `depth_guarded_guidance` | 5 | 0.000 | 0.581 |
| `proactive_question_chip` | 3 | 0.333 | 0.516 |

Summary:

- 49 of 58 clips need some assistant behavior beyond plain description.
- Assistant-not-plain recall on pro-not-best clips: 26/27 = 0.963.
- 19 clips require `verify_before_answer`.
- 22 clips require `stateful_video_agent`.
- 5 clips require `depth_guarded_guidance`.
- Only one pro-not-best clip is still left as `plain_description`.

## First-principles interpretation

This is the new product boundary:

```text
SceneTwin should not only choose the access surface.
It should choose the assistant behavior contract.
```

The behavior contract answers:

- should the system proactively offer a likely question?
- should it answer now or require verification?
- does it need frame history or a storyboard?
- is spatial/depth confidence required?
- is plain AD enough?

## Why this is more novel than another AD scorer

An AD scorer says:

```text
this caption is better than that caption
```

The visual-assistant policy says:

```text
this clip is unsafe to answer conversationally without evidence
this clip needs video memory
this clip needs a proactive question affordance
this clip should remain plain description
```

That is closer to the actual BLV use case in the new papers: reliable, goal-led
assistance under uncertainty.

## Known limits

This is lexical and proxy-based. It does not yet have:

- OCR/text detection
- ASR/commentary
- object/depth sidecars
- real user follow-up labels
- question logs from BLV users on these clips

The next strongest prototype is an evidence-led answerability index:

```text
for each clip/time:
  evidence sources present: transcript, frame, multi-frame storyboard, OCR, depth
  allowed assistant modes: describe, ask, verify, defer, handoff
```
