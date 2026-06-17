# Decisive Scene-Model Validation Check

## Verdict

**Not proven locally yet.** The decisive claim needs TRIBE-routed scene-model probes evaluated on the same clips as relation/action/count hallucinations. The current checkout has zero overlap between those sets.

| set | n |
|---|---:|
| human hallucination clips | 23 |
| local TRIBE timing clips | 20 |
| overlap | 0 |

## What is proven / strong already

1. All-clip corpus thesis: professional AD adds more scene-model axes than captions on `314/338` clips, p `5.69e-71`.
2. Object grounding failure: CLIP gate catches object/scene lies at `88.9%`, but scene-model lies at only `40.0%`.
3. TRIBE routing signal: TRIBE high-need questions are `79.5%` scene-model probes vs generic Claude `57.8%` and GPT-4o `45.6%`.
4. Probe artifact: authored relation/action/count probes have exact true+foil manifest support for `15/22` probes. Imperfect because exact-string matching undercounts paraphrases.

## What is missing for the revolutionary claim

Need one matched experiment:

```text
same clips + same hallucinated ADs
compare:
  CLIP grounding gate
  generic ADQA
  TRIBE-routed scene-model probes
endpoint:
  relation/action/count hallucination catch rate
```

## Minimal next run

Either:

A. Run/generate TRIBE high-need windows for the 23 existing hallucination clips; or
B. Author relation/action/count hallucinations on the existing 20 TRIBE timing clips.

Then evaluate whether TRIBE-routed probes catch the scene-model lies CLIP misses.
