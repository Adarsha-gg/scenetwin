# Regime-aware audit
Collision threshold: 0.493

## Does TRIBE predict where ensemble GT breaks?

- collision → known violation clips {0,12,14}: AUC **0.600**

## ρ under different GT definitions

| test | ρ |
|------|--:|
| tier_gt_stale_ensemble | 0.928 |
| tier_gt_v4_ensemble | 0.882 |
| tier_gt_regime_aware | 0.725 |
| consensus_gt_regime_aware | 0.744 |
| consensus_gt_v4_ensemble | 0.879 |

## Regime-conditional ρ

| test | ρ |
|------|--:|
| standard_regime_regime_score | 0.896 |
| collision_regime_regime_score | 0.620 |
| standard_regime_v4_ensemble | 0.896 |
| collision_regime_v4_ensemble | 0.872 |

## Interpretation

Pooled stale ensemble ρ≈0.928 drops to **v4 ρ≈0.882** when recomputed honestly. Regime-aware scoring does not beat v4 on tier GT — TRIBE's value is **routing** (flag collision clips for integrated AD workflow), not another blend weight.
