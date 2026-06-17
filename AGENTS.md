# SceneTwin — Project Workspace & Operating Instructions

This is Adarsha's SceneTwin project workspace. SceneTwin is a reference-free audit framework that scores whether audio descriptions for blind and low vision viewers preserve the visual content of a video clip. Two-signal core: CLIP visual grounding + frame-grounded ADQA. Side-car: TRIBE fMRI encoder as a risk forecaster.

The poster, PDF, and live Gradio demo all shipped on 2026-05-12 for NJBDA 2026 (Rowan University, May 20 presentation).

---

## Directory Structure

```
SceneTwin/
├── raw/                    # Source documents, datasets, papers (NEVER modify)
├── wiki/                   # LLM-maintained wiki pages
│   ├── index.md            # Master catalog of all wiki pages
│   ├── log.md              # Append-only chronological log of operations
│   └── research/           # Topic and experiment pages
├── output/                 # Rendered artifacts
│   ├── reports/            # Markdown writeups
│   ├── charts/             # Matplotlib scripts + PNGs
│   └── logos/              # Conference logos
├── tools/                  # Scripts and CLIs (scenetwin_*.py)
├── demo/                   # Live Gradio demo
└── workspace/              # Working files migrated from ~/njbda (TRIBE colab, frames, clips)
```

---

## Wiki Page Conventions

Frontmatter on every page:

```yaml
---
title: Page Title
category: research
tags: [tag1, tag2]
sources: [raw/.../source.md]
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Filenames: `kebab-case.md`. Body uses `##` sections. End with `## See Also` (with `[[wikilinks]]`) and `## Sources`.

---

## Special Files

### wiki/index.md
Catalog of all pages. Update on every ingest or page add/remove.

### wiki/log.md
Append-only. Format: `## [YYYY-MM-DD] operation | Description`.

---

## Operations

### Ingest
1. Move new files into the right `raw/` subdir
2. Clean (strip SVG/HTML blobs, download external images locally)
3. Write or update summary pages in `wiki/research/`
4. Flag contradictions
5. Update `wiki/index.md`
6. Append to `wiki/log.md`

Adarsha prefers batch ingest with light supervision.

### Query
1. Read `wiki/index.md`
2. Read relevant pages
3. Synthesize with citations
4. Render in the requested format (report, chart, slide)
5. File standalone artifacts back into the wiki
6. Append to `wiki/log.md`

### Lint
Produce `output/reports/lint-YYYY-MM-DD.md` flagging contradictions, stale claims, orphans, missing cross-refs.

---

## Output Formats

- **Markdown report**: `output/reports/report-title.md`
- **Marp slides**: `output/slides/deck-title.md` (start with `---\nmarp: true\ntheme: default\n---`)
- **Matplotlib chart**: `output/charts/chart-title.py` + `.png`

---

## Backlinks

- Internal wiki: `[[research/scenetwin-foo]]`
- Raw source: `[Title](../raw/...)`

---

## Project Context (as of 2026-05-12)

Headline result: Spearman rho = 0.929 [0.90, 0.96] on 18 clips x 4 tiers. 54/54 pairwise tier wins, 15/18 fully ordered, permutation p < 0.0005. CLIP-only rho = 0.801, ADQA-only rho = 0.789. Ensemble lifts past either with non-overlapping CIs. TRIBE risk forecast: AUC = 1.00, recall@2/18 = 100%, p = 0.0065 (Bonferroni p = 0.065).

Advisors: Dr. Nan Wang, Bohan Fan, Xiaoshan Wang.

Closure metric is dead (2026-05-11 sweep: every metric ranks shorter AD above pro AD on clip_01/03). Killed branches: Description Gain / MVRR, ROI content typing, neural closure, TRIBE-weighted ADQA.

Live demo: `python3 demo/scenetwin_demo.py` (cached, no API key needed, runs at http://127.0.0.1:7860).

Render PDF after HTML edits:
```
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="output/scenetwin_njbda_poster.pdf" \
  --virtual-time-budget=15000 \
  "file://$PWD/output/scenetwin_njbda_poster_charts.html"
```

PDF perf: avoid CSS `linear-gradient` / `rgba()` translucent backgrounds (they become `/Shading` and `/Pattern` objects that viewers recompute on every scroll). Solid colors only.

---

## Notes

- Adarsha sources material; the LLM writes the wiki.
- Prefer updating existing pages over creating new ones.
- Keep pages focused. 300-word page with good backlinks beats 2000-word dump.
- This project migrated from `~/Knowledge` and `~/njbda` on 2026-05-13.
