#!/usr/bin/env python3
"""AVBench-inspired audio–text / video–text consistency proxy for AD candidates.

Paper: AVBench (2026) trains specialized MLLM judges for AV/AT/VT consistency.
We proxy without a judge model:
  - AT: AD should not contradict dominant transcript words in same clip
  - VT: AD should cover ADQA required_visual_evidence terms
  - AV: combined score
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
FORECAST = TIMING / "tribe_native" / "tribe_failure_forecast.csv"
Q = TIMING / "adqa_v4" / "adqa_v4_questions.csv"
OUT = Path(__file__).resolve().parent / "output" / "av_consistency_scores.csv"

TIER_COLS = {
    "tier0_cross": "tier0_cross_text",
    "tier1_vatex_short": "tier1_vatex_short_text",
    "tier2_vatex_long": "tier2_vatex_long_text",
    "tier3_va11y": "tier3_va11y_text",
}


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z]{3,}", text.lower()))


def evidence_terms(clip_idx: int, questions: pd.DataFrame) -> set[str]:
    sub = questions[questions["clip_idx"] == clip_idx]
    terms = set()
    for _, row in sub.iterrows():
        for part in str(row.get("required_visual_evidence", "")).split(";"):
            for w in re.findall(r"[a-z]{3,}", part.lower()):
                terms.add(w)
    return terms


def at_score(ad: str, speech_density: float) -> float:
    """Talky clips: AD should add non-dialogue content, not repeat filler."""
    if speech_density > 0.8:
        # Penalize AD that is mostly generic speech verbs
        generic = len(re.findall(r"\b(says|talks|speaks|talking|speaking)\b", ad.lower()))
        return max(0.0, 1.0 - generic * 0.15)
    return 0.7  # neutral for silent clips


def vt_score(ad: str, evidence: set[str]) -> float:
    if not evidence:
        return 0.5
    ad_tok = tokenize(ad)
    hit = len(evidence & ad_tok)
    return min(1.0, hit / max(3, len(evidence) * 0.4))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fc = pd.read_csv(FORECAST)
    q = pd.read_csv(Q)
    rows = []
    for _, clip in fc.iterrows():
        cidx = int(clip["clip_idx"])
        ev = evidence_terms(cidx, q)
        speech = float(clip.get("mean_speech_density") or 0)
        for tier, col in TIER_COLS.items():
            ad = str(clip.get(col) or "")
            at = at_score(ad, speech)
            vt = vt_score(ad, ev)
            av = 0.4 * at + 0.6 * vt
            rows.append({
                "clip_idx": cidx,
                "tier": tier,
                "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier],
                "at_consistency": round(at, 3),
                "vt_consistency": round(vt, 3),
                "av_consistency": round(av, 3),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)

    from scipy.stats import spearmanr
    for col in ["at_consistency", "vt_consistency", "av_consistency"]:
        rho, p = spearmanr(df["gt"], df[col])
        print(f"{col}: ρ={rho:.3f} p={p:.4g}")
    print(f"Wrote {OUT} ({len(df)} rows)")


if __name__ == "__main__":
    main()
