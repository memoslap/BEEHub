#!/usr/bin/env python3
"""
run_derivation.py — run a project's declared derivation scripts under the
BEEHub contract, and fail loudly on anything that breaks it. Generic.

    ./Agent/tools/run_derivation.py <CODE> --dry-run
    ./Agent/tools/run_derivation.py <CODE>
    ./Agent/tools/run_derivation.py <CODE> --only <name>

Reads Projects/<CODE>/code/derivations.json — a list written by the
Data-Description agent:

    [
      {
        "name":        "meanrt",
        "script":      "code/summarise_rt.R",
        "input":       "bids_data",
        "output":      "derivatives/meanrt",
        "params":      "code/meanrt_params.json",
        "output_glob": "sub-*/ses-*/beh/*_desc-meanrt_beh.tsv"
      }
    ]

All paths are relative to Projects/<CODE>/. `params` is optional.

Each script is called exactly as the contract says:

    <interpreter> <script> --input <abs> --output <abs> [--params <abs>]

Fails (exit 1) when a script
  * exits non-zero,
  * modifies or deletes any file that existed under --input before it ran,
  * exits 0 but the output_glob matches no file it created or changed.

Output of every run is appended to Projects/<CODE>/code/derivation.log.
Exit: 0 all passed, 1 a derivation failed, 2 usage/setup error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import shutil
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from beehub_root import add_root_arg, find_root  # noqa: E402

INTERPRETERS = {".r": "Rscript", ".py": sys.executable}


def snapshot(d: pathlib.Path) -> dict[pathlib.Path, tuple[int, int]]:
    if not d.exists():
        return {}
    return {p: (p.stat().st_size, p.stat().st_mtime_ns)
            for p in d.rglob("*") if p.is_file()}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("code", help="project code, e.g. the folder name under Projects/")
    ap.add_argument("--dry-run", action="store_true", help="print commands, run nothing")
    ap.add_argument("--only", metavar="NAME", help="run one derivation by name")
    ap.add_argument("--timeout", type=int, default=6 * 3600, help="seconds per script")
    add_root_arg(ap)
    args = ap.parse_args()

    proj = find_root(None, args.root) / "Projects" / args.code
    decl = proj / "code" / "derivations.json"
    if not decl.is_file():
        print(f"❌ {decl} not found — the Data-Description agent writes it.", file=sys.stderr)
        return 2
    try:
        derivs = json.loads(decl.read_text(encoding="utf-8"))
        assert isinstance(derivs, list) and derivs
    except (json.JSONDecodeError, AssertionError):
        print(f"❌ {decl} must be a non-empty JSON list", file=sys.stderr)
        return 2
    if args.only:
        derivs = [d for d in derivs if d.get("name") == args.only]
        if not derivs:
            print(f"❌ no derivation named '{args.only}'", file=sys.stderr)
            return 2

    log = proj / "code" / "derivation.log"
    failed = 0
    for d in derivs:
        name = d.get("name", "?")
        missing = [k for k in ("name", "script", "input", "output", "output_glob") if not d.get(k)]
        if missing:
            print(f"❌ {name}: missing keys {missing}")
            failed += 1
            continue

        script = (proj / d["script"]).resolve()
        inp = (proj / d["input"]).resolve()
        out = (proj / d["output"]).resolve()
        params = (proj / d["params"]).resolve() if d.get("params") else None

        interp = INTERPRETERS.get(script.suffix.lower())
        errs = []
        if not script.is_file():
            errs.append(f"script not found: {d['script']}")
        if interp is None:
            errs.append(f"no interpreter known for '{script.suffix}'")
        elif not shutil.which(interp):
            errs.append(f"{interp} not on PATH")
        if not inp.is_dir():
            errs.append(f"input dir not found: {d['input']}")
        if params and not params.is_file():
            errs.append(f"params file not found: {d['params']}")
        if errs:
            print(f"❌ {name}: " + "; ".join(errs))
            failed += 1
            continue

        cmd = [interp, str(script), "--input", str(inp), "--output", str(out)]
        if params:
            cmd += ["--params", str(params)]
        print(f"── {name}\n   {' '.join(cmd)}")
        if args.dry_run:
            continue

        out.mkdir(parents=True, exist_ok=True)
        before_in, before_out = snapshot(inp), snapshot(out)
        t0 = dt.datetime.now(dt.timezone.utc)
        try:
            proc = subprocess.run(cmd, cwd=script.parent, capture_output=True,
                                  text=True, timeout=args.timeout)
            rc, so, se = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            rc, so, se = None, "", f"timed out after {args.timeout}s"
        secs = (dt.datetime.now(dt.timezone.utc) - t0).total_seconds()

        after_in, after_out = snapshot(inp), snapshot(out)
        # Files the script itself wrote may legitimately sit under --input when
        # output is nested inside it; only PRE-EXISTING input files are protected.
        touched_in = sorted(str(p.relative_to(proj)) for p, sig in before_in.items()
                            if after_in.get(p) != sig)
        produced = [p for p in out.glob(d["output_glob"])
                    if p.is_file() and before_out.get(p) != after_out.get(p)]

        problems = []
        if rc != 0:
            problems.append(f"exit {rc}")
        if touched_in:
            problems.append(f"modified/deleted {len(touched_in)} existing input file(s): "
                            + ", ".join(touched_in[:5]) + (" …" if len(touched_in) > 5 else ""))
        if rc == 0 and not produced:
            problems.append(f"exited 0 but wrote nothing matching {d['output_glob']}")

        status = "FAILED" if problems else "OK"
        print(f"   {status} in {secs:.1f}s — {len(produced)} output file(s)"
              + ("" if not problems else "\n   " + "\n   ".join(problems)))
        if problems:
            failed += 1

        with log.open("a", encoding="utf-8") as lf:
            lf.write(f"\n## {t0.isoformat(timespec='seconds')} {name} {status} "
                     f"({secs:.1f}s, {len(produced)} files)\n$ {' '.join(cmd)}\n")
            for p in problems:
                lf.write(f"! {p}\n")
            if so.strip():
                lf.write("--- stdout (tail)\n" + so[-4000:] + "\n")
            if se.strip():
                lf.write("--- stderr (tail)\n" + se[-4000:] + "\n")

    if not args.dry_run:
        print(f"\nlog: {log}")
    print(f"{len(derivs)} derivation(s), {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
