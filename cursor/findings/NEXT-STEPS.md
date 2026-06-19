---
title: SceneTwin Next Steps / Pending Experiments
category: research
tags: [SceneTwin, todo, pending, reproducibility]
updated: 2026-06-07
---

# Pending Experiments — read before re-running

These are queued because of an external blocker (LLM credits), not because they
failed. Everything is wired and one command away.

## 1. Rerun the graders with Opus / GPT (HIGH PRIORITY)

**Why:** All 2026-06-07 ADQA results (completeness ladder, machine-AD tier) used
**Gemini 2.5 Flash** because Anthropic and OpenAI were both out of credits
(`Anthropic: credit balance too low`; `OpenAI: 429 insufficient_quota`).
Gemini is the weak link: it ties `full == half` on 45% of clips and returned no
questions on 2 clips. A stronger grader should raise the `full > half` rung and
lift ensemble rho from the current **0.870 Gemini-floor** toward the in-domain 0.95.

**How (one flag, results cached separately by model so Gemini stays intact):**

```bash
# Opus grader
.venv/bin/python cursor/pipeline/finer_completeness_ladder.py \
    --provider anthropic --model claude-opus-4-20250514

# GPT grader
.venv/bin/python cursor/pipeline/finer_completeness_ladder.py \
    --provider openai --model gpt-4o
```

Then re-make the chart/finding from `cursor/output/finer_completeness_ladder.json`
and compare to the Gemini row in `cursor/findings/completeness-ladder.md`.

**Prereq:** top up Anthropic and/or OpenAI credits. Verify with:
```bash
.venv/bin/python - <<'PY'
import os; from pathlib import Path
[os.environ.__setitem__(k, l.split('=',1)[1].strip().strip('"'))
 for l in Path('.env').read_text().splitlines()
 for k in ('ANTHROPIC_API_KEY','OPENAI_API_KEY') if l.startswith(k)]
from anthropic import Anthropic
try: Anthropic().messages.create(model='claude-haiku-4-5-20251001',max_tokens=5,messages=[{'role':'user','content':'ok'}]); print('ANTHROPIC OK')
except Exception as e: print('ANTHROPIC', str(e)[:60])
PY
```

## 2. Machine-AD tier with an INDEPENDENT grader

The machine-AD rung (`cursor/pipeline/machine_ad_tier.py`) was confounded: Gemini
both wrote and graded the AD (self-preference) on top of frame-grounding
circularity, so `expert > machine` was only 22%. Re-run with a *different* model
grading than the one that generated the AD to remove self-grading bias:

```bash
.venv/bin/python cursor/pipeline/machine_ad_tier.py --provider anthropic --model claude-opus-4-20250514
```
Frame-circularity remains a caveat regardless; report it.

## 3. Finish the 2 dropped clips

`9eBhetL8n5Q_000222_000232` and `BHxn3qfPAl4_000018_000028` are **hard-blocked by
Gemini at the input level**: `prompt_feedback.block_reason = OTHER`, no candidates
returned, deterministic across 4 retries (verified 2026-06-07). This is a Gemini
content-filter refusal on those clips' frames, not a transient error or a bug in
our code — so it cannot be retried away on Gemini. Re-running with Opus or GPT
(item 1) will almost certainly process them and complete the set to 60. Until
then the ladder is reported on **58 clips**.

## 4. Neural Contrastive Retrieval (NCR) — needs a Colab TRIBE run

Highest-ceiling open swing. Built and self-tested; blocked only on a TRIBE GPU run.

1. Colab (existing TRIBE notebook through Step 4): run `cursor/research/tribe_ncr_dump_cell.py`
   (~300 calls, ~3–4h T4, npz-cached).
2. Download `ncr_similarity.csv` → `cursor/research/output/`.
3. `python cursor/pipeline/neural_contrastive_retrieval.py` → results + chart.

Tests whether an AD's TRIBE response retrieves the right clip's video response
(rank-percentile rising tier0<tier1<tier3, tier0_cross at chance). Designed to beat
the verbosity + language-injection confounds that killed neural closure. May hit
chance (TTS-text is OOD for TRIBE) — that's a reportable honest negative.
Design + rationale: `cursor/findings/neural-contrastive-retrieval.md`.

## Done this session (for context)

- Fake tier rung found + corrected ladder: rho 0.93->0.95 in-domain, 0.87->0.95 OOD
  (`cursor/findings/fake-tier-rung.md`).
- Valid 4-tier completeness ladder (Gemini): rho=0.870, 37/58 ordered
  (`cursor/findings/completeness-ladder.md`).
- Full CLIP+ADQA ensemble on 60 VATEX OOD clips: rho=0.873
  (`cursor/findings/vatex60-generalization.md`).
- Selective/abstention angle tested and de-prioritized (`cursor/findings/selective-audit.md`).

## See Also

- [[findings/completeness-ladder]]
- [[findings/fake-tier-rung]]
- [[findings/vatex60-generalization]]
