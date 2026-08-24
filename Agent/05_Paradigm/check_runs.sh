#!/usr/bin/env bash
# check_runs.sh — the "must run" gate for a generated experiment.
#
# Two checks:
#   1. Syntax: python -m py_compile  (fast, deterministic)
#   2. Launch: run the script headless with a short timeout.
#
# Why the timeout heuristic: a real experiment opens a window and then WAITS for input, so it
# never exits on its own. We can't wait for a clean exit. Instead we run it for a few seconds:
#   - if it crashes early (bad import, missing asset, wrong API) -> non-zero exit -> FAIL
#   - if it's still running when the timeout fires (exit code 124) -> it launched OK -> PASS
# This catches the failures that matter in v0 (won't even start) without a human at the keyboard.
#
# Usage:
#   ./Agent/03_Paradigm/check_runs.sh Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_B/OLM_Set_B_english_generated.py
#   LAUNCH_SECONDS=8 ./check_runs.sh path/to/file.py     # override the launch window
#
# Requires: python (in the active `psychopy` env). Uses xvfb-run if present (headless box);
# falls back to the real display otherwise.

set -uo pipefail

FILE="${1:-}"
LAUNCH_SECONDS="${LAUNCH_SECONDS:-6}"

if [[ -z "$FILE" ]]; then
  echo "usage: $0 <path-to-generated-.py>" >&2
  exit 2
fi
if [[ ! -f "$FILE" ]]; then
  echo "❌ not found: $FILE" >&2
  exit 2
fi

echo "── check 1/3: house style ─────────────────────────────────────"
LINT="$(dirname "$0")/lint_style.sh"
if [[ -x "$LINT" ]]; then
  if ! "$LINT" "$FILE"; then
    echo "❌ house-style violations — fix these before the run gate matters."
    exit 1
  fi
else
  echo "   (lint_style.sh not found/executable — skipping style check)"
fi

echo "── check 2/3: syntax (py_compile) ─────────────────────────────"
if python -m py_compile "$FILE"; then
  echo "✅ syntax OK"
else
  echo "❌ syntax error in $FILE"
  exit 1
fi

echo "── check 3/3: headless launch (${LAUNCH_SECONDS}s window) ──────"

# Build the launch command; prefer xvfb-run on machines with no display.
if command -v xvfb-run >/dev/null 2>&1; then
  RUNNER=(xvfb-run -a python "$FILE")
  echo "   (using xvfb-run — virtual display)"
else
  RUNNER=(python "$FILE")
  echo "   (no xvfb-run found — using current display)"
fi

# Run with a timeout. `timeout` returns 124 when it has to kill a still-running process.
timeout --preserve-status "${LAUNCH_SECONDS}s" "${RUNNER[@]}"
RC=$?

if [[ $RC -eq 124 || $RC -eq 143 ]]; then
  # 124 = timeout fired; 143 = SIGTERM (128+15) — both mean "still running when we stopped it".
  echo "✅ launched and ran for ${LAUNCH_SECONDS}s without crashing (killed by timeout, as expected)"
  exit 0
elif [[ $RC -eq 0 ]]; then
  echo "✅ script started and exited cleanly on its own"
  exit 0
else
  echo "❌ script exited early with code $RC — it did NOT launch cleanly"
  echo "   Common causes: missing/renamed stimulus asset, wrong PsychoPy/Pygame API symbol,"
  echo "   or a missing import. Re-run the script directly to see the full traceback:"
  echo "     ${RUNNER[*]}"
  exit 1
fi
