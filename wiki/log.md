# SceneTwin Log

## [2026-06-10] paper closeout | Restyled figure set + filled bibliography

Get-it-done pass on the consolidated paper. (1) FIGURES: built a shared design system
`output/charts/scenetwin_style.py` (Helvetica Neue, semantic teal/grey/blue/red/amber
palette, solid colors for PDF perf, titles above axes, direct value labels) and restyled
8 of 9 figures as `*_v2.{png,svg}`: competitive, corrected_ladder, fusion, gate,
wrongcontent, triage, steering. Built the hero brain-grounded steering diagram as designed
HTML/CSS rendered via Brave headless at 2x -> `output/charts/diagram_steering.{html,png}`
(this is the highest-ROI single visual: video -> TRIBE P_AV vs P_A -> blind spot -> steer
generator -> matched +0.113 vs unmatched +0.017). Only `ladder_robustness` (Fig 3) left
un-restyled. Repointed all paper figure refs to v2 + inserted the diagram as Fig 7
(renumbered steering->Fig 8, triage->Fig 9). (2) BIB: filled 39/40 first-author fields in
`output/papers/scenetwin-references.bib` via the arXiv Atom API (WebFetch; Bash has no
network) as `First Last and others`; only uncited non-arXiv `emotive2025nature` left TODO.
Paper draft is now content-complete with a coherent figure set and working citations.

## [2026-06-09] chart | Dedicated matched-vs-unmatched steering figure (Fig 7)

Built output/charts/scenetwin_steering_matched.py (+ .png), a grouped bar chart that
recomputes the gap-targeted - baseline ADQA delta from cursor/research/output/
tribe_crossjudge_{gpt5,opus_17}_perq.csv at render time (matched +0.113 d=0.43 11/0/51,
unmatched +0.017 d=0.05; non-headroom matched +0.167 d=0.42 8/1/15, unmatched +0.000
d=0.00 6/5/50), 95% bootstrap CI whiskers, solid colors. Repointed paper Fig 7 to this
chart; the triage PNG moved to Fig 8 in §8.4. Render env: .venv/bin/python.

## [2026-06-09] paper | Elevated brain-grounded steering to co-lead contribution

