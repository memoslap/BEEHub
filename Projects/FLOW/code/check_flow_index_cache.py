#!/usr/bin/env python3
"""
check_flow_index_cache.py — verify that every cached SessionFlowIndex in FLOW's
sidecars still agrees with the TSV it was derived from.

    ./check_flow_index_cache.py                    # whole FLOW dataset
    ./check_flow_index_cache.py --tol 1e-9         # tighter tolerance
    ./check_flow_index_cache.py --root /path/to/bids_data

READ-ONLY. This script opens files and prints. It writes nothing, moves nothing.

Why this exists
---------------
`sub-XXX_ses-XX_task-FLOW_run-01_FlowIndex_*_beh.json` stores a `SessionFlowIndex`
value inside the column's description object. That value is the mean of the
`flow_index` column of the accompanying `.tsv` — it is a CACHE, not independent
information, and nothing in the BEEHub pipeline reads it or checks it.

A cache nobody validates is a cache that can drift. If the builder was re-run with
different parameters over some sessions and not others, or a TSV was edited by
hand, the JSON and the TSV would disagree and no existing tool would notice. This
script notices.

Verified by hand on sub-006_ses-02 before writing this: the nine `flow_index` rows
mean to -4.666667, matching the sidecar exactly.

How the column is identified
----------------------------
Not hardcoded. Any top-level sidecar key whose value is an object containing
`SessionFlowIndex` is taken to be the name of the TSV column it summarises. So if
the Task measure names its column something other than `flow_index`, this still
works, and a sidecar with no cached value is reported as SKIP rather than failing.

Exit status
-----------
    0  every cached value agrees (or there were none to check)
    1  at least one disagreement or unreadable file
    2  usage error
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

CACHE_KEY = "SessionFlowIndex"


def find_cached(obj: dict) -> list[tuple[str, float, dict]]:
    """Return (column_name, cached_value, description_object) for each cache found."""
    out = []
    for key, val in obj.items():
        if isinstance(val, dict) and CACHE_KEY in val:
            try:
                out.append((key, float(val[CACHE_KEY]), val))
            except (TypeError, ValueError):
                out.append((key, float("nan"), val))
    return out


def column_values(tsv: Path, column: str) -> tuple[list[float], int, list[str]]:
    """Return (numeric values, total data rows, problems)."""
    problems: list[str] = []
    with tsv.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows:
        return [], 0, [f"TSV has no data rows"]
    if column not in rows[0]:
        return [], len(rows), [f"TSV has no column {column!r} "
                               f"(has: {', '.join(rows[0].keys())})"]
    vals: list[float] = []
    for i, r in enumerate(rows, start=2):
        raw = (r.get(column) or "").strip()
        if raw in ("", "n/a"):
            continue
        try:
            vals.append(float(raw))
        except ValueError:
            problems.append(f"line {i}: {column}={raw!r} is not numeric")
    return vals, len(rows), problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=None,
                    help="bids_data directory (default: locate Projects/FLOW/bids_data)")
    ap.add_argument("--tol", type=float, default=1e-5,
                    help="absolute tolerance (default 1e-5; the cache is stored "
                         "to 6 decimals, so anything below ~5e-7 will flag rounding)")
    ap.add_argument("--verbose", action="store_true", help="print every file, not just problems")
    args = ap.parse_args()

    if args.root:
        root = args.root.resolve()
    else:
        root = Path.cwd().resolve()
        while not (root / "Projects" / "FLOW" / "bids_data").is_dir() and root != root.parent:
            root = root.parent
        root = root / "Projects" / "FLOW" / "bids_data"
    if not root.is_dir():
        print(f"ERROR: {root} not found", file=sys.stderr)
        return 2

    print(f"root      : {root}")
    print(f"tolerance : {args.tol}\n")

    ok, mismatch, skipped, broken = 0, 0, 0, 0
    diffs: list[float] = []
    lines: list[str] = []

    for sidecar in sorted(root.rglob("sub-*_beh.json")):
        rel = sidecar.relative_to(root)
        tsv = sidecar.with_suffix(".tsv")

        try:
            obj = json.loads(sidecar.read_text(encoding="utf-8"))
        except Exception as e:
            lines.append(f"BROKEN   {rel}\n           unreadable JSON: {e}")
            broken += 1
            continue

        caches = find_cached(obj)
        if not caches:
            skipped += 1
            if args.verbose:
                lines.append(f"SKIP     {rel}  (no {CACHE_KEY})")
            continue

        if not tsv.is_file():
            lines.append(f"BROKEN   {rel}\n           cached {CACHE_KEY} but no matching TSV")
            broken += 1
            continue

        for column, cached, desc in caches:
            vals, n_rows, problems = column_values(tsv, column)
            for p in problems:
                lines.append(f"BROKEN   {rel}\n           {p}")
                broken += 1
            if not vals:
                continue

            actual = statistics.mean(vals)
            diff = abs(actual - cached)
            diffs.append(diff)

            notes: list[str] = []
            # Free structural cross-checks against the same description object.
            n_items = desc.get("NumberOfItems")
            if isinstance(n_items, int) and n_items != len(vals):
                notes.append(f"NumberOfItems={n_items} but {len(vals)} usable rows")
            bounds = desc.get("Bounds")
            if isinstance(bounds, list) and len(bounds) == 2:
                lo, hi = float(bounds[0]), float(bounds[1])
                out = [v for v in vals if v < lo or v > hi]
                if out:
                    notes.append(f"{len(out)} value(s) outside declared Bounds {bounds}")

            if diff > args.tol:
                lines.append(f"MISMATCH {rel}  [{column}]\n"
                             f"           cached={cached!r}  recomputed={actual:.9f}  "
                             f"diff={diff:.3e}  n={len(vals)}/{n_rows}")
                mismatch += 1
            else:
                ok += 1
                if args.verbose:
                    lines.append(f"OK       {rel}  [{column}] "
                                 f"cached={cached} recomputed={actual:.6f}")
            for n in notes:
                lines.append(f"NOTE     {rel}  [{column}]\n           {n}")

    for l in lines:
        print(l)

    print(f"\n{'=' * 68}")
    print(f"  agree        : {ok}")
    print(f"  MISMATCH     : {mismatch}")
    print(f"  no cache     : {skipped}")
    print(f"  unreadable   : {broken}")
    if diffs:
        print(f"  largest diff : {max(diffs):.3e}   median: {statistics.median(diffs):.3e}")
        print("  (diffs around 1e-7 are the 6-decimal rounding of the stored value,")
        print("   not drift. Anything materially larger means the cache is stale.)")
    if mismatch or broken:
        print("\n  Nothing was modified. Re-run build_flow_bids.py to regenerate,")
        print("  or investigate the listed files before trusting the cached values.")
    return 1 if (mismatch or broken) else 0


if __name__ == "__main__":
    sys.exit(main())
