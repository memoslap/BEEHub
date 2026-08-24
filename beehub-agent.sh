#!/usr/bin/env bash
# beehub-agent — launch a BEEHub agent.
#
#   ./beehub-agent                 list agents
#   ./beehub-agent 03              by number
#   ./beehub-agent paradigm        by name
#   ./beehub-agent --status        what's active
#
# The launcher knows NOTHING about any specific agent. Roles are discovered by scanning
# Agent/*/CLAUDE.md, so adding or renaming an agent needs no edit here. Anything an agent
# needs (a conda env, a prerequisite file) it declares itself in Agent/<folder>/agent.env.
#
# WHY IT EXISTS: Claude Code auto-loads a file named exactly CLAUDE.md, walking up from the
# working directory. A CLAUDE.md inside Agent/<folder>/ loads only on demand — too late to
# govern a session. So we symlink the chosen one to ./CLAUDE.md and launch from the root:
# correct working directory, exactly one instruction set loaded.

set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT" || exit 2

# ── Discover agents: any Agent/*/CLAUDE.md is a role ────────────────────────
declare -a KEYS=() PATHS=() LABELS=()
for f in Agent/*/CLAUDE.md; do
  [[ -f "$f" ]] || continue
  dir="$(basename "$(dirname "$f")")"        # e.g. 03_Paradigm
  num="${dir%%_*}"                            # 03   (or the whole name if unnumbered)
  name="${dir#*_}"                            # Paradigm
  key="$(echo "$name" | tr '[:upper:]' '[:lower:]')"
  KEYS+=("$key"); PATHS+=("$f"); LABELS+=("$dir")
done
# Any Agent/<dir> holding .md files but NO CLAUDE.md is almost certainly a role
# whose instruction file is misnamed — the single most common setup mistake here.
declare -a ORPHANS=()
for d in Agent/*/; do
  [[ -d "$d" ]] || continue
  [[ -f "${d}CLAUDE.md" ]] && continue
  compgen -G "${d}*.md" > /dev/null || continue
  ORPHANS+=("$(basename "$d")")
done

[[ ${#KEYS[@]} -eq 0 ]] && { echo "no agents found (expected Agent/*/CLAUDE.md)" >&2; exit 2; }

# Resolve a user argument to an index: match number prefix, full folder, or name substring.
resolve() {
  local q; q="$(echo "$1" | tr '[:upper:]' '[:lower:]')"
  local i
  for i in "${!KEYS[@]}"; do
    local lab="${LABELS[$i]}" low
    low="$(echo "$lab" | tr '[:upper:]' '[:lower:]')"
    [[ "${lab%%_*}" == "$1" || "$low" == "$q" || "${KEYS[$i]}" == "$q" ]] && { echo "$i"; return 0; }
  done
  for i in "${!KEYS[@]}"; do                   # fall back to substring
    [[ "${KEYS[$i]}" == *"$q"* ]] && { echo "$i"; return 0; }
  done
  return 1
}

list_agents() {
  local active=""; [[ -L CLAUDE.md ]] && active="$(readlink CLAUDE.md)"
  local i
  for i in "${!KEYS[@]}"; do
    local mark="  "; [[ "${PATHS[$i]}" == "$active" ]] && mark="→ "
    printf "%s%-30s %-28s (%s lines)\n" "$mark" "${LABELS[$i]}" "${KEYS[$i]}" "$(wc -l < "${PATHS[$i]}")"
  done
  if [[ ${#ORPHANS[@]} -gt 0 ]]; then
    echo
    for o in "${ORPHANS[@]}"; do
      echo "  ⚠️  ${o} has .md files but no CLAUDE.md — NOT loadable."
      local first; first="$(basename "$(ls "Agent/${o}"/*.md 2>/dev/null | head -1)")"
      [[ -n "$first" ]] && echo "      fix:  mv \"Agent/${o}/${first}\" \"Agent/${o}/CLAUDE.md\""
    done
  fi
}

show_status() {
  if [[ -L CLAUDE.md ]]; then
    echo "active : $(readlink CLAUDE.md)"
    [[ -e CLAUDE.md ]] || echo "         ⚠️  DANGLING — target does not exist"
  elif [[ -f CLAUDE.md ]]; then
    echo "active : CLAUDE.md is a regular file (not managed here)"
  else
    echo "active : none"
  fi
  echo; echo "agents:"; list_agents
}

case "${1:-}" in
  --status|-s) show_status; exit 0 ;;
  "")          echo "usage: $0 <agent>   (number, folder, or name)"; echo; list_agents; exit 0 ;;
  --help|-h)   echo "usage: $0 [--status] <agent>"; echo; list_agents; exit 0 ;;
esac

IDX="$(resolve "$1")" || { echo "❌ unknown agent '$1'" >&2; echo >&2; list_agents >&2; exit 2; }
TARGET="${PATHS[$IDX]}"; LABEL="${LABELS[$IDX]}"; DIR="$(dirname "$TARGET")"

if [[ -e CLAUDE.md && ! -L CLAUDE.md ]]; then
  echo "❌ CLAUDE.md exists as a regular file — move it aside first." >&2; exit 2
fi

ln -sfn "$TARGET" CLAUDE.md
echo "✅ ${LABEL}  →  ${TARGET}"

LINES=$(wc -l < "$TARGET")
[[ "$LINES" -gt 200 ]] && echo "⚠️  ${LINES} lines — over the ~200-line guidance; adherence may suffer."

# ── Per-agent requirements, declared by the agent itself ────────────────────
# Agent/<folder>/agent.env may set:
#   REQUIRED_CONDA_ENV="psychopy"          warn if a different env is active
#   REQUIRED_GLOB="Projects/*/*_description.json"   warn if nothing matches
#   NOTE="free text shown at launch"
if [[ -f "$DIR/agent.env" ]]; then
  # shellcheck disable=SC1090
  source "$DIR/agent.env"
  if [[ -n "${REQUIRED_CONDA_ENV:-}" && "${CONDA_DEFAULT_ENV:-}" != "$REQUIRED_CONDA_ENV" ]]; then
    echo "⚠️  conda env is '${CONDA_DEFAULT_ENV:-none}', this agent expects '${REQUIRED_CONDA_ENV}'."
    echo "    mamba activate ${REQUIRED_CONDA_ENV}   then relaunch."
  fi
  if [[ -n "${REQUIRED_GLOB:-}" ]]; then
    # shellcheck disable=SC2086
    if ! compgen -G $REQUIRED_GLOB > /dev/null; then
      echo "⚠️  expected something matching '${REQUIRED_GLOB}' — not found."
    fi
  fi
  [[ -n "${NOTE:-}" ]] && echo "ℹ️  ${NOTE}"
fi

echo
exec claude "${@:2}"
