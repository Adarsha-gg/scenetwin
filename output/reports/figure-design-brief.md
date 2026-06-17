---
title: SceneTwin — Figure Design Brief
purpose: hand this + the current PNGs to a design pass so all paper figures share one system
created: 2026-06-09
paper: output/reports/paper-scenetwin-consolidated.md
figures_dir: output/charts/
---

# SceneTwin Figure Design Brief

## 0. What this is for

I have an academic paper with 8 data figures (plus one system diagram that does not exist
yet). The numbers and the message of each figure are locked and correct; the **visual
design is not**. They are raw matplotlib defaults — three different color palettes across
the set, titles jammed into the plot area, default Times/DejaVu fonts, legends overlapping
data, no shared grid or hierarchy. I want one coherent, publication-grade visual system
applied across all of them. Redesign the *look*; do not change the data or the claim.

Attach the current PNGs from `output/charts/` (filenames listed per figure below) so you
can see the starting point.

## 1. The project (context for tone)

**SceneTwin** is a research system that evaluates **audio description (AD)** — the spoken
narration that makes video accessible to **blind and low-vision (BLV)** viewers. As AI
starts generating AD at scale, you need to (a) score whether a description actually
preserves the visual content, (b) catch descriptions that are fluent but hallucinated or
describe the wrong clip, and (c) use a brain encoder (an fMRI model called TRIBE) to steer
generation toward the exact visual facts the soundtrack drops, and to flag risky clips for
human review.

Three pillars, in priority order for the figures:
1. **Reference-free scoring** — two cheap signals (CLIP visual grounding + frame-grounded
   question answering) beat expensive frontier VLMs and 10 published metrics.
2. **A grader-free safety gate** — catches hallucinations and wrong-content descriptions.
3. **Brain-grounded steering (the novel star)** — an fMRI encoder steers what the AD
   describes, landing on exactly the visual facts it flagged.

**Tone:** serious academic, confident but honest (we show negative results too), clean and
modern. Think NeurIPS / CHI camera-ready, not a startup pitch deck. **Important irony to
lean into:** this is an *accessibility* paper, so the figures themselves must be
exemplary on accessibility — colorblind-safe, high contrast, legible at small print size.
That is both the right thing and a quiet rhetorical flex.

## 2. Design system (apply to ALL figures)

### Palette — semantic, colorblind-safe, SOLID COLORS ONLY
Use a fixed Okabe-Ito-style palette with consistent *meaning* across every figure. Never
reuse a color for two different roles.

| Role | Use for | Suggested hex |
|---|---|---|
| **OURS / positive** | SceneTwin, the winning method, "good" outcomes | teal-green `#0B7A6B` |
| **NEUTRAL / baseline** | published baselines, the "before"/uncorrected condition | slate grey `#9AA3AB` |
| **VLM / comparison** | frontier VLM judges, alternative signals | blue `#2D6CDF` |
| **DANGER / negative** | hallucinations, wrong-content, leakage, chance line | warm red `#D9534F` |
| **HIGHLIGHT / attention** | operating points, thresholds, the flagged stratum | amber `#E8A33D` |

**Hard constraint (do not violate):** **no gradients, no translucent `rgba` fills, no
drop shadows with blur.** Solid fills only. This is a real PDF-rendering performance
requirement on our side — translucent/gradient fills become `/Shading` objects that make
the PDF lag on scroll. Flat color, thin solid strokes.

### Typography
- One sans-serif family throughout (Inter, Source Sans 3, or Helvetica Neue). No serifs,
  no DejaVu.
- Clear hierarchy: **bold short title** (the claim, ~13pt) → optional thin subtitle (the
  setup/n, ~9pt grey) → axis labels (~10pt) → tick labels (~9pt) → value labels (~8.5pt).
- Title goes **above** the plot, never inside it. Current figures cram a 2-3 line title
  into the axes — kill that.

### Layout
- Drop the top and right spines. Keep light horizontal gridlines only (very light grey,
  `#E6E8EA`), no vertical grid unless it's a horizontal bar chart.
- Legends outside the data area (top, or to the right), frameless. Never let a legend sit
  on top of bars/curves (Fig 2 currently does this).
- Always label values directly on bars/points so the reader never reads off an axis.
- Consistent figure proportions: single-column ~3.3in wide, double-column ~7in wide,
  export **300 dpi PNG + SVG**. Tell me which figures are 1-col vs 2-col if it matters.

