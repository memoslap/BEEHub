#!/usr/bin/env bash
# project_notes.sh — per-project facts, kept out of the agents' CLAUDE.md files.
#
#   ./project_notes.sh new MT        create Agent/notes/MT.md from the template
#   ./project_notes.sh check MT      exit 1 if any question is still unanswered
#   ./project_notes.sh list          show every project and its status
#
# WHY: CLAUDE.md files load in full at every session start and compete for a 32k
# context. Project facts do not belong there — with 20 projects no CLAUDE.md could
# hold them. They live in Agent/notes/<CODE>.md and are read on demand, by code.
#
# An unanswered question is the literal string ?? — `check` fails while any remain,
# so an agent cannot proceed on assumptions the human never confirmed.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
while [[ ! -d "$ROOT/Agent" && "$ROOT" != "/" ]]; do ROOT="$(dirname "$ROOT")"; done
cd "$ROOT" || { echo "❌ repo root not found" >&2; exit 2; }

NOTES_DIR="Agent/notes"
TEMPLATE="$NOTES_DIR/_TEMPLATE.md"
CMD="${1:-}"; CODE="${2:-}"

usage() { sed -n '3,6p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'; exit 2; }

case "$CMD" in
  new)
    [[ -z "$CODE" ]] && usage
    [[ -f "$TEMPLATE" ]] || { echo "❌ missing $TEMPLATE" >&2; exit 2; }
    mkdir -p "$NOTES_DIR"
    DEST="$NOTES_DIR/${CODE}.md"
    [[ -e "$DEST" ]] && { echo "❌ $DEST already exists — edit it, don't overwrite." >&2; exit 2; }
    sed "s/<CODE>/$CODE/g" "$TEMPLATE" > "$DEST"
    echo "✅ created $DEST"
    echo
    echo "Answer every ?? before running an agent on this project:"
    grep -n '??' "$DEST" | sed 's/^/   /'
    ;;

  check)
    [[ -z "$CODE" ]] && usage
    DEST="$NOTES_DIR/${CODE}.md"
    if [[ ! -f "$DEST" ]]; then
      echo "❌ no notes for $CODE."
      echo "   Run: ./project_notes.sh new $CODE   then answer the questions."
      exit 1
    fi
    OPEN=$(grep -c '??' "$DEST" 2>/dev/null); OPEN=${OPEN:-0}
    if [[ "$OPEN" -gt 0 ]]; then
      echo "❌ $DEST has $OPEN unanswered question(s):"
      grep -n '??' "$DEST" | sed 's/^/   /'
      echo
      echo "   ASK THE HUMAN THESE QUESTIONS. Do not answer them yourself."
      exit 1
    fi
    echo "✅ $DEST — all questions answered."
    ;;

  list)
    mkdir -p "$NOTES_DIR"
    found=0
    for f in "$NOTES_DIR"/*.md; do
      [[ -f "$f" ]] || continue
      b="$(basename "$f" .md)"; [[ "$b" == "_TEMPLATE" ]] && continue
      found=1
      n=$(grep -c '??' "$f" 2>/dev/null); n=${n:-0}
      if [[ "$n" -gt 0 ]]; then printf "  ⚠️  %-8s %s open question(s)\n" "$b" "$n"
      else printf "  ✅ %-8s ready\n" "$b"; fi
    done
    [[ $found -eq 0 ]] && echo "  (no project notes yet — ./project_notes.sh new <CODE>)"
    ;;

  *) usage ;;
esac
