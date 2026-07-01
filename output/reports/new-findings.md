---
title: New Findings — 100 TRIBE/SceneTwin Research Ideas and Validation Loops
category: research
status: working research backlog
created: 2026-06-23
updated: 2026-06-23
sources:
  - README.md
  - CLAUDE.md
  - wiki/log.md
  - wiki/index.md
  - wiki/research/scenetwin-tribe-role-analysis.md
  - wiki/research/scenetwin-tribe-blind-spot-router.md
  - wiki/research/scenetwin-tribe-router-validation.md
  - cursor/findings/tribe-clip-level-triage.md
  - output/reports/paper-scenetwin-audit-framework.md
  - output/reports/paper-B-draft.md
  - cursor/research/tribe-v2-deep-dive.md
  - cursor/research/papers/INDEX.md
  - cursor/research/papers/CROSS-PAPER-SYNTHESIS.md
  - cursor/research/fundamentals-agenda.md
  - cursor/research/output/tribe_blind_spot_windows.csv
  - cursor/research/output/tribe_blind_spot_clip_summary.csv
  - cursor/research/output/tribe_blind_spot_cases.csv
  - cursor/research/output/tribe_surgical_adqa_perq.csv
  - cursor/research/output/tribe_crossjudge_gpt5_perq.csv
  - cursor/research/output/tribe_necessity_rematch_perq.csv
  - cursor/output/tribe_scene_model_probe_routing/summary.json
  - cursor/output/tribe_matched_scene_model_challenge/summary.json
---

# New Findings — 100 TRIBE/SceneTwin Research Ideas and Validation Loops

This file is the requested running `new-findings.md` report. These are **candidate findings / research moves**, not validated claims. Each item includes a validation path so weak ideas can die quickly.

## Current evidence anchors

- SceneTwin's corrected paper claim is an audit stack: CLIP+ADQA scoring, safety gates, and TRIBE as **clip-level review triage**, not a ranker (`output/reports/paper-scenetwin-audit-framework.md`).
- TRIBE cannot lift within-clip rank correlation when reduced to a per-clip scalar, but it can flag clips likely to fail ADQA: external ADQA-only failures AUC 0.79, p=0.0018 (`cursor/findings/tribe-clip-level-triage.md`).
- The Neural Blind Spot Map already has scale: 334 windows across 78 clips, 236 external windows, with routes `static_ad_ok_low_gap`=218, `layout_replay_or_scene_cue`=78, `action_state_or_agent_cue`=38 (`cursor/research/output/tribe_blind_spot_windows.csv`).
- External blind-spot structure is non-trivial: 17/60 external clips have scene/action temporal correlation <0.5, 31/60 have scene/action peaks at different timesteps, and mean top-1 concentration is 2.69× uniform (`wiki/research/scenetwin-tribe-blind-spot-router.md`).
- The strongest generative TRIBE result is surgical: gap-targeted AD improves matched questions more than unmatched ones, replicated with GPT-5 and Opus judge passes (`wiki/research/scenetwin-tribe-router-validation.md`).
- TRIBE vs transcript-armed VLM is not a clean superiority win; the honest claim is competitive, different target selection, and brain-grounded validity (`wiki/log.md`, 2026-05-30 entries).

## Actual local run #1 — cached-data findings (2026-06-23)

After the backlog, I ran `cursor/research/tribe_new_findings_local.py` with no API/GPU calls. Report: [`tribe-new-findings-local-run.md`](tribe-new-findings-local-run.md). Outputs: `cursor/research/output/new_findings_local/`.

New empirical/guardrail findings from that run:

1. **In-benchmark TRIBE AUC=1.00 is pilot evidence after feature-selection correction.** `mean_standard_slot_score` still gives AUC=1.00 and top-2 p=0.0065, but exact family-wise max-stat p across 14 plausible features is 0.0915. Use it as supporting evidence, not a standalone headline.
2. **External low-gap clips look safer, but not safe enough for automatic omission.** Bottom 25% by `max_visual_gap` has ADQA failure rate 0.067 and ensemble failure rate 0.000; top 25% has ADQA failure rate 0.200 and ensemble failure rate 0.133. This supports lower-review priority, not “skip AD blindly.”
3. **Route confidence is not calibrated.** `dominance_margin`, `visual_minus_control`, and `top1_vs_uniform` do not reliably predict the size of matched-question improvement across Haiku/GPT-5/Opus cached runs. Do not expose them as probability-of-success in the UI yet.
4. **Current matched surgical gain is mostly scene/spatial.** In `tribe_surgical_adqa_perq.csv`, scene/spatial matched questions carry n=50, mean delta +0.150, 16W/2L/32T, p=0.0007. Face/action/visual-form cells are too small to claim equally validated route types.
5. **Tensor metadata is usable but needs caveats.** Manifest has 78/78 JSON files, no missing files, no bad vertex shapes, and all `audio_only_ok=True`, but 23 AD-response rows have `alignment_cosine <= 0.5` and 35 rows have P_AV/P_A temporal-length mismatch. Quarantine/mention before tensor-derived paper figures.

## Actual cached-data run #2 — more validation findings (2026-06-23)

Report: [`tribe-new-findings-round2.md`](tribe-new-findings-round2.md). Outputs: `cursor/research/output/new_findings_round2/`.

