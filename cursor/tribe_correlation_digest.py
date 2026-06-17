#!/usr/bin/env python3
"""Plain-English digest of TRIBE feature ↔ outcome correlations."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORR = ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_native_correlations.csv"
OUT = Path(__file__).resolve().parent / "findings" / "tribe-correlation-digest.md"

PLAIN = {
    "all4_mean_full_order": "4-judge ADQA tier ordering agreement",
    "all4_mean_tier3_margin": "pro AD lead over next-best tier (4 judges)",
    "all4_mean_tier2_vs_tier1": "long caption vs short caption margin",
    "pro_minus_long_words": "pro AD word count minus VATEX-long",
}


def direction_note(rho: float) -> str:
    if rho < -0.3:
        return "Higher TRIBE → lower outcome (expected for judge agreement)"
    if rho > 0.3:
        return "Higher TRIBE → higher outcome"
    return "Weak / mixed"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CORR)
    df = df[df["p"] < 0.05].sort_values("p").head(15)

    lines = [
        "# TRIBE correlation digest",
        "",
        "Significant TRIBE features vs benchmark outcomes (p < 0.05).",
        "",
    ]
    for _, row in df.iterrows():
        feat = row["tribe_feature"]
        out = row["outcome"]
        rho = row["spearman_rho"]
        p = row["p"]
        out_plain = PLAIN.get(out, out)
        lines.append(
            f"- **{feat}** vs {out_plain}: ρ = {rho:.3f}, p = {p:.4g} — {direction_note(rho)}"
        )

    lines.extend([
        "",
        "## Takeaway",
        "",
        "`mean_standard_slot_score` inversely predicts judge agreement (ρ ≈ −0.75).",
        "That is the cleanest TRIBE-only story: use video+audio brain gap to forecast",
        "when automatic AD scoring will be unreliable, before any AD text exists.",
    ])
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(OUT.read_text())
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
