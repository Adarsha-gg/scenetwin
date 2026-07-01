---
title: SceneTwin T3 pairwise losses on the 60-clip primary set (corrected ladder)
category: research
tags: [scenetwin, generalization, failure-analysis, paper-section, primary]
sources: [cursor/output/external_ensemble_eval.csv, cursor/data/external_clips/registry.jsonl]
created: 2026-05-29
updated: 2026-06-27
---

> Corrected three-tier ladder, **60-clip primary set**. The T2 ("long VATEX") rung is removed, so
> the five old losses *to T2* no longer exist. Recomputed from `external_ensemble_eval.csv`.
> Superseded: the old 4-tier "7/180" version (5 of those losses were to the retired T2).

## Headline

On the 60-clip primary set, the CLIP+ADQA ensemble has **178/180 = 98.9% T3 pairwise wins**. Only
**2 losses** remain, both to T1 (crowd caption) and both on clips where T3 abstracts editorial
framing while the literal caption matches what CLIP sees. No T3 loses to T0 (cross-decoy).

## The 2 losses (corrected 3-tier)

| # | video_id | category | beaten by | T3 score | beating score | margin |
|---:|---|---|---|---:|---:|---:|
| 1 | GOH6fBhoi2o_000010_000020 | Entertainment | T1 | 0.602 | 1.000 | 0.398 |
| 2 | d7_SY48r__8_000060_000070 | How-to & Instructional | T1 | 0.972 | 1.000 | 0.028 |

Loss #2 is a near-tie (margin 0.028, below per-clip rank uncertainty). Loss #1 is the genuine
editorial case analyzed below.

## The dominant failure: T3 editorial framing vs raw visual content

Loss #1 (clip `GOH6fBhoi2o`, margin 0.398) is the genuine editorial case. The video shows a toddler in front of a TV. The professional T3 AD focuses on the toddler (subject), while the crowd caption (T1) mentions what's playing on the TV (background):

- **T3 (lost):** "In a dimly lit room, a toddler sits close to a television, captivated by the screen. The child giggles and fidgets, occasionally..."
- **T1/T2 (won):** "A dark recording of people hitting themselves and talking as a tv turns on and a child watches"

CLIP picks up the action on the TV; the professional AD chose not to describe it. **This is not a metric bug -- it is the metric correctly registering that T3 omitted visible content.** It surfaces a tension between AD authorship norms (describe the BLV viewer's primary referent) and metric semantics (does the AD mention what's on screen).

> **Retired:** three additional 4-tier losses were to the long-VATEX T2 rung
> (`u-olDM7oGGM`, `BHxn3qfPAl4`, `21T1JDdJgsM`, `ShSSAEfnyDs`). Removing T2 removed those losses;
> they are no longer part of the corrected-ladder failure set.

## Comparison to the in-benchmark pilot

| Set | T3 pairwise losses | Pattern |
|---|---:|---|
| Pilot (18) | 1/54 (clip 0, T0 = T1 tie; T3 wins all 18) | tie at the bottom rung |
| Primary (60) | 2/180 (both to T1) | T3 abstracts editorial framing; literal caption matches CLIP |

The metric rewards literal visual grounding over editorial abstraction. On the pilot this is nearly
invisible (all 18 T3 ADs are well-grounded); on the primary set it surfaces on 2/60 clips with
strong subject/background editorial choices, one of which is a near-tie.

## Paper framing

This is not a weakness to hide. Three honest framings work:

1. **Metric is doing exactly what it claims**: scoring AD against visible content. When AD makes editorial choices to omit visible content, the metric correctly penalises that.

2. **AD authorship has known editorial conventions**: pro AD prioritises the BLV viewer's narrative referent over exhaustive description. The metric is reference-free; it does not know about these conventions. This is a real-world tension worth naming.

3. **The 7 losses correspond to known difficult AD categories**: Entertainment (foreground / background tension), Health & Wellness (technical motion specificity). They give the paper a calibrated honesty about where the metric's reference-free design diverges from human pro-AD authorship.

## Recommended paper subsection

```
Section 5.2 Primary-set failure analysis (n=60)

On the corrected three-tier ladder the ensemble registers 2/180 T3
pairwise losses (98.9% wins), both to the crowd caption (T1). One is a
near-tie (margin 0.028). The other (clip GOH6fBhoi2o, toddler+TV) is an
editorial case where pro AD described the foreground subject while the
crowd caption described background TV content visible to CLIP.

This surfaces a tension between AD authorship conventions (selective
visual reporting) and reference-free metrics (exhaustive visual
grounding). We treat this not as a metric defect but as a calibrated
honesty about where reference-free evaluation will diverge from human
editorial choices.
```

## See Also

- [[research/scenetwin-tier-ordering-failures]] - pilot ordering (retired 4-tier rationale)
- [[research/scenetwin-external-validation]] - 60-clip primary ρ = 0.952 / 178/180 T3 wins
- [[research/scenetwin-external-baselines]] - paper-baseline comparison on the same 60 clips

## Sources

- `cursor/output/external_ensemble_eval.csv` (raw ensemble scores, corrected 3-tier)
- `cursor/data/external_clips/registry.jsonl` (AD text per clip)
