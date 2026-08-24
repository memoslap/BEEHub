#!/usr/bin/env python3
"""clean_MT.py — Extract the 15 analysis columns from raw PsychoPy CSVs and
write BIDS-compliant _beh.tsv + _beh.json for each participant-session.

Column authority: go_nogo_compiledData.csv header (15 columns).
All other columns (191) are dropped but recorded in the _beh.json sidecar.

Usage:
    python clean_MT.py [--dry-run] [--apply]

    --dry-run  (default)  Print what would be done without writing.
    --apply            Actually write .tsv and .json files.

The script reads raw CSVs from the source tree and writes cleaned output
into the target bids_data/ directory. It never modifies source files.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
# Column authority — the 15 columns the analysis pipeline uses.
# Order matches go_nogo_compiledData.csv header exactly.
KEPT_COLUMNS: list[str] = [
    "block_number",
    "trials_count",
    "digit",
    "trial_type",
    "correct_response",
    "mouse_resp.x",
    "mouse_resp.y",
    "mouse_resp.leftButton",
    "mouse_resp.midButton",
    "mouse_resp.rightButton",
    "mouse_resp.time",
    "click_pos_x",
    "click_pos_y",
    "iti_duration",
    "participant",
]

# Multi-value (trajectory array) columns — stored as JSON-like strings.
# These must remain as single TSV fields; do NOT split on commas.
MULTI_VALUE_COLUMNS: set[str] = {
    "mouse_resp.x",
    "mouse_resp.y",
    "mouse_resp.time",
}

# Column descriptions for the _beh.json sidecar.
COLUMN_DESCRIPTIONS: dict[str, str] = {
    "block_number": "Block index (integer)",
    "trials_count": "Number of trials in the block",
    "digit": "Stimulus digit presented (1-9, excluding 5)",
    "trial_type": "Go or no-go trial",
    "correct_response": "Required response: click (go) or none (nogo)",
    "mouse_resp.x": "Mouse x-position trajectory (JSON array of floats)",
    "mouse_resp.y": "Mouse y-position trajectory (JSON array of floats)",
    "mouse_resp.leftButton": "Left button state trajectory (JSON array)",
    "mouse_resp.midButton": "Middle button state trajectory (JSON array)",
    "mouse_resp.rightButton": "Right button state trajectory (JSON array)",
    "mouse_resp.time": "Mouse timestamp series (JSON array of floats)",
    "click_pos_x": "Final click x-position (float or empty for nogo)",
    "click_pos_y": "Final click y-position (float or empty for nogo)",
    "iti_duration": "Inter-trial interval in seconds",
    "participant": "Source participant identifier (e.g. '1a', '26b')",
}

logger = logging.getLogger("clean_MT")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract 15 analysis columns from raw PsychoPy CSVs to BIDS _beh.tsv"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Preview only (default).",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually write files.",
    )
    args = parser.parse_args()
    # argparse stores --dry-run as True by default; if --apply is given, override
    if args.apply:
        args.dry_run = False
    return args


def read_raw_csv(csv_path: Path) -> tuple[list[str], list[list[str]]]:
    """Read a raw PsychoPy CSV (UTF-8 with BOM), return (header, rows).

    The trailing empty column from PsychoPy is preserved in the header list
    so index lookups remain stable. Rows that are entirely empty are dropped.
    """
    csv.field_size_limit(500000000)  # trajectory arrays can be very long
    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if any(c.strip() for c in r)]
    return header, rows


def extract_columns(
    header: list[str], rows: list[list[str]], kept: list[str]
) -> tuple[list[str], list[list[str]]]:
    """Return (kept_header, kept_rows) for the columns in *kept*."""
    col_indices: dict[str, int] = {}
    for col in kept:
        if col not in header:
            raise ValueError(f"Column '{col}' not found in header")
        col_indices[col] = header.index(col)

    kept_header = list(kept)  # preserve our canonical order
    kept_rows = []
    for row in rows:
        kept_row = [row[idx] for idx in col_indices.values()]
        kept_rows.append(kept_row)
    return kept_header, kept_rows


def build_beh_json(
    dropped_all: list[str], kept: list[str]
) -> dict:
    """Build the _beh.json sidecar content."""
    # Keep only the columns that actually exist in our kept list, with desc.
    with_desc: dict[str, dict] = {}
    for col in kept:
        with_desc[col] = {
            "description": COLUMN_DESCRIPTIONS.get(col, ""),
        }
        if col in MULTI_VALUE_COLUMNS:
            with_desc[col]["type"] = "array"
        else:
            with_desc[col]["type"] = "scalar"

    return {
        "columns": with_desc,
        "dropped_columns": sorted(dropped_all),
    }


# ---------------------------------------------------------------------------
# Core migration logic
# ---------------------------------------------------------------------------
def parse_source_name(filename: str) -> tuple[int, str]:
    """Extract (participant_number, session_letter) from a raw filename.

    Examples:
        '1a_go_nogo_dm_2025-04-30_11h24.50.998.csv' -> (1, 'a')
        '26b_go_nogo_dm_2025-05-26_13h01.21.617.csv' -> (26, 'b')
    """
    base = filename.removesuffix(".csv")
    # Last two chars before the underscore-separated date: e.g. '1a', '26b'
    # Pattern: <digits><letter>_go_nogo_dm_...
    parts = base.split("_")
    prefix = parts[0]  # e.g. '1a', '26b'
    number = int(prefix[:-1])  # e.g. 1, 26
    letter = prefix[-1]  # e.g. 'a', 'b'
    return number, letter


def session_letter_to_bids(letter: str) -> str:
    """Map source session letter to BIDS ses-NN."""
    mapping = {"a": "01", "b": "02"}
    if letter not in mapping:
        raise ValueError(f"Unknown session letter: {letter!r}")
    return mapping[letter]


def clean_one_file(
    source_path: Path,
    target_dir: Path,
    dry_run: bool,
) -> dict:
    """Clean a single raw CSV and write the _beh.tsv + _beh.json.

    Returns a summary dict for logging.
    """
    filename = source_path.name
    num, letter = parse_source_name(filename)
    sub = f"sub-{num:03d}"
    ses = f"ses-{session_letter_to_bids(letter)}"

    # Destination paths
    beh_dir = target_dir / sub / ses / "beh"
    beh_tsv = beh_dir / f"{sub}_{ses}_task-gonogo_beh.tsv"
    beh_json = beh_dir / f"{sub}_{ses}_task-gonogo_beh.json"
    session_json = beh_dir / f"{sub}_{ses}_session.json"

    # Read raw CSV
    header, rows = read_raw_csv(source_path)
    total_rows = len(rows)

    # Find dropped columns
    header_set = set(header)
    dropped = sorted(c for c in header if c not in KEPT_COLUMNS)

    # Extract only kept columns
    kept_header, kept_rows = extract_columns(header, rows, KEPT_COLUMNS)

    # Build sidecar JSONs
    beh_json_content = build_beh_json(dropped, KEPT_COLUMNS)
    session_json_content = {
        "repetitiontime": 0.0,
        "task": "gonogo",
    }

    if dry_run:
        logger.info(
            "  [DRY-RUN] %s -> %s (%d rows, %d cols -> 15 cols, dropped %d)",
            filename,
            beh_tsv.relative_to(Path.cwd()),
            total_rows,
            len(header),
            len(dropped),
        )
        return {
            "file": filename,
            "target": str(beh_tsv.relative_to(Path.cwd())),
            "rows": total_rows,
            "kept": len(KEPT_COLUMNS),
            "dropped": len(dropped),
        }

    # Write TSV
    beh_dir.mkdir(parents=True, exist_ok=True)
    with beh_tsv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(kept_header)
        writer.writerows(kept_rows)

    # Write _beh.json sidecar
    with beh_json.open("w", encoding="utf-8") as fh:
        json.dump(beh_json_content, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    # Write _session.json sidecar
    with session_json.open("w", encoding="utf-8") as fh:
        json.dump(session_json_content, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    logger.info(
        "  [WROTE]    %s -> %s (%d rows, 15 cols, dropped %d)",
        filename,
        beh_tsv.relative_to(Path.cwd()),
        total_rows,
        len(dropped),
    )
    return {
        "file": filename,
        "target": str(beh_tsv.relative_to(Path.cwd())),
        "rows": total_rows,
        "kept": len(KEPT_COLUMNS),
        "dropped": len(dropped),
    }


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )

    log = logging.getLogger("clean_MT")
    log.info("=== clean_MT.py ===")
    log.info("Mode: %s", "DRY-RUN" if args.dry_run else "APPLY")

    # Paths — read raw CSVs from the already-migrated sourcedata/raw/
    # (the source directory is removed by migrate_MT.sh before this runs)
    base = Path(__file__).resolve().parent.parent  # repo root
    raw_dir = base / "Projects" / "MT" / "sourcedata" / "raw"
    target_dir = base / "Projects" / "MT" / "bids_data"

    if not raw_dir.is_dir():
        log.error("Source directory not found: %s", raw_dir)
        sys.exit(1)

    csv_files = sorted(raw_dir.glob("*.csv"))
    log.info("Found %d raw CSV files", len(csv_files))

    # Write column dictionary at bids_data root
    all_header = None
    with csv_files[0].open(newline="", encoding="utf-8-sig") as fh:
        all_header = next(csv.reader(fh))
    dropped_all = sorted(c for c in all_header if c not in KEPT_COLUMNS)
    root_beh_json = build_beh_json(dropped_all, KEPT_COLUMNS)

    if args.dry_run:
        log.info(
            "Root column dictionary would be written to: %s",
            (target_dir / "task-gonogo_beh.json").relative_to(Path.cwd()),
        )
        log.info("Session sidecar would include: task=gonogo")

    # Process each raw CSV — skip non-raw files like the compiled CSV
    # that may also live in sourcedata/raw/
    raw_prefix = "_go_nogo_dm_"
    results: list[dict] = []
    for csv_file in csv_files:
        fname = csv_file.name
        if raw_prefix not in fname:
            log.info("  Skipping non-raw file: %s", fname)
            continue
        result = clean_one_file(csv_file, target_dir, args.dry_run)
        results.append(result)

    # Write root column dictionary (once, same for all runs)
    root_json_path = target_dir / "task-gonogo_beh.json"
    if not args.dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        with root_json_path.open("w", encoding="utf-8") as fh:
            json.dump(root_beh_json, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        log.info("Wrote root column dictionary: %s", root_json_path)

    # Summary
    total_rows = sum(r["rows"] for r in results)
    log.info("=== Summary ===")
    log.info("Files processed: %d", len(results))
    log.info("Total rows written: %d", total_rows)
    log.info("Columns kept: %d, dropped: %d", results[0]["kept"], results[0]["dropped"])

    if args.dry_run:
        log.info("No files were written (--dry-run mode).")


if __name__ == "__main__":
    main()
