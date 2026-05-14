# SceneTwin Session Handoff - 2026-05-14

## What Changed

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

- The local directory is still not initialized as a git repo.
- GitHub repo creation/push was not completed before interruption.
- Secrets are protected by `.gitignore`; `.env` should not be committed.
- Recommended next commands:

```bash
git init
git branch -M main
git add .
git commit -m "Initial SceneTwin demo and evaluation workspace"
gh repo create scenetwin --public --source=. --remote=origin
git push -u origin main
```

Before running `git add .`, confirm `.env` is ignored:

```bash
git check-ignore -v .env
```

