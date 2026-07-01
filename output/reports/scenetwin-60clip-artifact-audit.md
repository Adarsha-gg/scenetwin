# SceneTwin 60-Clip Artifact Audit

Date: 2026-06-19

## Verdict

The 60-clip external evaluation artifacts were **recovered from GitHub remote branch** `origin/agent-loop/claude-round-70` after refreshing that remote-tracking branch.

The key source file is now restored locally:

- `cursor/output/external_ensemble_eval.csv`

## Verified recovered data

`cursor/output/external_ensemble_eval.csv` contains:

- 240 scored rows
- 60 unique `video_id` clips
- 4 tiers per clip: `tier0_cross`, `tier1_vatex_short`, `tier2_vatex_long`, `tier3_va11y`
- paired summary in `cursor/output/external_ensemble_eval.json`

Recovered headline from the JSON:

- CLIP+ADQA ensemble Spearman ρ = 0.8731713300938145
- 30/60 fully ordered clips
- 173/180 T3-vs-lower pairwise wins
- ADQA-only ρ = 0.7851460012050728
- CLIP-only ρ = 0.6313563795013782

## Restored files

Restored from `origin/agent-loop/claude-round-70`:

- `cursor/output/external_ensemble_eval.csv`
- `cursor/output/external_ensemble_eval.json`
- `cursor/output/vatex60/vatex60_ensemble_eval.csv`
- `cursor/output/vatex60/vatex60_ensemble_eval.json`
- `cursor/output/fake_rung_analysis.json`
- `cursor/output/corrected_ladder_robustness.json`
- `cursor/output/claim_level_gate.json`
- `cursor/output/gate_summary.json`
- `cursor/output/halluc_gate/halluc_gate.csv`
- `cursor/output/claim_gate/claims.csv`
- `cursor/pipeline/external_ensemble_eval.py`
- `cursor/pipeline/vatex60_eval.py`
- `cursor/pipeline/corrected_ladder_robustness.py`
- `cursor/pipeline/fake_rung_analysis.py`
- `cursor/pipeline/selective_audit.py`
- `cursor/pipeline/gate_outcome.py`
- recovered 2026-06 finding pages in `cursor/findings/`
- recovered paper drafts in `output/reports/paper-A-draft.md`, `paper-B-draft.md`, `paper-ad-safety-gate.md`
- recovered wiki research pages for external validation, baselines, statistical power, TRIBE role/ROI/router, VLM-as-judge, and paper outline/corpus

## Search trail

Initial local-only search did not find the row-level CSV because the local remote-tracking branch was stale. A read-only `git ls-remote` showed GitHub had a newer `agent-loop/claude-round-70` commit (`8a4139a2efe4b05d3085add18786e7e9686b728b`). After fetching that branch, `git log --all --name-only` exposed the missing artifacts, including `cursor/output/external_ensemble_eval.csv`.

## Paper-use rule

The 60-clip claims are no longer unsupported by missing files, but they still need normal paper hygiene before citation:

1. cite the restored CSV/JSON and exact commit/branch provenance;
2. rerun the relevant scripts where dependencies/API access permit;
3. use precise wording: `173/180 T3-vs-lower pairwise wins`, not vague “all pairwise wins.”
