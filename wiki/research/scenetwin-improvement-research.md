---
title: "SceneTwin: Improvement Research — Models, Metrics, and Directions"
category: research
tags: [SceneTwin, brain-encoding, audio-description, CLIP, evaluation-metrics, accessibility, NJBDA-2026]
sources:
  - https://elifesciences.org/reviewed-preprints/107607
  - https://arxiv.org/html/2505.20027v1
  - https://arxiv.org/html/2506.08277v1
  - https://arxiv.org/html/2602.07570v1
  - https://arxiv.org/html/2505.05071v1
  - https://github.com/aimagelab/pacscore
  - https://arxiv.org/abs/2510.00808
  - https://arxiv.org/html/2602.01390
  - https://proceedings.neurips.cc/paper_files/paper/2024/file/94ef721705ea95d6981632be62bb66e2-Paper-Conference.pdf
  - https://sharegpt4video.github.io/
  - https://dl.acm.org/doi/10.1007/978-3-031-73013-9_23
created: 2026-05-02
updated: 2026-05-02
---

Research summary on concrete tools, models, and papers for significantly improving SceneTwin beyond current TRIBE v2 + CLIP architecture. Organized by gap area. Does not repeat what is already in [[research/scenetwin-accuracy-plan]].

## Scope

This file is a roadmap, not evidence for the current poster result. The current evidence base remains:

- `TRIBE × CLIP` on the original Sintel proof of concept
- CLIP-L14 retrieval on real VideoA11y descriptions
- CLIP-L14 VideoA11y vs VATEX evaluation showing strong wrong-content rejection but weak within-scene AD-quality separation
- exploratory TRIBE ROI/temporal analyses on saved tensors

Near-term priority is narrow: run TRIBE Description Gain on the real VideoA11y/VATEX clips. The models below are candidates for future versions after that result exists.

---

## 1. Better Brain Encoding Models

