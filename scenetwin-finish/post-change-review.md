## Review

Note: I did **not** write `C:\Users\adars\Coding\scenetwin\scenetwin-finish\post-change-review.md` because the task also says “Do not edit”; per review-only/no-edit instructions, I left files unchanged.

- Correct:
  - `demo/qc_gate.py` and `cursor/export_static_api.py` parse successfully.
  - Generated JSON is strict-valid JSON: `cached-clips.json n=18`, `tribe-risk.json n=18`, `qc-gate.json n=18`, `review-priority.json n=0`.
  - Static asset URLs referenced by generated `cached-clips.json` / `tribe-risk.json` exist.
  - Dry-run of `cursor/export_static_api.py` with writes monkeypatched produced all four expected payloads.

- Fixed:
  - None; review-only.

- Blocker:
  - None found for syntax/import/static JSON validity in the reviewed paths.

- Note / Findings:
  1. **High — TRIBE benchmark copy overclaims pilot evidence.**
     - `web/pages/benchmark.jsx:8`, `web/pages/benchmark.jsx:34-35`, `web/pages/compare.jsx:50-52`, `web/pages/compare.jsx:61`, and `web/app.jsx:131-132` present TRIBE AUC/recall/review-cut as headline demo facts without the n=2 / feature-selection caveat.
     - Evidence: `output/reports/new-findings.md:51` says in-benchmark TRIBE AUC=1.00 should be “supporting evidence, not a standalone headline”; `output/reports/new-findings.md:84` says safe wording needs “pilot AUC=1 with n=2/family-wise p caveat.”
     - Smallest fix: change labels to “pilot TRIBE triage”, “recall@2 on 2 known failures”, or add the n=2/family-wise caveat beside AUC/recall cards.

  2. **Medium — `web/pages/benchmark.jsx:32` likely mislabels `0.84` as “Held-out rho”.**
     - The reviewed line says `Held-out rho` value `0.84` with subtext `live frame-based demo`.
     - Evidence in project reports distinguishes external SceneTwin rho as `0.873` and safety-gate AUC as `0.84` (`output/reports/paper-scenetwin-consolidated.md:38`, `:48`, `:105`, `:115`).
     - Smallest fix: if this card means external correlation, use `External rho 0.873`; if it means the safety gate, relabel as `CLIP gate AUC 0.84`.

  3. **Medium — generated `cursor/data/review-priority.json` is internally inconsistent.**
     - `cursor/data/review-priority.json:2-6` has `"n": 0`, empty `clips` / `top_review`, but still claims `"Both known ADQA failures rank #1 and #2 in composite score"`.
     - Smallest fix: when no source rows exist, emit a neutral empty-state note, or generate review priority from `qc-gate.json` top flagged clips instead.

  4. **Low — static exporter still depends on API module import.**
     - `README.md:9-11` presents `python cursor/export_static_api.py` as the local-only first step.
     - `cursor/export_static_api.py:101` imports from `api.server`; current environment has FastAPI installed, but a clean “static only” Python env without FastAPI would fail before exporting.
     - Smallest fix: document that exporter needs backend Python deps, or move cached endpoint builders into a dependency-light module imported by both API and exporter.