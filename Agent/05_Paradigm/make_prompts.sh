#!/usr/bin/env bash
# make_prompts.sh — emit the 4 conversion prompts with all paths substituted.
# Substitution happens HERE, in shell — never ask a small model to expand variables.
#
#   ./Agent/03_Paradigm/make_prompts.sh --list    # discover all paradigms/SETs, incl. short versions
#   ./Agent/03_Paradigm/make_prompts.sh --check   # verify configured paths exist
#   ./Agent/03_Paradigm/make_prompts.sh           # print all 4 prompts
#   ./Agent/03_Paradigm/make_prompts.sh 2         # print just prompt 2

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# ── Anchor to the repo root, wherever this was invoked from ─────────────────
# All paths below (Projects/..., Agent/...) are relative to the repo root, so cd there.
# Prefer git; fall back to two levels up from Agent/03_Paradigm/.
ROOT="$(git -C "$HERE" rev-parse --show-toplevel 2>/dev/null)"
[[ -z "$ROOT" || ! -d "$ROOT/Projects" ]] && ROOT="$(cd "$HERE/../.." && pwd)"
if [[ ! -d "$ROOT/Projects" ]]; then
  echo "❌ cannot locate the repo root (no Projects/ found near $HERE)" >&2
  echo "   run this from anywhere inside the BEEHub repo." >&2
  exit 2
fi
cd "$ROOT" || exit 2
ENV_FILE="$HERE/target.env"
[[ -f "$ENV_FILE" ]] || { echo "missing $ENV_FILE" >&2; exit 2; }
# shellcheck disable=SC1090
source "$ENV_FILE"
: "${OUT_BASENAME:=}"; : "${SET_PSYCHOPY:=}"
: "${DEMO_BASENAME:=}"; : "${DEMO_TITLE:=$PROJECT}"; : "${DEMO_N_REPS:=2}"
: "${DEMO_TEMPLATE:=Agent/03_Paradigm/template/paradigm_demo.html}"

# ── Discovery: what is actually in the repo? ─────────────────────────────────
list_targets() {
  echo "── available paradigms ─────────────────────────────────────────────────"
  echo
  local found=0
  for presdir in Projects/*/paradigm/presentation/*/*/; do
    [[ -d "$presdir" ]] || continue
    found=1
    local proj paradigm setname
    proj="$(echo "$presdir"    | cut -d/ -f2)"
    paradigm="$(echo "$presdir" | cut -d/ -f5)"
    setname="$(echo "$presdir"  | cut -d/ -f6)"

    local exp sce_n logs_n tag=""
    exp="$(find "$presdir" -maxdepth 1 -name '*.exp' -printf '%f\n' 2>/dev/null | head -1)"
    sce_n="$(find "$presdir/sce" -maxdepth 1 -name '*.sce' 2>/dev/null | wc -l)"
    logs_n="$(find "$presdir" -maxdepth 2 \( -iname '*.log' \) 2>/dev/null | wc -l)"
    [[ "$paradigm" == *_short ]] && tag="  [SHORT]"

    echo "  ${proj} / ${paradigm} / ${setname}${tag}"
    echo "      exp:  ${exp:-❌ none found}"
    echo "      sce:  ${sce_n} scenario file(s)"
    if [[ "$logs_n" -gt 0 ]]; then
      echo "      logs: ${logs_n} ✅ (use them as the oracle — see prompt 1)"
    else
      echo "      logs: 0 ⚠️  NO run logs — empirical questions must be answered from PCL alone"
    fi

    # matching psychopy outputs / references
    local psydir="Projects/${proj}/paradigm/psychopy/${paradigm}"
    if [[ -d "$psydir" ]]; then
      local refs
      refs="$(find "$psydir" -maxdepth 2 -name '*.py' ! -name '*_generated.py' -printf '        %P\n' 2>/dev/null | head -6)"
      if [[ -n "$refs" ]]; then
        echo "      existing psychopy references:"
        echo "$refs"
      else
        echo "      existing psychopy references: none"
      fi
    else
      echo "      psychopy dir: ❌ ${psydir} does not exist"
    fi
    echo
  done
  [[ $found -eq 0 ]] && echo "  (nothing found — are you in the repo root?)"
  echo "── set PROJECT / PARADIGM / SET_PRESENTATION / SET_PSYCHOPY in Agent/03_Paradigm/target.env ──"
  echo "   Remember: for _short paradigms SET_PSYCHOPY is usually \"\" (no subfolder)"
  echo "   and OUT_BASENAME must be set explicitly (naming differs from the full sets)."
}

