# VideoA11y + G7/G8 Timing Guidelines

**Sources:** VideoA11y rubric (HF 2502.20480) · DCMP/G7/G8 timing practice · `papers/timing_overlap_g7g8.py`

## Why they did it

BLV guidelines specify **objectivity** (no sighted-centric jargon), **clarity**, **descriptiveness**, and **synchronized delivery** in natural pauses. VideoA11y codifies rubric dimensions for human rating; broadcast standards (G7/G8) constrain **how much** fits in each gap.

## What we agree with

- Text-quality metrics **ignore illegal timing** — ADQA’s 40% misalignment is partly delivery.
- Tier3 pro AD may violate gap constraints while scoring highest on semantics.
- Rubric dims overlap IRT 6-dim paper — convergent validity.

## What we think is wrong / limited

1. **G7/G8 are heuristics** — no public labeled dataset at 10s granularity.
2. `videoa11y_rubric_proxy.py` uses lexical rules — misses TTS pacing.
3. Timing overlap alone **punishes tier2** for being too short (under-fill gaps) and **tier3** for over-fill — ambiguous direction vs tier GT.

## Our alternative

- Split timing score: **(a) overlap with valid windows** (too much speech in dialogue = bad), **(b) coverage of high-need windows** (TRIBE proxy).
- Combine only in **`audit_no_ref` fusion** where semantic cluster dominates tier3 bias.
- External clips: extract audio VAD for gap detection instead of movie AD scripts.

## Implementation

| Script | Status |
|--------|--------|
| `cursor/methods/videoa11y_rubric_proxy.py` | Lexical rubric |
| `cursor/papers/timing_overlap_g7g8.py` | Gap overlap |

## Takeaway

Timing cluster is the **highest-priority underimplemented** leg relative to paper literature — ADQA + AutoAD III + AVBench all skip it; IRT/CA3D/VideoA11y agree it matters.
