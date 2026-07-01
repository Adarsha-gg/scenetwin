---
title: Neural Contrastive Retrieval (NCR) — Design + Runbook (results pending Colab)
category: research
tags: [SceneTwin, TRIBE, retrieval, reference-free, pending]
updated: 2026-06-07
---

# Neural Contrastive Retrieval (NCR)

A genuinely new, AD-dependent, brain-grounded AD score designed to survive the two
confounds that killed every prior neural metric. **Full 60-clip L4 Colab run completed
2026-06-23 as a TTS-audio-only variant.** It is an honest near-null as a ranker,
with only weak source-specificity/pairwise hints; do not headline it as a working
brain-grounded AD score.

## The idea

Feed each candidate AD's TEXT through TRIBE → the predicted brain response to *hearing*
the AD. Mean-pool to a vector `q`. For every clip's VIDEO brain response
`v_j = mean(P_AV_j)`, ask: among all 60 clips, does `q` retrieve the **right** one?

- **Score** = rank-percentile of the correct clip (1 = top, 0.5 = chance) and the
  cosine margin (self minus mean distractor).
- **Q1 quality ordering:** a better AD should make its clip more retrievable →
  rank-percentile rises `tier0 < tier1 < tier3`.
- **Q2 wrong-content control (the test neural closure FAILED):** `tier0_cross` is an AD
  copied from a *different* clip. Its `q` should retrieve its **source** clip, not this
  one → near chance. `tier3` should sit well above chance.

## Why it dodges the graveyard

Neural closure / Description Gain / MVRR all died because (a) **verbosity** inflated the
TRIBE perturbation and (b) AD **language injection** moved the response away from the
silent-video `P_AV`. NCR neutralizes both:

- **Cosine + rank are magnitude-invariant** → a uniformly wordier AD doesn't win; only
  *relative* retrieval matters.
- **Language injection becomes the signal, not the noise:** every AD injects language
  equally, so the only thing that retrieves clip *i* is clip-*i*-specific visual content.
  A vague/wrong AD injects language but points nowhere — which is exactly the
  wrong-content discrimination the absolute-distance metrics lacked.

NCR is also **AD-dependent** (varies per candidate), unlike the per-clip
`accessibility_gap` that mathematically cannot enter within-clip ρ.

## How it was run

The original notebook cell `cursor/research/tribe_ncr_dump_cell.py` assumed missing
Colab globals and missing external clip MP4s, so the actual run used a self-contained
runner:

1. Build metadata locally: `python cursor/pipeline/build_ncr_metadata.py`.
2. Colab L4 setup: `tools/colab_tribe_setup.py`, restart kernel, then
   `tools/colab_tribe_smoke.py`.
3. Upload `cursor/research/output/ncr_external60_metadata.json` and run
   `tools/colab_tribe_ncr_runner.py`.
4. Analyze locally: `python cursor/pipeline/neural_contrastive_retrieval.py` and
   `python cursor/research/tribe_ncr_hidden_patterns.py`.

Important deviation: the full TRIBE text extractor requires gated
`meta-llama/Llama-3.2-3B`, so the completed run used **TTS-audio AD queries** and
video+audio references with text stages disabled.

## Result

Full 60-clip output: `cursor/research/output/ncr_similarity.csv` (14,400 rows).
Reports:

- `output/reports/colab-tribe-ncr-full-run.md`
- `output/reports/tribe-ncr-results.md`
- `output/reports/tribe-ncr-hidden-patterns.md`

Rank-percentile means stayed near chance:

| Tier | mean correct-rank percentile |
|---|---:|
| tier0_cross | 0.495 |
| tier1_vatex_short | 0.488 |
| tier2_vatex_long | 0.516 |
| tier3_va11y | 0.518 |

Aggregate signal:

- Spearman(tier, correct-rank percentile), 4-tier: `0.035`
- Spearman(tier, cosine margin), 4-tier: `0.026`
- Spearman(tier, correct-rank percentile), corrected 3-tier: `0.031`
- Spearman(word count, rank pct): `-0.008`
- Spearman(tier, length-residual rank pct): `0.035`

Small mechanism hints:

- T3 > short caption on 36/57 non-tie clips, one-sided sign p=`0.0314`.
- Wrong-content source rank > target rank on 37/60, one-sided sign p=`0.0462`.

Top-1 retrieval is heavily hubbed (one reference attracted 158/240 top-1 assignments),
so this is **not** a deployable scorer.

## Risk (stated up front)

TRIBE sees AD text via TTS→re-transcription (out-of-distribution vs natural movie
audio), and mean-pooling discards temporal structure. 60-way retrieval in 20484-dim
noisy space may land at chance. This is a real swing with real downside — but it is
*falsifiable* and structurally distinct from the dead branches.

## See Also

- [[findings/tribe-clip-level-triage]]
- [[research/scenetwin-description-gain-smoke-test]]
