---
title: Colab CLI / TRIBE NCR Handoff
category: handoff
created: 2026-06-23
updated: 2026-06-23
---

# Colab CLI / TRIBE NCR Handoff

This is the handoff for a fresh agent to continue GPU work without loading the whole prior chat.

## Goal

Run the next high-upside TRIBE experiment, preferably **Neural Contrastive Retrieval (NCR)**, on a Colab GPU runtime via the new Google Colab CLI. Use **L4/A100/H100 if available**; avoid T4 if we want speed.

NCR design doc: `cursor/findings/neural-contrastive-retrieval.md`.
Producer cell: `cursor/research/tribe_ncr_dump_cell.py`.
Expected output: `cursor/research/output/ncr_similarity.csv` then local analyzer if/when available.

## Current Colab CLI state

- Installed with:
  ```bash
  uv tool install google-colab-cli
  ```
- CLI version verified: `0.6.0`.
- Auth completed successfully. Token saved at:
  ```text
  C:\Users\adars\.config\colab-cli\token.json
  ```
- Do **not** ask user to auth again unless token refresh fails.
- Verified:
  ```bash
  colab sessions
  ```
  returns successfully.

## Windows caveat / patch

Official Colab CLI supports Linux/macOS only. This machine is Windows/MINGW and WSL is not installed.

Initial import failed because `colab_cli.console` imports `termios`. I patched the installed uv tool file:

```text
C:\Users\adars\AppData\Roaming\uv\tools\google-colab-cli\Lib\site-packages\colab_cli\console.py
```

Patch: wrap `import termios; import tty` in a try/except and make `connect_console()` raise on Windows. Non-console commands (`new`, `run`, `exec`, `install`, `download`, etc.) now import and run.

If `uv tool install -U google-colab-cli` is run, this patch may be lost.

## WSL state

WSL is not installed:

```text
Windows Subsystem for Linux is not installed
```

An elevated `wsl.exe --install -d Ubuntu` attempt was launched but did not complete/activate in this session. Do not assume WSL exists.

## GPU smoke test

Created:

```text
tools/colab_gpu_smoke.py
```

Ran:

```bash
colab run --gpu T4 --timeout 300 tools/colab_gpu_smoke.py
```

Result: successful. Remote runtime:

```json
{
  "torch": "2.11.0+cu128",
  "cuda_available": true,
  "device_count": 1,
  "device": "Tesla T4"
}
```

Session auto-stopped.

## TRIBE smoke test status

Created:

```text
tools/colab_tribe_smoke.py
```

It installs TRIBE from GitHub, `yt-dlp`, and `gtts`, then loads `TribeModel.from_pretrained('facebook/tribev2')`.

Started on T4:

```bash
colab run --gpu T4 --timeout 1200 tools/colab_tribe_smoke.py
```

The command was aborted during pip install. A T4 session `run-b4e087` remained active. I stopped it:

```bash
colab stop -s run-b4e087
```

Current session state after cleanup:

```bash
colab sessions
# No active sessions found on server.
```

Next agent should rerun TRIBE smoke on **L4** or **A100**, not T4 if possible:

```bash
colab run --gpu L4 --timeout 1800 tools/colab_tribe_smoke.py
# or, if available:
colab run --gpu A100 --timeout 1800 tools/colab_tribe_smoke.py
```

## Important data caveat before NCR

`cursor/research/tribe_ncr_dump_cell.py` assumes an existing Colab notebook state:

- `/content/scenetwin` exists
- TRIBE helper globals exist: `_TRIBE_MODEL`, `_tribe_from_path`, `_slug`, `CACHE_DIR`
- external clips exist at `/content/scenetwin/workspace/external_clips/`
- metadata exists at `/content/scenetwin/cursor/data/external_clips/<video_id>/metadata.json`

In the current local repo, `cursor/data/external_clips/` is **not present** and local video `.mp4` files are not present. The earlier notebook/session must have generated those on Colab, or a new self-contained runner must recreate them.

