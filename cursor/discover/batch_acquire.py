#!/usr/bin/env python3
"""Download multiple new clips per run — expand test set fast."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ACQUIRE = Path(__file__).resolve().parents[1] / "fundamentals" / "acquire_external_clip.py"


def main() -> None:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    ok = 0
    for i in range(n):
        idx = start + i
        print(f"\n=== acquire {i+1}/{n} index={idx} ===")
        rc = subprocess.call([sys.executable, str(ACQUIRE), "--index", str(idx)], cwd=str(ROOT))
        if rc == 0:
            ok += 1
    print(f"\nBatch done: {ok}/{n} acquired")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
