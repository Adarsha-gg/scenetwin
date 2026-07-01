# Progress

## Status
Local-only demo finish implemented and verified.

## Completed This Pass
- Restored the missing `demo/qc_gate.py` module required by both FastAPI and Gradio entry points.
- Added `cursor/export_static_api.py` and generated static JSON payloads for the web fallback:
  - `cursor/data/cached-clips.json`
  - `cursor/data/tribe-risk.json`
  - `cursor/data/qc-gate.json`
  - `cursor/data/review-priority.json`
- Reframed the web UI around cached/local-first demo flow; Live Audit is now clearly optional.
- Updated `README.md` and `wiki/demo-runbook.md` with no-key static runbook.
- Verified static frontend visually with a headless Brave screenshot at `scenetwin-finish/cached-page.png`.
- Verified cached API endpoints in a local venv.

## Validation
- `python -m py_compile demo/scenetwin_demo.py demo/qc_gate.py demo/live_pipeline.py api/server.py cursor/export_static_api.py`
- `python cursor/export_static_api.py`
- `python -m json.tool` on all four generated `cursor/data/*.json` files
- `.venv_api/Scripts/python - <<'PY' ... import api.server ... PY` returned cached=18, tribe=18, qc=18/3 flagged, review=0
- `.venv_api/Scripts/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000` plus `curl` smoke checks for `/health`, `/api/cached-clips`, `/api/tribe-risk`, `/api/qc-gate`
- `python -m http.server 5174` plus headless Brave screenshot of `/web/` cached page

## Not Done / Still Approval-Gated
- No paid/external LLM calls.
- No live YouTube audit run.
- No Colab/GPU/TRIBE inference.
- No BLV/human-subject collection.
- Pre-existing dirty research artifacts and `NUL` were not cleaned up.
