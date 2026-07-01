---
title: Colab TRIBE NCR Full Run
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - tools/colab_tribe_setup.py
  - tools/colab_tribe_smoke.py
  - tools/colab_tribe_ncr_runner.py
  - cursor/pipeline/build_ncr_metadata.py
  - cursor/pipeline/neural_contrastive_retrieval.py
  - cursor/research/tribe_ncr_hidden_patterns.py
  - cursor/research/output/ncr_similarity.csv
  - cursor/research/output/ncr_summary.json
  - output/reports/tribe-ncr-results.md
  - output/reports/tribe-ncr-hidden-patterns.md
---

# Colab TRIBE NCR Full Run

## What ran

- Tried A100 and H100 first; Colab returned Service Unavailable for both.
- Used **NVIDIA L4** (not T4).
- Fixed Colab TRIBE import/load by pinning a coherent Python 3.12 stack and restarting the kernel:
  - `numpy==2.2.6`
  - `scipy==1.15.3`
  - `pandas==2.2.3`
  - `scikit-learn==1.6.1`
  - `torch==2.6.0`
  - `torchvision==0.21.0`
- Verified `TribeModel.from_pretrained("facebook/tribev2")` on L4.
- Rebuilt NCR as a self-contained Colab runner from local metadata because the original notebook-only cell depended on missing `/content/scenetwin` state and missing local external clip MP4s.

## Important method deviation

The full TRIBE text extractor attempted to download gated `meta-llama/Llama-3.2-3B`. Rather than persist or expose the user-provided Hugging Face token, the completed run used the robust **TTS-audio-only NCR variant**:

- candidate AD text -> gTTS audio -> TRIBE audio extractor;
- reference clips -> video+audio events with text stages disabled;
- no gated Llama text extractor.

This still tests whether hearing an AD points toward the correct clip's audiovisual brain response, but it is **not** the full text-extractor NCR originally imagined.

## Artifacts

Full 60-clip artifacts:

- `cursor/research/output/ncr_similarity.csv` — recovered full 60-clip similarity CSV, 14,400 rows.
- `cursor/research/output/ncr_full60/ncr_similarity.csv` — same recovered full CSV.
- `cursor/research/output/ncr_full60/colab_exec_full60.log` — full Colab execution log; includes gzip+base64 recovery block for the CSV.
- `cursor/research/output/ncr_full60/manifest.sha256` — hashes for key recovered/analyzed artifacts.
- `cursor/research/output/ncr_run_summary.json` and `cursor/research/output/ncr_full60/ncr_run_summary.json` — run summary reconstructed from log.
- `cursor/research/output/ncr_query_metrics.csv` — local per-query rank/margin metrics.
- `cursor/research/output/ncr_summary.json` — local aggregate NCR metrics.
- `output/reports/tribe-ncr-results.md` — headline NCR result.
- `output/reports/tribe-ncr-hidden-patterns.md` — post-hoc pattern/guardrail analysis.

Pilot-only artifact:

- `cursor/research/output/ncr_pilot5/ncr_vectors.npz` — pilot vector archive only. The full remote `ncr_vectors.npz` was generated but not recovered because the Colab session disappeared immediately after the long run. The full CSV was recovered via stdout gzip+base64, which is sufficient for the rank analysis.

## Headline result

NCR does **not** work as a revolutionary AD-dependent ranker in this TTS-audio-only form.

Full 60-clip rank-percentile means:

| Tier | mean correct-rank percentile |
|---|---:|
| tier0_cross | 0.495 |
| tier1_vatex_short | 0.488 |
| tier2_vatex_long | 0.516 |
| tier3_va11y | 0.518 |

Aggregate correlations:

- Spearman(tier, correct-rank percentile), 4-tier: **0.035**
- Spearman(tier, cosine margin), 4-tier: **0.026**
- Spearman(tier, correct-rank percentile), corrected 3-tier: **0.031**
- Spearman(word count, rank pct): **-0.008**
- Spearman(tier, length-residual rank pct): **0.035**

## Small positive signals worth keeping as a mechanism hint

- Professional AD beats short crowd caption on rank percentile in **36/57 non-tie clips**, one-sided sign p = **0.0314**.
- Wrong-content AD retrieves its source clip more often than its target: source rank > target rank on **37/60**, one-sided sign p = **0.0462**.
- The effect is weak and hubbed: top-1 self retrieval is only 0-1/60 per tier, and one reference clip attracted 158/240 top-1 assignments.

## Paper-safe interpretation

Use NCR as an honest negative/guardrail plus a small source-specificity pilot. Do **not** claim it solves brain-grounded AD scoring. The stronger SceneTwin story remains:

1. CLIP+ADQA is the scorer.
2. Safety gates catch wrong-content/hallucination cases.
3. TRIBE is a clip/window-level blind-spot router and review triage side-car.
4. Future AD-dependent TRIBE scoring needs authenticated text-extractor access and a pre-registered text-vs-audio ablation.

## Colab cleanup

Stopped the L4 session after the run:

```bash
colab sessions
colab stop -s scenetwin-l4
colab sessions
# No active sessions found on server.
```
