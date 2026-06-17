#!/usr/bin/env python3
"""Smoke-test paper-aligned TRIBE proxy on a cached demo clip."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))

import live_pipeline as lp  # noqa: E402

CLIP = ROOT / "demo" / "clips" / "clip_12.mp4"  # highest risk clip
AD = (
    "A group of boys plays volleyball on an outdoor dirt court. "
    "One boy serves and another jumps to spike the ball over a slightly broken net."
)
OUT = Path(__file__).resolve().parent / "output" / "tribe_live_smoke.json"


def main() -> None:
    if not CLIP.exists():
        print(f"Missing {CLIP}")
        return
    ok, msg, data = lp.stage_tribe_proxy(str(CLIP), AD)
    print(f"ok={ok} msg={msg}")
    print(data)
    if ok:
        import json
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
