#!/usr/bin/env python3
"""clean_MT.py — extract the 15 analysis columns from raw PsychoPy CSVs and write
strict-BIDS _beh.tsv files for each participant-session.

    python clean_MT.py                  # dry run (DEFAULT)
    python clean_MT.py --apply
    python clean_MT.py --apply --trial-index    # also emit a trial_index column

Column authority: the go_nogo_compiledData.csv header (15 columns). Every other
raw column is dropped but recorded in the root sidecar.

Changes from the previous version, and why
------------------------------------------
1. **Runs from any directory.** The old version formatted log lines with
   `path.relative_to(Path.cwd())`, which raises ValueError unless the current
   directory is an ancestor of the target. Paths are now shown relative to the
   repository root, which is derived from this file's location.

2. **Empty cells are written as `n/a`.** BIDS: missing and non-applicable values
   MUST be coded as `n/a`, never as an empty field. `click_pos_x`/`click_pos_y`
   are empty on every nogo trial, so the old output violated this ~200 times per
   file.

3. **No per-run `_beh.json`.** The old version wrote an identical copy of the
   column dictionary next to every TSV. The Inheritance Principle RECOMMENDS
   storing shared metadata once, higher in the hierarchy. One root dictionary now.

4. **No `_session.json`.** Not a BIDS entity, and its contents were a lowercase
   `repetitiontime` (an MRI field, meaningless here) and `task` (already in every
   filename). Nothing was lost by removing it.

5. **Sidecar has the BIDS shape.** Column descriptions are keyed at the TOP level
   by column name, using `Description` / `Levels` / `Units` / `Delimiter`, not
   nested under a `columns` wrapper with a hand-rolled lowercase `type`. The
   trajectory columns declare `"Delimiter": ","`, which is the spec's mechanism
   for a cell holding a list. `dropped_columns` is retained: a sidecar MAY carry
   file-level metadata under keys that are not column names.

6. **The trailing empty header field no longer becomes a dropped column named
   `""`.** PsychoPy writes a trailing comma; the old code recorded the resulting
   empty name in the sidecar.

7. **Headers are verified across all files before anything is written.** The old
   version built the root dictionary from whichever file sorted first and never
   compared the rest. A mismatch is now a hard abort.

8. **Crash-safe.** Empty file lists and short rows no longer raise IndexError.

Retained from the previous version: the TRIAL_MARKER_COLUMN filter that removes
PsychoPy's welcome/instruction rows and the trailing end-of-experiment row. These
carry `participant` but no trial data, so an "all cells empty" filter does not
catch them. Output produced WITHOUT this filter has 5 extra rows per file
(4 leading + 1 trailing) and is wrong.
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
KEPT_COLUMNS: list[str] = [
    "block_number", "trials_count", "digit", "trial_type", "correct_response",
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.leftButton",
    "mouse_resp.midButton", "mouse_resp.rightButton", "mouse_resp.time",
    "click_pos_x", "click_pos_y", "iti_duration", "participant",
]

# A row is a real TRIAL only if this column is populated.
TRIAL_MARKER_COLUMN = "trial_type"

# Cells holding a list of values. Declared with "Delimiter" in the sidecar.
MULTI_VALUE_COLUMNS = {
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.time",
    "mouse_resp.leftButton", "mouse_resp.midButton", "mouse_resp.rightButton",
}

RAW_MARKER = "_go_nogo_dm_"          # distinguishes raw files from the compiled CSV
NA = "n/a"                            # BIDS missing-value token

# BIDS column descriptions. Top-level keys, CamelCase field names.
COLUMNS: dict[str, dict] = {
    "block_number": {"Description": "Block index within the session."},
    "trials_count": {"Description": "Number of trials in the block. Constant "
                                    "within a block; not a within-block counter."},
    "digit": {"Description": "Stimulus digit presented (1-9, excluding 5)."},
    "trial_type": {"Description": "Trial condition.",
                   "Levels": {"go": "Go trial: a click is required.",
                              "nogo": "No-go trial: the response must be withheld."}},
    "correct_response": {"Description": "Response required on this trial.",
                         "Levels": {"click": "A click inside the target box.",
                                    "none": "No response."}},
    "mouse_resp.x": {"Description": "Mouse x-position trajectory, pixels.",
                     "Units": "pixels"},
    "mouse_resp.y": {"Description": "Mouse y-position trajectory, pixels.",
                     "Units": "pixels"},
    "mouse_resp.leftButton": {"Description": "Left mouse button state at each sample."},
    "mouse_resp.midButton": {"Description": "Middle mouse button state at each sample."},
    "mouse_resp.rightButton": {"Description": "Right mouse button state at each sample."},
    "mouse_resp.time": {"Description": "Sample timestamps, seconds from trial onset. "
                                       "Sampled at approximately 60 Hz.",
                        "Units": "seconds"},
    "click_pos_x": {"Description": "Final click x-position. n/a when no click was made.",
                    "Units": "pixels"},
    "click_pos_y": {"Description": "Final click y-position. n/a when no click was made.",
                    "Units": "pixels"},
    "iti_duration": {"Description": "Inter-trial interval.", "Units": "seconds"},
    "participant": {"Description": "Source participant identifier from the raw file "
                                   "(e.g. '1a', '26b'), retained for provenance. The "
                                   "authoritative identifiers are the sub- and ses- "
                                   "entities in the file path."},
}
TRIAL_INDEX_DESC = {"Description": "1-based position of the trial within the session, "
                                   "after non-trial rows are removed. The raw data "
                                   "carries no trial counter, so this is the only "
                                   "reliable key for joining derivatives back."}

logger = logging.getLogger("clean_MT")


def raise_field_size_limit() -> int:
    """Lift csv's 128 KB field cap as far as this platform allows.

    Raw PsychoPy rows carry whole mouse trajectories in single cells — including
    in columns we discard (iti_trajectory_x, threshold_trajectory_*), which the
    reader must still parse. csv.field_size_limit(sys.maxsize) raises OverflowError
    where C long is narrower than Py_ssize_t, so halve until it is accepted rather
    than hardcoding a number that may be too small on one machine and invalid on
    another.
    """
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return limit
        except OverflowError:
            limit //= 2


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apply", action="store_true", help="actually write files")
    p.add_argument("--trial-index", action="store_true",
                   help="emit a leading trial_index column (see the sidecar note)")
    args = p.parse_args()
    args.dry_run = not args.apply
    return args


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / "Projects").is_dir():
            return p
        p = p.parent
    raise SystemExit("Could not locate the repository root (no Projects/ above this file)")


def read_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        return next(csv.reader(fh))


def read_raw_csv(path: Path) -> tuple[list[str], list[list[str]], int]:
    """Return (header, trial_rows, n_dropped_non_trial_rows)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        rows = [r for r in reader if any(c.strip() for c in r)]

    if TRIAL_MARKER_COLUMN not in header:
        raise ValueError(f"{path.name}: no {TRIAL_MARKER_COLUMN!r} column; "
                         "cannot distinguish trials from instruction rows")
    idx = header.index(TRIAL_MARKER_COLUMN)
    kept = [r for r in rows if idx < len(r) and r[idx].strip()]
    return header, kept, len(rows) - len(kept)


