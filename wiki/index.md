# SceneTwin Wiki Index
_Last updated: 2026-05-13, migrated from Knowledge_

## Reference
- [Presenter demo runbook](demo-runbook.md) — stable NJBDA walkthrough: Overview, Cached clips, TRIBE risk, Compare, optional Live Audit
- [TRIBE metric glossary](../output/reports/tribe-metric-glossary.md) — plain English of every number on the TRIBE page: rho sign, route badge, speech chip, need timeline, per-ROI gap
- [TRIBE demo additions plan](../output/reports/tribe-demo-additions.md) — the five TRIBE signals wired into the web page on 2026-05-14

## Research
- [[research/scenetwin-queryd-video-native-eval]] — Gemini video-native ADQA on real human QuerYD AD transcript windows: ADQA rho=0.865, CLIP+ADQA rho=0.932 on n=5
- [[research/scenetwin-frame-sampling-temporal-blindspot]] — live demo on held out VATEX beer pour clip: auto AD beat pro AD because frame sampling rewards static composition over temporal action
- [[research/scenetwin]] — SceneTwin: using TRIBE v2 to score audio description fidelity for blind/low-vision video access
- [[research/scene twin codex]] — working notes on SceneTwin proof of concept, hallucination failure, and TRIBE+CLIP corrected metric
- [[research/scenetwin-accuracy-plan]] — four experiments to dramatically improve SceneTwin: ROI-restricted scoring, per-TR alignment, Description Gain, contrastive retrieval
- [[research/scenetwin-improvement-research]] — concrete models, papers, and tools for next-generation SceneTwin: VALOR, FG-CLIP, PAC-S, ADQA, ShareCaptioner-Video, InternVideo2.5
- [[research/scenetwin-codex-handoff-2026-04-22]] — full local analysis: TRIBE variants x CLIP upgrades tested on saved tensors; best combo = Temporal-PPA x ViT-L-14
- [[research/scenetwin-revolutionary-implementation-plan]] — original counterfactual neural accessibility metrics: missing visual residual recovery, event-boundary recovery, redundancy penalty, profiles, and stress tests
- [[research/scenetwin-description-gain-smoke-test]] — 2-clip Colab smoke test showing raw Description Gain/MVRR are unstable and need visual grounding gates
- [[research/scenetwin-neural-description-need-pivot]] — pivot from TRIBE text scoring to TRIBE accessibility-gap curves for when/where audio description is needed
- [[research/scenetwin-neural-event-test]] — 2-clip test of TRIBE visual-only neural event boundaries as a secondary AD inspection trigger
- [[research/scenetwin-need-weighted-grounding]] — CLIP grounding weighted by TRIBE-derived AD need; 2-clip smoke test where TRIBE improves frame selection
- [[research/scenetwin-ocr-coverage-test]] — OCR coverage layer for visible text on important AD windows, tested on the Burger King title-card clip
- [[research/scenetwin-working-stack]] — current honest SceneTwin architecture after raw Description Gain failed: TRIBE timing + grounding/OCR content layers
- [[research/scenetwin-coarse-need-windows]] — 3s TRIBE-honest AD windows to avoid false sub-second timing precision
- [[research/scenetwin-hrf-lag-sensitivity]] — frame-alignment sensitivity test showing 0s lag beats 2.5s/5s on current two clips
- [[research/scenetwin-trajectory-metrics]] — DTW/resampled TRIBE trajectory metrics; useful diagnostic but weaker than need-weighted grounding
- [[research/scenetwin-metric-null-baselines]] — exact within-clip permutation nulls for small-sample metric sanity checks
- [[research/scenetwin-roi-gap-curve]] — ROI gap script scaffold that requires a real fsaverage5 ROI mask instead of fake vertex slices
- [[research/scenetwin-destrieux-roi-mask]] — real fsaverage5 Destrieux anatomical proxy mask for visual/language/auditory ROI smoke tests
- [[research/scenetwin-roi-gap-analysis]] — ROI-restricted gap analysis; promising on clip 00, mixed on clip 01, not headline-ready
- [[research/scenetwin-roi-content-typing]] — TRIBE ROI gaps converted into AD slot content types and matched against description content coverage
- [[research/scenetwin-gap-targeted-ad-loop]] — closed-loop AD generation spec where TRIBE per-ROI gap drives LLM prompts and accepts/rejects candidates by predicted cortical residual
- [[research/scenetwin-phase1-ad-ab-test]] — Phase 1 baseline vs gap-targeted AD candidate generation and scoring harness
- [[research/scenetwin-phase2-typing-validation]] — Phase 2 prerequisite test: TRIBE per-window dominant type agrees with pro AD only 4.8% (below chance), Phase 2 closed loop blocked until atlas/anchor fix
- [[research/scenetwin-glasser-roi-mask]] — Glasser HCP-MMP1.0 functional parcellation resampled to fsaverage5: PHA1/2/3 instead of whole parahippocampal gyrus, MT/MST/FST instead of MTG, FFC instead of fusiform gyrus
- [[research/scenetwin-glasser-vs-destrieux-typing]] — atlas swap improved typing agreement 4.8% to 19.0% (chance 16.7%); functional ROIs help but typing layer is still not closed-loop ready
- [[research/scenetwin-phase2-llm-typing-validation]] — Claude-classified pro AD agrees with Glasser TRIBE typing only 4.8%; lexicon was not the bottleneck, so ROI typing should be dropped from the headline
- [[research/scenetwin-20clip-timing-results]] — 20-clip scale-up: CLIP grounding is robust (rho ~ 0.73, null p<0.0005), while TRIBE weighting is timing/prioritization rather than a large CLIP boost
- [[research/scenetwin-tribe-only-analysis]] — TRIBE-only inspection on 20 clips and 2-clip tensors: no AD-verbosity correlation, no significant category fingerprint, no hard-case CLIP rescue; per-window timing remains the only surviving TRIBE-only contribution
- [[research/scenetwin-stage4-llm-adqa]] — Stage 4 LLM-ADQA comprehension audit: 54 questions, 216 grades, rho=0.942, null p<0.0005 using professional AD as reference answer key
- [[research/scenetwin-stage4-frame-grounded-adqa]] — corrected blind frame-grounded ADQA: 8 frames/clip, 5 questions/clip, anonymized candidates, unfiltered rho=0.803, tau=0.696, 51/54 tier3 wins, 8/18 fully ordered, null p<0.0005
- [[research/scenetwin-adqa-clip-ensemble]] — CLIP + frame-grounded ADQA ensemble: rho=0.929 [95% CI 0.90, 0.96], 54/54 tier3 wins, 15/18 fully ordered, non-overlapping CI vs CLIP-only, per-clip CLIP/ADQA rho=0.76 (complementary, not redundant)
- [[research/scenetwin-multijudge-adqa]] — multi-judge ADQA + VLM rater: fair all-judge rho=0.933 (53/54, 16/18), optimized rho=0.944, VLM-augmented rho=0.965 (54/54, 18/18); length bias checked; TRIBE reframed as content-type controller. Poster headline.
- [[research/scenetwin-tribe-failure-forecast]] — TRIBE as pre-scoring risk module: mean_standard_slot_score ranks both all4-ADQA full-order failures #1 and #2 out of 18; recall@2=100%, ROC-AUC=1.0, p=0.0065 (Bonferroni p=0.065); 11.1% review budget. Pilot evidence, secondary finding.
- [[research/scenetwin-tribe-balanced-text-feel-audit]] — text-feel audit for tribe-balanced AD generation
- [[research/scenetwin-tribe-text-feel-audit]] — earlier text-feel audit pass
- [[research/scenetwin-tribe-policy-validation]] — TRIBE policy validation on tribe-native and balanced sets
- [[research/scenetwin-tribe-native-analysis]] — TRIBE-native AD analysis on 20 clips
- [[research/scenetwin-tribe-need-adqa]] — TRIBE need + ADQA correlation pass
