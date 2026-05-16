# SceneTwin Presenter Runbook

Use the cached path for the main demo. Keep Live Audit as the optional proof that the same pipeline can run on a fresh YouTube URL.

## 0. Start The Demo

From the repo root:

```bash
.venv39/bin/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
python3 -m http.server 5174
```

Open:

```text
http://localhost:5174/web/
```

Quick health checks:

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8000/api/cached-clips
```

## 1. Overview

Open `Overview`.

Say:

```text
SceneTwin audits audio description by checking whether the AD preserves the visual information needed to understand a clip. It combines visual grounding, question answering, and a TRIBE-backed accessibility risk signal.
```

Keep this short. The goal is to orient the room before showing clips.

## 2. Cached Clips

Open `Cached clips`.

Use this as the main demo. The clips are already sorted so strong professional-AD examples appear first.

Click the first two or three clips and show:

- preview frames / video
- `Professional AD`
- `VATEX short`
- `VATEX long`
- ADQA question grades
- CLIP top matches

Suggested line:

```text
The professional AD answers the scene-specific questions more completely. The shorter VATEX-style captions often name the scene but miss the action that a blind or low-vision viewer needs.
```

Backup if a browser video does not play:

```text
Some cached clips are stored as MKV, so the frame preview is the reliable artifact. The scoring was computed from these sampled visual frames and the AD candidates.
```

## 3. TRIBE Risk

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
TRIBE is not the final caption grader. It is the triage signal: it tells us where visual information is neurologically important enough that an AD miss is more expensive.
```

Keep the claim precise:

```text
The pilot result is that TRIBE risk ranked both known ADQA failure cases at the top of the 18-clip benchmark.
```

## 4. Compare

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

## 5. Optional Live Audit

Only use `Live audit` if there is time and the network/API path is behaving.

Recommended presets:

- Mission Impossible trailer from start
- John Wick 4 trailer from start
- Top Gun Maverick trailer from start

Do not click a preset and expect it to run automatically. Preset click selects and previews; the top run button starts scoring.

Suggested framing:

```text
The cached benchmark is the stable result. Live Audit shows the same stack running on a new YouTube clip, but YouTube download and model APIs make this less deterministic during a live presentation.
```

## 6. If Something Breaks

If the API is down:

```bash
.venv39/bin/python -m uvicorn api.server:app --host 127.0.0.1 --port 8000
```

If the frontend is down:

```bash
python3 -m http.server 5174
```

If Live Audit fails:

```text
Switch back to Cached clips. The benchmark path is the result; live YouTube is the stress test.
```

If TRIBE images do not load:

```text
Use Cached clips and Compare. The TRIBE tab is a visual explanation layer, not required for the core ADQA/CLIP demo.
```

## 7. Closing

End with:

```text
SceneTwin is an audit layer for audio description quality. It does not replace human AD writers; it helps find where descriptions preserve the scene, where they miss important information, and which clips should be reviewed first.
```
