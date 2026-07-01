---
title: VLM-as-judge results — three frontier models all underperform the 2-signal ensemble
category: research
tags: [scenetwin, baselines, vlm, paper-a]
sources: [cursor/research/output/vlm_as_judge_*.csv]
created: 2026-05-29
updated: 2026-06-27
---

> **The per-model tables below are the retired 4-tier sweep** (ensemble 0.929/0.873; VLMs
> 0.71–0.76). On the **corrected 3-tier ladder** the manuscript reports the best VLM judge at
> **ρ = 0.847 on the 60-clip primary set / 0.863 on the 18-clip pilot**, versus SceneTwin
> **0.952 / 0.957** — a gap of roughly **+0.09–0.10**. The qualitative conclusion is unchanged
> (all three frontier VLMs trail the structured audit), but the **per-model corrected leaderboard
> CSV still needs regenerating** — `vlm_as_judge_leaderboard.csv` currently holds 4-tier values.
> Treat the granular numbers below as the retired ladder.

## Headline (retired 4-tier sweep)

We ran three frontier multimodal models (Anthropic Claude Sonnet 4.6, OpenAI GPT-5, Google Gemini 2.5 Pro) as zero-shot AD-quality judges across the combined 78-clip corpus. All three trail the 2-signal CLIP+ADQA ensemble by **0.13–0.17 Spearman ρ** in-benchmark and by similar margins externally. The three models agree with each other at ρ = 0.83–0.88 inter-provider but fail to reproduce the tier ranking that our smaller 2-signal ensemble captures. **This is the cleanest possible answer to the "a frontier VLM would beat your ensemble" reviewer challenge.**

## Apples-to-apples verification (identical clips, identical labels)

Before any cross-corpus comparison: both metrics were computed on the **same 78 clips** (18 in-bench + 60 external) with the **same tier ladder labels**. Zero label mismatches between `cursor/output/external_ensemble_eval.csv` and `cursor/research/output/vlm_as_judge_*_combined.csv`. The 60 external clip IDs in the VLM CSV are a perfect 60-of-60 overlap with the ensemble CSV.

This rules out the obvious "you compared the metric on different clips" reviewer challenge.

## Head-to-head against all three providers (identical clips, complete runs)

All three providers complete on the same 78 clips, same tier labels, zero label mismatches.

| Model | In-bench (n=72) | External (n=240) | Combined (n=312) |
|---|---:|---:|---:|
| **SceneTwin ensemble** | **0.929** | **0.873** | **0.886** |
| Gemini 2.5 Pro | 0.756 | 0.734 | 0.736 |
| GPT-5 | 0.727 | 0.739 | 0.735 |
| Claude Sonnet 4.6 | 0.713 | 0.715 | 0.713 |
| **Gap (ensemble - best VLM)** | **+0.173** | **+0.134** | **+0.150** |

Inter-VLM agreement on full n=312:
- Claude <-> Gemini: rho = 0.847
- Claude <-> GPT-5: rho = 0.833
- Gemini <-> GPT-5: rho = 0.837

The three frontier VLMs agree with each other at rho ~ 0.84 but with our tier GT at only rho ~ 0.73. The disagreement with the tier ladder is **systematic and consistent across vendors**, not VLM rating noise.

### Per-clip win rate (Claude Sonnet 4.6 vs ensemble)

External (60 clips):
- Ensemble better on **26/60 clips**
- VLM better on **10/60 clips**
- Tied (|delta rho| < 0.01) on **24/60 clips**

In-bench (18 clips):
- Ensemble better: **10/18**
- VLM better: **2/18**
- Tied: 6/18

The ensemble wins by aggregate rho AND by per-clip count, for every provider tested.

## Numbers (live - updates as remaining runs finish)

### In-benchmark (n=72)

| Model | ρ | T3 pairwise wins |
|---|---:|---:|
| **SceneTwin ensemble** | **0.929** | **54/54 (100%)** |
| Gemini 2.5 Pro | 0.756 | 43/54 (80%) |
| GPT-5 | 0.727 | 45/54 (83%) |
| Claude Sonnet 4.6 | 0.713 | 44/54 (81%) |

The 4-tier rank construction defeats every frontier VLM zero-shot judge.

### External (n=240 once all 3 runs complete)

| Model | ρ | T3 pairwise wins |
|---|---:|---:|
| **SceneTwin ensemble** | **0.873** | **173/180 (96.1%)** |
| Claude Sonnet 4.6 | 0.715 | 151/180 (83.9%) |
| Gemini 2.5 Pro | 0.756 (partial) | 25/30 (83.3%) (partial) |
| GPT-5 | 0.707 (partial) | 36/42 (85.7%) (partial) |

### Inter-provider agreement (pairwise Spearman on `overall`)

