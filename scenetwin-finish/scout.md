# Code Context

## Files Retrieved
1. `README.md` (lines 1-73) - local purpose, demo/API/frontend commands, key files, secrets convention.
2. `CLAUDE.md` (lines 1-118) - project operating context, shipped NJBDA status, wiki/report conventions, dead/superseded branches.
3. `progress.md` (lines 1-20) - latest local progress status and files changed by prior cached-data type-swapped audit.
4. `cursor/findings/NEXT-STEPS.md` (lines 1-117) - current research queue, locked claims, highest-priority closure tasks, approval-gated work.
5. `api/server.py` (lines 1-120, 229-348, 597-697) - FastAPI models/endpoints and live audit orchestration.
6. `demo/live_pipeline.py` (lines 1-220) - fault-tolerant live YouTube pipeline, cache/env/API-key handling, download/frame stages.
7. `demo/scenetwin_demo.py` (lines 1-160) - Gradio app entry point and cached benchmark data loading.
8. `web/app.jsx` (lines 1-120) - JavaScript frontend page shell and benchmark/demo navigation.
9. `requirements.txt` (lines 1-18) - Python runtime dependencies.

## Project Purpose
SceneTwin is a demo/evaluation workspace for auditing whether audio descriptions preserve visual content for blind and low-vision video access. Locally, the shippable product is a cached NJBDA demo plus a live YouTube audit path: download/trim a clip, extract frames, generate or accept an AD, score CLIP grounding and frame-grounded ADQA, and optionally expose TRIBE as a cached/neural risk-triage side signal. README says the core demo combines CLIP visual grounding + frame-grounded ADQA, with TRIBE as a cached benchmark-side neural risk signal (`README.md:1-13`).

## Current Dirty Worktree Summary
Severity: **high for release hygiene**. `git status --short` reported 60 dirty entries before this scout artifact: 7 modified tracked files and many untracked scripts/reports/output directories. Current branch is `pi/research-improvement`.

Tracked modified files:
- `cursor/findings/NEXT-STEPS.md` - current next-steps document changed.
- `cursor/findings/neural-contrastive-retrieval.md` - NCR findings changed.
- `wiki/index.md`, `wiki/log.md` - wiki catalog/log changed.
- `wiki/research/scenetwin-tribe-blind-spot-router.md`, `wiki/research/scenetwin-tribe-role-analysis.md`, `wiki/research/scenetwin-tribe-router-validation.md` - TRIBE wiki pages changed.

Notable untracked groups:
- `NUL` - suspicious Windows device-name artifact; severity **medium**, can break search/tools (`rg` hit an OS error when traversing it).
- `progress.md` - untracked despite being project progress; severity **medium** for handoff/history.
- `cursor/pipeline/build_ncr_metadata.py`, `cursor/pipeline/neural_contrastive_retrieval.py` - untracked NCR pipeline code.
- Multiple untracked `cursor/research/*.py` and `cursor/research/output/...` directories - recent cached/local research outputs.
- Multiple untracked `output/reports/*.md` - candidate paper/demo evidence reports.
- Untracked `tools/colab_*.py`, `tools/colab_clean_tribe_ncr.py` - Colab/GPU helper scripts.
- Untracked `subagent-reports/`, `pi`.

## Key Code

### Product entry points
- Gradio demo: `python3 demo/scenetwin_demo.py` (`README.md:5-11`, `demo/scenetwin_demo.py:1-8`). Loads cached benchmark CSVs from `output/scenetwin_timing_20clip/...` and provides cached benchmark + live YouTube tabs.
- FastAPI backend: `python3 -m uvicorn api.server:app --reload --port 8000` (`README.md:15-37`). Endpoints include `/health`, `/api/presets`, `/api/tribe-risk`, `/api/qc-gate`, `/api/review-priority`, `/api/cached-clips`, `/api/audit` (`api/server.py:229-255`, `api/server.py:465-598`).
- Static frontend: `python3 -m http.server 5174`, open `/web/` (`README.md:39-47`). `web/app.jsx` routes hero/audit/cached/benchmark/tribe/compare pages.

