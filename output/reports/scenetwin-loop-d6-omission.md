---
title: "SceneTwin Loop D6 — Reference-free Omission Scorer"
category: research
tags: [scenetwin, omission, reference-free, hallucination, adqa]
created: 2026-07-02
---

# D6 — Reference-free Omission Scorer

**Motivation.** Gold professional ADs state the probed key visual fact only
~61.8% of the time, so a *reference-keyed* ADQA is blind to omissions (it can
only ask about facts the reference AD happens to contain). This loop builds and
evaluates a **reference-free omission score**: for each clip, the fraction of
its probed key facts (`true_answer` terms) that the AD fails to mention.

Data: `cursor/output/relational_hallucination_probe_set/probes.csv` (76 probes,
23 clips) joined to AD texts in `cursor/output/halluc_gate/halluc_gate.csv`
(all 23 clips present). Script: `cursor/research/loop_d6_omission.py`.

## 1. Omission from cached mention labels

Omission(probe) = `1 - *_ad_mentions_true`; clip omission = fraction of that
clip's probed facts omitted.

| AD | probe-level omission | clip-level omission |
|----|---------------------|---------------------|
| Expert / truth | **0.382** (29/76) | 0.396 |
| Hallucinated   | **0.961** (73/76) | 0.966 |

The expert AD omits the probed fact ~38% of the time (mirrors the established
~62% coverage). The hallucinated AD omits it almost always — as expected, since
each foil swap replaces the true term.

## 2. Omission rate by probe type

| probe_type | n | expert omit | halluc omit |
|------------|---|-------------|-------------|
| action_relation  | 37 | 43.2% | 97.3% |
| spatial_relation | 16 | 37.5% | 100.0% |
| count            | 13 | 15.4% | 92.3% |
| who_role         | 10 | 50.0% | 90.0% |

Expert ADs omit **who_role** and **action_relation** facts most (43–50%) and
**count** facts least (15%). The hallucinated AD omits ~90–100% across all
types.

## 3. Does omission separate expert from hallucinated ADs?

Treating hallucinated as the higher-omission positive:

- **Probe-level AUC = 0.789** (label-permutation best-direction p < 0.0001,
  n=20000). Capped below 1.0 because the score is binary 0/1 and the expert AD
  itself omits 38% of probes (ties).
- **Clip-level AUC = 0.945**; the hallucinated AD omits strictly more than the
  expert AD in **21/23 clips** (2 ties, 0 reversals).

Omission is a strong reference-free separator, especially aggregated per clip.

## 4. Independent lexical detector vs cached labels (the real test)

To check whether a *purely lexical, reference-free* detector reproduces the
cached `truth_ad_mentions_true` labels, two detectors run `true_answer` against
`expert_text`:

| detector | agreement | TP | FP | FN | TN |
|----------|-----------|----|----|----|----|
| **A — whole-phrase substring** | **94.7% (72/76)** | 43 | 0 | 4 | 29 |
| B — ≥50% content-token overlap | 64.5% (49/76) | 47 | 27 | 0 | 2 |

The strict substring detector nearly reproduces the cached mention signal with
**zero false positives** — when the phrase literally appears, the cached label
always agrees. Its only 4 misses are paraphrase/synonym cases (e.g. cached says
"mentioned" but the exact phrase is not a substring). This is the headline
positive result: **a trivial reference-free lexical omission detector recovers
the cached omission labels at ~95%.**

The loose token-overlap detector over-fires (27 FP): generic tokens ("man",
"woman", "on") match everywhere, so it declares facts "mentioned" that the
cached label does not. Its omission AUC(halluc>expert) is only 0.671 — lexical
looseness collapses the signal. **Lesson: substring/phrase matching, not bag-of-
token overlap, is the right primitive for a lexical omission detector.**

## 5. Omission vs fabrication — are they separable?

The foil AD states the FALSE fact, which is a *fabrication*, not an omission.
Per probe on the hallucinated AD:

- states the TRUE fact: **3.9%** (omits it 96.1%)
- states the FALSE foil (fabrication): **69.7%** (53/76)
- expert AD states the foil: 1.3% (1/76 — clean control)

Breakdown of hallucinated failures: **fabrication (states foil) = 53**,
**silent omission (states neither true nor foil) = 22**, states-true = 3.

**Interpretation.** Here omission and fabrication *co-occur by construction* —
the swap deletes the true term and inserts a foil — so on this probe set they
are correlated but not identical. Omission is the **broader** signal: it flags
all 73 hallucinated failures where the fact is dropped, whereas a fabrication
detector would catch only the 53 that assert the foil. The 22 silent-omission
probes are invisible to any fabrication/contradiction check yet are exactly the
gap a reference-keyed ADQA cannot see. Conversely, the 3.9% where the halluc AD
*does* state the true fact are fabrications an omission scorer would miss. The
two signals are therefore **complementary**, and a full audit needs both — but
because this dataset entangles them, the numbers above do not cleanly isolate
fabrication-only detection.

## Limitations

- **Small, entangled sample**: n=76 probes / 23 clips; foil swaps make omission
  and fabrication co-vary by design, so their separability is not measured on
  independent axes here.
- **Binary omission score** caps probe-level AUC (0/1 ties); clip aggregation
  (AUC 0.945) is the fairer view but rests on ≤5 probes/clip.
- **Cached label dependence**: Tasks 1/3 use the cached `*_ad_mentions_true`
  fields as ground truth. Task 2 is the only fully reference-free check, and it
  shows a substring detector reproduces those labels at 94.7% — but its 4 FN
  (paraphrase misses) mean a naive lexical scorer will under-count coverage for
  ADs that describe a fact in different words. A production detector needs
  synonym/paraphrase handling to close that gap.
- No claim is made beyond these 23 clips.
