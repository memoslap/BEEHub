#!/usr/bin/env python3
"""
bids_repair.py — check (and optionally repair) a BEEHub project's bids_data/
tree against the BIDS specification.

    ./bids_repair.py MT FLOW OLM              # report only  (DEFAULT)
    ./bids_repair.py MT --apply               # perform the SAFE repairs
    ./bids_repair.py MT --apply --delimiter   # also add Delimiter to array columns

Design rules
------------
* **Dry-run is the default.** `--apply` must be explicit.
* **Nothing is ever deleted.** Files that should not be in the tree are MOVED to
  ``Projects/<CODE>/bids_repair_quarantine/`` with their relative path preserved.
* **`sourcedata/` is never touched.** It is outside the BIDS dataset root and holds
  the originals.
* **Judgement calls are reported, never auto-fixed.** Column renaming, subject-dir
  renaming and `dataset_description.json` content are left to a human, because each
  can silently break downstream analysis or belongs to another agent.

Spec basis (BIDS 1.11.1 "Common principles", tabular files section)
-------------------------------------------------------------------
Verified against the specification text, not from memory:

* Missing and non-applicable values MUST be coded as ``n/a``.
* Column names MUST NOT be blank and MUST NOT be duplicated within one TSV.
* snake_case with a lowercase first letter is RECOMMENDED, not required — so a
  name like ``mouse_resp.x`` is legal and is reported as INFO only.
* Tabs MUST be true tabs; string values containing tabs MUST be double-quoted.
* Numerical values MUST use ``.`` as the decimal separator.
* TSV files MUST be UTF-8.
* A data dictionary keys column descriptions at the TOP level by column name, and
  MAY additionally carry file-level metadata whose keys are not column names.
  (So a ``dropped_columns`` key is permissible; a ``{"columns": {...}}`` wrapper
  is not, because the column keys then are not at the top level.)
* ``Delimiter`` is the sanctioned field for a column whose cells are lists.
* A data type directory SHOULD NOT exist if it holds no files.
* Session-level metadata belongs in ``sub-<label>_sessions.tsv`` in the SUBJECT
  directory, with a compulsory ``session_id`` column — not in a per-run
  ``_session.json`` inside ``beh/``.
* Where metadata is identical across files it is RECOMMENDED to store it once
  higher in the hierarchy (Inheritance Principle) rather than duplicating it.

NOT verified by this tool: whether the official bids-validator emits warnings for
extra file-level keys. Run the real validator afterwards.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

csv.field_size_limit(500_000_000)  # trajectory cells can be enormous

# --------------------------------------------------------------------------- #
# Finding reporting
# --------------------------------------------------------------------------- #

MUST = "MUST"      # spec violation
SHOULD = "SHOULD"  # spec recommendation / house rule
INFO = "INFO"      # advisory only


@dataclass
class Finding:
    code: str
    level: str
    path: str
    message: str
    repairable: bool = False


@dataclass
class Report:
    code: str
    findings: list[Finding] = field(default_factory=list)
    repairs: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    def add(self, *a, **kw) -> None:
        self.findings.append(Finding(*a, **kw))


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    while p != p.parent:
        if (p / "Agent").is_dir() or (p / "Projects").is_dir():
            return p
        p = p.parent
    return start.resolve()


def quarantine(path: Path, bids_root: Path, project_root: Path,
               rep: Report, apply: bool, why: str) -> None:
    """Move a file out of the dataset instead of deleting it."""
    dest = project_root / "bids_repair_quarantine" / path.relative_to(bids_root)
    if apply:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        rep.repairs.append(f"quarantined {path.relative_to(bids_root)} ({why})")
    else:
        rep.repairs.append(f"[would quarantine] {path.relative_to(bids_root)} ({why})")


def read_tsv_rows(path: Path):
    """Yield (lineno, fields). Raises UnicodeDecodeError if not UTF-8."""
    with path.open(newline="", encoding="utf-8") as fh:
        for i, row in enumerate(csv.reader(fh, delimiter="\t"), start=1):
            yield i, row


def looks_like_array(cell: str) -> bool:
    c = cell.strip()
    return len(c) >= 2 and c[0] == "[" and c[-1] == "]"


def looks_like_comma_decimal(cell: str) -> bool:
    """'3,14' — a comma decimal separator. Excludes list-like cells."""
    c = cell.strip()
    if not c or looks_like_array(c) or c.count(",") != 1:
        return False
    a, b = c.split(",")
    return a.lstrip("+-").isdigit() and b.isdigit()


def is_snake_case(name: str) -> bool:
    return (name != "" and name[0].islower()
            and all(ch.islower() or ch.isdigit() or ch == "_" for ch in name))


# --------------------------------------------------------------------------- #
# Checks
# --------------------------------------------------------------------------- #

def check_tsv(path: Path, bids_root: Path, rep: Report,
              apply: bool, want_delimiter: bool) -> set[str]:
    """Check one TSV. Returns the set of columns whose cells look like arrays."""
    rel = str(path.relative_to(bids_root))
    array_cols: set[str] = set()

    try:
        rows = list(read_tsv_rows(path))
    except UnicodeDecodeError as e:
        rep.add("B011", MUST, rel, f"not valid UTF-8: {e}")
        return array_cols
    if not rows:
        rep.add("B015", MUST, rel, "file is empty (no header line)")
        return array_cols

    header = rows[0][1]
    n = len(header)

    # --- header MUSTs -----------------------------------------------------
    blanks = [i for i, c in enumerate(header) if c.strip() == ""]
    if blanks:
        rep.add("B002", MUST, rel,
                f"blank column name(s) at position(s) {blanks} — "
                "BIDS: column names MUST NOT be blank")
    dupes = {c for c in header if header.count(c) > 1 and c.strip()}
    if dupes:
        rep.add("B002", MUST, rel,
                f"duplicated column name(s) {sorted(dupes)} — "
                "BIDS: MUST NOT be duplicated within one file")

    for c in header:
        if c.strip() and not is_snake_case(c):
            rep.add("B008", INFO, rel,
                    f"column {c!r} is not snake_case — RECOMMENDED only, "
                    "not a violation; renaming may break analysis code")

    # --- body -------------------------------------------------------------
    empty_cells = 0
    ragged = []
    tabbed = 0
    comma_dec = set()
    for lineno, row in rows[1:]:
        if len(row) != n:
            ragged.append(lineno)
        for j, cell in enumerate(row):
            if cell == "":
                empty_cells += 1
            elif "\t" in cell:
                tabbed += 1
            elif looks_like_array(cell):
                if j < n:
                    array_cols.add(header[j])
            elif looks_like_comma_decimal(cell) and j < n:
                comma_dec.add(header[j])

    if ragged:
        rep.add("B013", MUST, rel,
                f"{len(ragged)} row(s) have a field count != header "
                f"(first at line {ragged[0]}) — an unescaped tab inside a value "
                "is the usual cause")
    if tabbed:
        rep.add("B013", MUST, rel, f"{tabbed} cell(s) contain a literal tab")
    if comma_dec:
        rep.add("B012", MUST, rel,
                f"column(s) {sorted(comma_dec)} appear to use ',' as decimal "
                "separator — BIDS requires '.'")
    if empty_cells:
        rep.add("B001", MUST, rel,
                f"{empty_cells} empty cell(s) — BIDS: missing/non-applicable "
                "values MUST be coded as 'n/a'", repairable=True)
        _repair_empty_cells(path, rep, bids_root, apply)

    return array_cols


def _repair_empty_cells(path: Path, rep: Report, bids_root: Path, apply: bool) -> None:
    rel = path.relative_to(bids_root)
    if not apply:
        rep.repairs.append(f"[would rewrite] {rel}: empty cells -> n/a")
        return
    tmp = path.with_suffix(path.suffix + ".repair_tmp")
    with path.open(newline="", encoding="utf-8") as fin, \
         tmp.open("w", newline="", encoding="utf-8") as fout:
        r = csv.reader(fin, delimiter="\t")
        w = csv.writer(fout, delimiter="\t", lineterminator="\n",
                       quoting=csv.QUOTE_MINIMAL)
        w.writerow(next(r))                       # header untouched
        for row in r:
            w.writerow(["n/a" if c == "" else c for c in row])
    tmp.replace(path)
    rep.repairs.append(f"rewrote {rel}: empty cells -> n/a")


def check_sidecar(path: Path, bids_root: Path, rep: Report, apply: bool) -> None:
    rel = str(path.relative_to(bids_root))
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        rep.add("B016", MUST, rel, f"unreadable JSON: {e}")
        return
    if not isinstance(obj, dict):
        rep.add("B016", MUST, rel, "sidecar is not a JSON object")
        return

    if "columns" in obj and isinstance(obj["columns"], dict):
        rep.add("B003", MUST, rel,
                "column descriptions are nested under a 'columns' key; BIDS keys "
                "them at the TOP level by column name", repairable=True)
        if apply:
            flat = dict(obj["columns"])
            for k, v in obj.items():
                if k != "columns":
                    flat[k] = v
            path.write_text(json.dumps(flat, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
            rep.repairs.append(f"flattened {path.relative_to(bids_root)}")
        else:
            rep.repairs.append(f"[would flatten] {path.relative_to(bids_root)}")

    # Key casing. BIDS names these fields Description / Units / Levels / Format;
    # the lowercase spellings are simply not the same field to a reader or tool.
    obj = json.loads(path.read_text(encoding="utf-8"))
    CASE = {"description": "Description", "units": "Units",
            "levels": "Levels", "format": "Format", "longname": "LongName"}
    fixed = 0
    for col, desc in obj.items():
        if not isinstance(desc, dict):
            continue
        for lower, proper in CASE.items():
            if lower in desc and proper not in desc:
                desc[proper] = desc.pop(lower)
                fixed += 1
    if fixed:
        rep.add("B014", SHOULD, rel,
                f"{fixed} metadata key(s) use lowercase spellings; BIDS names "
                "them Description / Units / Levels / Format", repairable=True)
        if apply:
            path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
            rep.repairs.append(f"corrected key casing in {path.relative_to(bids_root)}")
        else:
            rep.repairs.append(f"[would correct key casing in] {path.relative_to(bids_root)}")

    # Non-BIDS per-column keys that look like a hand-rolled type system.
    for col, desc in obj.items():
        if isinstance(desc, dict) and "type" in desc:
            rep.add("B017", INFO, rel,
                    f"column {col!r} carries a non-BIDS 'type' key. Harmless "
                    "file-level extra metadata, but Format/Delimiter express "
                    "this in spec terms. NOT removed automatically.")
            break


def check_session_json(path: Path, bids_root: Path, project_root: Path,
                       rep: Report, apply: bool) -> str | None:
    """`sub-X_ses-Y_session.json` inside beh/. Returns the ses- label."""
    rel = str(path.relative_to(bids_root))
    ses = None
    for part in path.name.split("_"):
        if part.startswith("ses-"):
            ses = part

    # Report what is actually inside, so the decision about where the content
    # should go is made on evidence rather than on the filename.
    keys: list[str] = []
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        keys = sorted(obj)
        if "repetitiontime" in {k.lower() for k in obj}:
            rep.add("B019", SHOULD, rel,
                    "carries a RepetitionTime field, which is an MRI acquisition "
                    "parameter with no meaning for behavioural data")
        if any(k[:1].islower() for k in obj):
            rep.add("B018", SHOULD, rel,
                    "has lowercase JSON keys; BIDS RECOMMENDS CamelCase")
    except Exception:
        pass

    rep.add("B005", MUST, rel,
            "'_session.json' is not a BIDS entity and will not be recognised. "
            f"Contents: {keys if keys else 'unreadable'}. If any of these are "
            "real per-session VARIABLES, they belong in a sub-<label>_sessions.tsv "
            "column; if they are constants or meaningless, the file just goes",
            repairable=True)
    quarantine(path, bids_root, project_root, rep, apply, "not a BIDS entity")
    return ses



# --------------------------------------------------------------------------- #
# Per-project driver
# --------------------------------------------------------------------------- #

def check_project(code: str, repo: Path, apply: bool, want_delimiter: bool) -> Report:
    rep = Report(code)
    project_root = repo / "Projects" / code
    bids_root = project_root / "bids_data"
    if not bids_root.is_dir():
        rep.add("B000", MUST, str(bids_root), "bids_data/ not found — skipped")
        return rep

    # --- dataset-level files ---------------------------------------------
    dd = bids_root / "dataset_description.json"
    if not dd.is_file():
        rep.add("B010", MUST, "dataset_description.json",
                "REQUIRED at the dataset root — owned by the Describe agent, "
                "not repaired here")
    else:
        try:
            o = json.loads(dd.read_text(encoding="utf-8"))
            for k in ("Name", "BIDSVersion"):
                if k not in o:
                    rep.add("B010", MUST, "dataset_description.json",
                            f"missing REQUIRED field {k!r}")
            if any(v == "TBD" for v in o.values() if isinstance(v, str)):
                rep.add("B020", SHOULD, "dataset_description.json",
                        "contains a 'TBD' value; omit the key instead")
        except Exception as e:
            rep.add("B010", MUST, "dataset_description.json", f"unreadable: {e}")

    if not (bids_root / "participants.tsv").is_file():
        rep.add("B021", SHOULD, "participants.tsv", "absent (RECOMMENDED)")

    # --- subject directories ---------------------------------------------
    array_cols_seen: set[str] = set()
    for sub_dir in sorted(p for p in bids_root.iterdir()
                          if p.is_dir() and p.name.startswith("sub-")):
        label = sub_dir.name[4:]
        if label.isdigit() and len(label) != 3:
            rep.add("B007", SHOULD, sub_dir.name,
                    f"subject label is {len(label)} digits; the BEEHub rule is "
                    "zero-padded to 3. NOT renamed automatically — a rename can "
                    "collide with an existing sub-0NN")

        sessions: list[str] = []
        for ses_dir in sorted(p for p in sub_dir.iterdir()
                              if p.is_dir() and p.name.startswith("ses-")):
            sessions.append(ses_dir.name)
            slabel = ses_dir.name[4:]
            if slabel.isdigit() and len(slabel) != 2:
                rep.add("B007", SHOULD, str(ses_dir.relative_to(bids_root)),
                        "session label is not zero-padded to 2 digits")

        for f in sorted(sub_dir.rglob("*")):
            if f.is_dir():
                continue
            rel = f.relative_to(bids_root)
            # Entity labels in the filename must match the directories it sits in.
            for ent, owner in (("sub-", sub_dir.name),
                               ("ses-", f.parent.parent.name)):
                got = next((p for p in f.name.split("_") if p.startswith(ent)), None)
                if got and owner.startswith(ent) and got != owner:
                    rep.add("B024", MUST, str(rel),
                            f"filename says {got!r} but the file sits in "
                            f"{owner!r}. NOT renamed automatically — which one "
                            "is correct is a question for the data owner")
            if f.suffix == ".tsv":
                array_cols_seen |= check_tsv(f, bids_root, rep, apply, want_delimiter)
            elif f.name.endswith("_session.json"):
                ses = check_session_json(f, bids_root, project_root, rep, apply)
                if ses and ses not in sessions:
                    sessions.append(ses)
            elif f.suffix == ".json":
                # Duplicate test FIRST: it compares this sidecar against the root
                # one, and flattening either side first would make them differ.
                if not _maybe_duplicate_sidecar(f, bids_root, project_root,
                                                rep, apply):
                    check_sidecar(f, bids_root, rep, apply)
            else:
                rep.add("B022", INFO, str(rel), "unexpected file type in bids_data/")

        if sessions and not (sub_dir / f"{sub_dir.name}_sessions.tsv").is_file():
            rep.add("B023", INFO, sub_dir.name,
                    f"{len(sessions)} sessions, no _sessions.tsv. This file is "
                    "OPTIONAL in BIDS and exists to record VARIABLES THAT CHANGE "
                    "BETWEEN SESSIONS (acq_time, order, condition). A file "
                    "containing only session_id restates the directory names and "
                    "is not worth adding. NOT written automatically")

    # --- root-level sidecars ---------------------------------------------
    # Checked AFTER the subject walk: the B004 duplicate test compares per-run
    # sidecars against the root one, so the root must not be reshaped first.
    for root_json in sorted(bids_root.glob("*.json")):
        if root_json.name == "dataset_description.json":
            continue
        check_sidecar(root_json, bids_root, rep, apply)

    # --- array columns without a Delimiter declaration --------------------
    declared: set[str] = set()
    for rj in bids_root.glob("task-*_beh.json"):
        try:
            o = json.loads(rj.read_text(encoding="utf-8"))
        except Exception:
            continue
        declared |= {k for k, v in o.items()
                     if isinstance(v, dict) and "Delimiter" in v}
    array_cols_seen -= declared

    if array_cols_seen:
        rep.add("B009", SHOULD, "task-*_beh.json",
                f"column(s) {sorted(array_cols_seen)} hold list-like values. BIDS "
                "provides the 'Delimiter' field for exactly this; declare it. "
                "(The values themselves are legal strings.)",
                repairable=want_delimiter)
        if want_delimiter:
            _add_delimiter(bids_root, array_cols_seen, rep, apply)
        else:
            rep.skipped.append("Delimiter declaration — pass --delimiter to add it")

    # --- empty directories ------------------------------------------------
    # Iterate to a fixpoint: removing sub-01/ses-02/beh makes sub-01/ses-02 empty
    # in turn, and a single pass over a pre-computed listing would miss that.
    # In dry-run there is no real removal, so simulate with a pending set.
    reported: set[Path] = set()
    while True:
        pending = set()
        for d in sorted((p for p in bids_root.rglob("*") if p.is_dir()),
                        key=lambda p: len(p.parts), reverse=True):
            if d in reported:
                continue
            children = [c for c in d.iterdir() if c not in reported]
            if children:
                continue
            pending.add(d)
            rep.add("B006", SHOULD, str(d.relative_to(bids_root)),
                    "empty directory — BIDS: a data type directory SHOULD NOT "
                    "exist if it holds no files", repairable=True)
            if apply:
                d.rmdir()
                rep.repairs.append(f"removed empty dir {d.relative_to(bids_root)}")
            else:
                rep.repairs.append(f"[would remove empty dir] {d.relative_to(bids_root)}")
        if not pending:
            break
        reported |= pending

    # --- stray files at the dataset root ----------------------------------
    ALLOWED_ROOT = {"dataset_description.json", "participants.tsv",
                    "participants.json", "README", "README.md", "CHANGES",
                    "LICENSE", "samples.tsv", "samples.json", ".bidsignore"}
    for f in sorted(p for p in bids_root.iterdir() if p.is_file()):
        if f.name in ALLOWED_ROOT or f.name.startswith("task-"):
            continue
        rep.add("B026", SHOULD, f.name,
                "unexpected file at the dataset root; validators MAY treat "
                "non-standard files as an error. Move it to code/ or the "
                "project level, or list it in .bidsignore")

    # --- participants.tsv sitting outside the dataset root ----------------
    if ((project_root / "participants.tsv").is_file()
            and not (bids_root / "participants.tsv").is_file()):
        rep.add("B028", MUST, "../participants.tsv",
                "participants.tsv is at the PROJECT level, outside bids_data/. "
                "BIDS places it at the dataset root, so nothing reading the "
                "dataset can see it. NOT moved automatically — check first "
                "whether anything references the current path")

    # --- excluded artefacts anywhere in the project -----------------------
    n_art = 0
    for p in project_root.rglob("*"):
        if "bids_repair_quarantine" in p.parts:
            continue
        if (p.name in ("Thumbs.db", "desktop.ini", "__pycache__")
                or p.suffix == ".pyc" or "(copy)" in p.name
                or p.name.startswith("~$")):
            n_art += 1
            if n_art <= 5:
                rep.add("B025", SHOULD, str(p.relative_to(project_root)),
                        "on the CLAUDE.md exclusion list; should not have been "
                        "migrated. NOT removed automatically")
    if n_art > 5:
        rep.add("B025", SHOULD, f"({n_art} total)",
                f"{n_art - 5} further excluded artefacts not listed individually")

    # --- root dictionary describing a suffix with no data files -----------
    for rj in sorted(bids_root.glob("task-*.json")):
        suffix = rj.stem.split("_")[-1]                    # 'beh' / 'events'
        if not any(bids_root.rglob(f"sub-*_{suffix}.tsv")):
            rep.add("B027", SHOULD, rj.name,
                    f"describes '_{suffix}.tsv' files, but the dataset contains "
                    "none. Either the data is missing or the dictionary is stale")

    return rep


def _maybe_duplicate_sidecar(f: Path, bids_root: Path, project_root: Path,
                             rep: Report, apply: bool) -> bool:
    """A per-run sidecar semantically identical to an inheritable root sidecar.

    Returns True if the file was (or would be) quarantined, so the caller can
    skip further checks on a file that is on its way out of the dataset.
    """
    if not f.name.endswith("_beh.json"):
        return False
    suffix = f.name.split("_")[-1]          # 'beh.json'
    for root_json in bids_root.glob(f"task-*_{suffix}"):
        try:
            a = json.loads(f.read_text(encoding="utf-8"))
            b = json.loads(root_json.read_text(encoding="utf-8"))
        except Exception:
            return False
        if a == b:
            rep.add("B004", SHOULD, str(f.relative_to(bids_root)),
                    f"identical to {root_json.name}; the Inheritance Principle "
                    "RECOMMENDS storing it once at the root", repairable=True)
            quarantine(f, bids_root, project_root, rep, apply,
                       "duplicate of root sidecar")
            return True
    return False


def _add_delimiter(bids_root: Path, cols: set[str], rep: Report, apply: bool) -> None:
    for root_json in sorted(bids_root.glob("task-*_beh.json")):
        try:
            obj = json.loads(root_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        changed = False
        for c in cols:
            if c in obj and isinstance(obj[c], dict) and "Delimiter" not in obj[c]:
                obj[c]["Delimiter"] = ","
                changed = True
        if not changed:
            continue
        if apply:
            root_json.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")
            rep.repairs.append(f"added Delimiter to {root_json.name}")
        else:
            rep.repairs.append(f"[would add Delimiter to] {root_json.name}")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #

def print_report(rep: Report, apply: bool) -> int:
    print(f"\n{'=' * 72}\n  {rep.code}\n{'=' * 72}")
    if not rep.findings:
        print("  no findings")
    order = {MUST: 0, SHOULD: 1, INFO: 2}
    for f in sorted(rep.findings, key=lambda x: (order[x.level], x.code, x.path)):
        mark = "*" if f.repairable else " "
        print(f"  {f.level:<6}{mark} [{f.code}] {f.path}\n           {f.message}")
    if rep.repairs:
        print(f"\n  --- repairs ({'APPLIED' if apply else 'dry run'}) ---")
        for r in rep.repairs[:200]:
            print(f"    {r}")
        if len(rep.repairs) > 200:
            print(f"    ... and {len(rep.repairs) - 200} more")
    for s in rep.skipped:
        print(f"  skipped: {s}")
    return sum(1 for f in rep.findings if f.level == MUST)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("codes", nargs="+", help="project codes, e.g. MT FLOW OLM")
    ap.add_argument("--apply", action="store_true",
                    help="perform the safe repairs (default: report only)")
    ap.add_argument("--delimiter", action="store_true",
                    help="also declare Delimiter for list-valued columns")
    ap.add_argument("--repo", type=Path, default=None, help="repository root")
    args = ap.parse_args()

    repo = args.repo.resolve() if args.repo else find_repo_root(Path.cwd())
    print(f"repo root: {repo}")
    print(f"mode     : {'APPLY' if args.apply else 'DRY RUN (nothing written)'}")

    must_total = 0
    seen_codes: set[str] = set()
    for code in args.codes:
        rep = check_project(code, repo, args.apply, args.delimiter)
        seen_codes |= {f.code for f in rep.findings}
        must_total += print_report(rep, args.apply)

    print(f"\n{'=' * 72}")
    print(f"  MUST-level findings across all projects: {must_total}")
    if not args.apply:
        print("  Nothing was written. Re-run with --apply to repair.")
    # Only mention what this run actually found. Printing the full list
    # unconditionally reads like a to-do list rather than a refusal.
    notes = {
        "B008": "column renaming (snake_case is RECOMMENDED, not required)",
        "B007": "subject/session directory renaming (collision risk)",
        "B024": "entity/directory label mismatches (which label is right is unknown)",
        "B010": "dataset_description.json content (owned by the Describe agent)",
        "B025": "removal of excluded artefacts (Thumbs.db, *.pyc, '(copy)' files)",
        "B028": "moving a misplaced participants.tsv (may be referenced elsewhere)",
    }
    hit = [notes[c] for c in notes if c in seen_codes]
    if hit:
        print("  Reported but NOT changed by this tool (human judgement required):")
        for h in hit:
            print(f"    - {h}")
    print("  Run the official bids-validator afterwards; this tool is not it.")
    return 1 if must_total else 0


if __name__ == "__main__":
    sys.exit(main())
