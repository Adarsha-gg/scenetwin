---
title: "SceneTwin — NJBDA 2026 Abstract"
conference: NJBDA 13th Annual Symposium, Rowan University, May 20, 2026
theme: "Building Accessible & Sustainable AI Ecosystems: People, Data, Ethics, & Infrastructure"
deadline: 2026-04-17
created: 2026-04-17
updated: 2026-05-04
---

# SceneTwin: A Brain-Grounded Audit Pipeline for AI Audio Description

Audio descriptions (AD) translate visual content into spoken language so blind and low-vision (BLV) viewers can access video. As AI systems begin generating AD at scale, accessibility QA needs more than a single caption score: an audit must identify *where* visual content is missing from the soundtrack, whether the AD text is visually grounded, whether on-screen text is covered, and whether a listener could answer key visual/narrative questions.

We propose **SceneTwin**, a multi-stage audit pipeline for AI-generated AD. Stage 1 uses Meta's TRIBE v2 brain-encoding model, validated against fMRI during naturalistic film viewing, to compute an audio-vs-audiovisual **accessibility-gap curve**: `distance(P_AV[t], P_A[t])`, where `P_AV` and `P_A` are predicted cortical responses to the audiovisual stimulus and audio-only soundtrack. High-gap moments mark windows where audio alone does not recover visual brain-state signal. Stage 2 scores candidate AD text against sampled video frames with CLIP-L14 grounding. Stage 3 flags visible on-screen text with OCR. Stage 4 generates and grades ADQA-style visual comprehension questions with an LLM.

On a 20-clip VideoA11y/VATEX scale-up with four AD candidates per clip (professional VideoA11y AD, two VATEX captions, and a cross-category control), TRIBE produced need curves for all 20 clips. On the 18 clips with complete grounding rows, CLIP robustly ranked description quality: need-weighted CLIP reached Spearman rho=0.733 and Kendall tau=0.588, with 48/54 tier-3-vs-control wins, 11/18 perfectly ordered clips, and permutation-null p<0.0005. Plain window-mean CLIP was close (rho=0.725), so TRIBE's role is accessibility-motivated timing and prioritization rather than a large aggregate boost over visual grounding alone. A corrected frame-grounded LLM-ADQA layer generated 90 questions from sampled video frames and graded 360 anonymized candidate-question pairs blind; it ranked tiers strongly without using professional AD as the answer key (rho=0.803, tau=0.696, 51/54 tier-3 wins, 8/18 perfectly ordered clips, permutation-null p<0.0005). Combining clip-normalized ADQA with CLIP mean improved rank agreement beyond either signal alone (rho=0.929, tau=0.836, 54/54 tier-3 wins, 15/18 perfectly ordered clips, permutation-null p<0.0005), supporting a complementarity claim: CLIP measures visual grounding, while ADQA measures answerability.

SceneTwin reframes brain encoding as an upstream triage layer in a practical AD audit stack. TRIBE decides where inspection is needed; CLIP, OCR, and LLM-ADQA evaluate what the description communicates. Future work validates the audit against BLV user outcomes and compares PAC-S/SigLIP against CLIP.
