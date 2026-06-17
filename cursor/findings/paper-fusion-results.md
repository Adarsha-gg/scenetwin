# Paper fusion results

| fusion | ρ | p | weights |
|--------|---:|---:|---------|
| ensemble_baseline | 0.928 | 0.0000 | existing |
| semantic_core | 0.887 | 0.0000 | {'llm_ad_eval': 0.34, 'adqa_v4': 0.33, 'vt_consistency': 0.33} |
| entity_action | 0.816 | 0.0000 | {'adqa_v4': 0.55, 'critic_entity': 0.2, 'action_coverage': 0.25} |
| grid_best | 0.810 | 0.0000 | {'adqa_v4': 0.75, 'story_recall': 0.0, 'vt_consistency': 0.25} |
| paper_stack_v1 | 0.794 | 0.0000 | {'adqa_v4': 0.35, 'story_recall': 0.2, 'vt_consistency': 0.2, 'action_coverage': 0.1, 'need_weighted_clip': 0.1, 'timing_g7g8': 0.05} |
| timing_semantic | 0.785 | 0.0000 | {'adqa_v4': 0.4, 'timing_g7g8': 0.35, 'need_weighted_clip': 0.25} |
| narrative_ground | 0.781 | 0.0000 | {'adqa_v4': 0.5, 'story_recall': 0.3, 'action_coverage': 0.2} |
| audit_no_ref | 0.776 | 0.0000 | {'adqa_v4': 0.45, 'vt_consistency': 0.4, 'coad_repetition': 0.15} |
