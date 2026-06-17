#!/usr/bin/env python3
"""Verify SceneTwin cached benchmark assets and Python deps."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMING = ROOT / "output" / "scenetwin_timing_20clip"

REQUIRED_CSV = [
    TIMING / "ensemble" / "adqa_clip_ensemble_scores.csv",
    TIMING / "ensemble" / "adqa_clip_ensemble_results.csv",
    TIMING / "tribe_native" / "tribe_failure_forecast.csv",
    TIMING / "tribe_native" / "tribe_native_correlations.csv",
    TIMING / "need" / "neural_description_need_curve.csv",
    TIMING / "need" / "coarse_need_windows.csv",
]

REQUIRED_CHARTS = [
    ROOT / "output" / "charts" / "scenetwin_failure_forecast.png",
    ROOT / "output" / "charts" / "scenetwin_per_tier_heatmap.png",
    ROOT / "output" / "charts" / "scenetwin_brain_three_panel.png",
]

OPTIONAL_MODULES = ["pandas", "numpy", "scipy", "sklearn", "fastapi"]


def main() -> int:
    ok = True
    print("SceneTwin health check\n" + "=" * 40)

    for path in REQUIRED_CSV:
        status = "OK" if path.exists() else "MISSING"
        if status == "MISSING":
            ok = False
        print(f"  [{status}] {path.relative_to(ROOT)}")

    for path in REQUIRED_CHARTS:
        status = "OK" if path.exists() else "MISSING"
        if status == "MISSING":
            ok = False
        print(f"  [{status}] {path.relative_to(ROOT)}")

    print("\nPython modules:")
    for mod in OPTIONAL_MODULES:
        try:
            importlib.import_module(mod)
            print(f"  [OK] {mod}")
        except ImportError:
            print(f"  [MISSING] {mod}")
            ok = False

    clip_count = 0
    forecast = TIMING / "tribe_native" / "tribe_failure_forecast.csv"
    if forecast.exists():
        import pandas as pd
        clip_count = len(pd.read_csv(forecast))
    print(f"\nBenchmark clips in forecast CSV: {clip_count}")

    print("\n" + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
