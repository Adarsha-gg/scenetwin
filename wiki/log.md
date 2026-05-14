# SceneTwin Log

## [2026-05-13] demo | t=0 high-motion trailer sweep

Reran high-motion trailer candidates from the actual start of each YouTube video, because
the live demo needs to work when a clean `watch?v=` URL is pasted. Best start-of-video
presets: Mission Impossible trailer (CLIP top3 0.333, ADQA 3/3), John Wick 4 trailer
(0.332, 3/3), Spider-Man No Way Home trailer (0.317, 3/3), and The Batman trailer
(0.305, 3/3). Top Gun Maverick remains the strongest stress demo when using the 55s action
timestamp (0.394, 3/3). Updated the Live tab presets so the first three one-click demos use
plain t=0 URLs. Sweep artifact: `output/live_high_motion_t0_sweep.csv`.

## [2026-05-13] demo | High-motion trailer presets tested

Swept six movie-trailer style high-motion clips through the exact Live YouTube path:
timestamped download, 8-frame sampling, GPT-4o-mini AD generation, CLIP grounding, and
Claude ADQA. All six downloaded and scored. Best high-motion options: Top Gun Maverick
trailer at 55s (CLIP top3 0.394, ADQA 3/3), Dune Part Two trailer at 82s (0.328, 3/3), and
The Batman trailer at 75s (0.304, 3/3). Added these to the Live tab presets ahead of the
safer non-trailer examples. Sweep artifact: `output/live_high_motion_preset_sweep.csv`.

## [2026-05-13] demo | Live YouTube presets and timestamp-safe trimming

Fixed `demo/live_pipeline.py` so YouTube `t=` / `start=` offsets are respected when ffmpeg
trims live clips. Before this, timestamped demo URLs could download the right video but trim
from 0s. Swept seven candidate live demo videos through the exact Live YouTube pipeline
(download, 8 frames, GPT-4o-mini AD, CLIP, Claude ADQA). Added the top three as one-click
presets in `demo/scenetwin_demo.py`: indoor diving platform (CLIP top3 0.379, ADQA 3/3),
waterfall (0.323, 3/3), and martial arts board break (0.315, 3/3). Sweep artifact:
`output/live_demo_preset_sweep.csv`.

## [2026-05-13] eval | QuerYD human AD + Gemini video-native breaks the frame ceiling

Added `tools/scenetwin_queryd_gemini_eval.py` and ran it on 5 QuerYD clips using real human
AD transcript windows from YouDescribe/QuerYD. Candidate tiers are transcript-derived:
cross-video negative, first utterance, first half, full AD window. Gemini Flash sees the real
trimmed MP4 segment and grades video-native ADQA. Result: CLIP rho = 0.617, Gemini ADQA rho =
0.865, ensemble rho = 0.932, pairwise ordered wins = 13/15, fully ordered = 3/5. This resolves
the VATEX confusion: video-native grading helps when candidates are actual AD transcripts,
not short caption-style candidates. Wiki page: [[research/scenetwin-queryd-video-native-eval]].

## [2026-05-13] live-demo + finding | Auto AD beat pro AD on held out VATEX clip

Rebuilt `demo/scenetwin_demo.py` after the Knowledge → Coding/SceneTwin migration. Two tabs: cached benchmark (18 clips, paths fixed, TRIBE need curve plot added) and Live YouTube (yt-dlp + 8 frames + GPT-4o-mini AD gen + ViT-B-32 CLIP + Claude Haiku ADQA). Cross model setup so the AD generator does not grade its own output. Built `demo/live_pipeline.py` with stages that return (ok, message, payload) and never throw, so the UI degrades gracefully when a stage's dep is missing. Robust yt-dlp fallback chain (tv_embedded + ios + mweb, then android + web_embedded, then Brave / Chrome cookies). New finding: on a held out VATEX clip (FtBS6OZSGMI, beer pour), the auto generated AD scored higher than the pro AD because the sampled frames caught the pre pour moment, so the pro AD's "filling the tall glass" claim was unsupported by the frames. Frame sampled scoring rewards static composition over temporal action. Headline rho = 0.929 still valid on VATEX benchmark categories which are composition heavy. Wiki page: [[research/scenetwin-frame-sampling-temporal-blindspot]].

## [2026-05-13] migration | Moved from Knowledge + njbda

Project split out from `~/Knowledge` (wiki/research/scenetwin*, tools/scenetwin_*, output/scenetwin*, output/reports/scenetwin-*, output/charts/scenetwin_*, demo/scenetwin_demo.py, output/logos/njbda*) and merged with the `~/njbda` workspace (clips, frames, TRIBE colab, eval scripts) under `~/Coding/SceneTwin`. Memory copied over: `project_scenetwin.md` (renamed from project_njbda.md) and `feedback_communication.md`. Knowledge wiki/index.md and MEMORY.md updated to drop SceneTwin entries.
