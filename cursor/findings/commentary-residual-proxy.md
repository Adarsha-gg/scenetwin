# Commentary Residual AD — Proxy Run

Date: 2026-05-27

## What ran

Implemented `cursor/methods/commentary_residual_ad.py`, based on the MCAD paper
note. It asks:

```text
what does the original audio/commentary already cover?
what residual visual state remains?
is there enough auditory room to say it now?
```

Outputs:

- `cursor/methods/output/commentary_residual_ad.csv`
- `cursor/methods/output/commentary_residual_ad_summary.json`

## Important caveat

This is not yet true ASR/commentary measurement. The workspace has no ASR
libraries installed and no transcript sidecars for the external clips. A
YouTube auto-caption fetch attempt via `yt-dlp` hit HTTP 429.

So every row currently uses:

```text
audio_context_source = tier_summary_proxy
```

That means the script is transcript-ready, but the current run should be treated
as a dry-run proxy over tier1/tier2 summaries, not a validated commentary metric.

## Results on 58 external clips

| Residual action | n | Pro-not-best rate | Mean overlap | Mean residual terms | Mean speech | Mean need |
|-----------------|--:|------------------:|-------------:|--------------------:|------------:|----------:|
| queue_residual_replay | 21 | 0.571 | 0.178 | 24.619 | 0.973 | 0.825 |
| describe_residual_now | 6 | 0.500 | 0.241 | 16.500 | 0.180 | 0.754 |
| residual_concise_cue | 20 | 0.500 | 0.163 | 24.100 | 0.955 | 0.404 |
| static_ok | 11 | 0.182 | 0.183 | 22.455 | 0.499 | 0.315 |

The shape is sensible:

- `queue_residual_replay` is high speech + high need.
- `describe_residual_now` is high need + low speech.
- `static_ok` is low need and has the lowest pro-not-best rate.

## Router alignment

| Router surface | describe_now | queue_replay | concise_cue | static_ok |
|----------------|-------------:|-------------:|------------:|----------:|
| concise_cue | 0 | 2 | 4 | 0 |
| creator_qc | 0 | 0 | 3 | 0 |
| defer_replay | 0 | 12 | 0 | 0 |
| identity_chip | 4 | 7 | 5 | 2 |
| static_ad | 2 | 0 | 8 | 9 |

This supports the existing `defer_replay` surface: every `defer_replay` router
clip lands in `queue_residual_replay`. The weak spot is `static_ad`: 8 static
clips are flagged by the proxy as `residual_concise_cue`, but the follow-up
audit found all 8 are `target=0`. Treat those as proxy noise until real ASR or
user labels say otherwise.

## First-principles challenge

MCAD's core insight is residualization against real commentary. This prototype
does not yet have real commentary, so it cannot validate that insight. It only
validates the mechanics and shows where the router would use such a signal.

Next proof step:

1. Add real ASR sidecars for a small sample of speech-heavy clips.
2. Re-run `commentary_residual_ad.py`.
3. Compare `audio_context_source=asr.txt` rows against the proxy rows.
4. If proxy and ASR disagree, update the router to trust ASR only.
