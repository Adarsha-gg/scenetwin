# Novel research metrics

**These are new.** Not tribe_pressure, collision_debt, ensemble ρ, or paper-metric re-runs.

## Definitions

| Metric | Formula intuition |
|--------|------------------|
| **comprehension_per_second** | critical-weighted ADQA ÷ read time |
| **false_grounding_gap** | CLIP norm − ADQA norm (within clip) — high = looks grounded, fails QA |
| **temporal_misalign** | \|need center-of-mass − visual-evidence center in AD\| |
| **visual_lexicon_purity** | AD words hitting ADQA `required_visual_evidence` lexicon |
| **audio_leakage** | on speech-heavy clips: 1 − lexicon purity |
| **saturation_ratio** | (ADQA gain over cross-video) ÷ word count |
| **rank_chaos** | 1 − Kendall(ADQA rank, CLIP rank) within clip |
| **head_agreement_index** | fraction of {ADQA, CLIP, story} picking tier3 |
| **inversion_mass_adqa** | magnitude of ADQA tier-order violations |
| **marginal_word_value_t3** | ΔADQA(t3−t1) ÷ Δwords |
| **RAI** | composite: CPS + anti-FGG + anti-TMI + purity + head agreement |
| **specificity_density** (external) | pro-unique content words ÷ pro length |
| **clip_gain_per_word** (external) | ΔCLIP(t3−t1) ÷ Δwords |

## Best for *research targets* (not tier ρ)

| Metric | Target | Value | Interpretation |
|--------|--------|------:|----------------|
| Inversion mass on ADQA | Ensemble GT violation | 0.911 | clip |
| Visual lexicon purity | Ensemble GT violation | 0.900 | tier3 |
| False grounding gap | ADQA disputes tier GT | 0.844 | tier3 |
| Temporal misalignment | ADQA disputes tier GT | 0.750 | tier3 |
| False grounding gap | Low tier3 margin | 0.679 | tier3 |
| Inversion mass on ADQA | Judge tier disagreement | 0.672 | clip |
| Temporal misalignment | Ensemble GT violation | 0.667 | tier3 |
| Rank chaos (ADQA vs CLIP disagree) | Pro AD critical miss | 0.667 | clip |
| Rank chaos (ADQA vs CLIP disagree) | Ensemble GT violation | 0.667 | clip |
| Research Audit Index (RAI) | Ensemble GT violation | 0.667 | clip |
| Rank chaos (ADQA vs CLIP disagree) | ADQA disputes tier GT | 0.656 | clip |
| Temporal misalignment | Judge tier disagreement | 0.656 | tier3 |

## Tier GT ρ (novel metrics only — for comparison)

- **Visual lexicon purity**: ρ=0.447
- **Saturation ratio**: ρ=0.350
- **Comprehension per second**: ρ=0.333
- **Rank chaos (ADQA vs CLIP disagree)**: ρ=0.000
- **Head agreement index**: ρ=0.000

## External clips (no ADQA)

- `clip_gain_per_word` vs `pro_beats_short_inv`: -0.813
- `clip_gain_per_word` vs `full_order_fail`: -0.592
- `cross_caption_overlap` vs `pro_beats_short_inv`: -0.124
- `specificity_density` vs `full_order_fail`: 0.088
- `specificity_density` vs `pro_beats_short_inv`: -0.085
- `cross_caption_overlap` vs `full_order_fail`: 0.083

## What actually helps research

**Key insight:** Several novel metrics have **ρ≈0 vs tier GT** on purpose — they measure different things.

- **inversion_mass_adqa** AUC **0.91** on ensemble violation clips
- **false_grounding_gap** AUC **0.84** on ADQA-vs-GT label disputes (clips 3, 7)
- **visual_lexicon_purity** ρ=**0.45** vs tier GT — best novel tier ranker
- **temporal_misalign** ρ=**−0.37** vs tier GT — pro AD often *mis-timed*, not better

1. **false_grounding_gap** — catches CLIP-happy / ADQA-sad tiers (clip 12 volleyball pattern)
2. **comprehension_per_second** — efficiency metric; tier3 may lose to tier2 on CPS even when raw ADQA wins
3. **rank_chaos** — reference-free clip difficulty before choosing an audit metric
4. **marginal_word_value_t3** — is pro AD worth the extra words?
5. **RAI** — first composite built only from novel legs, not stale ensemble

Use these instead of adding another semantic embedding to the pile.