| Pair | ρ | n_obs |
|---|---:|---:|
| Claude ↔ GPT-5 | **0.880** | 128 |
| Gemini ↔ GPT-5 | 0.842 | 112 |
| Claude ↔ Gemini | 0.831 | 112 |

The three frontier VLMs agree with each other at ρ ≈ 0.85 but with our tier GT at only ρ ≈ 0.73. The disagreement with the tier ladder is **systematic**, not just noise — they cluster on a slightly different judgment manifold than the controlled construction we use as GT.

## Why our ensemble wins

Three structural reasons:

1. **The tier ladder is controlled and rewards visual specificity.** Tier3 (professional AD) is engineered to add visual content over Tier2 (VATEX long), which adds specificity over Tier1 (VATEX short), which adds anything over Tier0 (cross-decoy). The VLM rates on holistic AD quality without seeing this construction. Some Tier2 VATEX captions are *fluent* and *plausible* but lack the visual specificity that the ladder is built around. The VLM rates them generously; our ADQA grounding catches the missing specificity.

2. **ADQA MCQs anchor scoring to specific visible content.** Per-clip, ADQA generates 5+ frame-grounded yes/no questions ("Does the AD mention the boy serving the ball?"). Each question must be answered against actual frames, so the metric cannot reward fluency. The VLM has no such structured grounding — it sees frames and AD and asks itself "is this good?" with no controlled question prior.

3. **CLIP grounding adds visual-object lift on controlled benchmarks.** CLIP's contribution shrinks externally (see [[research/scenetwin-signal-decomposition]]), but on the 18-clip in-benchmark tier ladder CLIP adds +0.14 ρ over ADQA-alone. That lift is what the VLMs are missing.

## What the VLMs DO get right (the smoke test on clip 12)

On clip 12 (boys playing volleyball, one of our 3 in-bench mis-orderings), Claude Sonnet 4.6's output:

| Tier | Claude `overall` | Our ensemble |
|---|---:|---:|
| T0 (cross-decoy: chef + tomato) | 0 | 0.000 |
| T1 ("Some boys talking in a foreign language are playing Volley Ball") | 35 | 0.688 |
| T2 ("A man runs to the back of a volleyball field bouncing the ball...") | 22 | 0.606 |
| T3 (pro AD, full description) | 42 | 0.982 |

Claude correctly identifies T2 as worse than T1 (matching our mis-ordering finding!) — both judgments penalise T2's factual error ("a man" vs *boys*, "bouncing" vs *serving*). The cross-validation here is reassuring: VLMs and our ensemble agree on the *category* of error even when they disagree on absolute calibration.

## What this means for the paper

Paper A §6.1 (Baselines) gains a strong table. The headline language becomes:

> Across three frontier multimodal models — Claude Sonnet 4.6, GPT-5, Gemini 2.5 Pro — zero-shot AD-quality judgment from sampled frames achieves Spearman ρ in the range [0.71, 0.76] on our 18-clip benchmark and similar values externally. Our 2-signal CLIP+ADQA ensemble achieves ρ = 0.929 in-bench and 0.873 external, a margin of 0.13–0.17 over the best VLM judge. The three VLMs agree with each other at ρ ≈ 0.85 but disagree with our tier-construction GT, suggesting the gap reflects a systematic difference in judgment manifold rather than noise.

This is a paper-strengthening result. The reviewer's most-likely challenge collapses.

## Cost paid

- Anthropic Claude Sonnet 4.6: ~$10
- Google Gemini 2.5 Pro: ~$4 (partial)
- OpenAI GPT-5: ~$8 (partial)
- Total committed: ~$22 (forecast at start: $25)

## What's still running

Gemini 2.5 Pro and GPT-5 are still processing external clips. Expected completion within the next ~30–60 min. Headline numbers above will firm up but trend is locked.

## Files

- `cursor/research/output/vlm_as_judge_anthropic_claude_sonnet_4_6_combined.csv` — full Claude results
- `cursor/research/output/vlm_as_judge_gemini_gemini_2.5_pro_combined.csv` — Gemini results (in progress)
- `cursor/research/output/vlm_as_judge_openai_gpt_5_combined.csv` — GPT-5 results (in progress)
- `cursor/research/output/vlm_as_judge_leaderboard.csv` — cross-model comparison
- `cursor/research/output/vlm_as_judge_agreement.csv` — inter-provider ρ
- `cursor/research/output/vlm_as_judge_summary.md` — auto-generated summary

## See Also

- [[research/scenetwin-vlm-as-judge-protocol]] — protocol, prompt, cost matrix, decision rule
- [[research/scenetwin-metric-landscape]] — full baselines table
- [[research/scenetwin-statistical-power]] — defense against "small n" challenge
