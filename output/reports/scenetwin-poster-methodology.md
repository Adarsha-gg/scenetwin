---
title: SceneTwin Methodology — Poster Copy
created: 2026-05-11
---

# Methodology — three drop-in versions

Pick whichever length fits your band. Long version for a dedicated
"Methods" band, medium for a column, short for a callout box.

---

## Long version  (~400 words)

**Heading:** *How SceneTwin scores an audio description*

SceneTwin takes one short video clip (10 to 20 seconds) and one candidate
audio description text. Two reference-free signals run in parallel; their
outputs are normalized and averaged. A third signal, derived from a
published fMRI brain encoder, runs as a side-car to forecast when the audit
score is likely to be fragile.

**Signal 1: CLIP visual grounding.** Eight evenly spaced frames are sampled
from the clip. Each frame is embedded with the CLIP-L/14 image encoder. The
candidate AD text is embedded with the CLIP-L/14 text encoder. Cosine
similarity is computed between each frame and the text, then averaged
across frames. This signal catches descriptions of the wrong scene or
hallucinated visual content.

**Signal 2: Frame-grounded ADQA.** The same eight frames are sent to a
vision language model (GPT-4o), which writes three comprehension questions
whose answers must be visually evident in the frames. The model does not
see the candidate description while writing the questions. A separate
language model (Claude haiku 4.5) then reads each candidate description
blind: no frames, no tier labels, no ground truth, no other candidates
visible. Candidates are presented as shuffled A, B, C, D identifiers to
remove any ordering bias. The grader answers each question yes or no and
quotes the supporting evidence from the description. The signal score is
the fraction of yes answers.

**Ensemble.** Each signal is min-max normalized within each clip (zero
equals the worst tier of that clip, one equals the best). The final audit
score is the simple mean of the two normalized signals. Weights are fixed
at fifty fifty; no tuning is performed on held-out data.

**Validation.** Eighteen clips, four candidate descriptions per clip, four
quality tiers (professional audio description, VATEX long, VATEX short,
cross-category wrong-scene control). Ground truth is the tier rank zero
through three. The primary metric is Spearman correlation between ensemble
score and ground truth, with a bootstrap 95 percent confidence interval
over two thousand resamples and a within-clip permutation null over two
thousand permutations.

**Side-car risk forecast.** For each clip the TRIBE v2 fMRI encoder
predicts brain activation under two viewing conditions: full audio and
video, and audio only. The pointwise absolute difference is the
accessibility gap on the fsaverage5 cortical surface. An aggregate
gap-derived feature is used as a risk score for that clip. Higher risk
means the audit score for that clip is more likely to invert tier
ordering.

---

## Medium version  (~200 words)

**Heading:** *Method*

SceneTwin takes a video clip and a candidate audio description. Two
reference-free signals run in parallel.

**CLIP visual grounding.** Eight frames per clip are embedded with
CLIP-L/14. The candidate description is embedded with the same model.
Cosine similarity between each frame and the text is averaged across
frames. Catches wrong-scene or hallucinated descriptions.

**Frame-grounded ADQA.** A vision language model writes three
comprehension questions from the frames. A separate language model grades
each candidate description blind: no frames, no labels, no other
candidates visible. Candidates are shuffled as A, B, C, D to prevent
ranking bias. Score is the fraction of questions answered correctly.

**Ensemble.** Each signal is clip-wise normalized. The final score is
the equal-weight mean. No tuning.

**Validation.** 18 clips, 4 quality tiers per clip. Primary metric:
Spearman rho between ensemble and ground-truth tier. Bootstrap 95 percent
confidence interval over 2000 resamples. Within-clip permutation null
over 2000 permutations.

**Risk forecast (side-car).** TRIBE v2 fMRI encoder predicts brain
activation under audiovisual and audio-only conditions. The gap between
them feeds a per-clip risk score that flags fragile evaluations.

---

## Short version  (~80 words)

**Heading:** *Method*

One video clip plus one candidate description. Two signals run in
parallel: CLIP cosine similarity between sampled frames and the
description, and frame-grounded ADQA where a vision language model writes
questions from the frames and a separate language model grades the
description blind. Each signal is clip-wise normalized and averaged 50 / 50.
A side-car TRIBE fMRI encoder flags clips where the audit may be fragile.
Validated on 18 clips × 4 quality tiers.

---

## Step-by-step  (numbered list, for a visual flow band)

1. **Input.** Take one video clip (10 to 20 seconds) and one candidate
   audio description.
2. **Frame sampling.** Extract eight evenly spaced frames.
3. **CLIP signal.** Embed frames and description with CLIP-L/14. Compute
   per-frame cosine similarity. Average across frames.
4. **ADQA signal — questions.** Send frames to a vision language model
   (GPT-4o). Generate three comprehension questions per clip.
5. **ADQA signal — grading.** Send the question set and the candidate
   description (without frames) to a separate language model (Claude haiku
   4.5). Grade blind. Score is the fraction of yes answers.
6. **Ensemble.** Clip-wise normalize both signals. Average with 50 / 50
   weights.
7. **Risk forecast.** Compute TRIBE accessibility gap on the same clip.
   Aggregate to a per-clip risk score. Flag fragile evaluations.
8. **Audit score returned.** One number per (clip, candidate description)
   pair, with an optional risk flag.

---

## Notes for the speaker

- **Why fixed 50 / 50?** Untuned ensembles are more defensible at small
  n. Weight tuning at n = 18 risks overfitting; the unweighted mean
  already exceeds either signal alone by a wide CI margin.
- **Why frame-grounded questions, not reference text?** Two skilled
  describers will write very different but equally valid scripts. There
  is no single "correct" AD to compare against. Grounding the questions
  to the frames removes the reference dependency.
- **Why a separate grader model?** Prevents the questioner from being
  biased by what answers it expects. The grader sees only what the
  description says.
- **Why blind candidates?** Tier labels, ground truth, and other
  candidates would all leak. Anonymizing as A, B, C, D and shuffling per
  clip removes the cues.
