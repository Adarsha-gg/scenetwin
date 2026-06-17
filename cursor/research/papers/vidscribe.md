# ViDscribe — Custom AD + VQA (CHI EA 2026)

**Source:** [arxiv_2603.14662.pdf](sources/arxiv_2603.14662.pdf)

## Why they did it

One-size-fits-all AD fails BLV users who differ in **detail preference**, ** pacing**, and **interest**. ViDscribe offers six customization types + conversational VQA on YouTube. Longitudinal study: customized AD improved effectiveness, enjoyment, immersion.

## What we agree with

- **Population-level tier GT is wrong** for a significant user subset — explains subjectivity findings in ADQA.
- VQA coverage (“did the AD answer what I care about?”) is a legitimate eval axis.
- Customization + query logs reveal **gaps in both AI and human AD**.

## What we think is wrong / limited

1. **n=8 longitudinal** — not a ranking metric for 18 clips.
2. **No ground-truth tier** — SceneTwin’s 4-tier ladder assumes one optimal description depth.
3. CHI paper is **system + UX**, not Spearman-friendly benchmark.

## Our alternative

- `vidscribe_query_coverage.py` — template questions per clip genre; score = fraction answerable from AD text alone.
- Use **variance across query types** as subjectivity flag, not mean score vs tier.
- Future: simulate 3 persona weights (minimal / standard / rich) and report **worst-persona ρ** instead of mean ρ.

## Implementation

| Script | Status |
|--------|--------|
| `cursor/methods/vidscribe_query_coverage.py` | Prototype; not on leaderboard |

## Takeaway

ViDscribe explains **when tier3 pro loses** to tier2 for some users — not a direct tier ranker. Pair with ADQA subjectivity work; don’t expect high ρ on aggregate benchmark.
