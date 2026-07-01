# TRIBE product/demo/paper framing ideas for SceneTwin

Scope: read-only framing pass over `README.md`, `web/pages/tribe.jsx`, `api/server.py`, current paper/report drafts, and `wiki/index.md`/linked TRIBE notes. No project/source files were edited; this report is the only written artifact.

## Evidence anchors used

- `README.md`: SceneTwin is a demo/evaluation workspace; core demo is CLIP + frame-grounded ADQA, with TRIBE as a cached benchmark-side neural risk signal. Live API has `run_tribe:false` by default because the path is heavy.
- `api/server.py`: `/api/tribe-risk` already joins failure forecast, correlations, need curves, coarse 3s windows, ROI gaps, and blind-spot router rows into one frontend contract. `/api/audit` only optionally runs a heavy TRIBE proxy and otherwise keeps TRIBE skipped for live demos.
- `web/pages/tribe.jsx`: current page already shows risk-ranked clips, Recall@2, p value, review budget, headline TRIBE correlation, Neural Blind Spot Map, per-clip brain map, need curve, route badges, speech-density chips, professional AD, and per-ROI bars.
- `output/reports/paper-scenetwin-audit-framework.md`: current recommended paper frames TRIBE as review triage, not scoring; a per-clip TRIBE gap cannot change within-clip ranking.
- `output/reports/paper-scenetwin-consolidated.md`: more ambitious draft frames TRIBE as brain-grounded description steering plus neural review triage, with targeted-question gains and explicit negative results.
- `output/reports/scenetwin-tribe-failure-forecast.md`: in-benchmark pilot: `mean_standard_slot_score` ranks both all-judge ADQA full-order failures top-2/18; recall@2=100%, hypergeom p=0.0065; caveat n=2 failures.
- `cursor/findings/tribe-clip-level-triage.md`: external 60-clip corrected ladder: TRIBE gap predicts ADQA-only misorders at AUC=0.79, p=0.0018; top 20% gap catches 60% of ADQA misorderings. Ensemble failure result is striking but underpowered at n=2.
- `wiki/research/scenetwin-tribe-roi-localization.md`: ROI evidence on 78 clips: clip x ROI interaction accounts for 54.7% of AV-vs-A gap structure; visual/control gap holds external (visual 0.184 vs control 0.087; perm p=5e-5); dominant lost region varies by clip.
- `wiki/research/scenetwin-tribe-blind-spot-router.md`: router inventory: 78 clips, 334 3s windows, 133 cases; cases include scene layout replay, dynamic type shift, moment-level authoring, agent/action cue, low-gap skip, audio/language confound check.
- `wiki/research/scenetwin-tribe-router-validation.md`: defensible router claim is surgical targeting. Matched gap-targeted AD improves over generic AD under GPT-5 judge by +0.113 with 11 wins / 0 losses (p=0.00049); surgical ADQA target improves +0.167 with 20 wins / 2 losses (p=6.1e-05). Negative: TRIBE does not match global professional-AD content distribution.
- `cursor/research/output/tribe_counterfactual_summary.md`: continuous calibration failed externally (`accessibility_gap` r=0.025, p=0.849 vs within-clip rho), supporting final binary triage/router framing.

## 25 concrete defensible TRIBE ideas

### 1. Human review queue: “inspect these clips first”
- **User/reviewer value:** Gives producers and paper reviewers a clean operational use for TRIBE: allocate scarce human review to clips where automatic scoring is likeliest to fail.
- **Minimal implementation/experiment:** In demo, keep `/api/tribe-risk` risk-ranked sidebar but add/export a reviewer queue CSV or “Review first” view sorted by `risk_rank`; in paper, report external ADQA-only misorder AUC=0.79 and in-bench recall@2=100% as triage, not scoring.
- **Validation signal:** Top-k capture of known scoring failures: top 20% TRIBE gap catches 60% of ADQA-only external misorderings; in-bench top-2 catches both all-judge failures.
- **Caveat:** Do not claim TRIBE improves within-clip rho; the gap is per-clip and cannot reorder candidate ADs.

### 2. Reviewer budget slider
- **User/reviewer value:** Turns abstract AUC into an actionable “with 10/20/30% review budget, here is expected failure capture” product control.
- **Minimal implementation/experiment:** Use existing `risk_score`/gap rows to compute cumulative recall curves for misordered clips; expose a slider on TRIBE page or static figure in paper.
- **Validation signal:** Area under triage curve, recall@budget, and comparison to random review budget.
- **Caveat:** Failure labels are benchmark-derived; live deployments need recalibration against local reviewer outcomes.

