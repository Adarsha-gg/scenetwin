# SceneTwin Wiki Index
_Last updated: 2026-06-27_

> **Canonical result (corrected 3-tier ladder):** the **60-clip set is the primary evaluation**
> (ρ = 0.952), with the original **18-clip benchmark as the corroborating pilot** (ρ = 0.957); the
> two sets are disjoint by construction. Canonical write-up: `output/papers/scenetwin-submission.tex`.
> Many research pages below were authored under the older 4-tier, n=18-primary framing (ρ = 0.929 /
> 0.873); where reconciled, each page carries a banner. Pages still tied to the retired 4-tier
> sweep are labelled as such.

## Recovery / audit
- [60-clip artifact audit](../output/reports/scenetwin-60clip-artifact-audit.md) — recovered the missing 60-clip external-eval CSV/JSON and paper/finding pages from `origin/agent-loop/claude-round-70` (`8a4139a2efe4b05d3085add18786e7e9686b728b`).
- [Submission thesis memo](../output/reports/scenetwin-paper-submission-thesis.md) — final same-day recommendation: use the corrected 3-tier ladder only; be honest that SceneTwin nearly ties, not crushes, the strongest reference-style ranking baseline; lead with human-reference-free audit + safety gates.
- [Paper evidence check](../output/reports/scenetwin-paper-evidence-check.md) — verification of corrected 3-tier metrics, market/baseline comparison, safety artifacts, and VLM-as-judge baselines.

## Papers
- [SceneTwin submission draft](../output/reports/paper-scenetwin-submission-draft.md) — **current recommended submission draft.** Updated 2026-06-26 with corrected 3-tier ladder, honest LLM-AD-Eval comparison, safety gates, external TRIBE cheap-baseline triage, and Access Surface routing.
- [SceneTwin submission package](../output/reports/paper-scenetwin-submission-package.md) — title/abstract, contribution bullets, safe-claim checklist, tables, figure plan, and reviewer-objection stubs.
- [SceneTwin audit-framework manuscript](../output/reports/paper-scenetwin-audit-framework.md) — prior full paper-style manuscript with corrected 3-tier ladder, related work citations, human-reference-free audit framing, safety gates, and review triage.
- [SceneTwin audit citation map](../output/reports/scenetwin-citation-map.md) — maps every external paper/source used in the manuscript to the claim and section it supports.
- [SceneTwin consolidated submission draft](../output/reports/paper-scenetwin-consolidated.md) — earlier broader draft with brain-grounded steering; useful source material, but too sprawling as the primary same-day submission target.