# ── Derived paths ────────────────────────────────────────────────────────────
PRES_DIR="Projects/${PROJECT}/paradigm/presentation/${PARADIGM}/${SET_PRESENTATION}"
if [[ -n "$SET_PSYCHOPY" ]]; then
  PSY_DIR="Projects/${PROJECT}/paradigm/psychopy/${PARADIGM}/${SET_PSYCHOPY}"
  DEFAULT_OUT="${PROJECT}_${SET_PSYCHOPY}_${LANG}${OUT_SUFFIX}.py"
else
  PSY_DIR="Projects/${PROJECT}/paradigm/psychopy/${PARADIGM}"
  DEFAULT_OUT="${PROJECT}_${SET_PRESENTATION}_${LANG}${OUT_SUFFIX}.py"
fi
EXP_PATH="${PRES_DIR}/${EXP_FILE}"
SCE_DIR="${PRES_DIR}/sce"
STIM_DIR="${PRES_DIR}/Stimuli"
TAG="${PROJECT}_${SET_PRESENTATION}"
MANIFEST="Agent/03_Paradigm/manifests/${TAG}.yaml"
OUT_NAME="${OUT_BASENAME:-$DEFAULT_OUT}"
OUT_PATH="${PSY_DIR}/${OUT_NAME}"
IS_SHORT="no"; [[ "$PARADIGM" == *_short ]] && IS_SHORT="yes"

# ── Short-version discovery (the demo is always derived from the SHORT version) ──
SHORT_PARADIGM="${PARADIGM%_short}_short"
SHORT_PSY_DIR="Projects/${PROJECT}/paradigm/psychopy/${SHORT_PARADIGM}"
SHORT_PRES_DIR="Projects/${PROJECT}/paradigm/presentation/${SHORT_PARADIGM}"
SHORT_PY=""
if [[ -d "$SHORT_PSY_DIR" ]]; then
  SHORT_PY="$(find "$SHORT_PSY_DIR" -maxdepth 2 -name "*${LANG}*.py" ! -name '*_generated.py' 2>/dev/null | head -1)"
  [[ -z "$SHORT_PY" ]] && SHORT_PY="$(find "$SHORT_PSY_DIR" -maxdepth 2 -name '*.py' ! -name '*_generated.py' 2>/dev/null | head -1)"
fi
DEMO_NAME="${DEMO_BASENAME:-${PROJECT}_short_demo.html}"
DEMO_PATH="${SHORT_PSY_DIR}/${DEMO_NAME}"

# log availability drives the wording of prompt 1
LOG_COUNT="$(find "$PRES_DIR" -maxdepth 2 -iname '*.log' 2>/dev/null | wc -l)"

check_paths() {
  local fail=0
  echo "── verifying paths for ${TAG}${IS_SHORT:+ }$([[ $IS_SHORT == yes ]] && echo '[SHORT]') ──"
  for d in "$PRES_DIR" "$SCE_DIR" "$STIM_DIR" "$PSY_DIR"; do
    if [[ -d "$d" ]]; then echo "  ✅ $d"; else echo "  ❌ MISSING DIR  $d"; fail=1; fi
  done
  for f in "$EXP_PATH" "$REFERENCE"; do
    if [[ -f "$f" ]]; then echo "  ✅ $f"; else echo "  ❌ MISSING FILE $f"; fail=1; fi
  done
  if [[ "$LOG_COUNT" -gt 0 ]]; then
    echo "  ✅ ${LOG_COUNT} run log(s) available — usable as the empirical oracle"
  else
    echo "  ⚠️  no run logs found under ${PRES_DIR} — prompt 1 adjusted accordingly"
  fi
  [[ -e "$OUT_PATH" ]] && echo "  ⚠️  output exists (will NOT be overwritten): $OUT_PATH"
  mkdir -p "$(dirname "$MANIFEST")"
  if [[ $fail -ne 0 ]]; then
    echo
    echo "Fix Agent/03_Paradigm/target.env. Reminders:"
    echo "  • SET naming differs: SET_A→Set_A, Set1_MRI→Set_1"
    echo "  • _short paradigms have NO psychopy subfolder → SET_PSYCHOPY=\"\""
    echo "  • run ./Agent/03_Paradigm/make_prompts.sh --list to see what actually exists"
    return 1
  fi
  echo "  all paths OK   → output: ${OUT_PATH}"
  return 0
}