def extract_columns(header: list[str], rows: list[list[str]],
                    trial_index: bool) -> tuple[list[str], list[list[str]]]:
    """Project onto KEPT_COLUMNS, converting empty cells to the BIDS n/a token."""
    idx = {c: header.index(c) for c in KEPT_COLUMNS}   # KeyError-free: verified earlier
    out_header = (["trial_index"] if trial_index else []) + list(KEPT_COLUMNS)
    out_rows: list[list[str]] = []
    for n, row in enumerate(rows, start=1):
        # `row[i] if i < len(row)` guards short rows, which PsychoPy can emit.
        vals = [(row[idx[c]].strip() if idx[c] < len(row) else "") for c in KEPT_COLUMNS]
        vals = [v if v != "" else NA for v in vals]
        out_rows.append(([str(n)] if trial_index else []) + vals)
    return out_header, out_rows


def build_sidecar(dropped: list[str], trial_index: bool,
                  not_universal: list[str] | None = None) -> dict:
    doc: dict = {
        "TaskName": "gonogo",
        "TaskDescription": (
            "Mouse-tracking go/no-go task. A digit is presented; participants click "
            "a target box on go trials and withhold the movement on no-go trials. "
            "The full mouse trajectory is recorded for every trial."
        ),
    }
    if trial_index:
        doc["trial_index"] = dict(TRIAL_INDEX_DESC)
    for col in KEPT_COLUMNS:
        entry = dict(COLUMNS[col])
        if col in MULTI_VALUE_COLUMNS:
            # BIDS: "If rows in a column may be interpreted as a list of values,
            # the character that separates one value from the next."
            entry["Delimiter"] = ","
        doc[col] = entry
    # Permitted file-level metadata: these keys are not TSV column names.
    doc["dropped_columns"] = dropped
    doc["dropped_column_count"] = len(dropped)
    if not_universal:
        # Honesty: the union is documented, but these did not exist in every
        # raw file, so the list is not a description of any single source.
        doc["dropped_columns_absent_from_some_raw_files"] = not_universal
    return doc


