#!/usr/bin/env bash
# Watchdog: restart run_loop.sh if dead; log heartbeat age.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INTERVAL="${CURSOR_GUARD_INTERVAL:-600}"
LOOP="$ROOT/cursor/run_loop.sh"
LOG="$ROOT/cursor/findings/loop-guard.log"
PIDFILE="$ROOT/cursor/.loop.pid"
HEARTBEAT="$ROOT/cursor/loop-heartbeat.txt"

mkdir -p "$(dirname "$LOG")"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

is_loop_running() {
  if [[ -f "$PIDFILE" ]]; then
    local pid
    pid="$(cat "$PIDFILE" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  pgrep -f "cursor/run_loop.sh" >/dev/null 2>&1
}

start_loop() {
  if [[ -f "$ROOT/cursor/STOP" ]]; then
    log "STOP present — not starting"
    return 1
  fi
  log "Starting run_loop.sh"
  nohup env CURSOR_LOOP_INTERVAL="${CURSOR_LOOP_INTERVAL:-600}" "$LOOP" >>"$LOG" 2>&1 &
  echo $! >"$PIDFILE"
  log "Loop PID $(cat "$PIDFILE")"
}

log "Guard START interval=${INTERVAL}s"

while [[ ! -f "$ROOT/cursor/STOP" ]]; do
  if is_loop_running; then
    if [[ -f "$HEARTBEAT" ]]; then
      log "OK loop running | $(head -3 "$HEARTBEAT" | tr '\n' ' ')"
    else
      log "OK loop running (no heartbeat yet)"
    fi
  else
    log "WARN loop dead — restarting"
    start_loop || true
  fi
  sleep "$INTERVAL"
done

log "Guard STOP"
