#!/usr/bin/env python3
"""ADx3 / TRIBE need-window AD slot generator (GenAD scaffold, no LLM).

Inspired by:
  - ADx3 (2026): GenAD baseline → refine → adapt
  - TRIBE need curves: WHEN to describe
  - VideoA11y: objective, concise, BLV-oriented wording

Outputs JSONL of generated AD *slots* with timing + content hints for one clip per run.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
NEED = TIMING / "need" / "coarse_need_windows.csv"
FORECAST = TIMING / "tribe_native" / "tribe_failure_forecast.csv"
OUT_DIR = Path(__file__).resolve().parent / "output" / "generated_ad"


SLOT_TEMPLATES = {
    "extended_or_integrated_ad": (
        "Between {start:.1f}s and {end:.1f}s: integrated narration — "
        "describe visible action and setting; speech already carries {speech_pct:.0f}% of the clip."
    ),
    "standard_ad_slot": (
        "At {start:.1f}s–{end:.1f}s: standard AD slot — "
        "one sentence on the key visual beat not covered by dialogue."
    ),
    "low_ad_need": None,
    "inspect_visual_event": (
        "At {start:.1f}s: inspect event — brief cue for sudden visual change."
    ),
}


def generate_for_clip(clip_idx: int) -> list[dict]:
    need = pd.read_csv(NEED)
    fc = pd.read_csv(FORECAST)
    clip_row = fc[fc["clip_idx"] == clip_idx]
    if clip_row.empty:
        return []
    clip_row = clip_row.iloc[0]
    pro_ad = str(clip_row.get("tier3_va11y_text") or "")
    windows = need[(need["clip_idx"] == clip_idx) & (need["recommendation"] != "low_ad_need")]
    slots = []
    for _, w in windows.iterrows():
        rec = str(w["recommendation"])
        tmpl = SLOT_TEMPLATES.get(rec)
        if not tmpl:
            continue
        hint = tmpl.format(
            start=float(w["start_s"]),
            end=float(w["end_s"]),
            speech_pct=float(w["speech_density"]) * 100,
        )
        slots.append({
            "clip_idx": clip_idx,
            "start_s": float(w["start_s"]),
            "end_s": float(w["end_s"]),
            "need_score": float(w["need_score"]),
            "recommendation": rec,
            "generation_hint": hint,
            "reference_pro_ad_excerpt": pro_ad[:200],
            "method": "adx3_genad_scaffold_v1",
        })
    return slots


def main() -> None:
    import sys
    clip_idx = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slots = generate_for_clip(clip_idx)
    path = OUT_DIR / f"clip_{clip_idx:02d}_slots.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for s in slots:
            f.write(json.dumps(s) + "\n")
    print(f"Generated {len(slots)} AD slots for clip_{clip_idx:02d} → {path}")
    for s in slots[:3]:
        print(f"  [{s['start_s']:.1f}-{s['end_s']:.1f}s] {s['recommendation']}")


if __name__ == "__main__":
    main()
