# T* Temporal Search

Source: `sources/arxiv_2504.02259.pdf`
arXiv: 2504.02259
Date read: 2026-05-27

## Why they did it

Long-video understanding has a haystack problem: the answer depends on a small
set of frames, but uniform sampling often misses them. T* reframes temporal
search as a lightweight keyframe search problem.

## Method

T* searches over long video by turning the query into visual cues, selecting
candidate regions, and iteratively zooming toward useful frames. It can plug
into existing VLMs as a frame-selection module.

The associated Long Video Haystack benchmark contains 15,092 human-annotated QA
instances from 988 videos spanning 423 hours.

## Evidence

Under a 32-frame inference budget on the LongVideoBench XL subset, the paper
reports that T* improves GPT-4o from 50.5 percent to 53.1 percent and
LLaVA-OneVision-OV-72B from 56.5 percent to 62.4 percent. The paper also argues
that T* gives stronger cost/latency tradeoffs than simply increasing frames.

## First-principles challenge

SceneTwin should stop pretending that "sample N frames" is neutral. Sampling is
a policy decision. If the key visual evidence appears once, a uniform sampler can
make the model confidently wrong.

For accessibility, this is not just model efficiency. It changes what the user
can trust:

```text
the system looked where the evidence likely was
```

## What I would do if I were them

I would evaluate retrieval failure as a user-visible state:

- relevant frame found
- likely relevant frame found but low confidence
- no supporting frame found
- query needs OCR/ASR/depth instead of visual keyframes

That would make keyframe search compose with other sidecars instead of acting as
the whole solution.

## Relevance to SceneTwin

T* maps directly to a SceneTwin keyframe sidecar. When the router predicts
defer-replay, identity ambiguity, creator QC, community context, or evidence
indexing, it should request sparse keyframes before asking a model to answer.

Implemented proxy:

- `cursor/methods/evidence_sidecar_readiness.py`

The proxy marks 27 of 58 external clips as needing keyframe search.

## Correlation to test

```text
keyframe_search_required
  vs
pro-not-best labels, social collision, and stateful video agent routing
```

If positive, SceneTwin's strongest use case is not writing more AD. It is
finding the few frames needed to decide which access surface is safe.