### Live audit flow
`api/server.py:597-697` runs:
1. `lp.stage_download()` - YouTube download/trim with `yt-dlp`, `ffmpeg` optional fallback.
2. `lp.stage_frames()` - frame extraction with OpenCV.
3. `lp.stage_generate_ad()` if no AD supplied - requires API key/provider path.
4. `lp.stage_clip_grounding()` - CLIP scoring.
5. `lp.stage_adqa()` - frame-grounded ADQA.
6. optional `lp.stage_tribe_proxy()` when `run_tribe=true`.
7. `qg.assess_live()` QC gate.

`demo/live_pipeline.py:1-220` explicitly says stages should be fault tolerant and not raise to caller; it reads `.env` for `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` (`demo/live_pipeline.py:45-69`).

### Research state / locked claims
`cursor/findings/NEXT-STEPS.md:12-18` locks current interpretation:
- CLIP+ADQA remains the scorer.
- TRIBE is review triage/blind-spot routing/Access Surface input, not a ranker or rho booster.
- NCR is currently a negative/guardrail result.
- Low-gap reduces review pressure; it does not justify skipping scoring.

## Architecture
- `demo/live_pipeline.py` is the shared Python scoring/download/cache layer.
- `demo/scenetwin_demo.py` is a Gradio UI over cached benchmark artifacts and live pipeline stages.
- `api/server.py` wraps the same pipeline for a JS frontend and serves media from `demo/live_cache`.
- `web/` is a static React-style frontend shell that expects the API at `http://127.0.0.1:8000`.
- `output/`, `cursor/research/output/`, and `wiki/` contain generated evidence, reports, and research narrative. Closure is as much evidence curation/release hygiene as code completion.

## Likely Shippable Closure Tasks
1. **Release hygiene / decision task (severity high):** decide what dirty worktree entries are intended to ship. Stage/commit or discard untracked research outputs, reports, Colab scripts, and modified wiki/findings files. Remove or quarantine `NUL` after approval.
2. **Demo smoke validation (severity high):** create a clean venv, install `requirements.txt`, and smoke test `demo/scenetwin_demo.py`, `api.server`, and `web/` static frontend against cached data.
3. **Dependency/import gap check (severity high):** current environment lacks required dependencies (`numpy`, `pandas`), so import smoke tests fail before deeper missing-module checks. Also `api/server.py` and `demo/scenetwin_demo.py` import `qc_gate as qg`, but no tracked or untracked `qc_gate.py` was found by `git ls-files | grep qc_gate` / `find . -name qc_gate.py`; verify whether this file is missing, generated elsewhere, or intentionally ignored.
4. **Promote strongest local evidence (severity medium):** `NEXT-STEPS.md:44-57` says the cheap-baseline gauntlet is the strongest confound-controlled external TRIBE triage result and should be promoted into paper/demo evidence.
5. **Prepare but do not run approval-gated scoring (severity medium):** type-swapped prompt control has a frozen JSONL candidate set but requires explicit approval for generation/judging (`NEXT-STEPS.md:21-30`).
6. **Reviewer worksheet closure (severity medium):** fill `cursor/research/output/parallel_research/access_surface/top25_reviewer_cases.csv` / `.md` with VLM or human review labels; do not claim BLV validation without actual BLV recruitment/approval (`NEXT-STEPS.md:32-42`).
7. **Clarify final claims (severity medium):** keep TRIBE as triage/access-surface context; avoid claims that it improves rank correlation or replaces CLIP+ADQA (`NEXT-STEPS.md:105-109`).

## Commands to Verify
Run from `C:/Users/adars/Coding/scenetwin`:

```bash
# worktree/release hygiene
git status --short
git diff --stat

# environment setup
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

# import/API smoke
.venv/Scripts/python - <<'PY'
import sys
sys.path.insert(0, 'demo')
import live_pipeline
import api.server
print('imports ok')
PY

# API health
.venv/Scripts/python -m uvicorn api.server:app --port 8000
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/presets

# static frontend
python -m http.server 5174
# open http://localhost:5174/web/

# cached Gradio demo
.venv/Scripts/python demo/scenetwin_demo.py
# open http://127.0.0.1:7860
```

Optional live audit needs network/video access and likely API keys if no candidate AD is supplied:
```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=avz06PDqDbM","run_tribe":false}'
```

