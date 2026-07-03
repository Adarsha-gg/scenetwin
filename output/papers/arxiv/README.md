# arXiv submission package — SceneTwin

Self-contained LaTeX source for arXiv. arXiv compiles LaTeX server-side, so upload the
**whole `arxiv/` folder** (main.tex + figures/) as a single `.zip`/`.tar.gz`.

## Files
- `main.tex` — the manuscript (figure paths point to `figures/`, no external deps).
- `figures/` — the 5 referenced PNGs.
- Bibliography is inline (`\section*{References}`), so there is **no `.bib` step** — good, one less thing to break.

## BEFORE you upload — verify it compiles (I could not compile here; no local TeX)
Easiest: drag `main.tex` + `figures/` into a new **Overleaf** project and hit Recompile.
Or locally: `pdflatex main.tex` **twice** (twice, for refs). Fix any missing-package errors
(all packages used — geometry, graphicx, booktabs, array, hyperref, amsmath, enumitem,
caption, times, fontenc, inputenc — are standard on TeXLive/Overleaf/arXiv).

## arXiv form metadata (copy-paste)
- **Title:** SceneTwin: Human-Reference-Free Audio Description Auditing with Visual Grounding, Frame-Grounded QA, and Review Triage
- **Authors:** Adarsha Mishra (William Paterson University)  ← solo, per your decision
- **Primary category:** `cs.HC` (Human-Computer Interaction)
- **Cross-list:** `cs.CV`, `cs.CL`
- **License:** CC BY 4.0 recommended (max reuse) — or arXiv non-exclusive if unsure.
- **Comments field:** e.g. "Preprint. 12 pages, 5 figures. Reproducibility scripts included; all headline numbers regenerate from released CSVs."
- **Abstract:** paste `abstract.txt` (already plain-text and trimmed to fit arXiv's ~1920-char limit; the full abstract stays in the PDF).

## Known hurdles (real ones)
1. **Endorsement.** First-time cs submitters sometimes need an *endorsement*. A `.edu` email
   and prior submissions from your institution usually auto-endorse; if prompted, ask an
   advisor or any cs.HC/cs.CV author you know to endorse. Not a paper-quality issue, just
   process.
2. **Solo authorship.** You confirmed this is intentional. Noting only that your advisors are
   recorded on the project; make sure that's genuinely agreed, since it's on the public record.
3. **Framing is method-first (correct for your no-human-study choice).** The paper already
   frames itself as a *reference-free evaluation & audit method*, not a BLV user-outcomes
   study — that framing is honest and matches what the evidence supports. Keep it.

## Pre-submission checklist
- [ ] `main.tex` compiles clean on Overleaf/arXiv (do this first).
- [ ] Abstract pasted into the form (markup stripped).
- [ ] Categories set (cs.HC primary).
- [ ] License chosen.
- [ ] Skim the compiled PDF for overflow/`??` undefined refs.
- [ ] (Optional) add a link to the code/repo in the Comments or a footnote.

## After arXiv
Per our plan: arXiv establishes priority now; then target a match-tier journal
(Universal Access in the Information Society, Journal on Multimodal User Interfaces,
IEEE Access, or Frontiers in CS–HCI) — all publishable without a BLV human study given the
honest method framing. Avoid pay-to-publish journals not indexed in DBLP/Scopus.
The canonical source remains `output/papers/scenetwin-submission.tex`; this `arxiv/main.tex`
is the flattened, self-contained copy for upload.
