---
title: VLM-as-judge baseline — protocol, cost matrix, decision rule
category: research
tags: [scenetwin, vlm, baseline, paper-a, protocol]
sources: [cursor/research/vlm_as_judge_runner.py]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

The paper needs a frontier VLM-as-judge baseline to preempt the obvious reviewer challenge "does a single VLM rating tie or beat the 2-signal ensemble?" The protocol is: per (clip, tier), send 6 sampled frames + AD text to a frontier multimodal model, ask for a 0-100 quality rating across 3 axes plus an overall score, parse, compare to our ensemble at Spearman rho. Total cost across the full 78-clip corpus ranges **$1-$50 depending on model**. Runner is at `cursor/research/vlm_as_judge_runner.py` — supports Anthropic, OpenAI, and Google Gemini.

## Why we need this

The paper claims a 2-signal CLIP+ADQA ensemble beats published reference-free metrics. A reviewer's most likely challenge: **"a frontier VLM rating the AD against frames would dominate this — why is your approach necessary?"** Without measurement we cannot defend.

Three possible outcomes:

| Outcome | Paper response |
|---|---|
| VLM rho < ensemble | Strongest result: we beat a frontier VLM with a parsimonious 2-signal ensemble at trivial cost (CLIP + ADQA inference) |
| VLM rho ≈ ensemble (within 0.02) | Interpretability + cost arguments do the work; VLM is opaque/expensive, our ensemble is auditable and cheap |
| VLM rho > ensemble | Reframe paper as "interpretable proxy for VLM judgment" and lean harder on TRIBE calibration claim. Still a paper, harder to position |

We need the number regardless. Better to learn now than at submission.

## Protocol

### Inputs per (clip, tier) call

- **6 frames** sampled evenly across the clip duration (using `ffmpeg -ss <t> -frames:v 1`, scaled to width 1024, JPEG q=5)
- **AD text** for that tier
- System prompt anchoring the rater to AD quality for blind/low-vision viewers, explicitly de-rewarding fluency and length

### Output expected (JSON)

```
{"visual_fidelity": <0-100>,
 "completeness": <0-100>,
 "informativeness": <0-100>,
 "overall": <0-100>}
```

Score parsing accepts any JSON block in the reply. The `overall` field is the headline metric we correlate with tier GT.

### Evaluation

- Compute Spearman rho between `overall` and tier GT (0..3) across all observations.
- Per-corpus and combined: in-bench (n=72), external (n=240), combined (n=312).
- Pairwise T3 wins per clip.
- Per-clip CLIP lift comparison (does VLM judgment correlate with ensemble, or is it an orthogonal signal we could blend?).

### Calls required

- In-bench: 18 × 4 = **72 calls**
- External: 60 × 4 = **240 calls**
- Combined: **312 calls**

## Cost matrix (full 78-clip corpus, 312 calls)

| Model | Input USD | Output USD | **Total USD** |
|---|---:|---:|---:|
| Claude Opus 4.7         | 47.27 | 2.34 | **49.61** |
| GPT-5                   |  7.88 | 0.31 |  **8.19** |
| GPT-4o                  |  7.88 | 0.31 |  **8.19** |
| Claude Sonnet 4.6       |  9.45 | 0.47 |  **9.92** |
| Gemini 2.5 Pro          |  3.94 | 0.16 |  **4.09** |
| Claude Haiku 4.5        |  2.52 | 0.12 |  **2.65** |
| Gemini 2.5 Flash        |  0.94 | 0.08 |  **1.02** |

Per-call breakdown: ~10,100 input tokens (6 images × ~1600 tokens + 500 prompt tokens) + ~100 output tokens.

## Smoke test cost (3 clips × 4 tiers = 12 calls)

| Model | USD |
|---|---:|
| Claude Opus 4.7         | 1.91 |
| Claude Sonnet 4.6       | 0.38 |
| Claude Haiku 4.5        | 0.10 |
| Gemini 2.5 Flash        | 0.04 |

Recommended workflow: run smoke test on chosen model first, manually verify the JSON parsing and score sensibility, then commit to the full run.

## Recommended runs for the paper

Three tiers of defensibility:

### Minimum (single frontier model, ~$10)
- Claude Sonnet 4.6 OR GPT-5 OR Gemini 2.5 Pro
- One column in the baselines table

### Strong (frontier + cheap, ~$12)
- Claude Sonnet 4.6 + Claude Haiku 4.5 (same family, shows VLM scale)
- Or: Gemini 2.5 Pro + Gemini 2.5 Flash
- Two columns showing whether scale matters

### Comprehensive (multi-vendor, ~$25)
- Claude Sonnet 4.6 + GPT-5 + Gemini 2.5 Pro
- Three columns: shows result is not vendor-specific

The "Strong" tier is the sweet spot for a paper baseline.

## What we DON'T do (and why)

- **No chain-of-thought reasoning**. The rater is instructed to output strictly JSON. CoT would add cost and variance without changing the headline.
- **No multi-shot prompting**. We use zero-shot rating per (clip, tier). Multi-shot would leak our tier ordering as exemplars.
- **No video input (raw mp4)**. Anthropic and OpenAI do not yet take video; Gemini takes video but we standardize on frame sampling for cross-vendor comparison.

## Runner

`cursor/research/vlm_as_judge_runner.py`. Supports:

```bash
# Cost-estimate dry run (no API calls)
python3 cursor/research/vlm_as_judge_runner.py --dry-run --corpus combined

# Smoke test (2 clips, requires API key in env)
ANTHROPIC_API_KEY=sk-... python3 cursor/research/vlm_as_judge_runner.py \
    --provider anthropic --model claude-sonnet-4-6 \
    --corpus inbench --limit 2

# Full run
ANTHROPIC_API_KEY=sk-... python3 cursor/research/vlm_as_judge_runner.py \
    --provider anthropic --model claude-sonnet-4-6 \
    --corpus combined
```

Outputs:
- Per-call CSV at `cursor/research/output/vlm_as_judge_<provider>_<model>_<corpus>.csv`
- Headline Spearman rho printed at end
- On failure (no JSON parsed) the raw model text is preserved in the `raw_text` column for retry

## Decision rule for paper writing

After the full run, three thresholds:

1. **VLM_overall rho < 0.85**: VLM is *worse* than our ensemble at 0.873 external. Paper headline: "even a frontier VLM cannot match our 2-signal interpretable baseline."

2. **0.85 ≤ VLM_overall rho < 0.88**: VLM is within bootstrap interval. Paper claim: "frontier VLM and our ensemble are statistically tied; ours is auditable and ~5 orders of magnitude cheaper per inference."

3. **VLM_overall rho ≥ 0.88**: VLM beats our ensemble. Paper reframe: "our ensemble approximates frontier VLM judgment at trivial cost and provides per-component interpretability."

All three outcomes still ship a paper. The only bad outcome is *not measuring* and being caught at review.

## See Also

- [[research/scenetwin-paper-outline]] §6.1
- [[research/scenetwin-metric-landscape]] - baselines table
- `cursor/research/vlm_as_judge_runner.py` - the runner

## Sources

- 2026 model pricing (advisory; verify before final run)
- `cursor/research/vlm_as_judge_runner.py`
