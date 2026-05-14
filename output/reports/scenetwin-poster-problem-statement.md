---
title: SceneTwin Problem Statement — Poster Copy
created: 2026-05-11
---

# Problem statement — three versions

Drop whichever length fits the band you assign to it. Same argument, different word budget.

---

## Long version (~250 words — for a dedicated "Problem" band)

**Heading:** *Audio description is the bottleneck no one can scale.*

Audio description (AD) is the spoken narration that lets blind and low-vision
viewers follow visual content — characters, actions, environments, on-screen
text — that the audio track alone never carries. For roughly **285 million**
people worldwide who live with significant vision loss, AD is not a feature.
It is the entire interface to film, television, video lectures, social media,
and an increasing share of daily information.

**Today, quality assurance for AD is entirely manual.** A trained describer
or evaluator watches the video, listens to the candidate description, and
makes a holistic judgment: does this convey what a sighted viewer would see?
This works at the scale of one studio prepping one film. It does not work at
the scale of YouTube, TikTok, online courses, or any catalog with thousands
of hours of video.

**AI is now generating audio descriptions** — faster, cheaper, more
available than human-written ones. But AI-generated AD fails in ways manual
oversight catches only one clip at a time:
- **Hallucinated content** — confidently describing a scene that is not on screen
- **Vague content** — technically correct but uninformative ("a person doing something")
- **Missed visuals** — skipping key actions, expressions, or on-screen text
- **No visual grounding** — text-only quality metrics (BLEU, ROUGE) cannot
  detect any of the above, because they compare AD to a reference description,
  not to the video itself.

**The gap:** the field needs an automated audit that grounds the description
against the actual visual content, runs on any clip and any candidate
description, requires no reference text, and catches the specific failure
modes humans currently catch by watching.

---

## Medium version (~140 words — fits inside a column)

**Heading:** *Quality assurance for audio description doesn't scale.*

Audio description (AD) lets blind and low-vision viewers follow video. The
problem is its quality control: today it is **entirely manual**. A trained
evaluator watches the clip, hears the AD, and judges whether it conveys what
a sighted viewer would see. That works for one studio. It does not work for
the millions of hours of YouTube, online courses, and AI-generated content
now produced every day.

AI generation makes the gap worse. Generated AD is fast but uneven —
**hallucinated scenes, vague descriptions, missed visual events**. Existing
text-based metrics (BLEU, ROUGE) cannot detect any of these failure modes
because they compare AD to a *reference description*, not to the video
itself. Two skilled human describers will write very different but equally
valid scripts, so there is no single "correct" answer to compare against.

The field needs a **reference-free, visually grounded, automated audit**.

---

## Short version (~70 words — for a tight callout box)

**Heading:** *The bottleneck.*

Audio description is how blind and low-vision viewers access video — but
quality control is **manual, slow, and unscalable**. AI now generates AD
in seconds; AI also hallucinates scenes, skips visual events, and produces
vague output. Existing text metrics (BLEU, ROUGE) compare descriptions to
reference text — they cannot ground against the video itself. **No
reference-free, visually grounded audit exists.** SceneTwin is that audit.

---

## Stat / source check

| Claim | Notes |
|---|---|
| 285 M with significant vision loss | WHO estimate. Round to "hundreds of millions" if you want to skip the citation. |
| Manual QA is current practice | Industry standard. ACB, AMI, DCMP guidelines all assume human evaluator. |
| AI generation accelerating | YouDescribe, VideoA11y, Microsoft Seeing AI, etc. Mentioned in NJBDA-aligned papers. |
| BLEU/ROUGE inappropriate | Documented limitation; cited in CIDEr, CLIPScore, and ADQA papers. |
| Two valid AD writers diverge | Implicit in the VATEX / VideoA11y dataset construction — each clip has multiple human descriptions. |

All claims here are defensible without further citation, but if a reviewer asks, point to:
- WHO Vision Atlas (vision-loss stats)
- Recent VideoA11y paper (AI generation gap)
- CLIPScore / PAC-S papers (text-only metrics fail without visual grounding)
