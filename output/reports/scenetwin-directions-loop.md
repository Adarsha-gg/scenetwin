---
title: SceneTwin research-directions loop — running findings
category: research
tags: [scenetwin, new-directions, loop, error-detection, subagents]
created: 2026-07-02
updated: 2026-07-02
---

# SceneTwin research-directions loop

Running log of an autonomous "propose direction → implement on cached data → record
result" loop. Rules for every round: **stdlib-only Python**
(`%LOCALAPPDATA%\Programs\Python\Python313\python.exe`, no numpy/scipy/sklearn/pandas/PIL),
**cached data only** (no API/GPU/human/network), and **no fabricated numbers** — a
direction that needs missing data is recorded as BLOCKED with a spec. Each round's scripts
live in `cursor/research/`; per-direction detail in `output/reports/scenetwin-loop-*.md`.

---

## Round 1 (done) — see `scenetwin-new-directions-run.md`

| Dir | Result | Status |
|---|---|---|
| D1 error-taxonomy detector | CLIP fab-vs-paraphrase AUC **0.835**, ADQA 0.801; ADQA blind 30%, CLIP catches those 18/18 | done |
| D2 comprehension target | gold ADs state the key visual fact only **61.8%** of the time (38% omissions) | done |
| D3 video-native scorer | 51% of QA is relation/action/count; ADQA 30% blind → motivated | BLOCKED (GPU) |
| D4 cheap-proxy fight | accessibility_gap AUC **0.794** (p=0.0023) > best cheap 0.714, thin vs cheap-ensemble 0.778 | done (visual proxies BLOCKED) |
| D5 cost Pareto | ρ 0.952 @ ~$1 no-ref vs frontier VLM 0.847 @ ~$50 | done (real-AD eval BLOCKED) |

---

## Round 2 (in progress)

Directions under test this round (implemented by parallel subagents):

- **D6 Omission scorer** — turn D2 into a reference-free score: per candidate AD, does it
  convey each key visual fact? Detection of omissions across tiers.
- **D7 Fused error detector** — combine CLIP-drop + ADQA-drop (max/OR/logistic-free) for
  fabrication detection; test lift over either alone (D1 complementarity).
- **D8 Operating points / decision curve** — convert the fab-detector AUC into recall@FPR
  and PPV/net-benefit under realistic AD-error base rates.
- **D9 Paraphrase false-alarm audit** — quantify CLIP/ADQA false-alarm on faithful
  paraphrase; magnitude vs sign; pick a deployable threshold.
- **D10 Severity-weighted error score** — weight errors by type (who_role/action >
  object) and test whether severity-weighting sharpens detection/ranking.
- **D11 Combined triage queue** — fuse accessibility_gap + CLIP-drop + ADQA-margin into
  one review-priority queue; recall@budget vs each alone.
- **D12 Question-type ADQA reliability** — per-type reliability weights for ADQA.

### Round 2 results

**D6 — Reference-free omission scorer (done).** Detail: `scenetwin-loop-d6-omission.md`.
- Expert/gold AD omits the probed key fact **38.2%** of probes; hallucinated AD omits **96.1%**.
- Separation (hallucinated = higher omission): probe-level AUC **0.789** (perm p<0.0001); **clip-level AUC 0.945** (21/23 clips, 0 reversals).
- Experts omit **who_role (50%)** and **action (43%)** most, counts least (15%).
- Independent lexical check: a strict whole-phrase substring detector reproduces the cached mention labels at **94.7%, 0 false positives** — so a purely reference-free omission detector is feasible; bag-of-token overlap over-fires (use phrase matching).
- Honest: omission and fabrication co-occur by construction here (correlated, not cleanly separable); omission is the broader signal, fabrication complementary.

**D9 — Paraphrase false-alarm audit (done).** Detail: `scenetwin-loop-d9d10-falsealarm-severity.md`.
- Naive **sign** rules are undeployable: CLIP-sign flags **65%** of faithful paraphrases; ADQA-sign 18.3%.
- **Magnitude** thresholding is the deployable signal: at a fixed 10% paraphrase false-alarm budget, CLIP catches **65%** of fabrications, ADQA 53%.
- Distributions confirm separation (CLIP fab mean +0.037 vs para +0.008). **Ship the CLIP-magnitude gate, never a sign rule.**

