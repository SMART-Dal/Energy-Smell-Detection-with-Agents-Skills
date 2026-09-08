
#!/usr/bin/env bash
# The body of the taxonomy batch, run inside tmux by run_next.sh.
#
# Preflight and the suite run sequentially in this one shell, deliberately:
# every process on this host reads the same package energy counter, so two
# measurements at once corrupt each other and nothing in the output says so.
set -uo pipefail
cd "$(dirname "$0")/.."

PY="$PWD/.venv/bin/python"
[ -x "$PY" ] || PY=python3

mkdir -p validation/results
LOG=validation/results/taxonomy.log

{
  echo "=== started $(date -Is) on $(hostname) ==="
  "$PY" --version
  echo

  if [ "${SKIP_PREFLIGHT:-0}" = "1" ]; then
    echo "SKIP_PREFLIGHT=1: preflight not re-run. Only set this when it passed"
    echo "on this host minutes ago and nothing has changed since."
  elif ! "$PY" validation/preflight.py; then
    echo
    echo "=== PREFLIGHT FAILED -- nothing measured ==="
    echo "The host could not resolve a known effect. Numbers taken now would"
    echo "be unresolvable rather than wrong, which is worse. Investigate what"
    echo "else is running before starting the suite."
    exit 1
  fi

  echo
  echo "=== preflight passed, starting the suite $(date -Is) ==="
  "$PY" validation/run.py taxonomy
  status=$?

  echo
  echo "=== ALL BATCHES FINISHED $(date -Is) (exit $status) ==="
  echo "Rows written: $(wc -l < validation/results/taxonomy.jsonl 2>/dev/null || echo 0)"
} 2>&1 | tee -a "$LOG"