log_clause() {
  cat <<EOF

FIRST, before reading any PCL, run the probe and read its report:

    ./Agent/03_Paradigm/probe.sh

It writes Agent/03_Paradigm/probes/${TAG}_probe.md containing MEASURED facts from the run logs
and the Stimuli tree: trial counts, block order, unique stimuli per block, the
response-code mapping, realised durations, which stimulus files are missing from
disk, directory pollution, absolute paths needing rewrite, and where shared assets
actually live.

Treat that report as authoritative. Do NOT re-derive anything it answers, and do
NOT put anything it answers into open_questions. If the report flags missing
stimulus files, STOP and report that — do not proceed with the conversion.
EOF
}

short_clause() {
  [[ "$IS_SHORT" == "yes" ]] && cat <<EOF

This is a SHORT version of the paradigm. Do not assume it matches the full-length
version in trial counts, block structure, or stimulus sets — derive everything from
THIS paradigm's own .exp and sce/ files.
EOF
}

p1() { cat <<EOF
── PROMPT 1 — inventory, no code ──────────────────────────────────────────────
Read the ${PROJECT} ${SET_PRESENTATION} paradigm and produce an inventory manifest.
Do not write any Python yet.

Source: ${PRES_DIR}/
Read ${EXP_FILE} in full, then every scenario in sce/ that it references — the real
PCL logic lives there, especially ${KEY_SCENARIOS}. List the Stimuli/ tree so you
know which files actually exist.$(log_clause)$(short_clause)

Write ${MANIFEST} using the schema in Agent/03_Paradigm/CONVERSION_WORKFLOW.md. Every stimulus
path must be verified on disk and marked exists: true|false. Never invent a
filename — anything referenced but not found goes in unresolved: with the exact
string from the source. Durations stay in milliseconds as written. Anything
ambiguous goes in open_questions: rather than being guessed.

Then print: number of blocks, trials per block, total stimuli, and counts for
unresolved and open_questions.
EOF
}

p2() { cat <<EOF
── PROMPT 2 — generate, template-first ────────────────────────────────────────
Now generate the PsychoPy script from the approved manifest ${MANIFEST}.

Start by copying the window setup, clock, and stimulus object definitions from
${REFERENCE} verbatim. Do not rewrite or restyle them. Then replace only the trial
and block logic with what the manifest specifies.

The manifest is the source of truth for structure — if it disagrees with the
.exp/.sce, stop and tell me instead of picking one. Convert durations from ms to
seconds here, with a comment where you do it. No parallel-port code.

Write to ${OUT_PATH}
Do not overwrite any existing file. Don't run anything yet.
EOF
}

p3() { cat <<EOF
── PROMPT 3 — gate ────────────────────────────────────────────────────────────
Now run:
  ./Agent/03_Paradigm/check_runs.sh ${OUT_PATH}

It checks house style first (pixel units, explicit ImageStim sizes), then syntax,
then a headless launch. If anything fails, read the actual error, fix the real
cause, and re-run until it passes. Don't report success while it's failing. If
you're stuck after a few tries, stop and tell me what's failing and what you tried.
EOF
}

p4() { cat <<EOF
── PROMPT 4 — only if the style lint keeps failing ────────────────────────────
You're still not matching the reference. Open ${REFERENCE}, copy the window and
stimulus setup block exactly as it is, and use those objects. Do not write your own
window or stimulus setup.
EOF
}


# ── Demo prompts ─────────────────────────────────────────────────────────────
demo_status() {
  echo "── HTML demo target ───────────────────────────────────────────────────"
  echo "  short paradigm : ${SHORT_PARADIGM}"
  if [[ -n "$SHORT_PY" ]]; then
    echo "  short .py      : ✅ ${SHORT_PY}"
  else
    echo "  short .py      : ❌ NONE FOUND — prompt D0 will create it first"
  fi
  if [[ -f "$DEMO_TEMPLATE" ]]; then
    echo "  demo template  : ✅ ${DEMO_TEMPLATE}"
  else
    echo "  demo template  : ❌ MISSING ${DEMO_TEMPLATE}"; return 1
  fi
  [[ -e "$DEMO_PATH" ]] && echo "  ⚠️  demo exists (will NOT be overwritten): ${DEMO_PATH}" \
                        || echo "  demo output    : ${DEMO_PATH}"
  return 0
}

