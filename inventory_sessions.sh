#!/usr/bin/env bash
# inventory_sessions.sh — count participants and sessions. Deterministically.
#
#   ./inventory_sessions.sh "Convert/MouseTracking Data/Raw Data"
#   ./inventory_sessions.sh Projects/MT/bids_data
#
# WHY THIS EXISTS
# A model asked "how many sessions does each participant have?" will pattern-complete
# the plausible design ("26 participants x 2 sessions") instead of counting. That is not
# a wording problem, it is a counting problem — so counting is done here, by awk, and the
# agent is required to quote this output instead of asserting anything itself.
#
# Recognises two filename patterns:
#   raw    12b_go_nogo_dm_2025-05-14_16h31.40.550.csv   -> participant 12, session b
#   bids   sub-012_ses-02_task-gonogo_beh.tsv           -> participant 012, session 02
#
# Exit codes: 0 = every participant has the same session set
#             1 = at least one participant is incomplete  <- NOT an error, a FINDING
#             2 = usage / nothing recognised

set -uo pipefail

DIR="${1:-}"
[[ -z "$DIR" ]] && { echo "usage: $0 <directory>" >&2; exit 2; }
[[ -d "$DIR" ]] || { echo "not a directory: $DIR" >&2; exit 2; }

# ── Extract (participant, session) pairs ───────────────────────────────────
# One line per data file. Sidecars (.json) are ignored so they can't inflate counts.
PAIRS=$(find "$DIR" -type f \( -name '*.csv' -o -name '*.tsv' -o -name '*.log' \) -printf '%f\n' 2>/dev/null \
  | sed -E '
      s/^sub-0*([0-9]+)_ses-0*([0-9]+).*/\1 \2/;      t
      s/^0*([0-9]+)([a-zA-Z])_.*/\1 \2/;              t
      d
    ' | sort -u)

[[ -z "$PAIRS" ]] && { echo "❌ no participant/session pattern recognised in $DIR" >&2; exit 2; }

echo "── session inventory: $DIR"
echo

echo "$PAIRS" | awk '
{ sess[$1] = sess[$1] $2 " "; n++; all[$2]=1 }
END {
  # Which session set is the norm?
  for (p in sess) { setcount[sess[p]]++ }
  best=""; bestn=0
  for (s in setcount) if (setcount[s] > bestn) { bestn=setcount[s]; best=s }

  np=0; for (p in sess) np++
  printf "participants : %d\n", np
  printf "data files    : %d\n", n
  printf "session sets  : "
  for (s in setcount) printf "[%s]x%d  ", s, setcount[s]
  printf "\n\n"

  # List every participant that deviates from the norm.
  bad=0
  for (p in sess) if (sess[p] != best) {
    printf "  ⚠️  participant %-4s has [%s] — expected [%s]\n", p, sess[p], best
    bad++
  }
  if (bad == 0) {
    printf "  ✅ all %d participants have the same sessions [%s]\n", np, best
  } else {
    printf "\n  %d of %d participants are INCOMPLETE.\n", bad, np
    printf "  Report this. Do not average over it. Do not invent a placeholder session.\n"
  }
  exit (bad > 0)
}
'
RC=$?

echo
echo "── quote these numbers verbatim; do not restate them from memory ──"
exit $RC
