# Scalable AD QC — IRT + VLM Raters (2026)

**Source:** [arxiv_2602.01390.pdf](sources/arxiv_2602.01390.pdf)

## Why they did it

Crowdsourced + VLM AD production lacks **systematic QC**. NLP metrics on short clips miss **delivery, timing, clarity, objectivity**. They built a **6-dimension rubric** (from professional guidelines + BLV consultants), expert GT on 30 ADs, then **Item Response Theory** to score rater proficiency and item difficulty. Top VLMs ≈ human raters on aggregate; VLM **reasoning** less actionable.

## What we agree with

- **Delivery/timing** dimensions are orthogonal to CLIP/ADQA — biggest gap in SceneTwin ensemble.
- IRT lets you **drop bad raters** — analog: drop noisy metrics with low discriminability on our tier ladder.
- Six dims map to VideoA11y / DCMP guidelines we already proxy.

## What we think is wrong / limited

1. **30 ADs × 10 videos** — small for IRT stability; our 72 rows are tier duplicates across clips.
2. **VLM-as-rater cost** — we use rubric **keyword/heuristic proxy**, not GPT-4V calls.
3. Rubric still **subjective** at expert level — same ADQA tension.

## Our alternative

- `irt_rubric_proxy.py` — six dim scores 0–1 from rule patterns (passive voice, timing words, sighted jargon, etc.).
- Merge with `timing_overlap_g7g8.py` for **G7/G8 delivery** dimension.
- Use IRT-inspired **weighting**: dimensions with higher tier separation get higher fusion weight (learned from correlation matrix).

## Implementation

| Script | Status |
|--------|--------|
| `cursor/methods/irt_rubric_proxy.py` | Prototype |
| Not yet on metric leaderboard | Run + add |

## Takeaway

Best candidate to **break Cluster A redundancy** — if IRT delivery ρ is low but **partial correlation** with ADQA is near zero, add to fusion without overfitting semantic cluster.
