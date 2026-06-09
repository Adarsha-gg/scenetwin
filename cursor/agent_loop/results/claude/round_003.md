# Round 003 — claude

**Angle:** `human_lies_expand`

BREAKTHROUGH: The CLIP grounding-drop gate is object-biased — blind to relational/action/count lies

## What I did (different from "add 5 generic lies")

Added 5 NEW hand lies on unused clips, but engineered them as a **controlled hard
stratum**: relational / action / count / spatial swaps that keep every salient noun
(car, forehead, couples, snow, pineapple, saw, metal pipe). The existing 18 lies and
the Gemini lies all swap concrete objects/colors/settings — so the prior 0.91 AUC was
never tested against the lie class CLIP can't ground. Re-ran `gate_review_holes.py`
(n 18→23) + a per-stratum audit.

## Result

| Lie stratum | n | mean drop (lie) | drop (clean) | AUC vs paraphrase |
|---|---|---|---|---|
| OLD-18 object/scene | 18 | +0.0687 | +0.0053 | 0.914 |
| NEW-5 relational/action/count | 5 | **-0.0024** | +0.0117 | **0.320** |
| Combined | 23 | +0.0532 | — | 0.783 |

- Adding the relational stratum drags human-lie AUC **0.914 → 0.783**.
- On relational lies the gate is **below chance**: e.g. `8vkNr` (carve→mash, basket→ground, man→woman) scores the lie **+0.034 higher** than the truthful AD.
- Honest scope: does not overturn the n=60 expert-ref headline (0.84) — that benchmark
  inherits the same noun-swap construction and blind spot. The gate detects
  *wrong-object* hallucinations, not *wrong-who/wrong-action/wrong-count* ones — which
  are the more dangerous AD errors for a blind viewer. Mitigation: pair CLIP with ADQA
  (explicit who/what/count questions); test next round.

Full writeup: `cursor/findings/human-lies-relational-stratum.md`.

COMMANDS_RUN: .venv/bin/python cursor/pipeline/gate_review_holes.py, .venv/bin/python (append jsonl rows), .venv/bin/python (per-stratum CLIP audit → cursor/output/human_lies_stratum.csv)
MISTAKE_AVOIDED: codex/I treated the human-lie AUC (0.91) as a robustness win by only ever testing object/color swaps that CLIP can trivially ground; I did not restate that locked number as safe — I adversarially probed the lie class it was never tested on.
NEW_APPROACH: stratified the new lies by swap TYPE (relational/action/count, nouns held fixed) to expose the gate's object-bias, vs codex's self-consistency reference-swap and my round-2 absolute-threshold gate. The contribution is a red-team limitation, not another headline ρ/AUC.
