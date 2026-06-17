# Fundamental assumption challenges

## tier0_beats_tier1 (ensemble_score)

- **Result:** 
- **Read:** cross-video control outscores in-domain short caption

## tier0_beats_tier1 (adqa_score)

- **Result:** 
- **Read:** cross-video control outscores in-domain short caption

## tier0_beats_tier1 (vt_consistency)

- **Result:** 
- **Read:** cross-video control outscores in-domain short caption

## hard_clip_violations (ensemble_score)

- **Result:** 0,12
- **Read:** GT violations on known-hard clips; total viol=3

## hard_clip_violations (adqa_score)

- **Result:** 0,12
- **Read:** GT violations on known-hard clips; total viol=5

## hard_clip_violations (vt_consistency)

- **Result:** 0
- **Read:** GT violations on known-hard clips; total viol=6

## length_confound_tier3 (ensemble_score)

- **Result:** r=0.005,p=0.9851
- **Read:** pro AD word count vs ensemble score (should be weak if not length-biased)

## ensemble_vt_redundancy (spearman)

- **Result:** rho=0.769,p=0.0000
- **Read:** high rho → VT adds little; low rho → orthogonal signal

## tribe_pressure_vs_tier3_margin (ensemble)

- **Result:** rho=-0.077,p=0.7602
- **Read:** high need → harder to separate pro from short?

