# Colab/GPU/TRIBE Task Inventory

Scope: read-only inspection of `C:/Users/adars/Coding/scenetwin` for GPU/Colab/TRIBE-run-dependent tasks referenced by new findings, NEXT-STEPS, scripts, and wiki logs. No files were modified except this requested report.

## Files Retrieved

1. `cursor/findings/NEXT-STEPS.md` (lines 72-79) - current explicit pending GPU item: NCR.
2. `output/reports/new-findings.md` (lines 110-115, 202) - new-findings backlog items that mention NCR, TTS timing, silence condition, and GPU availability.
3. `output/reports/colab-tribe-handoff.md` (lines 14-18, 62-73, 94-123, 126-164, 171-186, 221-226) - concrete Colab CLI/GPU run state and NCR handoff constraints.
4. `cursor/research/tribe_ncr_dump_cell.py` (lines 1-24, 35-70, 89-123) - Colab producer for NCR and expected artifacts.
5. `cursor/findings/neural-contrastive-retrieval.md` (lines 8-18, 46-52, 57-68) - NCR design/runbook and risks.
6. `wiki/log.md` (lines 496-510) - log confirms NCR built/pending Colab, but cites an analyzer path that is not present in this checkout.
7. `output/reports/paper-A-draft.md` (line 374) and `wiki/log.md` (lines 228-233) - paper draft has stale Colab blocker; later log says the 60-clip counterfactual returned and was integrated.
8. `cursor/research/tribe_tensor_dump_cell.py` (lines 1-24, 55-115, 199-227) - older full tensor dump Colab cell and artifacts.
9. `cursor/research/tribe_tensor_dump_slim.py` (lines 1-15, 24-27, 104-115) - older slim external P_AV/P_A Colab cell and artifacts.
10. `cursor/research/tribe-v2-deep-dive.md` (lines 42-46) - mentions counterfactual Description Gain; current project log marks Description Gain/closure branches killed.
11. `output/reports/tribe-new-findings-local-run.md` (lines 86-110) and `output/reports/tribe-new-findings-round2.md` (lines 113-115) - tensor health caveats that should gate any future P_AD/NCR run.

## Prioritized checklist: tasks that truly need Colab GPU/TRIBE inference

### P0 — Run Neural Contrastive Retrieval (NCR) pilot, then full run

- **Severity:** HIGH / active blocker.
- **Why GPU/TRIBE is truly required:** NCR needs new TRIBE predictions for candidate AD text and clip videos. `cursor/research/tribe_ncr_dump_cell.py` states it runs about `60 P_AV + 240 P_AD = ~300 TRIBE calls` and expects a Colab notebook with TRIBE loaded.
- **Primary references:**
  - `cursor/findings/NEXT-STEPS.md` lines 72-79.
  - `output/reports/new-findings.md` lines 110-115 and line 202.
  - `cursor/findings/neural-contrastive-retrieval.md` lines 46-52.
  - `wiki/log.md` lines 496-510.
  - `output/reports/colab-tribe-handoff.md` lines 126-164.
- **Script/cell to run:** `cursor/research/tribe_ncr_dump_cell.py`.
- **Expected Colab artifacts:**
  - `/content/tribe_ncr/ncr_similarity.csv` -> download to `cursor/research/output/ncr_similarity.csv`.
  - `/content/tribe_ncr/ncr_vectors.npz` -> should also be downloaded for re-analysis, even though the older runbook only names the CSV.
- **Current blockers/risks:**
  - `output/reports/colab-tribe-handoff.md` lines 128-135 says the current local repo lacks `cursor/data/external_clips/` and local `.mp4` files expected by the cell. A self-contained runner must reconstruct/download clips or recreate the earlier notebook state.
  - `wiki/log.md` lines 498-500 and `cursor/findings/neural-contrastive-retrieval.md` line 49 reference `cursor/pipeline/neural_contrastive_retrieval.py`, but `find cursor/pipeline -name '*neural*'` found no such file in this checkout. Do not assume the local analyzer exists.
  - Tensor health guardrail: `output/reports/new-findings.md` line 67 and `tribe-new-findings-local-run.md` lines 86-110 warn low AD-response alignment should quarantine P_AD/NCR claims.
- **Recommended order:**
  1. Run `colab sessions` and TRIBE smoke (`tools/colab_tribe_smoke.py`) on L4/A100 if available.
  2. Build/run a 5-clip self-contained NCR pilot that writes both artifacts.
  3. Add/restore the local analyzer or inspect the CSV manually before the full run.
  4. Scale to full 60 external clips only after pilot artifacts are valid.

### P1 — NCR extensions that require the same GPU-produced NCR artifacts, not necessarily additional TRIBE runs

