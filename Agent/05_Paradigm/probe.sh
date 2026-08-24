#!/usr/bin/env bash
# probe.sh — answer the agent's questions mechanically, before it has to ask them.
#
# Runs a battery of deterministic checks over a paradigm's .sce files, Stimuli tree and
# run logs, and writes a report the agent reads during Pass 1. Everything here was
# previously escalated to a human; none of it needs judgement.
#
#   ./Agent/03_Paradigm/probe.sh                 # uses Agent/03_Paradigm/target.env
#   ./Agent/03_Paradigm/probe.sh --out FILE      # write report elsewhere
#
# Report: Agent/03_Paradigm/probes/<PROJECT>_<SET>_probe.md

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
source "$HERE/target.env"
: "${SET_PSYCHOPY:=}"

PRES_DIR="Projects/${PROJECT}/paradigm/presentation/${PARADIGM}/${SET_PRESENTATION}"
SCE_DIR="${PRES_DIR}/sce"
STIM_DIR="${PRES_DIR}/Stimuli"
TAG="${PROJECT}_${SET_PRESENTATION}"
OUT="Agent/03_Paradigm/probes/${TAG}_probe.md"
[[ "${1:-}" == "--out" ]] && OUT="${2:?}"
mkdir -p "$(dirname "$OUT")"

[[ -d "$PRES_DIR" ]] || { echo "❌ no such paradigm dir: $PRES_DIR" >&2; exit 2; }

