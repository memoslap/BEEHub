#!/usr/bin/env bash
# migrate_MT.sh — Move MT project files into the canonical BEEHub layout.
#
# Usage:
#   ./migrate_MT.sh --dry-run   (default)  Print what would be done
#   ./migrate_MT.sh --apply               Actually move/copy files
#
# After --apply:
#   - Raw PsychoPy CSVs stay in sourcedata/raw/ (originals preserved)
#   - Paradigm files, literature, and compiled data are moved to their targets
#   - clean_MT.py is then run to produce BIDS _beh.tsv files from raw CSVs
#
# This script uses git mv for tracked files and cp for untracked originals.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SOURCE_DIR="$SCRIPT_DIR/MouseTracking Data"
PROJECT_DIR="$REPO_ROOT/Projects/MT"
LOG_FILE="$SCRIPT_DIR/migrate_MT.log"

DRY_RUN=true  # default to dry-run

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log() {
    local msg
    msg="$(date '+%Y-%m-%d %H:%M:%S') $1"
    echo "$msg" | tee -a "$LOG_FILE"
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
for arg in "$@"; do
    case "$arg" in
        --apply)
            DRY_RUN=false
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--dry-run|--apply]" >&2
            exit 1
            ;;
    esac
done

# Clear old log
echo "=== migrate_MT.sh ===" > "$LOG_FILE"
log "Mode: $([ "$DRY_RUN" = true ] && echo 'DRY-RUN' || echo 'APPLY')"
log "Source: $SOURCE_DIR"
log "Target: $PROJECT_DIR"

# ---------------------------------------------------------------------------
# Verify source exists
# ---------------------------------------------------------------------------
if [[ ! -d "$SOURCE_DIR" ]]; then
    log "ERROR: Source directory not found: $SOURCE_DIR"
    exit 1
fi

# ---------------------------------------------------------------------------
# Step 1 — Create target directory structure
# ---------------------------------------------------------------------------
log "--- Step 1: Create directory structure ---"

DIRS=(
    "bids_data"
    "literature"
    "paradigm/psychopy"
    "sourcedata/raw"
)

for d in "${DIRS[@]}"; do
    target="$PROJECT_DIR/$d"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would create directory: $target"
    else
        mkdir -p "$target"
        log "  Created: $target"
    fi
done

# Create per-subject/session directories
for sub in $(seq -w 1 26); do
    for ses in 01 02; do
        target="$PROJECT_DIR/bids_data/sub-${sub}/ses-${ses}/beh"
        if [[ "$DRY_RUN" = true ]]; then
            log "  [DRY-RUN] Would create: $target"
        else
            mkdir -p "$target"
        fi
    done
done

# ---------------------------------------------------------------------------
# Step 2 — Move literature files
# ---------------------------------------------------------------------------
log "--- Step 2: Move literature ---"

# PDF preprint
if [[ -f "$SOURCE_DIR/Mahesan et al. 2026 - bioRxiv.pdf" ]]; then
    SRC="$SOURCE_DIR/Mahesan et al. 2026 - bioRxiv.pdf"
    DST="$PROJECT_DIR/literature/Mahesan_2026_biorxiv.pdf"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would move: Mahesan et al. 2026 - bioRxiv.pdf -> literature/Mahesan_2026_biorxiv.pdf"
    else
        git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
        log "  Moved: Mahesan et al. 2026 - bioRxiv.pdf -> literature/Mahesan_2026_biorxiv.pdf"
    fi
fi

# Instructions (renamed to remove space and parentheses)
if [[ -f "$SOURCE_DIR/Program_final_german/Instructions (1).pptx" ]]; then
    SRC="$SOURCE_DIR/Program_final_german/Instructions (1).pptx"
    DST="$PROJECT_DIR/literature/instructions_de.pptx"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would move: Instructions (1).pptx -> literature/instructions_de.pptx"
    else
        git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
        log "  Moved: Instructions (1).pptx -> literature/instructions_de.pptx"
    fi
fi

# ---------------------------------------------------------------------------
# Step 3 — Move paradigm files (PsychoPy)
# ---------------------------------------------------------------------------
log "--- Step 3: Move paradigm files ---"

# Main experiment files — never rename .psyexp or _lastrun.py pair
PARADIGM_FILES=(
    "go_nogo_dm.py"
    "hover_up_click_007b_review.psyexp"
    "hover_up_click_007b_review_lastrun.py"
)

for f in "${PARADIGM_FILES[@]}"; do
    SRC="$SOURCE_DIR/Program_final_german/$f"
    DST="$PROJECT_DIR/paradigm/psychopy/$f"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would move: $f -> paradigm/psychopy/"
    else
        git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
        log "  Moved: $f -> paradigm/psychopy/"
    fi
done

# Condition tables — referenced by filename, keep names
CONDITION_FILES=(
    "go_nogo.xlsx"
    "go_nogo_prac.xlsx"
    "go_only.xlsx"
    "gopractice.xlsx"
    "block_sequence.xlsx"
)

for f in "${CONDITION_FILES[@]}"; do
    SRC="$SOURCE_DIR/Program_final_german/$f"
    DST="$PROJECT_DIR/paradigm/psychopy/$f"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would move: $f -> paradigm/psychopy/"
    else
        git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
        log "  Moved: $f -> paradigm/psychopy/"
    fi
done

# Stimulus images — NEVER rename (hard-coded references)
STIMULUS_FILES=(
    "Slide7.PNG"
    "Slide8.PNG"
)

