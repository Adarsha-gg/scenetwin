#!/usr/bin/env python3
"""Build self-contained metadata for the Colab NCR runner.

The old NCR Colab cell expected cursor/data/external_clips/registry.jsonl and
external mp4s that are not present in this checkout. This builder reconstructs the
60 external clip/tier records from workspace/vatex_overlap.json plus the clip IDs
already present in cursor/output/external_ensemble_eval.csv.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERLAP = ROOT / "workspace" / "vatex_overlap.json"
EXTERNAL_EVAL = ROOT / "cursor" / "output" / "external_ensemble_eval.csv"
OUT_FULL = ROOT / "cursor" / "research" / "output" / "ncr_external60_metadata.json"
OUT_PILOT = ROOT / "cursor" / "research" / "output" / "ncr_pilot5_metadata.json"


def parse_video_id(video_id: str) -> tuple[str, float, float]:
    yt_id, start_s, end_s = video_id.rsplit("_", 2)
    # Clip IDs use zero-padded whole seconds, e.g. *_000112_000122.
    return yt_id, float(int(start_s)), float(int(end_s))


def words(text: str) -> int:
    return len(str(text).split())


def build_records() -> list[dict]:
    overlap = {row["video_id"]: row for row in json.loads(OVERLAP.read_text(encoding="utf-8"))}
    seen: list[str] = []
    with EXTERNAL_EVAL.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            vid = row["video_id"]
            if vid not in seen:
                seen.append(vid)
    records = []
    for vid in seen:
        src = overlap.get(vid)
        if not src:
            raise KeyError(f"{vid} missing from {OVERLAP}")
        caps = list(src.get("vatex_caps") or [])
        if not caps:
            raise ValueError(f"{vid} has no VATEX captions")
        yt_id, start_s, end_s = parse_video_id(vid)
        tier1 = caps[0]
        tier2 = max(caps, key=len)
        records.append({
            "video_id": vid,
            "yt_id": yt_id,
            "start_s": start_s,
            "end_s": end_s,
            "category": src.get("category", ""),
            "tier1_vatex_short": tier1,
            "tier2_vatex_long": tier2,
            "tier3_va11y": src.get("va11y_desc", ""),
            "source_key": src.get("key", ""),
            "word_counts": {
                "tier1_vatex_short": words(tier1),
                "tier2_vatex_long": words(tier2),
                "tier3_va11y": words(src.get("va11y_desc", "")),
            },
        })
    # Wrong-content control: rotate professional ADs inside the selected external set.
    # This preserves the NCR source-rank test without depending on missing registry state.
    for i, rec in enumerate(records):
        source = records[(i + 1) % len(records)]
        rec["tier0_cross"] = source["tier3_va11y"]
        rec["tier0_source_vid"] = source["video_id"]
        rec["word_counts"]["tier0_cross"] = words(rec["tier0_cross"])
    return records


def main() -> None:
    records = build_records()
    OUT_FULL.parent.mkdir(parents=True, exist_ok=True)
    OUT_FULL.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_PILOT.write_text(json.dumps(records[:5], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT_FULL} ({len(records)} records)")
    print(f"Wrote {OUT_PILOT} ({min(5, len(records))} records)")


if __name__ == "__main__":
    main()
