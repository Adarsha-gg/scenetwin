# SceneTwin AD Experience Audit

## New finding

Existing SceneTwin metrics mostly ask whether an AD is visually grounded and answers frame-grounded questions. They can still give perfect scores to descriptions that are bad *audio description experiences*: frame-by-frame lists, premature/anticipatory wording, uncertain visual inference, or heavy temporal plot summaries.

This is a BLV-facing gap, not a metric-beautification gap: style guides emphasize preserving dialogue/silence, avoiding spoilers, describing with the action, and writing concise narration rather than a storyboard dump.

## Local novelty check

Repo search found prior work on frame-sampling temporal blind spots, TRIBE timing, hallucination gates, and claim-level gates. I did **not** find an existing `spoiler`, `suspense`, `frame-dump`, `listification`, or style-guide experience audit. This is therefore a new SceneTwin lane: **experience/style compliance as an orthogonal safety layer**.

## Corpus scan

Scanned `3737` local texts: VideoA11y professional ADs, VATEX captions, and live generated ADs.

| kind | n | mean severity | frame-dump/list | anticipation/spoiler | uncertain inference | timing sequence |
|---|---:|---:|---:|---:|---:|---:|
| crowd_caption | 3380 | 0.11 | 0.0% | 0.8% | 0.4% | 9.9% |
| generated_live_ad | 19 | 1.53 | 78.9% | 10.5% | 5.3% | 21.1% |
| professional_ad | 338 | 0.33 | 5.6% | 4.1% | 5.9% | 13.3% |

## Key result

Live generated ADs are the outlier: `15/19` (`78.9%`) have frame-dump/list markers, versus `19/338` (`5.6%`) professional ADs.

Among live ADs with perfect cached ADQA (`adqa >= 1.0`), `12/15` still have frame-dump/list markers. So ADQA can say 'all questions answered' while the text remains a poor listening experience.

## Examples flagged despite high semantic scores

| source | id | adqa | flags | snippet |
|---|---|---:|---|---|
| live_high_motion_preset_sweep.csv | The Batman trailer action | 1.0 | frame_dump_list, timing_sequence | The clip features a series of dynamic scenes. It opens with an aerial view of a dark space marked with cryptic writings and scattered items. Next, a young woman with short hair appears, looking concerned. Following that, |
| live_high_motion_preset_sweep.csv | John Wick 4 trailer action | 1.0 | frame_dump_list | 1. Three silhouetted figures stand on a horizon against a vibrant orange sunset, with the sun appearing large and round, casting a warm glow over the scene.  2. A man in a suit faces a group of people arranged in a semic |
| live_high_motion_preset_sweep.csv | Mission Impossible trailer action | 1.0 | frame_dump_list | The clip features a series of dynamic scenes. The first shows a figure in a narrow, dimly lit alley, holding a weapon. The second scene transitions to a sunset view over a city, with two people conversing on a rooftop. T |
| live_high_motion_preset_sweep.csv | Spider-Man No Way Home trailer action | 1.0 | frame_dump_list | The clip features various scenes. In the first, a man in a dark cloak stands in a dimly lit room, looking intently. The second scene shows three young people in a spacious, slightly disheveled room, engaged in conversati |
| live_high_motion_t0_sweep.csv | Mission Impossible trailer from start | 1.0 | frame_dump_list, timing_sequence | The clip features a series of dynamic scenes. A person rides a motorcycle on a rocky outcrop with mountains in the background, showcasing a vast landscape. The next shot captures a steep drop-off, emphasizing the height. |
| live_high_motion_t0_sweep.csv | Spider-Man No Way Home trailer from start | 1.0 | frame_dump_list, uncertain_inference | The clip features intense scenes from a superhero movie. A young man with tousled hair is shown in close-up, appearing distressed and wet, with city lights reflecting in the background. The title card for "Spider-Man: No |

## Why this helps BLV users

A blind viewer does not just need facts to be present; they need them delivered at the right time, without flattening a movie into a numbered storyboard or spoiling suspense. This layer would route technically-correct-but-unwatchable AI AD to rewrite/human review.

## External grounding checked

- Netflix AD guide: prioritize plot-critical information, allow dialogue/silence, avoid over-description, and preserve suspense.
- Prime Video AD guide: describe with the action; do not spoil surprises by describing before they happen.
- AMI described-video best practices: do not reveal/spoil story content or lessen sequential storytelling impact.
- Recent AD reception work: narrative specificity and spatiotemporal language affect imageability/comprehension for non-sighted listeners.

## Next experiment

Pair each generated AD with an experience rewrite that removes frame-list markers and spoiler/uncertainty wording while preserving facts. Then run a small BLV or proxy listening study measuring comprehension, suspense/immersion, and NASA-TLX effort. This is orthogonal to rho/AUC and actually tests whether SceneTwin makes AI AD watchable.

## Files

- `cursor/pipeline/ad_experience_audit.py`
- `cursor/output/ad_experience_audit/items.csv`
- `cursor/output/ad_experience_audit/summary.json`
