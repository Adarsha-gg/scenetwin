# SceneTwin/TRIBE Local Mining Pass — 25 New Research Ideas

Scope: read-only mining pass over `README.md`, `CLAUDE.md`, `wiki/index.md`, `wiki/log.md`, TRIBE finding/wiki pages, and local `cursor/research/output` CSV/JSON summaries. These ideas deliberately avoid restating existing claims (TRIBE as clip-level triage, blind-spot router, ROI localization, surgical matched-question gain) and instead propose next validation/use directions.

## 1. TRIBE-guided frame sampling for ADQA
- **Evidence/premise:** Live frame sampling can miss temporal action and cause wrong scoring (`wiki/log.md`, 2026-05-13 live-demo entry); TRIBE exposes time-localized high-gap windows (`wiki/research/scenetwin-tribe-blind-spot-router.md`; `cursor/research/output/tribe_blind_spot_windows.csv`).
- **Validation experiment:** Replace uniform 8-frame sampling with top-TRIBE-window sampling on the 60 external clips; rerun ADQA questions or reuse frame-grounded question generation on matched windows.
- **Success metric:** Fewer T3 pairwise losses and higher corrected 3-tier full-order rate vs uniform frames; especially on clips with high `top1_vs_uniform`.
- **Likely artifact path:** `cursor/research/tribe_guided_frame_sampling.py`, `cursor/research/output/tribe_guided_frame_sampling.csv`, `wiki/research/scenetwin-tribe-frame-sampling.md`.
- **Risk/confound:** May overfit to TRIBE temporal peaks and under-sample context; needs same number of frames and same grader budget.

## 2. Dynamic AD insertion budget from temporal concentration
- **Evidence/premise:** Router summary has `top1_share`, `uniform_null`, and `top1_vs_uniform` (`cursor/research/output/tribe_blind_spot_clip_summary.csv`); existing route counts identify moment-level authoring, but not a budget policy (`wiki/research/scenetwin-tribe-blind-spot-router.md`).
- **Validation experiment:** Allocate 0/1/2/3 AD insertion slots by `top1_vs_uniform` and compare generated AD against fixed-length generic AD.
- **Success metric:** Matched ADQA improvement per added word; target > generic AD at equal or lower word count.
- **Likely artifact path:** `cursor/research/tribe_dynamic_ad_budget.py`, `cursor/research/output/tribe_dynamic_ad_budget.csv`.
- **Risk/confound:** Word-count and verbosity can masquerade as improvement; enforce equal token budgets.

## 3. Scene-vs-action contrastive question templates
- **Evidence/premise:** Scene/action peaks diverge in 31/60 external clips and correlations are low in 17/60 (`wiki/research/scenetwin-tribe-router-validation.md`); window rows label `dominant_type`.
- **Validation experiment:** Generate paired ADQA questions: one scene-layout, one agent/action for clips with peak-apart > 0; test whether TRIBE-selected type is the harder/unanswered one for generic AD.
- **Success metric:** Larger gap-targeted-vs-generic delta on peak-divergent clips than non-divergent clips.
- **Likely artifact path:** `cursor/research/tribe_scene_action_contrast_questions.py`.
- **Risk/confound:** VLM question generator may encode TRIBE label in wording; blind the grader to route labels.

## 4. TRIBE-powered “evidence replay” reviewer UI benchmark
- **Evidence/premise:** Product route includes replay/keyframe surfaces (`wiki/research/scenetwin-tribe-blind-spot-router.md`); highest-gap windows are known (`cursor/research/output/tribe_blind_spot_windows.csv`).
- **Validation experiment:** Simulate reviewer workload: compare reviewing full clip vs only top TRIBE windows for finding missing AD facts.
- **Success metric:** Recall of known matched-target question failures at 30–50% of watch time.
- **Likely artifact path:** `output/reports/tribe_evidence_replay_eval.md`, later `web/pages/tribe.jsx` if implemented.
- **Risk/confound:** Offline simulation may not predict human reviewer behavior; needs human or VLM proxy caveat.

