# SceneTwin Central Thesis

## One-sentence thesis

**SceneTwin audits whether audio description preserves a blind or low-vision viewer’s mental model of a scene — not just whether it names visible objects.**

A correct scene model means the listener can answer:

- **Who** is present / acting?
- **What action** is happening?
- **How many** people or objects matter?
- **Where** are things relative to each other?
- **Which visual facts are not inferable from the soundtrack alone?**

This reframes the project from “AD caption scoring” to **accessibility safety auditing for scene understanding**.

---

## Why existing evaluation is insufficient

Most automatic AD/caption evaluation rewards object overlap or generic visual grounding. That is not enough for BLV access.

A description can mention all the right nouns and still invert the scene:

- man pushes someone away → says he pulls them closer
- three couples dance in sync → says two couples move out of step
- person cuts pipe with saw → says two people jam the saw and abandon the cut
- pineapple is carved into spirals → says it is mashed and dropped on the ground

Those are not cosmetic errors. They change the listener’s understanding of the event.

**Core failure:** object grounding can pass while scene-model correctness fails.

---

## How every part connects

### 1. ADQA + CLIP: the base semantic audit

Role: measure whether AD text covers visual facts and is grounded in video frames.

What it contributes:

- ADQA asks visual/narrative questions.
- CLIP checks visual grounding.
- Together they form the baseline SceneTwin audit stack.

Limit:

- Generic ADQA questions are opportunistic.
- CLIP is object-biased.
- Neither alone guarantees who/action/count/spatial correctness.

So ADQA+CLIP are necessary, but not sufficient.

---

### 2. Hallucination gate: object-level safety works

Role: detect blatantly wrong visual content.

Existing result:

- object/scene hallucinations caught well: `16/18 = 88.9%`

What it proves:

- SceneTwin can detect many wrong-content ADs.

Limit:

- The gate is strongest when the falsehood changes visible nouns/scenes.
- It breaks when the nouns stay similar but relations/actions/counts change.

So hallucination gating exposes the next problem: **scene-model hallucinations**.

---

### 3. Relational hallucination probes: the missing safety benchmark

Role: turn relation/action/count swaps into explicit comprehension probes.

Artifact:

- `cursor/output/relational_hallucination_probe_set/probes.csv`

Result:

- 23 hallucination clips
- 76 targeted probes
- probe types:
  - action/relation
  - who/role
  - count
  - spatial relation

Why it matters:

- This converts “CLIP missed a weird edge case” into a benchmark:
  **does the AD preserve the listener’s scene model?**

This is the paper’s safety layer.

---

### 4. Scene-model correctness gap: the central empirical finding

Role: consolidate the evidence that object grounding is not enough.

Key result:

| hallucination type | CLIP gate catch |
|---|---:|
| object / scene substitutions | `16/18 = 88.9%` |
| who/action/count/spatial flips | `2/5 = 40.0%` |

Interpretation:

> Current visual grounding can certify the nouns while missing the event.

This is the strongest paper claim.

---

### 5. TRIBE: neural router for where scene-model probes matter

TRIBE should not be sold as the final quality metric.

Its role is routing:

- `P_A`: what the soundtrack alone supports
- `P_AV`: what audiovisual viewing supports
- `P_AV - P_A`: where audio underspecifies the visual scene

Those high-gap moments are where BLV listeners most need AD to preserve the scene model.

New result:

| question source | scene-model question rate |
|---|---:|
| generic GPT-4o ADQA | `45.6%` |
| generic Claude ADQA | `57.8%` |
| TRIBE-prompted all questions | `62.2%` |
| TRIBE high-need matched questions | `79.5%` |

Permutation tests:

- TRIBE high-need vs generic Claude: `+21.8 pp`, p `0.0089`
- TRIBE high-need vs generic GPT-4o: `+34.0 pp`, p `0.00025`
- TRIBE high-need vs all TRIBE-prompted: `+17.3 pp`, p `0.0327`

Interpretation:

> TRIBE does not directly catch hallucinations. TRIBE finds the moments where the evaluator should ask scene-model questions.

This makes TRIBE central without overclaiming.

---

### 6. AD experience/style audit: deployment-facing extension

Role: show that semantic correctness is not the only deployment issue.

Finding:

- many live generated ADs answer ADQA yet sound like frame-by-frame dumps
- perfect ADQA can coexist with poor listening experience

This is secondary, not the main paper claim.

It supports the broader point:

> AD evaluation must be viewer-centered, not metric-centered.

But it should be a discussion/deployment section, not the headline.

---

## Final architecture

SceneTwin becomes a three-layer audit system:

### Layer 1 — Semantic coverage

**Question:** Does the AD cover important visual facts?

Tools:

- ADQA
- CLIP grounding

### Layer 2 — Scene-model safety

**Question:** Does the AD preserve who/action/count/spatial relations?

Tools:

- relational hallucination probes
- targeted scene-model ADQA
- hallucination gate by stratum

### Layer 3 — Neural need routing

**Question:** Where should the evaluator focus because audio alone underspecifies the visual scene?

Tool:

- TRIBE `P_AV - P_A` high-need windows

This is the key integration:

> TRIBE selects moments of likely access loss; SceneTwin probes whether the AD preserves the scene model at those moments.

---

## Paper abstract skeleton

Audio description should let blind and low-vision viewers build the same scene model available to sighted viewers. Existing automatic evaluation often rewards object naming or generic caption similarity, which can miss errors that invert who did what, how many entities are present, or how objects and people relate. We introduce SceneTwin, an audit framework for scene-model correctness in audio description. SceneTwin combines frame-grounded ADQA and visual grounding with targeted probes for who/action/count/spatial relations. We show that an object-grounding hallucination gate catches object/scene substitutions but fails on relation/action/count hallucinations, despite these errors changing viewer understanding. To focus evaluation where it matters, we use TRIBE counterfactual neural predictions to identify moments where audiovisual information exceeds what is available from audio alone. TRIBE-routed high-need moments are significantly enriched for scene-model probes compared with generic ADQA. SceneTwin reframes AD evaluation from caption similarity to accessibility safety: whether a BLV viewer can form the correct mental model of the scene.

---

## The central figure

A single figure should show:

1. Video + soundtrack split into `P_AV` and `P_A`.
2. TRIBE gap identifies high-need moments.
3. SceneTwin asks targeted probes at those moments:
   - who?
   - action?
   - count?
   - spatial relation?
4. Object grounding catches noun swaps but misses relation flips.
5. Scene-model probes catch the viewer-understanding error.

Caption:

> SceneTwin uses neural access-gap routing to target scene-model probes, auditing whether audio description preserves the visual relations needed for BLV comprehension.

---

## What to emphasize / de-emphasize

### Emphasize

- BLV mental-model correctness
- object grounding is insufficient
- relation/action/count hallucinations
- TRIBE as router, not scorer
- targeted probes as safety benchmark

### De-emphasize

- rho maximization
- generic metric leaderboard
- TRIBE as scalar quality metric
- UI/player demos
- speech-budget audit

---

## Next decisive experiment

Run truth vs hallucinated ADs through:

1. CLIP grounding gate
2. generic ADQA
3. TRIBE-routed scene-model probes
4. optionally video-VLM judge

Primary endpoint:

> relation/action/count hallucination catch rate.

Expected headline if it works:

| method | object/scene catch | scene-model catch |
|---|---:|---:|
| CLIP grounding | high | low |
| generic ADQA | medium | medium |
| TRIBE-routed scene-model probes | high | high |

That would make the paper genuinely strong.
