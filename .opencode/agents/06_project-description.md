---
description: Writes Projects/<CODE>/<CODE>_description.json from the paper, the restructured data and the outcomes recorded in the project notes. Writes exactly that one file plus a report.
mode: all
permissions:
  - {action: edit, resource: "*", effect: deny}
  - {action: edit, resource: "Projects/*/*_description.json", effect: allow}
  - {action: edit, resource: "Projects/*/agent_out/**", effect: allow}
  - {action: edit, resource: "Projects/*/bids_data/**", effect: deny}
  - {action: shell, resource: "*", effect: ask}
  - {action: shell, resource: "ls *", effect: allow}
  - {action: shell, resource: "find *", effect: allow}
  - {action: shell, resource: "head *", effect: allow}
  - {action: shell, resource: "wc *", effect: allow}
  - {action: shell, resource: "grep *", effect: allow}
  - {action: shell, resource: "./inventory_sessions.sh *", effect: allow}
  - {action: shell, resource: "cat Agent/notes/*", effect: allow}
  - {action: shell, resource: "uv run Agent/tools/pdf_for_agent.py *", effect: allow}
  - {action: subagent, resource: "*", effect: deny}
  - {action: shell, resource: "*-delete*", effect: deny}
  - {action: shell, resource: "rm *", effect: deny}
  - {action: shell, resource: "mv *", effect: deny}
---

You write exactly one file: `Projects/<CODE>/<CODE>_description.json`. Everything
else is read-only to you. `bids_data/dataset_description.json` belongs to the
data-description agent — do not touch it or treat it as missing.

Load skills: `description-schema`, `read-paper`, `outcome-selection`.

Read `Agent/notes/<CODE>.md` first (`AGENTS.md` rule 5). No file, or any
`?` left in it → ask the human and stop. If the notes have no "Derived
outcomes" block, **stop** and say the data-description agent has not run.

## Evidence, in this order

1. `literature/` — the paper's Methods (skill `read-paper`; reuse
   `agent_out/paper/` if it exists).
2. `bids_data/participants.tsv` and `./inventory_sessions.sh` — n, sessions.
3. `code/` and `code/derivations.json` — outcome measures and derivations.
4. `paradigm/` — response device, timing, software, implementations.
5. Measured data — `head -1` for column names; trial counts from tools.

## Write the file

Follow skill `description-schema` exactly: key order, controlled vocabularies,
`outcome_measures[]` transcribed from the notes with explicit roles, every
`column` and `suffix` verified against a real file, `_provenance` and
`_open_questions` at the end.

## Report, then stop

File written; fields filled; fields omitted and why; evidence per field; read out
`_open_questions`. The human reviews the JSON before anything else runs.
Next: `opencode --agent 07_paradigm`.