## Findings — 2026-06 ladder / generalization work (cursor/findings/)
- [New findings backlog](../output/reports/new-findings.md) — 100 candidate TRIBE/SceneTwin research ideas plus validation loops, plus cached-data local run #1 results.
- [TRIBE new findings local run](../output/reports/tribe-new-findings-local-run.md) — first actual cached-data pass: feature-selection-corrected pilot p-value, low-gap external safety signal, route-confidence negative, route-type support split, tensor health caveats.
- [TRIBE new findings round 2](../output/reports/tribe-new-findings-round2.md) — cross-judge cluster bootstrap, length-control check, triage budget curves, low-pressure early-exit, tie-target audit, simple confound checks, low-alignment sensitivity.
- [TRIBE new findings round 3](../output/reports/tribe-new-findings-round3.md) — ROI/profile dominance, category-residual threshold negative, fair VLM rematch, and generated review worksheet.
- [TRIBE review worksheet](../output/reports/tribe-review-worksheet.md) — top 25 non-low-gap blind-spot cases queued for human/VLM review.
- [TRIBE claims audit](../output/reports/tribe-claims-audit.md) — claim matrix plus overclaim-risk scan for stale rho/calibration/VLM/AUC wording.
- [Colab TRIBE NCR full run](../output/reports/colab-tribe-ncr-full-run.md) — L4 Colab runbook/results for self-contained 60-clip TTS-audio NCR; A100/H100 unavailable, L4 used, no active sessions left.
- [TRIBE NCR results](../output/reports/tribe-ncr-results.md) — full 60-clip NCR metrics: near-chance global rank signal, small T3>short and source-specificity pilot effects.
- [TRIBE NCR hidden patterns](../output/reports/tribe-ncr-hidden-patterns.md) — hubness, category splits, source-vs-target leakage, and paper-safe guardrails for NCR.
- [Parallel research synthesis](../output/reports/parallel-research-synthesis.md) — go-forward decisions from the 2026-06-23 parallel cached-data runs; promote cheap-baseline triage, demote frame-sampling/hallucination claims, and gate NCR/P_silence/BLV work.
- [Parallel route hallucination gate](../output/reports/parallel-research-route-hallucination-gate.md) — cached local route-stratified hallucination-gate analysis; TRIBE high-gap modestly stratifies gate strength but is not standalone risk.
- [Parallel TRIBE frame sampling](../output/reports/parallel-research-tribe-frame-sampling.md) — cached uniform-vs-TRIBE frame overlap/ADQA comparison; high-gap coverage improves but action-window coverage does not.
- [Parallel cheap baseline gauntlet](../output/reports/parallel-research-cheap-baseline-gauntlet.md) — cached TRIBE triage vs category/transcript/duration baselines; accessibility_gap wins ADQA-failure triage with category-shuffle support.
- [Parallel access-surface triage](../output/reports/parallel-research-access-surface-triage.md) — review-budget, low-gap early-exit, route counts, and reviewer-ready Access Surface OS case mapping.
- [Parallel type-swapped blocker/batch](../output/reports/parallel-research-type-swapped.md) — no cached type-swapped prompt-control result exists; generated future JSONL batch.
- [Parallel blocked next steps](../output/reports/parallel-research-blocked-next-steps.md) — feasibility and approval blockers for full text-extractor NCR, P_silence, and BLV micro-study.
- [Agent loop (Claude + Codex breakthrough hunt)](../cursor/agent_loop/README.md) — supervisor polls every 4m, assigns next tasks until credits die. State: `cursor/agent_loop/state.json`, log: `cursor/agent_loop/log.md`.
- [Agent-loop gate synthesis](../cursor/findings/agent-loop-gate-synthesis.md) — loop stopped by user on 2026-06-09; Codex consolidated the output into the AD safety gate subsection at commit `0d1a633`. Lead result: grader-free CLIP grounding-drop gate AUC 0.835 with 70% recall @ 10% FPR; fused CLIP+ADQA AUC 0.904 is footnoted as grader-dependent; zero-reference weakest-claim gate remains a negative (AUC 0.585).
- [Gate review-hole closure](../cursor/findings/gate-review-holes.md) — pre-subsection validation: 18 **hand-authored** fabrications break Gemini circularity (CLIP drop AUC 0.91 vs paraphrase); self-consistency gate with 2nd model-gen reference (n=5, AUC 0.76). Paper subsection locked at `output/reports/paper-ad-safety-gate.md` — headline **CLIP-only AUC 0.84 @ 70% recall / 10% FPR**; fusion 0.90 footnoted as grader-dependent.
- [Calibrated hallucination GATE (deployable vs not)](../cursor/findings/claim-level-gate.md) — turns the sensitivity result into an operating point at 10% FPR. Zero-reference single-AD gate (weakest CLIP claim grounding) is near chance (AUC 0.58); but a reference-comparison gate (candidate vs any trusted/2nd AD) catches hallucinations well — CLIP grounding-drop AUC 0.84, and CLIP+ADQA fused AUC 0.90, 72% recall @ 10% FPR. The dual signal pays off operationally (0.84/0.80→0.90). Ship as reference-comparison gate; use claim grounding only to highlight suspect claims (claim-level fab-vs-true AUC 0.69).
- [Hallucination sensitivity — the dual-signal outcome, with a control](../cursor/findings/hallucination-gate.md) — corrupt each expert AD's 2-3 visual facts into same-length plausible lies (±0.8 words) + a faithful-paraphrase control. ADQA is blind on 17/60 clips (lie ties the truth when it's not a probed question); on those exact clips CLIP catches 100%. Fabrication drops CLIP visual grounding ~5× more than a paraphrase (+0.037 vs +0.008, paired p<1e-4). The legitimate, controlled version of the retracted dual-signal claim: signals are complementary by construction. Caveat: raw sign false-alarms on paraphrase (CLIP 65%), so the usable signal is grounding-drop magnitude, not sign.
- [Dual-signal on hard completeness — RETRACTED (tie artifact)](../cursor/findings/dual-signal-complementarity.md) — a claimed "ensemble strictly dominates ADQA" result was overturned by self-audit: it was an artifact of strict-inequality scoring over ADQA's many ties (CLIP breaks half/full ties at 42%, below chance; tie-aware ADQA 0.776 > ensemble 0.741). Honest conclusion: dual signal does NOT help on hard completeness. Method lesson: always score ordering tie-aware.
- [Next steps / pending experiments](../cursor/findings/NEXT-STEPS.md) — queued reruns blocked only on LLM credits: Opus/GPT graders, independent machine-AD grading, 2 Gemini-blocked clips. Read before re-running.
- [Fake tier rung — corrected ladder](../cursor/findings/fake-tier-rung.md) — `tier2_vatex_long` is a structurally invalid rung (longest crowd caption, not a quality grade). Dropping it: in-domain rho 0.93->0.95, OOD rho 0.87->0.95, full order 50%->97%.
- [Corrected ladder — robustness](../cursor/findings/corrected-ladder-robustness.md) — the 0.95 is not a tuned config: flat plateau across ensemble weights w∈[0.2,0.8], holds under min-max/z-score/rank norms, bootstrap 95% CI [0.93,0.98] in-domain / [0.93,0.97] OOD (overlapping), permutation p=0.0002. Direct reviewer-defense.
- [TRIBE is clip-level triage, not a ρ booster](../cursor/findings/tribe-clip-level-triage.md) — TRIBE's gap is one value PER CLIP so it CANNOT lift within-clip ρ (why calibration was always null), but it flags which clips the metric misorders OOD: AUC=0.79 p=0.0018 for ADQA-only failures (top-20% gap catches 60%). Two-layer framing: ADQA+CLIP score, TRIBE triages.
- [Marginal Description Value (MDV)](../cursor/findings/marginal-description-value.md) — new reference-free metric: credit the AD only for visual info it adds OVER the soundtrack (transcript-answerability gate). Honest negative: audio leak is only 5.3% (narration genres up to 15%), MDV ≈ ADQA. Positive read: frame-grounded ADQA is audio-robust (a vision metric, not soundtrack paraphrase) — a validity check, not a new scorer.
- [Neural Contrastive Retrieval (NCR)](../cursor/findings/neural-contrastive-retrieval.md) — AD-dependent brain-grounded score design. Full L4 TTS-audio-only run completed 2026-06-23: global rank signal is near chance; keep only as negative/guardrail plus weak source-specificity pilot.
- [Completeness ladder (valid 4-tier)](../cursor/findings/completeness-ladder.md) — {cross < 1-sentence < half < full AD} with 10 frame-grounded questions (4 core + 6 secondary). Gemini grader: rho=0.870, 37/58 fully ordered on OOD clips. Gemini-floor result; stronger graders queued.
- [VATEX-60 generalization](../cursor/findings/vatex60-generalization.md) — full CLIP+ADQA ensemble on 60 held-out VATEX OOD clips: rho=0.873.
- [Selective / abstention audit](../cursor/findings/selective-audit.md) — reference-free min-margin confidence beats random abstention but is a modest result on n=18; de-prioritized.

