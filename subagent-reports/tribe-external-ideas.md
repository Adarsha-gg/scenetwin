# Research: 25 TRIBE/fMRI/video-neural-encoding ideas for SceneTwin audio-description accessibility research

## Summary
TRIBE v2 makes SceneTwin's existing side-car risk forecaster much more usable for accessibility research because it can predict cortical responses from video, audio, and text inputs on an fsaverage5 cortical mesh, with pretrained weights and a Colab/demo path. The strongest transfer pattern from current literature is to treat audio description (AD) quality as a neuro-computational alignment problem: good AD should preserve visual-event semantics, timing, uncertainty, and narrative salience in predicted brain response spaces, not merely match a reference script.

## Evidence base used
- **TRIBE v2**: multimodal brain encoding model for naturalistic video/audio/text; combines text, audio, and video models in a unified Transformer; predicts average-subject fMRI responses on fsaverage5 with a 5 s hemodynamic offset; code and weights are public. [GitHub](https://github.com/facebookresearch/tribev2), [Meta paper page](https://ai.meta.com/research/publications/a-foundation-model-of-vision-audition-and-language-for-in-silico-neuroscience/), [Hugging Face](https://huggingface.co/facebook/tribev2)
- **BOLD Moments Dataset (BMD)**: 1,102 three-second naturalistic videos, 10 subjects, rich object/scene/action/sentence/memorability metadata, BIDS release, OpenNeuro ds005165; reports that sentence-level descriptions correlate with visual brain activity more strongly than simple labels, and that frame shuffling reduces encoding accuracy in visual cortex. [Nature Communications](https://www.nature.com/articles/s41467-024-50310-3), [OpenNeuro ds005165](https://openneuro.org/datasets/ds005165)
- **Cross-modal brain encoding**: multimodal transformer representations can transfer across language and vision for brain encoding, supporting text-as-proxy tests for visual representations. [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11250991/)
- **ADQA**: evaluates audio descriptions with generated/answered questions because ADs are subjective and single-reference metrics are weak. [ACL Anthology](https://aclanthology.org/2025.emnlp-main.1199/), [project](https://katha-ai.github.io/projects/adqa/)
- **VideoA11y**: uses MLLMs plus accessibility guidelines and evaluates with BLV/sighted user studies on descriptiveness, objectivity, accuracy, and clarity. [Project](https://people-robots.github.io/VideoA11y/), [arXiv](https://arxiv.org/html/2502.20480)
- **Standards/guidance**: W3C requires description of visual content/key information for prerecorded synchronized media; ISO/IEC TS 20071-21 gives audio-description guidance. [W3C WAI](https://www.w3.org/WAI/media/av/description/), [WCAG 2.2 SC 1.2.3](https://www.w3.org/WAI/WCAG22/Understanding/audio-description-or-media-alternative-prerecorded), [ISO](https://www.iso.org/standard/63061.html)
- **Movie/narrative fMRI datasets**: Narrative Movie fMRI ds005531, CNeuroMod/Courtois, StudyForrest, Raiders, 101 Dalbraintians, CineBrain, and narrated-recall datasets support naturalistic narrative validation beyond SceneTwin's current 18 clips. [OpenNeuro ds005531](https://openneuro.org/datasets/ds005531/versions/1.0.0), [Narrated recall dataset](https://pmc.ncbi.nlm.nih.gov/articles/PMC9727629/), [101 Dalbraintians](https://francescasetti.github.io/101-Dalbraintians/), [CineBrain](https://arxiv.org/html/2503.06940v2), [StudyForrest](https://openfmri.org/dataset/ds000113/)

## 25 transferable ideas

1. **Neural-preservation score for AD tiers**
   - **Idea:** Run TRIBE on original video and on the AD-as-audio/text surrogate; score cosine/Pearson similarity between predicted cortical response maps in visual, language, and multimodal ROIs.
   - **Why it fits SceneTwin:** Directly generalizes the current CLIP+ADQA ensemble into a brain-alignment objective.
   - **Validation design:** Apply to SceneTwin's 18 clips x 4 tiers; compare tier ordering against existing human/pro/degraded labels.
   - **Success metric:** Spearman rho with tier quality; pairwise tier-win rate; bootstrap CI improvement over current TRIBE side-car.
   - **Confound:** TRIBE's text-to-speech/transcription path may reward language fluency rather than true visual preservation.
   - **Sources:** TRIBE v2 [GitHub](https://github.com/facebookresearch/tribev2); BMD sentence-description RSA [Nature](https://www.nature.com/articles/s41467-024-50310-3).

2. **Temporal omission risk from TRIBE time-course divergence**
   - **Idea:** Compute time-localized divergence between video-predicted and AD-predicted brain responses to flag missed visual beats.
   - **Why it fits SceneTwin:** SceneTwin already audits frame-grounded AD; this adds a neural temporal signal for omissions.
   - **Validation design:** Inject controlled omissions at object/action/emotion moments and measure divergence peaks near omitted frames.
   - **Success metric:** AUC/recall@k for known omissions; latency error between omitted event and divergence peak.
   - **Confound:** fMRI hemodynamic lag and TRIBE's 5 s offset blur short events.
   - **Sources:** TRIBE hemodynamic offset [GitHub](https://github.com/facebookresearch/tribev2); BMD temporal BOLD analyses [Nature](https://www.nature.com/articles/s41467-024-50310-3).

3. **Frame-shuffle sensitivity as an AD timing benchmark**
   - **Idea:** Use BMD's frame-shuffling logic: compare neural alignment for AD placed in correct pause windows vs shuffled/late timing.
   - **Why it fits SceneTwin:** AD quality depends on when description arrives, not only what it says.
   - **Validation design:** Create shifted AD variants (+/-1, 3, 5, 8 s) and test whether temporal neural score drops monotonically.
   - **Success metric:** Negative slope of score vs time shift; Kendall tau with timing severity.
   - **Confound:** Some descriptions remain useful even if delayed, especially narrative summaries.
   - **Sources:** BMD frame shuffling [Nature](https://www.nature.com/articles/s41467-024-50310-3); W3C AD guidance [W3C](https://www.w3.org/WAI/media/av/description/).

4. **ROI-specific error taxonomy**
   - **Idea:** Map AD failures to ROI families: early visual for low-level scene changes, ventral/category for objects/faces/places, dorsal/parietal for actions/spatial relations, language/DMN for narrative meaning.
   - **Why it fits SceneTwin:** Produces interpretable failure labels beyond one scalar score.
   - **Validation design:** Manually tag errors in current clips, then test which ROI divergences best predict each tag.
   - **Success metric:** Macro-F1 for error-type classification; calibrated per-ROI attribution stability.
   - **Confound:** ROI-to-cognitive-label mappings are approximate and may overinterpret encoding outputs.
   - **Sources:** BMD ROI definitions and action/semantic analyses [Nature](https://www.nature.com/articles/s41467-024-50310-3); encoding/decoding overview [NeuroImage](https://doi.org/10.1016/j.neuroimage.2010.07.073).

5. **Sentence-description objective for generated AD**
   - **Idea:** Optimize candidate AD toward sentence-level semantic representations that BMD found most brain-aligned, instead of object/action keyword lists.
   - **Why it fits SceneTwin:** Supports a richer replacement for CLIP-only visual grounding.
   - **Validation design:** Compare AD variants: keyword-heavy, sentence-rich, pro AD; evaluate neural score and ADQA.
   - **Success metric:** Sentence-rich/pro AD should beat keyword AD on BLV clarity/descriptiveness and neural alignment.
   - **Confound:** Overly verbose descriptions may score high semantically but violate pause constraints.
   - **Sources:** BMD metadata RSA [Nature](https://www.nature.com/articles/s41467-024-50310-3); VideoA11y evaluation dimensions [VideoA11y](https://people-robots.github.io/VideoA11y/).

6. **Neural ADQA question weighting**
   - **Idea:** Weight ADQA questions by TRIBE-predicted neural salience of the visual content they probe.
   - **Why it fits SceneTwin:** ADQA already exists in the repo context; TRIBE can make question sets less arbitrary.
   - **Validation design:** Generate questions, estimate salience from video-only TRIBE activations/ROI magnitude, then compare weighted vs unweighted ADQA.
   - **Success metric:** Higher correlation with human tier rankings and user comprehension tests.
   - **Confound:** Neural salience may favor visually intense content over narratively important but subtle cues.
   - **Sources:** ADQA [ACL](https://aclanthology.org/2025.emnlp-main.1199/); TRIBE [GitHub](https://github.com/facebookresearch/tribev2).

7. **Prospective comprehension risk using ForSeeBench-style questions**
   - **Idea:** Predict whether AD context supports answering near-future visual questions by measuring TRIBE alignment before the question point.
   - **Why it fits SceneTwin:** Turns risk forecasting into a forward-looking accessibility metric.
   - **Validation design:** Build future-event MCQs for clips; compare AD context neural state vs video state before answer window.
   - **Success metric:** Accuracy/AUC for whether users/models answer correctly.
   - **Confound:** Future inference often depends on plot priors, not just preserved visual evidence.
   - **Sources:** ForSeeBench dataset [Hugging Face](https://huggingface.co/datasets/forseebench/forseebench); ADQA [project](https://katha-ai.github.io/projects/adqa/).

8. **Memorability-preservation metric**
   - **Idea:** Estimate whether AD preserves neural signatures of memorable visual events, using BMD/Memento-style memorability metadata.
   - **Why it fits SceneTwin:** Accessibility should preserve what sighted viewers are likely to remember.
   - **Validation design:** Annotate clips for memorable moments; compare pro vs degraded AD on TRIBE responses in high-level visual/parietal ROIs.
   - **Success metric:** Correlation with delayed recall or recognition by BLV/sighted-with-audio participants.
   - **Confound:** AD can make otherwise low-memorability content memorable through wording.
   - **Sources:** BMD memorability analysis [Nature](https://www.nature.com/articles/s41467-024-50310-3); Memento10k/Moments links in BMD data availability [Nature](https://www.nature.com/articles/s41467-024-50310-3).

9. **Social-cue preservation score**
   - **Idea:** Evaluate AD coverage of faces, gaze, body motion, emotion, and intentions through TRIBE divergences in face/body/STS/social-action ROIs.
   - **Why it fits SceneTwin:** Many AD failures are subtle social-cue omissions.
   - **Validation design:** Curate clips with expressions/gaze/body-language; create AD variants omitting social cues.
   - **Success metric:** AUC for social-cue omission; human ratings of character-intent comprehension.
   - **Confound:** TRIBE may not isolate social cognition from generic action/face visibility.
   - **Sources:** BMD face/body/STS ROIs [Nature](https://www.nature.com/articles/s41467-024-50310-3); third visual pathway/social perception review cited in BMD [Trends Cogn Sci DOI](https://doi.org/10.1016/j.tics.2020.11.006).

10. **Action-chain continuity metric**
    - **Idea:** Score whether AD preserves action sequences, not isolated action labels, using temporal/dorsal/parietal TRIBE dynamics.
    - **Why it fits SceneTwin:** SceneTwin's closure metric was killed because shortness bias misranked AD; action-chain neural continuity may avoid that.
    - **Validation design:** Compare pro AD, short AD, and scrambled-action AD on clips with multi-step actions.
    - **Success metric:** Higher ordering accuracy than text length or CLIP similarity; pairwise wins pro > short.
    - **Confound:** Long descriptions may overlap dialogue or violate AD production norms.
    - **Sources:** BMD temporal/order findings [Nature](https://www.nature.com/articles/s41467-024-50310-3); W3C description guidance [W3C](https://www.w3.org/WAI/media/av/description/).

11. **Audio-overlap and cognitive-load predictor**
    - **Idea:** Use TRIBE audio+language predictions to estimate overload when AD competes with dialogue/music/sound effects.
    - **Why it fits SceneTwin:** Accessibility fails when correct visual information is inserted at unusable times.
    - **Validation design:** Create variants with same words in clean pauses vs over dialogue; test predicted multimodal divergence and user comprehension.
    - **Success metric:** Drop in comprehension/clarity ratings predicted by audio-language conflict score.
    - **Confound:** TRIBE is not a listener-fatigue model and may not model BLV listening strategies.
    - **Sources:** TRIBE multimodal inputs [GitHub](https://github.com/facebookresearch/tribev2); Section 508 synchronized media guidance [Section508](https://www.section508.gov/create/synchronized-media/).

12. **Guideline-to-neural audit bridge**
    - **Idea:** Translate W3C/ISO requirements into measurable neural checks: key visual content should reduce video-vs-AD cortical divergence.
    - **Why it fits SceneTwin:** Gives standards-grounded interpretation to model scores.
    - **Validation design:** For each clip, annotate W3C/ISO key visual items, then test whether omissions drive divergence.
    - **Success metric:** Recall of guideline violations at fixed false-positive rate.
    - **Confound:** Standards are normative; TRIBE is descriptive and may not encode legal sufficiency.
    - **Sources:** W3C [WAI](https://www.w3.org/WAI/media/av/description/); ISO/IEC TS 20071-21 [ISO](https://www.iso.org/standard/63061.html).

13. **Reference-free AD generation reranker**
    - **Idea:** Generate multiple AD candidates and rerank by combined SceneTwin score + TRIBE neural preservation.
    - **Why it fits SceneTwin:** SceneTwin is reference-free; TRIBE can add a biologically motivated candidate selector.
    - **Validation design:** Use VideoA11y/MLLM generation prompts; evaluate candidate ranking against BLV and expert ratings.
    - **Success metric:** NDCG/MAP for expert preference; win rate against CLIP+ADQA reranking.
    - **Confound:** Candidate pool quality limits reranking; neural score may prefer generic captions.
    - **Sources:** VideoA11y [project](https://people-robots.github.io/VideoA11y/); TRIBE [GitHub](https://github.com/facebookresearch/tribev2).

14. **Long-form narrative drift detector**
    - **Idea:** Track cumulative divergence between video and AD over a movie/episode to find where BLV narrative model may drift.
    - **Why it fits SceneTwin:** Extends from short clips to long-form AD audits.
    - **Validation design:** Use Narrative Movie fMRI, narrated recall, or 101 Dalbraintians annotations; segment into scenes.
    - **Success metric:** Divergence predicts later recall errors or ADQA failures.
    - **Confound:** Long-range narrative memory may exceed TRIBE's input/context design.
    - **Sources:** OpenNeuro ds005531 [OpenNeuro](https://openneuro.org/datasets/ds005531/versions/1.0.0); narrated recall fMRI [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9727629/); 101 Dalbraintians [site](https://francescasetti.github.io/101-Dalbraintians/).

15. **Narrated-recall alignment benchmark**
    - **Idea:** Use datasets where participants watched movies and then freely recalled them; test whether AD neural scores predict recall content.
    - **Why it fits SceneTwin:** Recall is a user-facing accessibility outcome.
    - **Validation design:** Map recall transcripts to scene-level visual facts; correlate AD-preservation scores with recalled fact coverage.
    - **Success metric:** Pearson/Spearman correlation with recall fact F1.
    - **Confound:** Free recall depends on individual memory, attention, and language ability.
    - **Sources:** Naturalistic movie watching and narrated recall dataset [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC9727629/).

16. **Cross-modal equivalence test: visual-to-language transfer**
    - **Idea:** Test if AD text/audio recovers the same representational geometry as video in TRIBE latent/cortical space.
    - **Why it fits SceneTwin:** Makes "equivalent access" measurable without a reference AD.
    - **Validation design:** Compute RDMs for video, pro AD, degraded AD; compare RDM correlations across clips.
    - **Success metric:** Pro AD RDM closer to video RDM than degraded AD, with permutation p-value.
    - **Confound:** RDMs require enough clips/conditions; current 18 clips may be small.
    - **Sources:** Multimodal transformer transfer across language/vision [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11250991/); RSA methods in BMD [Nature](https://www.nature.com/articles/s41467-024-50310-3).

17. **Dataset expansion from BOLD Moments short events**
    - **Idea:** Build a SceneTwin mini-benchmark by writing/procuring AD for BMD's 3-second clips and using metadata as ground truth.
    - **Why it fits SceneTwin:** BMD's controlled short events match SceneTwin's clip-level evaluation style.
    - **Validation design:** Use object/scene/action/sentence/memorability metadata to generate tiered omissions.
    - **Success metric:** Recovery of known object/action/scene omissions and metadata-weighted scores.
    - **Confound:** BMD videos are silent/short; real AD usually occurs in longer narrative contexts.
    - **Sources:** BMD [Nature](https://www.nature.com/articles/s41467-024-50310-3); OpenNeuro ds005165 [OpenNeuro](https://openneuro.org/datasets/ds005165).

18. **CineBrain audiovisual reconstruction stress test**
    - **Idea:** Use CineBrain-style audiovisual narrative data to test whether SceneTwin/TRIBE scores predict failures in multimodal brain-to-video reconstruction settings.
    - **Why it fits SceneTwin:** Forces the model to handle realistic audiovisual narratives, not silent clips.
    - **Validation design:** Compare AD variants on narrative segments with available neural/audiovisual annotations.
    - **Success metric:** Alignment with reconstruction-relevant audiovisual features and human accessibility ratings.
    - **Confound:** CineBrain is emerging; data availability/licensing may limit immediate use.
    - **Sources:** CineBrain [arXiv](https://arxiv.org/html/2503.06940v2), [GitHub](https://github.com/yanweifu-sii/CineBrain).

19. **Neural salience-guided AD compression**
    - **Idea:** When pause time is limited, select facts whose omission causes largest TRIBE divergence.
    - **Why it fits SceneTwin:** Converts audit scores into actionable script editing.
    - **Validation design:** Create constrained-length AD summaries with neural-salience selection vs CLIP salience vs random.
    - **Success metric:** BLV/sighted-with-audio comprehension per word or per second.
    - **Confound:** Neural salience can over-prioritize motion/visual intensity over plot relevance.
    - **Sources:** BMD memorability/salience evidence [Nature](https://www.nature.com/articles/s41467-024-50310-3); ShortScribe hierarchical summaries [arXiv](https://arxiv.org/html/2402.10382).

20. **Blind-spot discovery via activation-optimized counterexamples**
    - **Idea:** Generate or search clips that maximize TRIBE visual response but are poorly captured by ADQA/CLIP, then add them as adversarial audit cases.
    - **Why it fits SceneTwin:** Finds failure modes before demos/papers overfit to current 18 clips.
    - **Validation design:** Mine videos by high visual-neural novelty and low current score confidence; manually inspect.
    - **Success metric:** Number of confirmed novel failure categories; reviewer agreement.
    - **Confound:** Generated/search-selected clips may be distributionally odd or inaccessible to validate.
    - **Sources:** BMD mentions cortical discovery/video synthesis possibilities [Nature](https://www.nature.com/articles/s41467-024-50310-3); NeuroGen [NeuroImage](https://doi.org/10.1016/j.neuroimage.2021.118812).

21. **Subject/population robustness proxy**
    - **Idea:** Use available multi-subject datasets/noise ceilings to report uncertainty bands for TRIBE-derived accessibility scores.
    - **Why it fits SceneTwin:** Prevents overclaiming from average-subject predictions.
    - **Validation design:** Bootstrap across clips, ROI groups, and available subjects/datasets where possible.
    - **Success metric:** Stable tier ordering under resampling; narrow enough CI for acceptance decisions.
    - **Confound:** TRIBE v2 inference returns an average subject, not BLV-specific neural responses.
    - **Sources:** TRIBE average subject note [GitHub](https://github.com/facebookresearch/tribev2); BMD split-half/noise ceilings [Nature](https://www.nature.com/articles/s41467-024-50310-3).

22. **Mismatch localization heatmap for demos**
    - **Idea:** Visualize per-segment ROI divergence as a heatmap alongside video frames and AD text.
    - **Why it fits SceneTwin:** Makes TRIBE side-car interpretable for reviewers and accessibility stakeholders.
    - **Validation design:** Compare heatmap hotspots with human-annotated omissions in current clips.
    - **Success metric:** Precision@k of highlighted segments; qualitative reviewer usefulness.
    - **Confound:** Heatmaps can imply localization precision that fMRI/TRIBE cannot truly provide.
    - **Sources:** TRIBE plotting utilities and cortical mesh output [GitHub](https://github.com/facebookresearch/tribev2); BMD ROI methodology [Nature](https://www.nature.com/articles/s41467-024-50310-3).

23. **Cross-model ensemble with VIBE/ImageBind-style encoders**
    - **Idea:** Compare TRIBE scores against other multimodal brain encoders or ImageBind-like representations to identify robust neural-accessibility signals.
    - **Why it fits SceneTwin:** Reduces dependence on a single TRIBE architecture.
    - **Validation design:** Run ablations: CLIP-only, ADQA-only, TRIBE, VIBE/NForge/ImageBind-like, ensembles.
    - **Success metric:** Ensemble improves Spearman/tier wins with non-overlapping bootstrap CIs.
    - **Confound:** Some sources are preprints/tools with uncertain maintenance and licensing.
    - **Sources:** VIBE [arXiv](https://arxiv.org/html/2507.17958v2); multimodal brain encoding [arXiv](https://arxiv.org/html/2505.20027); ImageBind brain encoding [OpenReview](https://openreview.net/forum?id=3NMYMLL92j).

24. **Automatic AD defect synthesis from neural dimensions**
    - **Idea:** Create controlled degradations targeting neural dimensions: remove motion verbs, spatial prepositions, social-emotional words, scene anchors, object identities.
    - **Why it fits SceneTwin:** Gives stronger validation than arbitrary tiers.
    - **Validation design:** For each defect family, predict affected ROI group and test against TRIBE divergence.
    - **Success metric:** Correct defect-family classification and monotonic severity response.
    - **Confound:** Language edits may introduce unnatural AD, changing fluency and listener trust.
    - **Sources:** BMD object/scene/action/sentence metadata [Nature](https://www.nature.com/articles/s41467-024-50310-3); ADQA subjectivity discussion [ACL](https://aclanthology.org/2025.emnlp-main.1199/).

25. **Accessibility-specific brain-score benchmark card**
    - **Idea:** Publish a SceneTwin/TRIBE benchmark card reporting where neural evidence is strong, weak, and not BLV-specific.
    - **Why it fits SceneTwin:** Makes the repo's TRIBE claims reviewable and avoids neuroscientific overreach.
    - **Validation design:** Document datasets, ROI choices, inference settings, hemodynamic offset handling, ablations, and failure cases.
    - **Success metric:** Independent reviewer can reproduce rankings and understand residual risk.
    - **Confound:** Requires disciplined reporting rather than a new metric; may expose limitations.
    - **Sources:** Brain-Score/benchmarking tradition cited in BMD [Nature](https://www.nature.com/articles/s41467-024-50310-3); TRIBE code/weights [GitHub](https://github.com/facebookresearch/tribev2).

## Kept sources
- TRIBE v2 GitHub (https://github.com/facebookresearch/tribev2) — primary tool/source for inference behavior, mesh, offset, installation.
- Meta TRIBE v2 paper page (https://ai.meta.com/research/publications/a-foundation-model-of-vision-audition-and-language-for-in-silico-neuroscience/) — official publication context.
- Hugging Face TRIBE v2 (https://huggingface.co/facebook/tribev2) — weights availability.
- BOLD Moments Dataset Nature paper (https://www.nature.com/articles/s41467-024-50310-3) — strongest directly transferable video-fMRI dataset and methods source.
- OpenNeuro ds005165 (https://openneuro.org/datasets/ds005165) — BMD data/code availability.
- Brain encoding models transfer across language and vision (https://pmc.ncbi.nlm.nih.gov/articles/PMC11250991/) — evidence for cross-modal visual-language brain representation testing.
- ADQA ACL/project (https://aclanthology.org/2025.emnlp-main.1199/, https://katha-ai.github.io/projects/adqa/) — modern AD evaluation framing.
- VideoA11y (https://people-robots.github.io/VideoA11y/, https://arxiv.org/html/2502.20480) — accessibility-guideline and user-study grounding.
- W3C/WCAG/ISO/Section 508 guidance — standards grounding for what counts as required visual description.
- Narrative/movie fMRI datasets: OpenNeuro ds005531, narrated recall, 101 Dalbraintians, CineBrain, StudyForrest — transfer/validation datasets.

## Dropped sources
- Generic SEO summaries of audio description — excluded because standards and peer-reviewed ADQA/VideoA11y were stronger.
- Redundant TRIBE forks/search mirrors — excluded except where primary TRIBE GitHub/Meta/HF sources sufficed.
- Uncurated personal project pages for NForge-like demos — noted only indirectly; not used as core evidence because maintenance/provenance is weaker than TRIBE/BMD.
- Non-accessibility video captioning benchmarks without neural or AD-specific angle — excluded to avoid widening scope.

## Gaps and residual risks
- No source found showing TRIBE has been validated specifically on blind/low-vision users or on audio-description quality; all proposals are transfers from naturalistic fMRI, multimodal brain encoding, and AD evaluation literature.
- TRIBE predicts average-subject fMRI, not individual BLV neural responses; accessibility conclusions need behavioral/user validation.
- Some 2025-2026 sources are preprints or emerging datasets; treat as promising but not stable production dependencies.
- The current 18-clip SceneTwin set may be too small for reliable RSA/ROI-heavy analysis without additional clips or controlled synthetic degradations.

## Validation notes for this report
- Web research covered four angles: TRIBE/tools, naturalistic video-fMRI datasets, cross-modal brain encoding, and AD/accessibility evaluation.
- Full content was fetched/read for primary TRIBE GitHub, BMD Nature paper, cross-modal brain encoding, ADQA, VideoA11y, W3C guidance, and OpenNeuro narrative dataset pages.
- Project files were not edited except the requested report path.