- **Severity:** HIGH once NCR exists; not separately runnable before P0.
- **Items:**
  - Source-clip leakage check: `output/reports/new-findings.md` line 111.
  - Time-aware NCR comparison: `output/reports/new-findings.md` line 112.
  - AD length-normalized NCR: `output/reports/new-findings.md` line 114.
- **GPU requirement:**
  - If `ncr_vectors.npz` contains per-tier mean vectors only, source-rank and length residualization can be local after P0.
  - Time-aware NCR likely needs per-timestep vectors, not just mean vectors; current `tribe_ncr_dump_cell.py` saves mean vectors only. If time-aware retrieval is pursued, modify/replace the Colab producer to save per-timestep P_AD/P_AV vectors or sufficient window summaries.
- **Expected artifacts:**
  - Existing P0: `cursor/research/output/ncr_similarity.csv`, `cursor/research/output/ncr_vectors.npz`.
  - Additional if time-aware: a new NPZ/CSV with per-timestep or windowed query/reference representations.

### P2 — P_AD text-injection / TTS-timing sanity check

- **Severity:** MEDIUM / guardrail for NCR validity.
- **Why GPU/TRIBE is required:** The check compares raw-text proxy against generated TTS/word-timed AD fed through TRIBE. That requires new TRIBE inference on alternative AD delivery inputs unless a cached tensor set already contains exactly those variants.
- **Primary references:**
  - `output/reports/new-findings.md` line 113.
  - `cursor/research/tribe-v2-deep-dive.md` lines 42-46.
  - `cursor/findings/neural-contrastive-retrieval.md` lines 63-68 identifies TTS-text OOD risk.
- **Script status:** no concrete runner found. `cursor/research/tribe_ncr_dump_cell.py` has `_tribe_text_vec(...)` but uses text files, not an explicit TTS timing comparison.
- **Expected artifacts:** new small-subset CSV comparing raw-text vs TTS-timed TRIBE vectors, plus any NPZ cache. Suggested destination consistent with repo: `cursor/research/output/`.
- **Can partially be done locally:** design the subset, generate TTS audio, and write analysis scaffolding locally. The TRIBE vector generation needs Colab GPU.

### P3 — Counterfactual silence condition

- **Severity:** MEDIUM / interpretability caveat.
- **Why GPU/TRIBE is required:** Existing tensor bundle has `P_AV` and `P_A`; it does not obviously include `P_silence`. New `P_silence` predictions require TRIBE inference on silent/no-audio versions.
- **Primary reference:** `output/reports/new-findings.md` line 115.
- **Script status:** no concrete silence runner found. Existing tensor dump scripts can be adapted:
  - `cursor/research/tribe_tensor_dump_cell.py` saves P_AV/P_A/P_AD/P_AV_AD.
  - `cursor/research/tribe_tensor_dump_slim.py` saves P_AV/P_A only.
- **Expected artifacts:** per-clip `P_silence` vectors/tensors and comparison CSV for `P_AV vs P_A`, `P_AV vs P_silence`, `P_A vs P_silence`, likely under `cursor/research/output/`.
- **Can partially be done locally:** choose clips and create silent media files. TRIBE inference needs Colab GPU.

### P4 — New corpus tensor dumps only if the corpus changes or missing artifacts are discovered

- **Severity:** LOW for current 78-clip work; HIGH only for new external corpora.
- **Why GPU/TRIBE is required:** Producing full TRIBE tensors for new clips requires TRIBE model inference.
- **References/scripts:**
  - `cursor/research/tribe_tensor_dump_cell.py` lines 1-24 and 199-227 writes `/content/tribe_tensors_all78.zip`.
  - `cursor/research/tribe_tensor_dump_slim.py` lines 1-15 writes `/content/tribe_tensors_ext_60.zip`.
  - `wiki/log.md` lines 244-253 says `tribe_tensors_all78.zip` was loaded and used for 78 clips.
- **Current status:** Not an active task for the existing 78 clips because cached tensors and derived artifacts are present under `cursor/research/output/tribe_tensors/` and related CSVs. Re-run only if changing corpus, repairing bad/missing tensors, or adding new conditions like P_silence/time-aware NCR.

## Items that looked GPU-related but are stale, killed, or local-only

### Stale/closed Colab blockers

- **External 60-clip counterfactual re-run in Paper A:** `output/reports/paper-A-draft.md` line 374 says Colab compute is needed, but `wiki/log.md` lines 228-233 says the 60-clip external counterfactual returned and calibration-layer framing was closed. Treat the draft row as stale unless a new paper decision reopens it.
- **Description Gain / neural closure / MVRR:** older files mention these as Colab tasks (`workspace/scenetwin_paper_eval.py`, `workspace/scenetwin_real_eval.py`, older reports), but `CLAUDE.md` and `wiki/log.md` record these branches as killed/negative. Do not spend GPU on them unless explicitly designing a new variant with a falsifiable reason.
- **Full 78 tensor dump:** already done for current corpus according to `wiki/log.md` lines 244-253. Do not re-run just to reproduce existing CSVs.

