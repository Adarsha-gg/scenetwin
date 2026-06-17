#!/usr/bin/env python3
"""Export FastAPI JSON payloads to cursor/data/ for offline web UI."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "data"
sys.path.insert(0, str(ROOT / "api"))

from server import cached_clips, qc_gate_benchmark, review_priority, tribe_risk  # noqa: E402


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    tribe = tribe_risk()
    clips = cached_clips()
    review = review_priority()
    qc = qc_gate_benchmark()

    (OUT / "tribe-risk.json").write_text(json.dumps(tribe, indent=2), encoding="utf-8")
    (OUT / "cached-clips.json").write_text(json.dumps(clips, indent=2), encoding="utf-8")
    (OUT / "review-priority.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
    (OUT / "qc_gate.json").write_text(json.dumps(qc, indent=2), encoding="utf-8")

    meta = {
        "exported_from": str(ROOT),
        "n_tribe_clips": tribe.get("n"),
        "n_cached_clips": clips.get("n"),
        "headline_rho": (tribe.get("headline_correlation") or {}).get("rho"),
        "review_priority_top": [c.get("clip_idx") for c in review.get("top_review", [])],
    }
    (OUT / "manifest.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}/tribe-risk.json ({tribe.get('n')} clips)")
    print(f"Wrote {OUT}/cached-clips.json ({clips.get('n')} clips)")


if __name__ == "__main__":
    main()
