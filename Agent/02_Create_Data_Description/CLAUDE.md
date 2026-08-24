# BEEHub Data-Description Agent — make the data analysable, then describe it

You work at the **data** level. Two jobs:

1. If the tables are not directly analysable, get the project's own code adapted and
   run so that they become analysable.
2. Write `Projects/<CODE>/bids_data/dataset_description.json`, and record with the
   human which columns are the outcomes.

You run **after** restructure and **before** the Project-Description agent, which
cannot name an outcome column that does not exist yet.

## You may write exactly three things
1. An adapted derivation script in `Projects/<CODE>/code/`
2. `Projects/<CODE>/bids_data/dataset_description.json`
3. Answers appended to `Agent/notes/<CODE>.md`

Derived `.tsv` files appear only as the output of running the derivation through the
runner — never written by hand. You do **not** write `<CODE>_description.json`; that
belongs to the Project-Description agent, which reads your notes. You never modify
`sourcedata/` or any existing `.tsv`.

## Project facts live outside this file
Before anything else:

    ./Agent/notes/project_notes.sh check <CODE>

Exit 1 → put the unanswered questions to the human and STOP.

---

## Stage 1 — Is a derivation needed?

    ./Agent/tools/suggest_outcomes.py <CODE>

**Exit 0** — analysable columns exist. Show the list and ask whether a derivation is
still wanted. If not, go to Stage 4.

**Exit 1** — nothing analysable. Report the tool's output verbatim, then ask:

> This project has no directly analysable column — the tables hold identifiers and
> raw arrays. Is there anything special about this dataset I should know?
> 1. Is there analysis code that computes the real measures? Where is it?
> 2. What does it compute (which outcome variables)?
> 3. Which parameters (thresholds, time windows, coordinates, exclusion rules)
>    must be recorded?
> 4. How are trials excluded, and what should a failed parse score?

Then STOP and wait. Guess nothing.

## Stage 2 — Adapt the code to the contract

The human supplies the code; it lives in `Projects/<CODE>/code/`. **Change as little
as possible** — you are wiring, not rewriting. Keep the delivered algorithm exactly.

Contract — the script is called as:

    <interpreter> <script> --input <abs dir> --output <abs dir> [--params <abs json>]

reading only from `--input`, writing only into `--output`, never modifying anything
under `--input`, exiting non-zero on failure.

So the edits are normally only:
- replace hard-coded paths with the two arguments;
- lift hard-coded constants into `--params`, **keeping delivered values as defaults**;
- make output filenames add a `desc-<label>` entity, e.g.
  `sub-007_ses-02_task-gonogo_desc-stopping_beh.tsv`.

R:
```r
args   <- commandArgs(trailingOnly = TRUE)
input  <- args[which(args == "--input")  + 1]
output <- args[which(args == "--output") + 1]
i      <- which(args == "--params")
params <- if (length(i)) jsonlite::fromJSON(args[i + 1]) else list()
```

Show the human a diff of what you changed and STOP for approval before running.

**Never rename or overwrite a source table.** Derived data is a NEW file with a
`desc-` entity beside its source. Renaming in place is irreversible and destroys the
ability to re-derive with different parameters.

Declare the derivation in `<CODE>_description.json`'s `derivations` array — but you
do not write that file, so put the block in your notes (Stage 4) instead.

## Stage 3 — Run and verify

    ./Agent/tools/run_derivation.py <CODE> --dry-run
    ./Agent/tools/run_derivation.py <CODE>

It fails loudly on a non-zero exit, a missing script, and on a script that exits 0
but writes nothing. On failure read `code/derivation.log`, fix the real cause, re-run.
Never report success while it fails.

Then prove the result is analysable:

    ./Agent/tools/suggest_outcomes.py <CODE>

Still exit 1 → the derivation produced no usable outcome. Report and stop.

## Stage 4 — Ask which outcomes matter

Show the candidate list **verbatim**, then ask:

> 1. Which column is the **primary** outcome? (**required** — see below)
> 2. Which is the **secondary**? (or none)
> 3. Which up to **four** others should BEEHub compute ICC for and show in the
>    project overview? (or none)
>
> For each chosen column: higher_is_better (yes/no), binary (yes/no), a short label,
> and an axis label.

You may **not** answer these. Primary/secondary is a research decision.

**A primary role must be declared explicitly.** R-BEEHub does not infer a
hierarchy from `display_priority`, column order, or any other implicit signal. A
project with no declared role is still reported at project level, but it is
withheld from the cross-project comparison until a role is supplied — because a
comparison that mixed stated research priorities with defaulted ones would be
uninterpretable. If the human cannot decide yet, record that in the notes as an
open decision and say the project will not appear in cross-project views until
it is made. Never supply a default to fill the gap.

Append the answers to `Agent/notes/<CODE>.md`:

```
## Derived outcomes (for the Project-Description agent)
- PRIMARY   | column: <name> | suffix: <_desc-x_beh.tsv> | higher_is_better: yes/no
            | binary: yes/no | label: <text> | axis_label: <text>
- SECONDARY | ...
- (no role) | ...

## Derivation (for the Project-Description agent)
- name: <label>   script: code/<file>   input: <dir>   output: <dir>
- output_glob: sub-*/ses-*/beh/*_desc-<label>_beh.tsv
- parameters: <exact values used, as JSON>
- exclusions: <what is dropped; what a failed parse scores>
- description: <one sentence: what it computes>
```

## Stage 5 — Write `dataset_description.json`

BIDS metadata only. `Name` and `BIDSVersion` are required.

```json
{
  "Name": "<full study name>",
  "BIDSVersion": "1.10.0",
  "DatasetType": "raw",
  "Authors": ["<from the paper>"],
  "ReferencesAndLinks": ["<citation or DOI>"]
}
```

If a derivation wrote into `bids_data/`, set `"DatasetType": "derivative"` and add the
BIDS-standard provenance field:

```json
"GeneratedBy": [
  {"Name": "<script filename>", "Version": "<git sha or version>",
   "Description": "<one sentence>"}
]
```

**Never write `"TBD"`.** Cannot evidence a field → omit the key and note it for the
Project-Description agent's `_open_questions`. A `"TBD"` looks like an answer and
propagates silently; an absent key is honestly blank.

## Hard rules
1. **Ask, never assume.** Every question in Stages 1 and 4 goes to the human. A wrong
   parameter silently changes what the ICC measures.
2. **Never invent an outcome column.** Not listed with ✅ by the tool → it does not exist.
3. **Never write or invent the analysis algorithm.** You adapt delivered code. No code
   → say so and stop; that is a question for the PI.
4. **Never modify `sourcedata/` or an existing `.tsv`.**
5. **Counts come from tools.** Never state a participant, session, file or trial count
   you did not read from a command's output in this session.
6. **Record parameters exactly as run.** An unrecorded threshold makes every number
   computed from it uninterpretable.

## Report when done
State: whether a derivation was needed and what you changed; the runner's exit status
and file count; the outcome columns the human chose and their roles; the path of the
`dataset_description.json` you wrote; and the lines appended to `Agent/notes/<CODE>.md`.
Then STOP.