### 3. Neural Blind Spot Map as a demo centerpiece
- **User/reviewer value:** Shows something CLIP/ADQA cannot: when and what type of visual information audio alone drops before any AD is written.
- **Minimal implementation/experiment:** Promote existing `BlindSpotRouterPanel` in `web/pages/tribe.jsx` with a one-sentence interpretation and top 3 examples; paper figure can reuse case/route counts from router outputs.
- **Validation signal:** Router inventory: 334 windows/133 cases across 78 clips; external temporal/type structure (scene/action peaks apart in 31/60 clips; top-1 concentration 2.69x uniform).
- **Caveat:** TRIBE windows are model-predicted cortical gaps, not literal BLV attention or a ground-truth access need label.

### 4. 3-second AD authoring windows
- **User/reviewer value:** Converts TRIBE timing into concrete authoring instructions: “describe here; skip there.”
- **Minimal implementation/experiment:** Use existing `coarse_windows` from `/api/tribe-risk` to generate an editable timeline with labels (`low_ad_need`, `standard_ad_slot`, `extended_or_integrated_ad`, `inspect_visual_event`).
- **Validation signal:** Compare generated ADs with and without window guidance on matched ADQA questions; expect targeted-question lift rather than global lift.
- **Caveat:** Coarse windows avoid false sub-second precision; keep labels at 3s granularity.

### 5. Scene-layout replay mode
- **User/reviewer value:** For clips where audio misses spatial/scene context, asks the player or AD author to replay/place-set the scene before action details.
- **Minimal implementation/experiment:** Filter blind-spot cases for `scene_layout_replay`; build prompts like “give one concise scene-layout sentence for window X.”
- **Validation signal:** Matched scene/spatial questions improve vs generic AD; ROI evidence supports scene/spatial gaps (retrosplenial/PPA/V1 highest).
- **Caveat:** The router should not decide full AD content distribution; pro-AD priority matching was negative.

### 6. Agent/action cue mode
- **User/reviewer value:** Tells authoring tools when a window needs action/state detail rather than static place description.
- **Minimal implementation/experiment:** Filter route `action_state_or_agent_cue`; generate or review one action-focused sentence for those windows.
- **Validation signal:** Matched agent/action ADQA questions; router validation has matched-target gains across VLM and ADQA judge runs.
- **Caveat:** Audio often already carries agents/actions, so action cues should be used only when router gap is high, not by default.

### 7. Dynamic type-shift alert
- **User/reviewer value:** Warns reviewers that the clip changes from scene need to action need, making one generic AD prompt insufficient.
- **Minimal implementation/experiment:** Surface `dynamic_type_shift` cases with a mini timeline showing changing dominant type.
- **Validation signal:** Count and qualitative audit of 20 dynamic type-shift cases; compare authoring with a single global prompt vs type-shifted prompts.
- **Caveat:** Needs careful wording: it is a routing hypothesis, not evidence that viewers consciously experience a type shift.

### 8. Low-gap skip recommendation
- **User/reviewer value:** Saves author/reviewer time and reduces over-description where soundtrack already carries the needed information.
- **Minimal implementation/experiment:** Add “low-gap skip” badge for windows/clips with `low_gap_skip` or `static_ad_ok_low_gap` route; test omitting AD in those windows.
- **Validation signal:** No degradation on frame-grounded ADQA for omitted low-gap windows; viewe
viewer-facing future signal would be reduced cognitive load.
- **Caveat:** A low TRIBE gap is not permission to skip safety-critical visible text or identity cues; pair with OCR/safety gates.

### 9. Silent-clip risk chip
- **User/reviewer value:** Easy explanation for non-technical audiences: silent clips make AD do more work and are harder for the evaluator.
- **Minimal implementation/experiment:** Existing UI chips classify speech density as silent/mixed/talky; add paper/demo callout tying speech density to risk.
- **Validation signal:** `mean_speech_density` correlates with all4 full order (rho=0.519, p=0.027); feature AUC for failures was high in the failure-forecast report.
- **Caveat:** Speech density is partly non-neural and may be dataset-specific; frame it as a secondary interpretable covariate, not the TRIBE result.

### 10. Audit reliability forecast stat card
- **User/reviewer value:** Before scoring any candidate AD, tells the operator how stable the automatic audit is expected to be.
- **Minimal implementation/experiment:** Use existing headline correlation: `mean_standard_slot_score` vs `all4_mean_full_order` rho=-0.751, p=0.00033, n=18.
- **Validation signal:** Correlation with all-judge full-order success and top-k failure capture.
- **Caveat:** In-bench n=18; pair with external AUC=0.79 rather than using alone.

