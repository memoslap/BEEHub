#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "pyyaml"]
# ///
"""
reproduce_check.py — does this code, on this data, produce the paper's numbers?

Two subcommands, deliberately separate:

    run      execute the analysis scripts in an isolated copy and record what
             happened (exit code, duration, which output files appeared)

    compare  check the numbers in those outputs against claims extracted from
             the paper, within a stated tolerance

Neither answers "does it reproduce" on its own. `run` answers "does it
execute". `compare` answers "do the numbers we mapped match". Claims nobody
has mapped to an output are reported as UNRESOLVED, never as passing.

Usage
-----
    uv run Agent/tools/reproduce_check.py run "Projects/<CODE>/code" --workdir /tmp/repro
    uv run reproduce_check.py compare claims.yaml /tmp/repro/run
    uv run reproduce_check.py compare claims.yaml /tmp/repro/run --json

Safety
------
`run` copies the project to a scratch directory and executes there. It never
touches the original. It will still execute untrusted code on your machine —
read the scripts first, and run in a container if you did not write them.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import time

import pandas as pd
import yaml

STATS = {
    "mean": lambda s: s.mean(),
    "sd": lambda s: s.std(ddof=1),
    "median": lambda s: s.median(),
    "min": lambda s: s.min(),
    "max": lambda s: s.max(),
    "sum": lambda s: s.sum(),
    "n": lambda s: s.notna().sum(),
    "nunique": lambda s: s.nunique(),
}

INTERPRETERS = {".r": ["Rscript"], ".py": [sys.executable]}


# ---------------------------------------------------------------- run


def snapshot(root: pathlib.Path) -> dict[str, float]:
    return {str(p.relative_to(root)): p.stat().st_mtime
            for p in root.rglob("*") if p.is_file()}


def cmd_run(args: argparse.Namespace) -> int:
    src = pathlib.Path(args.project)
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")

    work = pathlib.Path(args.workdir) / "run"
    if work.exists():
        shutil.rmtree(work)
    work.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, work)
    print(f"copied to {work} (original untouched)\n")

    scripts = sorted(p for p in work.rglob("*")
                     if p.suffix.lower() in INTERPRETERS
                     and "__pycache__" not in p.parts)
    if args.only:
        wanted = set(args.only)
        scripts = [p for p in scripts if p.name in wanted]
    if not scripts:
        sys.exit("no .R or .py scripts found")

    # Numbered filenames ("1. compute.R") sort into the intended run order.
    print("run order:")
    for i, s in enumerate(scripts, 1):
        print(f"  {i}. {s.relative_to(work)}")
    print()

    results = []
    for s in scripts:
        interp = INTERPRETERS[s.suffix.lower()]
        if not shutil.which(interp[0]):
            print(f"SKIP {s.name} — {interp[0]} not on PATH")
            results.append({"script": str(s.relative_to(work)),
                            "status": "SKIPPED",
                            "reason": f"{interp[0]} not installed"})
            continue

        before = snapshot(work)
        print(f"RUN  {s.relative_to(work)} ... ", end="", flush=True)
        t0 = time.monotonic()
        try:
            proc = subprocess.run(interp + [s.name], cwd=s.parent,
                                  capture_output=True, text=True,
                                  timeout=args.timeout)
            rc, out, err = proc.returncode, proc.stdout, proc.stderr
            status = "OK" if rc == 0 else "FAILED"
        except subprocess.TimeoutExpired:
            rc, out, err, status = None, "", "", "TIMEOUT"
        dt = time.monotonic() - t0

        after = snapshot(work)
        produced = sorted(set(after) - set(before)) + \
            sorted(k for k in set(after) & set(before) if after[k] != before[k])

        print(f"{status} ({dt:.1f}s, {len(produced)} file(s) written)")
        if status == "FAILED" and err:
            print("     " + err.strip().splitlines()[-1][:200])

        results.append({"script": str(s.relative_to(work)), "status": status,
                        "returncode": rc, "seconds": round(dt, 1),
                        "produced": produced,
                        "stderr_tail": err.strip()[-2000:] if err else ""})

    log = work.parent / "run_log.json"
    log.write_text(json.dumps({"source": str(src), "workdir": str(work),
                               "results": results}, indent=2))
    print(f"\nlog: {log}")

    failed = [r for r in results if r["status"] in ("FAILED", "TIMEOUT")]
    skipped = [r for r in results if r["status"] == "SKIPPED"]
    print(f"{len(results)} script(s): {len(results)-len(failed)-len(skipped)} ok, "
          f"{len(failed)} failed, {len(skipped)} skipped")
    return 1 if failed else 0


# ------------------------------------------------------------ compare


def load_value(results: pathlib.Path, src: dict) -> tuple[float | None, str]:
    """Compute one number from a result file. Returns (value, note)."""
    path = results / src["file"]
    if not path.exists():
        hits = list(results.rglob(src["file"]))
        if not hits:
            return None, f"{src['file']} not produced"
        path = hits[0]

    sep = "\t" if path.suffix.lower() in (".tsv", ".txt") else ","
    try:
        df = pd.read_csv(path, sep=sep)
    except Exception as e:
        return None, f"could not read {path.name}: {e}"

    stat = src.get("stat", "mean")
    if stat == "nrow":
        return float(len(df)), ""
    if stat not in STATS:
        return None, f"unknown stat '{stat}'"

    col = src.get("column")
    if col is None:
        return None, "no column given"
    if col not in df.columns:
        return None, f"column '{col}' not in {path.name} " \
                     f"(has: {', '.join(map(str, df.columns[:8]))})"

    series = pd.to_numeric(df[col], errors="coerce")
    if "where" in src:                      # e.g. where: {trial_type: go}
        for k, v in src["where"].items():
            if k not in df.columns:
                return None, f"filter column '{k}' not in {path.name}"
            series = series[df[k] == v]
    if series.notna().sum() == 0:
        return None, f"no numeric values in '{col}' after filtering"

    return float(STATS[stat](series)) * float(src.get("scale", 1)), ""


def cmd_compare(args: argparse.Namespace) -> int:
    spec = yaml.safe_load(pathlib.Path(args.claims).read_text())
    results = pathlib.Path(args.results)
    if not results.is_dir():
        sys.exit(f"not a directory: {results}")

    rows = []
    for c in spec.get("claims", []):
        row = {"id": c.get("id", "?"), "text": c.get("text", ""),
               "paper": c.get("value"), "got": None, "status": "", "note": ""}

        if "source" not in c:
            row["status"] = "UNRESOLVED"
            row["note"] = "no output mapped to this claim yet"
        else:
            got, note = load_value(results, c["source"])
            row["got"], row["note"] = got, note
            if got is None:
                row["status"] = "MISSING"
            else:
                tol = float(c.get("tolerance", 0))
                row["status"] = "MATCH" if abs(got - float(c["value"])) <= tol \
                    else "MISMATCH"
        rows.append(row)

    counts = {s: sum(1 for r in rows if r["status"] == s)
              for s in ("MATCH", "MISMATCH", "MISSING", "UNRESOLVED")}

    if args.json:
        print(json.dumps({"counts": counts, "claims": rows}, indent=2))
    else:
        print(f"# Reproduction check — {spec.get('paper', args.claims)}\n")
        print(f"{len(rows)} claim(s): {counts['MATCH']} match, "
              f"{counts['MISMATCH']} mismatch, {counts['MISSING']} missing, "
              f"{counts['UNRESOLVED']} unresolved\n")
        for r in rows:
            got = "—" if r["got"] is None else f"{r['got']:.4g}"
            print(f"- **{r['status']}** `{r['id']}` — paper {r['paper']}, got {got}")
            if r["text"]:
                print(f"  - {r['text']}")
            if r["note"]:
                print(f"  - {r['note']}")
        if counts["UNRESOLVED"]:
            print("\nUnresolved claims are NOT passing. Map each to a "
                  "`source:` block or state why it cannot be checked.")

    return 1 if counts["MISMATCH"] or counts["MISSING"] or counts["UNRESOLVED"] else 0


# ---------------------------------------------------------------- cli


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="execute scripts in an isolated copy")
    r.add_argument("project")
    r.add_argument("--workdir", default="/tmp/repro")
    r.add_argument("--timeout", type=int, default=3600, help="per script, seconds")
    r.add_argument("--only", nargs="+", metavar="NAME", help="run only these filenames")
    r.set_defaults(func=cmd_run)

    c = sub.add_parser("compare", help="check outputs against paper claims")
    c.add_argument("claims", help="YAML written by the paper-claims agent")
    c.add_argument("results", help="directory produced by `run`")
    c.add_argument("--json", action="store_true")
    c.set_defaults(func=cmd_compare)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
