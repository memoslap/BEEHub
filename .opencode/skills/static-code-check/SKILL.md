---
name: static-code-check
description: Run and interpret the static checker on a project's R and Python analysis code — syntax, machine-specific paths, missing inputs, dependencies, run order. Use during intake and before any derivation.
---

# Static code check

```bash
uv run Agent/tools/check_code.py "<folder>"          # human-readable
uv run Agent/tools/check_code.py "<folder>" --json   # for further processing
```

Exit 1 means at least one ERROR or WARN.

| Severity | Means | For conversion |
|---|---|---|
| ERROR | file does not parse | cannot have produced the paper's results as-is — blocker |
| WARN | parses, but absolute path / `setwd()` / missing input / pyflakes issue | normal for inherited code; the derivation contract fixes paths |
| INFO | a check was skipped (usually no `Rscript`) | **never report a skipped file as clean** |

## Interpreting

- **Run order.** Numbered names (`1. x.R`, `2. y.R`) suggest an order. Confirm it
  from what each script reads and writes; state the evidence.
- **Missing inputs** may be outputs of an earlier script. Check before calling a
  file broken.
- **Dependencies** (R packages, Python imports) go into the report — they are what
  a reproduction needs.
- **Generated code** (e.g. PsychoPy Builder `*_lastrun.py`) matters less than its
  source (`.psyexp`).

## Never

Edit, reformat or run the code during this check. Describe fixes; do not apply them.