## Reference
- [Presenter demo runbook](demo-runbook.md) — local-only static walkthrough: Overview, Cached clips, Benchmark, TRIBE risk, Compare; optional API/Live Audit
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
- [[research/scenetwin-adqa-clip-ensemble]] — CLIP + frame-grounded ADQA ensemble (now the 18-clip PILOT, secondary to the 60-clip primary). Corrected 3-tier ladder: rho=0.954, 17/18 fully ordered, 53/54 pairwise. Leaderboard tables on the page are the retired 4-tier sweep (rho=0.929).
- [[research/scenetwin-multijudge-adqa]] — multi-judge ADQA + VLM rater: fair all-judge rho=0.933 (53/54, 16/18), optimized rho=0.944, VLM-augmented rho=0.965 (54/54, 18/18); length bias checked; TRIBE reframed as content-type controller. Poster headline.
- [[research/scenetwin-tribe-failure-forecast]] — TRIBE as pre-scoring risk module: mean_standard_slot_score ranks both all4-ADQA full-order failures #1 and #2 out of 18; recall@2=100%, ROC-AUC=1.0, p=0.0065 (Bonferroni p=0.065); 11.1% review budget. Pilot evidence, secondary finding.
- [[research/scenetwin-tier-ordering-failures]] — RETIRED 4-tier rationale: the 3/18 T1->T2 violations were the evidence for removing the invalid T2 rung. Corrected 3-tier pilot: 17/18 ordered (1 violation, clip 0 tie). Paper failure-analysis subsection.
- [[research/scenetwin-external-validation]] — PRIMARY 60-clip evaluation (corrected 3-tier): ensemble rho=0.952, 178/180 pairwise (hard T1-vs-T3 pair 58/60), 58/60 fully ordered; 18-clip pilot corroborates at 0.957. Sets are disjoint by construction.
- [[research/scenetwin-statistical-power]] — Power on the 60-clip primary (and 18 pilot): perm p<2e-4, bootstrap CI [0.93,0.97], min detectable rho ~0.21 vs observed ~0.95; combined-78 rho=0.954. Paper Methods/Power Analysis subsection.
- [[research/scenetwin-tribe-role-analysis]] — Honest measurement: TRIBE features do NOT correlate with continuous ensemble noise (all p>0.16) but DO predict binary all4_fail at AUC=1.00. Reframe TRIBE from "calibration layer" to "binary review triage flag" (11% review budget, recall@2=100%).
- [[research/scenetwin-tribe-roi-localization]] — TRIBE use-case: the AV-vs-A accessibility gap concentrates in visual cortex (retrosplenial/V1/scene-PPA) vs auditory/language controls (~2x), and HOLDS external (perm p=5e-5, n=60) where scalar calibration died. First anatomical, externally-generalizing TRIBE result; a validity/interpretability story, not calibration.
- [[research/scenetwin-tribe-blind-spot-router]] — Tensor-derived Neural Blind Spot Map: converts P_AV vs P_A into typed 3s authoring/review windows and product routes across 78 clips.
- [[research/scenetwin-tribe-router-validation]] — Validation of the router story: matched TRIBE-targeted questions improve across VLM/ADQA/judge comparisons, while global pro-AD priority matching is negative. Supports a surgical routing claim, not a rho claim.
- [[research/scenetwin-external-baselines]] — Paper baselines (leaderboards are retired 4-tier). Corrected 3-tier: SceneTwin 0.952 (60) / 0.957 (18) vs LLM-AD-Eval 0.942/0.941 — near-tie (lift +0.010/+0.016). Critical caveat still holds: reference-based metrics get 180/180 T3 wins trivially; ensemble's 178/180 is the meaningful number.
- [[research/scenetwin-external-t3-losses]] — Corrected 3-tier: only 2/180 T3 pairwise losses on the 60-clip primary (both to T1; one a near-tie). The retired 4-tier "7/180" had 5 losses to the removed T2 rung.
- [[research/scenetwin-metric-landscape]] — 10 paper-derived baselines (leaderboards are retired 4-tier). Corrected ladder: near-tie with LLM-AD-Eval (lift +0.010 on the 60-clip primary); fusion experiments find no lift. Paper Related Work / Baselines table.
- [[research/scenetwin-negative-results]] — What we tried that did NOT beat the ensemble: 6 fusion strategies, TRIBE calibration (all p>0.16), gated pipeline (every threshold hurts rho), closure dead branch. Argues parsimony over metric zoo. Paper Negative Results subsection.
- [[research/scenetwin-signal-decomposition]] — Honest CLIP-vs-ADQA decomposition (corrected 3-tier). CLIP lift over ADQA-only: +0.069 on the 18 pilot, +0.005 on the 60 primary. CLIP earns +0.024 on How-to (n=21), neutral elsewhere. Reframes the contribution from "dual-signal" to "ADQA backbone + CLIP for controlled benchmarks and visual-object content."
- [[research/scenetwin-method-inventory]] — Audit of 28 method scripts; 22 ran with measurements, 12 paper-derived stubs deferred. Splits cleanly into Paper A (metric+benchmark) and Paper B (Access Surface OS). 5 routing scripts have target-recall >=88% on n=58 external clips -- Paper B evidence is real.
- [[research/scenetwin-paper-outline]] — Master outline for Papers A and B. Section-by-section with evidence pages cited, figure/table inventory, blocker list. Writing roadmap: Paper A first (~2-3 weeks), Paper B during A's review.
- [[research/scenetwin-combined-paper-draft]] — Combined one-paper draft: reference-free AD scoring plus TRIBE Neural Blind Spot routing as one deployable BLV access system.
- [[research/scenetwin-paper-corpus]] — 37 papers reviewed; 6 clusters (semantic, narrative, agency, identity, assistant, evidence loop); Paper A baselines map to clusters A-D, Paper B Related Work spine is clusters E-I. Ready-to-paste Related Work skeletons for both papers.
- [[research/scenetwin-access-surface-os]] — Paper B empirical evidence consolidated. 5 routing claims on n=58: surface (92%), assistant mode (96.3%), task loop (88.9%), evidence sidecar (100%), commentary residual. Cross-claim consistency shows the 5 dimensions are not redundant. Paper B Section 4 ready.
- [[research/scenetwin-vlm-as-judge-protocol]] — Frontier VLM-as-judge baseline protocol + cost matrix. Full 78-clip run: $1 (Gemini Flash) to $50 (Claude Opus). Runner ready at cursor/research/vlm_as_judge_runner.py. Decision rule covers all 3 outcomes (VLM loses, ties, or beats ensemble).
- [[research/scenetwin-vlm-as-judge-results]] — All 3 frontier VLMs trail the structured audit. Corrected 3-tier (manuscript): best VLM judge rho=0.847 (60 primary) / 0.863 (18 pilot) vs SceneTwin 0.952/0.957. Per-model tables on the page are the retired 4-tier sweep (VLMs 0.71-0.76); per-model corrected leaderboard CSV still needs regenerating.
- [[research/scenetwin-tribe-balanced-text-feel-audit]] — text-feel audit for tribe-balanced AD generation
- [[research/scenetwin-tribe-text-feel-audit]] — earlier text-feel audit pass
- [[research/scenetwin-tribe-policy-validation]] — TRIBE policy validation on tribe-native and balanced sets
- [[research/scenetwin-tribe-native-analysis]] — TRIBE-native AD analysis on 20 clips
- [[research/scenetwin-tribe-need-adqa]] — TRIBE need + ADQA correlation pass