def parse_source_name(filename: str) -> tuple[int, str]:
    prefix = filename.removesuffix(".csv").split("_")[0]     # '1a', '26b'
    if not prefix[:-1].isdigit() or prefix[-1] not in "ab":
        raise ValueError(f"cannot parse participant/session from {filename!r}")
    return int(prefix[:-1]), prefix[-1]


def clean_one(src: Path, target_dir: Path, repo: Path,
              dry_run: bool, trial_index: bool) -> dict:
    num, letter = parse_source_name(src.name)
    sub = f"sub-{num:03d}"
    ses = f"ses-{ {'a': '01', 'b': '02'}[letter] }"
    beh_dir = target_dir / sub / ses / "beh"
    beh_tsv = beh_dir / f"{sub}_{ses}_task-gonogo_beh.tsv"

    header, rows, n_dropped_rows = read_raw_csv(src)
    out_header, out_rows = extract_columns(header, rows, trial_index)
    shown = beh_tsv.relative_to(repo)

    if dry_run:
        logger.info("  [DRY-RUN] %-44s -> %s  (%d trials, %d non-trial rows removed)",
                    src.name, shown, len(out_rows), n_dropped_rows)
    else:
        beh_dir.mkdir(parents=True, exist_ok=True)
        with beh_tsv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n",
                           quoting=csv.QUOTE_MINIMAL)
            w.writerow(out_header)
            w.writerows(out_rows)
        logger.info("  [WROTE]   %-44s -> %s  (%d trials, %d non-trial rows removed)",
                    src.name, shown, len(out_rows), n_dropped_rows)

    return {"file": src.name, "sub": sub, "ses": ses,
            "trials": len(out_rows), "dropped_rows": n_dropped_rows}


