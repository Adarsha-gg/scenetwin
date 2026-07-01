# SceneTwin Central Thesis

_Last updated: 2026-06-19_

## One-sentence thesis

**SceneTwin is a human-reference-free audit framework for audio description: it scores candidate ADs on a corrected three-tier ladder, gates unsafe descriptions, and routes uncertain clips to review.**

## Main correction

We are **not using the old four-tier benchmark as the paper benchmark**.

The old T2 “long VATEX” tier is invalid because it is simply the longest of several equal-status crowd captions. That makes it a verbosity rung, not a quality rung. The paper should use the corrected three-tier ladder:

```text
T0 cross-decoy < T1 crowd caption < T3 professional AD
```

## Honest headline

| Corpus | Clips | Rows | Spearman ρ | Fully ordered | T3-vs-lower wins |
|---|---:|---:|---:|---:|---:|
| In-benchmark | 18 | 54 | 0.954 | 17/18 | 36/36 |
| External | 60 | 180 | 0.947 | 58/60 | 118/120 |

This is strong and clean.

## Honest market read

We are **not much better than the strongest reference-style metric on ranking**.

| Comparator | In-benchmark ρ | External ρ |
|---|---:|---:|
| SceneTwin CLIP+ADQA | 0.954 | 0.947 |
| LLM-AD-Eval proxy | 0.941 | 0.942 |
| Best frontier VLM judge | 0.863 | 0.847 |

So the paper should not claim broad industry dominance. It should say:

> SceneTwin reaches ranking performance comparable to the strongest reference-style evaluation, but without requiring a human reference AD for ranking, and adds deployment safety gates that ranking metrics do not provide.

## The actual contribution

SceneTwin is paper-worthy as an **audit stack**, not as a huge rho improvement:

1. **Human-reference-free scoring:** CLIP + ADQA ranks corrected AD tiers well without a professional reference.
2. **Safety gates:** CLIP grounding-drop catches many hallucinations when given a clip-relevant anchor; raw CLIP catches wrong-content failures without an anchor.
3. **Review policy:** ADQA margin and TRIBE gap help decide what to ship versus review.

## What to remove from paper framing

Remove or demote:

- old four-tier result tables;
- old four-tier comparison counts as headline numbers;
- any broad “we beat all industry methods by a large margin” language;
- brain-grounded steering as main thesis;
- Access Surface OS;
- 0.965 tuned/multi-judge headline.

## What to emphasize

- Corrected 3-tier ladder.
- Human-reference-free deployability.
- Safety gates with operating points.
- VLM judges trail structured grounding.
- LLM-AD-Eval nearly ties ranking, so our advantage is deployment and safety, not raw score dominance.

## Active files

- `output/reports/paper-scenetwin-audit-framework.md` — active submission draft.
- `output/reports/scenetwin-paper-submission-thesis.md` — final thesis memo.
- `output/reports/scenetwin-paper-evidence-check.md` — verified numbers.