**D10 — Severity-weighted error score (done, NEGATIVE).**
- Not supported: severity (probe-type) vs drop magnitude Spearman CLIP +0.148 (p=0.50), ADQA +0.010 (p=0.97). High-severity clips show *slightly smaller* drops — signals are weakest exactly on the errors judged most severe. n=5 relation/action/count, so directional only. Honest negative; a real severity target likely needs a video-native signal (D3).

**D7 — Fused error detector (done).** Detail: `scenetwin-loop-d7d8-fusion-oppoints.md`.
- z-normalized CLIP-drop + ADQA-drop. **Mean fusion AUC 0.904** (best), vs CLIP 0.835 / ADQA 0.801 alone — **+0.069, perm p<1e-4**. Fusion genuinely beats either single signal (validates the D1 complementarity), though the gain is modest.

**D8 — Operating points / decision curve (done).**
- Recall at FPR 5/10/20%: **fusion 66.7 / 75.0 / 86.7%**, beating CLIP and ADQA at every point.
- PPV at 10% FPR = 28 / 57 / 76% at base rates 5 / 15 / 30% → precision is base-rate-limited: this is **triage, not an auto-reject gate**.
- Decision curve: flagging beats review-all/review-none for harm thresholds ~1.4–28% (π=5%), widening to ~11–76% (π=30%).

**D11 — Combined triage queue (done, NEGATIVE).** Detail: `scenetwin-loop-d11d12-triage-qtype.md`.
- Fusing signals does **not** beat `accessibility_gap` alone for ADQA-failure triage: best honest rank-fusion AUC 0.800 vs 0.794 (Δ+0.006, within n=10 noise); accessibility_gap alone wins recall@10/20/30% budgets (0.40/0.60/0.70). **Ship accessibility_gap as the single triage signal.**

**D12 — Question-type ADQA reliability (done, UNBLOCKED).**
- Per-question grades were cached (`output/scenetwin_timing_20clip/*/grades.csv`); joined 684 typed questions → 2,736 graded instances, 0 unmatched.
- Tier3-vs-tier0 discrimination AUC by type: **action_relation 0.959**, count 0.920, other 0.917, who_role 0.899, spatial_relation 0.818, object_attr 0.811. All types work; the two weakest (spatial/attribute) have pro-AD yes-rates ~0.53–0.56 — **even gold ADs omit fine spatial/attribute detail** (converges with D2/D6 omission finding).

### Round 2 synthesis

1. **Error DETECTION benefits from fusion (D7: 0.904), but review TRIAGE does not (D11: use accessibility_gap alone).** Two different jobs, two different signal stacks — a clean paper structure.
2. **Omission is the biggest untapped signal.** D6 (clip AUC 0.945), D2 (38% of key facts omitted), and D12 (gold ADs weakest on spatial/attribute) all point the same way. A reference-free omission scorer is feasible and novel.
3. **Deployment reality:** CLIP-magnitude gate (D9), triage-not-gate PPV (D8), severity-weighting unsupported by current signals (D10) — honest boundaries for the paper.

---

## Round 3 (in progress) — synthesis toward paper-ready artifacts

- **D13 Combined omission+fabrication scorer** — merge D6 omission + D7 fused fabrication into one reference-free AD-error score; evaluate on BOTH the tier ladder (ranking) and fabrication/omission detection.
- **D14 Claim/sentence-level localization** — can we point to WHICH claim is wrong/omitted (not just clip-level), reference-free, using lexical spans + cached mention labels? Measure localization accuracy vs known swap spans.
- **D15 Omission-aware ensemble** — add an omission penalty to CLIP+ADQA; test 60-clip ladder ρ and whether it recovers the known T3 pairwise losses.
- **D16 Question-type-reweighted ADQA** — reweight ADQA by D12 per-type discrimination; test whether ladder ρ improves.

_Results appended below as subagents report._

### Round 3 results

