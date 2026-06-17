---
title: Discovery Pulse
updated: 2026-05-27
---

# Discovery pulse — live hits

**Registry:** 45+ auto-discovered metrics (iter 1–20+). Loop: `discovery_v7` every 10 min.

## Top research signals (not tier ρ)

| Metric | Target | AUC | Notes |
|--------|--------|-----|-------|
| `ratio(read_s, adqa_t3_minus_t0)` | critical miss | **1.00** | Long read time when pro AD underperforms cross-tier |
| `mut_log_ratio(read_s, adqa_t3_minus_t0)` | critical miss | **1.00** | Mutation of above — robust |
| `diff(need_mean, speech_mean)` | judge disagree | **1.00** | TRIBE need vs speech density gap flags judge chaos |
| `mut_tier_scale_diff(need_mean, speech_mean)` | judge disagree | **1.00** | Tier-weighted variant |
| `diff(adqa_norm, speech_mean)` | judge disagree | **0.94** | QA score vs speech load |
| `std_ratio(clip_top3, crit_w)` | critical miss | **0.89** | Cross-tier instability in grounding vs QA |
| `lex_minus_clip` | ensemble violation | **0.89** | Lexicon purity diverges from CLIP |
| `peak_over_words` | ensemble violation | **0.80** | Need peak late + verbose AD |
| `diff(clip_top3, story_recall)` | GT dispute | **0.78** | Clips 3, 7 disagreement |
| `clip_spread_x_tier` | low margin | **0.86** | Tier slope × CLIP spread |

## Phase rotation (each iteration)

0 tier spread → 1 temporal → 2 lexical → 3 mutations → 4 rank instability → 5 conditional → 6 combinatorial

## External

Clip #41 acquired: `h8wsO9A9v_c` (People & Vlogs, 10s trim).

## Next

- Mutations of AUC=1.0 hits (read×inversion, need−speech blends)
- External-only discovery pass on 42 clips
- QC gate: block ensemble when `peak_over_words` or `lex_minus_clip` fire
