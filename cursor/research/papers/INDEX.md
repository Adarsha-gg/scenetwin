# Paper analyses — SceneTwin research corpus

PDFs live in [`sources/`](sources/). Each note follows: **why they did it → agree/disagree → our alternative → what we built → measured result**.

| Paper | File | arXiv | Implemented |
|-------|------|-------|-------------|
| ADQA | [adqa.md](adqa.md) | 2510.00808 | `methods/adqa_va_nu_eval.py`, benchmark ADQA v4 |
| AutoAD III | [autoad-iii.md](autoad-iii.md) | 2404.14412 | `papers/llm_ad_eval_proxy.py`, `papers/critic_entity.py`, `papers/multi_ref_r_at_k.py` |
| CoAD / StoryRecall | [coad-storyrecall.md](coad-storyrecall.md) | 2510.25440 | `papers/coad_repetition.py`, `discover/story_recall_proxy.py` |
| ADx3 + GenAD threshold | [adx3-genad.md](adx3-genad.md) | 2602.02684, 2605.05348 | `methods/adx3_slot_generator.py`, `discover/mdci_slot_iou.py` |
| AVBench | [avbench.md](avbench.md) | 2605.24652 | `methods/av_consistency_eval.py` |
| ViDscribe | [vidscribe.md](vidscribe.md) | 2603.14662 | `methods/vidscribe_query_coverage.py` |
| SemVideo | [semvideo.md](semvideo.md) | 2602.21819 | `methods/hierarchical_semantic_eval.py` |
| MAVERIX | [maverix.md](maverix.md) | 2503.21699 | `methods/maverix_modality_dependence.py`, `discover/maverix_gate.py` |
| TRIBE v2 | [tribe-v2.md](tribe-v2.md) | 2605.04326 | need curves, `pipeline/`, side-car forecast |
| IRT scalable QC | [irt-scalable-qc.md](irt-scalable-qc.md) | 2602.01390 | `methods/irt_rubric_proxy.py` |
| CA3D | [ca3d.md](ca3d.md) | 2412.10002 | timing overlap in `papers/timing_overlap_g7g8.py` |
| VideoA11y / G7G8 | [videoa11y-timing.md](videoa11y-timing.md) | 2502.20480 | `methods/videoa11y_rubric_proxy.py`, G7/G8 timing |
| AudioCapBench | [audiocapbench.md](audiocapbench.md) | 2602.23649 | proposed `methods/audio_sufficiency_qa.py` |
| LVOmniBench | [lvomnibench.md](lvomnibench.md) | 2603.19217 | proposed `methods/longform_access_state_probe.py` |
| DescribePro | [describepro.md](describepro.md) | 2508.01092 | proposed `methods/variation_pack_router.py` |
| Describe Now | [describe-now.md](describe-now.md) | 2411.11835 | proposed `methods/user_driven_policy_sim.py` |
| CustomAD | [customad.md](customad.md) | 2408.11406 | proposed `methods/customization_policy_router.py` |
| SPICA | [spica.md](spica.md) | 2402.07300 | proposed `methods/layered_object_explorer.py` |
| ADCanvas | [adcanvas.md](adcanvas.md) | 2602.07266 | proposed `methods/blv_authoring_agent_qc.py` |
| WorldScribe | [worldscribe.md](worldscribe.md) | 2408.06627 | proposed `methods/context_aware_description_policy.py` |
| FocusedAD | [focusedad.md](focusedad.md) | 2504.12157 | proposed `methods/character_identity_memory.py` |
| MCAD Soccer | [mcad-soccer.md](mcad-soccer.md) | 2511.09448 | proposed `methods/commentary_residual_ad.py` |
| Scene2Audio | [scene2audio.md](scene2audio.md) | 2603.27295 | proposed `methods/soundscape_surface_gate.py` |
| Lightweight VLM accessibility | [lightweight-vlm-accessibility.md](lightweight-vlm-accessibility.md) | 2511.10615 | proposed `methods/edge_model_feasibility_gate.py` |
| Neutral/emotive AD styles | [emotive-ad-style.md](emotive-ad-style.md) | Nature 2025 | proposed `methods/emotive_style_policy.py` |
| Proactive BLV visual questions | [proactive-visual-questions.md](proactive-visual-questions.md) | 2510.01576 | `methods/visual_assistant_skill_policy.py` |
| MLLM visual assistant diary | [mllm-visual-assistant-diary.md](mllm-visual-assistant-diary.md) | 2602.13469 | `methods/visual_assistant_skill_policy.py` |
| Multimodal Agent Video Player | [mavp-agent-video-player.md](mavp-agent-video-player.md) | 2602.04104 | `methods/visual_assistant_skill_policy.py` |
| GuideDog | [guidedog.md](guidedog.md) | 2503.12844 | `methods/visual_assistant_skill_policy.py` |
| Vid2Coach | [vid2coach.md](vid2coach.md) | 2506.00717 | `methods/task_assistant_affordance.py` |
| AROMA | [aroma.md](aroma.md) | 2507.10963 | `methods/task_assistant_affordance.py` |
| StreetReaderAI | [streetreaderai.md](streetreaderai.md) | 2508.08524 | `methods/task_assistant_affordance.py` |
| CoSight | [cosight.md](cosight.md) | 2508.08582 | `methods/task_assistant_affordance.py` |
| UniTime | [unitime.md](unitime.md) | 2506.18883 | `methods/evidence_sidecar_readiness.py` |
| VidText | [vidtext.md](vidtext.md) | 2505.22810 | `methods/evidence_sidecar_readiness.py` |
| VideoMind | [videomind.md](videomind.md) | 2503.13444 | `methods/evidence_sidecar_readiness.py` |
| T* Temporal Search | [tstar-temporal-search.md](tstar-temporal-search.md) | 2504.02259 | `methods/evidence_sidecar_readiness.py` |

Cross-paper synthesis: **[CROSS-PAPER-SYNTHESIS.md](CROSS-PAPER-SYNTHESIS.md)**

Metric pairwise correlations: `cursor/papers/output/metric_correlations.csv`

Fusion experiments: `cursor/papers/paper_fusion_v1.py` → `cursor/papers/output/paper_fusion_scores.csv`

Updated: 2026-05-27