### 11. Per-ROI why-flagged explanation
- **User/reviewer value:** Makes triage less black-box: the clip is flagged because scene/spatial cortex diverged from audio-only, not because an opaque score said so.
- **Minimal implementation/experiment:** Existing `RoiBars` can serve as explanation panel; in paper, show top ROI gaps and a representative clip.
- **Validation signal:** ROI localization: visual/control gap external p=5e-5; clip x ROI interaction 54.7% shows not just scalar magnitude.
- **Caveat:** Full per-ROI tensors may be sparse in the web cache; avoid implying every clip has a high-resolution brain map unless data exists.

### 12. Scalar-vs-profile ablation figure
- **User/reviewer value:** Defends why TRIBE is not just another scalar metric by showing scalar gap misses ROI-specific routing structure.
- **Minimal implementation/experiment:** Paper figure: decompose AV-vs-A gap into clip global magnitude, fixed anatomy, clip x ROI interaction.
- **Validation signal:** 54.7% clip x ROI interaction; dominant lost region varies (retrosplenial 37, early V1 21, scene PPA 16, object/body 4).
- **Caveat:** This is interpretability/routing evidence, not direct AD quality evidence.

### 13. TRIBE-targeted ADQA question generation
- **User/reviewer value:** Makes questions focus on the moments/types most likely to matter for access instead of uniformly sampling frames.
- **Minimal implementation/experiment:** Use top TRIBE windows/types to seed one extra ADQA question per high-gap window; compare against generic ADQA questions.
- **Validation signal:** Surgical TRIBE ADQA target vs generic AD: matched +0.167, 20 wins / 2 losses, p=6.1e-05.
- **Caveat:** Keep this as targeted-question enrichment, not replacement for general frame-grounded ADQA.

### 14. Gap-targeted AD generation prompt
- **User/reviewer value:** Producer-facing feature: generate a draft that explicitly covers neural blind spots instead of generic visible content.
- **Minimal implementation/experiment:** Convert top windows/routes into prompt bullets: window, dominant type, required focus; generate AD; judge against generic AD on matched questions.
- **Validation signal:** GPT-5 judge matched questions: +0.113, 11 wins / 0 losses, p=0.00049; Opus subset matched +0.306, 8/0 wins.
- **Caveat:** Necessity control indicates VLMs with transcript can be competitive; claim distinct, targeted signal, not superiority over VLMs.

### 15. Before/after matched-question demo
- **User/reviewer value:** More persuasive than abstract rho: show generic AD misses a TRIBE-targeted question and gap-targeted AD answers it.
- **Minimal implementation/experiment:** Pick 3 cases from `tribe_crossjudge_*_perq.csv`; display question, target type/window, generic evidence, TRIBE-targeted evidence.
- **Validation signal:** Per-question win/loss/tie examples backed by aggregate matched-question gains.
- **Caveat:** Example selection can cherry-pick; show aggregate stats and include at least one tie/non-win.

### 16. TRIBE is not a score negative-results panel
- **User/reviewer value:** Builds reviewer trust by preempting p-hacking concerns and clarifying system architecture.
- **Minimal implementation/experiment:** Add a small demo/paper panel: AD-level score = CLIP+ADQA; clip-level triage = TRIBE; no fusion into rho.
- **Validation signal:** Counterfactual calibration failed externally (`accessibility_gap` r=0.025, p=0.849 vs within-clip rho); structural argument: per-clip constant cannot reorder AD candidates.
- **Caveat:** Negative-result panels must not undercut the valid router story; pair with triage/targeting evidence.

### 17. Expensive-review router
- **User/reviewer value:** Cost-control product story: TRIBE decides which clips/questions deserve frontier VLM or human review.
- **Minimal implementation/experiment:** For high-risk or high-gap windows, trigger VLM-as-judge/second-model review; for low-gap windows, use normal CLIP+ADQA.
- **Validation signal:** Review-budget capture of failures; matched-question improvements when focusing on TRIBE-selected targets.
- **Caveat:** Must measure false positives/cost; TRIBE does not guarantee overall professional-style priority.

### 18. Paper section: Neural side-car for deployment triage
- **User/reviewer value:** Clean Paper A section without over-claiming: why TRIBE is useful despite not improving the scalar score.
- **Minimal implementation/experiment:** Section structure: structural non-score proof, external triage AUC, in-bench recall@2 pilot, reviewer workflow implication.
- **Validation signal:** External ADQA-only AUC=0.79 p=0.0018 and top-budget recall; in-bench top-2/18 recall=100% p=0.0065.
- **Caveat:** Keep ensemble n=2 failure result as corroborating, not headline.

