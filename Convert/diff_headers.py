#!/usr/bin/env python3
"""
diff_headers.py — characterise the header variants among MT's raw PsychoPy CSVs.

    python diff_headers.py

READ-ONLY. Reads only the first line of each CSV. Writes nothing.

Answers the three questions that decide how clean_MT.py should handle them:

  1. Are the column SETS identical and only the ORDER differs?
     -> Harmless. Extraction is by name (header.index), so order never mattered.
        The consistency check was simply too strict.

  2. Do the sets differ, but only among columns we DROP anyway?
     -> Tolerable. The root dictionary must then document the union, and note
        which columns are absent from which files.

  3. Does any of the 15 KEPT columns go missing in one variant?
     -> Hard stop. Those files cannot be cleaned to the same column set, and
        the difference has to be understood before anything is written.
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict
from pathlib import Path

KEPT = [
    "block_number", "trials_count", "digit", "trial_type", "correct_response",
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.leftButton",
    "mouse_resp.midButton", "mouse_resp.rightButton", "mouse_resp.time",
    "click_pos_x", "click_pos_y", "iti_duration", "participant",
]
RAW_MARKER = "_go_nogo_dm_"


def find_repo(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / "Projects").is_dir():
            return p
        p = p.parent
    sys.exit("Could not locate the repository root")


def main() -> int:
    repo = find_repo(Path(__file__).parent)
    raw = repo / "Projects" / "MT" / "sourcedata" / "raw"
    files = sorted(p for p in raw.glob("*.csv") if RAW_MARKER in p.name)
    if not files:
        sys.exit(f"No raw CSVs in {raw}")

    variants: dict[tuple, list[str]] = defaultdict(list)
    for f in files:
        with f.open(newline="", encoding="utf-8-sig") as fh:
            variants[tuple(next(csv.reader(fh)))].append(f.name)

    print(f"{len(files)} raw files, {len(variants)} header variant(s)\n")
    ordered = sorted(variants.items(), key=lambda kv: -len(kv[1]))

    for i, (h, names) in enumerate(ordered, 1):
        blanks = sum(1 for c in h if not c.strip())
        print(f"variant {i}: {len(h)} columns ({blanks} blank), {len(names)} files")
        # session letter breakdown, in case the split tracks a/b
        a = sum(1 for n in names if n.split("_")[0].endswith("a"))
        print(f"   sessions: {a} 'a' files, {len(names) - a} 'b' files")
        # acquisition-date range, in case it tracks a mid-study software change
        dates = sorted(n.split("_go_nogo_dm_")[1][:10] for n in names)
        print(f"   dates   : {dates[0]} .. {dates[-1]}")
        print(f"   example : {names[0]}")

    if len(ordered) < 2:
        print("\nOnly one variant — nothing to diff.")
        return 0

    base_h, base_names = ordered[0]
    base_set = set(base_h)

    for i, (h, names) in enumerate(ordered[1:], 2):
        s = set(h)
        only_base = sorted(c for c in base_set - s if c.strip())
        only_this = sorted(c for c in s - base_set if c.strip())

        print(f"\n{'=' * 68}\nvariant 1 vs variant {i}\n{'=' * 68}")

        if not only_base and not only_this:
            print("  Column SETS are IDENTICAL. The difference is ORDER only.")
            # show the first few positions that differ
            diffs = [(n, a, b) for n, (a, b) in enumerate(zip(base_h, h), 1) if a != b]
            print(f"  {len(diffs)} position(s) differ; first few:")
            for n, a, b in diffs[:8]:
                print(f"    pos {n:>3}: variant1={a!r}  variant{i}={b!r}")
            print("\n  => HARMLESS. clean_MT.py extracts by name, not position.")
        else:
            if only_base:
                print(f"  Present in variant 1, ABSENT from variant {i} ({len(only_base)}):")
                for c in only_base:
                    print(f"    - {c}")
            if only_this:
                print(f"  Present in variant {i}, ABSENT from variant 1 ({len(only_this)}):")
                for c in only_this:
                    print(f"    + {c}")

        missing_kept = [c for c in KEPT if c not in s]
        if missing_kept:
            print(f"\n  *** KEPT COLUMN(S) MISSING from variant {i}: {missing_kept}")
            print("  *** These files cannot be cleaned to the 15-column set.")
        else:
            print(f"\n  All 15 KEPT columns are present in variant {i}.")

    print(f"\n{'=' * 68}")
    all_kept_ok = all(all(c in set(h) for c in KEPT) for h, _ in ordered)
    print("  Verdict:", "every variant has all 15 kept columns"
          if all_kept_ok else "AT LEAST ONE VARIANT IS MISSING A KEPT COLUMN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
