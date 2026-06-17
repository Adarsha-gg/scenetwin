#!/usr/bin/env python3
"""AutoAD II R@k/N multi-reference proxy — score AD against ALL VATEX captions.

Instead of single reference, max similarity to any of 10 crowd captions + va11y.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
EVAL = json.loads((ROOT / "workspace" / "vatex_eval_clips.json").read_text())
OVERLAP = {r["video_id"]: r.get("vatex_caps", []) for r in json.loads((ROOT / "workspace" / "vatex_overlap.json").read_text())}
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "multi_ref_r_at_k.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "paper-multi-ref-rk.md"

TIERS = ["tier0_cross", "tier1_vatex_short", "tier2_vatex_long", "tier3_va11y"]


def token_f1(hyp: str, ref: str) -> float:
    ht = set(re.findall(r"[a-z]{3,}", hyp.lower()))
    rt = set(re.findall(r"[a-z]{3,}", ref.lower()))
    if not ht or not rt:
        return 0.0
    p = len(ht & rt) / len(ht)
    r = len(ht & rt) / len(rt)
    return 2 * p * r / max(p + r, 1e-9)


def r_at_k(refs: list[str], hyp: str, k: int = 3) -> float:
    scores = sorted([token_f1(hyp, r) for r in refs], reverse=True)
    return float(sum(scores[:k]) / k) if scores else 0.0


def main() -> None:
    fc = pd.read_csv(FORECAST)
    vid_map = {r["video_id"]: r for r in EVAL}
    rows = []
    for _, clip in fc.iterrows():
        vid = clip["video_id"]
        caps = list(OVERLAP.get(vid, []))
        if vid in vid_map:
            caps.append(vid_map[vid]["tier3_va11y"])
            caps.extend(vid_map[vid].get("tier2_vatex_long", "") and [vid_map[vid]["tier2_vatex_long"]] or [])
        caps = [c for c in caps if c]
        for tier in TIERS:
            col = f"{tier}_text" if f"{tier}_text" in clip else None
            if not col:
                col_map = {"tier3_va11y": "tier3_va11y_text", "tier2_vatex_long": "tier2_vatex_long_text",
                           "tier1_vatex_short": "tier1_vatex_short_text", "tier0_cross": "tier0_cross_text"}
                text = str(clip[col_map[tier]])
            else:
                text = str(clip[col])
            rows.append({"clip_idx": int(clip["clip_idx"]), "tier": tier, "gt": TIERS.index(tier),
                         "r_at_3": r_at_k(caps, text, 3), "r_at_1": r_at_k(caps, text, 1),
                         "n_refs": len(caps)})
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["r_at_3"])
    FINDINGS.write_text(f"# AutoAD II R@3/N proxy\n\nρ vs tier GT: **{rho:.3f}** p={p:.4f}\n", encoding="utf-8")
    print(f"R@3/N ρ={rho:.3f} p={p:.4f}")


if __name__ == "__main__":
    main()
