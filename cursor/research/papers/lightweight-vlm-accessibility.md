# Lightweight VLMs and Custom LLM-Evals for BLV Accessibility

**Source:** [arxiv_2511.10615.pdf](sources/arxiv_2511.10615.pdf) · [arXiv](https://arxiv.org/abs/2511.10615)

## Why they did it

This paper asks whether smaller VLMs can support BLV video description on
consumer devices. It evaluates SmolVLM2 500M and 2.2B variants on outdoor
AVCaps and indoor Charades, using progressive prompts and custom accessibility
dimensions such as spatial orientation, social interaction, action events,
ambience, descriptiveness, objectivity, accuracy, and clarity.

They also test FP32 and INT8 mobile deployment. The key finding is pragmatic:
smaller models are not always worse. The 500M model often gives more objective
or environmentally adaptive descriptions, while the 2.2B model can be clearer or
more accurate in structured scenarios. But mobile latency remains high: their
500M runs still take about 60-83 seconds, so "on-device" is feasible for some
private/offline workflows but not yet for seamless live AD.

## What we agree with

- Deployment is part of the accessibility problem. Cloud-only systems fail on
  privacy, bandwidth, cost, and reliability.
- Model scaling is not monotonic for BLV needs. Bigger can be less objective or
  less useful in a specific context.
- Custom accessibility dimensions are more relevant than BLEU/ROUGE/CIDEr alone.

## What we think is wrong / limited

1. **Latency is under-sold.** A minute-scale local model is not live access; it
   is offline review, authoring assist, or cached detail.
2. **The metrics still lack viewer task grounding.** Spatial orientation and
   clarity are better than BLEU, but they need task outcomes.
3. **No policy for model choice.** The paper compares models but does not decide
   when to run a tiny local model, a larger cloud model, or no model.

## If I were them

I would build a model-selection router:

- local tiny model for privacy-sensitive preview and coarse alerts
- cloud model for high-value verification
- cached/offline model for creator review
- no model when audio sufficiency is high

Then evaluate the router, not only each model.

## SceneTwin relevance

SceneTwin's policy-engine direction needs a deployment layer. The project should
not assume every access decision can call a frontier model. Lightweight VLMs
suggest an edge fallback:

```text
cheap local model -> classify surface and risk
expensive model -> only for high-debt/high-uncertainty clips
human/creator QC -> when claims are unsafe
```

This is directly compatible with the social-collision boundary: use cheap
signals to decide which clips deserve expensive analysis or human review.

## Proposed prototype

`cursor/methods/edge_model_feasibility_gate.py`

Inputs:

- clip category
- speech density
- TRIBE/proxy need
- uncertainty from cheap local model
- privacy/latency budget

Outputs:

- `run_local`
- `run_cloud`
- `defer_to_creator_qc`
- `skip_visual_model`

Hypothesis: a model router will create more usable accessibility than forcing
one VLM across every clip and surface.
