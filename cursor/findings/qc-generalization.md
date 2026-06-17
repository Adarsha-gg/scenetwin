# QC generalization — external calibration

**External clips:** 58 | **Benchmark:** 18

## Calibration rule

- Thresholds: mean/std/p80 from **external YouTube clips only** (58 clips)
- Flag rule: risk >= external p80 (top 20% on held-out YouTube clips) (p80 risk = **0.551**)
- Signals: need−speech gap, peak/words, CLIP(t3−t1), read time
- **No** benchmark min-max, **no** hard-coded violation clip IDs

## AUC — external (calibration set)

- full_order_fail: **0.637**
- pro_loses: **0.741**

## AUC — benchmark (true holdout for thresholds)

- full_order_fail: **0.938**
- pro_loses: **0.732**
- judge_disagree: **0.938**
- known_violation: **0.800**

## Per-signal AUC on external

| signal | full_order_fail | pro_loses |
|--------|----------------:|----------:|
| need_speech_gap | 0.394 | 0.466 |
| peak_over_words | 0.438 | 0.529 |
| clip_t3_minus_t1 | 0.881 | 1.000 |
| read_seconds | 0.594 | 0.472 |

## Flagged clips (same rule both sets)

**External:** _oAKCHh_Av4_000003_0, BHxn3qfPAl4_000018_0, EA3HCx0yTIY_000281_0, RlfVK8z5wJ0_000000_0, F-mRnL_XmJU_000000_0, 0m0-Q0zz_-c_000112_0, 1YemrpNBpf4_000001_0, AEkLDauJVi0_000069_0, gFBO3zrod9Y_000005_0, 1kLhK8KfIEw_000020_0, Xdz1cxEjLYc_000007_0, rGQ64NXktF8_000006_0 … (12/58)

**Benchmark:** clip_12 (1/18)

## Benchmark violations vs QC risk (sanity, not training)

- clip_12 risk=0.579 flagged=True VIOL
- clip_04 risk=0.483 flagged=False     
- clip_07 risk=0.455 flagged=False     
- clip_15 risk=0.442 flagged=False     
- clip_00 risk=0.389 flagged=False VIOL
- clip_19 risk=0.383 flagged=False     
- clip_11 risk=0.383 flagged=False     
- clip_18 risk=0.378 flagged=False     
- clip_14 risk=0.372 flagged=False VIOL
- clip_06 risk=0.365 flagged=False     
- clip_13 risk=0.356 flagged=False     
- clip_17 risk=0.333 flagged=False     
- clip_05 risk=0.323 flagged=False     
- clip_03 risk=0.316 flagged=False     
- clip_09 risk=0.299 flagged=False     
- clip_08 risk=0.267 flagged=False     
- clip_01 risk=0.250 flagged=False     
- clip_16 risk=0.221 flagged=False     
