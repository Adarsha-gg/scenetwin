---
title: Parallel Research Blocked Next Steps
category: research
created: 2026-06-23
updated: 2026-06-23
sources:
  - output/reports/colab-tribe-ncr-full-run.md
  - output/reports/tribe-ncr-results.md
  - output/reports/tribe-ncr-hidden-patterns.md
  - output/reports/colab-tribe-handoff.md
  - tools/colab_tribe_ncr_runner.py
  - cursor/pipeline/neural_contrastive_retrieval.py
  - cursor/pipeline/build_ncr_metadata.py
  - cursor/research/tribe_tensor_dump_slim.py
  - cursor/research/output/tribe_tensors/manifest.csv
  - output/reports/tribe-new-findings-local-run.md
  - output/reports/tribe-new-findings-round2.md
  - output/reports/tribe-new-findings-round3.md
  - output/reports/tribe-review-worksheet.md
---

# Parallel Research Blocked Next Steps

Scope: local-only feasibility/blocker pass for three lower-priority items: authenticated full text-extractor NCR ablation, `P_silence` condition, and BLV micro-study. I did **not** use any HuggingFace token, call external services, run Colab, download videos/models, or contact humans.

Note: the requested `context.md` and `plan.md` were not present at repository root (`C:/Users/adars/Coding/scenetwin/context.md`, `.../plan.md`). This report uses the local reports/scripts/artifacts listed above as source of truth.

## Current local evidence inventory

| Area | Local artifact(s) inspected | Status |
|---|---|---|
| NCR TTS-audio-only run | `cursor/research/output/ncr_similarity.csv`, `cursor/research/output/ncr_full60/ncr_similarity.csv`, `cursor/research/output/ncr_summary.json`, `output/reports/tribe-ncr-results.md` | Full 60-clip TTS-audio NCR exists: 14,400 similarity rows, 240 query vectors summarized, 60 clips. Global tier Spearman is ~0.035 / corrected 3-tier ~0.031: near chance. |
| NCR vector cache | `cursor/research/output/ncr_pilot5/ncr_vectors.npz`; no full `ncr_vectors.npz` under `ncr_full60/` | Pilot vectors are local; full remote vectors were not recovered, only full CSV/log/summary. Full text-vs-TTS vector-level ablation cannot be run from current local caches. |
| NCR analyzers | `cursor/pipeline/neural_contrastive_retrieval.py`, `cursor/research/tribe_ncr_hidden_patterns.py` | Local analyzers now exist and can re-score current CSVs without GPU/API calls. |
| TRIBE tensor summaries | `cursor/research/output/tribe_tensors/manifest.csv`, `cursor/research/output/tribe_tensors/{external,inbench}/*.json` | 78 JSON summary rows exist (60 external, 18 in-benchmark). They contain shapes/scalars, not raw `P_AV`/`P_A` arrays. No `P_silence` column/artifact exists. |
| Video/cache availability | `workspace/external_clips/`, `cursor/data/external_clips/`, `workspace/vatex_clips/` absent; some in-benchmark MP4 copies exist under `output/scenetwin_timing_20clip/...` | External 60 videos are not locally materialized. Creating external silence conditions locally would require downloads or restored media. |
| Local TRIBE runtime | `python` import check | `tribev2` and `torch` are not installed locally; no local GPU/TRIBE inference path is available. |
| BLV/proxy study materials | `output/reports/tribe-review-worksheet.md`, `cursor/research/output/new_findings_round3/review_worksheet_rows.csv`, `cursor/research/output/tribe_crossjudge_gpt5_perq.csv`, `cursor/research/output/tribe_gap_targeted_external_scores.csv` | A study packet can be designed locally from cached rows, but no BLV participant data exists in-repo. |

## Review findings

### 1. Authenticated full text-extractor NCR ablation

- **Severity: HIGH blocker for this item.** Full text-extractor NCR requires gated Llama/TRIBE text path access (`meta-llama/Llama-3.2-3B`) plus GPU inference. Current completed run intentionally avoided the token and used TTS-audio queries; see `output/reports/colab-tribe-ncr-full-run.md` and `tools/colab_tribe_ncr_runner.py`.
- **What is possible locally now:**
  - Re-run current TTS-audio-only analysis from existing CSVs:
    - `python cursor/pipeline/neural_contrastive_retrieval.py`
    - `python cursor/research/tribe_ncr_hidden_patterns.py`
  - Prepare a pre-registered ablation spec without credentials: fixed clip subset, success criteria, quarantine rules for low-alignment rows, and comparison metrics.
  - Verify current baseline artifacts: `cursor/research/output/ncr_similarity.csv`, `cursor/research/output/ncr_summary.json`, `output/reports/tribe-ncr-results.md`.
- **What is not possible locally now:**
  - No full text-extractor TRIBE predictions are cached.
  - Full vectors for the 60-clip TTS run are not local, only the full similarity CSV. The pilot vectors exist at `cursor/research/output/ncr_pilot5/ncr_vectors.npz` but are insufficient for a full ablation.
  - Local Python cannot import `tribev2` or `torch`; local machine is not currently an inference environment.
