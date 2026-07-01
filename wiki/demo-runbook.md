# SceneTwin Presenter Runbook

Use the cached/static path for the main demo. Keep Live Audit as an optional stress test only.

## 0. Local-only start

From the repo root:

```bash
python cursor/export_static_api.py
python -m http.server 5174
```

Open:

```text
http://localhost:5174/web/
```

This path uses cached JSON and local chart/frame assets only. It does not need API keys, paid APIs, YouTube download, browser cookies, Colab/GPU, or human-subject collection.

## 1. Overview

Open `Overview`.

Say:

```text
SceneTwin audits audio description by checking whether the AD preserves the visual information needed to understand a clip. The stable demo is cached: CLIP grounding, frame-grounded ADQA, and TRIBE-backed review triage are already computed.
```

Use the `Open cached clips` button. Do not start with Live Audit.

## 2. Cached Clips

Open `Cached clips`.

Use this as the main demo. The clips are already sorted so strong professional-AD examples appear first.

Click the first two or three clips and show:

- preview frames / video
- `Professional AD`
- `VATEX short`
- `VATEX long`
- ADQA question grades
- CLIP scores
- QC/review gate if present

Suggested line:

```text
The professional AD answers the scene-specific questions more completely. The shorter VATEX-style captions often name the scene but miss the action that a blind or low-vision viewer needs.
```

Backup if a browser video does not play:

```text
Some cached clips are stored as MKV, so the frame preview is the reliable artifact. The scoring was computed from these sampled visual frames and the AD candidates.
```

## 3. Benchmark

Open `Benchmark`.

Show the poster-ready charts and keep the claim narrow:

```text
The core score is CLIP plus frame-grounded ADQA. TRIBE is not the final ranker; it is a cached risk/triage signal.
```

## 4. TRIBE Risk

Open `TRIBE risk`.

Click the top-ranked risk clips.

Show:

- risk-ranked clip list
- brain-backed visual-lift map
- need curve
- review decision
- ROI summary

Suggested line:

```text
TRIBE is not the final caption grader. It tells us where visual information is important enough that an AD miss is more expensive, so those clips deserve review first.
```

Precise claim:

```text
In the cached 18-clip benchmark, the TRIBE risk queue ranked both known ADQA full-order failure clips at the top.
```

## 5. Compare

Open `Compare`.

Use this to answer "why not just a VLM?"

Say:

```text
A normal VLM can describe what is visible. SceneTwin asks a different question: did this audio description preserve the specific visual facts needed by the viewer, and which clips deserve human review first?
```

Point to the three-part distinction:

- CLIP grounding checks visual match.
- ADQA checks whether the AD answers scene-specific questions.
- TRIBE risk prioritizes where missing visual information matters most.

## 6. Optional API backend

Only start the backend if you want live endpoints or want to prove the static JSON matches API payloads.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

Quick health checks:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/cached-clips
curl -s http://127.0.0.1:8000/api/tribe-risk
curl -s http://127.0.0.1:8000/api/qc-gate
```

## 7. Optional Live Audit

Only use `Live audit` if there is time and the network/API path is behaving.

Recommended presets:

- Mission Impossible trailer from start
- John Wick 4 trailer from start
- Top Gun Maverick trailer from start

Do not click a preset and expect it to run automatically. Preset click selects and previews; the top run button starts scoring.

Suggested framing:

```text
The cached benchmark is the stable result. Live Audit shows the same stack running on a new YouTube clip, but YouTube download, model weights, and model APIs make it less deterministic during a live presentation.
```

For a no-key live attempt, paste a candidate AD. Leaving Candidate AD blank asks the backend to call a model API.

## 8. If Something Breaks

If static data is stale or missing:

```bash
python cursor/export_static_api.py
```

If the frontend is down:

```bash
python -m http.server 5174
```

If the API is down:

```bash
.venv/Scripts/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

If Live Audit fails:

```text
Switch back to Cached clips. The benchmark path is the result; live YouTube is the stress test.
```

If TRIBE images do not load:

```text
Use Cached clips and Compare. The TRIBE tab is a visual explanation layer, not required for the core ADQA/CLIP demo.
```

## 9. Closing

End with:

```text
SceneTwin is an audit layer for audio description quality. It does not replace human AD writers; it helps find where descriptions preserve the scene, where they miss important information, and which clips should be reviewed first.
```
