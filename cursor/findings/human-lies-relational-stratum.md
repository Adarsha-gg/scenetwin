# Red-team: the CLIP grounding-drop gate is object-biased

**Round 3 / claude / `human_lies_expand`** — grader-free, zero API.

## What I did

Added 5 NEW hand-authored lies on previously-unused clips, but deliberately in a
**CLIP-hard class**: relational / action / count / spatial swaps that *keep every
salient noun intact* (car, forehead, couples, snow, pineapple, saw, metal pipe).
This is the opposite of the existing 18 lies and of the Gemini lies, which swap
concrete objects/colors/settings (taxi, watermelon, green saw, jazz, mountain resort).

Then re-ran `gate_review_holes.py` (n 18 → 23) and a per-stratum audit
(`cursor/output/human_lies_stratum.csv`).

## Result — the gate fails on relational lies

| Lie stratum | n | mean grounding-drop (lie) | mean drop (clean para) | AUC vs paraphrase |
|---|---|---|---|---|
| OLD-18 object / scene swaps | 18 | **+0.0687** | +0.0053 | **0.914** |
| NEW-5 relational / action / count | 5 | **-0.0024** | +0.0117 | **0.320** |
| Combined | 23 | +0.0532 | — | 0.783 |

Adding 5 relational lies drags the headline human-lie AUC from **0.914 → 0.783**.
On the relational stratum alone the gate is **below chance** (0.32): the
fabricated description scores *as well or better* on CLIP than the truthful one.

Per-clip (lie caught only if its drop > its own paraphrase's drop):

- 3/5 MISS, including `8vkNr` (man→woman, carve→mash, basket→ground) at drop **-0.034** — CLIP ranks the lie *higher* than the expert AD.
- The 2 it "caught" had near-zero margins, not real separation.

## Why

CLIP text-image similarity grounds on the **bag of salient nouns**, not on agency,
count, or spatial relations. Swapping "vase → bowl" or "city park → mountain resort"
moves the embedding; swapping "man throws → woman rolls" or "three couples → two
couples" barely does. So the existing 0.91 human-lie AUC is **inflated by the lie
construction**: every prior lie swapped a groundable object.

## Honest scope

- This does **not** overturn the n=60 expert-reference headline (AUC 0.84) — that
  benchmark is also built from object/scene swaps, so it inherits the same blind spot.
- It is an **honest limitation for the paper**: the safety gate detects *wrong-object*
  hallucinations, not *wrong-action / wrong-count / wrong-who* hallucinations. Those
  are arguably the more dangerous AD errors for a blind viewer (who is doing what).
- Mitigation direction (not run, needs API): pair CLIP with the frame-grounded ADQA
  signal, which asks explicit who/what/count questions and should not share CLIP's
  noun bias. Testing that is the natural next round.

## Files

- `cursor/data/human_hallucinations.jsonl` (+5 rows, tagged `swap_class`)
- `cursor/output/gate_review_holes.json` (n=23)
- `cursor/output/human_lies_stratum.csv` (per-row drops + stratum flag)