**D13 — Combined omission+fabrication scorer (done, NEGATIVE for fusion).** Detail: `scenetwin-loop-d13-combined-scorer.md`.
- Detection (gold vs hallucinated, 23 probe clips, per-AD): omission alone **AUC 0.945** (reproduces D6), fabrication alone (per-AD fused −z CLIP/ADQA) 0.809, **combined 0.941** — combining does **not** beat omission alone; it slightly dilutes it. Signals correlated (Spearman 0.595, co-occur by construction).
- Fusion still wins its own task (fab-vs-paraphrase z-drop on 23 clips, mean-fusion **0.921** ≈ D7 0.904).
- Ranking baseline: `ensemble_mean_clip_top3` vs gt pooled Spearman **0.947** (3-tier corrected; 0.873 with invalid T2; canonical recompute 0.9516). Omission-aware ranking term **BLOCKED** — no per-tier AD texts cached for the full ladder (spec in detail report).
- Verdict: **keep detection (fusion) and ranking (ensemble) as separate modules; ship omission as the primary reference-free error signal.** Do not collapse into one combined score.

**D14 — Claim/sentence-level localization (done, NEGATIVE for reference-free).** Detail: `scenetwin-loop-d14-localization.md`.
- Alignment: **60/60** clips cleanly alignable (equal sentence counts); mean 3.55 sents/clip, 2.30 changed; the alignment diff is the literal error-location ground truth.
- Reference-free text-only top-1 localization = **0.917**, but a trivial "pick first sentence" prior also = **0.917** (content lift over structure **+0.000**). The opening scene-setting sentence is changed 55/60 vs the closing mood sentence 15/60 — the "signal" is a positional/boilerplate artifact, **not error-specific**. Reference-free claim localization is **not demonstrated**.
- Reference-COMPARISON path works: sentence diff recovers a changed sentence **100%**; probe swaps are lexically clean **52.6%** (cached fuzzy labels). Note: probe `swap_text` foils are QA distractors, not literal edits (exact foil-in-halluc only 3.9%) — use the alignment diff as GT.
- **BLOCKED:** a genuine zero-reference localizer needs per-sentence visual grounding (per-claim CLIP frame-match / frame-grounded ADQA) = video+CLIP/API calls, uncached here. Only that can separate a *wrong* claim from a merely *detailed* one.

**D16 — Question-type-reweighted ADQA (done, NULL — equal-weight wins).** Detail: `scenetwin-loop-d16-qtype-reweight.md`.
- Equal-weight ADQA ranks tiers at **ρ = 0.932** (perm p=0.00005). Reweighting by D12 per-type discrimination gains at most **+0.0019 ρ** (bootstrap Δρ CI includes zero); dropping weak types *hurts* (−0.0026).
- Ablation: **all questions 0.932 > scene-model-only 0.915 > non-scene-model-only 0.885** — discarding questions hurts. Per-type reliability is a useful diagnostic, **not** a ranking weight. Ship equal-weight (parsimony). Caveat: small n, near-ceiling ladder, in-sample weights.

**D15 — Omission-aware ensemble (done, NULL).** Detail: `scenetwin-loop-d15-omission-ensemble.md`.
- Baseline ladder ρ reproduced exactly (**0.9516**). Omission proxy (adqa_yes_rate coverage; true per-tier omission BLOCKED, not cached) is largely redundant with ADQA (r=0.85). Weight sweep peaks at w=0.10, **ρ=0.9597 (+0.008)** — within bootstrap noise, perm-p unchanged (0.0002).
- **T3-loss recovery: 0/2** (both losses are zero-coverage CLIP-driven flips the omission term is blind to).
- Verdict: keep omission as a **detection** signal (D6); do not fold into ranking.

### Round 3 synthesis — two convergent meta-findings

1. **Parsimony is confirmed, four independent ways.** Combining omission+fabrication (D13),
   folding omission into ranking (D15), reweighting ADQA by question type (D16) all give
   ≤ +0.008 ρ/AUC (within noise), and discarding questions *hurts*. The existing modular
   design — fused CLIP+ADQA for **detection** (0.904), ensemble for **ranking** (0.952),
   accessibility_gap for **triage** (0.794), omission as a **standalone detector** (0.945)
   — is at a local optimum. This directly fills the paper's Negative-Results/parsimony section.
