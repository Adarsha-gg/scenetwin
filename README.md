# SceneTwin

SceneTwin is a demo and evaluation workspace for auditing audio descriptions for blind and low-vision video access. The current NJBDA demo combines CLIP visual grounding with frame-grounded ADQA, with TRIBE used as a cached benchmark-side neural risk signal.

## Run The Demo

```bash
python3 demo/scenetwin_demo.py
```

Open `http://127.0.0.1:7860`.

The Live YouTube tab includes tested presets for high-motion trailers and safer static clips. It downloads a timestamped 30 second YouTube segment, extracts 8 frames, generates an AD if none is supplied, then scores CLIP grounding and ADQA.

## Run The API Backend

The JavaScript frontend should call the FastAPI backend instead of reimplementing the scoring stack.

```bash
python3 -m venv --system-site-packages .venv39
.venv39/bin/pip install fastapi uvicorn
.venv39/bin/python -m uvicorn api.server:app --reload --port 8000
```

Useful endpoints:

- `GET /health` - key/config health check.
- `GET /api/presets` - tested demo videos for the frontend preset buttons.
- `POST /api/audit` - run the live YouTube audit and return JSON plus media URLs.

Example request:

```bash
curl -X POST http://127.0.0.1:8000/api/audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=avz06PDqDbM","run_tribe":false}'
```

## Run The JavaScript Frontend

The current frontend lives in `web/` and uses the FastAPI backend at `http://127.0.0.1:8000`.

```bash
python3 -m http.server 5174
```

Open `http://localhost:5174/web/`.

## Key Files

- `demo/scenetwin_demo.py` - Gradio app.
- `api/server.py` - FastAPI backend for a JS frontend.
- `web/` - JavaScript frontend shell and live audit UI.
- `demo/live_pipeline.py` - fault-tolerant live pipeline stages.
- `demo/live_presets.py` - shared Live YouTube demo presets.
- `tools/scenetwin_queryd_gemini_eval.py` - QuerYD video-native Gemini evaluation.
- `output/charts/` - poster chart scripts and generated chart images.
- `output/reports/` - report markdown for poster/eval results.
- `wiki/` - project research notes and running log.

## Demo Presets

High-motion examples tested through the live path from `t=0`:

- Mission Impossible trailer: `https://www.youtube.com/watch?v=avz06PDqDbM`
- John Wick 4 trailer: `https://www.youtube.com/watch?v=qEVUtrk8_B4`
- Spider-Man No Way Home trailer: `https://www.youtube.com/watch?v=JfVOs4VSpmA`

The best mid-trailer stress example is Top Gun Maverick at `https://www.youtube.com/watch?v=giXco2jaZ_4&t=55s`.

## Secrets

Put API keys in `.env` locally. `.env` is ignored by git.
