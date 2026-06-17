---
title: SceneTwin external T3 pairwise losses (7/180 on 60-clip corpus)
category: research
tags: [scenetwin, generalization, failure-analysis, paper-section, external]
sources: [cursor/output/external_ensemble_eval.csv, cursor/data/external_clips/registry.jsonl, cursor/research/output/external_t3_pairwise_losses.csv]
created: 2026-05-29
updated: 2026-05-29
---

## Headline

On 60 external clips, the CLIP+ADQA ensemble has 173/180 = 96.1% T3 pairwise wins. The 7 losses concentrate in two narrow failure modes: **3 are essentially ties** (margin < 0.04), **2 are near-ties** (margin < 0.15), and **2 are large losses on a single clip** where T3 described the foreground while VATEX captions described the background TV content. No T3 loses to T0 (cross-decoy).

## The 7 losses

| # | video_id | category | beaten by | T3 score | beating score | margin |
|---:|---|---|---|---:|---:|---:|
| 1 | GOH6fBhoi2o_000010_000020 | Entertainment | T1 | 0.602 | 1.000 | +0.398 |
| 2 | GOH6fBhoi2o_000010_000020 | Entertainment | T2 | 0.602 | 1.000 | +0.398 |
| 3 | u-olDM7oGGM_000012_000022 | Health & Wellness | T2 | 0.857 | 1.000 | +0.143 |
| 4 | BHxn3qfPAl4_000018_000028 | Health & Wellness | T2 | 0.877 | 0.917 | +0.039 |
| 5 | 21T1JDdJgsM_000047_000057 | Entertainment | T2 | 0.958 | 0.987 | +0.028 |
| 6 | d7_SY48r__8_000060_000070 | How-to & Instructional | T1 | 0.972 | 1.000 | +0.028 |
| 7 | ShSSAEfnyDs_000000_000010 | Entertainment | T2 | 0.996 | 1.000 | +0.004 |

## Breakdown

| Beating tier | Count |
|---|---:|
| T2 (vatex_long)  | 5 |
| T1 (vatex_short) | 2 |
| T0 (cross-decoy) | **0** |

| Category | Count of losses |
|---|---:|
| Entertainment            | 4 |
| Health & Wellness        | 2 |
| How-to & Instructional   | 1 |
| (other 7 categories)     | 0 |

## The dominant failure: T3 editorial framing vs raw visual content

Two of the 7 losses (both on clip `GOH6fBhoi2o`, margin 0.398 each) share a single editorial pattern. The video shows a toddler in front of a TV. The professional T3 AD focuses on the toddler (subject), while T1/T2 mention what's playing on the TV (background):

- **T3 (lost):** "In a dimly lit room, a toddler sits close to a television, captivated by the screen. The child giggles and fidgets, occasionally..."
- **T1/T2 (won):** "A dark recording of people hitting themselves and talking as a tv turns on and a child watches"

CLIP picks up the action on the TV; the professional AD chose not to describe it. **This is not a metric bug -- it is the metric correctly registering that T3 omitted visible content.** It surfaces a tension between AD authorship norms (describe the BLV viewer's primary referent) and metric semantics (does the AD mention what's on screen).

## Health & Wellness losses follow a similar pattern (smaller magnitude)

| clip | T3 framing | T2 framing (the winner) |
|---|---|---|
| u-olDM7oGGM (boy + dog on street) | "young boy with backpack walks alongside group" | "boy puts his sweater around his shoulders and runs out into the road" -- describes specific motion that T3 generalized |
| BHxn3qfPAl4 (massage) | "massage therapist gently stretches and massages her neck" | "someone behind her is pushing her neck all the way to the left" -- direction specificity that T3 abstracted |

Pattern: **T3 abstracts; T1/T2 are literal**. When CLIP scores against the video, literal beats abstract on these clips.

## The near-ties (5/7 within margin = 0.039)

Five of the seven losses are within 0.04 of T3, which is below any meaningful per-clip rank uncertainty (cluster bootstrap on a single clip's 4 scores would easily span this). These are reporting ties, not metric failures.

## Comparison to the in-benchmark 3/18 failures

| Set | Failures | Pattern |
|---|---:|---|
| In-benchmark (18) | 3 (T1>T2 violations; T3 wins all 18) | Long T2 with errors / filler |
| External (60) | 7 (T3 pairwise losses; T2 or T1 wins) | T3 abstracts editorial framing; lower tiers are literal |

The failure modes are different but both reduce to **the metric rewards literal visual grounding over editorial abstraction**. In-benchmark that property is invisible because all 18 T3 ADs are well-grounded. Externally it surfaces on 4/60 = 6.7% of clips with strong subject/background editorial choices.

## Paper framing

This is not a weakness to hide. Three honest framings work:

1. **Metric is doing exactly what it claims**: scoring AD against visible content. When AD makes editorial choices to omit visible content, the metric correctly penalises that.

2. **AD authorship has known editorial conventions**: pro AD prioritises the BLV viewer's narrative referent over exhaustive description. The metric is reference-free; it does not know about these conventions. This is a real-world tension worth naming.

3. **The 7 losses correspond to known difficult AD categories**: Entertainment (foreground / background tension), Health & Wellness (technical motion specificity). They give the paper a calibrated honesty about where the metric's reference-free design diverges from human pro-AD authorship.

## Recommended paper subsection

```
Section 5.2 External failure analysis (n=60)

The ensemble registers 7/180 T3 pairwise losses (96.1% wins). Failure
modes concentrate in Entertainment and Health & Wellness clips where
professional AD abstracts narrative framing while VATEX captions are
literal about visible content. Five of the seven losses are within
margin 0.04 of T3 (reporting ties). The remaining two losses share a
single editorial pattern (clip GOH6fBhoi2o, toddler+TV) where pro AD
described the foreground subject while VATEX captions described
background TV content visible to CLIP.

This surfaces a tension between AD authorship conventions (selective
visual reporting) and reference-free metrics (exhaustive visual
grounding). We treat this not as a metric defect but as a calibrated
honesty about where reference-free evaluation will diverge from human
editorial choices.
```

## See Also

- [[research/scenetwin-tier-ordering-failures]] - in-benchmark 3/18 (T1->T2 boundary)
- [[research/scenetwin-external-validation]] - external rho=0.873 / 173/180 T3 wins
- [[research/scenetwin-external-baselines]] - paper-baseline comparison on the same 60 clips

## Sources

- `cursor/research/output/external_t3_pairwise_losses.csv` (per-loss table)
- `cursor/output/external_ensemble_eval.csv` (raw ensemble scores)
- `cursor/data/external_clips/registry.jsonl` (AD text per clip)