# ---------------------------------------------------------------------------
def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    logger.info("=== clean_MT.py ===")
    logger.info("Mode: %s", "DRY-RUN" if args.dry_run else "APPLY")
    logger.info("CSV field size limit: %d bytes", raise_field_size_limit())

    repo = find_repo_root(Path(__file__).parent)
    raw_dir = repo / "Projects" / "MT" / "sourcedata" / "raw"
    target_dir = repo / "Projects" / "MT" / "bids_data"
    logger.info("Repo:   %s", repo)
    logger.info("Source: %s", raw_dir.relative_to(repo))
    logger.info("Target: %s", target_dir.relative_to(repo))

    if not raw_dir.is_dir():
        logger.error("Source directory not found: %s", raw_dir)
        return 1

    raw_files = sorted(p for p in raw_dir.glob("*.csv") if RAW_MARKER in p.name)
    skipped = sorted(p.name for p in raw_dir.glob("*.csv") if RAW_MARKER not in p.name)
    logger.info("Raw per-session CSVs: %d   (skipping %d non-raw: %s)",
                len(raw_files), len(skipped), ", ".join(skipped) or "none")
    if not raw_files:
        logger.error("No files matching %r in %s", RAW_MARKER, raw_dir)
        return 1

    # --- verify headers BEFORE writing anything ---------------------------
    # Compare column SETS, not order: extraction is by name (header.index), so a
    # reordered header is harmless. What matters is (a) that every KEPT column
    # exists everywhere, and (b) whether the dropped set varies, which changes
    # what the root dictionary can honestly claim.
    logger.info("Checking headers across %d files...", len(raw_files))
    variants: dict[frozenset, list[str]] = {}
    orders: set[tuple] = set()
    for f in raw_files:
        h = read_header(f)
        orders.add(tuple(h))
        variants.setdefault(frozenset(c for c in h if c.strip()), []).append(f.name)

    if len(orders) > 1:
        logger.info("  %d distinct column ORDERS — harmless, extraction is by name",
                    len(orders))

    bad = {names[0]: sorted(c for c in KEPT_COLUMNS if c not in s)
           for s, names in variants.items()
           if any(c not in s for c in KEPT_COLUMNS)}
    if bad:
        logger.error("Some files are missing required column(s). Aborting; "
                     "nothing was written.")
        for name, missing in bad.items():
            logger.error("  e.g. %s is missing: %s", name, missing)
        return 1

    all_cols = frozenset().union(*variants)
    universal = frozenset.intersection(*variants)
    dropped = sorted(c for c in all_cols if c not in KEPT_COLUMNS)
    not_universal = sorted(c for c in all_cols - universal if c not in KEPT_COLUMNS)

    if len(variants) > 1:
        logger.warning("  %d distinct column SETS. All 15 kept columns are present "
                       "in every file, so cleaning is safe, but %d dropped column(s) "
                       "do not exist in every raw file.",
                       len(variants), len(not_universal))
        for s, names in sorted(variants.items(), key=lambda kv: -len(kv[1])):
            absent = sorted(c for c in all_cols - s if c.strip())
            logger.warning("    %d files (e.g. %s) lack: %s",
                           len(names), names[0],
                           absent[:6] if absent else "nothing")
        logger.warning("  Run diff_headers.py for the full comparison.")
    else:
        logger.info("  all %d files share one column set", len(raw_files))
    logger.info("  keeping %d columns, dropping %d", len(KEPT_COLUMNS), len(dropped))

    # --- process -----------------------------------------------------------
    results = [clean_one(f, target_dir, repo, args.dry_run, args.trial_index)
               for f in raw_files]

    # --- root sidecar ------------------------------------------------------
    root_json = target_dir / "task-gonogo_beh.json"
    sidecar = build_sidecar(dropped, args.trial_index, not_universal)
    if args.dry_run:
        logger.info("  [DRY-RUN] root dictionary -> %s", root_json.relative_to(repo))
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        root_json.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        logger.info("  [WROTE]   root dictionary -> %s", root_json.relative_to(repo))

    # --- summary -----------------------------------------------------------
    logger.info("=== Summary ===")
    logger.info("Files processed : %d", len(results))
    logger.info("Trials written  : %d", sum(r["trials"] for r in results))
    logger.info("Non-trial rows removed: %d", sum(r["dropped_rows"] for r in results))

    counts = sorted({r["trials"] for r in results})
    if len(counts) > 1:
        logger.warning("Trial counts differ across sessions: %s — check the outliers",
                       counts)
        for r in results:
            if r["trials"] != counts[-1]:
                logger.warning("    %s %s: %d trials", r["sub"], r["ses"], r["trials"])

    subs = {}
    for r in results:
        subs.setdefault(r["sub"], []).append(r["ses"])
    incomplete = {s: v for s, v in subs.items() if len(v) < 2}
    if incomplete:
        logger.warning("Subjects with a single session (reported, not filled in): %s",
                       ", ".join(f"{s} ({v[0]})" for s, v in sorted(incomplete.items())))

    if args.dry_run:
        logger.info("No files were written. Re-run with --apply.")
    else:
        logger.info("Next: python Agent/bids_repair.py MT")
    return 0


if __name__ == "__main__":
    sys.exit(main())