### Iconography (optional, tasteful)
Small inline glyphs are welcome where they clarify: an eye for "visual grounding," a
speech bubble for AD text, a brain for TRIBE. Keep them monochrome line icons, not clipart.

## 3. The figures (current file → message → redesign direction)

For each: the **one message** must survive at thumbnail size. Numbers are final.

### Fig 1 — Competitive map  ·  `scenetwin_competitive_map.png`
- **Type:** scatter, x = cost per inference (USD, log scale), y = Spearman ρ (quality).
- **Data:** Ours (CLIP+ADQA) ρ=0.929 at ~$0.001 (cheap). Frontier VLM judges (Claude
  Sonnet 4.6 0.713, GPT-5 0.727, Gemini 2.5 Pro 0.756) clustered far right (10-30× cost)
  and lower. 8 grey published baselines mid-left (best LLM-AD-Eval 0.899). One leakage
  point (Multi-ref R@3) flagged separately.
- **Message:** *We sit alone in the top-left — best quality at near-zero cost; the
  expensive VLMs are bottom-right.*
- **Fix:** make "Ours" a clearly dominant marker (large teal star with a subtle halo ring,
  no blur). Shade/annotate the desirable top-left quadrant lightly. VLMs in blue, baselines
  in grey, leakage in red with an "excluded" tag. Move labels off the points with thin
  leader lines so nothing overlaps (Claude/GPT labels currently collide on the right).

### Fig 2 — Corrected ladder  ·  `scenetwin_corrected_ladder.png`
- **Type:** two side-by-side grouped bar panels: (left) Spearman ρ, (right) % correctly
  ordered. Groups = Benchmark (in-domain) vs VATEX-60 (out-of-distribution). Bars =
  4-tier-with-fake-rung (neutral grey) vs 3-tier-corrected (teal/ours).
- **Data:** ρ 0.93→0.95 (in-domain), 0.87→0.95 (OOD); ordering 83→94%, 50→97%.
- **Message:** *The apparent generalization gap was a broken benchmark rung; fixing it,
  OOD ≈ in-domain.*
- **Fix:** the OOD ordering jump (50→97) is the hero number — emphasize it (e.g., a delta
  arrow/callout on that pair). Legend OUT of the plot (it currently sits on the bars).
  Consistent y-axis treatment across both panels. Grey = "before/broken," teal = "fixed."

### Fig 3 — Ladder robustness  ·  `scenetwin_ladder_robustness.png`
- **Type:** robustness panel(s) — ensemble-weight sweep showing a flat high plateau, plus
  normalization variants and bootstrap CIs.
- **Data:** ρ flat ~0.94-0.97 across ADQA weight w∈[0.2,0.8]; stable under 3 normalizations;
  bootstrap CI in-domain [0.927,0.977], OOD [0.928,0.968]; permutation null p=0.0002.
