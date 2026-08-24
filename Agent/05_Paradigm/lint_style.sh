#!/usr/bin/env bash
# lint_style.sh — enforce BEEHub PsychoPy house style (see Agent/03_Paradigm/HOUSE_STYLE.md).
#
# Small models ignore prose instructions but respond well to a failing check with a concrete
# message. This makes the display conventions mechanical rather than advisory.
#
# Usage: ./Agent/03_Paradigm/lint_style.sh path/to/script.py
# Exit 0 = clean, 1 = violations found.

set -uo pipefail
FILE="${1:-}"
[[ -z "$FILE" ]] && { echo "usage: $0 <file.py>" >&2; exit 2; }
[[ ! -f "$FILE" ]] && { echo "not found: $FILE" >&2; exit 2; }

FAIL=0
note() { echo "  ❌ $1"; FAIL=1; }

echo "── house-style lint: $FILE ──"

# RULE 1: pixel units only.
if grep -nq "units\s*=\s*['\"]norm['\"]" "$FILE"; then
  note "units='norm' is forbidden. Use units=\"pix\" (HOUSE_STYLE.md rule 1)."
  grep -n "units\s*=\s*['\"]norm['\"]" "$FILE" | sed 's/^/       /'
fi
if grep -nq "units\s*=\s*['\"]height['\"]" "$FILE"; then
  note "units='height' is forbidden. Use units=\"pix\" (rule 1)."
fi
if grep -q "visual.Window" "$FILE" && ! grep -q "units\s*=\s*['\"]pix['\"]" "$FILE"; then
  note "visual.Window without units=\"pix\" (rule 1)."
fi

# RULE 2: every ImageStim needs an explicit size=.
#   Handles the common single-line case; multi-line calls are checked by the -1..1 heuristic below.
while IFS= read -r line; do
  n="${line%%:*}"
  body="${line#*:}"
  if [[ "$body" == *"ImageStim("* && "$body" != *"size="* && "$body" == *")"* ]]; then
    note "line $n: ImageStim without size= (rule 2): ${body#"${body%%[![:space:]]*}"}"
  fi
done < <(grep -n "ImageStim(" "$FILE")

# RULE 3: norm-style fractional geometry values.
if grep -nqE "(height|wrapWidth)\s*=\s*0?\.[0-9]" "$FILE"; then
  note "fractional height/wrapWidth found — these are norm units; use pixels (rule 3)."
  grep -nE "(height|wrapWidth)\s*=\s*0?\.[0-9]" "$FILE" | head -5 | sed 's/^/       /'
fi
if grep -nqE "pos\s*=\s*\(\s*-?0?\.[0-9]+\s*,|pos\s*=\s*\(\s*-?[01]\s*,\s*-?0?\.[0-9]+" "$FILE"; then
  note "fractional pos= found — positions must be in pixels (rule 3)."
  grep -nE "pos\s*=\s*\(\s*-?0?\.[0-9]+\s*,|pos\s*=\s*\(\s*-?[01]\s*,\s*-?0?\.[0-9]+" "$FILE" \
    | head -5 | sed 's/^/       /'
fi

# RULE 4: missing stimuli must raise, not warn-and-continue.
if grep -nqi "WARNING: stimulus not found" "$FILE"; then
  note "missing stimuli must raise FileNotFoundError, not print a warning (rule 4)."
fi

# RULE 5: deprecated TextStim alignment params.
#   alignHoriz/alignVert raise at runtime in current PsychoPy:
#   "`anchor_y` must be either top, bottom, center, or baseline".
if grep -vE "^\s*#" "$FILE" | grep -qE "align(Horiz|Vert)\s*=\s*['\"]"; then
  note "alignHoriz/alignVert are DEPRECATED and raise at runtime (rule 5)."
  note "  alignHoriz='X' -> alignText='X', anchorHoriz='X'   |   alignVert='Y' -> anchorVert='Y'"
  grep -nE "align(Horiz|Vert)\s*=\s*['\"]" "$FILE" | grep -vE "^\s*[0-9]+:\s*#" | head -5 | sed 's/^/       /'
fi

# RULE 6: unconverted top-left-origin (pygame) coordinates.
#   PsychoPy units="pix" has the origin at the SCREEN CENTRE. A position built
#   from win.size[N]/2 WITHOUT a subtraction is almost always a pygame coord that
#   was never converted — it renders in the corner and raises nothing.
if grep -nE "pos\s*=|\.pos\s*=" "$FILE" | grep -qE "win\.size\[[01]\]\s*/\s*2" ; then
  if ! grep -q "_px(" "$FILE"; then
    note "position built from win.size[..]/2 with no _px() conversion (rule 6)."
    note "  PsychoPy pix origin is the SCREEN CENTRE, not the top-left corner."
    note "  Add:  def _px(x, y): return (x - win.size[0]/2.0, win.size[1]/2.0 - y)"
    grep -nE "(pos\s*=|\.pos\s*=).*win\.size\[[01]\]\s*/\s*2" "$FILE" | head -5 | sed 's/^/       /'
  fi
fi

# No EEG/parallel-port code (no trigger hardware in this setup).
if grep -nq "psychopy.parallel\|ParallelPort\|setData(" "$FILE"; then
  note "parallel-port/EEG code found — there is no trigger hardware; remove it."
fi

if [[ $FAIL -eq 0 ]]; then
  echo "✅ house style OK"
  exit 0
else
  echo "Fix the above, then re-run. Reference: Agent/03_Paradigm/HOUSE_STYLE.md and Agent/03_Paradigm/template/paradigm_template.py"
  exit 1
fi
