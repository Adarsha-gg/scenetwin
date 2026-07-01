# Parallel research: TRIBE-guided frame sampling
## Scope
Local-only pass over existing uniform vs TRIBE ADQA frame directories, cached timing/window/router CSVs, and cached ADQA aggregate outputs. No external APIs were called. The requested `context.md` and `plan.md` were not present in the repo, so this report uses the explicit task plus local artifacts as source of truth.
## Inputs and artifacts
- `output/scenetwin_timing_20clip/adqa_frames` (frames_dir)
- `output/scenetwin_timing_20clip/need/coarse_need_windows.csv` (need_csv)
- `cursor/research/output/tribe_blind_spot_windows.csv` (router_csv)
- `output/scenetwin_timing_20clip/adqa_q-claude-haiku-4-5_g-claude-haiku-4-5/aggregate_results.csv` (uniform_adqa_aggregate)
- `output/scenetwin_timing_20clip/adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5/aggregate_results.csv` (tribe_adqa_aggregate)
- Output artifacts: `cursor/research/output/parallel_research/frame_sampling/`
## Findings
1. **TRIBE sampling does target more high-gap need windows, but only modestly.** Across 18 clips with both frame sets, uniform frames landed in `need_score >= 0.4` windows at 57.4%; TRIBE frames landed there at 70.8%. Mean per-clip high-need frame-rate delta was +12.0%.
2. **Typed router overlap also improves only slightly.** Against `tribe_blind_spot_windows.csv` routed windows (`layout_replay_or_scene_cue` or `action_state_or_agent_cue`), uniform frame overlap was 30.2% and TRIBE frame overlap was 30.3%; mean per-clip routed-window delta was +1.3%.
3. **Action-window coverage does not improve overall.** On 9 clips with an `action_state_or_agent_cue` router window, uniform frame overlap was 20.9%; TRIBE overlap was 18.6%. Clip 08 improves locally, but the aggregate action-route result does **not** yet show that current TRIBE sampling fixes the static-composition-over-temporal-action blind spot.
4. **Material differences exist, but budget parity is weak.** 5 clips met the material-difference rule (`>=20pp` frame-rate shift into high/routed windows, mean nearest-frame shift `>=0.60s`, or duplicate TRIBE timestamps). However, 17/18 TRIBE frame folders and 9/18 uniform folders contain fewer than the intended 8 frames, so comparisons are not fully budget matched.
5. **Cached ADQA scoring does not show a global ranking lift.** With the same cached Claude-Haiku questioner/grader, uniform ADQA has Spearman rho `0.801`, pairwise `49/54`, full-order `9/18`; TRIBE-frame ADQA has rho `0.782`, pairwise `53/54`, full-order `9/18`. This supports TRIBE sampling as a targeted coverage/triage change, not a proven aggregate leaderboard improvement.

## Review findings
- **Medium — frame-budget mismatch:** Existing `_tribe` directories contain only 89 frames vs 129 uniform frames, and 17/18 TRIBE clip folders are below `N_FRAMES=8`. Path: `output/scenetwin_timing_20clip/adqa_frames`; evidence: `cursor/research/output/parallel_research/frame_sampling/frame_sampling_overlap_by_clip.csv`.
- **Medium — temporal/action blind spot not solved:** Action-route overlap is lower for TRIBE than uniform (18.6% vs 20.9%) on the 9 action-route clips. Path: `cursor/research/output/tribe_blind_spot_windows.csv`; evidence: `high_gap_window_frame_counts.csv`.
- **Low — aggregate scorer lift not established:** Cached TRIBE-frame ADQA improves pairwise wins (53/54 vs 49/54) but has lower rho (0.782 vs 0.801). Path: `output/scenetwin_timing_20clip/adqa_tribe_q-claude-haiku-4-5_g-claude-haiku-4-5/aggregate_results.csv`.

## Materially different clips (top local examples)
| clip | category | uniform n | TRIBE n | high-gap frame-rate delta | routed frame-rate delta | action delta | mean nearest shift | notes |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 16 | Pets & Animals | 8 | 5 | +35.0% | 0.000 | 0.000 | 0.30s | TRIBE frame dir has <8 frames; action-route clip |
| 13 | Sports | 8 | 6 | +29.2% |  |  | 0.30s | TRIBE frame dir has <8 frames |
| 08 | Travel | 7 | 5 | +22.9% | 0.114 | 0.114 | 0.20s | TRIBE frame dir has <8 frames; action-route clip |
| 00 | Food & Cooking | 7 | 4 | +21.4% | 0.107 |  | 0.16s | TRIBE frame dir has <8 frames |
| 09 | Sports | 8 | 8 | +0.0% | -0.250 |  | 0.33s | 2 duplicate TRIBE timestamps |

## Known temporal blind spot assessment
The prior limitation was that 8 evenly sampled frames can reward static composition and miss temporal actions such as pouring, sports motion, or fast state changes. The local evidence is mixed-to-negative for the current implementation: TRIBE sampling shifts frames toward coarse high-gap windows, which is a plausible mechanism for better temporal targeting, but it does **not** increase aggregate `action_state_or_agent_cue` coverage in the typed router. The available cached score comparison is also insufficient to claim a solved blind spot: aggregate rho decreases slightly while pairwise wins improve, and many TRIBE frame folders contain fewer than the intended 8 frames, reducing budget parity.

## Residual risks / limits
- No new LLM/CLIP/VLM scoring was run. Existing cached scoring can be summarized, but verifying whether the new frames improve question relevance requires re-running ADQA generation/grading or CLIP/video-native scoring.
- The TRIBE sampler in `tools/scenetwin_tribe_adqa.py` allocates frames over all need windows with a minimum-per-window rule; existing `_tribe` directories often have fewer than `N_FRAMES=8`, so current comparison is not fully budget matched.
- Local window overlap measures temporal coverage, not semantic correctness. A frame inside an action window may still miss the critical sub-action.
- `context.md` and `plan.md` requested by the task were absent, so no additional experiment-specific constraints could be applied.

## Next runnable command/batch
If API credentials are available and external calls are allowed later, rerun the matched ADQA comparison after deleting/regenerating incomplete TRIBE frame folders so both samplers use 8 frames:
```bash
python tools/scenetwin_tribe_adqa.py --question-model anthropic:claude-haiku-4-5-20251001 --grader-model anthropic:claude-haiku-4-5-20251001 --refresh-cache
```
For a local-only reproducibility check of this pass:
```bash
python cursor/research/parallel_frame_sampling_analysis.py
```

## Artifact index
- `cursor/research/output/parallel_research/frame_sampling/frame_sampling_overlap_by_clip.csv` — per-clip frame timestamp overlap/coverage metrics.
- `cursor/research/output/parallel_research/frame_sampling/high_gap_window_frame_counts.csv` — per-high-window uniform vs TRIBE frame counts.
- `cursor/research/output/parallel_research/frame_sampling/materially_different_clips.csv` — clips with material timestamp/coverage shifts.
- `cursor/research/output/parallel_research/frame_sampling/cached_adqa_uniform_vs_tribe_scores.csv` — cached per-tier ADQA score comparison; no re-scoring.
- `cursor/research/output/parallel_research/frame_sampling/summary.json` — machine-readable summary.