# Presentation logs: tab-separated; $3=Event Type, $4=Code, $8=Duration (units 0.1 ms)
# Select logs for THIS set only. results/ holds logs from both SETs, pilots, phantoms and
# other paradigm versions — taking the first alphabetically measures the WRONG set and
# reports every stimulus as "missing".
ALL_LOGS=$(find "$PRES_DIR" -maxdepth 2 -iname '*.log' 2>/dev/null | sort)
NALL=$(printf '%s\n' "$ALL_LOGS" | grep -c . || echo 0)
SETLETTER="$(echo "${SET_PRESENTATION##*_}" | tr '[:lower:]' '[:upper:]')"
LOGS=$(printf '%s\n' "$ALL_LOGS" \
       | grep -iE "(_|-)(ses[0-9]_)?${SETLETTER}([_.-]|$)|set${SETLETTER}([_.-]|$)" \
       | grep -viE "pilot|phantom|test|fehlstart" || true)
NLOGS=$(printf '%s\n' "$LOGS" | grep -c . || echo 0)
if [[ "$NLOGS" -eq 0 ]]; then
  LOGS="$ALL_LOGS"; NLOGS="$NALL"
  LOGFILTER="⚠️ no log matched set '${SETLETTER}' — using ALL ${NALL} (unreliable)"
else
  LOGFILTER="set '${SETLETTER}': ${NLOGS} of ${NALL}"
fi
REF_LOG=$(printf '%s\n' "$LOGS" | head -1)

{
echo "# Probe report — ${TAG}"
echo
echo "Generated $(date -u '+%Y-%m-%d %H:%M UTC') by \`Agent/03_Paradigm/probe.sh\`."
echo "**These are measured facts. Prefer them over interpreting PCL. Do not re-derive"
echo "anything answered here, and do not put it in \`open_questions:\`.**"
echo

# ── 1. Inventory ────────────────────────────────────────────────────────────
echo "## 1. Inventory"
echo
echo '```'
echo "exp file(s) : $(find "$PRES_DIR" -maxdepth 1 -name '*.exp' -printf '%f ' 2>/dev/null)"
echo "scenarios   : $(find "$SCE_DIR" -name '*.sce' 2>/dev/null | wc -l)"
echo "run logs    : ${NLOGS}   [${LOGFILTER}]"
echo "stimuli dirs: $(find "$STIM_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f ' 2>/dev/null)"
echo '```'
echo

if [[ "$NLOGS" -eq 0 ]]; then
  echo "> ⚠️ **No run logs.** Sections 2-5 unavailable; counts must be derived from PCL."
  echo "> Be explicit about your reasoning and mark uncertain values in \`open_questions:\`."
  echo
else
echo "Reference log: \`$(basename "$REF_LOG")\`"
echo

# ── 2. Trial structure ──────────────────────────────────────────────────────
echo "## 2. Trial structure (measured)"
echo
echo '```'
echo "block/condition tag counts:"
awk -F'\t' 'NR>4 && $3=="Picture"{print $4}' "$REF_LOG" \
  | grep -oE ";block[0-9]+;[A-Za-z0-9]+" | sort | uniq -c | sed 's/^/  /'
echo
echo "block order as actually run:"
awk -F'\t' 'NR>4 && $3=="Picture"{print $4}' "$REF_LOG" \
  | grep -oE "block[0-9]+|crt[0-9]+" | uniq | tr '\n' ' ' | sed 's/^/  /'
echo
echo "unique stimuli per block:"
for b in 1 2 3 4 5 6; do
  n=$(awk -F'\t' 'NR>4 && $3=="Picture"{print $4}' "$REF_LOG" \
        | grep "block$b" | cut -d';' -f1 | sort -u | wc -l)
  [[ "$n" -gt 0 ]] && echo "  block$b: $n"
done
echo
echo "control trials:"
awk -F'\t' 'NR>4 && $3=="Picture"{print $4}' "$REF_LOG" \
  | grep -oE "crt[0-9]+-[rl]" | sort | uniq -c | sed 's/^/  /'
echo '```'
echo

# ── 3. Response mapping ─────────────────────────────────────────────────────
echo "## 3. Response mapping (measured)"
echo
echo "Port input → response code, from the real run. Preserve these SEMANTICS in the"
echo "keyboard version; write the internal code to the CSV so scoring matches."
echo
echo '```'
grep -E "Port Input|Response" "$REF_LOG" | awk -F'\t' '{print $3, $4}' \
  | sort | uniq -c | sort -rn | head -8 | sed 's/^/  /'
echo '```'
echo "ASCII: 97='a', 98='b', 115='s' (scanner pulse, NOT a response)."
echo

# ── 4. Timing ───────────────────────────────────────────────────────────────
echo "## 4. Realised timing (measured, log units = 0.1 ms)"
echo
echo '```'
echo "stimulus events (most common durations):"
awk -F'\t' 'NR>4 && $3=="Picture" && $4 ~ /block[0-9];LS/{print $8}' "$REF_LOG" \
  | sort -n | uniq -c | sort -rn | head -4 | sed 's/^/  /'
echo "feedback events:"
awk -F'\t' 'NR>4 && $4 ~ /^(correct|incorrect)/{print $8}' "$REF_LOG" \
  | sort -n | uniq -c | sort -rn | head -4 | sed 's/^/  /'
echo '```'
PULSES=$(grep -c "Pulse" "$REF_LOG" 2>/dev/null || echo 0)
if [[ "$PULSES" -gt 0 ]]; then
echo "⚠️ **${PULSES} scanner pulses present — the original was fMRI pulse-locked.**"
echo "Realised durations are therefore variable, NOT the nominal \`set_duration()\` values."
echo "Decide explicitly: nominal PCL values (recommended for standalone) or empirical"
echo "medians. Never mix. Record the choice in the provenance header."
fi
echo

# ── 5. Missing stimuli: what the run used vs what is on disk ────────────────
echo "## 5. Missing stimuli (log vs disk)"
echo
MISSING=0
echo '```'
for b in 1 2 3 4; do
  used=$(awk -F'\t' 'NR>4 && $3=="Picture"{print $4}' "$REF_LOG" \
          | grep "block$b" | cut -d';' -f1 | sort -u)
  [[ -z "$used" ]] && continue
  nused=$(printf '%s\n' "$used" | grep -c .)
  bdir="${STIM_DIR}/learning/block${b}"
  ndisk=$(find "$bdir" -maxdepth 1 -iname '*.jpg' 2>/dev/null | wc -l)
  echo "  block${b}: run used ${nused} unique, disk has ${ndisk} .jpg"
  if [[ -d "$bdir" ]]; then
    while IFS= read -r f; do
      [[ -z "$f" ]] && continue
      [[ -f "${bdir}/${f}" ]] || { echo "    ❌ MISSING: ${f}"; MISSING=$((MISSING+1)); }
    done <<< "$used"
  else
    echo "    ❌ directory does not exist: ${bdir}"
  fi
done
echo '```'
if [[ "$MISSING" -gt 0 ]]; then
  echo "🚨 **${MISSING} stimulus file(s) used in the real run are absent from disk.**"
  echo "Do NOT convert this SET until they are recovered — the deficit would be baked in."
  echo "Record them under \`unresolved:\` and stop."
else
  echo "✅ Every stimulus used in the reference run is present on disk."
fi
echo
fi   # end has-logs

# ── 5b. Stimulus pairing integrity (k/i house grouping) ─────────────────────
echo "## 5b. Pairing integrity (LEARNING blocks only)"
echo
echo "The generated PsychoPy pairs each _k_ (correct-position) file with _i_ files of the"
echo "SAME house. A _k_ with no same-house _i_ yields an empty foil list, so those trials"
echo "silently vanish and the other images are never shown. This does NOT crash."
echo
PAIRFAIL=0
echo '```'
# Learning blocks ONLY. Control uses a flat list (ctrPics) with no k/i pairing,
# so the 1-k-plus-3-foils contract does not apply there.
for d in "$STIM_DIR"/learning/block*; do
  [[ -d "$d" ]] || continue
  rel="${d#$STIM_DIR/}"
  nk=$(find "$d" -maxdepth 1 -iname '*_k_*.jpg' 2>/dev/null | wc -l)
  ni=$(find "$d" -maxdepth 1 -iname '*_i_*.jpg' 2>/dev/null | wc -l)
  orphan=0; total_pairs=0
  while IFS= read -r kf; do
    [[ -z "$kf" ]] && continue
    h="$(basename "$kf" | cut -d_ -f1)"
    m=$(find "$d" -maxdepth 1 -iname "${h}_*_i_*.jpg" 2>/dev/null | wc -l)
    total_pairs=$((total_pairs+1))
    [[ "$m" -eq 0 ]] && { echo "    ❌ ${rel}/$(basename "$kf") — NO same-house _i_ partner"; orphan=$((orphan+1)); }
  done < <(find "$d" -maxdepth 1 -iname '*_k_*.jpg' 2>/dev/null)
  # images that would actually be presented = sum over k of (1 + its foils)
  shown=0
  while IFS= read -r kf; do
    [[ -z "$kf" ]] && continue
    h="$(basename "$kf" | cut -d_ -f1)"
    m=$(find "$d" -maxdepth 1 -iname "${h}_*_i_*.jpg" 2>/dev/null | wc -l)
    shown=$((shown + 1 + m))
  done < <(find "$d" -maxdepth 1 -iname '*_k_*.jpg' 2>/dev/null)
  tot=$((nk+ni))
  flag=""; [[ "$shown" -ne "$tot" ]] && { flag="  ⚠️ ${tot} files present but only ${shown} would be shown"; PAIRFAIL=1; }
  echo "  ${rel}: ${nk} _k_ + ${ni} _i_ = ${tot}${flag}"
done
echo '```'
if [[ "$PAIRFAIL" -ne 0 ]]; then
  echo "🚨 **Pairing is broken in at least one block.** Files present but never presented means"
  echo "the folder was assembled without keeping house groups intact (each _k_ needs its"
  echo "same-house _i_ foils). Fix the STIMULUS FOLDERS — do not work around this in code."
else
  echo "✅ Every _k_ file has same-house _i_ partners; all files would be presented."
fi
echo

# ── 5c. Learning/control overlap ────────────────────────────────────────────
echo "## 5c. Learning vs control overlap"
echo
echo '```'
for n in 1 2 3 4; do
  ld="$STIM_DIR/learning/block${n}"; cd_="$STIM_DIR/control/block${n}"
  [[ -d "$ld" && -d "$cd_" ]] || continue
  ov=$(comm -12 \
        <(find "$ld" -maxdepth 1 -iname '*.jpg' -printf '%f\n' 2>/dev/null | sort) \
        <(find "$cd_" -maxdepth 1 -iname '*.jpg' -printf '%f\n' 2>/dev/null | sort) | wc -l)
  nl=$(find "$ld" -maxdepth 1 -iname '*.jpg' 2>/dev/null | wc -l)
  echo "  block${n}: ${ov} of ${nl} learning images also appear in control"
done
echo '```'
echo "Any overlap means participants see learning stimuli again during control blocks —"
echo "extra encoding exposure that can confound the learning measure. Check whether the"
echo "ORIGINAL presentation folders overlap too; if they do not, the folders were"
echo "mis-assembled. Escalate rather than deciding this yourself."
echo

# ── 6. Directory pollution ──────────────────────────────────────────────────
echo "## 6. Non-stimulus files in Stimuli/"
echo
JUNK=$(find "$STIM_DIR" \( -iname 'Thumbs.db' -o -iname 'desktop.ini' -o -iname '~$*' \) 2>/dev/null | wc -l)
echo '```'
echo "Thumbs.db / desktop.ini / lock files: ${JUNK}"
echo '```'
if [[ "$JUNK" -gt 0 ]]; then
echo "⚠️ **Directory listings are polluted.** Any directory-scanning logic in the generated"
echo "PsychoPy MUST filter to \`*.jpg\` explicitly, or these will be loaded as stimuli."
echo "Add them to .gitignore. Do not count them in stimulus totals."
fi
echo

# ── 7. Absolute paths in .sce ───────────────────────────────────────────────
echo "## 7. Absolute Windows paths in scenarios"
echo
echo "These resolved only on the acquisition machine and MUST be replaced with paths"
echo "relative to the paradigm folder. Note which SET each points at — cross-set"
echo "references mean the asset is SHARED, not misplaced."
echo
echo '```'
grep -rnoE '"[A-Za-z]:/[^"]+"' "$SCE_DIR" 2>/dev/null \
  | sed 's/.*sce\///' | sort -u | head -12 | sed 's/^/  /'
echo '```'
echo

# ── 8. Referenced-but-absent assets, searched repo-wide ─────────────────────
echo "## 8. Referenced assets — do they exist anywhere?"
echo
echo '```'
for d in prac AFC bubbles control learning instr; do
  local_hit=$(find "$STIM_DIR" -maxdepth 2 -type d -iname "$d" 2>/dev/null | head -1)
  if [[ -n "$local_hit" ]]; then
    echo "  ${d}/ : ✅ ${local_hit}"
  else
    repo_hit=$(find Projects -type d -iname "$d" 2>/dev/null | head -2 | tr '\n' ' ')
    if [[ -n "$repo_hit" ]]; then
      echo "  ${d}/ : ⚠️ not in this SET, but found elsewhere → ${repo_hit}"
    else
      echo "  ${d}/ : ❌ NOT FOUND anywhere under Projects/"
    fi
  fi
done
# instruction images
NINSTR=$(find Projects -iname 'instr_[0-9]*.jpg' 2>/dev/null | wc -l)
echo "  instr_NN.jpg referenced by 00_Instr_1.sce : ${NINSTR} found repo-wide"
if [[ "$NINSTR" -eq 0 ]]; then
  PPTX=$(find "$PRES_DIR" -maxdepth 2 -iname '*.pptx' 2>/dev/null | head -2 | tr '\n' ' ')
  FOLIE=$(find Projects -iname 'Folie*.JPG' 2>/dev/null | wc -l)
  echo "    → but Instructions.pptx present: ${PPTX:-none}"
  echo "    → and ${FOLIE} Folie*.JPG slide exports exist elsewhere in the repo"
fi
echo '```'
if [[ "$NINSTR" -eq 0 ]]; then
echo "**Instruction images are missing but REGENERABLE** — export the slides from"
echo "\`Instructions.pptx\` (the short paradigm stores them as \`Instr/instr/Folie*.JPG\`)."
echo "They are full-screen 1280x720, unlike the 1024x787 house stimuli."
fi
echo

# ── 9. AFC variant discrimination ───────────────────────────────────────────
echo "## 9. AFC scenario variants"
echo
echo '```'
for f in "$SCE_DIR"/*AFC*.sce; do
  [[ -f "$f" ]] || continue
  n=$(basename "$f")
  sh=$(grep -c "shuffle()" "$f" 2>/dev/null || echo 0)
  jf=$(grep -c 'find(".jpg")' "$f" 2>/dev/null || echo 0)
  sz=$(grep -oE 'width = [0-9]+; *height = [0-9]+' "$f" 2>/dev/null | head -1)
  echo "  ${n}: shuffle=${sh}  jpg_filter=${jf}  ${sz}"
done
echo '```'
echo "The \`.jpg\` filter is a **bug fix**, not a style choice: without it, Thumbs.db and"
echo "desktop.ini (see §6) are loaded as stimuli. Prefer the filtered variant, and filter"
echo "in the generated PsychoPy regardless of which scenario you follow."
echo

# ── 10. What still needs a human ────────────────────────────────────────────
echo "## 10. Genuinely open — escalate only these"
echo
echo "Everything above is measured. Put a question in \`open_questions:\` ONLY if it is"
echo "a study-design decision that no file can answer, e.g.:"
echo
echo "- fMRI timing convention: nominal PCL durations vs empirical log medians"
echo "- whether a deliberate-looking oddity in the PCL is intended (confirm with the author)"
echo "- how to word instructions when the response device changes (grips → keyboard)"
echo
echo "Do NOT escalate: trial counts, block order, stimulus inventories, response codes,"
echo "durations, missing files, which AFC variant, or where a shared asset lives."
} > "$OUT"

echo "✅ probe report written: $OUT"
grep -E "^🚨|^⚠️" "$OUT" | head -8
