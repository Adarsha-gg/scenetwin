# Gap-Targeted AD Prompts Preview

Built from `output/scenetwin_description_gain/roi_content_typing_windows.csv` and audio TSVs in `output/scenetwin_description_gain/audio`. 21 prompts emitted.

Output JSONL: `output/scenetwin_description_gain/gap_targeted_prompts.jsonl`.

## Sample 1: clip 1 window 1 (0.9-1.8s, extended_or_integrated_ad)

```
You are generating an audio description for blind/low-vision listeners.

Window: 0.92-1.84s (duration 0.92s)
Recommendation: extended_or_integrated_ad
Speech density: 62%
Audio context (what listener already hears): Somebody's getting ready to crown him.
Visual context available to you: In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger. He takes quick bites and washes them down with a drink. As he continues, he appears to struggle slightly, coughing at times. Around him, people are laughing and clapping, encouraging him to finish. Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.

A brain-encoding model (TRIBE) predicts the listener's cortical response is missing
visual signal from the soundtrack alone. The missing signal decomposes by cortical
content type as follows:

  motion_action        score=0.04  share=4%
  scene_spatial        score=0.37  share=33%
  face_character       score=0.10  share=9%
  object_body          score=0.20  share=18%
  visual_form          score=0.28  share=25%
  language_auditory    score=0.13  share=11%

Dominant gap: scene_spatial (score 0.37).
Second gap:   visual_form (score 0.28, margin 0.09).

Instructions:
- Emphasize scene_spatial content first (describe the place, layout, and spatial arrangement of objects/people). If words remain, cover visual_form (describe shape, color, framing, lighting, or visual state). Skip dimensions with low share.
- Do NOT restate audible content from the soundtrack.
- Select only details supported by the visual context. Do not invent new scenes, people, objects, locations, or actions.
- Word budget: 4 (~2.5 words/sec * 0.92s).
- Use concrete sensory language for the targeted dimensions; avoid generic adjectives.
- Output JSON ONLY, with keys: ad_text (string), targeted_types (list of strings from
  ['motion_action', 'scene_spatial', 'face_character', 'object_body', 'visual_form', 'language_auditory']), word_count (int). No prose outside JSON.

```

## Sample 2: clip 0 window 8 (7.2-8.1s, standard_ad_slot)

```
You are generating an audio description for blind/low-vision listeners.

Window: 7.22-8.12s (duration 0.90s)
Recommendation: standard_ad_slot
Speech density: 0%
Audio context (what listener already hears): [silent]
Visual context available to you: In a bustling kitchen, a chef holds a cherry tomato and counts down in Spanish. With precision, he throws the tomato at a wall, followed by a knife, which pins the tomato in place. The chef smiles, showcasing his skill.

A brain-encoding model (TRIBE) predicts the listener's cortical response is missing
visual signal from the soundtrack alone. The missing signal decomposes by cortical
content type as follows:

  motion_action        score=0.15  share=13%
  scene_spatial        score=0.26  share=22%
  face_character       score=0.17  share=14%
  object_body          score=0.17  share=14%
  visual_form          score=0.26  share=22%
  language_auditory    score=0.17  share=15%

Dominant gap: visual_form (score 0.26).
Second gap:   scene_spatial (score 0.26, margin 0.01).

Instructions:
- Emphasize visual_form content first (describe shape, color, framing, lighting, or visual state). If words remain, cover scene_spatial (describe the place, layout, and spatial arrangement of objects/people). Skip dimensions with low share.
- Do NOT restate audible content from the soundtrack.
- Select only details supported by the visual context. Do not invent new scenes, people, objects, locations, or actions.
- Word budget: 4 (~2.5 words/sec * 0.90s).
- Use concrete sensory language for the targeted dimensions; avoid generic adjectives.
- Output JSON ONLY, with keys: ad_text (string), targeted_types (list of strings from
  ['motion_action', 'scene_spatial', 'face_character', 'object_body', 'visual_form', 'language_auditory']), word_count (int). No prose outside JSON.

```

## Sample 3: clip 1 window 0 (0.0-0.9s, extended_or_integrated_ad)

```
You are generating an audio description for blind/low-vision listeners.

Window: 0.00-0.92s (duration 0.92s)
Recommendation: extended_or_integrated_ad
Speech density: 60%
Audio context (what listener already hears): Somebody's getting ready to crown him.
Visual context available to you: In a Burger King restaurant, a bald man in a gray hoodie is rapidly eating a hamburger. He takes quick bites and washes them down with a drink. As he continues, he appears to struggle slightly, coughing at times. Around him, people are laughing and clapping, encouraging him to finish. Afterward, someone uses ketchup to write 'BURGER EATING' on a tray liner.

A brain-encoding model (TRIBE) predicts the listener's cortical response is missing
visual signal from the soundtrack alone. The missing signal decomposes by cortical
content type as follows:

  motion_action        score=0.23  share=20%
  scene_spatial        score=0.10  share=9%
  face_character       score=0.25  share=22%
  object_body          score=0.26  share=23%
  visual_form          score=0.17  share=15%
  language_auditory    score=0.13  share=11%

Dominant gap: object_body (score 0.26).
Second gap:   face_character (score 0.25, margin 0.01).

Instructions:
- Emphasize object_body content first (describe the salient object or body posture and how it is being used). If words remain, cover face_character (describe visible characters, expression, gaze, attention, social cues). Skip dimensions with low share.
- Do NOT restate audible content from the soundtrack.
- Select only details supported by the visual context. Do not invent new scenes, people, objects, locations, or actions.
- Word budget: 4 (~2.5 words/sec * 0.92s).
- Use concrete sensory language for the targeted dimensions; avoid generic adjectives.
- Output JSON ONLY, with keys: ad_text (string), targeted_types (list of strings from
  ['motion_action', 'scene_spatial', 'face_character', 'object_body', 'visual_form', 'language_auditory']), word_count (int). No prose outside JSON.

```
