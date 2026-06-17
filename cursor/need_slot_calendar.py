#!/usr/bin/env python3
"""Per-clip AD slot calendar from TRIBE need curves + coarse windows."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NEED = ROOT / "output" / "scenetwin_timing_20clip" / "need"
OUT_DIR = Path(__file__).resolve().parent / "output"
OUT_CSV = OUT_DIR / "need_slot_calendar.csv"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    coarse = pd.read_csv(NEED / "coarse_need_windows.csv")
    forecast = pd.read_csv(
        ROOT / "output" / "scenetwin_timing_20clip" / "tribe_native" / "tribe_failure_forecast.csv",
        usecols=["clip_idx", "category", "tribe_route", "risk_rank"],
    )

    # Non-low windows only
    actionable = coarse[~coarse["recommendation"].astype(str).str.contains("low_ad_need", case=False)].copy()
    actionable = actionable.merge(forecast, on="clip_idx", how="left")
    actionable["slot_label"] = actionable["recommendation"].str.replace("_", " ", regex=False)
    actionable = actionable.sort_values(["risk_rank", "clip_idx", "start_s"])

    cols = [
        "clip_idx", "category", "risk_rank", "tribe_route",
        "start_s", "end_s", "need_score", "speech_density", "slot_label",
    ]
    actionable[cols].to_csv(OUT_CSV, index=False)

    print(f"Actionable AD windows: {len(actionable)} across {actionable['clip_idx'].nunique()} clips")
    print(actionable.groupby("slot_label").size().to_string())
    print(f"\nWrote {OUT_CSV}")

    # Top-risk clip sample
    top = actionable[actionable["risk_rank"] <= 3].head(8)
    if not top.empty:
        print("\nSample slots for top-3 risk clips:")
        print(top[cols].to_string(index=False))


if __name__ == "__main__":
    main()
