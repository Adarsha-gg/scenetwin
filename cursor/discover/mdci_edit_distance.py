#!/usr/bin/env python3
"""MDCI proxy from 'Making AI Drafts Count' (arxiv 2605.05348) — edit distance across tiers.

Measures TEXT contribution: how much human pro AD edits away from VATEX short/long drafts.
Not correlation — raw edit burden per clip.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
OUT = Path(__file__).resolve().parent / "output" / "mdci_proxy.csv"
FINDINGS = Path(__file__).resolve().parents[1] / "findings" / "discover-mdci.md"


def token_edit_ratio(a: str, b: str) -> float:
    ta = re.findall(r"\w+", a.lower())
    tb = re.findall(r"\w+", b.lower())
    if not ta:
        return 1.0
    # normalized Levenshtein via word overlap
    sa, sb = set(ta), set(tb)
    return 1.0 - len(sa & sb) / max(len(sa), len(sb))


def main() -> None:
    fc = pd.read_csv(FORECAST)
    rows = []
    for _, r in fc.iterrows():
        pro = str(r["tier3_va11y_text"])
        short = str(r["tier1_vatex_short_text"])
        long_c = str(r["tier2_vatex_long_text"])
        e_short = token_edit_ratio(pro, short)
        e_long = token_edit_ratio(pro, long_c)
        rows.append({
            "clip_idx": int(r["clip_idx"]),
            "category": r["category"],
            "mdci_text_vs_short": e_short,
            "mdci_text_vs_long": e_long,
            "pro_words": int(r.get("tier3_va11y_words", len(pro.split()))),
            "tribe_pressure": float(r["tribe_pressure"]),
            "quality_risk": str(r.get("quality_risk", "")),
        })

    df = pd.DataFrame(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    # NEW: clips needing most human edit (high MDCI) vs TRIBE pressure
    from scipy.stats import spearmanr
    r, p = spearmanr(df["mdci_text_vs_short"], df["tribe_pressure"])

    top = df.nlargest(5, "mdci_text_vs_short")[["clip_idx", "category", "mdci_text_vs_short", "tribe_pressure"]]
    FINDINGS.write_text(
        f"# MDCI text-edit proxy (ADx3 quality threshold paper)\n\n"
        f"**Finding:** edit burden (pro vs short) vs TRIBE pressure ρ={r:.3f} p={p:.4f}\n\n"
        f"High MDCI = pro AD is mostly a rewrite of crowd caption, not incremental polish.\n\n"
        f"## Top edit-burden clips\n{top.to_string(index=False)}\n",
        encoding="utf-8",
    )
    print(top.to_string(index=False))
    print(f"ρ(MDCI, tribe_pressure)={r:.3f}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
