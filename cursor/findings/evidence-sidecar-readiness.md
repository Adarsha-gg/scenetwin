# Evidence sidecar readiness

Date: 2026-05-27  
Script: `cursor/methods/evidence_sidecar_readiness.py`  
Input: `cursor/methods/output/task_assistant_affordance.csv`  
Output: `cursor/methods/output/evidence_sidecar_readiness.csv`

## Claim

The Evidence Loop Router is still incomplete unless it outputs the missing
evidence sidecars required to answer safely.

The better SceneTwin use case is:

```text
for each clip/time/query, compile an answerability bill of materials:
  temporal grounding
  sparse keyframe search
  video text/OCR
  ASR transcript
  object/depth evidence
  planner-grounder-verifier
  current-state monitor
  community/human quality gate
```

This is more useful than another AD metric because it tells the product what
evidence must exist before it describes, answers, guides, defers, or escalates.

## Papers combined

| Paper | Sidecar pressure |
|-------|------------------|
| UniTime | Answers need timestamp windows, not just captions |
| T* | Long/dense video needs sparse keyframe search |
| VidText | Scene text is a separate evidence channel |
| VideoMind | Non-trivial answers need planner, grounder, verifier, and answerer roles |
| Vid2Coach / AROMA | Task access needs step state and current user-state comparison |
| GuideDog / StreetReaderAI | Spatial guidance needs depth/orientation guards |
| CoSight | Human context can be useful but needs quality gating |

## Prototype result

After removing eval-label leakage from urgency assignment, the 58 external clips
produce:

```json
{
  "n_clips": 58,
  "urgency_counts": {
    "high": 36,
    "low": 4,
    "medium": 18
  },
  "mean_sidecar_count": 4.793103448275862,
  "sidecar_need_counts": {
    "temporal_grounding": 37,
    "keyframe_search": 27,
    "video_text_ocr": 28,
    "planner_grounder_verifier": 49,
    "object_depth": 16,
    "asr_transcript": 49,
    "current_state_monitor": 18,
    "community_quality_gate": 18
  },
  "high_urgency_target_n": 24,
  "target_with_any_sidecar_rate": 1.0,
  "no_sidecar_target_misses": 0
}
```

Interpretation:

- Every one of the 27 pro-not-best clips has at least one missing evidence
  sidecar.
- 24 of 27 pro-not-best clips land in the deployable high-urgency bucket.
- The high bucket is broad: 36 clips, 24 positives, precision 0.667.
- Planner/verifier and ASR are the most common sidecars, each at 49 of 58 clips.
- Temporal grounding appears in 37 clips; OCR in 28; keyframe search in 27.

## First-principles read

The old product shape was:

```text
video -> AD string -> score
```

The new product shape should be:

```text
video/query/user state
  -> detect missing evidence
  -> retrieve sidecars
  -> choose surface
  -> answer with citations or defer
```

This is the novel use case: SceneTwin as an evidence compiler for accessible
video systems.

## Why this matters for TRIBE

TRIBE-inspired need curves tell us when audio-only state diverges from
audio+visual state. They do not say what evidence fixes the divergence.

The sidecar router supplies the next layer:

```text
TRIBE says "visual access debt exists"
sidecars say "which evidence is missing"
surface router says "how to deliver or defer it"
```

That combination is stronger than using TRIBE as a ranking feature.

## Risks

This is still a proxy over downloaded clips, not a user study. The urgency logic
uses observable fields, but the sidecar labels are heuristic and need real ASR,
OCR, temporal localization, and user-query logs.

The broad high-urgency bucket is a product risk: it could over-request expensive
sidecars. A cost-aware version should rank sidecars by expected value and latency.

The three pro-not-best clips not promoted to high urgency are still not static
caption cases:

| Clip | Category | Current route | Sidecars | Reason it stayed medium |
|------|----------|---------------|---------:|--------------------------|
| `0m0-Q0zz_-c_000112_000122` | How-to & Instructional | `stepwise_task_coach` | 5 | low collision despite task/current-state sidecars |
| `0t0DB1B1w8Y_000000_000010` | Sports | `evidence_indexed_video_agent` | 4 | collision just below high threshold |
| `1HUWWCLza0w_000000_000010` | Sports | `evidence_indexed_video_agent` | 4 | collision below high threshold |

That suggests the next rule should not simply widen high urgency. It should use a
cost-aware lane: sports/stateful clips can get cheap ASR+keyframe sidecars first,
while how-to clips get step/current-state sidecars only when the user is actually
doing the task.

## Next test

Build the actual sidecar cache for a subset:

```text
ASR transcript + OCR snippets + keyframes + timestamp windows
```

Then measure whether grounded answers reduce hallucinated follow-ups and explain
the 3 pro-not-best clips not caught by the current high-urgency bucket.