## 5. TRIBE conflict detector for soundtrack-dominant clips
- **Evidence/premise:** Control/language/auditory gaps are available (`tribe_blind_spot_windows.csv`, `tribe_roi_gap_per_clip.csv`); router includes `audio_language_confound_check` cases (`wiki/research/scenetwin-tribe-blind-spot-router.md`).
- **Validation experiment:** Identify windows where control gap is high relative to visual gap; test if ADQA/CLIP errors are due to audio-language confounds rather than visual omission.
- **Success metric:** Higher false-positive rate of TRIBE routes or lower gap-targeted gains in high-control windows; a guardrail threshold that preserves matched gains.
- **Likely artifact path:** `cursor/research/tribe_audio_confound_guardrail.py`.
- **Risk/confound:** Control gap may reflect encoder noise, not speech; pair with transcript speech density if available.

## 6. ROI-profile clustering for access genres
- **Evidence/premise:** ROI localization shows >54% clip x ROI interaction, dominant lost region varies (`wiki/research/scenetwin-tribe-roi-localization.md`); per-ROI CSV has 8 visual/control columns.
- **Validation experiment:** Cluster 78 clips by normalized ROI gap vector and compare clusters to content categories and AD failure types.
- **Success metric:** Clusters predict which AD prompt template wins better than YouTube category alone.
- **Likely artifact path:** `cursor/research/tribe_roi_profile_clusters.py`, `output/charts/tribe_roi_profile_clusters.png`.
- **Risk/confound:** n=78 is small for clustering; require stability across bootstraps.

## 7. Category-conditioned TRIBE thresholds
- **Evidence/premise:** Scene-minus-agent differs by category (`wiki/research/scenetwin-tribe-roi-localization.md`); external categories include How-to, Entertainment, Sports, etc. (`tribe_blind_spot_clip_summary.csv`).
- **Validation experiment:** Learn per-category thresholds for `mean_visual_gap` or `top1_vs_uniform` to route only unusually high-gap clips within category.
- **Success metric:** Better precision at fixed recall for T3 losses or matched-question wins vs global threshold.
- **Likely artifact path:** `cursor/research/tribe_category_thresholds.py`.
- **Risk/confound:** Some categories have low n; use leave-one-category-out sanity checks.

## 8. TRIBE-informed tie handling for near-margin external losses
- **Evidence/premise:** External T3 losses include many within-margin ties (`wiki/index.md` external T3 losses entry); TRIBE gap flags ensemble misordered clips externally (`cursor/findings/tribe-clip-level-triage.md`).
- **Validation experiment:** When SceneTwin score margin is tiny and TRIBE gap high, emit “needs review/tie” rather than forced rank.
- **Success metric:** Reduced harmful false wins with minimal coverage loss; risk-coverage curve improves over score-margin alone.
- **Likely artifact path:** `cursor/research/tribe_margin_tie_policy.py`.
- **Risk/confound:** Could become selective abstention redux; must beat existing reference-free min-margin confidence.

## 9. Per-window CLIP residual audit
- **Evidence/premise:** CLIP helps controlled visual-object content but is weak externally (`wiki/research/scenetwin-signal-decomposition` in index); TRIBE supplies windows/routes.
- **Validation experiment:** Compute CLIP grounding only on frames from high-gap windows vs low-gap windows; test if residual disagreement localizes to TRIBE windows.
- **Success metric:** High-gap-window CLIP residual predicts matched ADQA misses better than full-clip CLIP.
- **Likely artifact path:** `cursor/research/tribe_window_clip_residual.py`.
- **Risk/confound:** Frame extraction alignment may be noisy; use coarse 3s windows only.

## 10. Negative-prompt generator: “do not waste words on low-gap windows”
- **Evidence/premise:** Router has 218 `static_ad_ok_low_gap` windows (`wiki/research/scenetwin-tribe-blind-spot-router.md`); global pro AD priority matching was negative (`wiki/research/scenetwin-tribe-router-validation.md`).
- **Validation experiment:** Generate AD with explicit instruction to skip low-gap windows and spend words only on high-gap windows; compare to generic and positive-only TRIBE prompt.
- **Success metric:** Equal or better matched ADQA with fewer words and no drop on whole-question averages.
- **Likely artifact path:** `cursor/research/tribe_skip_low_gap_generation.py`.
- **Risk/confound:** Skipping context may hurt coherence; include human-readable coherence judge.

