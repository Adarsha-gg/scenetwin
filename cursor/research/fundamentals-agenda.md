# Fundamentals research agenda

**Goal:** Challenge and rebuild SceneTwin from first principles — not demo polish, not ρ sweeps.

## What we question

1. **Four-tier GT** — Is pro AD always best? (clip_00 cross-video, clip_12 tier inversion)
2. **Spearman-only eval** — Pairwise wins, full-order rate, LOO stability, violation rate matter too
3. **18-clip benchmark** — Download new VATEX×VideoA11y overlap clips and test tier ordering cold
4. **TRIBE = risk forecast only** — Need routing, category profiles, AD length recommender, slot alignment

## Scripts (`cursor/fundamentals/`)

| Script | Purpose |
|--------|---------|
| **`ground_up_reframe.py`** | Recompute ensemble from v4, challenge tier GT, TRIBE router AUC |
| **`regime_aware_audit.py`** | Two-stage auditor implementation + consensus GT |
| `acquire_external_clip.py` | Download new clip from `vatex_overlap.json` |
| `score_external_clip.py` | Score tiers on external clips without ADQA |
| `eval_suite.py` | Multi-metric report (τ, pairwise, LOO, perm p) |
| `challenge_assumptions.py` | Test confounds and redundancies |
| `tribe_usecase_lab.py` | 7 TRIBE use-case experiments |

## Loop v6 rotation

`loop_worker.py` → **fundamentals_v6**: ground_up → regime_aware → challenge → eval_suite → tribe_lab (+ papers every 2nd tick)

## Thesis doc

**`cursor/research/GROUND-UP-THESIS.md`** — honest numbers and reframed claim.

## Next fundamentals to build

- [ ] Frame extraction + lightweight CLIP on external clips (no Colab)
- [ ] Counterfactual AD dataset: generate P_AD candidates, score with TRIBE gap
- [ ] MAVERIX modality-dependence: questions requiring audio+video
- [ ] LVOmniBench-style long-form segments (>60s)
- [ ] Human rubric correlation (VideoA11y 6-dim with VLM judge)

## Outputs

- `cursor/fundamentals/output/` — CSV reports
- `cursor/data/external_clips/` — downloaded clips + registry.jsonl
- `cursor/findings/fundamentals-*.md` — readable summaries
