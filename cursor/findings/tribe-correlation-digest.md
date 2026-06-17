# TRIBE correlation digest

Significant TRIBE features vs benchmark outcomes (p < 0.05).

- **mean_standard_slot_score** vs 4-judge ADQA tier ordering agreement: ρ = -0.751, p = 0.0003327 — Higher TRIBE → lower outcome (expected for judge agreement)
- **mean_speech_density** vs 4-judge ADQA tier ordering agreement: ρ = 0.519, p = 0.02721 — Higher TRIBE → higher outcome
- **mean_extended_need_score** vs claude_vlm_specificity_norm_tier3_margin: ρ = -0.478, p = 0.04494 — Higher TRIBE → lower outcome (expected for judge agreement)

## Takeaway

`mean_standard_slot_score` inversely predicts judge agreement (ρ ≈ −0.75).
That is the cleanest TRIBE-only story: use video+audio brain gap to forecast
when automatic AD scoring will be unreliable, before any AD text exists.