- **Requires explicit approval/credentials/GPU:**
  1. Explicit approval to use a HuggingFace read token for gated Llama access. Do not use pasted chat tokens; pass credentials via Colab secret/env var only.
  2. Colab/GPU or equivalent GPU runtime.
  3. A new or parameterized runner for the text path. Current `tools/colab_tribe_ncr_runner.py` deliberately uses gTTS + audio-only events.
- **Concrete staged plan:**
  - **Stage A — local prereg/spec (no credentials):** write `output/reports/ncr-text-ablation-protocol.md` defining 5-clip smoke, 20-clip pilot, then 60-clip full; compare TTS-audio vs full text path on correct-rank percentile, source leakage, top-ref hubness, length residual, and alignment-quarantined subsets.
  - **Stage B — approved GPU smoke:** create/modify `tools/colab_tribe_ncr_text_runner.py` so it reads `cursor/research/output/ncr_external60_metadata.json`, loads `TribeModel.from_pretrained('facebook/tribev2')`, authenticates to HuggingFace only from approved runtime env, and writes `/content/tribe_ncr_text/ncr_similarity.csv`, `/content/tribe_ncr_text/ncr_vectors.npz`, `/content/tribe_ncr_text/ncr_run_summary.json`.
  - **Stage C — pilot command sequence after approval:**
    ```bash
    colab new -s scenetwin-l4 --gpu L4
    colab exec -s scenetwin-l4 -f tools/colab_tribe_setup.py --timeout 1800
    colab restart-kernel -s scenetwin-l4
    colab exec -s scenetwin-l4 -f tools/colab_tribe_smoke.py --timeout 1800
    # upload/copy metadata + approved HF env/secret, then run 5-clip config
    colab exec -s scenetwin-l4 -f tools/colab_tribe_ncr_text_runner.py --timeout 3600
    colab download -s scenetwin-l4 /content/tribe_ncr_text/ncr_similarity.csv -o cursor/research/output/ncr_text_pilot5/ncr_similarity.csv
    colab download -s scenetwin-l4 /content/tribe_ncr_text/ncr_vectors.npz -o cursor/research/output/ncr_text_pilot5/ncr_vectors.npz
    ```
  - **Stage D — full run only if pilot passes:** write artifacts under `cursor/research/output/ncr_text_full60/` and a comparison report under `output/reports/tribe-ncr-text-ablation.md`.
- **Estimated value:** Medium but uncertain. Current TTS-audio NCR is near chance globally, with only small source-specificity hints. The text ablation is scientifically clean and answers a reviewer objection, but it is unlikely to become a headline unless the text path materially reduces hubness and lifts tier separation.

### 2. `P_silence` condition

- **Severity: MEDIUM blocker.** The cached tensor summaries have `P_AV_shape`, `P_A_shape`, `P_AD_shape`, and scalar gaps, but no raw arrays and no `P_silence`. `cursor/research/output/tribe_tensors/manifest.csv` has 78 rows and no silence fields.
- **What is possible locally now:**
  - Audit/select candidate clips from existing summaries and router windows.
  - Define the exact `P_silence` semantics and output schema.
  - For the small subset of locally present in-benchmark MP4s under `output/scenetwin_timing_20clip/...`, generate silent media files if desired, but this still does not produce TRIBE predictions without GPU/TRIBE.
- **What is not possible locally now:**
  - No local external MP4s are present (`workspace/external_clips/` missing).
  - No raw `P_AV`/`P_A` arrays are present for recomputing per-timestep control contrasts.
  - Local `tribev2`/`torch` are not installed.
- **Requires explicit approval/GPU and possibly media downloads:**
  1. Product/method decision: define `P_silence` as silent-audio-only response, silent-video response, or black-video+silence response. For the stated comparison (`P_AV vs P_A`, `P_AV vs P_silence`, `P_A vs silence`), the cleanest condition is usually a same-duration silent **audio-only** event, but this should be approved before spending GPU.
  2. GPU/TRIBE inference.
  3. Restored/uploaded videos or explicit approval to download external clips again.
- **Concrete staged plan:**
  - **Stage A — local protocol:** write `output/reports/tribe-silence-condition-protocol.md` with the condition definition, clip subset, and metrics. Use `cursor/research/tribe_tensor_dump_slim.py` as the implementation template.
  - **Stage B — build runner after method approval:** create `tools/colab_tribe_silence_runner.py` that writes per-clip NPZ arrays and summaries:
    - `/content/tribe_silence/<video_id>.npz` with `P_AV`, `P_A`, `P_silence`.
    - `/content/tribe_silence/manifest.csv` with `cos_av_a`, `cos_av_silence`, `cos_a_silence`, `visual_minus_silence_control`, shapes, and failures.
  - **Stage C — approved pilot commands:**
    ```bash
    colab new -s scenetwin-l4 --gpu L4
    colab exec -s scenetwin-l4 -f tools/colab_tribe_smoke.py --timeout 1800
    colab exec -s scenetwin-l4 -f tools/colab_tribe_silence_runner.py --timeout 3600
    colab download -s scenetwin-l4 /content/tribe_silence/manifest.csv -o cursor/research/output/tribe_silence/manifest.csv
    colab download -s scenetwin-l4 /content/tribe_silence/tribe_silence.zip -o cursor/research/output/tribe_silence/tribe_silence.zip
    ```