6. **Cross-judge matched-question lift survives cluster bootstrap.** Matched deltas: Haiku +0.167 CI [0.093,0.243], GPT-5 +0.113 CI [0.055,0.183], Opus17 +0.167 CI [0.036,0.333], Opus15 +0.306 CI [0.147,0.500]. Matched-minus-unmatched is positive too, but not equally strong in every run.
7. **Gap-targeted full-window AD gains are not explained by extra length alone.** Targeted AD is +5.3 words/clip on average and +0.080 ADQA, but Spearman(word delta, ADQA delta)=0.049; non-longer cases still average +0.050.
8. **Mean visual gap is the better external triage queue.** At 10/20/30% review budget, `mean_visual_gap` catches 2/3/4 of 10 ADQA failures; `max_visual_gap` catches 0/2/4.
9. **Low-pressure early exit should reduce review, not replace scoring.** Bottom third by max gap has ADQA fail 0.050 and ensemble fail 0.000, but CLIP-only remains too weak for replacement.
10. **The old `all4_fail` positives are not a strict-tie artifact.** One is a tier2/tier1 inversion and one is a T3-margin inversion; no positive is merely a tie.
11. **Simple/category confounds do not explain in-bench risk queue.** `mean_standard_slot_score` AUC=1.000; category sports-or-pets AUC=0.750; duration AUC=0.719; speech-density needs inverted direction and remains weaker.
12. **Low AD-response alignment quarantines P_AD/NCR claims, not AV-vs-A triage.** High-alignment external rows still have mean-gap AUC 0.650 vs ADQA fail; low-alignment rows have fail rate 0.286 and should be analyzed separately for AD-dependent TRIBE scores.

## Actual cached-data run #3 — ROI, VLM rematch, worksheet (2026-06-23)

Report: [`tribe-new-findings-round3.md`](tribe-new-findings-round3.md). Outputs: `cursor/research/output/new_findings_round3/`. Worksheet: [`tribe-review-worksheet.md`](tribe-review-worksheet.md).

13. **ROI/profile evidence is overwhelmingly scene/spatial.** External dominant ROI counts: retrosplenial 30, V1 17, scene PPA 9, lateral object 2, body EBA 1, higher visual 1. Body/face/motion/object claims are underpowered.
14. **Category-residual gap does not improve external ADQA-failure triage.** Raw mean visual gap AUC=0.672; category-residual AUC=0.646; category-z AUC=0.684. Do not spend time on category-normalized thresholds yet.
15. **Fair transcript-armed VLM rematch confirms conservative wording.** TRIBE/VLM target disagreement is 90.9%; TRIBE-vs-VLM all-question delta +0.020 CI [-0.002,+0.043], matched delta +0.065 CI [+0.017,+0.113]. Claim: competitive/different, not decisively superior.
16. **Review worksheet is now concrete.** Generated top 25 non-low-gap blind-spot cases with priority scores, windows, reasons, existing fail flags, and top router windows for human/VLM review.

## Actual cached-data/copy audit #4 — claim safety (2026-06-23)

Report: [`tribe-claims-audit.md`](tribe-claims-audit.md). Outputs: `cursor/research/output/new_findings_claims_audit/`.

17. **Claim matrix created.** Ten TRIBE claims now have status, safe wording, avoid wording, evidence, and source paths.
18. **Overclaim scan found 41 review hits.** Breakdown: AUC=1/no-caveat 19, TRIBE-improves-rho wording 4, beats/superior-to-VLM wording 7, calibration-layer wording 8, necessary wording 3. The scan is conservative and includes false positives, but it gives a concrete cleanup queue before paper/demo copy edits.
19. **Paper-safe core wording is now locked.** Use: “TRIBE is clip-level triage/router,” “pilot AUC=1 with n=2/family-wise p caveat,” “competitive/different vs VLM,” “scene/spatial route best validated,” and “future P_AD/NCR claims need low-alignment quarantine.”

## Actual cached-data run #5 — parallel experiment gauntlet (2026-06-23)

Reports: [`parallel-research-type-swapped.md`](parallel-research-type-swapped.md), [`parallel-research-route-hallucination-gate.md`](parallel-research-route-hallucination-gate.md), [`parallel-research-tribe-frame-sampling.md`](parallel-research-tribe-frame-sampling.md), [`parallel-research-cheap-baseline-gauntlet.md`](parallel-research-cheap-baseline-gauntlet.md), [`parallel-research-access-surface-triage.md`](parallel-research-access-surface-triage.md), [`parallel-research-blocked-next-steps.md`](parallel-research-blocked-next-steps.md). Outputs: `cursor/research/output/parallel_research/`.