## 11. TRIBE-hard subset for benchmark construction
- **Evidence/premise:** Existing paper benchmark has external 60 and in-bench 18; TRIBE ranks hard gaps and metric failures (`cursor/findings/tribe-clip-level-triage.md`, `tribe_blind_spot_clip_summary.csv`).
- **Validation experiment:** Build a 20-clip “TRIBE-hard” evaluation subset from top visual gap/concentration, then compare metrics and VLM judges.
- **Success metric:** Larger separation between SceneTwin and generic VLM-as-judge or more diagnostic failure diversity than random 20 clips.
- **Likely artifact path:** `cursor/research/output/tribe_hard_subset.json`, `wiki/research/scenetwin-tribe-hard-benchmark.md`.
- **Risk/confound:** Selecting on TRIBE can bias claims; present as stress test, not headline population estimate.

## 12. Cross-modal redundancy score using transcript answerability
- **Evidence/premise:** MDV found audio leak is small overall but narration genres leak up to 15% (`wiki/index.md` MDV entry); TRIBE distinguishes visual vs control gaps.
- **Validation experiment:** Combine transcript-answerability with low TRIBE visual gap to identify clips where AD can be shorter without losing access.
- **Success metric:** Short AD generated for redundant clips retains ADQA score while reducing words by ≥20%.
- **Likely artifact path:** `cursor/research/tribe_audio_redundancy_policy.py`.
- **Risk/confound:** Transcript-answerability may miss non-speech audio cues; avoid overclaiming “no AD needed.”

## 13. Motion-region failure audit despite low mean MT+
- **Evidence/premise:** Motion MT+ mean gap is low in ROI localization (`wiki/research/scenetwin-tribe-roi-localization.md`), yet live failure involved temporal action (`wiki/log.md`, 2026-05-13 frame sampling blindspot).
- **Validation experiment:** Inspect clips where MT+ is high relative to the clip’s own visual ROI profile, not absolute mean; compare to temporal-action ADQA failures.
- **Success metric:** Relative MT+ z-score predicts action-specific question misses better than absolute MT+ gap.
- **Likely artifact path:** `cursor/research/tribe_relative_motion_audit.py`.
- **Risk/confound:** Glasser MT+ proxy may be weak after fsaverage projection; treat as exploratory.

## 14. Retrosplenial/PPA layout prompt ablation
- **Evidence/premise:** Largest ROI gaps are retrosplenial/spatial and scene PPA (`wiki/research/scenetwin-tribe-roi-localization.md`); router route `layout_replay_or_scene_cue` exists.
- **Validation experiment:** For high RSC/PPA clips, compare generic AD vs prompt explicitly requiring spatial layout/scene gist vs agent/action prompt.
- **Success metric:** Layout prompt wins only on high scene/spatial ROI clips, showing type-specific control.
- **Likely artifact path:** `cursor/research/tribe_layout_prompt_ablation.py`.
- **Risk/confound:** Prompt may simply be more detailed; equalize word budget and judge matched layout questions.

## 15. TRIBE uncertainty from hemisphere disagreement
- **Evidence/premise:** Counterfactual CSV stores `video_mean_lh/rh` and `video_ad_mean_lh/rh` (`tribe_counterfactual_external_per_clip.csv`); existing claims do not use lateralization.
- **Validation experiment:** Compute left-right disagreement features and test whether high disagreement marks unreliable TRIBE routes or audio-language confounds.
- **Success metric:** Hemisphere disagreement predicts cases where TRIBE-targeted AD does not beat generic.
- **Likely artifact path:** `cursor/research/tribe_hemisphere_uncertainty.py`.
- **Risk/confound:** Mean hemisphere values are crude summaries; tensor-level lateralization would be better.

## 16. TRIBE route consistency under temporal jitter
- **Evidence/premise:** HRF lag sensitivity showed 0s lag best on two clips (`wiki/index.md`); router uses 3s windows, but stability under jitter is not reported.
- **Validation experiment:** Recompute window routes after shifting TR indices/windows ±1 TR or ±1s and measure route agreement.
- **Success metric:** Top-window route agreement >80%; unstable windows marked low-confidence.
- **Likely artifact path:** `cursor/research/tribe_route_jitter_stability.py`.
- **Risk/confound:** Requires tensor-level recomputation or careful approximation; avoid changing existing tensors.

