#!/usr/bin/env python3
"""VideoA11y + IRT 6-dimension AD quality proxy (2025–2026 papers).

VideoA11y: objectivity, clarity, accuracy, descriptiveness.
IRT AD QC (2026): adds delivery + timing dimensions.

Heuristic proxies on tier text — no human raters.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
FORECAST = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv"
NEED = ROOT / "output" / "scenetwin_timing_20clip" / "need" / "coarse_need_windows.csv"
OUT = Path(__file__).resolve().parent / "output" / "six_dim_rubric.csv"

TIER_COLS = {
    "tier0_cross": "tier0_cross_text",
    "tier1_vatex_short": "tier1_vatex_short_text",
    "tier2_vatex_long": "tier2_vatex_long_text",
    "tier3_va11y": "tier3_va11y_text",
}


def objectivity(ad: str) -> float:
    subjective = len(re.findall(r"\b(beautiful|amazing|wonderful|sadly|fortunately|clearly)\b", ad.lower()))
    return max(0.0, 1.0 - subjective * 0.2)


def clarity(ad: str) -> float:
    words = ad.split()
    if not words:
        return 0.0
    avg_len = sum(len(w) for w in words) / len(words)
    return max(0.0, 1.0 - abs(avg_len - 5.5) / 5.5)


def descriptiveness(ad: str) -> float:
    visual = len(re.findall(r"\b(red|blue|left|right| wearing| holds| stands| walks| runs)\b", ad.lower()))
    return min(1.0, visual / 4.0)


def timing_fit(clip_idx: int, word_count: int, need_df: pd.DataFrame) -> float:
    sub = need_df[need_df["clip_idx"] == clip_idx]
    if sub.empty:
        return 0.5
    extended_frac = (sub["recommendation"] == "extended_or_integrated_ad").mean()
    # More extended windows → need longer AD
    ideal_words = 20 + extended_frac * 40
    return max(0.0, 1.0 - abs(word_count - ideal_words) / max(ideal_words, 1))


def delivery(ad: str, speech_density: float) -> float:
    """Shorter AD when talky; longer when silent."""
    wc = len(ad.split())
    if speech_density > 0.8:
        return max(0.0, 1.0 - max(0, wc - 35) / 35)
    if speech_density < 0.3:
        return min(1.0, wc / 25)
    return 0.7


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fc = pd.read_csv(FORECAST)
    need = pd.read_csv(NEED)
    rows = []
    for _, clip in fc.iterrows():
        cidx = int(clip["clip_idx"])
        speech = float(clip.get("mean_speech_density") or 0)
        for tier, col in TIER_COLS.items():
            ad = str(clip.get(col) or "")
            wc = len(ad.split())
            dims = {
                "objectivity": objectivity(ad),
                "clarity": clarity(ad),
                "descriptiveness": descriptiveness(ad),
                "timing_fit": timing_fit(cidx, wc, need),
                "delivery": delivery(ad, speech),
            }
            dims["accuracy_proxy"] = dims["descriptiveness"]  # placeholder until VLM judge
            composite = sum(dims.values()) / len(dims)
            rows.append({
                "clip_idx": cidx,
                "tier": tier,
                "gt": {"tier0_cross": 0, "tier1_vatex_short": 1, "tier2_vatex_long": 2, "tier3_va11y": 3}[tier],
                **dims,
                "six_dim_mean": composite,
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    rho, p = spearmanr(df["gt"], df["six_dim_mean"])
    print(f"Six-dim rubric vs tier GT: ρ={rho:.3f} p={p:.4g}")
    print(df.groupby("tier")["six_dim_mean"].mean().to_string())
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