Restructured §8 of paper-scenetwin-consolidated.md so TRIBE's causal gap-targeted
generation leads instead of triage. New §8 = "Brain-Grounded Description Steering": §8.1
the blind-spot signal, §8.2 causal steering (matched +0.113 d=0.43 11W/0L vs unmatched
+0.017 d=0.05, GPT-5 cross-family judge; non-headroom 17-clip matched +0.167 d=0.42 vs
unmatched +0.000 d=0.00 -- recomputed from cursor/research/output/tribe_crossjudge_*.csv,
verified on disk), §8.3 necessity control (transcript-armed VLM ties, 91% target
disagreement -> "distinct competitive signal" not superiority), §8.4 why-not-a-metric +
triage (AUC 0.79). Updated title, abstract, intro contributions (steering now #4 "most
novel", triage split to #5), §2.4 ("first fMRI encoder used to steer AD content, not
evaluate it"), discussion, conclusion, keywords. Numbers locked from CSV, not memory.

## [2026-06-09] paper | Consolidated single-paper draft (supersedes paper-A/B/combined)

Wrote output/reports/paper-scenetwin-consolidated.md, a prose-complete submission draft
that folds the two June findings the older drafts were missing: (1) the corrected-ladder
result (drop the invalid length-only T2 rung -> ρ≈0.95 in-domain AND OOD, 58/60 ordered,
closing the apparent generalization gap), and (2) the AD safety gate as a deployment
section (grader-free CLIP grounding-drop hallucination gate AUC 0.84 @ 70% recall/10% FPR;
single-AD wrong-content gate 98%@2%). TRIBE reframed as clip-level triage (AUC 0.79 on OOD
ADQA misorderings) + typed blind-spot routing, with the calibration null reported honestly.
Sections 1-11 + 3 appendices, 7 existing figures wired in, numbers locked. Remaining: build
.bib first-author fields. Supersedes paper-A-draft / paper-B-draft / paper-combined-draft.

## [2026-06-07] research | Valid 4-tier completeness ladder (replaces fake rung)

Built a legitimate 4th tier after two attempts. (1) Machine-AD rung failed:
frame-grounding circularity + self-grading make machine AD tie/beat expert
(expert>machine only 22%). (2) Coarse completeness (5 questions) saturated:
half≈full. (3) Finer completeness ladder WORKS: cross < expert-AD-1sentence <
expert-AD-half < expert-AD-full, graded by Gemini against 10 questions spanning a
granularity gradient. 58 OOD clips: ensemble ρ=0.870, ordering 37/58 (64%);
adjacent rungs correct at 100% / 88% / 74%; ADQA never inverts the top rung
(full>=half 100%). Ensemble lifts over ADQA (0.77) and CLIP (0.64). Demonstrates
SceneTwin measures essential visual-content coverage, not verbosity. Artifacts:
`cursor/pipeline/finer_completeness_ladder.py`, `cursor/pipeline/machine_ad_tier.py`,
`cursor/output/finer_completeness_ladder.json`, `output/charts/scenetwin_completeness_ladder.png`,
`cursor/findings/completeness-ladder.md`.

## [2026-06-07] research | Fake tier rung — corrected ladder closes OOD gap

Discovered the 4-tier AD benchmark has a structurally invalid rung: tier2
("long VATEX") is built as `max(crowd_captions, key=len)` — the wordiest of ~10
equal-status crowd captions (differs from tier1 only by length on 299/338 clips).
Two independent signals rank tier2>tier1 at chance (CLIP 67%/42%, ADQA 67%/50%
benchmark/OOD) — the rung carries no quality signal. Evaluating the valid ladder
{cross control < crowd caption < pro AD} lifts results in-domain AND OOD:
benchmark ρ 0.928→0.954 (order 15/18→17/18); VATEX-60 OOD ρ 0.873→0.947
(order 30/60→58/60, i.e. 50%→97%). The apparent generalization gap was largely
an artifact of grading against word count. Not cherry-picking: a category invalid
by construction, confirmed at chance by two metrics before looking at outcomes.
Artifacts: `cursor/pipeline/fake_rung_analysis.py`, `cursor/output/fake_rung_analysis.json`,
`output/charts/scenetwin_corrected_ladder.png`, `cursor/findings/fake-tier-rung.md`.

## [2026-06-07] research | Selective reference-free audit — SceneTwin self-abstention

Found and validated the paper's new headline: SceneTwin emits a reference-free
confidence per clip (smallest gap between its 4 sorted tier scores; no GT, no
extra model). On 60 held-out VATEX clips OOD, abstaining on the least-confident
50% lifts retained pooled ρ from 0.873 to **0.911** (95% CI [0.893, 0.931]),
overlapping the in-domain benchmark ρ=0.928, and beats random abstention at
p<0.005 (40-60% coverage). Abstention is targeted: 4/5 genuine pro-AD ranking
misses are flagged. Reframes the OOD drop (0.93→0.87) as the first reference-free
AD audit with calibrated self-abstention. Artifacts: `cursor/pipeline/selective_audit.py`,
`cursor/output/selective_audit.json`, `output/charts/scenetwin_risk_coverage.png`,
`cursor/findings/selective-audit.md`.

## [2026-05-14] web | TRIBE page expanded with five new signals

Added all five planned TRIBE additions to `web/pages/tribe.jsx` and
`api/server.py` `/api/tribe-risk`. (1) Headline correlation surfaced as a
fifth stat card and callout: TRIBE `mean_standard_slot_score` predicts
4-judge ADQA full-order agreement at rho = -0.751, p = 0.0003 on n=18
from video/audio alone, before any AD is written. (2) Per-ROI cortical
accessibility gap chart on Glasser HCP-MMP1.0 atlas (retrosplenial 0.96,
scene PPA 0.79, V1 0.25 on clip 00) for the two clips with full TRIBE
tensors; honest fallback message for the rest. (3) Inline SVG AD-need
curve over time per clip with 3s coarse-window bands underneath
(extended / standard / inspect / low) for all 20 clips. (4) Colored TRIBE
route badge in sidebar (extended AD / standard AD / low pressure). (5)
Speech density chip (silent / talky / mixed) in sidebar and as a fifth
selected-clip stat. Wiring plan in
[`output/reports/tribe-demo-additions.md`](../output/reports/tribe-demo-additions.md).

## [2026-05-14] web demo | TRIBE risk and comparison tabs

Added the FastAPI `/api/tribe-risk` endpoint and wired it into the JavaScript frontend.
The TRIBE tab now shows the cached 18-clip neural risk forecast, brain imagery, recall@2
= 100%, p = 0.0065, and clickable risk-ranked clips. Added a Compare tab to explain why
SceneTwin is not just a VLM grader: CLIP grounds the AD in visual evidence, ADQA checks
whether blind/low-vision viewers receive needed scene facts, and TRIBE routes likely
comprehension failures to human review. The web demo now opens on the Overview preview,
with Live Audit, Benchmark, TRIBE Risk, and Compare available from the top nav.

Rendered per-clip TRIBE brain panels for all 18 cached benchmark clips from the saved
`P_AV` and `P_A` prediction arrays. Each panel shows audiovisual viewing, audio-only
viewing, and the absolute accessibility gap `|P_AV - P_A|`. The TRIBE Risk tab now swaps
the large brain map when a clip row is selected.

## [2026-05-13] demo | t=0 high-motion trailer sweep

Reran high-motion trailer candidates from the actual start of each YouTube video, because
the live demo needs to work when a clean `watch?v=` URL is pasted. Best start-of-video
presets: Mission Impossible trailer (CLIP top3 0.333, ADQA 3/3), John Wick 4 trailer
(0.332, 3/3), Spider-Man No Way Home trailer (0.317, 3/3), and The Batman trailer
(0.305, 3/3). Top Gun Maverick remains the strongest stress demo when using the 55s action
timestamp (0.394, 3/3). Updated the Live tab presets so the first three one-click demos use
plain t=0 URLs. Sweep artifact: `output/live_high_motion_t0_sweep.csv`.

## [2026-05-13] demo | High-motion trailer presets tested

Swept six movie-trailer style high-motion clips through the exact Live YouTube path:
timestamped download, 8-frame sampling, GPT-4o-mini AD generation, CLIP grounding, and
Claude ADQA. All six downloaded and scored. Best high-motion options: Top Gun Maverick
trailer at 55s (CLIP top3 0.394, ADQA 3/3), Dune Part Two trailer at 82s (0.328, 3/3), and
The Batman trailer at 75s (0.304, 3/3). Added these to the Live tab presets ahead of the
safer non-trailer examples. Sweep artifact: `output/live_high_motion_preset_sweep.csv`.

## [2026-05-13] demo | Live YouTube presets and timestamp-safe trimming

Fixed `demo/live_pipeline.py` so YouTube `t=` / `start=` offsets are respected when ffmpeg
trims live clips. Before this, timestamped demo URLs could download the right video but trim
from 0s. Swept seven candidate live demo videos through the exact Live YouTube pipeline
(download, 8 frames, GPT-4o-mini AD, CLIP, Claude ADQA). Added the top three as one-click
presets in `demo/scenetwin_demo.py`: indoor diving platform (CLIP top3 0.379, ADQA 3/3),
waterfall (0.323, 3/3), and martial arts board break (0.315, 3/3). Sweep artifact:
`output/live_demo_preset_sweep.csv`.

## [2026-05-13] eval | QuerYD human AD + Gemini video-native breaks the frame ceiling

Added `tools/scenetwin_queryd_gemini_eval.py` and ran it on 5 QuerYD clips using real human
AD transcript windows from YouDescribe/QuerYD. Candidate tiers are transcript-derived:
cross-video negative, first utterance, first half, full AD window. Gemini Flash sees the real
trimmed MP4 segment and grades video-native ADQA. Result: CLIP rho = 0.617, Gemini ADQA rho =
0.865, ensemble rho = 0.932, pairwise ordered wins = 13/15, fully ordered = 3/5. This resolves
the VATEX confusion: video-native grading helps when candidates are actual AD transcripts,
not short caption-style candidates. Wiki page: [[research/scenetwin-queryd-video-native-eval]].

## [2026-05-13] live-demo + finding | Auto AD beat pro AD on held out VATEX clip

Rebuilt `demo/scenetwin_demo.py` after the Knowledge → Coding/SceneTwin migration. Two tabs: cached benchmark (18 clips, paths fixed, TRIBE need curve plot added) and Live YouTube (yt-dlp + 8 frames + GPT-4o-mini AD gen + ViT-B-32 CLIP + Claude Haiku ADQA). Cross model setup so the AD generator does not grade its own output. Built `demo/live_pipeline.py` with stages that return (ok, message, payload) and never throw, so the UI degrades gracefully when a stage's dep is missing. Robust yt-dlp fallback chain (tv_embedded + ios + mweb, then android + web_embedded, then Brave / Chrome cookies). New finding: on a held out VATEX clip (FtBS6OZSGMI, beer pour), the auto generated AD scored higher than the pro AD because the sampled frames caught the pre pour moment, so the pro AD's "filling the tall glass" claim was unsupported by the frames. Frame sampled scoring rewards static composition over temporal action. Headline rho = 0.929 still valid on VATEX benchmark categories which are composition heavy. Wiki page: [[research/scenetwin-frame-sampling-temporal-blindspot]].

## [2026-05-13] migration | Moved from Knowledge + njbda

Project split out from `~/Knowledge` (wiki/research/scenetwin*, tools/scenetwin_*, output/scenetwin*, output/reports/scenetwin-*, output/charts/scenetwin_*, demo/scenetwin_demo.py, output/logos/njbda*) and merged with the `~/njbda` workspace (clips, frames, TRIBE colab, eval scripts) under `~/Coding/SceneTwin`. Memory copied over: `project_scenetwin.md` (renamed from project_njbda.md) and `feedback_communication.md`. Knowledge wiki/index.md and MEMORY.md updated to drop SceneTwin entries.

## [2026-05-29] paper-push | Identified 3 mis-ordered clips (failure analysis)
All 3 violations (clip 0, 12, 14) at the T1->T2 boundary. T3 wins all 18. Pattern: ensemble correctly penalises crowd-sourced T2 length without information gain (factual errors, narration framing, filler). Paper failure-analysis subsection ready.
Created [[research/scenetwin-tier-ordering-failures]].

## [2026-05-29] paper-push | External generalization measured
CLIP+ADQA ensemble rho=0.873 on 60 unseen external clips x 4 tiers (n=240, p<3e-76). Drop from in-benchmark 0.929 is only -0.056. T3 pairwise wins 173/180 (96.1%). Cross-category rho range [0.81, 0.93] across 10 categories. This is paper headline #2. Created [[research/scenetwin-external-validation]].

## [2026-05-29] paper-push | Statistical power defense
4 significance tests all p<1e-15 (Spearman, Kendall, within-clip permutation, 54/54 binomial). Cluster bootstrap 95% CI [0.881, 0.962]. Min detectable rho ~0.325 vs observed 0.929; margin +0.604 above floor. Created [[research/scenetwin-statistical-power]].

## [2026-05-29] paper-push | TRIBE role honestly measured
Swept 12 TRIBE features against per-clip ensemble noise (within_clip_rho): all p>0.16, max |r|=0.34. TRIBE does NOT predict continuous ensemble quality. Gated-pipeline simulation: every threshold hurts rho. Abstention curve: flat. But TRIBE forecasts the binary all4_fail event at AUC=1.00 (different failure mode than the 3 ensemble mis-orderings; overlap=1). Recommended paper frame: "metric (CLIP+ADQA) + binary review-triage flag (TRIBE)" rather than "calibration layer." Created [[research/scenetwin-tribe-role-analysis]].

## [2026-05-29] paper-push | Paper baselines run on 60-clip external set
LLM-AD-Eval 0.857, CRITIC 0.613, multi_ref_r3 0.948 (reference-leakage suspect), CoAD -0.011, word_count 0.339. Ensemble lift over LLM-AD-Eval holds across corpora: +0.030 in-bench, +0.016 external. Critical caveat: reference-based metrics (LLM-AD-Eval, multi_ref_r3, token_overlap) get 180/180 T3 wins trivially since T3 IS their reference. Only the CLIP+ADQA ensemble's 173/180 (96.1%) is meaningful. Created [[research/scenetwin-external-baselines]].

## [2026-05-29] paper-push | External T3 pairwise losses characterized
7/180 losses on 60-clip external set. 5/7 beaten by T2_vatex_long, 2/7 by T1_vatex_short, 0/7 by T0_cross-decoy. 5/7 within margin 0.04 (reporting ties). 4/7 are Entertainment, 2/7 Health & Wellness, 1/7 How-to. Dominant failure: T3 abstracts editorial framing while T1/T2 literal about visible content. Created [[research/scenetwin-external-t3-losses]].

## [2026-05-29] paper-push | n=60 external + combined-corpus statistical defense
External (n=240): rho=0.8732, Kendall=0.756, permutation p<2e-4, bootstrap CI [0.836, 0.902], min detectable r=0.180. Per-category CIs across 10 unseen categories all have lower bounds >=0.665. Combined corpus (n=312, 78 clips, 11 categories): rho=0.8865, p<1e-100, min detectable r=0.158. Updated [[research/scenetwin-statistical-power]] with the bigger numbers.

## [2026-05-29] paper-push | Cross-paper synthesis promoted to wiki
Two new canonical pages: [[research/scenetwin-metric-landscape]] (10 baselines + 6 fusions + cluster correlations + external replication) and [[research/scenetwin-negative-results]] (what we tried that did NOT beat ensemble -- arguments for paper Negative Results subsection). Both promoted from cursor/papers/ findings into wiki/research/.

## [2026-05-29] paper-push | Signal decomposition (CLIP vs ADQA per corpus)
In-bench: CLIP lift over ADQA-only = +0.140. External: +0.006. Per-category external: +0.034 How-to (n=21), -0.036 Health & Wellness, neutral elsewhere. ADQA is the workhorse externally; CLIP adds controlled-benchmark stability + category-specific lift on visual-object content. Honest paper framing: "ADQA backbone + CLIP cheap insurance" rather than overclaim "dual-signal." Created [[research/scenetwin-signal-decomposition]].

## [2026-05-29] paper-push | Method inventory audit
28 scripts audited. 22 have measured outputs, 12 paper-derived stubs unrun (deferred to follow-up). Splits cleanly into Paper A (metric+benchmark, 19 keep) and Paper B (Access Surface OS, 7 routing scripts; target recall >=88% on n=58 external clips). Created [[research/scenetwin-method-inventory]].

## [2026-05-29] paper-push | Master paper outline written
Paper A: metric + benchmark (10 sections, 9 figure/table assets ready). Paper B: Access Surface OS (5 routing claims with target-recall numbers). Master outline at [[research/scenetwin-paper-outline]] maps each section to evidence pages + measurements + blockers. Writing order: A first (~2-3 weeks, all evidence locked except TRIBE §8.3), B during A's review.

## [2026-05-29] paper-push | Cross-paper synthesis promoted to corpus page
37-paper corpus consolidated to [[research/scenetwin-paper-corpus]]: 6 thematic clusters (A semantic, B narrative, C conflicts, D audio/longform, E user agency, F identity/deploy, G assistant, H task loop, I sidecars). Paper A baselines map to clusters A-D; Paper B Related Work uses E-I. Includes ready-to-paste Related Work skeletons for both papers.

## [2026-05-29] paper-push | multi_ref_r3 mismatch resolved + Paper B evidence consolidated
multi_ref_r3 jump from 0.532 to 0.948 was a name collision; recomputing with same formula gives in-bench 0.964 (also reference-leaking). Updated [[research/scenetwin-external-baselines]] with the clarification.
Paper B empirical evidence now in single page [[research/scenetwin-access-surface-os]]: 5 routing claims on 58 external clips, target recall >=88% per claim, cross-claim consistency table. Section 4 paper-ready.

## [2026-05-29] paper-push | Paper A headline figures rendered
4 figures committed to output/charts/:
- scenetwin_per_category_rho.png — 9 categories x bootstrap CI on 60 clips
- scenetwin_metric_correlation_heatmap.png — pairwise rho among 11 metrics (clustered)
- scenetwin_fusion_results.png — fusion bar chart (negative results)
- scenetwin_tribe_risk_coverage.png — TRIBE flagged 11% review budget = 100% recall
Each has a .py source. Saves writing-phase work.

## [2026-05-29] paper-push | Paper A draft skeleton written
output/reports/paper-A-draft.md instantiates the outline as a fillable scaffold: abstract + 10 sections + 3 appendices + writing TODO + figure inventory (all 4 PNGs referenced). All measured numbers locked into tables; prose paragraphs are placeholders. §8.3 (TRIBE counterfactual) is the one section explicitly marked "fill when Colab returns".

## [2026-05-29] paper-push | VLM-as-judge baseline protocol + cost matrix
Runner at cursor/research/vlm_as_judge_runner.py (Anthropic/OpenAI/Gemini). Cost matrix on full 78-clip x 4-tier = 312 calls: $1.02 (Gemini Flash) -> $9.92 (Claude Sonnet 4.6) -> $49.61 (Claude Opus 4.7). Recommended "Strong" tier: Sonnet 4.6 + Haiku 4.5 (~$12) for two-column comparison. Decision rule covers VLM-loses / ties / wins. Wiki page at [[research/scenetwin-vlm-as-judge-protocol]].

## [2026-05-29] paper-push | TRIBE counterfactual numbers integrated
Colab run returned per-clip data for 18 in-bench clips. Headline: accessibility_gap correlates with within_clip_rho at r=-0.453, p=0.059 (n=18). This is 33% larger than the maximum |r|=0.342 across 12 existing TRIBE features. Just misses p<0.05 but n=18 detection floor is ~0.45. description_gain ties existing top max_need at AUC=1.000 on low_tier3_margin -- theoretically motivated brain-counterfactual at parity with slot-score heuristic. Updated [[research/scenetwin-tribe-role-analysis]] (Open question -> RESOLVED) and Paper A draft §8.3. Calibration-layer story is back on the table awaiting n=60 external re-run.

## [2026-05-29] paper-push | VLM-as-judge runs launched + TRIBE writeup expanded
3 providers running in parallel on combined 78-clip corpus:
- anthropic claude-sonnet-4-6 (~$10)
- openai gpt-5 (~$8)
- gemini-2.5-pro (~$4)
Smoke tests passed on n=8: Claude 0.716, GPT-5 0.642, Gemini 0.736.
Discovered 2 quirks: GPT-5 needs max_completion_tokens (not max_tokens), Gemini 2.5 Pro burns reasoning tokens before output -- bumped budget to 4000.
Runner saves incrementally; resume-on-crash supported.
cursor/research/papers/tribe-v2.md expanded 37 -> 98 lines (dense). Conservative + aggressive paper claim wording, both versions, ready for Paper A §8.

## [2026-05-29] paper-push | VLM-as-judge results converging
Claude Sonnet 4.6 finished full 78-clip combined run: rho=0.713 (vs ensemble 0.886, gap -0.173). T3 pairwise wins 195/234 (83%) vs ensemble 227/234 (97%). Gemini and GPT-5 still finishing externals; partial: Gemini 0.756, GPT-5 0.727. Inter-VLM agreement 0.83-0.88. Headline trend locked: all 3 frontier VLMs land in [0.71, 0.76], decisively below our 2-signal ensemble. Created [[research/scenetwin-vlm-as-judge-results]]. Paper A §6.1 baselines table strengthens.

## [2026-05-29] paper-push | Paper B draft + BibTeX + analyzer
- Paper B draft skeleton at output/reports/paper-B-draft.md (10 sections; 5 routing claims; 3 figures pending render)
- BibTeX file at output/papers/scenetwin-references.bib (40 entries; arXiv fetch was rate-limited, used offline INDEX-based generation; first-author TODOs fillable from PDFs at submission time)
- VLM analyzer at cursor/research/vlm_judge_analyzer.py (auto-detects all per-provider CSVs and produces leaderboard + agreement + summary)

## [2026-05-29] paper-push | Head-to-head VLM-as-judge verified on identical clips
Zero label mismatches between ensemble CSVs and VLM CSVs (60 external clip overlap = 60/60). All 3 frontier VLMs land in the same ~0.21 in-bench / ~0.16 external gap range vs our ensemble:
- Gemini 2.5 Pro: in-bench gap +0.173
- GPT-5: in-bench gap +0.202
- Claude Sonnet 4.6: in-bench gap +0.216 (complete external: gap +0.159)
Per-clip win rate (Claude, external 60): ensemble better 26, VLM better 10, tied 24.
Paper A draft §6.1.1 (VLM-as-judge subsection) now has full numbers. Wiki [[research/scenetwin-vlm-as-judge-results]] updated.

## [2026-05-29] paper-push | 4 new figures rendered
- output/charts/scenetwin_competitive_map.png -- Paper A §6 headline (cost vs quality scatter; our green star at 0.929 with 30x lower cost than the cheapest VLM judge)
- output/charts/scenetwin_routing_target_recall.png -- Paper B Fig 2 (4 routing dims at 89-100% recall vs static baseline at 0%)
- output/charts/scenetwin_access_surface_sankey.png -- Paper B Fig 1 (5 surfaces x 4 compute tiers on 58 clips)
- output/charts/scenetwin_routing_consistency.png -- Paper B Fig 3 (pairwise Jaccard overlap heatmap; 0.69-0.96)
Paper A and B drafts updated to reference all figures.

## [2026-05-29] paper-push | TRIBE external + VLM full results integrated
### TRIBE external 60-clip counterfactual (Colab returned)
- Calibration test FAILED: accessibility_gap vs within_clip_rho_ext = +0.025 p=0.85 (was -0.453 p=0.059 at n=18).
- 18-clip emerging signal did NOT generalize. Calibration-layer paper framing CLOSED.
- T3 pairwise loss prediction (n=60, 6 positives): description_gain AUC=0.731 (best new feature), well below in-bench mean_standard_slot_score AUC=1.000.
- Paper now ships honest null. TRIBE contribution is in-bench binary review-triage flag only.

### VLM-as-judge full runs complete (all 3 providers, 78 clips each)
- Final verified head-to-head:
  - In-bench (n=72): Ensemble 0.929, Gemini 0.756, GPT-5 0.727, Claude 0.713. Gap +0.173.
  - External (n=240): Ensemble 0.873, GPT-5 0.739, Gemini 0.734, Claude 0.715. Gap +0.134.
  - Combined (n=312): Ensemble 0.886, Gemini 0.736, GPT-5 0.735, Claude 0.713. Gap +0.150.
- Inter-VLM agreement 0.83-0.85.
- Updated [[research/scenetwin-vlm-as-judge-results]] and competitive map figure.
- Updated [[research/scenetwin-tribe-role-analysis]] with the honest external null.

## [2026-05-29] query | TRIBE use-case found: accessibility gap localizes to visual cortex

Loaded full per-vertex counterfactual tensors (78 clips, P_AV/P_A/P_AD/P_AV_AD)
from `tribe_tensors_all78.zip` into `cursor/research/output/tribe_tensors/`.
New finding: the AV-vs-A gap concentrates in visual ROIs (retrosplenial, V1,
scene PPA) vs auditory/language controls, and holds external (perm p=5e-5,
n=60) where scalar calibration died. First anatomical, externally-generalizing
TRIBE result. New page `wiki/research/scenetwin-tribe-roi-localization.md`,
chart `output/charts/scenetwin_tribe_roi_localization.png`, analysis
`cursor/research/tribe_roi_gap_usecase.py` -> `output/tribe_roi_gap_per_clip.csv`.

## [2026-05-29] query | TRIBE use-case sharpened to typed accessibility gaps

Pushback: "isn't visual-cortex divergence obvious?" — yes. Ran the decisive
test (`cursor/research/tribe_roi_typing.py`): variance decomposition of the
per-(clip,ROI) gap = 20.5% clip-global (the scalar) + 24.7% fixed anatomy
(tautology) + 54.7% clip x ROI interaction (clip-specific typing a scalar
cannot capture). ROI gaps corr scalar only 0.19-0.57; dominant lost region
varies; scene-minus-agent gap orders categories (Food 0.32 ... Pets 0.12).
Reframed `scenetwin-tribe-roi-localization.md` to lead with typed gaps, not the
sanity check. Failure-flag prediction ruled out (inbench-only, 1-2 positives).

## [2026-05-29] query | Per-region neural closure tested -> negative (generalizes)

`cursor/research/tribe_roi_closure.py`: does P_AD move toward P_AV per ROI?
No. Adding the description moves the response AWAY from audiovisual in ~70% of
clips, even inside visual cortex (scene-PPA helps only 27% external;
auditory/language 0-2%) because P_AD injects spoken-language content P_AV never
had. Closure now closed per-region as it was at the scalar level. Typing
(54.7% clip x ROI) remains the sole live TRIBE use-case.

## [2026-05-29] query | Reframed TRIBE to its real role: corpus-wide AD-need schedule

Adarsha flagged that TRIBE was never meant to be a Spearman/quality metric.
Re-read the wiki: TRIBE is the upstream AD-NEED engine (when/what-kind to
describe), per scenetwin-neural-description-need-pivot (2026-05-02). Built the
corpus-wide schedule from the new per-timestep tensors:
`cursor/research/tribe_ad_need_schedule.py` -> `output/tribe_ad_need_schedule.csv`,
334 windows/78 clips incl. 60 external (first time out of bench). ~75% windows
flag AD need, ~80% spatial/scene. Updated scenetwin-neural-description-need-pivot
with a corpus-wide section. The 3 quality nulls (scalar/closure/routing) are
expected: TRIBE scores demand, not supply. Next differentiators: need-weighted
grounding at scale + gap-targeted AD loop.

## [2026-05-29] query | Need-weighted grounding at scale: 2-clip 0.976 did NOT hold

Ran real TRIBE per-timestep need-weighted CLIP on all 60 external clips
(`cursor/research/tribe_need_weighted_real.py` -> `output/tribe_need_weighted_real.csv`).
Real TRIBE need-weighted rho=0.642 vs plain clip_top3 0.631 = lift +0.011,
95% bootstrap CI [-0.009, +0.032] (crosses 0, P(>0)=0.86, NOT significant).
The prior 2-clip 0.976-vs-0.878 was small-n noise. BUT real TRIBE need beats the
motion+speech proxy (which hurt at -0.010), a ~+0.021 swing -- the fMRI signal
carries something the proxy doesn't, just not enough to move the headline.
Conclusion: TRIBE's defensible role is AD-need authoring/scheduling (generative),
not a metric lift. Quality-scorer and grounding-weight paths both closed.

## [2026-05-29] query | Gap-targeted AD loop SCALED to 60 external clips -> significant WIN

`cursor/research/tribe_gap_targeted_external.py`: built per-window TRIBE content
typing from the new tensors, generated baseline vs gap-targeted AD with Claude
Haiku, scored with the Phase-1 lexical scorer. Externally (60 clips):
dominant_keyword_coverage +0.295 (23W/2L, p<1e-4); profile_alignment +0.096
(17W/4L, p=0.0095, now significant vs p=0.105 on 2 in-bench clips);
specificity flat (no diversity loss, unlike in-bench). TRIBE's ROI need profile
causally steers LLM AD content -- the generative differentiator, validated
external. Output `cursor/research/output/tribe_gap_targeted_external_scores.csv`.
This is the strongest TRIBE result: significant + external + in its real
(authoring, not evaluation) lane.

## [2026-05-29] query | ADQA confirms gap-targeted AD is BETTER, not just different

`cursor/research/tribe_gap_targeted_adqa.py`: blind-graded generated baseline vs
gap-targeted AD against each external clip's fixed ADQA question set (Haiku
judge, reused stage4 grade_prompt). gap-targeted ADQA 0.348 vs baseline 0.297,
delta +0.052, 30W/18L/12T, Wilcoxon p=0.0085, 95% boot CI [+0.007,+0.095]
(excludes 0). End-to-end TRIBE differentiator complete: ROI need profile steers
LLM AD content (p<1e-4) AND the steered AD answers visual questions better
(p=0.0085), both external. Caveat: judge is same model family as generator;
harden with GPT-5/Gemini judge or BLV raters.
Output: cursor/research/output/tribe_gap_targeted_adqa_scores.csv