- **Estimated value:** Medium-low for Paper A, medium for robustness. It would clarify whether the audio-only baseline is measuring soundtrack content or just non-speech/audio complexity. It is unlikely to change the main score/gate results but can strengthen TRIBE triage caveats.

### 3. BLV micro-study

- **Severity: HIGH external-human blocker, LOW compute blocker.** The repository contains proxy and worksheet materials but no BLV participant data. A real BLV micro-study requires recruitment, consent/IRB decision, accessible study materials, and participant time. It does not require Colab/GPU.
- **What is possible locally now:**
  - Build a study packet from existing cached evidence:
    - top cases: `output/reports/tribe-review-worksheet.md`, `cursor/research/output/new_findings_round3/review_worksheet_rows.csv`.
    - matched-question outcomes: `cursor/research/output/tribe_crossjudge_gpt5_perq.csv`.
    - baseline/targeted AD text: `cursor/research/output/tribe_gap_targeted_external_scores.csv`.
    - route/window metadata: `cursor/research/output/tribe_blind_spot_windows.csv`, `cursor/research/output/tribe_blind_spot_cases.csv`.
  - Draft protocol/instrument locally: 10-20 participants, within-subject baseline vs gap-targeted AD, targeted questions after each audio/clip, confidence + NASA-TLX short form, accessibility notes.
  - Generate a CSV stimulus table with randomized condition order and exclude low-alignment/low-confidence items.
- **What is not possible locally now:**
  - Any claim about BLV comprehension/preference effect. Current evidence is LLM/judge proxy only.
  - Human-facing deployment without explicit approval, ethics/consent decision, and accessibility review.
- **Requires explicit approval/humans:**
  1. Approval to recruit BLV participants/advisors and decide whether this is informal advisory feedback or formal human-subjects research.
  2. Participant compensation/recruitment channel.
  3. Accessible survey/playback implementation.
- **Concrete staged plan:**
  - **Stage A — local-only materials:** produce:
    - `output/reports/blv-micro-study-protocol.md`
    - `cursor/research/output/blv_micro_study/stimuli.csv`
    - `cursor/research/output/blv_micro_study/randomization.csv`
    - `output/reports/blv-micro-study-consent-draft.md`
  - **Stage B — dry run with internal/proxy reviewer only:** verify instructions, audio playback, keyboard/screen-reader flow. Do not call it BLV validation.
  - **Stage C — approved human run:** 10-20 BLV participants, 8-12 clips each, within-subject randomized baseline vs targeted AD; primary endpoint = targeted-question accuracy/confidence on TRIBE-matched questions; secondary endpoints = perceived usefulness, cognitive load, verbosity/timing preference.
- **Estimated value:** High for paper/product credibility, but not a quick blocker fix. It directly addresses the recurring limitation that SceneTwin/TRIBE evidence is not BLV-user-validated.

## Recommended priority order

1. **BLV micro-study protocol packet (local-only prep):** highest value per local effort; no GPU/credentials needed until recruitment.
2. **`P_silence` protocol + method decision:** useful robustness check, but do not spend GPU until the silence semantics are approved.
3. **Authenticated full text-extractor NCR:** scientifically clean but expensive and credential-sensitive; current TTS result is weak enough that this should stay lower priority unless reviewers specifically challenge the TTS deviation.

## Residual risks

- Local search only covered files visible in this checkout; hidden remote notebooks may contain additional runners or tensors.
- Many relevant files are currently untracked/modified in the worktree, apparently from prior work. This pass did not normalize or stage them.
- The exact `P_silence` semantics remain a method decision and should not be silently chosen during implementation.
- Any BLV micro-study crosses from artifact prep into human-subjects workflow and needs explicit approval before recruitment or data collection.
- Full text-extractor NCR cannot proceed safely without credential-handling approval; no pasted token should be used.

## Commands run in this pass

```bash
# Attempted required context reads; both missing
# read C:/Users/adars/Coding/scenetwin/context.md
# read C:/Users/adars/Coding/scenetwin/plan.md

# Repository/artifact discovery
find/grep/read targeted searches for NCR, Colab, silence, BLV, tensor, and matched-question artifacts

# Artifact inventory summary
python - <<'PY'
# counted NCR rows, tensor rows, blind-spot rows, checked ncr summary, checked P_silence absence
PY

# Local runtime availability
python - <<'PY'
# attempted import tribev2 and torch; both ModuleNotFoundError
PY

# Local media availability
python - <<'PY'
# checked workspace/external_clips, cursor/data/external_clips, workspace/vatex_clips; all absent
PY

# Worktree state
 git status --short
```
