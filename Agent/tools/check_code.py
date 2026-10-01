#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["ruff"]
# ///
"""
check_code.py — static check of inherited R and Python analysis scripts.

Answers three questions about a folder of code before it enters BEEHub:
  1. Does it parse?                     (ERROR — it cannot run at all)
  2. Will it run somewhere else?        (WARN  — absolute paths, missing inputs)
  3. What does it need?                 (INFO  — declared dependencies)

Usage
-----
    uv run Agent/tools/check_code.py "Projects/<CODE>/code"
    uv run Agent/tools/check_code.py "Projects/<CODE>/code" --json > report.json

Exit code is 0 when no ERROR and no WARN were found, 1 otherwise, so it can
gate a pipeline step.

Requires no setup beyond uv. R syntax checking additionally needs Rscript on
PATH; without it R files are still checked for paths, inputs and libraries,
and the skipped parse is reported explicitly rather than silently passed.
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import shutil
import subprocess
import sys

# Absolute or user-home paths: the single most common reason inherited
# research code fails on another machine.
ABS_PATH = re.compile(
    r"""["']\s*(?:[A-Za-z]:[\\/]|/(?:home|Users|media|mnt|data)/|~/)[^"']*["']"""
)
R_SETWD = re.compile(r"\bsetwd\s*\(")

# Data files the script reads. Captures the quoted argument.
PY_READS = re.compile(
    r"""(?:open|read_csv|read_excel|read_table|read_tsv|np\.load|loadtxt)\s*\(\s*["']([^"']+)["']"""
)
R_READS = re.compile(
    r"""(?:read\.csv|read_csv|read\.table|read_excel|read_xlsx|fread|load|source)\s*\(\s*["']([^"']+)["']"""
)

PY_IMPORT = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][\w]*)", re.M)
R_LIBRARY = re.compile(r"""(?:library|require)\s*\(\s*["']?([A-Za-z][\w.]*)["']?\s*\)""")


def finding(sev: str, path: pathlib.Path, line: int | None, msg: str) -> dict:
    return {"severity": sev, "file": str(path), "line": line, "message": msg}


def read_text(path: pathlib.Path) -> tuple[str | None, list[dict]]:
    """Return decoded text, plus a finding if the file is not valid UTF-8."""
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8"), []
    except UnicodeDecodeError as e:
        # German research code is frequently latin-1. Readable, but it will
        # corrupt umlauts if anything downstream assumes UTF-8.
        return raw.decode("latin-1"), [
            finding("WARN", path, None,
                    f"not valid UTF-8 ({e.reason} at byte {e.start}); "
                    "read as latin-1 — re-encode before converting")
        ]


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def check_common(path: pathlib.Path, text: str, reads: re.Pattern,
                 deps: re.Pattern) -> tuple[list[dict], list[str]]:
    out: list[dict] = []

    for m in ABS_PATH.finditer(text):
        out.append(finding("WARN", path, line_of(text, m.start()),
                           f"absolute path {m.group(0).strip()} — will not "
                           "resolve on another machine"))

    for m in reads.finditer(text):
        ref = m.group(1)
        if ref.startswith(("http://", "https://")) or "{" in ref or "%s" in ref:
            continue  # URL or built at runtime — cannot check statically
        target = (path.parent / ref)
        if not target.exists():
            out.append(finding("WARN", path, line_of(text, m.start()),
                               f"reads '{ref}' — not found relative to this file"))

    found = sorted({m.group(1) for m in deps.finditer(text)})
    return out, found


def check_python(path: pathlib.Path) -> tuple[list[dict], list[str]]:
    text, out = read_text(path)
    if text is None:
        return out, []

    try:
        ast.parse(text, filename=str(path))
    except SyntaxError as e:
        # Do not run ruff on a file that does not parse; the output is noise.
        out.append(finding("ERROR", path, e.lineno, f"syntax error: {e.msg}"))
        common, deps = check_common(path, text, PY_READS, PY_IMPORT)
        return out + common, deps

    if shutil.which("ruff"):
        proc = subprocess.run(
            ["ruff", "check", "--select", "E9,F", "--output-format", "json",
             "--no-cache", str(path)],
            capture_output=True, text=True,
        )
        try:
            for item in json.loads(proc.stdout or "[]"):
                out.append(finding("WARN", path,
                                   (item.get("location") or {}).get("row"),
                                   f"{item.get('code')}: {item.get('message')}"))
        except json.JSONDecodeError:
            out.append(finding("INFO", path, None, "ruff produced no parseable output"))
    else:
        out.append(finding("INFO", path, None, "ruff unavailable — undefined-name check skipped"))

    common, deps = check_common(path, text, PY_READS, PY_IMPORT)
    return out + common, deps


def check_r(path: pathlib.Path) -> tuple[list[dict], list[str]]:
    text, out = read_text(path)
    if text is None:
        return out, []

    if shutil.which("Rscript"):
        proc = subprocess.run(
            ["Rscript", "-e",
             f'tryCatch(invisible(parse("{path}")), error=function(e) '
             'stop(conditionMessage(e)))'],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            out.append(finding("ERROR", path, None,
                               f"syntax error: {proc.stderr.strip().splitlines()[-1]}"))
    else:
        out.append(finding("INFO", path, None,
                           "Rscript unavailable — R syntax NOT verified"))

    for m in R_SETWD.finditer(text):
        out.append(finding("WARN", path, line_of(text, m.start()),
                           "setwd() — makes the script depend on one machine's layout"))

    common, deps = check_common(path, text, R_READS, R_LIBRARY)
    return out + common, deps


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="file or folder to check")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    root = pathlib.Path(args.target)
    if not root.exists():
        sys.exit(f"no such path: {root}")

    files = [root] if root.is_file() else sorted(
        p for p in root.rglob("*")
        if p.suffix.lower() in {".py", ".r"} and "__pycache__" not in p.parts
    )
    if not files:
        sys.exit(f"no .py or .R files under {root}")

    findings: list[dict] = []
    deps: dict[str, list[str]] = {}
    for f in files:
        got, d = check_python(f) if f.suffix.lower() == ".py" else check_r(f)
        findings.extend(got)
        if d:
            deps[str(f)] = d

    counts = {s: sum(1 for x in findings if x["severity"] == s)
              for s in ("ERROR", "WARN", "INFO")}

    if args.json:
        print(json.dumps({"files": [str(f) for f in files], "counts": counts,
                          "dependencies": deps, "findings": findings}, indent=2))
    else:
        print(f"# Code check — {root}\n")
        print(f"{len(files)} file(s): "
              f"{counts['ERROR']} error, {counts['WARN']} warning, {counts['INFO']} note\n")
        for f in files:
            mine = [x for x in findings if x["file"] == str(f)]
            print(f"## {f}")
            if not mine:
                print("- OK\n")
                continue
            for x in sorted(mine, key=lambda x: (x["line"] or 0)):
                loc = f":{x['line']}" if x["line"] else ""
                print(f"- **{x['severity']}**{loc} — {x['message']}")
            print()
        if deps:
            print("## Dependencies referenced\n")
            for f, d in deps.items():
                print(f"- `{f}`: {', '.join(d)}")

    sys.exit(1 if counts["ERROR"] or counts["WARN"] else 0)


if __name__ == "__main__":
    main()
