# New methods catalog — papers → SceneTwin prototypes

Sources read 2026-05-27. Each row maps a **paper idea** to a **new script** in `cursor/methods/`.

| Paper | Year | Novel idea | Our prototype |
|-------|------|------------|---------------|
| [ADQA](https://arxiv.org/pdf/2510.00808) | EMNLP 2025 | Split **Visual Appreciation (VA)** vs **Narrative Understanding (NU)**; MCQ on minutes-long segments | `methods/adqa_va_nu_eval.py` |
| [Scalable AD QC + IRT](https://arxiv.org/html/2602.01390v2) | 2026 | **6 dimensions** incl. delivery/timing; VLM-as-rater | `methods/irt_rubric_proxy.py` |
| [AVBench](https://arxiv.org/html/2605.24652v1) | 2026 | **Audio–video–text consistency** evaluators (AT, VT, AV) | `methods/av_consistency_eval.py` |
| [SemVideo](https://arxiv.org/html/2602.21819v1) | 2026 | **Hierarchical semantics**: static anchor, motion narrative, holistic | `methods/hierarchical_semantic_eval.py` |
| [ViDscribe](https://arxiv.org/html/2603.14662v1) | 2026 | **User-driven VQA** + customizable AD (not one-size-fits-all) | `methods/vidscribe_query_coverage.py` |
| [ADx3](https://arxiv.org/html/2602.02684) | 2026 | GenAD → RefineAD → AdaptAD pipeline | `methods/adx3_slot_generator.py` |
| [VideoA11y](https://huggingface.co/papers/2502.20480) | 2025 | BLV guideline rubric: objectivity, clarity, descriptiveness | `methods/videoa11y_rubric_proxy.py` |
| [MAVERIX](https://arxiv.org/pdf/2503.21699) | 2025 | Questions requiring **joint audio+video** reasoning | `methods/maverix_modality_dependence.py` |
| [TRIBE v2](https://arxiv.org/html/2605.04326) | 2026 | **Counterfactual** P_AV/P_A/P_AD for generation routing | `methods/need_window_ad_generator.py` |
| [AudioCapBench](https://arxiv.org/abs/2602.23649) | 2026 | Audio caption judging split into **accuracy / completeness / hallucination** across sound, music, speech | proposed `methods/audio_sufficiency_qa.py` |
| [LVOmniBench](https://arxiv.org/abs/2603.19217) | 2026 | Long-form A/V QA with unimodal filtering and temporal localization | proposed `methods/longform_access_state_probe.py` |
| [DescribePro](https://arxiv.org/abs/2508.01092) | 2025 | Collaborative AD authoring with forks, tags, and human-AI variations | proposed `methods/variation_pack_router.py` |
| [Describe Now](https://arxiv.org/abs/2411.11835) | 2025 | BLV user-triggered concise/detailed AD; timing/detail preference data | proposed `methods/user_driven_policy_sim.py` |
| [CustomAD](https://arxiv.org/abs/2408.11406) | 2024 | BLV preference controls for length, emphasis, speed, voice, tone, and format | proposed `methods/customization_policy_router.py` |
| [SPICA](https://arxiv.org/abs/2402.07300) | 2024 | Layered temporal navigation plus spatial object exploration | proposed `methods/layered_object_explorer.py` |
| [ADCanvas](https://arxiv.org/abs/2602.07266) | 2026 | BLV creator-side authoring with verification, candidates, and configurable automation | proposed `methods/blv_authoring_agent_qc.py` |
| [WorldScribe](https://arxiv.org/abs/2408.06627) | 2024 | Live descriptions routed by intent, visual context, sound context, and latency | proposed `methods/context_aware_description_policy.py` |
| [FocusedAD](https://arxiv.org/abs/2504.12157) | 2025 | Character identity and narrative-salient region focus for movie AD | proposed `methods/character_identity_memory.py` |
| [MCAD Soccer](https://arxiv.org/abs/2511.09448) | 2025 | Commentary-aware, domain-specific sports AD plus reference-free ARGE-AD rubric | proposed `methods/commentary_residual_ad.py` |
| [Scene2Audio](https://arxiv.org/abs/2603.27295) | 2026 | Nonverbal soundscape surface for aesthetic/vista access, combined with speech | proposed `methods/soundscape_surface_gate.py` |
| [Lightweight VLM accessibility](https://arxiv.org/abs/2511.10615) | 2025 | Edge feasibility and custom BLV evals for 500M/2.2B VLMs | proposed `methods/edge_model_feasibility_gate.py` |
| [Neutral/emotive AD styles](https://www.nature.com/articles/s41599-025-05201-3) | 2025 | Emotive narration can improve visualization, enjoyment, story following, and emotion recognition | proposed `methods/emotive_style_policy.py` |

## What we are NOT doing anymore in the loop

- Bootstrap ρ re-runs on the same ensemble column
- Random weight sweeps on CLIP/ADQA blend
- Re-running `tribe_failure_forecast.py` every tick

Those are frozen baseline checks. The loop now rotates **new method prototypes** above.

## Next papers to ingest

- Long-form AD authoring studies beyond short social clips
- Open-weight audio caption models that can run locally for `audio_sufficiency_qa.py`
- Real user preference datasets linking AD style, identity need, and interaction burden

## Full paper corpus (2026-05-27)

Per-paper critiques, alternatives, and measured ρ: **`cursor/research/papers/`** (PDFs in `sources/`).

Cross-paper metric clusters and fusion experiments: **`cursor/research/papers/CROSS-PAPER-SYNTHESIS.md`**.
