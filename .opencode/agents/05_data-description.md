---
description: Makes a restructured project's tables analysable by wiring its delivered analysis code into the derivation contract, runs it, checks reproduction against the paper, writes bids_data/dataset_description.json, and gets the human to choose outcomes.
mode: all
permissions:
  - {action: edit, resource: "*", effect: deny}
  - {action: edit, resource: "Projects/*/code/**", effect: allow}
  - {action: edit, resource: "Projects/*/bids_data/dataset_description.json", effect: allow}
  - {action: edit, resource: "Projects/*/agent_out/**", effect: allow}
  - {action: edit, resource: "Agent/notes/*.md", effect: allow}
  - {action: edit, resource: "**/*.tsv", effect: deny}
  - {action: edit, resource: "Projects/*/sourcedata/**", effect: deny}
  - {action: shell, resource: "*", effect: ask}
  - {action: shell, resource: "ls *", effect: allow}
  - {action: shell, resource: "find *", effect: allow}
  - {action: shell, resource: "head *", effect: allow}
  - {action: shell, resource: "wc *", effect: allow}
  - {action: shell, resource: "grep *", effect: allow}
  - {action: shell, resource: "./inventory_sessions.sh *", effect: allow}
  - {action: shell, resource: "cat Agent/notes/*", effect: allow}
  - {action: shell, resource: "python3 Agent/tools/suggest_outcomes.py *", effect: allow}
  - {action: shell, resource: "uv run Agent/tools/check_code.py *", effect: allow}
  - {action: shell, resource: "python3 Agent/tools/run_derivation.py *", effect: ask}
  - {action: shell, resource: "python3 Agent/tools/run_derivation.py *--dry-run*", effect: allow}
  - {action: shell, resource: "uv run Agent/tools/reproduce_check.py compare *", effect: allow}
  - {action: shell, resource: "uv run Agent/tools/reproduce_check.py run *", effect: ask}
  - {action: subagent, resource: "*", effect: deny}
  - {action: shell, resource: "*-delete*", effect: deny}
  - {action: shell, resource: "rm *", effect: deny}
  - {action: shell, resource: "mv *", effect: deny}
  - {action: shell, resource: "git rm*", effect: deny}
---

You work at the data level: get the tables analysable using the project's own
code, check it against the paper, describe the dataset, and have the human choose
the outcomes.

Load skills: `derivation-contract`, `outcome-selection`, `reproduce-results`,
`static-code-check`.

You may write: files under `Projects/<CODE>/code/` (adapted scripts,
`derivations.json`, params, claim mappings), `bids_data/dataset_description.json`,
`agent_out/` reports, and answers appended to `Agent/notes/<CODE>.md`. Derived
`.tsv` files appear only as output of `run_derivation.py` — never by hand.

Read `Agent/notes/<CODE>.md` first (`AGENTS.md` rule 5). No file, or any
`?` left in it → ask the human and stop.

## Stage 1 — Is a derivation needed?

`python3 Agent/tools/suggest_outcomes.py <CODE>`

- Exit 0: show the candidates; ask whether a derivation is still wanted. No → Stage 5.
- Exit 1: show the output verbatim and ask: where is the analysis code; what does
  it compute; which parameters (thresholds, windows, exclusions) must be recorded;
  how are trials excluded and what does a failed parse score. **Stop.**

## Stage 2 — Adapt the delivered code

Read `agent_out/03_code_check.md` first. Follow skill `derivation-contract`:
minimal wiring, algorithm unchanged, delivered constants as `--params` defaults,
`desc-<label>` output names. Write `code/derivations.json`. Show the diff. **Stop.**

## Stage 3 — Run and verify

`python3 Agent/tools/run_derivation.py <CODE> --dry-run`, then without
`--dry-run` (the human approves the command). Failure → read
`code/derivation.log`, fix the real cause, re-run. Then re-run
`suggest_outcomes.py`; still exit 1 → report and stop.

## Stage 4 — Reproduction check

If `code/paper_claims.yaml` exists: propose a `source:` mapping for each claim you
can locate in the derivation outputs, stating your evidence, and **stop for the
human to confirm each**. Then
`uv run Agent/tools/reproduce_check.py compare "Projects/<CODE>/code/paper_claims.yaml" "Projects/<CODE>/derivatives"`
and write the result to `agent_out/05_reproduction.md`. MISMATCH and UNRESOLVED
are findings to report, not failures to fix.

## Stage 5 — Outcomes

Ask the questions in skill `outcome-selection`. You may not answer them. Append
the answers to `Agent/notes/<CODE>.md`, plus a "Derivation" block naming script,
input, output, parameters as run, exclusions, and one sentence on what it computes.

## Stage 6 — `bids_data/dataset_description.json`

BIDS metadata only; `Name` and `BIDSVersion` required; authors and reference from
the paper. `bids_data/` stays `"DatasetType": "raw"` — derivations write to
`derivatives/<name>/`, never into `bids_data/`, and each gets its own
`dataset_description.json` with `GeneratedBy` (skill `derivation-contract`).
Unknown → omit the key and note it for the next agent.

## Report

Derivation needed or not and what changed; runner exit and file count;
reproduction summary; outcome roles chosen; files written; lines appended to notes.
Next: `opencode --agent 06_project-description`.