### Can be done locally from cached artifacts

These are real next steps but do **not** need a Colab GPU/TRIBE run with current cached tensors/CSVs:

- Tensor health / data-quality quarantine: `cursor/research/tribe_new_findings_local.py`, outputs under `cursor/research/output/new_findings_local/`.
- Route calibration, failure AUCs, top-k review curves, low-gap skip simulation, category splits, leave-video-out thresholds: use existing `tribe_blind_spot_*`, `tribe_tensors/manifest.csv`, ADQA/gate CSVs.
- Matched/unmatched meta-analysis and cluster bootstrap: local over `tribe_crossjudge_*_perq.csv`, `tribe_surgical_adqa_perq.csv`, and router outputs.
- Type-swapped prompt controls, generator/judge reruns, and Opus 44 completion: these need LLM/API credits, not Colab GPU/TRIBE, unless they introduce new TRIBE vector conditions.
- Demo/API tasks: route schema, static export, matched-question cards, low-gap example, caveat panel, source links, API regression smoke tests.
- Cheap proxy/category-only/random-window baselines: local over frames, transcripts, and cached router tensors. May need CPU/OpenCV/LLM depending implementation, but not TRIBE GPU.
- Paper/writing hygiene: claim matrix, dead-branch detector, paper language split, wiki index truth table.

## Start Here

Open `output/reports/colab-tribe-handoff.md` first. It contains the current Colab CLI state, GPU smoke-test commands, NCR-specific data caveat, and the recommended self-contained runner plan. Then open `cursor/research/tribe_ncr_dump_cell.py` to see exactly what the current NCR producer assumes and what artifacts it writes.

## Review findings

- **HIGH:** NCR is the only clearly active, concrete, high-priority task that truly needs a Colab GPU/TRIBE run now.
- **HIGH:** The documented local analyzer `cursor/pipeline/neural_contrastive_retrieval.py` is referenced but absent in this checkout; downstream analysis cannot be assumed ready.
- **HIGH:** Current NCR producer assumes missing local/Colab data layout (`cursor/data/external_clips/`, external `.mp4` files). A self-contained runner or data reconstruction is required before full run.
- **MEDIUM:** P_AD/NCR claims must quarantine low-alignment rows; do not publish raw NCR results without sensitivity checks.
- **MEDIUM:** TTS-timing and silence-condition checks are legitimate GPU tasks, but no concrete runner exists yet.
- **LOW:** Several older Colab tasks are stale or killed and should not consume GPU time.

## Residual risks

- Search was repository-local and read-only; hidden untracked notebooks or remote branches may contain additional GPU tasks.
- Some referenced scripts/reports contain stale claims contradicted by later logs; this inventory prioritized later `wiki/log.md` and new-finding reports.
- I did not execute Colab or inspect token/auth state because the task requested inventory only.
- Notebook contents were identified but not exhaustively read cell-by-cell beyond grep/find results; active tasks were sufficiently covered by markdown runbooks and scripts.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Concrete findings include paths, line ranges, severity, expected artifacts, and local-vs-Colab classification in sections 'Prioritized checklist', 'Review findings', and 'Residual risks'."
    }
  ],
  "changedFiles": [],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "ls .",
      "result": "passed",
      "summary": "Listed repository top-level directories/files."
    },
    {
      "command": "grep/find/read targeted searches for Colab/GPU/TRIBE/NEXT-STEPS across markdown, Python, and notebooks",
      "result": "passed",
      "summary": "Identified NEXT-STEPS, new-findings, Colab handoff, NCR producer, tensor dump scripts, and wiki log references."
    },
    {
      "command": "find cursor/pipeline -name '*neural*' and grep neural_contrastive_retrieval",
      "result": "passed",
      "summary": "Confirmed referenced NCR analyzer is absent in this checkout."
    },
    {
      "command": "PYTHONIOENCODING=utf-8 python line-reference scan",
      "result": "passed",
      "summary": "Collected exact line references for GPU/Colab/TRIBE task evidence."
    }
  ],
  "validationOutput": [
    "Report artifact written to subagent-reports/colab-gpu-task-inventory.md (requested output only; no repo code/data edits staged)"
  ],
  "residualRisks": [
    "Remote branches or hidden untracked files may include additional tasks not visible in this checkout.",
    "Some source references are stale; later wiki log entries were used to classify stale vs active work.",
    "No Colab/GPU commands were run; this is an inventory, not runtime validation."
  ],
  "noStagedFiles": true,
  "notes": "The only active concrete Colab/TRIBE run is NCR; TTS-timing and silence checks are legitimate but need runners; most other TRIBE follow-ups can run locally on cached tensors/CSVs or require LLM credits rather than GPU."
}
```