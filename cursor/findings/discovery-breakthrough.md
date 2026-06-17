# Discovery findings — 2026-05-27

## NEW: StoryRecall beats full-order rate

**CORRECTED** StoryRecall uses ADQA critical answer keys as story beats (not pro AD — that was tautological).

- tier3 wins: **16/18**
- full order 3>2>1>0: **6/18** (worse than ensemble **15/18**)
- tier means: cross=0.03, short=0.36, long=0.47, pro=0.67

StoryRecall is a valid NEW axis but does not replace ensemble for tier ordering.

## NEW: External clips break tier ordering

**10 new clips downloaded.** Heuristic scoring on cold data:

- pro beats short VATEX: **100%** (10/10)
- full tier order 3>2>1>0: **20%** (2/10)

The 18-clip benchmark **overstates** how well tiers separate. Fundamentals must be validated on `cursor/data/external_clips/` not just ρ on the same 18 clips.

## NEW: Subjectivity predicts ranking margin

**ρ(subjectivity, tier3_margin) = 0.486, p = 0.041**

Clips where pro AD diverges most from VATEX short captions also have the largest ensemble margins. Subjectivity isn't noise — it's signal that pro AD is doing real work beyond crowd captions.

Highest subjectivity: check `cursor/discover/output/subjectivity_index.csv`

## NEW: MDCI edit burden

Pro AD vs short VATEX token edit ratio peaks at **91%** (clip_01 Burger King). TRIBE pressure does NOT predict edit burden (ρ=-0.057). Visual complexity ≠ caption rewrite distance.

## NEW: Slot placement F1 = 0.55

CA3D-style IoU between TRIBE need windows and GenAD slots: mean F1 **0.55**. Half of clips have perfect placement; half have zero overlap — generator only runs per-clip not globally.

## MAVERIX audio gate

Zero audio-gated ADQA questions in v4 set — our benchmark is vision-only. Need to ingest MAVERIX questions or tag ADQA for AV-dependent items.

## External clips

Registry growing in `cursor/data/external_clips/`. Heuristic tier order holds on some, breaks on others — external set is the generalization test.

- [2026-05-27] **GENERALIZATION GAP**: external clips full order 2/10 vs benchmark 15/18 — fundamentals challenged
- [2026-05-27] StoryRecall (fixed): tier3 wins 16/18, full order 6/18
- [2026-05-27] Subjectivity ρ=0.49 p=0.04 with tier margin

`discover_v4` — rotates 6 novel scripts, batch download every 3 ticks. No eval_suite reruns.