## [2026-05-29] query | Full-clip gap-targeted AD: effect COMPOUNDS (d=0.47)

Generated AD for ALL need windows/clip (not just top-2): 625 candidates/60 clips
(`tribe_gap_targeted_external_full_scores.csv`, GAP_MAX_WIN=99). Controllability
holds (dominant_kw +0.26 p<1e-4). ADQA on full-clip ADs
(`tribe_gap_targeted_adqa_full_scores.csv`): baseline 0.337 -> gap 0.417,
delta +0.080, 31W/13L, Wilcoxon p=0.0006, 95% CI [0.039,0.124], Cohen's d=0.47,
70% decisive wins = 23% of the caption(tier1)->pro(tier3) ADQA gap. Bigger than
the 2-window version (+0.052, d=0.30, 15%) -> per-window targeting is additive,
not a top-window fluke. Honest size: near-medium effect, prompt-only, no
retraining. Still a nudge not a transformation; judge is Haiku (cross-judge
hardening still open).

## [2026-05-29] query | SURGICAL: gap-targeted ADQA lift concentrates on TRIBE-flagged questions

`cursor/research/tribe_surgical_adqa.py` (per-question blind re-grade of full-clip
ADs, questions classified by content type, matched against each clip's dominant
TRIBE need type): on TRIBE-MATCHED questions lift=+0.167 d=0.55 p=0.0001 (n=60);
on unmatched questions lift=+0.051 d=0.15 p=0.0101 (n=235); matched>unmatched
Mann-Whitney p=0.0050. Matched lift = ~48% of caption(tier1)->pro(tier3) ADQA
gap. The clip-wide +0.080 average was diluting a 3.3x-larger targeted effect.
Mechanism claim: TRIBE predicts which visual facts an AD misses and targeting
recovers exactly those. Output cursor/research/output/tribe_surgical_adqa_perq.csv.
Still Haiku judge (cross-judge open); matched n=60 (~1 matched q/clip).

