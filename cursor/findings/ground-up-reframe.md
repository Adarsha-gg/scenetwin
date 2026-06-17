# SceneTwin ground-up thesis (2026-05-27)

## What we challenged

1. **Frozen ensemble CSV uses ADQA v2**, not v4 — headline ρ may be stale.
2. **Within-clip minmax** ties max tiers (clip 0: tier0/tier3 ADQA ties → both get 1.0).
3. **Tier GT is assumed**, not verified — ADQA v4 disagrees on **11%** of clips.
4. **TRIBE as blend weight** is wrong framing — collision signals predict *when GT fails*.

## Ensemble recomputed (honest)

| Method | ρ pooled | ρ per-clip mean | LOO ρ | violations |
|--------|---------:|----------------:|------:|-----------:|
| ensemble_w50_adqa_need_weighted_clip | 0.928 | 0.940 | 0.928 | 3 |
| ensemble_v4_rank_50 | 0.889 | 0.905 | 0.889 | 5 |
| ensemble_v4_minmax_50 | 0.882 | 0.933 | 0.882 | 6 |
| ensemble_crit_minmax_50 | 0.878 | 0.922 | 0.878 | 7 |
| ensemble_no_norm_sum | 0.800 | 0.922 | 0.800 | 7 |
| ensemble_adqa_v4_only | 0.793 | 0.912 | 0.793 | 5 |
| adqa_v4_mean | 0.793 | 0.912 | 0.793 | 5 |
| ensemble_clip_only | 0.735 | 0.822 | 0.735 | 8 |
| clip_top3 | 0.735 | 0.822 | 0.735 | 8 |
| need_weighted_clip | 0.733 | 0.833 | 0.733 | 7 |

- Stale `ensemble_w50_adqa_need_weighted_clip` (v2): **ρ=0.928**
- Rebuilt v4 minmax 50/50: **ρ=0.882**
- ADQA v4 alone (no CLIP, no norm): **ρ=0.793**
- Rank fusion (no minmax tie inflation): **ρ=0.889**
- v2 vs v4 row mismatches (|Δ|>0.05): **54** / 72

## Tier GT vs ADQA v4

- Tier3 is ADQA-best on **89%** of clips (16/18)
- Tier2 beats tier3 on ADQA in **0** clips
- Clips where GT likely wrong: 3,7

## TRIBE reframed: collision regime router

Stop asking: *does TRIBE improve ρ?*

Ask: *when dense speech + high visual debt collide, does professional slot-AD fail?*

**Target:** tier2 beats tier3 on ADQA, or pro AD critical miss.

Best signal: `high_need_seconds_frac` → `critical_any_miss` AUC=**0.556** (n_pos=3)

### Two-stage model

```
if collision_index >= median:
    regime = INTEGRATED  # tier order may invert; audit tier2/tier3 separately
else:
    regime = STANDARD    # ADQA v4 + CLIP ranking applies
```

- Tier2 beats tier3 rate (collision regime): **0.00**
- Tier2 beats tier3 rate (standard regime): **0.00**

## Real research claim (replaces ρ headline)

> **SceneTwin is a two-stage accessibility auditor.** Stage 1 (TRIBE collision index) classifies whether a clip is in *standard slot-AD* or *integrated/collision* regime. Stage 2 (ADQA + CLIP) scores description quality **within** regime. Global tier ordering is invalid when regimes mix — the old ρ=0.929 conflates correct rankings on easy clips with wrong GT on collision clips.

## Next experiments

- Export TRIBE P_AV/P_A vectors for cached clips → `vector_policy_boundary`
- Regime-conditional ρ (report separately, not pooled)
- External clips: test if collision predicts generalization gap
- Replace tier GT with ADQA-consensus labels on disagreement clips
