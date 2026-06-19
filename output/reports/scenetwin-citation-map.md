# SceneTwin Audit Paper Citation Map

Date: 2026-06-19

This file records every external paper/source used in `output/reports/paper-scenetwin-audit-framework.md`, what claim it supports, and where it appears. It is meant to prevent vague “related work” citation stuffing.

| Ref | Source | Used for | Paper sections |
|---|---|---|---|
| Radford et al. 2021, CLIP | `radford2021clip` | CLIP as text-frame visual grounding backbone. | Abstract, §4.1 |
| Han et al. 2024, AutoAD III | `han2024autoad3` | AD generation context; LLM-AD-Eval, CRITIC, multi-reference recall, action coverage baselines; reference-style metric caveat. | §1, §2.1, §2.2, §6.1, References |
| Kala et al. 2025, ADQA | `kala2025adqa` | Frame-grounded QA scoring; critique of single-reference AD evaluation; ADQA leg of SceneTwin. | Abstract, §1, §2.2, §4.2, §10 |
| Li et al. 2025, VideoA11y / G7/G8 timing | `li2025videoa11y` | Timing, synchronization, rubric-quality pressure beyond semantic similarity. | §2.1 |
| RNIB 2025 AI-generated AD report | `rnib2025aigeneratedad` | Industry/accessibility motivation: AI AD is fluent but inaccurate; blind/partially sighted participants and describers say human review remains essential. | §1, §9 |
| Khandelwal et al. 2025, CoAD / StoryRecall | `khandelwal2025coad` | Narrative coherence and repetition baselines; why long-form coherence differs from short-clip semantic matching. | §2.2, §6.4 |
| Yang et al. 2026, AVBench | `yang2026avbench` | Fine-grained text-video / audio-video consistency; baseline/fusion motivation. | §2.2, §6.4 |
| d’Ascoli et al. 2026, TRIBE v2 | `dascoli2026tribe` | Brain-encoding side-car; audio-vs-audiovisual gap; triage not scoring. | Abstract, §1, §2.4, §4.5, §8, References |
| Chang et al. 2024, WorldScribe | `chang2024worldscribe` | Live description policy: intent, sound context, latency, uncertainty; supports hybrid routing framing. | §2.3, §9 |
| Natalie et al. 2024, CustomAD | `natalie2024customad` | User control over AD length/emphasis/presentation; supports user-agency/hybrid workflow discussion. | §2.3, §9 |
| Cheema et al. 2024, Describe Now | `cheema2024describenow` | User-triggered concise/detailed AD; agency vs cognitive load tradeoff. | §2.3, §9 |
| Cheema et al. 2025, DescribePro | `cheema2025describepro` | Human-AI collaborative authoring, forks/tags/editorial control; not full replacement. | §1, §2.3, §9 |
| Do et al. 2026, ADx3 | `do2026adx3` | Collaborative workflow: generation + refinement + adaptive queries; AI drafts need human/editorial loop. | §1, §2.1 |

## Deliberate non-uses / caveats

- Frontier VLM judge results are empirical baselines from our own cached runs, not literature claims; the paper does not cite vendor model reports.
- The LLM-AD-Eval baseline is discussed through AutoAD III, but our local implementation is explicitly a proxy: semantic similarity to T3/pro AD.
- The hallucination gate is not cited to outside hallucination-detection literature yet. It is presented as an empirical SceneTwin result.
- TRIBE is cited only for the encoder/brain-prediction primitive. The AD-review-triage use is SceneTwin’s own experiment.

## Local source notes read

- `cursor/research/papers/autoad-iii.md`
- `cursor/research/papers/adqa.md`
- `cursor/research/papers/videoa11y-timing.md`
- `cursor/research/papers/tribe-v2.md`
- `cursor/research/papers/coad-storyrecall.md`
- `cursor/research/papers/avbench.md`
- `cursor/research/papers/worldscribe.md`
- `cursor/research/papers/describe-now.md`
- `cursor/research/papers/describepro.md`
- `cursor/research/papers/customad.md`
- RNIB page fetched from live web: https://www.rnib.org.uk/professionals/research-and-data/reports-and-insight/exploring-ai-generated-audio-description-can-emerging-technologies-help-expand-access-to-broadcast-media/
