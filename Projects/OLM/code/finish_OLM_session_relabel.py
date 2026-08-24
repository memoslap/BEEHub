#!/usr/bin/env python3
"""
finish_OLM_session_relabel.py — complete the half-done ses-3/ses-4 -> ses-1/ses-2
relabel in Projects/OLM/raw_logs/, and pad the labels to match bids_data/.

    ./finish_OLM_session_relabel.py            # dry run (DEFAULT)
    ./finish_OLM_session_relabel.py --apply

What is currently on disk
-------------------------
    raw_logs/sub-001/ses-1/sub-001_ses-3_task-OLM_acq-1_beh.log
                     ^^^^^          ^^^^^
                     renamed        NOT renamed

The directories were relabelled; the filenames inside them were not. Separately,
the directories use ses-1/ses-2 while bids_data/ uses ses-01/ses-02, and mixing
padded and unpadded session labels in one dataset is forbidden by CLAUDE.md.

What this script does
---------------------
    directory  ses-1 -> ses-01        filename  ses-3 -> ses-01
               ses-2 -> ses-02                  ses-4 -> ses-02

acq-1/acq-2 is NOT touched. It splits 10/10 within *both* sessions, so it encodes
something orthogonal to session order and no rename should disturb it.

Safety
------
* Dry run is the default; --apply must be explicit.
* **The mapping is re-derived and re-verified from disk before anything moves.**
  This script does not trust the analysis that motivated it. If a single file
  contradicts the expected pairing, it aborts having changed NOTHING — a partly
  applied rename is far worse than none, because afterwards you can no longer
  tell which files were already correct.
* Nothing is deleted. Renames use `git mv` when the file is tracked.
* Idempotent: names already in the target form are counted and skipped.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# Directory label -> canonical label.
DIR_MAP = {"ses-1": "ses-01", "ses-2": "ses-02",
           "ses-01": "ses-01", "ses-02": "ses-02"}

# The OLD filename label expected inside each canonical session directory.
# ses-01 was formerly ses-3; ses-02 was formerly ses-4.
EXPECTED_OLD = {"ses-01": "ses-3", "ses-02": "ses-4"}

SES_RE = re.compile(r"_(ses-\d+)_")


def git_mv(src: Path, dst: Path, repo: Path) -> None:
    """git mv if tracked, plain rename otherwise. Never overwrites."""
    if dst.exists():
        raise FileExistsError(f"refusing to overwrite existing {dst}")
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(src)],
        cwd=repo, capture_output=True).returncode == 0
    if tracked:
        subprocess.run(["git", "mv", str(src), str(dst)], cwd=repo, check=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="perform the renames")
    ap.add_argument("--repo", type=Path, default=None)
    args = ap.parse_args()

    repo = args.repo.resolve() if args.repo else Path.cwd()
    while not (repo / "Projects").is_dir() and repo != repo.parent:
        repo = repo.parent
    raw_logs = repo / "Projects" / "OLM" / "raw_logs"
    if not raw_logs.is_dir():
        print(f"ERROR: {raw_logs} not found", file=sys.stderr)
        return 2

    print(f"repo    : {repo}")
    print(f"raw_logs: {raw_logs}")
    print(f"mode    : {'APPLY' if args.apply else 'DRY RUN (nothing written)'}\n")

    # ---------------- pass 1: verify, change nothing ----------------------
    file_moves: list[tuple[Path, Path]] = []
    dir_moves: list[tuple[Path, Path]] = []
    already = 0
    problems: list[str] = []

    for sub_dir in sorted(p for p in raw_logs.iterdir()
                          if p.is_dir() and p.name.startswith("sub-")):
        for ses_dir in sorted(p for p in sub_dir.iterdir() if p.is_dir()):
            canon = DIR_MAP.get(ses_dir.name)
            if canon is None:
                problems.append(f"{ses_dir.relative_to(repo)}: unknown session "
                                f"directory label {ses_dir.name!r}")
                continue
            old_label = EXPECTED_OLD[canon]

            for f in sorted(ses_dir.iterdir()):
                if f.is_dir():
                    problems.append(f"{f.relative_to(repo)}: unexpected subdirectory")
                    continue
                rel = f.relative_to(repo)

                if not f.name.startswith(sub_dir.name + "_"):
                    problems.append(f"{rel}: filename subject label does not "
                                    f"match directory {sub_dir.name!r}")
                    continue

                m = SES_RE.search(f.name)
                if not m:
                    problems.append(f"{rel}: no ses- label in filename")
                    continue
                found = m.group(1)

                if found == canon:
                    already += 1
                    continue
                if found != old_label:
                    problems.append(
                        f"{rel}: sits in {ses_dir.name!r} (canonical {canon!r}) "
                        f"so its label should be {old_label!r} or {canon!r}, "
                        f"but it is {found!r} — the mapping does not hold here")
                    continue

                file_moves.append((f, f.with_name(
                    f.name.replace(f"_{found}_", f"_{canon}_", 1))))

            if ses_dir.name != canon:
                dir_moves.append((ses_dir, ses_dir.with_name(canon)))

    print(f"files already correct   : {already}")
    print(f"files to rename         : {len(file_moves)}")
    print(f"directories to rename   : {len(dir_moves)}")
    print(f"problems                : {len(problems)}\n")

    if problems:
        print("ABORTING — nothing was changed. Resolve these first:\n")
        for p in problems:
            print(f"  ! {p}")
        return 1

    for src, dst in file_moves[:6]:
        print(f"  {src.name}\n    -> {dst.name}")
    if len(file_moves) > 6:
        print(f"  ... and {len(file_moves) - 6} more files")
    for src, dst in dir_moves[:4]:
        print(f"  DIR {src.relative_to(raw_logs)} -> {dst.name}")
    if len(dir_moves) > 4:
        print(f"  ... and {len(dir_moves) - 4} more directories")

    if not args.apply:
        print("\nDry run. Re-run with --apply to perform the renames.")
        return 0

    # ---------------- pass 2: apply, files before directories -------------
    # Files first: renaming the directory first would invalidate every path
    # collected above.
    for src, dst in file_moves:
        git_mv(src, dst, repo)
    for src, dst in dir_moves:
        git_mv(src, dst, repo)

    print(f"\nRenamed {len(file_moves)} file(s) and {len(dir_moves)} directory(ies).")
    print("Verify:")
    print("  find Projects/OLM/raw_logs -name '*ses-3*' -o -name '*ses-4*'   # must be empty")
    print("  find Projects/OLM/raw_logs -type d -name 'ses-[0-9]'            # must be empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