d0() { cat <<EOF
── PROMPT D0 — no short version exists, create it first ───────────────────────
There is no short-version PsychoPy script under ${SHORT_PSY_DIR}.
Create one before the demo can be derived.

Source of truth for the SHORT paradigm: ${SHORT_PRES_DIR}/
Read its .exp and every scenario in sce/. Do NOT assume it matches the
full-length paradigm — a short version differs by design in trial counts,
repetitions and stimulus sets. Derive everything from the short paradigm's own
files. If it has no run logs, say so and reason from the PCL, putting anything
uncertain in open_questions rather than guessing.

Copy the window setup, clock and stimulus object definitions from
${REFERENCE} verbatim, then write only the trial/block logic for the short
paradigm. House style is mandatory (pixel units, explicit ImageStim size=).

Write to ${SHORT_PSY_DIR}/${PROJECT}_short_version_${LANG}_generated.py
Then run ./Agent/03_Paradigm/check_runs.sh on it and fix until it passes.
EOF
}

d1() { cat <<EOF
── PROMPT D1 — build the interactive HTML demo ────────────────────────────────
Create a browser demo of the SHORT ${PROJECT} paradigm for Research_BEEHub.

Template : ${DEMO_TEMPLATE}
Source   : ${SHORT_PY:-<the short-version .py you just created>}
Output   : ${DEMO_PATH}

Method — copy the template, then edit ONLY the marked config block:
  1. Copy ${DEMO_TEMPLATE} to ${DEMO_PATH} unchanged.
  2. In the copy, fill in every {{PLACEHOLDER}} inside the block marked
     "▼▼▼ PARADIGM CONFIG — THIS IS THE ONLY BLOCK YOU EDIT ▼▼▼".
  3. Change NOTHING outside that block. The CSS, the six screens and all trial
     machinery are paradigm-agnostic and already work — do not restyle or
     refactor them, and do not rename functions.

Values to fill, all taken from the short-version .py:
  {{PARADIGM_TITLE}}  -> ${DEMO_TITLE}
  {{STIM_BASE}}       -> relative path to the demo's Stimuli folder (e.g. 'Stimuli/')
  {{PAIRS}}           -> one entry per item: house id, correct ('k') image, foil ('i') image
  {{AFC_IMAGES}}      -> one AFC composite per house, SAME ORDER as PAIRS
  {{BUBBLE_*}}        -> the info-bubble images
  {{*_DUR_MS}}        -> timings from the .py, converted seconds -> MILLISECONDS
  {{N_REPS}}          -> ${DEMO_N_REPS}
  {{N_REPS_REAL}}     -> the real repetition count from the .py (documents the difference)

Hard rules:
  - Every image path must exist on disk under the demo's Stimuli folder. Verify
    each one. If any is missing, STOP and report it — never invent a filename.
  - PAIRS and AFC_IMAGES must be the same length and in the same house order.
  - Timing values must match the .py exactly after the s -> ms conversion.
  - Leave no {{PLACEHOLDER}} unreplaced.

When done, report: number of pairs, number of AFC images, the four timing values,
and confirm that no placeholders remain.
EOF
}

d2() { cat <<EOF
── PROMPT D2 — verify the demo ────────────────────────────────────────────────
Check ${DEMO_PATH}:
  1. grep for '{{' — there must be no unreplaced placeholders.
  2. Confirm PAIRS.length === AFC_IMAGES.length.
  3. Verify every image path referenced in the config exists on disk; list any
     that do not.
  4. Confirm nothing outside the PARADIGM CONFIG block differs from
     ${DEMO_TEMPLATE} (diff them and show only the config-block differences).
Report what you found. Fix only real problems; do not restyle anything.
EOF
}

case "${1:-all}" in
  --list)  list_targets; exit 0 ;;
  demo)
     demo_status || exit 1
     if [[ -z "$SHORT_PY" ]]; then echo; d0; fi
     echo; d1; echo; d2
     exit 0 ;;
  --check) check_paths; exit $? ;;
  1) check_paths || exit 1; echo; p1 ;;
  2) check_paths || exit 1; echo; p2 ;;
  3) check_paths || exit 1; echo; p3 ;;
  4) check_paths || exit 1; echo; p4 ;;
  all)
     check_paths || exit 1
     echo; p1; echo; echo "   [stop here — review ${MANIFEST} yourself before prompt 2]"
     echo; p2; echo; p3; echo; p4
     echo; echo "── after prompt 3 passes, verify yourself ──"
     echo "  diff ${PSY_DIR}/${OUT_NAME/${OUT_SUFFIX}/} ${OUT_PATH}"
     echo "  python ${OUT_PATH}"
     ;;
  *) echo "usage: $0 [--list|--check|1|2|3|4|all|demo]" >&2; exit 2 ;;
esac