Available local metadata sources:

- `workspace/vatex_overlap.json` — 338 VATEX/VideoA11y overlap records with `video_id`, `category`, `va11y_desc`, `vatex_caps`.
- `workspace/vatex_eval_clips.json` — 21 in-benchmark/eval-style records with `tier0_cross`, `tier1_vatex_short`, `tier2_vatex_long`, `tier3_va11y`.
- `workspace/videoa11y_clips.json` — VideoA11y clip metadata.
- `cursor/research/output/matched_clip_list.json` — matched clip list.
- `cursor/output/external_ensemble_eval.csv` — 60 held-out external tier scores, if present in this checkout.
- `cursor/research/paper_baselines_on_60.py` and `cursor/pipeline/vatex60_eval.py` show how the 60 external records/tiers were constructed.

## Recommended next plan

1. Check current CLI state:
   ```bash
   cd /c/Users/adars/Coding/scenetwin
   colab sessions
   ```
2. Run TRIBE load smoke on L4/A100:
   ```bash
   colab run --gpu L4 --timeout 1800 tools/colab_tribe_smoke.py
   ```
3. If TRIBE loads, build a **self-contained NCR Colab runner** instead of relying on notebook globals. It should:
   - clone or copy the repo to `/content/scenetwin`;
   - install `tribev2`, `yt-dlp`, `gtts`, and any minimal deps;
   - materialize a small subset first, e.g. 5 clips × 4 tiers;
   - download or reconstruct clip videos from YouTube using `yt_id/start/end` where available;
   - define `_tribe_from_path`, `_slug`, and `CACHE_DIR` locally;
   - write `/content/tribe_ncr/ncr_similarity.csv` and `/content/tribe_ncr/ncr_vectors.npz`;
   - download those artifacts with `colab download` or print base64 if download fails.
4. Only after the 5-clip pilot succeeds, scale to the full ~60 clips / ~300 TRIBE calls.

## Useful commands

Create a reusable L4 session:

```bash
colab new -s scenetwin-l4 --gpu L4
colab exec -s scenetwin-l4 -f tools/colab_tribe_smoke.py --timeout 1800
colab stop -s scenetwin-l4
```

Try A100 if allowed:

```bash
colab new -s scenetwin-a100 --gpu A100
```

Download remote artifact example:

```bash
colab download -s scenetwin-l4 /content/tribe_ncr/ncr_similarity.csv -o cursor/research/output/ncr_similarity.csv
```

Stop leaked sessions:

```bash
colab sessions
colab stop -s <session_name>
```

## Security / cleanup notes

- OAuth auth code files were deleted after auth.
- Do not print or commit `C:\Users\adars\.config\colab-cli\token.json`.
- Do not commit Colab auth temp files if they reappear.

## Research state summary

Local/non-GPU work found useful guardrails but not a new headline result yet:

- Corrected in-bench TRIBE AUC weakens after family-wise correction: p ≈ `0.0915`.
- Matched-question TRIBE lift survives cross-judge bootstrap.
- Gap-targeted gains are not explained by length: word delta vs ADQA delta Spearman ≈ `0.049`.
- TRIBE/VLM rematch is competitive/different, not clearly superior.
- ROI evidence mostly points to scene/spatial regions.
- Claim audit found 41 overclaim-risk hits.

Relevant reports:

- `output/reports/tribe-new-findings-local-run.md`
- `output/reports/tribe-new-findings-round2.md`
- `output/reports/tribe-new-findings-round3.md`
- `output/reports/tribe-claims-audit.md`
- `output/reports/tribe-review-worksheet.md`

## Files created/modified for Colab

- `tools/colab_cli_auth_wait.py`
- `tools/colab_gpu_smoke.py`
- `tools/colab_tribe_smoke.py`
- patched installed package file: `C:\Users\adars\AppData\Roaming\uv\tools\google-colab-cli\Lib\site-packages\colab_cli\console.py`