### 19. Paper section: Neural Blind Spot routing
- **User/reviewer value:** Strong Paper B story: TRIBE identifies localized access interventions that generic scoring cannot.
- **Minimal implementation/experiment:** Section structure: AV-vs-A definition, ROI/type groups, router inventory, matched-target validation, negative pro-priority result.
- **Validation signal:** 78 clips/334 windows/133 cases; matched gains across GPT-5, Opus, and surgical ADQA.
- **Caveat:** State explicitly that TRIBE does not replace human/VLM content planning globally.

### 20. Triage waterfall visualization
- **User/reviewer value:** Shows how failures concentrate as review budget grows; easier to read than AUC.
- **Minimal implementation/experiment:** Sort external clips by TRIBE gap; mark ADQA/ensemble failures as red ticks; add cumulative recall line and random baseline.
- **Validation signal:** Top 20% catches 60% of ADQA-only misorderings; top 30% catches 70%.
- **Caveat:** Use external corrected-ladder data, not just 18-clip pilot, to avoid small-n critique.

### 21. ROI fingerprint small multiples
- **User/reviewer value:** Demonstrates clip-specific lost-information profiles: scene-heavy, action-heavy, low-gap.
- **Minimal implementation/experiment:** Select 6 clips from 78 and plot grouped ROI bars; annotate route type.
- **Validation signal:** Dominant lost region varies across clips; per-ROI gaps are not rescaled scalar copies (correlations 0.19-0.57 with scalar).
- **Caveat:** Avoid neuroanatomical overinterpretation; labels should be “encoder ROI proxies.”

### 22. Type-shift timeline visualization
- **User/reviewer value:** Compelling demo of why a single AD prompt is insufficient: the same clip changes from layout to action need.
- **Minimal implementation/experiment:** For a dynamic-type-shift case, plot scene/spatial and
agent/action gap curves over time with AD slots.
- **Validation signal:** 17/60 external clips have scene/action temporal correlation <0.5; 31/60 have peaks at different timesteps.
- **Caveat:** Requires per-timestep tensors; if only cached summaries are available, use existing 3s windows.

### 23. Cache-first TRIBE preprocessing for live demos
- **User/reviewer value:** Keeps live demo fast while still showing TRIBE outputs for known/preset clips.
- **Minimal implementation/experiment:** Match live/preset video IDs to precomputed TRIBE rows; if absent, display "TRIBE queued/offline" rather than running heavy proxy by default.
- **Validation signal:** Demo latency remains CLIP+ADQA-bound; TRIBE page/API remains available from cached CSVs.
- **Caveat:** README and API already signal `run_tribe:false`; do not make live path depend on heavy TRIBE compute.

### 24. TRIBE-to-ADQA curriculum pipeline
- **User/reviewer value:** Uses TRIBE to decide which questions to ask, then lets ADQA remain the validated scoring mechanism.
- **Minimal implementation/experiment:** For each high-gap window, generate one scene/action question; run normal ADQA grading; compare coverage vs uniform question set.
- **Validation signal:** More matched high-gap evidence captured without hurting global ADQA; surgical ADQA matched gains are existing support.
- **Caveat:** Question generator can leak route assumptions into grading; keep questions frame-grounded and candidates anonymized.

### 25. Access Surface OS routing layer
- **User/reviewer value:** Expands beyond AD strings: route to static AD, extended/integrated AD, replay/keyframe surfaces, or assistant follow-up based on neural blind spots.
- **Minimal implementation/experiment:** Map routes to interventions: `static_ad_ok_low_gap` -> no/short AD; `layout_replay_or_scene_cue` -> scene replay/keyframe; `action_state_or_agent_cue` -> action narration; high-risk -> human/VLM review.
- **Validation signal:** Router inventory and matched-target gains; align with Paper B/access-surface evidence rather than metric leaderboard evidence.
- **Caveat:** This becomes a product/system claim, not just metric evaluation; needs usability/user-study validation before claiming BLV benefit.

## Cross-cutting recommendations

1. Use TRIBE in three defensible lanes only: review triage, time/type routing, and targeted generation/questioning.
2. Avoid these claims: TRIBE improves global rho; TRIBE is a direct AD text scorer; TRIBE predicts professional AD content distribution; TRIBE is literal human/BLV attention.
3. For demo, lead with cached, visual, explainable pieces: risk queue, 3s need curve, route badges, ROI fingerprint, and before/after targeted-question examples.
4. For paper, separate Paper A and Paper B framing: Paper A can use TRIBE as a modest but useful side-car; Paper B can carry the richer Neural Blind Spot Map and targeted-generation evidence.
5. Validation should be budget/target oriented, not leaderboard oriented: recall@review-budget, matched-question delta, wins/losses, sign tests, cost saved, and abstention/review yield.
