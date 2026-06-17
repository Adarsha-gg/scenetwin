#!/usr/bin/env python3
"""ViDscribe-style query coverage: can each AD tier answer frame-grounded questions?

ViDscribe (2026): BLV users want customizable AD + on-demand visual Q&A.
We score whether AD text *covers* answer_key terms from ADQA questions (proxy for
"could a BLV user get the answer from this AD alone?").
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
FORECAST = TIMING / "tribe_native" / "tribe_failure_forecast.csv"
Q = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
OUT = Path(__file__).resolve().parent / "output" / "vidscribe_query_coverage.csv"

TIER_COLS = {
    "tier0_cross": "tier0_cross_text",
    "tier1_vatex_short": "tier1_vatex_short_text",
    "tier2_vatex_long": "tier2_vatex_long_text",
    "tier3_va11y": "tier3_va11y_text",
}


def answer_terms(answer_key: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", answer_key.lower()))


def coverage(ad: str, answer_key: str) -> float:
    terms = answer_terms(answer_key)
    if not terms:
        return 0.0
    ad_tok = set(re.findall(r"[a-z]{3,}", ad.lower()))
    hit = len(terms & ad_tok)
    return min(1.0, hit / len(terms))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fc = pd.read_csv(FORECAST)
    q = pd.read_csv(Q)
    rows = []
    for _, clip in fc.iterrows():
        cidx = int(clip["clip_idx"])
        qs = q[q["clip_idx"] == cidx]
        for tier, col in TIER_COLS.items():
            ad = str(clip.get(col) or "")
            covs = [coverage(ad, str(r["answer_key"])) for _, r in qs.iterrows()]
            mean_cov = sum(covs) / len(covs) if covs else 0.0
            rows.append({
                "clip_idx": cidx,
                "tier": tier,
                "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier],
                "query_coverage": mean_cov,
                "n_questions": len(covs),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["query_coverage"])
    print(f"ViDscribe query coverage vs tier GT: ρ={rho:.3f} p={p:.4g}")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
