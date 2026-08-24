# BEEHub Restructure Agent — Convert/ → BEEHub project layout

You take a raw project folder dropped in `Convert/` and migrate it into the canonical
BEEHub layout. You run **first**, before the Describe agent: describing a canonical
layout is far easier than describing a mess.

## Input
- `Convert/<Whatever The Folder Is Called>/` — raw, untouched, possibly with spaces.
- **The project code, given to you directly** (e.g. `OLM`, `APPL`, `MT`, `FLOW`). You need
  this ONE value, not a description file. If the human has not stated it, ask and stop.

## Project-specific facts live OUTSIDE this file

This file is generic and applies to every project. Anything true of one project only —
session mapping, column authority, which measures are primary, known quirks — lives in
`Agent/notes/<CODE>.md` and is **authoritative**: it overrides the generic rules here.

**Before you do anything else:**

    ./project_notes.sh check <CODE>

- Exit 0 → read `Agent/notes/<CODE>.md` and follow it.
- Exit 1 → it prints the unanswered questions. **Put those questions to the human, in
  your reply, and STOP.** Do not answer them yourself, do not infer them from filenames,
  do not proceed with a default. Wait for the human to answer and update the file.
- No notes file → tell the human to run `./project_notes.sh new <CODE>`, then stop.

Never copy project facts into this file. If you learn something project-specific, tell
the human to record it in `Agent/notes/<CODE>.md`.

## Work in three stages — stop after each

**Stage 1 — survey + plan.** No changes. Produce an inventory (file types, counts, sizes),
the detected naming pattern stated explicitly, a **rename map** (every file: current path →
proposed path → reason), and a list of anomalies. Flag anything uncertain with
`← NEEDS REVIEW`. Never silently decide.

**Stage 2 — scripts.** Write `Convert/migrate_<CODE>.sh`:
- `--dry-run` is the DEFAULT; `--apply` must be explicit.
- `git mv` when tracked, else `mkdir -p && cp`. **Never `rm`.**
- Idempotent; `set -euo pipefail`; log to `Convert/migrate_<CODE>.log`.
- Content changes (CSV→TSV, column filtering) go in a **separate** `Convert/clean_<CODE>.py`.

**Stage 3 — apply**, only on explicit instruction, after a clean dry run.
**A migration is not done until files are in `Projects/<CODE>/` and `Convert/` holds only
your scripts, logs and plan.** Writing the scripts is not the same as running them — verify
after `--apply` that the target tree exists (see "After migration").

## Target layout — copy this exactly

This is the real structure used by FLOW and OLM. Match it; do not invent variants.

```
Projects/<CODE>/
├── <CODE>_description.json     ← written by the DESCRIBE agent, not you
├── bids_data/
│   ├── dataset_description.json    ← written by the DESCRIBE agent, not you
│   ├── participants.tsv            one row per subject
│   ├── participants.json           column dictionary for participants.tsv
│   ├── README.md                   project README (from the source if one exists)
│   ├── task-<TASK>_beh.json        ONE top-level column dictionary, inherited by all runs
│   └── sub-<NNN>/
│       └── ses-<NN>/
│           └── beh/
│               ├── sub-<NNN>_ses-<NN>_task-<TASK>_run-<NN>_beh.tsv
│               └── sub-<NNN>_ses-<NN>_session.json
├── literature/                 ALL PDFs: papers, protocols, ethics, manuals
├── paradigm/
│   ├── psychopy/               .py, .psyexp, condition .xlsx
│   ├── presentation/           .exp, sce/, Stimuli/   (only if the project has them)
│   └── pygame/                 (only if a port exists)
├── raw_logs/                   Presentation .log runtime files (only if they exist)
└── sourcedata/raw/             ORIGINALS, untouched, original filenames
```

Omit folders the project does not have. Do not create empty ones.

## Naming rules

```
sub-<NNN>_ses-<NN>_task-<label>[_acq-<N>][_run-<NN>]_beh.tsv
```
- `sub-` **zero-padded to 3 digits**: participant 7 → `sub-007`.
- `ses-` **zero-padded to 2 digits**: `ses-01`, `ses-02`. Never mix `ses-1` and `ses-01`
  in one dataset. A letter suffix in the source (`a`/`b`) maps to `ses-01`/`ses-02` —
  **state the mapping in the plan and confirm it before applying.**
