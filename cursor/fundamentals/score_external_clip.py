#!/usr/bin/env python3
"""Score external clips WITHOUT the 18-clip ADQA pipeline.

Uses caption-consensus + specificity heuristics to test whether tier ordering
(pro AD > long vatex > short vatex > cross) holds on NEW data.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

EXT_DIR = Path(__file__).resolve().parent.parent / "data" / "external_clips"
REGISTRY = EXT_DIR / "registry.jsonl"
OUT = Path(__file__).resolve().parent / "output" / "external_clip_scores.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "fundamentals-external-clips.md"

TIER_GT = {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}
TIERS = list(TIER_GT.keys())


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def consensus_terms(vatex_caps: list[str]) -> set[str]:
    """Terms appearing in >=40% of crowd captions."""
    if not vatex_caps:
        return set()
    counts: dict[str, int] = {}
    for cap in vatex_caps:
        for t in tokenize(cap):
            counts[t] = counts.get(t, 0) + 1
    thresh = max(2, int(0.4 * len(vatex_caps)))
    return {t for t, c in counts.items() if c >= thresh}


def score_tier(ad: str, consensus: set[str], all_caps: list[str]) -> dict:
    ad_t = tokenize(ad)
    cap_union = set()
    for c in all_caps:
        cap_union |= tokenize(c)
    cons_hit = len(consensus & ad_t) / max(1, len(consensus))
    cap_hit = len(cap_union & ad_t) / max(1, len(cap_union))
    specificity = len(ad_t - cap_union) / max(1, len(ad_t))  # unique detail beyond crowd
    length_norm = min(1.0, len(ad.split()) / 80)
    composite = 0.35 * cons_hit + 0.25 * cap_hit + 0.25 * specificity + 0.15 * length_norm
    return {
        "consensus_coverage": cons_hit,
        "caption_union_coverage": cap_hit,
        "specificity": specificity,
        "composite": composite,
    }


def load_overlap_caps(video_id: str) -> list[str]:
    overlap = json.loads((Path(__file__).resolve().parents[2] / "workspace" / "vatex_overlap.json").read_text())
    for row in overlap:
        if row["video_id"] == video_id:
            return row.get("vatex_caps", [])
    return []


def main() -> None:
    if not REGISTRY.exists():
        print("No external clips yet — run acquire_external_clip.py first")
        return

    rows = []
    clip_summaries = []
    for line in REGISTRY.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        meta = json.loads(line)
        if not meta.get("download_ok", True):
            continue
        vid = meta["video_id"]
        caps = load_overlap_caps(vid)
        consensus = consensus_terms(caps)
        tier_scores = {}
        for tier in TIERS:
            text = meta.get(tier, "")
            s = score_tier(text, consensus, caps)
            tier_scores[tier] = s["composite"]
            rows.append({
                "video_id": vid,
                "category": meta.get("category"),
                "tier": tier,
                "gt": TIER_GT[tier],
                **s,
            })

        ordered = sorted(tier_scores.items(), key=lambda x: -x[1])
        gt_ordered = sorted(TIER_GT.items(), key=lambda x: -x[1])
        pro_wins = tier_scores["tier3_va11y"] > tier_scores["tier1_vatex_short"]
        cross_loses = tier_scores["tier0_cross"] < tier_scores["tier3_va11y"]
        full = (
            tier_scores["tier3_va11y"] > tier_scores["tier2_vatex_long"] > tier_scores["tier1_vatex_short"]
            > tier_scores["tier0_cross"]
        )
        clip_summaries.append({
            "video_id": vid,
            "category": meta.get("category"),
            "pro_beats_short": pro_wins,
            "pro_beats_cross": cross_loses,
            "full_order": full,
            "ranking": " > ".join(t for t, _ in ordered),
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    n = len(clip_summaries)
    pro_rate = sum(c["pro_beats_short"] for c in clip_summaries) / max(n, 1)
    full_rate = sum(c["full_order"] for c in clip_summaries) / max(n, 1)

    lines = [
        "# External clip tier ordering (no ADQA)\n\n",
        f"Scored **{n}** external clips with caption-consensus heuristic.\n\n",
        f"- Pro AD beats short VATEX: **{pro_rate:.0%}** ({sum(c['pro_beats_short'] for c in clip_summaries)}/{n})\n",
        f"- Full tier order (3>2>1>0): **{full_rate:.0%}**\n\n",
        "## Per clip\n\n",
    ]
    for c in clip_summaries:
        flag = "✓" if c["full_order"] else "✗"
        lines.append(f"- {flag} `{c['video_id']}` ({c['category']}): {c['ranking']}\n")

    FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    FINDINGS.write_text("".join(lines), encoding="utf-8")
    print(f"Scored {n} external clips → {OUT}")
    print(f"Pro beats short: {pro_rate:.0%} | full order: {full_rate:.0%}")


if __name__ == "__main__":
    main()
