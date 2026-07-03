---
title: SceneTwin Loop D13 — Combined reference-free omission + fabrication error scorer
category: research
tags: [scenetwin, loop, error-detection, omission, fabrication, fusion, ranking]
created: 2026-07-02
---

# D13 — Combined reference-free omission + fabrication AD-error score

Merge the two round-2 reference-free signals into ONE AD-error score and test whether a
single combined score is worth it:

- **Fabrication** (D7): fused z-normalised CLIP-drop + ADQA-drop, mean-fusion AUC 0.904 (60 clips).
- **Omission** (D6): fraction of key visual facts the AD fails to state, clip-level AUC 0.945.

Script: `cursor/research/loop_d13_combined_scorer.py` (stdlib only, cached data only).

## Task 1 — Detection (gold vs hallucinated)

Evaluated on the **23 probe-labelled clips** present in both `probes.csv` and
`halluc_gate.csv` (46 per-AD instances: 23 gold + 23 hallucinated). Per-AD, reference-free
error scores, oriented so higher = more error; AUC = P(hallucinated > gold).

| Signal | AUC | perm p | notes |
|---|---|---|---|
| Fabrication (fused −z CLIP, −z ADQA, per-AD) | **0.809** | 0.0002 | reference-free per-AD form of D7 |
| Omission (1 − key-fact mention rate) | **0.945** | <1e-4 | reproduces D6 exactly |
| **Combined (z-mean of fabrication + omission)** | **0.941** | <1e-4 | — |

**The combined score does NOT beat omission alone (0.941 < 0.945).** Fusing the weaker,
partly-redundant fabrication signal into the omission signal *slightly dilutes* it.
The two signals are correlated (Spearman 0.595 across the 46 instances) — they co-occur by
construction (a hallucinated AD both omits the true fact and asserts a false foil), so there
is little independent information to gain.

Secondary check (D7's own task, fab-vs-paraphrase z-drops, paired, on these 23 clips):
CLIP-drop AUC 0.905, ADQA-drop 0.769, **mean-fusion 0.921** — i.e. fusion still helps for the
fabrication-vs-faithful-paraphrase job it was designed for (edges D7's 60-clip 0.904; small n).

### Honest limitations (Task 1)
- **n is tiny** (23 clips). AUC differences of ±0.02 are within noise; treat the ordering as
  directional, not decisive.
- **Two different hallucinated generations.** The fabrication CLIP/ADQA come from
  `halluc_gate`'s `halluc_text`; the omission labels come from the probe set's
  `hallucinated_ad` — these are *different* hallucinated ADs of the same clip (the gold/expert
  AD is identical across both files). So the combined score is a clip-level hallucinated-
  *condition* indicator, not a single-text score. A true same-text combined score would need
  CLIP/ADQA scored on the probe-set hallucinated AD (not cached).
- Omission and fabrication are correlated here, so the combined AUC is essentially omission-
  driven.

## Task 2 — Ranking on the tier ladder

Baseline pooled Spearman rho of `ensemble_mean_clip_top3` vs `gt` (60 ladder clips):

| Ladder | rows | rho |
|---|---|---|
| 4-tier as cached (incl. invalid T2 long-VATEX) | 240 | 0.8732 |
| **3-tier corrected (T0_cross < T1_vatex_short < T3_va11y)** | 180 | **0.9473** |
| canonical `recompute_corrected_ladder.py` (re-normalised 3-tier ensemble) | 180 | 0.9516 |

The ensemble already ranks the corrected ladder very well (rho ≈ 0.95).

**Omission/fabrication-aware ranking term: BLOCKED.** Computing an omission score per tier
needs the **AD text for every rung** (tier0_cross, tier1_vatex_short, tier3_va11y) of all 60
ladder clips, plus probe-style key-fact mention labels per tier. Cached data has AD text +
mention labels only for **tier3 (pro = `truth_ad`) and one hallucinated variant, and only for
the 23 probe clips**; `external_ensemble_eval.csv` carries no AD text at all.

**Spec to unblock:** obtain/generate per-tier AD text for all tiers × 60 clips → run the D6
key-fact extractor + phrase-match mention detector per tier → add an omission-penalty term to
the ensemble and recompute the 3-tier ladder rho (and check whether it recovers the known
T1-vs-T3 pairwise losses, cf. D15).

## Task 3 — Verdict

**A single combined error score is not worth it; keep DETECTION (fusion) and RANKING
(ensemble) as separate modules** — consistent with the round-2 synthesis.

1. For **gold-vs-hallucinated detection**, omission alone (0.945) already dominates; adding
   fabrication produces a slightly *lower* combined AUC (0.941) because the signals are
   correlated (rho 0.595) and fabrication is weaker per-AD. Omission is the single best
   reference-free error signal.
2. **Fusion still earns its keep in its own lane** — fabrication-vs-faithful-paraphrase,
   where the fused z-drop reaches 0.921 (≈ D7). Different job, different signal stack.
3. **Ranking** is already handled well by the CLIP+ADQA ensemble (rho ≈ 0.95); an omission-
   aware term cannot even be tested on cached data (BLOCKED), so there is no evidence it would
   help and clear evidence the ensemble does not need it.

Bottom line: ship **omission as the primary reference-free error detector**, keep the fused
CLIP+ADQA fabrication gate for the paraphrase-vs-fabrication distinction, and keep the ensemble
as the ranking module. Do not collapse them into one score.
