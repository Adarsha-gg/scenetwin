#!/usr/bin/env python3
"""Generalization gap: benchmark ρ vs external clip tier-order rate."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

EXT_SCORES = Path(__file__).resolve().parents[1] / "fundamentals" / "output" / "external_clip_scores.csv"
REGISTRY = Path(__file__).resolve().parents[1] / "data" / "external_clips" / "registry.jsonl"
OUT = Path(__file__).resolve().parent / "output" / "generalization_gap.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-generalization.md"


def main() -> None:
    if not EXT_SCORES.exists():
        print("no external scores yet")
        return
    df = pd.read_csv(EXT_SCORES)
    # per video: does tier3 composite beat tier1?
    rows = []
    for vid, g in df.groupby("video_id"):
        v = dict(zip(g["tier"], g["composite"]))
        rows.append({
            "video_id": vid,
            "category": g["category"].iloc[0],
            "pro_beats_short": v.get("tier3_va11y", 0) > v.get("tier1_vatex_short", 0),
            "full_order": (
                v.get("tier3_va11y", 0) > v.get("tier2_vatex_long", 0) > v.get("tier1_vatex_short", 0)
                > v.get("tier0_cross", 0)
            ),
            "tier3_composite": v.get("tier3_va11y"),
            "tier1_composite": v.get("tier1_vatex_short"),
        })
    rep = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rep.to_csv(OUT, index=False)
    n = len(rep)
    FINDINGS.write_text(
        f"# Generalization gap (NEW clips)\n\n"
        f"External clips: **{n}**\n"
        f"- pro beats short: {rep['pro_beats_short'].mean():.0%}\n"
        f"- full tier order: **{rep['full_order'].mean():.0%}** ({rep['full_order'].sum()}/{n})\n\n"
        f"Benchmark claims 15/18 full order on ensemble. External heuristic: **{rep['full_order'].sum()}/{n}**.\n\n"
        f"**This challenges the fundamentals** — 18-clip benchmark may overstate tier separability.\n\n"
        f"Failures:\n{rep[~rep['full_order']].to_string(index=False)}\n",
        encoding="utf-8",
    )
    print(rep.to_string(index=False))
    print(f"full order {rep['full_order'].sum()}/{n}")


if __name__ == "__main__":
    main()
