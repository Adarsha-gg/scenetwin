# Round 003 — codex

**Angle:** `self_consistency_expand`

## Cache Expansion

Expanded the best-of-N cache without `--refresh-cache`, using the existing first-17 cached clips as cache hits and targeting only missing clips inside the `--limit 20` prefix.

Before expansion:

| artifact | count |
|---|---:|
| cache files | 85 |
| complete best-of-N clips | 17 |

After `.venv/bin/python cursor/pipeline/best_of_n_rerank.py --limit 20 --n 4`:

| artifact | count |
|---|---:|
| cache files | 95 |
| complete best-of-N clips | 19 |

`BHxn3qfPAl4_000018_000028` was a legitimate uncached target but returned fewer than two usable candidates, so the pipeline skipped it. The two newly usable clips were `ShSSAEfnyDs_000000_000010` and `d7_SY48r__8_000060_000070`.

No `CREDIT_EXHAUSTED` condition occurred.

## Gate Review

Post-expansion `gate_review_holes.py`:

| metric | before | after |
|---|---:|---:|
| self-consistency clips | 14 | 16 |
| clean pairs | 42 | 48 |
| self-consistency AUC | 0.903 | 0.895 |
| recall @ about 10% FPR | 0.786 | 0.688 |
| FPR | 0.119 | 0.104 |
| tau | 0.0332 | 0.0394 |
| mean lie drop | 0.0767 | 0.0724 |
| mean clean drop | -0.0024 | 0.0016 |

The locked expert-reference headline remains unchanged:

| gate | AUC | recall | FPR | n |
|---|---:|---:|---:|---:|
| expert-reference CLIP grounding-drop | 0.835 | 0.700 | 0.100 | 60 |

The Claude round-3 relational/action/count red team also remains intact:

| gate | AUC | recall | FPR | n |
|---|---:|---:|---:|---:|
| human lies, expert ref | 0.783 | 0.565 | 0.130 | 23 |
| Gemini lies, expert ref | 0.905 | 0.783 | 0.130 | 23 |
| human lies, self-consistency ref | 0.895 | 0.688 | 0.104 | 16 clips |

## Best-of-N Control

The expanded best-of-N reranker is still not a positive deployment result. Independent expert-similarity evaluation stayed below the random-candidate baseline:

| selector | n clips | top1 sim | random sim | length-matched sim | win vs random | p |
|---|---:|---:|---:|---:|---:|---:|
| ensemble | 19 | 0.701 | 0.707 | 0.702 | 42% | 0.729 |
| ADQA only | 19 | 0.694 | 0.707 | 0.716 | 37% | 0.902 |
| CLIP only | 19 | 0.705 | 0.707 | 0.707 | 37% | 0.689 |

Interpretation: extra generated references help coverage, but they do not justify claiming that SceneTwin can select better ADs from a same-prompt candidate pool. The useful role is narrower: generated ADs are noisy independent references for a hallucination gate, and expansion should be reported with the observed stability loss rather than as monotonic improvement.

## Files Written

- `cursor/output/best_of_n/cache/` gained 10 cache files.
- `cursor/output/best_of_n/best_of_n_candidates.csv` now has 19 complete clips.
- `cursor/output/best_of_n_rerank.json` updated to n=19.
- `cursor/output/gate_review_holes.json` updated to self-consistency n=16.
- `output/charts/scenetwin_best_of_n.png` and `output/charts/scenetwin_gate_review_holes.png` updated.

COMMANDS_RUN: sed -n skill/context/peer reads, ls cursor/output/best_of_n/cache/ | wc -l, ls cursor/output/best_of_n/cache/ | sed -n '1,120p', .venv/bin/python cursor/pipeline/best_of_n_rerank.py --help, git status --short --branch, jq summaries for best_of_n_rerank.json and gate_review_holes.json, rg targeted cache/limit checks in best_of_n_rerank.py, sed targeted best_of_n_rerank.py cache/loop excerpts, wc/sed/tail best_of_n_candidates.csv, awk unique video/cache coverage counts, rg cache lookup for uncached video IDs, .venv/bin/python cursor/pipeline/best_of_n_rerank.py --limit 20 --n 4, .venv/bin/python cursor/pipeline/gate_review_holes.py, git diff/status for touched outputs
MISTAKE_AVOIDED: avoided repeating Claude's object-bias overclaim by not treating higher self-consistency AUC as proof of robustness against relational/action/count lies; also avoided Codex's earlier cache-waste pattern by using no refresh and expanding only the uncached prefix.
NEW_APPROACH: coverage-stability stress test for generated self-consistency references: expand the cache just enough to add new uncached clips, then ask whether the self-consistency gate and best-of-N selector improve out of sample. This differs from Claude's hand-lie swap-type red team and from threshold/CLIP-consensus gates; it tests whether more machine references make the gate more reliable or merely noisier.
