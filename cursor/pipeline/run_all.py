#!/usr/bin/env python3
"""Run the full external eval pipeline + all discover scripts. One command."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURSOR = ROOT / "cursor"
PY = sys.executable


def run(cmd: list[str], timeout: int = 3600) -> bool:
    print(f"\n>>> {' '.join(cmd[-2:])}")
    rc = subprocess.call(cmd, cwd=str(ROOT), timeout=timeout)
    return rc == 0


def main() -> None:
    steps = [
        ([PY, str(CURSOR / "pipeline" / "external_clip_pipeline.py")], 3600),
        ([PY, str(CURSOR / "discover" / "generalization_gap.py")], 120),
        ([PY, str(CURSOR / "discover" / "story_recall_proxy.py")], 120),
        ([PY, str(CURSOR / "discover" / "subjectivity_index.py")], 120),
        ([PY, str(CURSOR / "discover" / "slot_iou_tribe.py")], 120),
    ]
    ok = 0
    for cmd, to in steps:
        if run(cmd, to):
            ok += 1
    print(f"\n=== FULL RUN: {ok}/{len(steps)} steps OK ===")
    sys.exit(0 if ok >= 1 else 1)


if __name__ == "__main__":
    main()
