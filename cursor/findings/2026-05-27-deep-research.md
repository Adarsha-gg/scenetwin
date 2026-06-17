# Deep research session — 2026-05-27 (continued)

## TRIBE v2 — how it actually works

Read the [arXiv paper](https://arxiv.org/html/2605.04326) and Meta docs. Key facts:

- **Encoders**: V-JEPA2 (video), Wav2Vec-BERT (audio), LLaMA 3.2 (text via TTS+timings)
- **Output**: fsaverage5 mesh, ~20k vertices, **5s HRF lag**
- **Training**: 720 subjects, 1000+ h fMRI; beats Deep FIR baseline
- **In-silico use**: GLM contrasts recover FFA, PPA, language network — validates **counterfactual** framing
- **Modality ablation**: video→occipital, audio→temporal, text→language/PFC

SceneTwin's correct TRIBE role: **AV−A gap for routing**, not scoring AD text directly.

See `cursor/research/tribe-v2-deep-dive.md`.

## Literature breakthroughs to integrate

| Source | Idea | Action |
|--------|------|--------|
| ADQA (EMNLP 2025) | 40% human ADs lack temporal alignment | Question timing windows, not single-sentence GT |
| IRT + VLM raters (2026) | 6-dimension QC incl. delivery/timing | Future: timing dimension in ADQA grades |
| SemVideo / CineNeuron | Static vs motion semantic layers | `motion_static_adqa_split.py` — motion Qs ρ=0.75 |
| Gaze-aware encoding (2026) | Eye tracking improves naturalistic encoding | Proxy via saliency/motion until gaze data |
| Emotive AD (2025) | BLV users prefer emotive over neutral | Tier3 "pro" may not be universal gold |

See `cursor/research/literature-scan-2026-05-27.md`.

## Label audit — is tier3 wrong?

**Corrected GT violation count (ADQA): 2/18 clips**

| Clip | Violation | Notes |
|------|-----------|-------|
| clip_00 | tier0_cross > tier3_va11y | Cross-video AD beats pro on ADQA (0.2 vs 0.2 tie-ish; tier0=0.2 tier3=0.2) |
| clip_15 | tier2 > tier3 | **Known failure clip** — pro AD barely leads |

Critical-only ADQA violations: **5/18** — weighting critical questions alone is *noisier*, not cleaner.

**Conclusion**: Tier labels are mostly right. Ensemble ρ=0.929 holds. Failures concentrate on high-TRIBE-pressure Sports/Animals clips where **tier2≈tier3** — label noise is local, not systemic.

## Efficiency sweep

| Feature | Fail forecast AUC | Needs TRIBE GPU? |
|---------|-------------------|------------------|
| mean_standard_slot_score | **1.00** | Yes (cached) |
| cheap_need − speech z | **1.00** | Yes (cached) |
| category_sports heuristic | 0.625 | **No** |
| pro_adqa alone | 0.48 | No |

**Best efficiency path**: cache TRIBE need curves offline; live demo uses speech+gap proxies without forward pass.

## Live TRIBE proxy bug

Current `stage_tribe_proxy` compares video-only vs video+AD. Paper counterfactual is **P_AV vs P_A vs P_AD**.

Spec written: `cursor/findings/tribe-live-proxy-fix.md`

## Loop infrastructure

- `cursor/run_loop.sh` — experiments every **120s** (2 min)
- `cursor/loop_guard.sh` — watchdog restarts loop if dead, checks every **120s**
- Stop: `touch cursor/STOP`

Both running in background as of this session.
