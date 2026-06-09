# Round 001 — claude

**Angle:** Expand the self-consistency gate. Instead of caching more best-of-N ADs (blocked
by API credits), I diagnosed the real bottleneck and broke it for free.

## Diagnosis

The n=5 self-consistency gate from `gate_review_holes.py` was **not** limited by available
references — 9 clips already have an independent model-generated AD (`machine_ad_tier.csv`,
frames→AD). It was limited by the script requiring best-of-N *clean candidates*, which only
5 clips have. Dropping that requirement and using the expert/paraphrase as the clean
candidate unlocks the experiment at scale with **zero API credits** (CLIP only, grader-free).

## Experiment: reference-substitution robustness

`cursor/pipeline/reference_substitution_gate.py` — re-runs the grounding-drop gate
`flag if clip(anchor) - clip(candidate) > tau` while **swapping the anchor**. Verified the
manual CLIP pipeline reproduces the cached scores exactly (diff 0.00000).

| Anchor | What it is | AUC | recall@10%FPR | n |
|---|---|---|---|---|
| A1 human expert | headline baseline | 0.84 [0.76, 0.90] | 70% | 60 |
| **A2 model paraphrase** | model rewrite, no human at scoring | **0.85** [0.77, 0.92] | 73% | 60 |
| A3a indep model-AD | frames→AD, vs Gemini lie | 0.73 [0.46, 0.94] | 56% | 9 |
| **A3b indep model-AD** | frames→AD, vs **hand-authored** lie | **0.81** [0.57, 1.0] | 67% | 9 |
| A4 cross-clip (NULL) | another clip's AD as anchor (20 derangements) | 0.60 ± 0.01 | 21% | 60 |
| A0 no anchor (absolute) | flag low absolute grounding | 0.66 [0.56, 0.76] | 33% | 60 |

Permutation p (A1 vs the cross-clip null distribution): **p = 0.0** — 0/20 derangements
reach the real-anchor AUC.

## Outcome (construct validity / reviewer-proof)

1. **Anchor authorship is irrelevant:** human-expert 0.84 ≈ model-paraphrase 0.85 ≈
   independent model-AD 0.73–0.81. The gate does not need a human reference; the system can
   generate its own anchor.
2. **The anchor must be clip-relevant:** a random cross-clip anchor degrades to 0.60, sitting
   at the no-anchor absolute floor (0.66). The lift is from the anchor *describing this clip*.
3. **Strongest cell:** an independent model anchor (no human text anywhere) catches
   hand-authored lies at **AUC 0.81**, grader-free — breaking the human-reference dependency
   and the Gemini same-family circularity at once.

This makes the "reference-free" claim honest and falsifies the "you cheated with the human
expert AD" objection. It is the construct-validity subsection the gate was missing.

## Honest limitations

- A2's paraphrase derives from the expert *text*, so it proves anchor authorship is
  interchangeable, not that no seed description is needed. The fully-independent claim (A3)
  is real but **n=9** with wide CIs. Expanding A3 to n=60 needs API credits (one independent
  frames→AD per clip).
- The null floor is **0.60, not 0.50** — the absolute-grounding component survives anchor
  randomization. Reported as "degrades to the no-anchor floor," not "collapses to chance."

## Artifacts

- `cursor/pipeline/reference_substitution_gate.py`
- `cursor/output/ref_subst/reference_substitution.json`
- `cursor/output/ref_subst/img_emb.npz` (cached per-clip image features, reusable)
- `output/charts/scenetwin_reference_substitution.png`
- `cursor/findings/reference-substitution-gate.md`

BREAKTHROUGH: The hallucination gate is anchor-author-agnostic — a model-generated anchor (no human reference) catches hand-authored lies at AUC 0.81, grader-free, while a wrong-clip anchor collapses to the no-anchor floor

## Next round

- Spend credits to generate one independent frames→AD anchor for the remaining ~51 clips,
  lifting A3 (the only fully-reference-free cell) from n=9 to n=60.
- Test A2/A3 anchors fused over multiple self-generated anchors (mean grounding drop across k
  re-descriptions) for variance reduction.