## [2026-05-29] query | Cross-judge (GPT-5): diffuse average is ~half bias, SURGICAL result holds

Re-graded full-clip ADs with GPT-5 (cross-family vs Haiku generator),
`cursor/research/tribe_crossjudge_adqa.py` -> `tribe_crossjudge_gpt5_perq.csv`.
Overall delta shrank +0.080->+0.037 (d=0.27, p=0.022) => ~half the clip-wide
average was Haiku-grading-Haiku bias. BUT the surgical dissociation is
judge-robust: MATCHED questions +0.113 d=0.43 p=0.0011, unmatched +0.017 d=0.05
n.s., matched>unmatched MW p=0.0149. matched lift ~32% of caption->pro gap.
Paper headline = the cross-family-robust MECHANISM (TRIBE recovers exactly the
flagged facts), NOT the diffuse average.

## [2026-05-29] query | Frontier generator (Opus) on high-need clips: LARGE matched effect (d=0.79)

Regenerated AD with Claude Opus (vs Haiku) on the 15 highest-headroom matched
clips (`tribe_gap_targeted_opus_subset_scores.csv`), GPT-5 cross-judge
(`tribe_crossjudge_opus_subset_perq.csv`). MATCHED questions lift +0.306 d=0.79
(LARGE) p=0.0047; unmatched +0.026 d=0.08 n.s.; matched>unmatched MW p=0.0004.
Apples-to-apples matched-q gap-targeted score (GPT-5 judge, same 15 clips):
Haiku-gen 0.000->0.300, Opus-gen 0.033->0.378, pro(tier3)~0.57 -> Opus recovers
~2/3 of the distance to professional AD on the flagged facts. CAVEAT: 15 clips
selected for low baseline (headroom), so "to-pro" has selection; the clean
non-circular results are matched>unmatched dissociation (p=0.0004) and
Opus>Haiku generator gain. Two true statements: global cross-judged average is
modest (+0.037 d=0.27); where TRIBE flags a clear need + strong generator, the
targeted effect is large and judge-robust.

