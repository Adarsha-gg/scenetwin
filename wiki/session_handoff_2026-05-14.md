# SceneTwin Session Handoff - 2026-05-14

## What Changed

- Current status as of the latest JS demo pass:
  - GitHub repo is live at `https://github.com/Adarsha-gg/scenetwin`.
  - Backend FastAPI is running at `http://127.0.0.1:8000`.
  - Frontend is running at `http://localhost:5174/web/`.
  - Default frontend page is now the polished Overview preview, not the audit form.
  - Live Audit keeps the run button at the top; preset clicks only select and preview clips.
  - Added Benchmark, TRIBE Risk, and Compare tabs to explain the poster result and why this is not just a generic VLM grader.
  - Added `/api/tribe-risk`, backed by the cached 18-clip TRIBE failure forecast.
  - TRIBE Risk shows the brain imagery, recall@2 = 100%, p = 0.0065, the 18-clip risk ranking, and selected-clip details.
  - Compare explains SceneTwin's blind/low-vision value: missing visual evidence, no reference AD requirement for live clips, CLIP grounding, frame-grounded ADQA, and TRIBE risk routing.
- Added repo hygiene files:
  - `.gitignore`
  - `.env.example`
  - `README.md`
- Updated `demo/scenetwin_demo.py` Live YouTube presets so the first demo choices are high-motion movie trailers that work from `t=0`.
- Updated `demo/live_pipeline.py` so YouTube URLs with `t=` or `start=` offsets are respected before ffmpeg trims the 30 second segment.
- Added/kept sweep artifacts:
  - `output/live_high_motion_t0_sweep.csv`
  - `output/live_high_motion_preset_sweep.csv`
  - `output/live_demo_preset_sweep.csv`
- Updated `wiki/log.md` with the new t=0 high-motion sweep.
- Tightened `.gitignore` so `.env`, local caches, downloaded video/frame corpora, heavyweight model/data artifacts, and nested external repo metadata do not get committed.

## Best Demo Videos

These were tested through the exact Live YouTube path from `t=0`: download, 8-frame sampling, generated AD, CLIP grounding, and ADQA.

| Demo | URL | CLIP top3 | ADQA |
|---|---|---:|---:|
| Mission Impossible trailer | `https://www.youtube.com/watch?v=avz06PDqDbM` | 0.333 | 3/3 |
| John Wick 4 trailer | `https://www.youtube.com/watch?v=qEVUtrk8_B4` | 0.332 | 3/3 |
| Spider-Man No Way Home trailer | `https://www.youtube.com/watch?v=JfVOs4VSpmA` | 0.317 | 3/3 |
| The Batman trailer | `https://www.youtube.com/watch?v=mqqft2x_Aa4` | 0.305 | 3/3 |

Best high-motion stress example with timestamp:

| Demo | URL | CLIP top3 | ADQA |
|---|---|---:|---:|
| Top Gun Maverick action segment | `https://www.youtube.com/watch?v=giXco2jaZ_4&t=55s` | 0.394 | 3/3 |

## Validation Done

- `PYTHONPYCACHEPREFIX=.pycache_tmp python3 -m py_compile demo/scenetwin_demo.py demo/live_pipeline.py` passed.
- The first compile attempt failed only because macOS tried writing bytecode to `/Users/adarsha/Library/Caches/...`, which is outside the sandbox. Redirecting pycache fixed it.

## Current Server State

- The previous Gradio process on port `7860` was stale and was killed.
- Attempts to restart inside the sandbox failed because the sandbox cannot bind/list local ports reliably.
- A sandbox-external background start was attempted, but `/tmp/scenetwin_demo.log` stayed empty and `lsof` did not show the port listening.
- Next step: start manually or rerun outside sandbox:

```bash
cd /Users/adarsha/Coding/SceneTwin
MPLCONFIGDIR=/Users/adarsha/Coding/SceneTwin/.runtime/matplotlib python3 -u demo/scenetwin_demo.py
```

Then open:

```text
http://127.0.0.1:7860
```

## GitHub Push Status

- Repo is initialized and pushed to `https://github.com/Adarsha-gg/scenetwin`.
- Latest pushed feature commit before this note: `4ee57ec Add TRIBE risk and comparison tabs`.
- Secrets are protected by `.gitignore`; `.env` is not committed.