## 17. TRIBE route confidence calibration
- **Evidence/premise:** Window rows include `dominance_margin`, `visual_minus_control`, and route (`tribe_blind_spot_windows.csv`); current validation reports aggregate gains.
- **Validation experiment:** Predict matched-question win probability from dominance margin and visual-minus-control.
- **Success metric:** Monotonic calibration curve: top confidence quartile has materially higher win rate than bottom quartile.
- **Likely artifact path:** `cursor/research/tribe_route_confidence.py`, `output/charts/tribe_route_calibration.png`.
- **Risk/confound:** Many ties in judge outputs reduce resolution; use paired sign tests.

## 18. Clip-level “why score is unreliable” explanations
- **Evidence/premise:** TRIBE flags clip-level metric failures but not continuous rho (`cursor/findings/tribe-clip-level-triage.md`); router has typed windows/cases.
- **Validation experiment:** Generate automatic explanations combining high gap, dominant ROI/type, and low score margin; have VLM/human rate if explanation identifies actual failure mode.
- **Success metric:** Explanations for failed clips are rated more specific/actionable than score-margin-only explanations.
- **Likely artifact path:** `output/reports/tribe_failure_explanations.md`, `cursor/research/output/tribe_failure_explanations.json`.
- **Risk/confound:** Explanation quality is subjective; separate factual evidence from generated prose.

## 19. TRIBE-guided reviewer question budget
- **Evidence/premise:** ADQA uses questions; surgical TRIBE ADQA target beats generic (`wiki/research/scenetwin-tribe-router-validation.md`).
- **Validation experiment:** Allocate more ADQA questions to high-gap windows and fewer to low-gap clips under fixed total question budget.
- **Success metric:** Same or better failure recall with 30–50% fewer questions than uniform 5-per-clip allocation.
- **Likely artifact path:** `cursor/research/tribe_adqa_budget_allocator.py`.
- **Risk/confound:** Question generator and grader dependence; include no-TRIBE uncertainty baseline.

## 20. Early-exit “low pressure” policy validation
- **Evidence/premise:** Router inventory has 26 low_gap_skip cases and many static low-gap windows (`wiki/research/scenetwin-tribe-blind-spot-router.md`).
- **Validation experiment:** For low-gap clips/windows, test whether cheap CLIP-only or fewer ADQA questions matches full ensemble decisions.
- **Success metric:** ≥95% agreement with full SceneTwin on low-pressure subset while reducing scoring cost.
- **Likely artifact path:** `cursor/research/tribe_low_pressure_early_exit.py`.
- **Risk/confound:** Low-gap does not mean low audit risk; enforce conservative false-negative bound.

## 21. TRIBE-vs-VLM disagreement mining
- **Evidence/premise:** VLM-as-judge disagrees with tier ladder (`wiki/index.md`); TRIBE target beats VLM target on matched evidence (`wiki/research/scenetwin-tribe-router-validation.md`).
- **Validation experiment:** Find clips where VLM priority and TRIBE route disagree maximally; manually/VLM inspect which missing visual facts each surfaces.
- **Success metric:** Taxonomy of complementary failure modes plus cases where TRIBE finds non-obvious spatial/action gaps.
- **Likely artifact path:** `cursor/research/output/tribe_vlm_disagreement_cases.md`.
- **Risk/confound:** Case-study evidence can be cherry-picked; predefine top-k by cosine/disagreement.

## 22. TRIBE-informed hallucination gate anchor selection
- **Evidence/premise:** Hallucination gate works best with a clip-relevant anchor; no-anchor is weak (`wiki/index.md` safety gate entries). TRIBE identifies high visual-need windows.
- **Validation experiment:** Build anchor claims/questions only from top TRIBE windows, then test grounding-drop hallucination gate vs uniform/random anchors.
- **Success metric:** Higher AUC or recall at 10% FPR on hand-authored fabrications.
- **Likely artifact path:** `cursor/research/tribe_hallucination_anchor_selection.py`.
- **Risk/confound:** Fabrications may not target TRIBE windows; include matched and unmatched fabrication sets.

## 23. ROI-aware OCR/text coverage trigger
- **Evidence/premise:** OCR coverage layer exists for visible text (`wiki/index.md` OCR coverage entry); TRIBE high scene/spatial/V1 gaps may mark title cards or signs.
- **Validation experiment:** Trigger OCR checks only when early V1/scene gaps spike and compare to always-on OCR on external clips with visible text.
- **Success metric:** Same OCR miss recall with fewer OCR calls/false alarms.
- **Likely artifact path:** `cursor/research/tribe_ocr_trigger.py`.
- **Risk/confound:** TRIBE was not trained for text; high V1 gap may reflect generic visual change.

