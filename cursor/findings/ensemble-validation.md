# Ensemble validation (cursor rerun)

Clips with complete data: **18**

## Global Spearman vs tier ground truth

| Metric | ρ |
|--------|---|
| CLIP top3 norm | 0.8010 |
| ADQA norm | 0.8536 |
| Ensemble 50/50 | 0.9285 |

Mean per-clip CLIP↔ADQA ρ: **0.822** (complementarity diagnostic)

Bootstrap 95% CI on ensemble ρ (2000 resamples): **[0.881, 0.961]** (point 0.928)