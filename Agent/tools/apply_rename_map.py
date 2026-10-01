#!/usr/bin/env python3
"""
apply_rename_map.py — execute a reviewed rename map. Generic for every project.

Replaces the per-project `migrate_<CODE>.sh` + `clean_<CODE>.py` pattern: the
Restructure agent writes DATA (a rename map), this one script acts on it.

    ./Agent/tools/apply_rename_map.py Convert/<drop>/_intake/rename_map.tsv          # dry run
    ./Agent/tools/apply_rename_map.py Convert/<drop>/_intake/rename_map.tsv --apply

The map is a TSV with a header row:

    source    target    action    note

  source   path relative to the repo root (quote nothing; tabs separate columns)
  target   path relative to the repo root; must lie under Projects/
  action   copy      copy one file, verify checksum
           csv2tsv   read CSV, write TSV (empty cells -> n/a, as BIDS requires)
           copytree  copy a whole directory unchanged (Stimuli/, paradigm trees)
           skip      deliberately not migrated (junk, duplicates) — say why in note
           review    undecided — --apply refuses while any row says this

Guarantees
  * dry run is the default; nothing is written without --apply
  * sources are never modified, moved or deleted
  * idempotent: an identical target is reported "already done" and left alone
  * refuses to apply if any source is missing, two rows share a target, a
    target exists with different content, or a row is still `review`
  * appends every action to apply_rename_map.log next to the map

Exit: 0 clean, 1 problems found (or refused), 2 usage error.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import pathlib
import re
import shutil
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from beehub_root import add_root_arg, find_root  # noqa: E402

ACTIONS = {"copy", "csv2tsv", "copytree", "skip", "review"}
BIDS_FILE = re.compile(r"^sub-(\d+)_ses-(\d+)_")

# Python's default cell limit is 128 KB. Behavioural paradigms routinely write a
# whole mouse/eye trajectory into one cell (mouse_positions_x and friends), which
# is larger than that, so the default makes csv.reader raise on perfectly valid
# data. Raise it to the platform maximum; sys.maxsize overflows the C long on
# 32-bit builds, hence the fallback.
try:
    csv.field_size_limit(sys.maxsize)
except OverflowError:
    csv.field_size_limit(2**31 - 1)


def sha(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_to_tsv_bytes(src: pathlib.Path, encoding: str) -> bytes:
    text = src.read_text(encoding=encoding)
    out = io.StringIO()
    w = csv.writer(out, delimiter="\t", lineterminator="\n")
    for n, row in enumerate(csv.reader(io.StringIO(text)), 1):
        for cell in row:
            if "\t" in cell or "\n" in cell:
                raise ValueError(f"line {n}: a cell contains a tab or newline — "
                                 "cannot be written as TSV safely")
        w.writerow([c if c.strip() != "" else "n/a" for c in row])
    return out.getvalue().encode("utf-8")


JUNK = ("Thumbs.db", "desktop.ini", "~$*", "__pycache__", "*.pyc")


def is_junk(rel: pathlib.PurePath) -> bool:
    return any(part == j or pathlib.PurePath(part).match(j) for part in rel.parts for j in JUNK)


def tree_signature(root: pathlib.Path) -> dict[str, str]:
    # Same exclusions as the copy itself, so a re-run compares like with like.
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and not is_junk(p.relative_to(root))}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("map", help="rename_map.tsv")
    ap.add_argument("--apply", action="store_true", help="actually write files")
    add_root_arg(ap)
    ap.add_argument("--encoding", default="utf-8-sig",
                    help="encoding of CSV sources for csv2tsv (default utf-8-sig)")
    args = ap.parse_args()

    map_path = pathlib.Path(args.map)
    if not map_path.is_file():
        print(f"no such map: {map_path}", file=sys.stderr)
        return 2
    root = find_root(map_path.parent, args.root)

    with map_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    need = {"source", "target", "action"}
    if not rows or not need <= set(rows[0].keys()):
        print(f"map needs a header with columns: {', '.join(sorted(need))}", file=sys.stderr)
        return 2

    problems: list[str] = []
    warnings: list[str] = []
    plan: list[tuple[str, pathlib.Path, pathlib.Path | None, str]] = []
    seen_targets: dict[str, int] = {}
    ses_widths: set[int] = set()
    sub_widths: set[int] = set()

    for n, r in enumerate(rows, 2):                      # line 1 is the header
        action = (r.get("action") or "").strip()
        src_s = (r.get("source") or "").strip()
        tgt_s = (r.get("target") or "").strip()
        where = f"line {n}"

        if action not in ACTIONS:
            problems.append(f"{where}: unknown action '{action}'")
            continue
        if action == "review":
            problems.append(f"{where}: still marked review — {src_s}")
            continue
        src = root / src_s
        if not src.exists():
            problems.append(f"{where}: source missing — {src_s}")
            continue
        if action == "skip":
            plan.append(("skip", src, None, r.get("note") or ""))
            continue

        if not tgt_s.startswith("Projects/"):
            problems.append(f"{where}: target must be under Projects/ — {tgt_s}")
            continue
        if tgt_s in seen_targets:
            problems.append(f"{where}: target also used on line {seen_targets[tgt_s]} — {tgt_s}")
            continue
        seen_targets[tgt_s] = n
        tgt = root / tgt_s
        if not tgt.resolve().is_relative_to((root / "Projects").resolve()):
            problems.append(f"{where}: target escapes Projects/ — {tgt_s}")
            continue

        if action == "copytree" and not src.is_dir():
            problems.append(f"{where}: copytree needs a directory — {src_s}")
            continue
        if action in ("copy", "csv2tsv") and not src.is_file():
            problems.append(f"{where}: {action} needs a file — {src_s}")
            continue

        if "/bids_data/sub-" in tgt_s and tgt.suffix:
            m = BIDS_FILE.match(tgt.name)
            if not m:
                warnings.append(f"{where}: BIDS file name does not start sub-<N>_ses-<N>_ — {tgt.name}")
            else:
                sub_widths.add(len(m.group(1)))
                ses_widths.add(len(m.group(2)))

        # Idempotence / conflict check against what is already on disk.
        state = "new"
        if tgt.exists():
            try:
                if action == "copy":
                    same = tgt.is_file() and sha(tgt) == sha(src)
                elif action == "csv2tsv":
                    same = tgt.is_file() and tgt.read_bytes() == csv_to_tsv_bytes(src, args.encoding)
                else:
                    same = tgt.is_dir() and tree_signature(tgt) == tree_signature(src)
            except (ValueError, UnicodeDecodeError) as e:
                problems.append(f"{where}: {e}")
                continue
            if same:
                state = "done"
            else:
                problems.append(f"{where}: target exists with DIFFERENT content — {tgt_s}")
                continue
        elif action == "csv2tsv":
            try:
                csv_to_tsv_bytes(src, args.encoding)          # fail now, not mid-apply
            except (ValueError, UnicodeDecodeError) as e:
                problems.append(f"{where}: {e} (try --encoding latin-1)")
                continue

        plan.append((action if state == "new" else "done", src, tgt, r.get("note") or ""))

    if len(sub_widths) > 1:
        warnings.append(f"mixed sub- zero-padding widths: {sorted(sub_widths)}")
    if len(ses_widths) > 1:
        warnings.append(f"mixed ses- zero-padding widths: {sorted(ses_widths)}")

    counts: dict[str, int] = {}
    for a, *_ in plan:
        counts[a] = counts.get(a, 0) + 1
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"# {mode} — {map_path}  ({len(rows)} rows)")
    print("  " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "  nothing to do")
    for w in warnings:
        print(f"  WARN  {w}")
    for p in problems:
        print(f"  ERROR {p}")

    if problems:
        print(f"\n{len(problems)} problem(s). Nothing written. Fix the map and re-run.")
        return 1
    if not args.apply:
        for a, src, tgt, note in plan:
            if a in ("copy", "csv2tsv", "copytree"):
                print(f"  {a:8} {src.relative_to(root)} -> {tgt.relative_to(root)}")
        print("\nDry run only. Re-run with --apply to write.")
        return 1 if warnings else 0

    log = map_path.parent / "apply_rename_map.log"
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    with log.open("a", encoding="utf-8") as lf:
        lf.write(f"\n## {stamp} apply {map_path}\n")
        for a, src, tgt, note in plan:
            if a not in ("copy", "csv2tsv", "copytree"):
                continue
            tgt.parent.mkdir(parents=True, exist_ok=True)
            if a == "copy":
                shutil.copy2(src, tgt)
                if sha(src) != sha(tgt):
                    raise SystemExit(f"checksum mismatch after copy: {tgt}")
            elif a == "csv2tsv":
                tgt.write_bytes(csv_to_tsv_bytes(src, args.encoding))
            else:
                shutil.copytree(src, tgt, ignore=shutil.ignore_patterns(*JUNK))
            lf.write(f"{a}\t{src.relative_to(root)}\t{tgt.relative_to(root)}\n")
            print(f"  {a:8} -> {tgt.relative_to(root)}")
    print(f"\nlog: {log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
