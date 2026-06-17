#!/usr/bin/env python3
"""Loop worker v7 — metric discovery every tick, no repeat experiments."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CURSOR = Path(__file__).resolve().parent
ROOT = CURSOR.parent
METRICS = CURSOR / "metrics"
STATE = CURSOR / ".loop.state.json"
STATUS = CURSOR / "loop-status.json"
HEARTBEAT = CURSOR / "loop-heartbeat.txt"
DISCOVERIES = CURSOR / "findings" / "auto-discoveries.md"

# Only run discovery + rare one-offs. NO leaderboard/bootstrap/paper reruns.
DISCOVERY_SCRIPTS = [
    "discovery_engine.py",
    "novel_research_metrics.py",  # only refreshes definitions, registry dedupes repeats
]

# Every N ticks: one external data action (not re-scoring benchmark)
RARE_SCRIPTS = [
    (15, CURSOR / "fundamentals" / "acquire_external_clip.py", ["--index"], "clips_acquired"),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_state() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"iteration": 0, "clips_acquired": 0}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_script(path: Path, args: list[str] | None = None, timeout: int = 900) -> dict:
    cmd = [sys.executable, str(path), *(args or [])]
    t0 = time.time()
    try:
        rc = subprocess.call(cmd, cwd=str(ROOT), timeout=timeout)
        return {"ok": rc == 0, "seconds": round(time.time() - t0, 1), "script": path.name}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "script": path.name}
    except Exception as e:
        return {"ok": False, "error": str(e), "script": path.name}


def run_iteration(iteration: int, state: dict) -> dict:
    t0 = time.time()
    results = []

    # Primary: always discovery engine (invents new metrics)
    primary = "discovery_engine.py"
    print(f"\n>>> DISCOVERY {primary}")
    r = run_script(METRICS / primary, timeout=600)
    results.append({"track": "discovery", "name": primary, **r})

    # Secondary: novel metrics catalog refresh every 5th tick (static defs, not combinatorial)
    if iteration % 5 == 0:
        sec = "novel_research_metrics.py"
        print(f"\n>>> METRICS refresh {sec}")
        r2 = run_script(METRICS / sec, timeout=300)
        results.append({"track": "metrics", "name": sec, **r2})

    # Rare: acquire external clip (data only)
    for mod, path, arg_base, state_key in RARE_SCRIPTS:
        if iteration % mod == 0 and path.exists():
            idx = state.get(state_key, 0)
            print(f"\n>>> RARE acquire clip #{idx}")
            ra = run_script(path, [arg_base[0], str(idx)], timeout=600)
            results.append({"track": "acquire", "name": "external_clip", **ra})
            if ra.get("ok"):
                state[state_key] = idx + 1

    ok = sum(1 for x in results if x.get("ok"))
    payload = {
        "iteration": iteration,
        "mode": "discovery_v7",
        "primary": primary,
        "finished": utc_now(),
        "duration_s": round(time.time() - t0, 1),
        "tasks_ok": ok,
        "tasks_total": len(results),
        "clips_acquired": state.get("clips_acquired", 0),
        "total_discovered": json.loads((METRICS / ".discovery.state.json").read_text())["total_discovered"]
        if (METRICS / ".discovery.state.json").exists() else 0,
        "results": results,
    }
    STATUS.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    HEARTBEAT.write_text(
        f"iteration={iteration}\nmode=discovery_v7\nprimary={primary}\n"
        f"discovered={payload['total_discovered']}\nclips={state.get('clips_acquired', 0)}\n"
        f"ok={ok}/{len(results)}\nfinished={payload['finished']}\n",
        encoding="utf-8",
    )
    print(f"\nDONE iter {iteration}: {ok}/{len(results)} | discovery")
    return payload


def main() -> None:
    state = load_state()
    state["iteration"] = int(state.get("iteration", 0)) + 1
    iteration = state["iteration"]
    save_state(state)
    payload = run_iteration(iteration, state)
    save_state(state)
    sys.exit(0 if payload["tasks_ok"] > 0 else 1)


if __name__ == "__main__":
    main()