2. **The cached-data frontier is reached; the critical path is now visual grounding.**
   Every remaining high-value direction — claim-level localization (D14), severity (D10),
   video-native temporal scoring (D3) — converges on the *same* blocker: **per-sentence /
   per-claim / temporal visual grounding**, which needs GPU or API calls not available in
   the loop. D14 made this concrete: reference-free text-only localization is a positional
   artifact (+0.000 over a first-sentence prior); a real zero-reference localizer needs
   per-claim frame grounding.

**Deployable stack after 3 rounds (all reference-free):** omission detector (AUC 0.945) +
fused fabrication gate (0.904, CLIP-magnitude, 75% recall @10% FPR) as **detection**;
CLIP+ADQA ensemble (ρ 0.952) as **ranking**; accessibility_gap (0.794) as **triage**.

---

## Round 4 (in progress) — pivot: consolidate + mine unused data + scaffold the unblock

Round 3 hit diminishing returns on "combine/reweight" ideas, so round 4 pivots:
- **D17 Paper-ready synthesis section** — draft a "Reference-free AD Error Detection"
  results section from D1–D16 (writing; cached).
- **D18 Unused-data direction hunt** — inventory cached outputs not yet used
  (best_of_n_rerank, ref_subst, clip_consensus, tribe_matched_scene_model_challenge,
  core20_scene_model_benchmark, ad_experience_audit, decisive_scene_model_validation) and
  RUN one or two genuinely new cached-data directions from them.
- **D19 Unblock scaffold** — write the one-command runnable spec + scaffolded runner for the
  video-native / per-claim-grounding experiments (no execution; ready for GPU/API green-light).

### Round 4 results

**D17 — Paper-ready error-detection section (done).** Wrote `scenetwin-error-detection-section.md`:
a drop-in "Reference-Free Audio-Description Error Detection" manuscript section with the
3-module stack, a negative-results/parsimony subsection, limitations, and a results table.

**D18 (unused-data hunt) and D19 (unblock scaffold) — INCOMPLETE.** Both subagents died on a
session/rate limit before writing outputs (resets 10:20pm ET). Carried to round 5.

**D21 — Cheap visual proxies vs TRIBE neural gap (done — UNBLOCKED the round-1 D4 fight).**
Detail: `scenetwin-loop-d21-visual-proxy.md`. Installed a numpy+Pillow venv (`.venv_np`,
user-authorized) and computed frame-difference motion / scene-cut / brightness / detail
proxies from cached JPG frames for the 18 clips with both frames and a TRIBE signal.
- **TRIBE's accessibility GAP is NOT reducible to cheap visual motion** — no proxy predicts
  `tr_mean_cosine_gap` at significance (best motion_max ρ=+0.44 p=0.069, duration +0.45
  p=0.059; both fail an honest permutation test at n=18). **Defends TRIBE's necessity**:
  combined with round-1 D4 (beat cheap text/metadata proxies, AUC 0.794), the neural gap
  now also survives cheap *visual* proxies.
- **Honest nuance:** the TRIBE *need timeline* partly tracks **brightness variability**
  (ρ≈+0.6, p<0.01); the triage "gap" signal does not. Caveat: n=18, frame-sample stats not
  dense optical flow.

### Round 4 synthesis

- The visual-proxy result closes the last open cached-data question from round 1: TRIBE
  earns its place against both cheap *text* and cheap *visual* baselines (with a fair
  need-timeline-vs-brightness caveat). The reference-free detection stack now has a clean
  parsimony story on every axis tested.
- Cached-data frontier is genuinely exhausted for novel *scoring* gains. Remaining work:
  (a) round-5 finish of D18/D20 unused-data mining + D19 unblock scaffold (non-gated, just
  interrupted by the limit), and (b) the visual-grounding unblock (video-native D3,
  per-claim localization D14) needing GPU/API or a torch venv.

_Round 5 (after limit reset): re-run D18 + D19; then decide on the torch/API unblock._
