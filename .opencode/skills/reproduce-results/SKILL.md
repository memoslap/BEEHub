---
name: reproduce-results
description: Test whether a project's code, run on its data, reproduces the paper's numbers — extract claims, run in isolation, compare with tolerance. Use after derivations exist.
---

# Reproducing the paper's results

Three separable questions; never collapse them:

1. **Does the code run?** `reproduce_check.py run` — executes in a scratch copy.
2. **What does the paper claim?** `paper_claims.yaml` — written by `paper-claims`.
3. **Do the numbers match?** `reproduce_check.py compare`.

```bash
uv run Agent/tools/reproduce_check.py run "Projects/<CODE>/code" --workdir tmp/repro_<CODE>
uv run Agent/tools/reproduce_check.py compare "Projects/<CODE>/code/paper_claims.yaml" tmp/repro_<CODE>/run
```

## The one step no agent may do alone

Each claim needs a `source:` block naming the output file, column and statistic
that holds it:

```yaml
source: {file: summary.csv, column: accuracy, stat: mean, scale: 100}
```

Stats: `mean sd median min max sum n nunique nrow`; optional `where: {col: value}`
and `scale:`. **A wrong mapping produces a check that passes for the wrong
reason.** Propose mappings with your evidence; the human confirms each one.
Unmapped claims report `UNRESOLVED` and count as failing — that is correct.

## Reading the outcome

| Status | Meaning |
|---|---|
| MATCH | within the paper's own printed precision |
| MISMATCH | report the size of the gap — 4th decimal ≠ 1st decimal |
| MISSING | output file or column not produced |
| UNRESOLVED | no mapping yet — not a pass |

Legitimate causes of small mismatch: package-version defaults, unseeded RNG,
floating-point accumulation. Name the likely cause; do not "fix" the analysis.

`run` executes untrusted code in a copy under `tmp/`. Static-check it first.
The copy is scratch: never the only place a file exists.
