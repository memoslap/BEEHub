#!/usr/bin/env python3
"""
suggest_outcomes.py — list the columns in a project's BIDS tables and say which
are usable as ICC outcomes, so a human can pick the primary and secondary.

    ./suggest_outcomes.py MT
    ./suggest_outcomes.py MT --max-outcomes 6

The agent does NOT decide which column is primary. It runs this, shows the table,
and asks. This script does the measuring; the human does the choosing.

An ICC outcome must be:
  - numeric
  - present for (nearly) every subject x session
  - variable BETWEEN subjects  (zero between-subject variance -> ICC undefined)
  - reducible to ONE value per subject x session

Columns holding trajectory arrays, identifiers, or constants are rejected with a
reason. Rejections are as useful as acceptances: they tell you the raw table has
no analysable outcome yet and a derivation step is missing.

Exit 0 = at least one viable column found
Exit 1 = none found (derivation step required before BEEHub can compute ICC)
Exit 2 = usage error
"""
import sys
import csv
import re
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(10_000_000)   # trajectory cells can be very large

SUBJ = re.compile(r"sub-([0-9A-Za-z]+)")
SESS = re.compile(r"ses-([0-9A-Za-z]+)")
ID_LIKE = re.compile(r"(^|_)(id|participant|subject|session|trial|block|index|"
                     r"date|time_?stamp|file|name|count)(_|$)", re.I)


def is_number(s):
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        print("usage: ./suggest_outcomes.py <CODE> [--max-outcomes N]", file=sys.stderr)
        return 2
    code = args[0]
    try:
        i = sys.argv.index("--max-outcomes")
        max_out = int(sys.argv[i + 1])
    except (ValueError, IndexError):
        max_out = 6

    root = Path.cwd()
    while not (root / "Agent").is_dir() and root != root.parent:
        root = root.parent
    bids = root / "Projects" / code / "bids_data"
    if not bids.is_dir():
        print(f"❌ {bids} not found.", file=sys.stderr)
        return 2

    tsvs = sorted(bids.glob("sub-*/ses-*/**/*.tsv"))
    if not tsvs:
        print(f"❌ no sub-*/ses-*/**.tsv under {bids}", file=sys.stderr)
        return 2

    # group files by their suffix (everything after sub-XXX_ses-YY_)
    by_suffix = defaultdict(list)
    for t in tsvs:
        parts = t.name.split("_")
        suffix = "_" + "_".join(parts[2:]) if len(parts) > 2 else t.name
        by_suffix[suffix].append(t)

    print(f"── outcome scan: Projects/{code}/bids_data")
    print(f"   {len(tsvs)} table(s) in {len(by_suffix)} group(s)\n")

    any_viable = False
    viable_all = []

    for suffix, files in sorted(by_suffix.items()):
        # values[col][(sub,ses)] = list of numeric values
        values = defaultdict(lambda: defaultdict(list))
        nonnum = defaultdict(int)
        cols = []
        for f in files:
            sub = SUBJ.search(f.name)
            ses = SESS.search(f.name)
            key = (sub.group(1) if sub else "?", ses.group(1) if ses else "?")
            try:
                with f.open(newline="") as fh:
                    r = csv.DictReader(fh, delimiter="\t")
                    if r.fieldnames and not cols:
                        cols = [c for c in r.fieldnames if c]
                    for row in r:
                        for c in cols:
                            v = (row.get(c) or "").strip()
                            if v == "" or v.lower() in ("na", "nan", "n/a"):
                                continue
                            if is_number(v):
                                values[c][key].append(float(v))
                            else:
                                nonnum[c] += 1
            except Exception as e:
                print(f"   ⚠️  could not read {f.name}: {e}")

        print(f"── group  {suffix}   ({len(files)} files)")
        if not cols:
            print("   (no header)\n")
            continue

        n_cells = len({(SUBJ.search(f.name).group(1) if SUBJ.search(f.name) else '?',
                        SESS.search(f.name).group(1) if SESS.search(f.name) else '?')
                       for f in files})

        rows = []
        for c in cols:
            cells = values[c]
            n_have = len(cells)
            if nonnum[c] and n_have == 0:
                rows.append((c, "no", "non-numeric (text/array)"))
                continue
            if n_have == 0:
                rows.append((c, "no", "empty"))
                continue
            if ID_LIKE.search(c):
                rows.append((c, "no", "identifier/index column"))
                continue
            # one value per subject-session = mean of the cell
            means = [sum(v) / len(v) for v in cells.values()]
            spread = max(means) - min(means) if means else 0.0
            if spread == 0:
                rows.append((c, "no", "constant across subjects (ICC undefined)"))
                continue
            cov = n_have / n_cells if n_cells else 0
            note = (f"n={n_have}/{n_cells} cells, "
                    f"range {min(means):.4g}..{max(means):.4g}")
            if cov < 0.8:
                rows.append((c, "weak", note + " — sparse coverage"))
            else:
                rows.append((c, "YES", note))
                viable_all.append((suffix, c))
                any_viable = True

        w = max(len(r[0]) for r in rows) + 2
        for c, ok, note in rows:
            mark = {"YES": "✅", "weak": "⚠️ ", "no": "  "}[ok]
            print(f"   {mark} {c:<{w}} {note}")
        print()

    # ---- the questions the agent must put to the human ------------------
    print("=" * 70)
    if not any_viable:
        print("❌ NO ICC-VIABLE COLUMN FOUND.")
        print()
        print("   The tables contain only identifiers and/or raw arrays. BEEHub")
        print("   cannot compute reliability from these. A DERIVATION step is")
        print("   required: a script must reduce the raw records to one numeric")
        print("   value per subject x session per measure, written as its own")
        print("   table, and declared in the project description.")
        print()
        print("   Declare it, then run:")
        print(f"       ./Agent/tools/run_derivation.py {code}")
        print()
        print("   Do NOT invent outcome columns to fill the gap.")
        return 1

    print(f"✅ {len(viable_all)} candidate outcome column(s).")
    print()
    print("ASK THE HUMAN (do not answer these yourself):")
    print()
    for n, (suffix, c) in enumerate(viable_all, 1):
        print(f"   [{n}] {c}   (in {suffix})")
    print()
    print("   Q1. Which is the PRIMARY outcome?   (one number — REQUIRED)")
    print("   Q2. Which is the SECONDARY outcome? (one number, or 'none')")
    print(f"   Q3. Which others should BEEHub compute ICC for? "
          f"(up to {max_out - 2} more, or 'none')")
    print()
    print("   For each chosen column also ask: higher_is_better (yes/no),")
    print("   is it binary (0/1), and a short human-readable label.")
    print()
    print("   A PRIMARY role must be declared explicitly. R-BEEHub does NOT infer")
    print("   a hierarchy from display_priority or column order: a project with no")
    print("   declared role is reported at project level but WITHHELD from the")
    print("   cross-project comparison. Do not answer Q1 yourself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
