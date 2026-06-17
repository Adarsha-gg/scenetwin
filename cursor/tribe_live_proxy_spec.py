#!/usr/bin/env python3
"""Recommend fixing live TRIBE proxy: use AV−A gap per TRIBE paper counterfactuals."""
from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parent / "findings" / "tribe-live-proxy-fix.md"

CONTENT = """# TRIBE live proxy fix (from paper + code review)

## Current bug in `demo/live_pipeline.py`

`stage_tribe_proxy` compares:
- `B_video` (video-only prediction)
- `B_video+AD` (video + AD text injected)

## What TRIBE paper actually supports

Counterfactual modality experiment:
- **P_AV** = full audiovisual stimulus
- **P_A** = audio-only (visual absent)
- **P_AD** = text/audio description as language channel

SceneTwin need curve already uses `cos(P_AV, P_A)` gap per TR.

## Correct proxy metrics

```python
gap(t) = need_score from AV−A cosine/residual
dg(ad) = cos(mean(P_AV), mean(P_AD)) - cos(mean(P_AV), mean(P_A))
```

Live stage should report:
1. **Accessibility gap** (AV vs A) — pre-AD, matches TRIBE routing
2. **Description gain** (AD vs A relative to AV) — post-AD, matches wiki Description Gain

## Efficiency

Running full TRIBE forward pass is expensive. For live demo:
- Skip TRIBE by default (already done)
- When enabled, compute **mean gap only** on downsampled TRs (every 3rd) 
- Cache `get_events_dataframe` per video slug

## HRF note

TRIBE outputs are **5s HRF-lagged**. Align AD text events to word timings,
not clip start, when injecting text.

## Action items

- [ ] Refactor `stage_tribe_proxy` to load A-only and AV predictions separately
- [ ] Expose `description_gain` alongside `alignment_cosine`
- [ ] Add `--tribe-subsample 3` flag to API AuditRequest
"""

def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(CONTENT, encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
