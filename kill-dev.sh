#!/bin/bash
# ── Kill EAGLE dev zombies ────────────────────────────────────────
# Finds and kills anything on ports 8000 (backend) and 3000 (frontend).
# Safe to run anytime — idempotent.
#
# Usage:  ./kill-dev.sh
#         ./kill-dev.sh 8000       # kill only port 8000
#         ./kill-dev.sh 8000 3000  # explicit ports
# ──────────────────────────────────────────────────────────────────

PORTS="${@:-8000 3000}"
killed=0

for port in $PORTS; do
  pids=$(netstat -ano 2>/dev/null | grep ":${port}" | grep LISTENING | awk '{print $5}' | sort -u | grep -v '^0$' || true)
  if [ -n "$pids" ]; then
    for pid in $pids; do
      echo "Killing PID $pid on port $port"
      taskkill //F //PID "$pid" 2>/dev/null && killed=$((killed + 1)) || true
    done
  fi
done

# Clean up PID files
rm -f "$(dirname "$0")/server/.uvicorn.pid"

if [ "$killed" -eq 0 ]; then
  echo "No zombie processes found on ports: $PORTS"
else
  echo "Killed $killed process(es)"
fi
