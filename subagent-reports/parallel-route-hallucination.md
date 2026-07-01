# Parallel Route Hallucination Gate

## Scope

Local-only EXPERIMENT 2 pass. `context.md` and `plan.md` were not present in the project root when checked, so this run used the task text and cached local artifacts as the contract. No external APIs were called.

## Inputs

- `cursor/output/halluc_gate/halluc_gate.csv`
- `cursor/output/hallucination_gate.json`
- `cursor/output/relational_hallucination_probe_set/probes.csv`
- `cursor/research/output/tribe_blind_spot_clip_summary.csv`
- `cursor/research/output/tribe_blind_spot_windows.csv`
- `cursor/research/output/tribe_blind_spot_cases.csv`

## Outputs

- Report: `output/reports/parallel-research-route-hallucination-gate.md`
- Artifacts: `cursor/research/output/parallel_research/hallucination_gate/`
  - `joined_clip_rows.csv`
  - `route_summary.csv`
  - `dominant_type_summary.csv`
  - `category_summary.csv`
  - `route_category_summary.csv`
  - `case_summary.csv`
  - `swap_class_summary.csv`
  - `probe_type_summary.csv`
  - `tribe_predictor_auc.csv`
  - `summary.json`
- Repro script: `cursor/research/parallel_route_hallucination_gate.py`

## Findings

- Join succeeded for all hallucination-gate clips: 60/60 by `video_id`; no unmatched hallucination clips.
- Overall cached gate reproduced the prior summary: mean CLIP hallucination drop 0.0369, paraphrase drop 0.0077, hallucination-specific CLIP margin 0.0292; mean ADQA hallucination drop 0.1683 with 17/60 ADQA-blind clips.
- TRIBE top route stratifies the gate but does not cleanly predict it alone:
  - `action_state_or_agent_cue` top windows had the largest mean CLIP hallucination drop (0.0407) and CLIP-specific margin (0.0325).
  - `layout_replay_or_scene_cue` had the lowest ADQA blind rate (0.1923).
  - `static_ad_ok_low_gap` still showed nonzero CLIP hallucination drops (0.0361), so low TRIBE gap is not a safe negative gate.
- Simple high-gap AUCs are modest:
  - Top-quartile CLIP hallucination drop: best AUC 0.6593 from mean visual gap; max visual gap AUC 0.6548 with recall@top20% 0.4667.
  - Top-quartile CLIP-specific margin: best AUC 0.6178 from mean visual gap.
  - ADQA detected: best AUC 0.5979 from mean agent-action gap.
  - Top-quartile ADQA drop: best AUC 0.6519 from action-state/agent-cue route peak.

## Interpretation

TRIBE route/high-gap is best treated as a routing or triage lens for hallucination-sensitive review, not a standalone hallucination-risk score. Route/category cells are informative but small, so claims should remain descriptive unless rerun on a larger set.

## Validation

Commands run:

```bash
python cursor/research/parallel_route_hallucination_gate.py
python cursor/research/parallel_route_hallucination_gate.py && python -m py_compile cursor/research/parallel_route_hallucination_gate.py && python - <<'PY'
import json, csv
p='cursor/research/output/parallel_research/hallucination_gate/summary.json'
data=json.load(open(p,encoding='utf-8'))
assert data['join']['joined_rows']==60
assert not data['join']['unmatched_hallucination_video_ids']
rows=list(csv.DictReader(open('cursor/research/output/parallel_research/hallucination_gate/tribe_predictor_auc.csv',encoding='utf-8')))
assert rows and {'label','feature','auc'}.issubset(rows[0])
print('validated route hallucination artifacts:', data['join']['joined_rows'], 'joined rows;', len(rows), 'predictor rows')
PY
```

Validation output: `validated route hallucination artifacts: 60 joined rows; 110 predictor rows`.
