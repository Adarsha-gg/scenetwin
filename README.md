# SceneTwin

SceneTwin is a demo and evaluation workspace for auditing audio descriptions for blind and low-vision video access. The stable NJBDA demo combines CLIP visual grounding with frame-grounded ADQA, with TRIBE used as a cached benchmark-side neural risk signal.

## Local-only finish

This is the preferred handoff path. It uses cached artifacts only: no API keys, no paid model calls, no YouTube download, no browser cookies, no Colab/GPU, and no human-subject collection.

```bash
python cursor/export_static_api.py
python -m http.server 5174
```

Open `http://localhost:5174/web/` and use:

- `Cached clips` for the clip-by-clip evidence browser.
- `Benchmark` for poster-ready charts.
- `TRIBE risk` for cached review triage.
- `Compare` for the method explanation.

The static frontend falls back to JSON snapshots in `cursor/data/` when the FastAPI backend is not running.

## Optional API backend

Use this when you want cached endpoints or the optional live audit page.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn api.server:app --reload --port 8000
```

Useful cached endpoints:

- `GET /health` - key/config health check.
- `GET /api/cached-clips` - cached benchmark browser payload.
- `GET /api/tribe-risk` - cached TRIBE risk/route payload.
- `GET /api/qc-gate` - local cached QC/review-gate payload.
- `GET /api/presets` - tested live-demo video presets.

## Optional Gradio demo

```bash
python demo/scenetwin_demo.py
```

Open `http://127.0.0.1:7860`.

## Optional live YouTube audit

Live audit is not part of the local-only finish. It can require network access, YouTube/`yt-dlp`, local model downloads, and OpenAI or Anthropic keys if no candidate AD is supplied.

Example request when the API backend is running:

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=avz06PDqDbM","run_tribe":false}'
```

For a no-key live attempt, provide `candidate_ad`; otherwise AD generation/ADQA will fail without keys.

## Key files

- `web/` - static JavaScript frontend.
- `cursor/export_static_api.py` - writes cached JSON snapshots for the frontend.
- `cursor/data/*.json` - static frontend fallback payloads.
- `api/server.py` - FastAPI backend for cached endpoints and optional live audit.
- `demo/qc_gate.py` - local cached/live QC review-gate helpers.
- `demo/scenetwin_demo.py` - Gradio app.
- `demo/live_pipeline.py` - fault-tolerant optional live pipeline stages.
- `demo/live_presets.py` - shared Live YouTube demo presets.
- `tools/scenetwin_queryd_gemini_eval.py` - QuerYD video-native Gemini evaluation.
- `output/charts/` - poster chart scripts and generated chart images.
- `output/reports/` - report markdown for poster/eval results.
- `wiki/` - project research notes and running log.

## Demo presets

High-motion examples tested through the optional live path from `t=0`:

- Mission Impossible trailer: `https://www.youtube.com/watch?v=avz06PDqDbM`
- John Wick 4 trailer: `https://www.youtube.com/watch?v=qEVUtrk8_B4`
- Spider-Man No Way Home trailer: `https://www.youtube.com/watch?v=JfVOs4VSpmA`

The best mid-trailer stress example is Top Gun Maverick at `https://www.youtube.com/watch?v=giXco2jaZ_4&t=55s`.

## Secrets

Put API keys in `.env` locally. `.env` is ignored by git. Do not use keys for the local-only finish.
