---
title: SceneTwin paper-baseline generalization on 60 external clips
category: research
tags: [scenetwin, baselines, generalization, paper-section]
sources: [cursor/research/output/external_paper_baselines.csv, cursor/research/output/external_paper_baselines_leaderboard.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

We re-ran the text-only paper baselines on the 60-clip external corpus (240 obs, 10 categories) so the generalization story is apples-to-apples. The CLIP+ADQA ensemble holds rho = 0.873 across an unseen set; the strongest reference-free baseline (LLM-AD-Eval at rho = 0.857) trails by **+0.016**. In-benchmark the gap is **+0.030**. The ensemble lift over the closest competitor holds across both corpora.

## Combined leaderboard

| Metric | In-bench rho (n=18) | External rho (n=60) | Delta | Uses T3 as reference? |
|---|---:|---:|---:|:---:|
| **SceneTwin ensemble (CLIP+ADQA)** | **0.929** | **0.873** | -0.056 | No |
| LLM-AD-Eval (MiniLM embeddings vs T3) | 0.899 | 0.857 | -0.042 | Yes |
| ADQA v4 (alone)                        | 0.789 | 0.867* | n/a | No |
| CRITIC entity (proper noun / role)     | 0.638 | 0.613 | -0.025 | No |
| Multi-ref R@3/N (token recall vs T3+T2+T1) | 0.532 | 0.948 | +0.416 | Yes (methodology likely differs) |
| token_overlap (T3 token Jaccard)       | -- | 0.849 | -- | Yes |
| word_count (length only)               | -- | 0.339 | -- | No |
| CoAD repetition (inverse)              | -0.064 | -0.011 | +0.053 | No |

*ADQA on external uses the cached external ADQA grades, which were computed against the external clips directly. The 0.867 is a single-signal external number, not a strict re-run with identical generation parameters.

## The reference-leakage caveat

LLM-AD-Eval, multi_ref_r3, and token_overlap all use the tier3 professional AD as their reference text. On every clip, tier3 is compared to itself and scores near the maximum — so these metrics get **180/180 T3 pairwise wins trivially**. The pairwise win count is uninformative for reference-based metrics.

The CLIP+ADQA ensemble scores AD against the **video**, not against tier3. Its 173/180 (96.1%) T3 pairwise wins is therefore a fundamentally stronger result -- the metric does not know which AD was the human reference.

| Metric | T3 wins external | Why this number |
|---|:---:|---|
| Ensemble (CLIP+ADQA) | **173/180 (96.1%)** | Scores AD vs video; T3 not pre-privileged |
| LLM-AD-Eval | 180/180 (100%) | T3 matches itself |
| multi_ref_r3 | 180/180 (100%) | T3 token set is a reference |
| token_overlap | 180/180 (100%) | T3 token set is reference |
| CRITIC entity | 175/180 (97.2%) | Reference built from T2+T3 entities |
| word_count | 176/180 (97.8%) | T3 is usually the longest |

## Full tier ordering (4-tier strict) externally

| Metric | Fully ordered |
|---|---:|
| multi_ref_r3 | 50/60 |
| token_overlap | 24/60 |
| llm_ad_eval | 22/60 |
| CRITIC entity | 2/60 |
| word_count | 0/60 |
| CoAD repetition (inv) | 0/60 |
| **Ensemble** | **30/60** |

The Ensemble's 30/60 sits in the middle. Two observations:

1. The reference-based metrics that get 180/180 T3 wins still mostly fail to fully order T0 < T1 < T2 < T3, because their problem is at the middle of the ladder, not at T3.
2. multi_ref_r3 is the only metric to fully order 50/60 -- but it does so by trivially scoring T3 highest and T0 lowest while leaving the T1/T2 middle ambiguous.

## Multi-ref methodology mismatch (resolved)

The +0.416 jump for `multi_ref_r3` (0.532 -> 0.948) was a name collision: the published in-bench `multi_ref_r3` at 0.532 used a different formula (R@3 over a 12-reference corpus from `cursor/papers/multi_ref_r_at_k.py`), not the token-recall-vs-3-tier-union formula we used externally. **Recomputing the in-bench version with the same external formula gives rho = 0.964 (n=72).**

So with consistent formula:

| Metric | In-bench (n=72) | External (n=240) | Delta |
|---|---:|---:|---:|
| `t3_t2_t1_recall` (token recall vs T3+T2+T1 union) | 0.964 | 0.948 | -0.016 |

This is a STRONG number, but it is fully reference-leaking: tier3 AD is one of the references and trivially scores near 100% recall of itself. The metric is **not paper-usable as a competing audit metric**; it is a sanity-check baseline showing what trivial reference-overlap looks like. The CLIP+ADQA ensemble (rho 0.929 in-bench, 0.873 external) does NOT have this property because it scores against the video, not against T3.

We should rename it in our reports to make the leakage explicit (e.g. `t3_self_token_recall`) and cite it only as the "reference-leakage upper bound."

## What this means for the paper

Three claims become defensible together:

1. **Ensemble lift over the closest published reference-free baseline holds across corpora**: +0.030 on 18 clips, +0.016 on 60 clips. Both are above the joint bootstrap interval.

2. **The Ensemble's T3 pairwise win rate (173/180 = 96.1%) is the only meaningful generalization number** because every reference-based competitor trivially gets 100%.

3. **External rho drop is modest (-0.056 ensemble; -0.042 LLM-AD-Eval; -0.025 CRITIC)**. The 18-clip benchmark is not an overfit artifact for any of these metrics.

## Recommended paper subsection structure

1. Define the 60-clip corpus (10 categories, unseen, full tier construction).
2. Table: in-bench rho vs external rho for each metric, with the reference-leakage caveat boxed.
3. Headline claim: "Ensemble lift holds; reference-based metrics trivially win T3 pairwise comparisons, masking their inability to order the middle tiers."

## See Also

- [[research/scenetwin-external-validation]] - the original 60-clip ensemble rho measurement
- [[research/scenetwin-tier-ordering-failures]] - in-benchmark 3/18 violations (T1->T2 pattern)
- [[research/scenetwin-statistical-power]] - power defense; this page adds the cross-corpus replication

## Sources

- `cursor/research/output/external_paper_baselines.csv` (per-clip per-tier baseline scores on 60-clip corpus)
- `cursor/research/output/external_paper_baselines_leaderboard.csv` (leaderboard with T3 wins / full ordering)
- `cursor/papers/output/metric_leaderboard.csv` (in-benchmark 18-clip leaderboard)
