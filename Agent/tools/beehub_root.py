"""
beehub_root.py — one way to find the BEEHub repository root. Shared by every
tool in Agent/tools/ so they cannot disagree about where the repo is.

Why this exists: the tools originally each walked up looking for a directory
holding BOTH Agent/ and Projects/. That breaks the moment the agent tooling
lives somewhere other than the repo root (e.g. extracted into a subfolder),
because no ancestor of Convert/ then has both — and it fails with a message
about "repo root" that does not say what to do.

Resolution order, first hit wins:

  1. an explicit --root argument, if the tool offers one
  2. $BEEHUB_ROOT
  3. `git rev-parse --show-toplevel` — the same root OpenCode uses as its
     project root, so relative paths in opencode.json and in agent
     instructions mean the same thing here
  4. walking up from the starting path for a directory containing Projects/
  5. walking up from the current directory for the same

A candidate is accepted when it contains `Projects/`. `Agent/` is NOT required:
the tools need the data tree, not their own location, and requiring both is
what made this brittle.
"""

from __future__ import annotations

import os
import pathlib
import subprocess

__all__ = ["find_root", "add_root_arg"]

MARKER = "Projects"


def _walk_up(start: pathlib.Path) -> pathlib.Path | None:
    p = start.resolve()
    if p.is_file():
        p = p.parent
    while True:
        if (p / MARKER).is_dir():
            return p
        if p == p.parent:
            return None
        p = p.parent


def _git_root(start: pathlib.Path) -> pathlib.Path | None:
    d = start.resolve()
    if d.is_file():
        d = d.parent
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=d,
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    p = pathlib.Path(out.stdout.strip())
    return p if (p / MARKER).is_dir() else None


def find_root(start: pathlib.Path | str | None = None,
              explicit: pathlib.Path | str | None = None) -> pathlib.Path:
    """Return the repo root, or exit with a message saying how to fix it."""
    tried: list[str] = []

    if explicit:
        p = pathlib.Path(explicit).expanduser().resolve()
        if (p / MARKER).is_dir():
            return p
        raise SystemExit(f"--root {p} does not contain {MARKER}/")

    env = os.environ.get("BEEHUB_ROOT")
    if env:
        p = pathlib.Path(env).expanduser().resolve()
        if (p / MARKER).is_dir():
            return p
        tried.append(f"$BEEHUB_ROOT={p} (no {MARKER}/ there)")

    begin = pathlib.Path(start) if start else pathlib.Path.cwd()

    for name, cand in (("git root", _git_root(begin)),
                       ("walking up from the given path", _walk_up(begin)),
                       ("walking up from the current directory",
                        _walk_up(pathlib.Path.cwd()))):
        if cand:
            return cand
        tried.append(name)

    raise SystemExit(
        "cannot locate the BEEHub repository root.\n"
        f"  Looked for a directory containing {MARKER}/ via: " + "; ".join(tried) + "\n"
        "  Fix it in one of these ways:\n"
        "    - run the tool from inside the repository, or\n"
        "    - pass --root /path/to/BEEHub, or\n"
        "    - export BEEHUB_ROOT=/path/to/BEEHub"
    )


def add_root_arg(parser) -> None:
    """Give a tool a --root flag with consistent help text."""
    parser.add_argument(
        "--root", metavar="DIR", default=None,
        help="BEEHub repository root (default: $BEEHUB_ROOT, else the git root, "
             "else the nearest parent containing Projects/)")
