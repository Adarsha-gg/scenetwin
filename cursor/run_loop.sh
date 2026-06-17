#!/usr/bin/env bash
# SceneTwin cursor loop — each tick runs loop_worker.py (real rotating experiments).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
INTERVAL="${CURSOR_LOOP_INTERVAL:-600}"
PIDFILE="$ROOT/cursor/.loop.pid"
LOG="$ROOT/cursor/findings/loop-tick.log"

if [[ -f "$ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT/.venv/bin/activate"
fi

mkdir -p "$(dirname "$LOG")"
echo $$ >"$PIDFILE"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

log "SceneTwin loop START pid=$$ interval=${INTERVAL}s"
log "Watch: cursor/loop-heartbeat.txt cursor/loop-status.json cursor/findings/auto-discoveries.md"

while [[ ! -f "$ROOT/cursor/STOP" ]]; do
  log "TICK — running loop_worker.py"
  if python3 "$ROOT/cursor/loop_worker.py" >>"$LOG" 2>&1; then
    log "TICK ok"
  else
    log "TICK partial/fail (see loop-status.json)"
  fi
  log "Sleep ${INTERVAL}s"
  sleep "$INTERVAL"
done

rm -f "$PIDFILE"
log "STOP file — exiting"
