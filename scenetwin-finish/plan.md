# Implementation Plan

## Goal
Finish SceneTwin as a reproducible local-only demo and evidence bundle that runs without paid APIs, credentials, human-subject collection, or large refactors while preserving existing work.

## Review Findings

- **High - API/demo import blocker**: `api/server.py` and `demo/scenetwin_demo.py` both import `qc_gate`, but no `qc_gate.py` exists anywhere under the repo. The FastAPI backend and Gradio demo will fail at import before any endpoint/page can run.
  - Files: `api/server.py`, `demo/scenetwin_demo.py`
  - Evidence: repo search found `import qc_gate as qg` usages only; no matching module file.
- **High - current live path is not local-only**: `demo/live_pipeline.py` generates AD and ADQA through OpenAI/Anthropic if keys are present; `requirements.txt` includes paid API SDKs; README presents live YouTube generation/scoring as the primary path.
  - Files: `demo/live_pipeline.py`, `requirements.txt`, `README.md`
  - Local-only impact: violates no paid APIs / no credential use unless the live path is disabled, gated, or changed to cached/supplied-input-only behavior.
- **Medium - YouTube live download can use browser credentials**: `demo/live_pipeline.py` builds `yt_dlp` attempts with `cookiesfrombrowser` for Brave/Chrome/Firefox.
  - File: `demo/live_pipeline.py`
  - Local-only impact: violates the no credential-use constraint for the finishing path. Keep live YouTube off the local-only success path.
- **Medium - static frontend fallback is incomplete**: `web/pages/cached.jsx` and `web/pages/tribe.jsx` expect `cursor/data/cached-clips.json`, `cursor/data/review-priority.json`, and `cursor/data/tribe-risk.json`; only `cursor/data/human_hallucinations.jsonl` exists. README/runbook imply a static export, but no `cursor/export_static_api.py` exists.
  - Files: `web/pages/cached.jsx`, `web/pages/tribe.jsx`, `web/components.jsx`, `cursor/data/`
  - Impact: the frontend cannot be relied on without the API, and the API currently has the missing `qc_gate` import blocker.
- **Medium - optional review-priority endpoint points at a missing artifact**: `api/server.py` reads `cursor/output/combined_review_priority.csv`, but that file is absent.
  - File: `api/server.py`
  - Impact: not fatal because the endpoint returns an empty list, but UI copy should not depend on review-priority data until the CSV or a static substitute exists.
- **Low - local assets are mostly present**: cached benchmark CSVs, frame/video assets, charts, poster PDF, and TRIBE brain-map images are present under `output/`.
  - Files/dirs: `output/scenetwin_timing_20clip/`, `output/charts/`, `output/scenetwin_njbda_poster.pdf`
  - Impact: the safest finish is to center the cached benchmark/static demo and demote live YouTube to optional future work.
- **Low - requested source context missing**: `C:/Users/adars/Coding/scenetwin/context.md` was requested but is not present.
  - File: `context.md`
  - Impact: plan is based on direct repo inspection instead.

## Tasks

1. **Record current repo state before changing anything**: Capture uncommitted work and avoid touching unrelated files.
   - File: none
   - Changes: Run `git status --short`, save output in the executor notes, and do not overwrite existing modified files unless they are explicitly listed below.
   - Acceptance: executor can show a before/after `git status --short` where only planned files changed.

2. **Add the missing local QC gate module**: Implement the small module that existing API/demo code already expects.
   - File: `demo/qc_gate.py`
   - Changes: Add pure-local functions used by existing imports: `load_qc_benchmark()`, `gate_ensemble(ensemble, risk_score)`, `assess_live(clip_top3, adqa_score, ad_text, duration_s=30)`, and `render_qc_html(qc)`. Read cached CSVs from `output/scenetwin_timing_20clip/tribe_native/tribe_failure_forecast.csv` when available; otherwise return an empty/non-flagging benchmark. Do not call external APIs.
   - Acceptance: `python -m py_compile demo/qc_gate.py api/server.py demo/scenetwin_demo.py` passes, and `python -c "import sys; sys.path.insert(0,'demo'); import qc_gate; print(qc_gate.load_qc_benchmark().keys())"` prints keys including `clips`.

3. **Make the backend importable with no credentials**: Validate all cached-data endpoints work without OpenAI/Anthropic/Gemini keys.
   - File: `api/server.py`
   - Changes: Keep existing endpoint contracts, but if Task 2 reveals additional import/runtime assumptions, limit fixes to local cached-data handling only. Do not add credential reads beyond existing `.env` detection; do not make live audit part of the local-only acceptance path.
   - Acceptance: With API keys unset, `python -c "from api.server import health, cached_clips, tribe_risk; print(health()); print(cached_clips()['n']); print(tribe_risk()['n'])"` exits successfully and prints nonzero cached/tribe counts.

4. **Create a static export for the frontend fallback**: Generate local JSON snapshots from cached backend endpoint functions.
   - File: `cursor/export_static_api.py`
   - Changes: Add a small script that imports `api.server` and writes `cursor/data/cached-clips.json`, `cursor/data/tribe-risk.json`, `cursor/data/review-priority.json`, and `cursor/data/qc-gate.json`. It should create `cursor/data/` if missing and never call `/api/audit`, YouTube, OpenAI, Anthropic, Gemini, or TRIBE model loading.
   - Acceptance: `python cursor/export_static_api.py` creates/updates the four JSON files, and `python -m json.tool cursor/data/cached-clips.json > NUL` succeeds on Windows.