- **Message:** *The 0.95 is a property of the data, not a tuned knob.*
- **Fix:** lead with the weight-sweep line/area as a flat plateau (shade the "we didn't sit
  on a peak" band), with the chosen operating weight marked. Keep secondary robustness
  evidence as a compact subpanel or small table beside it, not a wall of plots.

### Fig 4 — Fusion ablation  ·  `scenetwin_fusion_results.png`
- **Type:** horizontal bar chart, ρ per method, sorted descending.
- **Data:** Ours 0.928 on top (teal), then 7 fusion blends 0.776-0.887 (grey). A dashed
  reference line at our 0.928.
- **Message:** *Stacking more metrics does not beat two signals — parsimony wins.*
- **Fix:** ours teal and clearly separated at top; all blends grey; keep the dashed "ours"
  line. Clean monospace-free labels (the `semantic_core (LLM+ADQA+VT)` style underscores
  read like code — render as plain words). Tight value labels at bar ends.

### Fig 5 — Hallucination gate ROC  ·  `scenetwin_gate_summary.png`
- **Type:** ROC curves, x = false-positive rate (flagging a truthful AD), y = hallucination
  recall. Three curves + chance diagonal + a vertical 10% FPR line with operating-point dots.
- **Data:** zero-reference claim gate AUC 0.58 (red, near chance — a negative result),
  CLIP grounding-drop AUC 0.84 (the deployable headline), CLIP+ADQA fused AUC 0.90
  (footnoted as grader-dependent). Operating points at 10% FPR: CLIP catches 70%.
- **Message:** *A grader-free CLIP signal catches 70% of hallucinations at a 10% false-
  alarm rate; the no-reference variant fails.*
- **Fix:** color by role, not rainbow: the CLIP headline curve in **teal (ours/hero)**, the
  fused curve in blue (secondary), the failed zero-reference curve in **red/dashed
  (negative)**, chance in light grey dashed. Emphasize the 10% FPR operating point (amber
  marker + annotation "70% caught"). AUCs in a clean legend block outside the plot.

### Fig 6 — Wrong-content gate  ·  `scenetwin_wrong_content_global_gate.png`
- **Type:** threshold / separation plot on raw (unnormalized) CLIP grounding.
- **Data:** wrong-content ADs cluster low (mean raw clip_top3 ≈ 0.074), legitimate ADs high
  (≈ 0.311); a single global threshold (~0.15-0.22) catches 98.3% at 2.2% false alarm.
- **Message:** *One raw-CLIP threshold cleanly separates "describes the wrong clip" from
  legitimate AD — deployable on a single description, no reference needed.*
- **Fix:** show the two distributions (wrong-content in red, legitimate in teal) with the
  threshold as a vertical amber line, and annotate "98% caught / 2% false alarm" at the
  line. Make the separation gap visually obvious. Strip/jitter or histogram, whichever
  reads cleaner — the point is the clean gap.

### Fig 7 — Brain-grounded steering (THE STAR)  ·  `scenetwin_steering_matched.png`
- **Type:** grouped bars, mean ADQA delta (gap-targeted − baseline), with 95% bootstrap CI
  whiskers. Two judge runs; each split into matched (TRIBE-flagged questions) vs unmatched.
- **Data:** 60-clip GPT-5 cross-judge: matched +0.113 (d=0.43, 11W/0L), unmatched +0.017
  (d=0.05). Held-out 17-clip non-headroom: matched +0.167 (d=0.42), unmatched +0.000
  (d=0.00). The dissociation IS the result.
- **Message:** *Steering improves exactly the visual facts the brain signal flagged, and
  nothing else — zero spillover.*
- **Fix:** this is the paper's most novel figure — make it the most polished. Matched bars
  in **teal (the signal)**, unmatched in **grey (the control)**, so the eye instantly sees
  "tall colored vs flat grey." Annotate effect sizes cleanly. Consider a subtle "matched
  vs unmatched" bracket/callout that names the dissociation. Note the 17-clip matched CI is
  wide (n=24) — keep the whisker honest, don't hide it. A small brain glyph over the
  "matched" group would tie it to TRIBE.

### Fig 8 — Neural review triage  ·  `scenetwin_tribe_triage.png`
- **Type:** shows the per-clip TRIBE "accessibility gap" is higher on the clips the metric
  misorders than the ones it gets right (AUC 0.79).
- **Data:** ADQA-only misorders 10/60 OOD clips; gap on fail 0.267 vs ok 0.158, AUC 0.79,
  p=0.0018. Top-20% highest-gap review catches 60% of misorderings.
- **Message:** *The brain gap flags which clips the metric will get wrong — route those to
  human review.*
- **Fix:** secondary figure, keep it simple. Either a clean two-group distribution (fail vs
  ok, red vs teal) with the AUC called out, or a small risk-coverage curve. One message,
  no clutter.

## 4. New figure needed — Fig 0: System diagram (does not exist yet)

A clean architecture/flow diagram is the single biggest missing asset. It should show the
pipeline as **audit → repair → route**:

```
            ┌─────────── SceneTwin ───────────┐
 clip ──►   │  SCORING   CLIP grounding + ADQA │ ──► ranked AD candidates
 + AD       │  SAFETY    grader-free CLIP gate │ ──► reject hallucination / wrong-content
 candidates │  STEERING  TRIBE P_AV − P_A      │ ──► generate AD targeting the visual gap
            │  TRIAGE    TRIBE per-clip gap     │ ──► route risky clips to human review
            └──────────────────────────────────┘
```

- Left input: a video clip + candidate AD text.
- Three/four labeled stages using the semantic palette: Scoring (teal), Safety gate (red
  accent for the reject path), Steering (amber/brain), Triage (blue).
- Make clear that CLIP+ADQA are the shared backbone and TRIBE is a side-car feeding
  steering + triage (NOT the score). The brain encoder should look distinct from the
  scoring path.
- Flat vector, same fonts/palette as the data figures.

## 5. Deliverables I want back

- All 8 data figures restyled to the system above, **SVG + 300dpi PNG**, same filenames
  with a `_v2` suffix is fine.
- The new Fig 0 system diagram (SVG).
- A one-page palette/type spec sheet so future figures stay consistent.
- Keep every number and label exactly as given here — design only.