20. **Cheap-baseline gauntlet is the strongest new support for TRIBE triage.** For corrected external ADQA failures, `accessibility_gap` reaches AUC=0.794 and survives within-category shuffling (p=0.003), beating category-only, transcript/speech, and duration/word-count baselines. This is now the cleanest external reviewer-defense result.
21. **Review-budget wording should use mean visual gap, not case priority.** `mean_visual_gap` catches 4/10 ADQA failures at 25% review budget and 5/10 at one-third; the case-priority non-low-gap queue is weaker. Use this as operational triage, not automatic skip/replacement.
22. **Low-gap remains a review-pressure reducer only.** Bottom third by max visual gap has ADQA fail rate 0.050 and ensemble fail rate 0.000, but CLIP-only replacement is still too weak for deployable “no AD needed” claims.
23. **Route-specific hallucination gate is descriptive, not detector-grade.** TRIBE joins 60/60 hallucination clips and stratifies gate strength modestly: action-route top windows have the largest CLIP hallucination drop, but the best simple high-gap AUC for top-quartile CLIP drop is only 0.659. Keep it as route-aware review context.
24. **Current TRIBE frame sampling should not be claimed as a temporal-action fix.** It increases high-need window coverage (70.8% vs 57.4%) but does not improve action-window coverage (18.6% vs 20.9%) and cached ADQA rho drops slightly (0.782 vs 0.801). Fix budget parity before another scoring run.
25. **Type-swapped prompt control is not yet a result.** No cache contains same-clip/same-question `generic`, `matched`, and `swapped` conditions. A future no-API JSONL batch now exists at `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl`.
26. **Access Surface OS mapping is ready for review workflow.** The router maps 334 windows to 218 static/low-pressure, 78 layout/keyframe, and 38 action-cue windows; top-25 reviewer cases now have surfaces, validation targets, fail flags, and blank reviewer fields.
27. **Lower-priority GPU/human items are explicitly gated.** Full text-extractor NCR needs approved HF-gated Llama + GPU; `P_silence` needs a method decision + GPU/media; BLV micro-study needs human-study approval. Do not silently spend credentials or recruit humans.

## 100 candidate findings and validation loops