### VALOR-based multimodal encoding (eLife preprint, 2025)
- **What**: Uses VALOR (Vision-Audio-Language Omni-peRception), a video-text alignment model, as feature extractor for a whole-brain fMRI encoding model trained on naturalistic movie fMRI.
- **Key finding**: VALOR-based encoding outperforms unimodal and static multimodal baselines across both sensory and high-order cortex. Critically, it separately captures audio, visual, and language streams over time — not just a fused embedding.
- **Relevance to SceneTwin**: VALOR would let you compare video predictions and description predictions with modality-decomposed cortical maps rather than the single fused TRIBE output. You could ask "does the description recover the visual-stream response specifically?" rather than a generic cross-modal cosine. Source: [eLifesciences preprint](https://elifesciences.org/reviewed-preprints/107607)

### Multi-modal brain encoding models for multi-modal stimuli (Algonauts 2025 competition, arXiv 2505.20027)
- **What**: Stacked ensemble of pretrained feature extractors (visual, audio, language) with ridge regression to fsaverage5 fMRI responses to movies. Top Algonauts 2025 submissions.
- **Key finding**: Late fusion of video + audio + transcript features substantially beats any single-modality model. Stacking over multiple backbone architectures further improves noise ceiling correlation.
- **Relevance**: The Algonauts 2025 dataset is the right benchmark for validating any new brain encoding component you swap into SceneTwin. If you replace TRIBE with a better encoder, Algonauts 2025 leaderboard scores give you ground truth to compare against. Source: [arXiv 2505.20027](https://arxiv.org/html/2505.20027v1)

### Instruction-tuned video-audio models and brain functional specialization (arXiv 2506.08277, 2025)
- **What**: Shows that instruction-tuned multimodal LLMs (e.g., Gemini, GPT-4V variants) whose internal representations are probed against fMRI responses reveal functional specialization — the model's visual layer predicts visual cortex, language layer predicts language cortex.
- **Key finding**: Functionally-specialized intermediate representations outperform final embeddings for predicting specific brain regions.
- **Relevance**: Instead of using TRIBE's final cortical prediction, you could probe intermediate layers of a multimodal LLM against a target ROI (e.g., PPA). This would let SceneTwin use off-the-shelf models without the TRIBE inference overhead. Source: [arXiv 2506.08277](https://arxiv.org/html/2506.08277v1)

**Recommendation**: Near-term, stick with TRIBE but adopt the Algonauts 2025 framework for validation. Longer-term, VALOR-based encoding with separate audio/visual/language streams is the architectural upgrade to pursue — it directly solves the "TRIBE can't distinguish which modality stream the description matched."

---

## 2. Better Grounding / Scene Matching Than CLIP ViT-B-32

### FG-CLIP (Fine-Grained CLIP, arXiv 2505.05071)
- **What**: CLIP fine-tuned on 40M bounding-box-level region-caption pairs. Adds region-level alignment on top of global image-text alignment.
- **Key finding**: Substantially outperforms standard CLIP on fine-grained visual grounding benchmarks (e.g., Winoground, ARO). Handles spatial relationships and object attributes that CLIP's bag-of-words embedding misses.
- **Relevance**: A direct drop-in replacement for the current CLIP ViT-B-32 grounding step. Weights available on HuggingFace. Would improve detection of descriptions that get spatial layout wrong (e.g., "man on the left" when he's on the right). Source: [arXiv 2505.05071](https://arxiv.org/html/2505.05071v1)

### SigLIP (Google, 2023/2024)
- **What**: Replaces CLIP's softmax contrastive loss with a sigmoid loss that scores each pair independently, making it better for retrieval and fine-grained similarity comparisons.
- **Key finding**: Better calibrated similarity scores than CLIP for retrieval tasks; handles cases where softmax normalization over batch distorts pairwise distances.
- **Relevance**: SceneTwin's CLIP grounding step is fundamentally a retrieval task (does this description match these frames?). SigLIP's pairwise scoring semantics are better suited than CLIP's batch-normalized softmax. SigLIP-So400M is open-source via `transformers`.

**Recommendation**: Replace CLIP ViT-B-32 with FG-CLIP for the grounding check. SigLIP is a secondary option if you want better-calibrated similarity scores without region-level supervision.

---

## 3. State-of-the-Art AD Quality Metrics

### ADQA — QA-based benchmark (arXiv 2510.00808, EMNLP 2025)
- **What**: Benchmark that evaluates ADs using two question types over coherent multi-minute video segments: Visual Appreciation (VA, visual facts) and Narrative Understanding (NU, plot comprehension). Evaluates whether ADs would actually help BLV users understand story and visual details.
- **Key finding**: Standard NLP metrics (BLEU, METEOR, CIDEr) correlate poorly with human judgment on AD quality. QA-based evaluation is more semantically aligned with user need.
- **Relevance**: This is the closest existing work to SceneTwin's intent. ADQA could serve as human-outcome ground truth to validate whether the SceneTwin neural score predicts actual AD usefulness. If SceneTwin's score correlates with ADQA performance, that's a strong validation claim. Code/data at [arxiv.org/abs/2510.00808](https://arxiv.org/abs/2510.00808)

### VLM-based multi-dimensional AD rating (arXiv 2602.01390, 2026)
- **What**: Uses VLMs (GPT-4V, LLaVA) to score ADs along multiple dimensions — completeness, accuracy, relevance, temporal order, cognitive load. Correlates with human expert ratings.
- **Key finding**: VLM raters achieve ~0.7 Spearman correlation with human AD experts across dimensions. Individual dimensions (accuracy, completeness) are more predictive than aggregate scores.
- **Relevance**: Ready-to-use automatic AD evaluation pipeline that SceneTwin could run alongside its neural score to get a multi-dimensional quality signal. The "accuracy" and "hallucination" dimensions directly overlap with SceneTwin's goals. Source: [arXiv 2602.01390](https://arxiv.org/html/2602.01390)

**Recommendation**: Use ADQA as validation ground truth. Use the VLM-based multi-dimensional rater as a fast proxy when you don't have human annotations. Both can run on the same clips as SceneTwin.

---

## 4. Event-Level / Temporal Alignment

### SlowFocus (NeurIPS 2024)
- **What**: Video LLM trained specifically for fine-grained temporal understanding — event boundaries, event duration, event order. Evaluated on dense captioning, temporal QA, moment retrieval.
- **Key finding**: Substantially improves over base VideoLLMs on fine-grained temporal tasks. Uses a "slow focus" attention mechanism that dedicates compute to event-boundary frames.
- **Relevance**: For SceneTwin's per-TR temporal alignment experiment (Experiment 2 in [[research/scenetwin-accuracy-plan]]), SlowFocus could be used to auto-detect event boundaries in a video clip. This lets you align the description to events rather than doing naive time-stretching. Source: [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/94ef721705ea95d6981632be62bb66e2-Paper-Conference.pdf)

### SODA_c metric for dense video captioning
- **What**: SODA_c (Story-Oriented Dense-captioning Alignment) is the standard automatic metric for dense video captioning that rewards temporal overlap between predicted and ground-truth event segments while also evaluating caption quality.
- **Key finding**: SODA_c is better correlated with human judgment than per-event METEOR/CIDEr averages for event-localized description.
- **Relevance**: If SceneTwin moves to event-level scoring, SODA_c is the metric to report alongside the neural score for comparability with the dense captioning literature.

**Recommendation**: Use SlowFocus or any VideoLLM's event-boundary detector to segment the video, then align description sentences to segments. Score temporal alignment with per-segment TRIBE cosine (restricted to scene ROIs) and report SODA_c for academic comparability.

---

## 5. Experience Preservation / Narrative Comprehension

### "I hear what you see" — immersion and enjoyment study (2020, still the primary reference)
- **What**: Empirical study comparing BLV vs. sighted audiences watching films with AD. Measured immersion, narrative understanding, suspense, enjoyment.
- **Key finding**: BLV audiences scored lower on narrative understanding and suspense but equal on most other reception dimensions including enjoyment and presence. The gap is specifically in narrative/plot comprehension, not overall immersion.
- **Relevance**: This is the empirical grounding for SceneTwin's Description Gain framing. The thing ADs most often fail at is narrative understanding, not general immersion — which means ADQA's Narrative Understanding questions are the right target for validation.

### Neutral vs. emotive AD styles (Nature Humanities, 2025)
- **What**: RCT comparing neutral (standard guideline-compliant) vs. emotive (interpretative) AD styles on comprehension and presence ratings from BLV participants.
- **Key finding**: Emotive/interpretative descriptions improve visualization and emotional comprehension; neutral descriptions are more accurate but less engaging. Neither metric captures both.
- **Relevance**: SceneTwin's neural score could potentially detect this tradeoff — emotive descriptions might score higher on language/affect cortex, accurate descriptions on scene-selective cortex. This suggests a two-component score: scene fidelity (PPA/RSC ROIs) + affect alignment (limbic/STS ROIs). Source: [Nature Humanities 2025](https://www.nature.com/articles/s41599-025-05201-3)

---

## 6. Better Contrastive / Retrieval-Style Caption Metrics

### PAC-S (CVPR 2023, extended IJCV 2025)
- **What**: Positive-Augmented Contrastive Score. Fine-tunes a CLIP-based metric using positive augmentation (generated image/text pairs) to better distinguish good from mediocre captions. Outperforms CLIPScore and CIDEr on human-judgment correlation for both images and videos.
- **Code**: [github.com/aimagelab/pacscore](https://github.com/aimagelab/pacscore)
- **Relevance**: This is the right replacement for the raw CLIP cosine in SceneTwin's grounding step. PAC-S is trained to rank captions the way humans rank them, which is closer to what SceneTwin needs than a zero-shot CLIP similarity. It also has a video variant.

### SPECS (Specificity-Enhanced CLIPScore, arXiv 2509.03897)
- **What**: Modifies CLIP with a new objective that rewards correct specific details and penalizes incorrect ones. Designed for long captions where CLIP averages away specificity.
- **Key finding**: Matches open-source LLM-based metrics on human correlation while being much faster.
- **Relevance**: Audio descriptions are long and specific (40-80 words). Standard CLIPScore underweights specific details. SPECS directly addresses this.

**Recommendation**: Replace raw CLIP cosine with PAC-S (available off-the-shelf, video variant exists). Add SPECS as a specificity penalty if descriptions are getting rewarded for vague generalities.

---

## 7. Video Description Generation Models

### ShareGPT4Video / ShareCaptioner-Video (2024)
- **What**: Open-source video captioner trained on ShareGPT4Video dataset (40K videos with GPT-4V-annotated captions). Produces detailed, temporally-aware video descriptions. Available on HuggingFace (`Lin-Chen/ShareCaptioner-Video`).
- **Key finding**: State-of-the-art on long-video dense captioning. Handles both short clips (direct) and long videos (sliding window).
- **Relevance**: Best current open-source model for generating AD-style descriptions of video clips at scale. Can replace manually written descriptions in SceneTwin's pipeline. Source: [sharegpt4video.github.io](https://sharegpt4video.github.io/)

### InternVideo2.5 (January 2025, ECCV 2024 + arXiv 2501.12386)
- **What**: Video-language foundation model achieving SOTA on video understanding benchmarks. InternVideo2.5 specifically adds long-context temporal reasoning, can track targets across tens of thousands of frames.
- **Key finding**: Produces detailed motion descriptions with temporal timestamps. Understands long video contexts (hours).
- **Relevance**: Better than ShareCaptioner-Video for temporally-grounded descriptions (captures "at 0:12, the character...") which directly supports per-event alignment. Source: [InternVideo2 ECCV 2024](https://dl.acm.org/doi/abs/10.1007/978-3-031-73013-9_23)

### VideoLLaMA2 (2024, DAMO-NLP-SG)
- **What**: Open-source video LLM with strong spatial-temporal modeling and built-in audio understanding (processes video + audio jointly).
- **Relevance**: The audio understanding component is key — it can produce descriptions that reference what's heard as well as seen, which matches how real ADs are written (they work around dialogue, not over it). Available on HuggingFace.

**Recommendation**: Use ShareCaptioner-Video for generating baseline descriptions quickly. Use InternVideo2.5 when you need temporally-grounded descriptions for the per-event alignment experiment. VideoLLaMA2 if you need audio-aware description generation.

---

## 8. What BLV Users Actually Need Described

### "Describe Now" (ACM DIS 2025, arXiv 2411.11835)
- **What**: User study with BLV participants on preferences for on-demand vs. pre-scripted AD across video types.
- **Key finding**: BLV users prefer detailed descriptions for heavily visual content (film, animation) and concise descriptions for action sequences. Characters and their emotional states are highest priority; spatial layout is important for orientation scenes; background detail is low priority unless it's narratively relevant.
- **Relevance**: Directly informs what SceneTwin should weight. Character/emotion content → FFA + STS ROIs. Scene/spatial layout → PPA + RSC ROIs. Action → MT+ ROI. SceneTwin could report per-dimension scores matching user priorities. Source: [arXiv 2411.11835](https://arxiv.org/html/2411.11835v2)

### Visual and narrative priorities of BLV audiences (eye-tracking + AD study)
- **What**: Eye-tracking study showing what sighted viewers attend to during scenes that overlaps with what BLV users report needing in ADs: faces/expressions first, then actions, then scene-establishing shots.
- **Key finding**: Automated saliency maps (based on eye-tracking) are a reasonable proxy for what should be described. Character face + action descriptions account for ~70% of user-rated "needed" content.
- **Relevance**: If you want to add a saliency-weighted version of SceneTwin, FFA (face) and EBA (body/action) TRIBE ROI scores should be weighted higher than V1 or A1. This maps cleanly onto the existing TRIBE vertex atlas.

---

## Summary of Actionable Recommendations

| Gap | Tool/Model | Action |
|---|---|---|
| Brain encoder modularity | VALOR encoding model | Adopt for future SceneTwin version; validate against Algonauts 2025 |
| CLIP grounding replacement | FG-CLIP (HuggingFace) | Drop-in for current CLIP ViT-B-32 grounding step |
| Caption metric | PAC-S (github.com/aimagelab/pacscore) | Replace raw CLIP cosine, video variant available |
| AD quality ground truth | ADQA benchmark (arXiv 2510.00808) | Use to validate that SceneTwin score predicts AD usefulness |
| AD generation at scale | ShareCaptioner-Video | Replace hand-written descriptions in POC |
| Temporal alignment | InternVideo2.5 timestamps | Event-boundary detection for per-segment TRIBE scoring |
| VLM-based AD rating | arXiv 2602.01390 pipeline | Multi-dimensional automatic rating alongside neural score |
| ROI weighting | "Describe Now" user study priorities | Weight FFA+STS > PPA+RSC > MT+ > V1 in per-ROI SceneTwin |

---

## See Also

- [[research/scenetwin]]
- [[research/scenetwin-accuracy-plan]]
- [[research/scenetwin-codex-handoff-2026-04-22]]

## Sources

- [VALOR multimodal encoding / eLife 2025](https://elifesciences.org/reviewed-preprints/107607)
- [Multi-modal brain encoding models arXiv 2505.20027](https://arxiv.org/html/2505.20027v1)
- [Instruction-tuned video-audio models + brain specialization arXiv 2506.08277](https://arxiv.org/html/2506.08277v1)
- [FG-CLIP arXiv 2505.05071](https://arxiv.org/html/2505.05071v1)
- [PAC-S GitHub](https://github.com/aimagelab/pacscore)
- [ADQA arXiv 2510.00808](https://arxiv.org/abs/2510.00808)
- [VLM-based AD rating arXiv 2602.01390](https://arxiv.org/html/2602.01390)
- [SlowFocus NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/94ef721705ea95d6981632be62bb66e2-Paper-Conference.pdf)
- [ShareGPT4Video](https://sharegpt4video.github.io/)
- [InternVideo2 ECCV 2024](https://dl.acm.org/doi/abs/10.1007/978-3-031-73013-9_23)
- [Describe Now arXiv 2411.11835](https://arxiv.org/html/2411.11835v2)
- [Neutral vs. emotive AD styles Nature 2025](https://www.nature.com/articles/s41599-025-05201-3)
