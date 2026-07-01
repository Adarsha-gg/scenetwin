# Literature scan — 2026-05-27

Papers searched for SceneTwin extensions and label/metric sanity checks.

## Direct competitors / complements

| Paper | Venue | Relevance to SceneTwin |
|-------|-------|------------------------|
| [ADQA](https://aclanthology.org/2025.emnlp-main.1199/) | EMNLP 2025 | Closest eval framework; **40% of human ADs lack temporal alignment** — challenges our tier GT |
| [Scalable AD QC (IRT + VLM raters)](https://arxiv.org/html/2602.01390v2) | 2026 | 6-dimension rubric + delivery/timing; VLMs ≈ human raters — could augment ADQA |
| [ADx3 collaborative workflow](https://arxiv.org/html/2602.02684) | 2026 | HITL refinement + on-demand queries; TRIBE need windows could drive **when** to prompt |
| [Emotive vs neutral AD reception](https://www.nature.com/articles/s41599-025-05201-3) | 2025 | BLV users prefer emotive AD — our tier3 "pro" label may not be universally optimal |

## Neuro + video (efficiency / new signals)

| Paper | Idea | SceneTwin hook |
|-------|------|----------------|
| [TRIBE v2 foundation model](https://arxiv.org/html/2605.04326) | In-silico counterfactuals, multimodal ablation | Core side-car; use modality ablation not text scoring |
| [SemVideo fMRI→video](https://arxiv.org/html/2602.21819v1) | Hierarchical semantics: static anchor, motion narrative, holistic | Split ADQA into **static vs motion** question buckets |
| [CineNeuron](https://arxiv.org/html/2605.14569v1) | Dual-pathway: bottom-up semantics + top-down memory | Frame selection weighted by **motion TRIBE gap** |
| [Gaze-aware encoding](https://arxiv.org/pdf/2603.11663) | Eye tracking + CNN features beat fixation-free on StudyForrest | Proxy: **center-bias + saliency** until we have gaze |
| [NEURONS](https://arxiv.org/html/2503.11167v2) | Decouple object / concept / scene / blurry video sub-tasks | Match TRIBE ROI gaps to AD slot **content types** |

## Breakthrough hypotheses to test (this session)

1. **Label may be wrong on clip_00/03** — closure sweep already showed shorter AD beats pro on some clips; re-test with ADQA-critical-only GT.
2. **Tier2 > Tier3 on motion-heavy Sports** — VATEX-long may beat pro AD when action is under-described in pro track.
3. **Cheap proxy ≥ TRIBE for routing** — `high_need_seconds_frac + speech_density` without neural forward pass.
4. **ADQA question importance split** — critical questions only may invert tier order on "talky" clips.
5. **TRIBE text path is wrong for AD eval** — paper uses TTS+timings; our live proxy uses raw text injection — measure proxy vs need-curve correlation.
