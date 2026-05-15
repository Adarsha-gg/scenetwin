---
title: "TRIBE metric glossary"
category: reference
tags: [scenetwin, tribe, glossary, demo]
created: 2026-05-14
---

# TRIBE metric glossary

Plain English explanations of every number that appears on the TRIBE
page (`web/pages/tribe.jsx`) and what high vs low values actually mean.

## Top of the page (the five stat cards)

### Recall@2 (100%)

Out of the 18 clips in the benchmark, 2 are "failures": clips where
the 4-judge ADQA panel got the tier ordering wrong. TRIBE's risk score
ranks them as the top 2 most-risky clips. So if a human only reviews
TRIBE's top 2 picks (11% of the work), they catch 100% of the
failures. That is what "recall at top-k = 100%" means.

### p value (0.0065)

Probability that we got recall@2 = 100% by random chance. Hypergeometric
test. p = 0.0065 means roughly 1 in 150 chance of fluke. Small p =
unlikely to be luck.

### Risk clips (2/18)

Number of known failure clips in the benchmark. Hard target count.

### Review budget (2)

How many clips TRIBE asks you to review by hand. 2 of 18 = 11.1% of
the data. The cheaper this is, the more useful TRIBE is.

### rho vs judges (-0.75)

Spearman rank correlation between TRIBE pressure and 4-judge ADQA
agreement, across all 18 clips.

**The negative sign is the whole point.** TRIBE pressure goes up when
a scene is visually dense and audio-only doesn't carry the content.
Judge agreement goes up when the 4 auto-graders order the AD tiers
the same way (pro AD > long > short > cross-video). The two move in
**opposite** directions:

- High TRIBE pressure → judges struggle to agree → audit fragile.
- Low TRIBE pressure → judges agree → audit reliable.

|rho| = 0.75 on n = 18 with p = 0.0003 means this is a strong,
statistically significant relationship. The minus is the story.

## Sidebar (per-clip)

### Risk score

A number from 0 to ~0.3. Higher = TRIBE thinks the auto-scorer will
be wobbly on this clip. Comes from `mean_standard_slot_score`. Green
under 0.08, amber 0.08 to 0.2, red over 0.2.

### #rank

TRIBE's ranked order, 1 = most risky out of 18. Clip 12 (volleyball,
Sports) is rank 1.

### Route badge (color)

TRIBE's recommendation for what kind of AD this clip needs. Computed
from the audio/visual gap structure, no AD text required.

- **EXTENDED AD** (red): heavy visual content the audio doesn't carry.
  The AD needs extra time slots or integrated narration.
- **STANDARD AD** (amber): normal pacing, fit AD into the natural
  speech gaps.
- **LOW PRESSURE** (green): audio already carries most of the story,
  AD just labels essentials.

### Speech chip

Density of speech in the clip's audio track.

- **silent** (red): under 30% of the clip has speech. AD must do
  most of the work.
- **talky** (green): over 80% speech. Audio already explains the scene.
- **mixed** (grey): in between.

This pairs with the route badge. Silent + extended-AD-needed = the
hardest combination.

### Quality risk text

One of: `clean`, `tier2/tier1 inversion risk`,
`professional AD barely leads`. Plain-English label for what kind of
audit failure mode TRIBE saw on this clip in the benchmark.

## Selected clip card

### Risk score, mean need, high-need sec %, speech density, tier margin

- **Risk score**: same as the sidebar, see above.
- **Mean need**: average TRIBE accessibility gap across the whole clip.
  Higher = more of the clip is visually demanding.
- **High-need sec %**: percentage of the clip's seconds where need
  exceeds the threshold. A clip can have low mean need but a short
  high-need burst, or vice versa.
- **Speech density**: 0 to 1, average over the clip.
- **Tier margin**: how cleanly the pro AD beat the long caption in
  the existing 4-judge benchmark. High = clear win, near zero or
  negative = the auto-judges barely separated tiers (audit failed).

### TRIBE route + Quality risk panel

Same labels as the sidebar, with the full long-form text shown.

### Professional AD candidate

The actual professional VideoA11y description for this clip, shown
for reference. Not a TRIBE output, just useful context.

## AD need over time (the timeline chart)

### What the curve shows

X-axis: seconds into the clip. Y-axis: TRIBE need score per 1.49s
fMRI TR. Higher curve = TRIBE thinks that moment is visually demanding
and the audio is not covering it.