## [2026-05-30] query | Opus 44-clip run hit credit limit at 17; non-circular dissociation HOLDS

Anthropic credits exhausted mid-run -> only 17/44 Opus clips generated
(`tribe_gap_targeted_opus_44_scores.csv`). These 17 are NOT headroom-selected
(non-circular). GPT-5 cross-judge (`tribe_crossjudge_opus_17_perq.csv`):
MATCHED +0.167 d=0.41 p=0.038, unmatched +0.000 d=0.00 p=0.52, matched>unmatched
MW p=0.0076; overall +0.047 d=0.34 p=0.063 (n.s.). CONFIRMS surgical
specificity non-circularly + cross-family. The 15-clip d=0.79 was inflated by
headroom selection; honest non-circular matched effect = d=0.41. Headline =
specificity (zero spillover to unmatched), not magnitude. TODO: top up Anthropic
credits to finish remaining 27 clips for full-44 n.

## [2026-05-30] query | NECESSITY: TRIBE beats a VLM "what's-missing" targeting baseline

`cursor/research/tribe_necessity_baseline.py` -> `tribe_necessity_perq.csv`.
Held generator+judge constant (gpt-4o), varied only emphasis source: baseline /
TRIBE-ROI-type / VLM-vision-picked-type, 44 matched clips. TRIBE & VLM agree on
dominant type only 14%. Symmetric check: on TRIBE's dimension tribe 0.524 > vlm
0.452 (p=0.003); on VLM's OWN dimension tribe 0.583 >= vlm 0.528 (vlm BELOW
baseline 0.556!, +0.056 n.s. n=18); neither's dimension no diff. Overall
non-circular tribe>vlm +0.018 p=0.023. => TRIBE non-redundant; VLM is a poor
need-detector (its emphasis doesn't beat baseline even on its own picks).
CAVEAT: VLM got frames only, NOT audio/transcript; TRIBE has P_AV-P_A (audio+video).
Fair rematch = give VLM a Whisper transcript, re-run. That's the gating experiment
for a locked necessity claim.

## [2026-05-30] query | FAIR rematch: transcript-armed VLM ~ ties TRIBE. Necessity NOT strongly established.

`cursor/research/tribe_necessity_rematch.py` -> `tribe_necessity_rematch_perq.csv`.
Gave the VLM need-detector the Whisper transcript (cached in
output/external_transcripts/) so it has TRIBE's cross-modal info. Results, 44 clips:
TRIBE-VLM agree only 9%; ALL-q tribe-vlm +0.020 p=0.025/0.0495(two-sided);
TRIBE-dim +0.065 p=0.021 (circular); VLM-dim TIE 0.656=0.656 (both > baseline
0.594). The frame-only VLM's picks were BELOW baseline; transcript fixed that ->
much of TRIBE's prior edge was the audio-info confound. HONEST VERDICT: TRIBE is
COMPETITIVE not necessary -- picks different targets (91% disagree), small
borderline overall edge, never loses, but a transcript-armed VLM is a viable
alternative. Paper claim drops from "TRIBE beats VLM" to "brain-grounded need is
a valid/effective targeting signal comparable to a strong VLM, identifying
different targets." Contribution = the grounding, not superiority.

## [2026-05-30] query | TRIBE vs human-priority: NEGATIVE (worse than VLM and worse than chance)

`cursor/research/tribe_vs_pro_priority.py` -> `tribe_vs_pro_priority.csv`. Does
TRIBE's need profile predict professional human AD content priority better than a
VLM? NO. cosine with pro-AD profile: TRIBE 0.361 < VLM 0.503 < uniform/chance
0.616. TRIBE-VLM -0.142 p=0.0021; TRIBE top-type matches pro top-type 15% (<20%
chance). TRIBE's peaked scene/spatial profile mispredicts the broad pro-AD mix.
Brain-response signal does NOT track human descriptive priority. Angle dead.
META: ~10 angles tested; TRIBE's only real capability = content steering
(p<1e-4) + modest surgical quality gain (d~0.4, intermittent). Competitive not
superior to VLM; not good at perceptual priority. Further computational fishing
= p-hacking risk. Remaining real lever = BLV human study (LLM judges structurally
can't reward perceptual-fit over semantic completeness).

## [2026-06-07] housekeeping | Pending-experiments doc + index catalog + Gemini block confirmed

Logged queued reruns (blocked only on LLM credits, not failures) in
`cursor/findings/NEXT-STEPS.md`: (1) re-run completeness/machine-AD graders with
Opus/GPT (one `--provider` flag; Gemini was the only live provider on 2026-06-07,
ties full==half on ~45% of clips => current rho=0.870 is a Gemini-floor); (2)
machine-AD tier needs an INDEPENDENT grader (Gemini self-graded its own AD =>
expert>machine only 22%); (3) 2 dropped clips. Catalogued the 2026-06 ladder
findings in `wiki/index.md` (new Findings section). Confirmed the 2 dropped clips
(`9eBhetL8n5Q_000222_000232`, `BHxn3qfPAl4_000018_000028`) are HARD-blocked by
Gemini at the input level (`prompt_feedback.block_reason=OTHER`, no candidates,
deterministic over 4 retries) -- a content-filter refusal on those frames, not a
bug; Opus/GPT will likely complete the set to 60. Ladder reported on 58 clips.

## [2026-06-07] query | Corrected-ladder rho=0.95 survives every knob (reviewer-defense)

`cursor/pipeline/corrected_ladder_robustness.py` -> `corrected_ladder_robustness.json`,
`output/charts/scenetwin_ladder_robustness.png`,
`cursor/findings/corrected-ladder-robustness.md`. Stress-tested whether the headline
3-tier rho (drop fake long-VATEX rung) is a tuned config. Recomputed from RAW
clip_top3 + ADQA signals over a full ensemble-weight sweep x 3 clip-wise norms +
cluster bootstrap + within-clip permutation null. RESULTS: weight sweep is a flat
PLATEAU (w=0.5 gives 0.957 in-domain / 0.952 OOD; best 0.967@w0.30 in-domain,
0.953@w0.85 OOD -- 0.5 is on the plateau, not a spike; rho stays high across all
w in [0.2,0.8]). Norm ablation OOD: minmax 0.952 / zscore 0.932 / rank 0.934.
Cluster-bootstrap 95% CI: benchmark [0.927,0.977], OOD [0.928,0.968] -- tight and
heavily OVERLAPPING, so OOD truly matches in-domain (gap closed, not hidden).
Permutation p=0.0002 (floor) both splits. The result is a property of the data,
not the configuration. Direct answer to "did you tune the weight to the number?".

## [2026-06-07] query | TRIBE can't lift OOD rho (structural) but flags failure clips (AUC 0.79, p=0.0018)

`cursor/pipeline/tribe_triage_corrected_ladder.py` -> `tribe_triage_corrected_ladder.json`,
`output/charts/scenetwin_tribe_triage.png`, `cursor/findings/tribe-clip-level-triage.md`.
Context: on the corrected 3-tier ladder OOD, ADQA-only=0.946 ~ ensemble=0.952, so
CLIP barely lifts rho; asked whether TRIBE can be the missing signal. ANSWER: no,
and provably so -- TRIBE's accessibility_gap is ONE value PER CLIP (video property,
constant across candidate ADs), so it is mathematically incapable of reordering
within-clip tiers -> cannot change rho. That is WHY all prior TRIBE-as-calibration
tests were null (p>0.16): wrong tool. What it CAN do, confirmed OOD on corrected
ladder: flag which whole clips the metric misorders. ADQA-only misorders 10/60 ->
gap 0.267(fail) vs 0.158(ok), AUC=0.79, MWU p=0.0018; flagging top-20% highest-gap
clips catches 60% of failures (top-30%->70%). Ensemble misorders 2/60 and those are
the 2 HIGHEST-gap clips of all 60 (AUC=1.00, p=0.0006, but n=2 underpowered).
FRAMING: SceneTwin is a two-layer system -- AD-level scoring (ADQA+CLIP) for rho,
clip-level TRIBE gap for review triage. Orthogonal by construction. Matches the
in-domain binary-triage result (AUC=1.00) and now generalizes OOD. NOT a rho claim.

## [2026-06-07] query | Marginal Description Value (new metric) -> honest negative + validity win

`cursor/pipeline/marginal_description_value.py` -> `marginal_description_value.json`,
`output/charts/scenetwin_mdv.png`, `cursor/findings/marginal-description-value.md`.
NEW reference-free idea (no humans): credit an AD only for visual info it adds OVER
the soundtrack (content-level analogue of TRIBE's AV-A gap). Grade each frame question
for answerability from the Whisper TRANSCRIPT alone, then score AD on visual-only
questions = MDV. Improves on maverix_audio_gate (keyword guess) by using real
transcripts + LLM answerability. RESULT on 60 OOD clips (Gemini): audio-redundant
credit = only 5.3% (no fully-redundant clip); leak concentrated in narration genres
(Health/Wellness 15%, Vlogs 10%, Food 7%) and 0% for Sports/Music/Film. Re-grounding
to MDV changes nothing: rho 0.869->0.859 (slightly worse), pro>crowd margin 0.348->
0.350 (both 95%). => hypothesis "metric leaks credit for restating audio" is FALSE
here. POSITIVE read: frame-grounded ADQA is audio-ROBUST -- a genuine vision metric,
not soundtrack paraphrase. Rebuts reviewer "you just reward restating the audio".
Use MDV as a threats-to-validity probe, NOT a replacement scorer. Honest negative.

## [2026-06-07] design | Neural Contrastive Retrieval (NCR) — built, results pending Colab

`cursor/research/tribe_ncr_dump_cell.py` (Colab producer) + `cursor/pipeline/
neural_contrastive_retrieval.py` (local analyzer, --selftest verified) +
`cursor/findings/neural-contrastive-retrieval.md`. NEW AD-dependent brain-grounded
score: feed candidate AD TEXT through TRIBE -> brain response to HEARING the AD,
mean-pool to q; for each clip's video response v=mean(P_AV), does q RETRIEVE the right
clip among 60? Score = rank-percentile + cosine margin. Designed to beat the two
confounds that killed neural closure/DescGain/MVRR: cosine+rank is magnitude-invariant
(kills verbosity) and language-injection becomes the SIGNAL (only clip-specific content
retrieves the right clip), giving the wrong-content control closure failed (tier0_cross
should retrieve its SOURCE clip ~chance, tier3 high). AD-DEPENDENT unlike accessibility_
gap. Runs on 60 external x 4 tiers (~300 TRIBE calls, ~3-4h T4). BLOCKED on Colab TRIBE
run (no local GPU/model). Analyzer + chart pipeline verified via synthetic selftest.
RISK stated: TTS-text is OOD for TRIBE + mean-pool loses time -> 60-way retrieval may
hit chance; if so, honest negative. Falsifiable, structurally distinct from dead branches.

## [2026-06-07] query | DUAL SIGNAL WINS on hard task: ensemble strictly dominates ADQA (p<0.001, 0 breaks)

`cursor/pipeline/dual_signal_complementarity.py` -> `dual_signal_complementarity.json`,
`output/charts/scenetwin_dual_signal_hardtask.png`,
`cursor/findings/dual-signal-complementarity.md`. Resolves the "+0.006 over ADQA is
nothing" objection. That +0.006 is on the SATURATED tier ladder (cross-vs-pro trivial,
both signals max out -> no headroom). Tested on the HARD completeness ladder
{cross<1sent<half<full} (truncations of the SAME expert AD), n=58: full ordering ADQA
21/58, CLIP 17/58, ENSEMBLE 37/58 (nearly 2x ADQA). Paired McNemar on hard adjacent
rungs (does adding CLIP fix ADQA's errors without breaking its correct ones?):
1sent<half ADQA 71%->ENS 88% (fixes 10, breaks 0, p=0.0010); half<full ADQA 55%->ENS
74% (fixes 11, breaks 0, p=0.0005). ZERO regressions both rungs = Pareto improvement,
not a trade-off. CLIP & ADQA make complementary errors; the second signal makes the
HARD completeness calls a single signal can't, and never costs a correct ordering.
This is the honest dual-signal contribution (was masked by benchmark saturation).
NOTE: global rho slightly favors ADQA (0.883 vs 0.867) bc CLIP's absolute scale is
noisier; the per-clip ORDERING (the deployed use) is where ensemble wins decisively.

## [2026-06-07] correction | RETRACT the dual-signal "domination" -- it was a tie artifact

Adversarial self-audit (prompted by user skepticism) overturns the entry above. The
"ensemble strictly dominates ADQA on completeness (half<full 55%->74%, fixes 11 breaks
0, p=0.0005)" claim is WRONG: artifact of strict `>` ordering with ties. ADQA is
discrete -> 26/58 EXACT TIES on half-vs-full, 0 inversions (full>=half by construction).
Strict `>` scores ties as ADQA failures; the continuous ensemble breaks them and looks
like it "fixes" 11. But on those 26 ties CLIP breaks correctly only 11, WRONG 15 (42%,
below chance, p=0.84). Under FAIR tie-aware scoring (tie=0.5): ADQA 0.776 > ENSEMBLE
0.741 -- ensemble is WORSE. "breaks 0" is near-automatic given how ties interact with
strict ordering. => on hard completeness rungs the dual signal does NOT beat ADQA;
CLIP cannot separate half vs full. SEPARATELY re-audited the 3-tier {cross<crowd<pro}
ordering: ADQA ties tier1-vs-tier3 only 2/60, so the 50->58 gain is NOT a tie artifact
and survives tie-aware (0.954->0.983), but is small and at the cross/crowd boundary.
METHOD LESSON: always score ordering tie-aware; strict full_order/pairwise-win silently
over-credit a continuous signal breaking a discrete one's ties. Finding doc rewritten
as a retraction. Honest position restored: ADQA workhorse, CLIP modest/regime-specific.

## [2026-06-07] hallucination sensitivity | The dual-signal outcome, done WITH a control
Reframed away from ρ/p toward an OUTCOME: would the metric notice if an AD lied? Built
cursor/pipeline/hallucination_gate.py. For 60 OOD clips, corrupt the human expert AD's
2-3 concrete visual facts into same-length plausible falsehoods (bald->long-haired,
cymbal->snare, blue->red mittens; ±0.8 words) AND a faithful-paraphrase control (reword,
facts intact). Score each twin against frames with ADQA + CLIP.
RESULTS: (1) ADQA has a structural hallucination BLIND SPOT — ties the lie with the
truth on 17/60 clips (28%) because the fabricated fact isn't a probed question; catches
70% overall, low paraphrase false-alarm (18%). (2) CLIP visual grounding is FABRICATION-
SPECIFIC: grounding drops +0.037 for a lie vs +0.008 for a paraphrase (~5x, paired
Wilcoxon p<1e-4), and on the 17 ADQA-blind clips CLIP catches 100% (drop +0.035 vs +0.006,
p=1e-4). So the two signals are complementary BY CONSTRUCTION, not redundant.
This is the legitimate version of the dual-signal claim retracted earlier today: it has a
control, uses magnitude not sign, and is significant on the subset that matters.
HONEST CAVEAT: raw "expert beats candidate" sign is biased (CLIP false-alarms 65% on
benign paraphrase), so a fielded detector must threshold grounding-drop magnitude, not
sign. Hallucinations generated by the grader family (Gemini); independent-grader rerun
queued. Findings: cursor/findings/hallucination-gate.md; chart:
output/charts/scenetwin_hallucination_gate.png.

## [2026-06-08] hallucination GATE | Calibrated operating point: deployable with a reference, not zero-shot
Pushed the sensitivity result into a real gate with an ROC + operating point (10% FPR) on
the same 60 clips (expert AD vs same-length lie vs faithful-paraphrase control). Built
cursor/pipeline/claim_level_gate.py (zero-reference) and cursor/pipeline/gate_summary.py
(comparison). RESULTS: (1) ZERO-REFERENCE single-AD gate — decompose AD into atomic visual
claims, flag by weakest CLIP claim grounding — is NEAR CHANCE (AUC 0.58, 17% recall@10%FPR;
within-AD min-z variant worse at 0.46). Absolute per-claim grounding too noisy (true abstract
claims ground as low as fabricated objects). Claim-level fabricated-vs-true is a modest AUC
0.69 (0.197 vs 0.237) -> useful only for highlighting suspect claims, not auto-reject.
(2) WITH-REFERENCE gate (score candidate's grounding DROP vs a trusted/2nd AD) is STRONG:
CLIP-drop AUC 0.84 (70% recall@10%FPR), ADQA-drop 0.80, and CLIP+ADQA FUSED AUC 0.90
(72% recall@10%FPR). Dual signal pays off operationally (0.84/0.80->0.90), consistent with
the complementarity finding. DEPLOYMENT: ship as a reference-comparison gate (QA pipelines
usually have a prior/2nd AD); do not ship zero-shot single-AD auto-reject.
Independent-grader rerun still blocked: confirmed 2026-06-08 Anthropic balance too low /
OpenAI quota exceeded; gate DECISION is CLIP (grader-free) so ROC is grader-independent.
Findings: cursor/findings/claim-level-gate.md; chart: output/charts/scenetwin_gate_summary.png.

## [2026-06-08] gate review holes closed + paper subsection | headline CLIP 0.84, not fusion 0.90
Before writing the AD safety gate subsection: (1) hand-authored 18 fabrications
(cursor/data/human_hallucinations.jsonl, zero API) to break Gemini circularity — CLIP
grounding-drop vs expert ref AUC=0.91, mean drop +0.069 (lie) vs +0.005 (paraphrase);
Gemini lies on same 18: AUC=0.94. (2) self-consistency gate: reference = 2nd model
generation (machine AD / bon c0), clean = alt candidates c1-c3, n=5 clips / 15 clean
pairs, AUC=0.76 (preliminary, cache-limited). Locked paper subsection at
output/reports/paper-ad-safety-gate.md: LEAD with CLIP-only grader-free gate AUC=0.84,
70% recall @ 10% FPR (n=60); fusion 0.90 footnoted as grader-dependent; zero-reference
claim gate AUC=0.58 reported as honest negative. No demo work.

## [2026-06-09] agent loop stopped + gate synthesis cataloged | Codex consolidation commit 0d1a633
Recorded the stopped Claude+Codex agent loop in the wiki after the supervisor was killed
by user request at 2026-06-09T18:00:00Z. Canonical state lives in
cursor/agent_loop/state.json (`loop_status: stopped`, `stopped_by: user`, Codex
`status: done`, commit `0d1a633`) and cursor/agent_loop/log.md. Codex synthesis lives at
cursor/findings/agent-loop-gate-synthesis.md and supports the paper subsection in
output/reports/paper-ad-safety-gate.md: lead with grader-free CLIP grounding-drop gate
AUC 0.835 / 70% recall @ 10% FPR; keep CLIP+ADQA fusion AUC 0.904 as grader-dependent;
report zero-reference weakest-claim gate as an honest negative (AUC 0.585).