## Blockers Requiring Approval / External Credentials / Humans
- **External LLM/API scoring:** type-swapped prompt control requires approval for generation/judging (`NEXT-STEPS.md:21-30`).
- **Human/BLV study:** BLV micro-study requires human-subjects/recruitment approval; local packet prep is safe only (`NEXT-STEPS.md:83-95`).
- **GPU/Colab/Hugging Face:** `P_silence` needs method definition before GPU spend; full text-extractor NCR requires gated HF/Llama access via secure runtime secret plus GPU (`NEXT-STEPS.md:97-103`).
- **YouTube live path:** may need network, `yt-dlp`, `ffmpeg`, and possibly browser cookies depending on source availability (`demo/live_pipeline.py:71-150`).
- **Secrets:** `.env` is the local key mechanism; `.env` is ignored (`README.md:71-73`). Do not run paid/live generation without approval.
- **Missing/uncertain local module:** `qc_gate.py` was not found, but both API and Gradio import `qc_gate`; after dependencies are installed this may become the next hard runtime blocker.

## Commands Run During Scout
- `ls .` - passed; listed repo top-level.
- `find . -pattern README/CLAUDE/progress/NEXT-STEPS` - passed; found `README.md`, `CLAUDE.md`, `progress.md`, `cursor/findings/NEXT-STEPS.md` and related reports.
- `git status --short && git branch --show-current` - passed; found dirty branch `pi/research-improvement`.
- `find . -pattern **/*.py` - passed; mapped Python entry points/scripts.
- `find . -pattern requirements/test files` - passed; found `requirements.txt`, no formal pytest/pyproject/package files.
- `python -m py_compile api/server.py demo/scenetwin_demo.py demo/live_pipeline.py` - passed; syntax OK.
- Python import smoke for `api.server` / `demo/scenetwin_demo` - failed due missing installed deps (`numpy`, `pandas`) in current interpreter.
- `git ls-files | grep qc_gate || true; find . -name qc_gate.py` - passed; no `qc_gate.py` found.

## Residual Risks
- Import smoke did not reach all app modules because current interpreter lacks required dependencies.
- I did not run the UI servers or live YouTube audit; this was a no-edit quick audit.
- Worktree is heavily dirty; some untracked outputs may be valuable deliverables, but shipping/discarding needs owner decision.
- `NUL` artifact interferes with ripgrep traversal and may affect other tooling until removed/quarantined.

## Start Here
Open `cursor/findings/NEXT-STEPS.md` first for closure priorities and claim boundaries, then `README.md` for runnable surfaces, then `git status --short` to decide what belongs in the final ship/commit.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete findings include file paths, line ranges, severity labels for release hygiene/dependency/import issues, dirty worktree summary, closure tasks, verification commands, blockers, and residual risks."
    }
  ],
  "changedFiles": ["scenetwin-finish/scout.md"],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {"command": "ls .", "result": "passed", "summary": "Listed repository top-level."},
    {"command": "find/read README.md CLAUDE.md progress.md cursor/findings/NEXT-STEPS.md", "result": "passed", "summary": "Retrieved local purpose/progress/next-step docs."},
    {"command": "git status --short && git branch --show-current", "result": "passed", "summary": "Found 60 dirty entries on pi/research-improvement before scout output."},
    {"command": "find . -name '*.py' and related config/test discovery", "result": "passed", "summary": "Mapped Python entry points and found no formal test/config files beyond requirements.txt."},
    {"command": "python -m py_compile api/server.py demo/scenetwin_demo.py demo/live_pipeline.py", "result": "passed", "summary": "Syntax compile succeeded."},
    {"command": "python import smoke for api.server and demo/scenetwin_demo", "result": "failed", "summary": "Failed because current interpreter lacks numpy/pandas dependencies."},
    {"command": "git ls-files | grep qc_gate || true; find . -name qc_gate.py", "result": "passed", "summary": "No qc_gate.py found despite imports in API/Gradio entry points."}
  ],
  "validationOutput": [
    "py_compile produced no errors.",
    "import api.server FAILED: ModuleNotFoundError No module named 'numpy'",
    "import demo/scenetwin_demo FAILED: ModuleNotFoundError No module named 'pandas'"
  ],
  "residualRisks": [
    "No full server/UI/live audit smoke was run.",
    "Dependency installation was not performed, so deeper runtime blockers may remain.",
    "Dirty worktree ownership/disposition needs human decision.",
    "External scoring, BLV study, GPU/HF work require approval or credentials."
  ],
  "noStagedFiles": true,
  "notes": "Scout wrote only the requested artifact; no repository source edits were made."
}
```
