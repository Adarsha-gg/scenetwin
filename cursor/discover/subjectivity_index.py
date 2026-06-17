#!/usr/bin/env python3
"""ADQA paper insight: AD is subjective — quantify dual-track disagreement.

No Spearman. Measures how much pro AD diverges from VATEX crowd captions per clip.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
EVAL = json.loads((ROOT / "workspace" / "vatex_eval_clips.json").read_text())
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
ENSEMBLE = ROOT / "output" / "scenetwin_timing_20clip" / "ensemble" / "adqa_clip_ensemble_scores.csv"
OUT = Path(__file__).resolve().parent / "output" / "subjectivity_index.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-subjectivity.md"


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(1, len(a | b))


def main() -> None:
    fc = pd.read_csv(FORECAST)
    ens = pd.read_csv(ENSEMBLE)
    ens_col = "ensemble_w50_adqa_need_weighted_clip"
    rows = []
    for row in EVAL:
        vid = row["video_id"]
        clip = fc[fc["video_id"] == vid]
        if clip.empty:
            continue
        cidx = int(clip.iloc[0]["clip_idx"])
        pro_t = tokens(row["tier3_va11y"])
        short_t = tokens(row["tier1_vatex_short"])
        long_t = tokens(row["tier2_vatex_long"])
        sub_short = 1.0 - jaccard(pro_t, short_t)
        t3 = ens[(ens["clip_idx"] == cidx) & (ens["tier"] == "tier3_va11y")]
        t1 = ens[(ens["clip_idx"] == cidx) & (ens["tier"] == "tier1_vatex_short")]
        margin = float(t3[ens_col].iloc[0] - t1[ens_col].iloc[0]) if len(t3) and len(t1) else float("nan")
        rows.append({
            "clip_idx": cidx,
            "category": row["category"],
            "subjectivity_pro_vs_short": sub_short,
            "ensemble_tier3_margin": margin,
            "tribe_pressure": float(clip.iloc[0]["tribe_pressure"]),
        })
    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    from scipy.stats import spearmanr
    r, p = spearmanr(df["subjectivity_pro_vs_short"], df["ensemble_tier3_margin"])
    FINDINGS.write_text(
        f"# Subjectivity index\n\nρ(subjectivity, tier3_margin)={r:.3f} p={p:.4f}\n\n"
        f"High subjectivity clips: {df.nlargest(5,'subjectivity_pro_vs_short')['clip_idx'].tolist()}\n",
        encoding="utf-8",
    )
    print(f"ρ={r:.3f} p={p:.4f} | wrote {OUT}")


if __name__ == "__main__":
    main()