5. **Shift the web app to a cached/local-first story**: Make the static frontend usable without backend, network video embeds, or credentials.
   - Files: `web/components.jsx`, `web/pages/hero.jsx`, `web/pages/audit.jsx`, optionally `web/pages/cached.jsx`
   - Changes: Reorder/word the navigation and hero so `Cached clips`, `Benchmark`, and `TRIBE risk` are the primary local demo path. Replace the hero YouTube iframe with a local chart/frame asset. Mark `Live audit` as optional/experimental and show a clear local-only notice that arbitrary YouTube + generated ADQA is not part of the no-credential finish. Keep `fetchSceneTwinJson()` fallback behavior but rely on Task 4 JSON.
   - Acceptance: Serving with `python -m http.server 5174` and no backend still lets `http://localhost:5174/web/` load Overview, Cached clips, Benchmark, TRIBE risk, and Compare from local files.

6. **Document the local-only runbook**: Align project docs with the constrained finish.
   - Files: `README.md`, `wiki/demo-runbook.md`
   - Changes: Add a top-level “Local-only finish” section: no API keys, no paid APIs, no browser cookies, no human-subject collection. Preferred path: run static export, serve `web/`, use cached benchmark/tribe pages. Backend is optional for cached endpoints only. Move live YouTube instructions to an explicitly non-acceptance optional section.
   - Acceptance: Docs include commands for static export and local server, and no longer imply that paid-key live AD generation is required for the finish.

7. **Run local validation**: Prove the finish path works without credentials.
   - File: none
   - Changes: Run the validation commands below after implementation.
   - Acceptance: all commands pass, or any failure is documented with exact stderr and a follow-up task.

## Validation Commands

Use PowerShell from `C:/Users/adars/Coding/scenetwin`:

```powershell
git status --short
$env:OPENAI_API_KEY=$null; $env:ANTHROPIC_API_KEY=$null; $env:GEMINI_API_KEY=$null
python -m py_compile demo/qc_gate.py demo/live_pipeline.py demo/scenetwin_demo.py api/server.py cursor/export_static_api.py
python -c "from api.server import health, cached_clips, tribe_risk; print(health()); print(cached_clips()['n']); print(tribe_risk()['n'])"
python cursor/export_static_api.py
python -m json.tool cursor/data/cached-clips.json > NUL
python -m json.tool cursor/data/tribe-risk.json > NUL
python -m json.tool cursor/data/review-priority.json > NUL
python -m json.tool cursor/data/qc-gate.json > NUL
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

In another PowerShell while uvicorn is running:

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s http://127.0.0.1:8000/api/cached-clips
curl.exe -s http://127.0.0.1:8000/api/tribe-risk
```

Static frontend smoke:

```powershell
python -m http.server 5174
```

Open `http://localhost:5174/web/` and verify Overview, Cached clips, Benchmark, TRIBE risk, and Compare render from local assets. Do not validate success by running live YouTube or paid-model ADQA.

## Files to Modify

- `api/server.py` - only if needed for local cached endpoint robustness after `qc_gate.py` exists.
- `web/components.jsx` - local-first nav/copy if needed.
- `web/pages/hero.jsx` - replace external YouTube embed and API-ready copy with local cached assets.
- `web/pages/audit.jsx` - add local-only notice / optional status for live audit.
- `web/pages/cached.jsx` - adjust copy if static fallback remains missing/error-prone after export script.
- `README.md` - local-only finish instructions and constraints.
- `wiki/demo-runbook.md` - cached/static demo runbook and failure fallback.

## New Files

- `demo/qc_gate.py` - missing local QC helper module expected by API and Gradio demo.
- `cursor/export_static_api.py` - static JSON exporter for frontend fallback.
- `cursor/data/cached-clips.json` - generated static cached-clips payload.
- `cursor/data/tribe-risk.json` - generated static TRIBE-risk payload.
- `cursor/data/review-priority.json` - generated static review-priority payload, possibly empty if source CSV remains absent.
- `cursor/data/qc-gate.json` - generated static QC-gate payload.

## Dependencies

- Task 2 blocks Tasks 3 and 4 because the backend imports `qc_gate` at module import time.
- Task 3 should pass before Task 4 so the static exporter can import backend functions safely.
- Task 4 should complete before Task 5 so the frontend has real local JSON fallback files.
- Task 6 depends on the final decisions in Tasks 4 and 5.
- Task 7 depends on all implementation tasks.

## Risks

- Existing uncommitted work is unknown from file inspection alone; protect it with `git status --short` before edits.
- `qc_gate.py` behavior must be conservative and clearly labeled as a local QC/display gate, not a new validated metric.
- CLIP live scoring may still try to download/load model weights if someone runs `/api/audit`; exclude live audit from local-only acceptance unless all model assets are already cached and no network occurs.
- Browser testing cannot be fully proven by shell commands; do one manual visual smoke pass of the static pages.
- `cursor/output/combined_review_priority.csv` is absent, so review-priority JSON may be empty unless another local source is selected.
- `context.md` was missing, so there may be task-specific instructions not available in-repo.

## Residual Risks

- The finish plan intentionally does not validate arbitrary YouTube live audits because they require network download and model/API behavior outside the local-only constraints.
- No human-subject validation is included; prepared reviewer worksheets remain future approval-gated work.
- Static frontend success depends on local browser file serving and relative paths to `output/` assets.
