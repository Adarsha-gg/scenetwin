# ADQA — What You See Is What You Ask (EMNLP 2025)

**Source:** [arxiv_2510.00808.pdf](sources/arxiv_2510.00808.pdf) · [project](https://katha-ai.github.io/projects/adqa/)

## Why they did it

Automatic AD work evaluated **few-second clips** against **one reference AD**. ADQA authors aligned **two independent human AD tracks** for the same movies and showed massive subjectivity in *when*, *whether*, and *what* to describe (~40% temporal misalignment). They built **minute-long segment MCQs** split into:

- **Visual Appreciation (VA)** — visual facts, aesthetics
- **Narrative Understanding (NU)** — plot-critical points

Goal: test whether an AD would help a BLV viewer **understand the story** and **appreciate visuals**, not match one writer’s wording.

## What we agree with

- Single-reference CIDEr/BLEU/embedding-to-pro-AD is a weak audit target.
- Segment length matters; VATEX 10s tiers are a stress test ADQA explicitly criticizes.
- VA vs NU decomposition is actionable — different failure modes (pretty but plot-blind vs plot-heavy but sparse).

## What we think is wrong / limited

1. **MCQ still has one keyed answer** — subjectivity is measured then ignored at eval time.
2. **Generation leaderboard focus** — ADQA is generative benchmarking; SceneTwin needs **reference-free tier ranking** without human question authoring per clip.
3. **Critical vs non-critical questions** — paper hints importance weighting; default aggregate treats all questions equally (we saw tier order flip on “talky” clips when only critical items matter).

## Our alternative

- Use ADQA-style **frame-grounded QA** as one ensemble leg (already: `adqa_v4_score`).
- Add **critical-only** and **VA-only / NU-only** ρ splits — if NU-only ρ drops, our tier GT is narrative-biased.
- Pair with **subjectivity proxy** (embedding divergence between tier1 vs tier3) instead of second human track.

## Implementation

| Script | Status |
|--------|--------|
| `output/scenetwin_timing_20clip/adqa_v4/` | Production ADQA v4 scores |
| `cursor/methods/adqa_va_nu_eval.py` | VA/NU split prototype |

## Measured (18 clips × 4 tiers)

| Metric | ρ vs tier GT |
|--------|-------------:|
| `adqa_v4` | **0.789** |

Second in paper leaderboard after ensemble and LLM-AD-Eval proxy. Complements CLIP (visual) without referencing pro AD text at score time — **prefer ADQA over LLM-AD-Eval** for audit semantics.