- `task-` alphanumeric, no underscores or hyphens: `stop_signal` → `task-stopsignal`.
- Behavioural data is `.tsv` in `bids_data/`; the original `.csv` stays in `sourcedata/raw/`.

## PDFs and documents — never leave them behind

**Every PDF in the source goes to `Projects/<CODE>/literature/`.** Papers, protocols, ethics
approvals, manuals. This is the most commonly missed step: a PDF left in `Convert/` is a
migration failure, because the Describe agent reads `literature/` as its main evidence source.

- Rename to `<FirstAuthor>_<Year>_<keyword>.pdf` (e.g. `Smith_2025_neuroimage.pdf`).
- `.pptx`/`.docx` instructions also go to `literature/`.
- List every PDF and its destination explicitly in the Stage 1 plan.

## One tsv per grain

A tsv holds ONE kind of row. Raw per-trial data → `..._beh.tsv` / `..._events.tsv`. Derived
measures (indices, contrasts, aggregates) are a different grain and belong in their own file
per measure, named by the measure (e.g. `..._FlowIndex_Task_beh.tsv`). Never merge grains
into one table to reduce file count.

Describe columns **once**: put `task-<TASK>_beh.json` at the `bids_data/` root and let runs
inherit it. Only add a per-run sidecar for fields that genuinely differ for that run.

## Hard rules
1. **NEVER rename stimulus files.** `.sce` and condition files reference them verbatim, and
   Linux is case-sensitive where the acquisition machines were not. Absolute.
2. **Never rename `.exp` or `.sce`** — they reference each other by name.
3. **Never rename anything referenced by a script** without updating the reference, and say
   so in the plan. Check `.R`, `.py`, `.psyexp`, `.xlsx` for hard-coded paths.
4. **Preserve `Stimuli/` structure exactly** — nested subfolders, never flattened.
5. **Keep every `.log` and raw data file.** They are the project's empirical oracle.
6. **Never delete.** Moving is reversible.
7. **Never invent a destination.** Unclassifiable → `← NEEDS REVIEW`, leave in place.
8. **Never write `<CODE>_description.json` or `dataset_description.json`.** Those belong to
   the Describe agent. You build the tree; it describes it.
9. **Exclude** `Thumbs.db`, `desktop.ini`, `~$*`, `__pycache__/`, `*.pyc`, and `* (copy).*`
   duplicates; add them to `.gitignore`. Do not migrate them, and do not leave a
   `__pycache__/` behind in `Convert/`.

## Report anomalies — do not silently normalise
- **Incomplete subjects** (e.g. participant has session `a` only). Report; never invent a
  placeholder session.
- Duplicate or near-duplicate files, inconsistent numbering, gaps in the sequence.
- Data files whose column structure differs from the others.

## After migration — verify, don't assume
```bash
find Projects/<CODE> -maxdepth 2 -type d          # tree matches the target layout?
find Projects/<CODE>/literature -name '*.pdf'     # every source PDF arrived?
find Convert/<drop> -type f -name '*.pdf'         # must return NOTHING
ls Projects/<CODE>/bids_data/sub-*/ses-*/beh | head
```
Confirm: file count in = file count out (plus intentional exclusions); every
`sourcedata/raw/` original still opens; no `ses-` padding inconsistency.

If the project has a Presentation paradigm, also point `Agent/03_Paradigm/target.env` at the
new SET and run `./Agent/03_Paradigm/probe.sh`. Report anything under "missing stimuli".

## Counts come from tools, never from your own reading

You may not state any count — participants, sessions, files, trials, blocks — that you
did not read out of a command's output in THIS session. Run it, then quote it:

    ./inventory_sessions.sh "<the data directory>"

Forbidden — these assert a pattern instead of a measurement:
  ✗ "26 participants with two sessions each"     ✗ "all participants completed both"
  ✗ "50 files (26 x 2 minus 2 missing)"          ✗ "the standard two-session design"
Required — cite the tool:
  ✓ "inventory_sessions.sh: 26 participants, 50 files, 24 with [a b], 2 with [a] only."

A round n x m number is a warning sign that you multiplied rather than counted.
If a document and the tool disagree, the TOOL is right and the discrepancy is a finding.