The dashed horizontal line at 0.5 is the "high need" cutoff used
throughout the framework.

### The colored bands underneath

Each band is a 3-second coarse window with a recommendation:

- **EXTENDED / INTEGRATED** (red): visually dense, AD should run
  longer or be woven into the dialogue.
- **STANDARD SLOT** (amber): normal AD pacing fits here.
- **INSPECT EVENT** (purple/accent): a visual event spike that
  deserves human attention.
- **LOW NEED** (grey): audio carries it, no AD required.

### Why the 3 second windows

TRIBE's effective temporal resolution is roughly 3 seconds. Per-TR
labels would imply false sub-second precision. The coarse windows
match what the brain encoder actually resolves.

## Per-ROI accessibility gap (the bar chart)

### What this chart shows

For each cortical Region of Interest (ROI), how much TRIBE's predicted
brain response changes when you remove the video and keep only the
audio. Higher bar = that part of cortex loses a lot of signal when the
listener can't see the video.

The metric is **cosine gap = 1 - cos(P_AV, P_A)**:
- P_AV = predicted cortical activation given audio plus video.
- P_A  = predicted activation given audio alone.
- 0    = audio fully replaces the video for this brain region.
- 1    = audio captures none of what the video provided.

So a high bar means "this brain region needs the video, and AD has to
substitute for it."

### The ROIs (Glasser HCP-MMP1.0 parcellation)

- **Retrosplenial (scene context)**: builds the sense of "where am I
  in space" and links scenes to memory. Usually the biggest gap.
  When this is high, AD needs to describe the setting and spatial
  layout.
- **Scene PPA (parahippocampal place area)**: recognises places,
  rooms, environments. High gap = AD must name the location type.
- **Early visual V1**: low-level edges, contrast, motion onsets.
  Always nonzero but usually moderate.
- **Higher visual V2/V3/V4**: shape, color, texture.
- **Motion MT**: motion and trajectory. Spikes during action.
- **Face FFC**: faces. Spikes when characters are on screen.
- **Body EBA**: bodies, poses, gestures.
- **Lateral object**: object recognition.
- **Language control**: semantic and language regions.
- **Auditory control**: should be near zero (audio is present in both
  conditions, so removing video shouldn't move auditory cortex much).
  Acts as a sanity check.

### Why only clips 00 and 01 have these bars

The full per-ROI cortical fingerprint requires the complete TRIBE
tensor (one prediction per cortical vertex per TR). We only saved
that for 2 demo clips. The other 16 clips show the same metrics
aggregated (mean need, risk score, etc) but not the per-ROI breakdown.

The fallback message in the UI says this honestly.

## The "P_AV / P_A / |gap|" label on the brain map

P_AV = predicted brain response, audio + video.
P_A  = predicted brain response, audio only.
|gap| = absolute difference between them, mapped to cortex.

The brain map image is a cortical surface render showing where the
gap is geographically located. Red on the map = high accessibility
gap = the listener loses a lot of cortical signal when they can't
see the video.

## TRIBE pressure (mentioned in the live demo)

A single summary number per clip: roughly `mean_need + max_need`.
Used in the Gradio cached benchmark panel.

## What none of this measures

- **Whether the AD is correct.** That is CLIP + ADQA's job. TRIBE
  does not read AD text in the failure-forecast path.
- **Whether the AD is well written.** Style, fluency, length all
  belong to the live grader, not the brain encoder.
- **Real fMRI from a real human.** TRIBE is a learned encoder
  pre-trained on fMRI data; what it produces here is a model
  prediction of cortical activity, not real measurements.

## One sentence each, for the poster

- **Risk score**: how likely the auto-audit is to be wrong here.
- **Route badge**: what kind of AD this clip needs (extended,
  standard, low).
- **Speech chip**: how much the audio track helps.
- **Need timeline**: when in the clip AD is most load-bearing.
- **Per-ROI gap**: which brain regions lose signal without the video.
- **rho = -0.75**: TRIBE-derived visual demand predicts judge
  disagreement, from video and audio alone.

## Source files

- `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv`
- `output/scenetwin_timing_20clip/tribe_native/tribe_native_correlations.csv`
- `output/scenetwin_timing_20clip/tribe_only_per_roi.csv`
- `output/scenetwin_timing_20clip/need/neural_description_need_curve.csv`
- `output/scenetwin_timing_20clip/need/coarse_need_windows.csv`
