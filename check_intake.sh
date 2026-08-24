#!/usr/bin/env bash
# check_intake.sh — is there anything new in Convert/ waiting to be integrated?
#
#   ./check_intake.sh            report on every unhandled drop
#   ./check_intake.sh --quiet    print nothing unless there IS something to do
#                                (use this one from .bashrc / cron / motd)
#   ./check_intake.sh --all      include drops already marked done
#
# NO MODEL. This only looks and prints. It never renames, moves, deletes, or launches
# an agent — deciding what to do with a dataset is the human's job, and doing it is the
# restructure agent's job. This just makes sure a new drop doesn't sit unnoticed.
#
# A drop is "handled" when Convert/<drop>/.beehub_done exists. Mark one yourself with:
#   touch "Convert/<drop>/.beehub_done"
#
# Exit codes:  0 = nothing to do   1 = at least one unhandled drop   2 = usage/setup error

set -uo pipefail

# ── Anchor to the repo root, however we were invoked ────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# If the script lives in a subfolder, walk up to the dir that holds Convert/.
while [[ ! -d "$ROOT/Convert" && "$ROOT" != "/" ]]; do ROOT="$(dirname "$ROOT")"; done
cd "$ROOT" 2>/dev/null || { echo "❌ cannot cd to repo root" >&2; exit 2; }
[[ -d Convert ]] || { echo "❌ no Convert/ directory found (looked up from $(dirname "${BASH_SOURCE[0]}"))" >&2; exit 2; }

QUIET=0; SHOW_ALL=0
for arg in "$@"; do
  case "$arg" in
    --quiet|-q) QUIET=1 ;;
    --all|-a)   SHOW_ALL=1 ;;
    --help|-h)  sed -n '2,12p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

# ── Collect unhandled drops ────────────────────────────────────────────────
declare -a DROPS=()
for d in Convert/*/; do
  [[ -d "$d" ]] || continue                      # no drops at all -> glob stays literal
  if [[ -f "${d}.beehub_done" && $SHOW_ALL -eq 0 ]]; then continue; fi
  DROPS+=("${d%/}")
done

if [[ ${#DROPS[@]} -eq 0 ]]; then
  [[ $QUIET -eq 0 ]] && echo "✅ Convert/ — nothing new."
  exit 0
fi

# ── Report ─────────────────────────────────────────────────────────────────
echo
echo "📦 ${#DROPS[@]} unhandled drop(s) in Convert/"
echo

for drop in "${DROPS[@]}"; do
  name="$(basename "$drop")"
  done_marker=""
  [[ -f "$drop/.beehub_done" ]] && done_marker="   (marked done)"

  # Cheap inventory. -maxdepth keeps this fast on big trees; we never read file CONTENTS.
  files=$(find "$drop" -type f -not -name '.beehub_done' 2>/dev/null | wc -l)
  size=$(du -sh "$drop" 2>/dev/null | cut -f1)
  subdirs=$(find "$drop" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)

  echo "── $name$done_marker"
  echo "   $files files, $size, $subdirs top-level folder(s)"

  # Top file extensions — a fast hint at what this is.
  exts=$(find "$drop" -type f -name '*.*' -printf '%f\n' 2>/dev/null \
           | sed 's/.*\.//' | tr '[:upper:]' '[:lower:]' \
           | sort | uniq -c | sort -rn | head -5 \
           | awk '{printf "%s(%s) ", $2, $1}')
  [[ -n "$exts" ]] && echo "   types: $exts"

  # Format hints — purely informational, never a decision.
  hints=""
  find "$drop" -maxdepth 3 \( -iname '*.sce' -o -iname '*.exp' \) 2>/dev/null \
    | grep -q . && hints+="Presentation paradigm; "
  find "$drop" -maxdepth 3 -iname '*.psyexp' 2>/dev/null | grep -q . && hints+="PsychoPy; "
  find "$drop" -maxdepth 3 -iname '*.log' 2>/dev/null | grep -q . && hints+="run logs present; "
  find "$drop" -maxdepth 2 -iname 'sub-*' 2>/dev/null | grep -q . && hints+="already BIDS-ish; "
  [[ -n "$hints" ]] && echo "   hints: ${hints%; }"

  # Things worth a human's eye BEFORE an agent touches them.
  warns=()
  find "$drop" -name '* *' 2>/dev/null | grep -q . && warns+=("spaces in filenames")
  find "$drop" \( -name 'Thumbs.db' -o -name 'desktop.ini' -o -name '~$*' \) 2>/dev/null \
    | grep -q . && warns+=("Thumbs.db/desktop.ini to gitignore")
  if [[ ${#warns[@]} -gt 0 ]]; then
    joined="${warns[0]}"
    for ((i = 1; i < ${#warns[@]}; i++)); do joined+="; ${warns[$i]}"; done
    echo "   ⚠️  $joined"
  fi
  echo
done

# ── What to do next ────────────────────────────────────────────────────────
cat <<'EOF'
Next step — restructure runs first (it needs only the raw drop + the project code):

    ./beehub-agent 01          # 01_Renaming_Restructure

Then: 02 describe → [review the JSON] → 03 paradigm → 04 check

When a drop is fully integrated, mark it so this stops reporting it:

    touch "Convert/<drop>/.beehub_done"

EOF

exit 1