| # | Candidate finding / idea | Validation loop | Pass signal | Primary local hook |
|---:|---|---|---|---|
| 1 | **TRIBE should become a window selector, not a score.** Use top visual-gap windows to decide where ADQA asks questions. | Compare generic ADQA vs TRIBE-window ADQA on truth-vs-lie candidates. | TRIBE-window questions catch more targeted lies at equal question budget. | `tribe_blind_spot_windows.csv`, `tribe_matched_scene_model_challenge.py` |
| 2 | **Scene/action split is the useful TRIBE axis.** Current scene/action peak divergence suggests a one-prompt AD is too blunt. | Generate separate scene-layout and agent-action AD variants per high-gap window. | Matched q lift is larger when prompt type matches dominant gap. | `dominant_type`, `route` columns |
| 3 | **Low-gap skip is an explicit product feature.** 218/334 windows route low-gap; SceneTwin can reduce unnecessary AD. | Simulate AD budget: omit low-gap windows, keep high-gap windows, grade against ADQA. | Same ADQA with fewer words/seconds or improved words-per-correct-answer. | `static_ad_ok_low_gap` rows |
| 4 | **TRIBE can route between concise cue and layout replay.** `layout_replay_or_scene_cue` windows should receive spatial summaries, not action verbs. | A/B prompt: layout-only vs generic AD on layout windows. | Layout prompts improve spatial_relation questions without hurting action questions. | `layout_replay_or_scene_cue` route |
| 5 | **TRIBE can route action-state cues separately.** Agent/action windows should prioritize who-does-what and state changes. | A/B action prompt on `action_state_or_agent_cue` windows. | Higher motion/action ADQA scores; no object-label verbosity inflation. | `action_state_or_agent_cue` route |
| 6 | **Use dominance margin as confidence.** High gap but tiny scene/action margin means ambiguous routing. | Bin windows by `dominance_margin` and test matched prompt lift by bin. | Lift monotonic in margin; low-margin windows abstain or ask VLM. | `dominance_margin` |
| 7 | **Top1 concentration is an authoring urgency score.** A concentrated gap means one moment carries most missing access. | Compare top-window-only vs full-window targeted AD by `top1_vs_uniform`. | Top-window-only works on high concentration; full-window needed otherwise. | `tribe_blind_spot_clip_summary.csv` |
| 8 | **Scene/action decorrelation predicts need for multi-part AD.** Clips with decorrelated peaks may need separate timing slots. | Split AD into scene pass + action pass only when `scene_agent_time_rho < .5`. | Better matched q lift on 17 decorrelated external clips. | `scene_agent_time_rho` |
| 9 | **Peak-apart clips need two timestamps.** 31/60 external clips have different scene/action peak timesteps. | Generate one combined cue vs two timestamped cues. | Two-cue version wins on ADQA and timing-overlap rubric. | `scene_agent_peak_apart` |
| 10 | **TRIBE can drive a replay recommendation.** Moment-level high concentration implies “replay/show frame” may beat spoken AD. | Human/VLM judge: static AD vs replay+caption package on top moment cases. | Replay package answers target questions faster/more accurately. | `moment_level_authoring` cases |
| 11 | **Calibrate TRIBE routing against failure clips, not global rho.** Prior nulls used wrong target. | Report clip-level AUC for ADQA fail, ensemble fail, hallucination fail, low-margin fail. | At least one externally powered AUC >0.75 survives bootstrap. | `tribe-clip-level-triage.md` |
| 12 | **Top-k review budget curves should replace single AUC.** Deployment wants recall at budget. | Plot recall@5/10/20/30% for ADQA failures, safety gate failures, pro-not-best clips. | Stable recall lift over random across budgets. | paper §8 + router CSVs |
| 13 | **Matched-question effect needs a meta-analysis table.** Current GPT-5/Opus/Haiku passes are scattered. | Combine all matched/unmatched runs with random-effects estimate. | Matched lift positive in every judge family; unmatched near zero. | `tribe_router_validation_summary.json` |
| 14 | **Permutation must preserve clip clusters.** Window/question-level p-values may overstate if clip correlation ignored. | Cluster bootstrap by video_id for matched-question lifts. | CI excludes 0 at clip level. | `tribe_surgical_adqa_perq.csv` |
| 15 | **Use negative-control windows.** Pair each high-gap target with a low-gap same-clip window. | Ask target questions from low-gap windows too. | TRIBE lift appears only high-gap, not arbitrary same-clip facts. | high vs low `peak_visual_gap` |
| 16 | **Use type-swapped prompts as controls.** Scene prompt on action window should not help as much. | Run matched, generic, and swapped prompt variants. | Matched > swapped > generic or matched > both. | prompt generation scripts |
| 17 | **Ablate audio, not just video.** TRIBE has P_AV vs P_A; compare transcript-armed VLM to no-transcript VLM. | Re-run necessity baseline with frames-only, transcript-only, frames+transcript. | TRIBE differs from both and wins at least in a targeted regime. | `tribe_necessity_rematch_perq.csv` |
| 18 | **Cheap-proxy boundary should be reported honestly.** If speech+motion approximates TRIBE, use TRIBE only where it beats proxy. | Train simple proxy to predict high-gap windows and compare downstream ADQA lift. | TRIBE residual still predicts matched lift after proxy. | `tribe-v2-deep-dive.md` |
| 19 | **Reliability should be split by category.** Sports/how-to/music likely have different TRIBE utility. | Compute routed-lift by category with wide CIs. | Identify 2–3 categories where TRIBE is worth expensive run. | category columns |
| 20 | **Use leave-video-out thresholds.** Avoid tuned route thresholds. | Recompute all thresholds LOO by video/clip. | Routing lift survives LOO. | `corrected_ladder_robustness.py` style |
| 21 | **Neural Contrastive Retrieval remains the highest-ceiling AD-dependent TRIBE score.** It makes P_AD clip-specific. | Run Colab NCR producer, then local analyzer. | Tier3 retrieves true clip above tier1/tier0; cross-decoy at chance. | `cursor/findings/neural-contrastive-retrieval.md` |
| 22 | **NCR should test source-clip leakage.** Cross-decoy AD might retrieve its original source clip. | Track both target rank and source-rank for cross decoys. | Cross-decoy retrieves source, not target; validates semantic specificity. | planned NCR CSV |
| 23 | **Time-aligned NCR may beat mean-pool NCR.** Mean pooling can erase AD timing. | Compare mean pooled, DTW, and window-max retrieval. | Time-aware version improves tier separation. | `tribe_spatiotemporal.py` patterns |
| 24 | **P_AD text injection needs a TTS-timing sanity check.** TRIBE paper uses TTS+word timing. | Compare raw-text proxy vs generated TTS word timings on a small subset. | Correlation high enough to trust proxy, or proxy downgraded. | `tribe-v2-deep-dive.md` |
| 25 | **Use AD length-normalized neural retrieval.** Avoid repeating verbosity confound. | Regress NCR score on word count and use residual. | Tier signal remains after length residualization. | prior verbosity confounds |
| 26 | **Counterfactual silence condition.** Audio-only gap may mix speech and non-speech audio. | Compare P_AV vs P_A, P_AV vs P_silence, and P_A vs silence. | Identify whether TRIBE need is missing visual information or audio complexity. | TRIBE tensors |
| 27 | **Transcript-answerability + TRIBE gap can define marginal visual demand.** MDV found low audio leak; combine with TRIBE windows. | On each question, label transcript-answerable and high-gap. | High-gap non-audio-answerable questions are where TRIBE should help most. | `marginal-description-value.md` |
| 28 | **Per-ROI residuals can become typed evidence sidecars.** Top ROI group suggests what evidence to show. | Map ROI group to evidence sidecar: keyframe, motion strip, identity chip, OCR. | Human/VLM prefers ROI-matched sidecar over generic frame gallery. | `tribe_blind_spot_cases.csv` |
| 29 | **Visual-minus-control is a confound filter.** Route only when visual gap exceeds language/auditory control. | Compare routing with raw `peak_visual_gap` vs `visual_minus_control`. | Control-subtracted routing improves precision. | `visual_minus_control` |
| 30 | **Dominant type should be multi-label when margin is low.** Binary scene/action labels may hide mixed needs. | Generate multi-label prompts for low-margin high-gap windows. | Multi-label wins only in low-margin bin. | `dominance_margin` |
| 31 | **TRIBE-routed scene-model probes are central.** They target who/action/count/spatial facts generic ADQA misses. | Finish truth-vs-targeted-lie grading for 14 high-need scene-model targets. | TRIBE probes catch lies generic ADQA misses. | `tribe_matched_scene_model_challenge` |
| 32 | **Relation/action hallucinations need targeted questions, not CLIP alone.** CLIP object grounding misses relation flips. | Create relation/count/action lies with same objects. | TRIBE-routed ADQA catches relation flips better than CLIP-drop. | scene-model probe reports |
| 33 | **Count questions are scarce but high value.** Generic ADQA has partial count coverage; TRIBE can target count when high need. | Manually label count-risk windows and generate count probes. | Higher count-lie recall at same question budget. | `question_type=count` rows |
| 34 | **Spatial relation probes should use multi-frame evidence.** Single-frame CLIP cannot judge trajectories. | Add temporal strip evidence to TRIBE-routed spatial/action questions. | Judge rationale cites frame transition; fewer false ties. | frame gallery + routes |
| 35 | **Hallucination gate should be route-aware.** Scene windows and action windows may need different thresholds. | Compute CLIP-drop/ADQA-drop ROC separately by TRIBE route. | Route-specific thresholds improve recall@10% FPR. | `hallucination_gate.json` + router |
| 36 | **Wrong-content gate can use TRIBE as a prior.** High-gap clips may deserve stricter CLIP threshold. | Stratify wrong-content false negatives/false positives by TRIBE gap. | Better expected risk under base-rate model. | wrong-content gate outputs |
| 37 | **Targeted hallucinations should be generated from TRIBE targets.** Instead of random lies, flip exactly high-gap facts. | Build lie set from `hallucination_risk` column. | TRIBE probes show large recall lift on these surgical lies. | `targets.csv` |
| 38 | **Use paraphrase controls per route.** Scene paraphrases may CLIP-drop differently than action paraphrases. | Route-balanced faithful paraphrase controls. | Hallucination drop remains above paraphrase in every route. | gate-review controls |
| 39 | **Scene-model paper can claim “probe routing,” not “lie detection,” until end-to-end run finishes.** | Separate precursor coverage metric from final catch-rate metric. | Coverage result survives; final result not overclaimed. | `scenetwin-tribe-scene-model-probe-routing.md` |
| 40 | **Generic ADQA miss table should become a reviewer figure.** It visibly proves why routing matters. | Render examples of TRIBE target vs nearest generic question. | Clear qualitative evidence plus strict coverage numbers. | `comparisons.csv` |
| 41 | **BLV micro-study should test matched windows, not global AD preference.** Global preference is noisy. | 10–20 BLV participants answer targeted questions after baseline vs gap-targeted AD. | Higher accuracy/confidence on TRIBE-matched questions. | matched-question evidence |
| 42 | **Measure cognitive load of low-gap skipping.** Less AD may be better if comprehension holds. | User/VLM proxy: full generic AD vs high-gap-only AD. | Equal answers, lower listening time/load. | low-gap skip routes |
| 43 | **Ask preference for access surface, not just description text.** Static AD may not be right output. | Compare prose vs replay chip vs object explorer for top case types. | Surface choice aligns with TRIBE route. | Paper B Access Surface OS |
| 44 | **Personalization can sit on top of TRIBE route.** Same high-gap window could be concise/detail/user-controlled. | Simulate CustomAD controls conditioned on route and user profile. | Users choose different detail levels by route/profile. | CustomAD/Describe Now sources |
| 45 | **Trust calibration matters.** High TRIBE gap could be shown as “review suggested,” not “bad AD.” | User study language variants for TRIBE flags. | Less overtrust/undertrust, more correct review decisions. | demo TRIBE page |
| 46 | **Human describer workflow should use TRIBE as checklist.** Give describers blind-spot windows before drafting. | A/B human/LLM describer with and without TRIBE checklist. | Checklist improves target coverage without verbosity spike. | `tribe_gap_targeted_external.py` |
| 47 | **Creator QC queue is a stronger product than autonomous AD replacement.** | Measure how many high-risk clips route to QC and what errors are found. | QC catches high-impact misses efficiently. | Paper B creator_qc surface |
| 48 | **User-driven “tell me more” prompts should be offered only on concentrated gaps.** | Trigger optional detail chips for high top1 concentration. | Fewer interruptions at same answered-question rate. | `top1_share` |
| 49 | **Need timing should adapt to speech density.** Talky clips may need defer/replay, silent clips can take inline AD. | Add speech-density policy to route and validate with timing rubric. | Fewer overlap violations, same content coverage. | `mean_speech_density`, coarse windows |
| 50 | **TRIBE route labels should be translated into BLV-facing language.** “Scene layout,” “action cue,” “replay moment.” | Test comprehension of labels with blind/low-vision advisors. | Labels are understandable and actionable. | web TRIBE page |
| 51 | **Demo needs per-window thumbnails.** Current TRIBE page lists router cases; add visual strip for each top window. | Implement static JSON + thumbnail strip; inspect demo. | Reviewer instantly sees why window is routed. | `web/pages/tribe.jsx`, `/api/tribe-risk` |
| 52 | **Show matched-question before/after.** Demo should display baseline AD vs gap-targeted AD and target question score. | Add a “TRIBE improved this question” card from cached CSVs. | Concrete mechanism visible in one screen. | `tribe_crossjudge_gpt5_perq.csv` |
| 53 | **Add “what TRIBE is not” panel.** Prevent overclaim: not a ranker, not a BLV brain, not direct quality. | Add caveat block to TRIBE page. | Paper/demo alignment; fewer reviewer objections. | manuscript §8 |
| 54 | **Display review budget curve, not only recall@2.** | Add chart from top-k review simulation. | Shows operational tradeoff. | `scenetwin_tribe_triage.png` |
| 55 | **Route badges should be paper-language consistent.** Rename from risk to blind-spot/review-priority. | Copy audit across README, web, paper. | No “TRIBE score” ambiguity. | README/web/manuscript |
| 56 | **Expose raw evidence paths in demo.** Reviewers need reproducibility. | Add source CSV/script links in TRIBE tab. | Demo doubles as reproducibility navigator. | `/api/tribe-risk` |
| 57 | **Add a low-gap positive example.** Show when SceneTwin recommends no extra AD. | Select a low-gap clip and explain skip/defer. | Demonstrates restraint, not maximalism. | `low_gap_skip` cases |
| 58 | **Add a “TRIBE vs VLM disagrees” example.** This supports non-redundancy. | Pick clip where transcript-armed VLM and TRIBE choose different type. | Qualitative case shows different target selection. | `tribe_necessity_rematch_perq.csv` |
| 59 | **Turn top-cases into a reviewer worksheet.** One markdown/CSV sheet per high-priority clip. | Generate `output/reports/tribe-review-worksheet.md`. | Human reviewer can act on TRIBE output. | `tribe_blind_spot_cases.csv` |
| 60 | **Export static API data for all new router evidence.** | Add cached JSON export for blind-spot windows and matched evidence. | Web can run without backend. | `cursor/export_static_api.py` if present |
| 61 | **Transcript-armed VLM is the fair baseline; keep it.** Frame-only VLM overstates TRIBE. | Make fair VLM baseline mandatory for every TRIBE targeting claim. | TRIBE survives or claim is downgraded cleanly. | `tribe_necessity_rematch.py` |
| 62 | **Motion+speech proxy is the cheap baseline.** | Use optical flow + speech density as a route predictor. | TRIBE beats proxy on targeted quality, not merely need detection. | live frames + transcripts |
| 63 | **Random high-gap labels baseline.** | Shuffle TRIBE windows within category and rerun prompts. | Real windows beat category-matched shuffle. | router CSVs |
| 64 | **Category-only baseline.** How-to often action-heavy; ensure TRIBE not just category. | Predict route from category, compare to TRIBE. | TRIBE residual improves matched lift. | category columns |
| 65 | **Word-count/verbosity baseline.** Gap-targeted AD may simply be longer. | Match word budgets across baseline and targeted AD. | Targeted lift remains at equal words. | generated AD JSONL |
| 66 | **Question difficulty baseline.** Matched questions may be easier/harder. | Compare baseline scores before targeting by matched vs unmatched. | Lift not explained by initial difficulty alone. | per-question CSVs |
| 67 | **Judge-family baseline.** Need GPT, Gemini, Anthropic spread. | Regrade same cached candidates with at least 2 judge families. | Matched>unmatched direction stable. | crossjudge scripts |
| 68 | **Generator-family baseline.** Opus vs Haiku showed magnitude shifts. | Generate with GPT/Claude/Gemini on same clips. | TRIBE benefit is not a Claude-prompt artifact. | gap-targeted scripts |
| 69 | **Prompt-only baseline without TRIBE.** Use generic “be detailed about actions/spatial layout.” | Compare to route-specific TRIBE prompt. | TRIBE prompt beats generic accessibility prompt. | generation scripts |
| 70 | **Human-authored lie baseline.** Avoid model circularity. | Extend 18 hand-authored lies to TRIBE-targeted fact flips. | Gate/probe results hold on human lies. | `human_hallucinations.jsonl` |
| 71 | **Long-form TRIBE is a separate paper-worthy extension.** Short clips hide memory and fatigue. | Run 60–180s clips with rolling TRIBE windows. | Route changes over narrative segments; AD policy adapts. | LVOmniBench notes |
| 72 | **Carry-over context should be tracked.** Long-form AD depends on what was already described. | Add state memory: has identity/layout already been described? | Less repeated AD, same answerability. | Access Surface OS |
| 73 | **TRIBE need decay can schedule re-description.** Layout once may suffice until scene changes. | Model gap peaks after scene cuts vs repeated layout cues. | Replay layout only when gap/state changes. | need curves |
| 74 | **Chunk-boundary sensitivity test.** TRIBE windows depend on clip start and HRF lag. | Shift windows ±1–5s and recompute top cases. | Top route stable or uncertainty shown. | HRF sensitivity scripts |
| 75 | **Shot-change alignment should augment TRIBE.** | Detect cuts and compare to need peaks. | Combined cut+TRIBE routes improve timing precision. | frame extraction |
| 76 | **Speech overlap policy should use soundtrack slots.** | Validate AD insertion windows against transcript silence/low-speech segments. | Fewer timing conflicts vs need-only route. | transcripts + `speech_density` |
| 77 | **Live YouTube path can include cheap TRIBE proxy.** Heavy TRIBE off by default; proxy routes demo clips. | Add local proxy from motion/speech; compare to cached TRIBE on known clips. | Proxy agrees enough for demo prefilter. | `api/server.py`, live pipeline |
| 78 | **Frame count sensitivity affects TRIBE-targeted ADQA.** | Compare 8, 16, 24 frames for target question generation. | Target coverage improves or saturates. | live eval CSVs |
| 79 | **Need windows can choose frame sampling.** Sample more frames inside high-gap windows. | Compare uniform frames vs TRIBE-window frames for ADQA questions. | Better targeted question relevance. | `stage_frames` + router |
| 80 | **Use TRIBE to choose video-native vs frame-grounded grader.** Motion-heavy high-gap clips may need Gemini video. | Route only high action-gap clips to video-native grading. | Improves catch-rate per dollar vs grading all clips. | QuerYD/video-native eval |
| 81 | **Manuscript should separate Paper A and Paper B claims.** A: audit/gates/triage. B: access surface routing. | Rewrite intro/claims with no blended overreach. | Reviewer can verify each claim independently. | `paper-scenetwin-audit-framework.md`, `paper-B-draft.md` |
| 82 | **TRIBE “side-car” needs a formal definition.** | Add equation and invariants: clip-level, candidate-invariant unless P_AD experiment. | No reviewer expects rho lift. | manuscript §4.5/§8 |
| 83 | **Report failed TRIBE routes as negative results.** Closure, ROI typing-to-pro, calibration nulls strengthen honesty. | Add compact table of killed TRIBE claims. | Preempts p-hacking critique. | `wiki/log.md`, negative results |
| 84 | **Position TRIBE as brain-grounded hypothesis generator.** It proposes where to inspect; ADQA/VLM/humans verify. | Update language across reports. | Claims survive even if TRIBE not superior to VLM. | router validation |
| 85 | **Use “competitive with transcript-armed VLM” not “beats VLM.”** | Ensure paper/demo wording follows fair rematch. | No contradiction with 2026-05-30 negative. | `tribe_necessity_rematch_perq.csv` |
| 86 | **The strongest novelty is cross-surface routing.** | Tie TRIBE windows to Access Surface OS surfaces. | Paper B becomes more than an AD scorer extension. | `paper-B-draft.md` |
| 87 | **Use operational metrics.** Recall@budget, words saved, review minutes saved, hallucination caught. | Add operational table to paper. | Deployment value clearer than correlation. | paper §7/§8 |
| 88 | **Add base-rate math for gates and triage.** | Estimate precision at 1%, 5%, 10% failure base rates. | Honest deployment expectations. | gate outputs |
| 89 | **Cite ADQA subjectivity to justify reference-free + routing.** | Align claim with ADQA: describers differ in when/what/how. | Strong literature fit. | ADQA source |
| 90 | **Cite CustomAD/Describe Now to justify user controls.** | Link TRIBE need to when/how-much customization. | Paper B related work becomes product-grounded. | CustomAD/Describe Now sources |
| 91 | **Create a `tribe_claim_matrix.md`.** Rows: claim, evidence, n, p/CI, limitations, status. | Write a reviewer-facing matrix. | No stale or contradictory TRIBE claims. | all reports |
| 92 | **Add a one-command router validation script.** | Consolidate current scattered scripts into `cursor/pipeline/tribe_router_validation_suite.py`. | Recreates tables from raw CSVs. | current router scripts |
| 93 | **Freeze static data snapshots.** | Save exact CSV hashes used by paper. | Reproducibility under branch drift. | output CSVs |
| 94 | **Generate per-clip cards.** | One markdown per high-priority clip with frames, windows, questions, AD deltas. | Easier human audit and paper appendix. | router CSV + frames |
| 95 | **Update wiki index with a TRIBE “truth table.”** | Group live, killed, pending TRIBE branches. | Future agents stop rediscovering dead paths. | `wiki/index.md` |
| 96 | **Add tests for route counts.** | Unit/smoke test that `/api/tribe-risk` returns expected route/case counts. | Demo data regressions caught. | `api/server.py` |
| 97 | **Make a route schema.** | Pydantic/JSON schema for blind-spot windows and cases. | Frontend/report/scripts share contract. | API endpoint |
| 98 | **Version prompts.** | Store baseline/gap-targeted prompts with IDs. | Cross-judge/generator comparisons are auditable. | generated JSONL |
| 99 | **Build a “dead branch detector.”** | Search new reports for banned claims: TRIBE boosts rho, closure works, pro-priority match. | Prevents regressions in writing. | lint report convention |
| 100 | **Run the next loop as evidence-first, not idea-first.** | Pick top 10 ideas above and require one CSV/JSON artifact each. | Each survives with data or gets killed. | this file |

