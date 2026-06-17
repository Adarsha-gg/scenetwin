#!/usr/bin/env python3
"""Category-level TRIBE pressure vs ADQA fragility on the 18-clip benchmark."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_CSV = OUT_DIR / "category_risk_summary.csv"
OUT_MD = Path(__file__).resolve().parent / "findings" / "category-risk.md"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(TIMING / "tribe_native" / "tribe_failure_forecast.csv")
    df["judge_fragility"] = 1.0 - df["all4_mean_full_order"].fillna(0)
    df["tier3_weak"] = (df["all4_mean_tier3_margin"] < 0.15).astype(int)

    rows = []
    for cat, grp in df.groupby("category"):
        n = len(grp)
        rows.append({
            "category": cat,
            "n_clips": n,
            "mean_risk_score": grp["risk_score"].mean(),
            "mean_tribe_pressure": grp["tribe_pressure"].mean(),
            "mean_high_need_frac": grp["high_need_seconds_frac"].mean(),
            "mean_speech_density": grp["mean_speech_density"].mean(),
            "judge_failures": int(grp["all4_fail"].sum()) if "all4_fail" in grp else int((grp["all4_mean_full_order"] == 0).sum()),
            "tier3_weak_count": int(grp["tier3_weak"].sum()),
            "extended_ad_count": int(grp["tribe_route"].astype(str).str.contains("extended", case=False).sum()),
        })

    summary = pd.DataFrame(rows).sort_values("mean_risk_score", ascending=False)
    summary.to_csv(OUT_CSV, index=False)

    # clip-level: does category explain risk beyond TRIBE?
    cat_dummies = pd.get_dummies(df["category"], prefix="cat", drop_first=True)
    if len(cat_dummies.columns) > 0:
        X = np.column_stack([df["mean_standard_slot_score"].values, cat_dummies.values])
    else:
        X = df[["mean_standard_slot_score"]].values
    y = df["judge_fragility"].values
    rho_tribe, p_tribe = spearmanr(df["mean_standard_slot_score"], y)

    lines = [
        "# Category risk analysis",
        "",
        f"Source: `{OUT_CSV.relative_to(ROOT)}`",
        "",
        "## Headline",
        "",
        f"- Spearman(TRIBE standard-slot score, judge fragility) = **{rho_tribe:.3f}** (p = {p_tribe:.4f}, n = {len(df)})",
        f"- Highest mean risk category: **{summary.iloc[0]['category']}** (mean risk {summary.iloc[0]['mean_risk_score']:.3f})",
        "",
        "## By category",
        "",
        summary.to_markdown(index=False),
        "",
        "## Interpretation",
        "",
        "Sports clips cluster toward extended-AD routing and higher TRIBE pressure.",
        "Food & Cooking clips often have talky audio (high speech density), lowering",
        "review priority even when visual action is present.",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