for f in "${STIMULUS_FILES[@]}"; do
    SRC="$SOURCE_DIR/Program_final_german/$f"
    DST="$PROJECT_DIR/paradigm/psychopy/$f"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would move: $f (verbatim, NOT renamed) -> paradigm/psychopy/"
    else
        git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
        log "  Moved: $f (verbatim) -> paradigm/psychopy/"
    fi
done

# readme.md (0 bytes — documentation)
SRC="$SOURCE_DIR/Program_final_german/readme.md"
DST="$PROJECT_DIR/paradigm/psychopy/readme.md"
if [[ "$DRY_RUN" = true ]]; then
    log "  [DRY-RUN] Would move: readme.md -> paradigm/psychopy/"
else
    git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
    log "  Moved: readme.md -> paradigm/psychopy/"
fi

# ---------------------------------------------------------------------------
# Step 4 — Move README
# ---------------------------------------------------------------------------
log "--- Step 4: Move README ---"

SRC="$SOURCE_DIR/README_MT.md"
DST="$PROJECT_DIR/bids_data/README.md"
if [[ "$DRY_RUN" = true ]]; then
    log "  [DRY-RUN] Would move: README_MT.md -> bids_data/README.md"
else
    git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
    log "  Moved: README_MT.md -> bids_data/README.md"
fi

# ---------------------------------------------------------------------------
# Step 5 — Move compiled data to sourcedata/raw
# ---------------------------------------------------------------------------
log "--- Step 5: Move compiled data ---"

SRC="$SOURCE_DIR/go_nogo_compiledData.csv"
DST="$PROJECT_DIR/sourcedata/raw/go_nogo_compiledData.csv"
if [[ "$DRY_RUN" = true ]]; then
    log "  [DRY-RUN] Would copy: go_nogo_compiledData.csv -> sourcedata/raw/"
else
    git mv "$SRC" "$DST" 2>/dev/null || (cp "$SRC" "$DST" && rm "$SRC")
    log "  Moved: go_nogo_compiledData.csv -> sourcedata/raw/"
fi

# ---------------------------------------------------------------------------
# Step 6 — Copy raw data to sourcedata/raw (preserved originals)
# ---------------------------------------------------------------------------
log "--- Step 6: Copy raw CSVs to sourcedata/raw/ ---"

for rawfile in "$SOURCE_DIR"/"Raw Data"/*.csv; do
    fname="$(basename "$rawfile")"
    DST="$PROJECT_DIR/sourcedata/raw/$fname"
    if [[ "$DRY_RUN" = true ]]; then
        log "  [DRY-RUN] Would copy: Raw Data/$fname -> sourcedata/raw/"
    else
        git mv "$rawfile" "$DST" 2>/dev/null || (cp "$rawfile" "$DST" && rm "$rawfile")
        log "  Copied: Raw Data/$fname -> sourcedata/raw/"
    fi
done

# ---------------------------------------------------------------------------
# Step 7 — Move remaining source files that have no BIDS home
# ---------------------------------------------------------------------------
log "--- Step 7: Handle remaining source files ---"

# The __pycache__ directory and .pyc files are excluded (added to .gitignore)
if [[ -d "$SOURCE_DIR/__pycache__" ]]; then
    log "  Skipping: __pycache__/ (build artefact, excluded from migration)"
fi

# ---------------------------------------------------------------------------
# Step 8 — Clean up empty source directories
# ---------------------------------------------------------------------------
log "--- Step 8: Clean up empty source dirs ---"

if [[ "$DRY_RUN" = true ]]; then
    log "  [DRY-RUN] Would remove empty dirs:"
    log "    $SOURCE_DIR/Raw Data/"
    log "    $SOURCE_DIR/Program_final_german/"
    log "    $SOURCE_DIR/"
else
    rmdir "$SOURCE_DIR/Program_final_german" 2>/dev/null && log "  Removed: Program_final_german/" || true
    rmdir "$SOURCE_DIR/Raw Data" 2>/dev/null && log "  Removed: Raw Data/" || true
    rmdir "$SOURCE_DIR" 2>/dev/null && log "  Removed: MouseTracking Data/" || true
fi

# ---------------------------------------------------------------------------
# Step 9 — Run clean_MT.py (if --apply)
# ---------------------------------------------------------------------------
if [[ "$DRY_RUN" = false ]]; then
    log "--- Step 9: Running clean_MT.py ---"
    python3 "$SCRIPT_DIR/clean_MT.py" --dry-run
    if [[ $? -eq 0 ]]; then
        log "Dry run of clean_MT.py passed. Running for real:"
        python3 "$SCRIPT_DIR/clean_MT.py" --apply
    else
        log "ERROR: clean_MT.py dry-run failed. Aborting."
        exit 1
    fi
else
    log "--- Step 9: clean_MT.py would be run ---"
    log "  [DRY-RUN] Would run: python3 clean_MT.py --dry-run"
    log "  [DRY-RUN] If dry-run passes: python3 clean_MT.py --apply"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
log ""
log "=== Migration complete ==="
if [[ "$DRY_RUN" = true ]]; then
    log "This was a dry run. No files were changed."
    log "Re-run with --apply to actually migrate."
else
    log "Files moved. Run verification commands:"
    log "  find Projects/MT -maxdepth 2 -type d"
    log "  find Projects/MT/bids_data -name '*_beh.tsv' | wc -l"
    log "  find Projects/MT/literature -name '*.pdf'"
fi