## Top 12 to execute next after the parallel cached-data run

1. **Run the type-swapped prompt-control batch** (#16) only after approved generator/judge/human scoring is available; use `cursor/research/output/parallel_research/type_swapped_prompt_batch.jsonl` as the fixed candidate set.
2. **Fill the top-25 reviewer worksheet** (#59/#94) with VLM or human review rather than re-ranking; start from `cursor/research/output/parallel_research/access_surface/top25_reviewer_cases.csv`.
3. **Fix TRIBE-frame budget parity before rescoring** (#79): regenerate 8 frames per clip and rerun matched ADQA only after uniform/TRIBE frame counts match.
4. **Promote the cheap-baseline gauntlet into paper/demo evidence** (#62/#64): external ADQA-failure triage is now the strongest confound-controlled TRIBE result.
5. **Keep route-specific hallucination as a stratified gate appendix** (#35/#38), not a primary detector claim, unless a larger run lifts AUC beyond the current modest 0.659.
6. **Draft BLV micro-study materials locally** (#41/#43) before any recruitment: protocol, consent draft, stimuli, randomization, accessibility dry run.
7. **Define the `P_silence` protocol** (#26) before spending GPU: decide same-duration silent audio-only vs black-video+silence semantics.
8. **Move full text-extractor NCR to reviewer-objection priority** (#21/#22/#23): current L4 TTS-audio NCR is near-null; text path requires approved gated HF access and is unlikely to become a headline.
9. **Add paper copy guardrails** (#81/#83/#85): TRIBE is triage/router/access-surface routing, not ranker, calibration layer, or VLM replacement.
10. **Create static route schema/API regression smoke tests** (#96/#97) for the 334-window router and Access Surface mappings.
11. **Generate demo before/after matched-question cards** (#52) from cached cross-judge rows and show the surgical mechanism.
12. **Freeze hashes for all parallel artifacts** (#93) before paper edits so claims point to immutable CSV/JSON snapshots.

## Subagent loop synthesis

Parallel subagents produced four read-only reports under `subagent-reports/`:

- `subagent-reports/tribe-local-ideas.md` — local TRIBE mining, 25 ideas.
- `subagent-reports/tribe-external-ideas.md` — external TRIBE/fMRI/accessibility literature, 25 ideas.
- `subagent-reports/tribe-validation-ideas.md` — statistical validation/reviewer-defense, 25 ideas.
- `subagent-reports/tribe-product-paper-ideas.md` — demo/product/paper framing, 25 ideas.

The 100-item table above already covers the main reusable themes. The strongest subagent-specific additions to carry into the next loop are:

1. **TRIBE-guided frame sampling:** sample ADQA frames from top blind-spot windows to address the known temporal blindspot from the live demo.
2. **Dynamic AD insertion budget:** allocate 0/1/2/3 AD slots by `top1_vs_uniform`, not by fixed clip length.
3. **Scene-vs-action contrast question pairs:** generate paired scene/action questions for peak-divergent clips to prove the route type matters.
4. **Control-gap guardrail:** suppress or downweight TRIBE routes where auditory/language control gap is high relative to visual gap.
5. **ROI-profile clustering:** cluster normalized ROI-gap vectors and test whether clusters predict prompt-template wins better than category.
6. **Relative MT+ motion audit:** use within-clip relative motion gap, not absolute MT+ mean, to catch temporal-action failures.
7. **Hemisphere disagreement as TRIBE uncertainty:** test whether left/right mismatch predicts failed TRIBE-targeted generations.
8. **Route jitter stability:** recompute route labels under ±1 TR / ±1s shifts and mark unstable windows low-confidence.
9. **Route-confidence calibration:** calibrate matched-question win probability from `dominance_margin` and `visual_minus_control`.
10. **Tensor manifest health audit:** verify tensor dimensions, finite values, joins, and reproducibility before building more claims.
11. **BOLD Moments transfer benchmark:** use BMD short videos + metadata to build controlled object/action/scene omission tests.
12. **Frame-shuffle timing benchmark:** adapt BMD frame-shuffle logic to AD timing shifts and test monotonic neural-score drop.
13. **Memorability preservation:** test whether AD preserves moments likely to be remembered, not just visible objects.
14. **Social-cue preservation:** use face/body/social-action ROI gaps for emotion/gaze/intent omissions.
15. **Cross-modal RDM equivalence:** compare representational geometry of video, pro AD, and degraded AD in TRIBE space.
16. **Narrated-recall alignment:** validate long-form AD scores against recall-fact coverage in narrative fMRI datasets.
17. **Guideline-to-neural bridge:** map W3C/ISO “key visual information” violations to TRIBE divergence checks.
18. **Activation-optimized counterexamples:** mine high-neural-novelty clips where CLIP/ADQA are uncertain to create adversarial audit cases.
19. **Family-wise feature-selection null:** max-statistic permutation over all TRIBE features for the in-bench AUC=1.00 claim.
20. **Tie-aware TRIBE target audit:** ensure no TRIBE failure label is produced by strict inequality over ADQA ties.
21. **Calibration equivalence test:** use TOST/equivalence against the external null to defend “no meaningful continuous calibration.”
22. **Decision-curve base-rate math:** translate review queue AUC into PPV/net-benefit under realistic failure prevalence.
23. **Gap-targeted length control:** prove targeted gains are not just added words.
24. **Before/after matched-question demo cards:** show generic AD miss vs TRIBE-targeted AD answer, with aggregate stats.
25. **Access Surface OS mapping:** map `static_ad_ok_low_gap`, `layout_replay_or_scene_cue`, and `action_state_or_agent_cue` to concrete product surfaces.

## External source notes used in this pass

- TRIBE v2 is tri-modal (video, audio, language), predicts cortical activity from naturalistic stimuli, and is designed for modality ablations / in-silico neuroscience: Meta research page and arXiv `2605.04326`.
- ADQA argues AD is subjective in when/what/how describers describe, motivating frame-grounded questions and undermining single-reference evaluation as the only target: ACL Anthology / arXiv `2510.00808`.
- ViDscribe, DescribePro, CustomAD, ADx3, and Describe Now all support the product direction that BLV video access needs customization, user control, human-AI workflows, and QA — not just one static generated AD string.
- BOLD Moments, narrated-recall/movie-fMRI datasets, and cross-modal brain-encoding work support the next expansion from short-clip AD scoring into controlled visual-event omission, timing, memory, and long-form narrative validation.