## 24. Personalized access profile simulation
- **Evidence/premise:** ROI profile carries clip-specific structure invisible to scalar (`wiki/research/scenetwin-tribe-roi-localization.md`); existing work treats all users identically.
- **Validation experiment:** Simulate profiles weighting scene/spatial vs agent/action needs and test whether route ordering changes AD prompt choices.
- **Success metric:** Different profiles select meaningfully different windows/prompts while preserving base ADQA adequacy.
- **Likely artifact path:** `cursor/research/tribe_access_profile_simulation.py`.
- **Risk/confound:** No real user labels; must frame as simulation until user study.

## 25. External TRIBE tensor manifest health audit
- **Evidence/premise:** Tensors exist for 78 clips under `cursor/research/output/tribe_tensors/`; CSVs derive many downstream claims. Some counterfactual rows have unusual values (e.g. alignment_cosine `0.0` sample in `tribe_counterfactual_external_per_clip.csv`).
- **Validation experiment:** Validate tensor dimensions, finite values, hemisphere symmetry, category/clip ID joins, and derived CSV reproducibility from tensors.
- **Success metric:** 100% manifest rows reproducible or clearly quarantined; downstream metrics unchanged after quarantine.
- **Likely artifact path:** `cursor/research/tribe_tensor_health_audit.py`, `output/reports/tribe_tensor_health_audit.md`.
- **Risk/confound:** Audit may uncover data issues that require revising claims; high value but schedule risk.

## Files Retrieved
1. `README.md` (lines 1-58) — project entry points and current TRIBE-as-cached-risk framing.
2. `CLAUDE.md` (lines 1-112) — project operating context and known killed TRIBE branches.
3. `wiki/index.md` (lines 1-200) — canonical index of existing TRIBE claims and negative results.
4. `wiki/log.md` (lines 1-200) — chronology of TRIBE web work, frame-sampling blindspot, and paper-push findings.
5. `cursor/findings/tribe-clip-level-triage.md` (lines 1-55) — existing claim that TRIBE is clip-level triage, not rho booster.
6. `wiki/research/scenetwin-tribe-role-analysis.md` (lines 1-160) — measured null calibration, binary triage, counterfactual external closure.
7. `wiki/research/scenetwin-tribe-roi-localization.md` (lines 1-123) — ROI gap localization and clip x ROI interaction evidence.
8. `wiki/research/scenetwin-tribe-blind-spot-router.md` (lines 1-137) — typed 3s windows, route inventory, priority cases.
9. `wiki/research/scenetwin-tribe-router-validation.md` (lines 1-97) — matched-target validation and negative professional-priority result.
10. `wiki/research/scenetwin-tribe-native-analysis.md` (lines 1-134) — original route counts and TRIBE feature associations.
11. `cursor/research/output/*tribe*.csv/json` selected summaries — inspected schemas/samples for blind-spot, ROI, calibration, counterfactual, and decomposition data.

## Acceptance Report
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Wrote only the requested report at subagent-reports/tribe-local-ideas.md; did not edit source/wiki/data files."
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "Each of 25 ideas includes title, local evidence/premise with file refs, validation experiment, success metric, likely artifact path, and risk/confound."
    }
  ],
  "changedFiles": [
    "subagent-reports/tribe-local-ideas.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "ls/find/read targeted project and TRIBE files",
      "result": "passed",
      "summary": "Mapped README, CLAUDE, wiki index/log, TRIBE finding/wiki pages, and output summaries."
    },
    {
      "command": "python CSV schema/sample inspection without pandas",
      "result": "passed",
      "summary": "Inspected columns and sample rows for key TRIBE CSV outputs using Python csv/json modules."
    }
  ],
  "validationOutput": [
    "Report file was written to subagent-reports/tribe-local-ideas.md with 25 numbered ideas and required fields."
  ],
  "residualRisks": [
    "Ideas are research proposals, not executed experiments; several require new model/ADQA/VLM runs.",
    "Line-level citations in the report are file-level/section refs because the task prioritized local mining and synthesis over citation extraction."
  ],
  "noStagedFiles": true,
  "notes": "No source files were modified."
}
```
