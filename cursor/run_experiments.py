#!/usr/bin/env python3
"""Run all cursor/ offline experiments; optional loop mode."""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CURSOR = Path(__file__).resolve().parent
ROOT = CURSOR.parent

SCRIPTS = [
    "health_check.py",
    "export_static_api.py",
    "category_risk_analysis.py",
    "combined_review_priority.py",
    "ensemble_validation.py",
    "tribe_correlation_digest.py",
    "need_slot_calendar.py",
    "build_insights_html.py",
    "label_audit.py",
    "efficiency_proxy_sweep.py",
    "motion_static_adqa_split.py",
    "tribe_counterfactual_audit.py",
    "critical_weighted_ensemble_test.py",
    "tribe_live_proxy_spec.py",
]

LOG = CURSOR / "findings" / "experiment-log.md"


def run_once() -> bool:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [f"\n## Run {stamp}\n"]
    all_ok = True

    for name in SCRIPTS:
        path = CURSOR / name
        print(f"\n{'='*50}\n>>> {name}\n{'='*50}")
        rc = subprocess.call([sys.executable, str(path)], cwd=str(ROOT))
        status = "ok" if rc == 0 else f"FAIL (exit {rc})"
        lines.append(f"- `{name}`: {status}")
        if rc != 0:
            all_ok = False

    with LOG.open("a", encoding="utf-8") as f:
        f.writelines(line + "\n" for line in lines)

    # Also invoke upstream tools when venv has deps
    upstream = [
        ROOT / "tools" / "scenetwin_tribe_failure_forecast.py",
        ROOT / "tools" / "scenetwin_bias_reduction_analysis.py",
    ]
    for tool in upstream:
        if tool.exists():
            print(f"\n{'='*50}\n>>> {tool.name}\n{'='*50}")
            rc = subprocess.call([sys.executable, str(tool)], cwd=str(ROOT))
            lines.append(f"- `tools/{tool.name}`: {'ok' if rc == 0 else f'FAIL ({rc})'}")
            if rc != 0:
                all_ok = False

    print(f"\n{'PASS' if all_ok else 'PARTIAL'} — log appended to {LOG}")
    return all_ok


def main() -> None:
    parser = argparse.ArgumentParser(description="SceneTwin cursor experiment runner")
    parser.add_argument("--loop", action="store_true", help="Repeat every 90 seconds")
    parser.add_argument("--interval", type=int, default=90, help="Loop interval seconds")
    args = parser.parse_args()

    if not args.loop:
        ok = run_once()
        sys.exit(0 if ok else 1)

    print(f"Loop mode: every {args.interval}s (Ctrl+C to stop)")
    iteration = 0
    while True:
        iteration += 1
        print(f"\n{'#'*60}\n# Iteration {iteration}\n{'#'*60}")
        run_once()
        print(f"Sleeping {args.interval}s…")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
