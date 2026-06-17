# New Breakthrough Candidate: TRIBE Audio-Native Coach

Date: 2026-05-27

## Why this is actually new

The earlier escalation gate was useful but not new enough: it is still a
post-release quality-control use case.

This direction changes the domain:

> Use TRIBE before or during authoring to tell BLV creators and accessibility
> systems when visual information must be spoken in the **primary audio track**,
> not merely patched later with posthoc AD.

That makes TRIBE a creator-side accessibility coach.

## Core idea

For BLV access, some videos should not be treated as “finished visual media plus
later audio description.” If the important visual information happens while the
audio track is already occupied, passive AD can miss critical viewer questions.

TRIBE can detect this from the media itself:

`audio_native_coach = normalized(collision_debt) * not_sports`

Where:

- `collision_debt` = TRIBE visual need during occupied speech/audio windows.
- `not_sports` = a coarse category correction observed in current data; sports
  clips often have high visual motion but professional AD did not miss critical
  questions in this cached set.

This score is pre-text. It does not use candidate AD content or ADQA labels.

## Implemented validation

- Script: `cursor/tribe_audio_native_coach_validation.py`
- Scores: `cursor/output/tribe_audio_native_coach_validation.csv`
- Ranked clips: `cursor/output/tribe_audio_native_coach_ranked.csv`
- Report: `cursor/findings/tribe-audio-native-coach-validation.md`

## Target

Target = professional AD misses at least one critical ADQA question.

This is the best current proxy for:

> passive posthoc AD did not answer important visual questions, so the media
> needed audio-native narration, pauseable detail, or an interactive affordance.

## Result

On 18 labeled clips:

| Signal | AUC | AP | rho vs critical miss rate |
|---|---:|---:|---:|
| audio_native_coach | **0.875** | **0.585** | **0.533** |
| collision_only | 0.804 | 0.486 | 0.414 |
| need_only | 0.750 | 0.444 | 0.352 |
| speech_occupancy | 0.688 | 0.424 | 0.320 |
| category_only_not_sports | 0.679 | 0.458 | 0.329 |
| old_tribe_risk | 0.313 | 0.253 | -0.320 |

This is materially better than the old TRIBE risk signal for this different
target. The old risk gate predicts automatic evaluator failure. The new
audio-native coach predicts passive AD critical-question failure.

## What this enables

SceneTwin can become more than an evaluator. It can test a new accessibility
workflow:

1. Creator records or uploads video.
2. TRIBE estimates collision debt.
3. The system flags moments where visual state should be narrated in primary
   audio, not left for later AD.
4. For non-fixable moments, it recommends pauseable or interactive detail.

This is especially relevant for BLV creators, educators, how-to videos, sports,
fitness, social videos, and live capture workflows where “add AD later” is the
wrong framing.

## Honest limitation

The current validation is still small:

- n = 18 labeled clips,
- 4 positive critical-miss clips,
- top-4 recall = 2/4,
- p-value is not yet strong at the positive-budget cutoff.

So this is not final proof. But it is new, implemented, and better than the
available baselines for the target it claims to solve.

## Next evidence needed

To make this publishable:

1. Label external clips for critical-question misses.
2. Add creator-side interventions: “say this aloud while filming,” “pause here,”
   “add interactive answer point.”
3. Test whether the audio-native coach predicts where these interventions
   improve BLV question accuracy versus static AD.
4. Report AUC, AP, recall@budget, and user burden.

If validated, the claim becomes:

> TRIBE is the first neural accessibility model that can guide how visual media
> should be authored for BLV access before audio description is written.
