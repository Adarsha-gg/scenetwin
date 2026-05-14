---
title: "SceneTwin Gap-Targeted AD Loop"
category: research
tags: [SceneTwin, TRIBE, AD-generation, brain-guided-LLM, controller, accessibility]
created: 2026-05-03
updated: 2026-05-03
sources:
  - tools/scenetwin_gap_targeted_prompts.py
  - output/scenetwin_description_gain/gap_targeted_prompts.jsonl
  - wiki/research/scenetwin-roi-content-typing.md
  - wiki/research/scenetwin-working-stack.md
---

# SceneTwin Gap-Targeted AD Loop

## Why this exists

ROI content typing made TRIBE a window-typer. That is novel framing on classified
output. To make TRIBE the differentiator, it has to control what AD gets generated,
not just describe what kind of AD a window calls for.

The loop turns TRIBE into a brain-encoding controller for an LLM AD generator.
The output is AD text that no system without TRIBE could have produced.

## Architecture

```text
Window w with per-ROI need profile P_w
   |
   v
Gap-targeted prompt (already built, see scenetwin_gap_targeted_prompts.py)
   |
   v
LLM (Claude/GPT) generates AD candidate D_w
   |
   v
TRIBE(audio_w + D_w) -> P_{A+D}
   |
   v
Compare P_{A+D} to P_AV in the ROIs that drove the gap
   |
   +---> if gap shrinks in target ROIs: accept
   +---> else: feed residual gap back to LLM, regenerate
```

This is closed-loop AD generation gated on predicted cortical response.

## Phase 1: prompt-only A/B (no TRIBE in loop)

Cheapest test of whether the typing actually changes generated AD.

1. Use the JSONL prompts as-is for the gap-targeted condition.
2. Build a baseline condition: same audio context, same word budget, NO ROI profile,
   NO dominant-type instruction. Just "describe the scene for a blind listener."
3. Generate AD with each condition for all 21 windows.
4. Score with:
   - CLIP-L14 against window center frame
   - Per-content-type lexicon coverage (already in roi_content_profile)
   - Profile alignment to the window's TRIBE need profile
5. Pass condition: gap-targeted AD shows higher profile alignment than baseline AD
   on the dominant ROI for each window, with similar or better CLIP grounding.

If Phase 1 fails (gap-targeted prompt does not change AD content), the loop is dead
and TRIBE is decorative. If it passes, advance to Phase 2.

### Implementation status

Implemented:

- `tools/scenetwin_phase1_generate_ad.py`
- `tools/scenetwin_phase1_score_ad.py`
- `output/scenetwin_description_gain/phase1_ad_candidates.jsonl`
- `output/scenetwin_description_gain/phase1_ad_scores.csv`
- `output/scenetwin_description_gain/phase1_ad_summary.csv`

The first run used the local-template fallback because no LLM API key was present
in the shell environment. Treat it as a pipeline smoke test, not evidence that an
LLM follows TRIBE guidance. The real run is:

```bash
ANTHROPIC_API_KEY=... python tools/scenetwin_phase1_generate_ad.py --provider anthropic
python tools/scenetwin_phase1_score_ad.py
```

## Phase 2: TRIBE in the loop (Colab)

Adds the actual cortical feedback signal.

1. For each window, run TRIBE on (audio_w + D_w_baseline) and (audio_w + D_w_targeted).
2. Compute residual gap per ROI:
   `residual_roi(w) = roi_gap(P_AV, P_{A+D}, ROI)` for each ROI in the typing.
3. Compare residual gaps across conditions:
   - target ROIs (high gap before): residual should drop more under gap-targeted
   - non-target ROIs: residual should be similar (or gap-targeted should not damage them)
4. Accept candidate if residual_target < tolerance and residual_nontarget is not worse
   than baseline by more than `delta`.
5. If rejected, feed back to LLM with structured residual:
   ```
   Previous AD did not close the cortical gap in target ROI {roi}.
   Predicted residual gap: {residual:.2f} (was {original:.2f}).
   Underweighted dimensions: {list}.
   Regenerate with stronger emphasis on {dominant_type}.
   ```
6. Stop after `max_iters=3` or when accepted.

Compute budget: 2 TRIBE forward passes per iteration per window. On L4 with the
Colab notebook from the description gain test, that is roughly 2-3 minutes per
iteration per window. For 21 windows x 2 iterations x 2 conditions, plan ~3 hours
of GPU time.

## Phase 3: counterfactual ablation

Required for any "TRIBE causes the AD to be different" claim.

1. Run the full pipeline with the ROI need profile shuffled across windows
   (preserving marginal distribution but breaking window-specific signal).
2. Run with the ROI need profile zeroed (uniform prior over content types).
3. Compare generated AD between (a) real profile, (b) shuffled profile, (c) zeroed
   profile.
4. Differences must be statistically larger between (a) and (c) than between
   (b) and (c). Otherwise the LLM is reacting to surface formatting, not TRIBE.

## Phase 4: human / ADQA validation

The metric story still needs an external check.

1. Sample 20 windows across clips, with paired AD (baseline + gap-targeted).
2. ADQA-style: write 2-3 visual/narrative questions per window. Rate which AD
   answers them better. Blind ratings.
3. If gap-targeted wins above chance with reasonable significance, the controller
   produces functionally better AD, not just metric-aligned AD.

## Acceptance criteria for the headline claim

To say *"TRIBE-guided AD generation produces measurably better audio descriptions
than caption-grounded baselines"*, all of these must hold:

- Phase 1: profile alignment significantly higher under gap-targeted prompt
  (p < 0.05 on permutation test, on >= 20 windows).
- Phase 2: target-ROI residual gap significantly lower under gap-targeted AD
  (paired test, n >= 20 windows).
- Phase 3: AD divergence (real profile) - (zeroed profile) > AD divergence
  (shuffled profile) - (zeroed profile), measured by token-level Jaccard or
  embedding distance.
- Phase 4: human/ADQA preference for gap-targeted AD above chance.

If any phase fails, downgrade the claim to what survives. Phase 1 alone is enough
for an undergrad symposium poster. Phases 1+2 together is enough for a workshop
paper. All four is enough for a venue paper.

## Risks and dead-end signals

| Failure mode | Diagnostic | Action |
|---|---|---|
| LLM ignores ROI profile | identical or near-identical AD across conditions | strengthen prompt; increase profile salience |
| ROI profile is not informative | random shuffle gives same AD differences | the typing is the failure, not the loop; revisit Destrieux -> functional atlas |
| TRIBE residual does not move | P_{A+D} - P_A is near zero regardless of D | TRIBE is not text-sensitive enough at this scale; need joint A+D event encoding (codex flagged this) |
| Gap shrinks but human prefers baseline | metric/human mismatch | metric is gameable; need ADQA or BLV ratings as the real target |

## What is needed before Phase 1 runs

1. An LLM endpoint (Anthropic API or OpenAI) and a small wrapper that reads
   `gap_targeted_prompts.jsonl`, calls the model, and writes back AD candidates
   plus model metadata. ~50 lines of Python.
2. A baseline prompt template (no ROI profile) that matches the structural format
   of the gap-targeted prompt to control for length/style.
3. A scoring script that runs CLIP-L14 + lexicon coverage + profile alignment on
   the resulting AD set. The lexicon coverage code already exists in
   `tools/scenetwin_roi_content_profile.py` and can be reused.

Phase 1 is a half-day of work after the LLM wrapper is written. It does not need
GPU. It is the first experiment that can falsify or support the controller pitch.
