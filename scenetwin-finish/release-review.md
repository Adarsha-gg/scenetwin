## Review

Note: I did **not** write `scenetwin-finish/release-review.md` because the task also says “Do not edit,” and the review-agent instructions say no-edit wins over artifact-writing conflicts. Findings are below.

- Correct:
  - Entry points are identifiable: Gradio demo (`README.md:5-11`), FastAPI (`README.md:15-37`), static frontend (`README.md:39-47`).
  - Core Python files are syntactically parseable: `api/server.py`, `demo/live_pipeline.py`, `demo/live_presets.py`, `demo/scenetwin_demo.py`.
  - No staged files: verified with `git diff --cached --name-only`.

- Blocker P0: API/Gradio import a missing `qc_gate` module.
  - Evidence: `api/server.py:24`, `api/server.py:465-467`, `api/server.py:681-687`; `demo/scenetwin_demo.py:36`, `demo/scenetwin_demo.py:81`, `demo/scenetwin_demo.py:516-517`.
  - Verification command:
    ```bash
    git ls-files | grep -E '(^|/)qc_gate\.py$' || true
    find . -name 'qc_gate.py' -print
    ```
    Result: no `qc_gate.py` found.
  - Smallest safe fix: restore/add `qc_gate.py` with `load_qc_benchmark`, `assess_live`, `render_qc_html`, and `gate_ensemble`, or make QC optional with a local fallback.

- Blocker P0: README API setup is not sufficient for a clean local handoff.
  - Evidence: README installs only `fastapi uvicorn` (`README.md:20-22`), but `api.server` imports `demo/live_pipeline.py`, which imports `numpy` and `pandas` at module import (`demo/live_pipeline.py:20-21`). Required deps are in `requirements.txt:1-19`.
  - Verification command:
    ```bash
    PYTHONDONTWRITEBYTECODE=1 python -c "import api.server"
    ```
    Result in current interpreter: `ModuleNotFoundError: No module named 'numpy'`.
  - Smallest safe fix: change README setup to install `-r requirements.txt`, then verify:
    ```bash
    python -m venv .venv
    .venv/Scripts/python -m pip install -r requirements.txt
    PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python -c "import sys; sys.path.insert(0,'demo'); import api.server; import scenetwin_demo; print('imports ok')"
    ```

- Blocker P1: frontend static fallback is advertised in code but missing artifacts.
  - Evidence: `web/components.jsx:278-292` falls back to static JSON; `web/pages/cached.jsx:24-25` expects `../cursor/data/cached-clips.json`; `web/pages/tribe.jsx:249-250` expects `../cursor/data/tribe-risk.json`.
  - Verification command:
    ```bash
    test -f cursor/data/cached-clips.json || echo cached-clips.json missing
    test -f cursor/data/tribe-risk.json || echo tribe-risk.json missing
    test -f cursor/export_static_api.py || echo export_static_api.py missing
    ```
    Result: all missing.
  - Smallest safe fix: either commit generated static JSON plus export script, or remove fallback messaging and require the FastAPI backend.

- Blocker P1: research artifact handoff still contains unresolved claim/copy gates.
  - Evidence: locked claim boundaries say CLIP+ADQA remains scorer and TRIBE is not a ranker/rho booster (`cursor/findings/NEXT-STEPS.md:12-17`); synthesis says type-swapped control is pending and frame sampling is not validated (`output/reports/parallel-research-synthesis.md:19-24`, `:32-39`); claims audit found overclaim-risk hits (`output/reports/tribe-claims-audit.md:34-43`) and gives required safe wording (`:97-99`).
  - Smallest safe fix: update paper/demo copy to the safe wording in `parallel-research-synthesis.md:26-39`, and do not present type-swapped controls or TRIBE-frame sampling as completed results.

- Note P2: release hygiene is not finished.
  - Evidence: `git status --short` shows 7 modified tracked files and many untracked scripts/reports/output dirs, including `?? NUL`. `progress.md` is untracked scratch and should not be treated as noise by itself.
  - Smallest safe fix: decide which generated reports/scripts are deliverables, commit/stage them intentionally, ignore scratch files, and remove/quarantine `NUL` after approval.