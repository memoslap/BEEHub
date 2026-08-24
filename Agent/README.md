# BEEHub Agents — how to run them

Agents live in numbered folders under `Agent/`. Only **one** is active at a time.
`beehub-agent` replaces the `claude` command: it points `CLAUDE.md` at the agent you
asked for, then starts Claude Code.

**Every agent's instruction file must be named exactly `CLAUDE.md`.** A file called
`00_Intake_agent.md` is never loaded. `./beehub-agent --status` now warns about any
folder that has `.md` files but no `CLAUDE.md`, and prints the `mv` that fixes it.

---

# QUICK START

Integrating a new dataset, start to finish. Replace `MT` with your project code.

### 0. Is there anything to do?
```bash
cd /media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub
./Agent/00_Intake_agent/check_intake.sh
```
Lists unhandled drops in `Convert/` with a file inventory. No model, no side effects.

### 1. Answer the project questions FIRST
Agents are generic; everything project-specific lives in `Agent/notes/<CODE>.md`.
```bash
./Agent/notes/project_notes.sh new MT     # creates Agent/notes/MT.md + questions
$EDITOR Agent/notes/MT.md                 # answer every ?? — your job, not the agent's
./Agent/notes/project_notes.sh check MT   # must exit 0 before launching anything
```
An agent that finds an unanswered `??` asks you and stops. Deliberate: it cannot
invent a session mapping or pick your primary outcome.

### 2. Restructure (agent 01)
```bash
./beehub-agent 01
```
> Project code is **MT**. Source: `Convert/MouseTracking Data/`.
> Run **Stage 1 only** — survey and plan. Do not write any scripts yet.

Check the plan: every PDF has a `literature/` destination, the session mapping is
stated (not assumed), the participant count was quoted from `inventory_sessions.sh`.
Then:

> Stage 2 — write the migration script.

```bash
bash Convert/migrate_MT.sh             # dry-run is the default
bash Convert/migrate_MT.sh --apply     # only after a clean dry run
./Agent/tools/extract_docs.py Projects/MT/literature   # PDFs -> readable text
find "Convert/MouseTracking Data" -name '*.pdf'        # must return NOTHING
```

### 3. Data description (agent 02) — restart first
```
Ctrl+D
```
```bash
./beehub-agent 02
```
> Project code is **MT**. Check whether the data needs a derivation, then write
> `dataset_description.json`.

This agent asks whether anything is special about the dataset, takes your analysis
code, adapts it to the runner contract, produces derived tables, and asks which
columns are the primary, secondary, and up to four further outcomes. It records the
answers in `Agent/notes/MT.md`.

```bash
./Agent/tools/suggest_outcomes.py MT    # must exit 0 before agent 03
```

### 4. Project description (agent 03) — restart first
```
Ctrl+D
```
```bash
./beehub-agent 03
```
> Project code is **MT**. Write `Projects/MT/MT_description.json`.

```bash
grep -c TBD Projects/MT/*.json                                    # must be 0
python3 -m json.tool Projects/MT/MT_description.json >/dev/null && echo "valid JSON"
```
Read out its `_open_questions` and answer them.

### 5. Check (agent 04)
```
Ctrl+D
```
```bash
./beehub-agent 04
```
> Audit `Projects/MT/`. Report BLOCKING / SHOULD FIX / NOTE.

### 6. Paradigm (agent 05) — only if there is a Presentation paradigm
```
Ctrl+D
```
```bash
mamba activate psychopy
./beehub-agent 05
```
> Point `target.env` at `<the SET>`, run `probe.sh`, show me the report.
> Do not generate any code yet.

Then mark the drop done:
```bash
touch "Convert/MouseTracking Data/.beehub_done"
```

**One project per session. Always.** Restart between agents — instructions load once.

---

## The agents

| # | Name | Folder | Does | Writes |
|---|---|---|---|---|
| 00 | `intake` | `Agent/00_Intake_agent/` | Surveys a new `Convert/` drop | read-only |
| 01 | `renaming_restructure` | `Agent/01_Renaming_Restructure/` | Raw drop -> BEEHub/BIDS layout | proposes, then moves |
| 02 | `create_data_description` | `Agent/02_Create_Data_Description/` | Derivation + `dataset_description.json` + outcome selection | script, derived tsv, 1 JSON, notes |
| 03 | `create_project_description` | `Agent/03_Create_Project_Description/` | `<CODE>_description.json` from literature + notes | 1 JSON |
| 04 | `check_structure` | `Agent/04_Check_structure/` | Repo + stimulus integrity audit | read-only |
| 05 | `paradigm` | `Agent/05_Paradigm/` | Presentation `.exp`/`.sce` -> PsychoPy | `*_generated.py` |

Agents are **discovered**, not hardcoded: anything matching `Agent/*/CLAUDE.md` is a
role. Add a folder with a `CLAUDE.md` and it appears — no launcher edit.

**Why 02 and 03 are separate.** 02 works on the *data*: it writes executable code and
produces tables. 03 works on the *description*: it is read-only over data and writes
one JSON. Different permissions, different skills, and either instruction set alone is
already near the ~200-line adherence limit.

## The tools (no model — run these yourself)

| Tool | Does | Exit 1 means |
|---|---|---|
| `Agent/00_Intake_agent/check_intake.sh [--quiet]` | Unhandled drops in `Convert/` | work is waiting |
| `Agent/notes/project_notes.sh {new\|check\|list} <CODE>` | Per-project facts + open questions | questions unanswered |
| `Agent/tools/inventory_sessions.sh <dir>` | Counts participants/sessions from filenames | someone is incomplete |
| `Agent/tools/extract_docs.py <dir>` | PDF/PPTX -> text agents can read | a document yielded no text |
| `Agent/tools/suggest_outcomes.py <CODE>` | Which columns can carry an ICC | none can — derivation needed |
| `Agent/tools/run_derivation.py <CODE>` | Runs declared derivations | a derivation failed |
| `Agent/05_Paradigm/probe.sh` | Trial counts, timing, missing stimuli | — |
| `Agent/05_Paradigm/check_runs.sh <file>` | Lint + syntax + headless launch gate | generated code fails |

These exist because **a model asked to count will pattern-complete a plausible design
instead of counting**, and a model asked to name an outcome column will invent one.
Any question with a computable answer is answered by a script, and the agents must
quote the output rather than assert a value.

## Project-specific facts: `Agent/notes/<CODE>.md`

Every `CLAUDE.md` is generic. Session mappings, column authorities, which measure is
primary, known quirks — all live in `Agent/notes/<CODE>.md`, which is **authoritative**
and overrides the generic rules. Instruction files over ~200 lines lose adherence on a
small model, and notes load on demand rather than every session.

```bash
./Agent/notes/project_notes.sh list
```
Commit `Agent/notes/*.md` — with its provenance table (fact / source / date) it is the
record of what each PI actually confirmed.

## Derivations

A project whose tables are not directly analysable declares a `derivations` array in
`<CODE>_description.json` naming a script in `Projects/<CODE>/code/`, its input and
output directories, and the exact parameters used. The runner calls every script the
same way:

    <interpreter> <script> --input <dir> --output <dir> [--params <json>]

read-only from input, write-only to output. Derived tables gain a `desc-<label>`
entity (`..._task-gonogo_desc-stopping_beh.tsv`) beside their source — **sources are
never renamed or overwritten**, because that is irreversible and destroys the ability
to re-derive with different parameters.

## Launching and switching

```bash
./beehub-agent                   # list agents
./beehub-agent 02                # by number
./beehub-agent paradigm          # by name (substring works)
./beehub-agent --status          # what's active + misnamed instruction files
```

**Switching requires a restart.** Quit with `Ctrl+D`, then relaunch.

`mamba activate psychopy` **before** launching agent 05 — never inside a session.

## Per-agent requirements

An agent declares prerequisites in `Agent/<folder>/agent.env` (all keys optional):
```bash
REQUIRED_CONDA_ENV="psychopy"          # warn if a different env is active
REQUIRED_GLOB="Projects/*/bids_data"   # warn if nothing matches
NOTE="shown at launch"
```
`01` needs only the raw drop and the project code — if its `agent.env` still declares
`REQUIRED_GLOB="...description.json"` from the old describe-first order, delete it.

## Order

```
check_intake.sh  ->  project_notes.sh  ->  [you answer the questions]
  ->  01 restructure   ->  [approve the dry run, then --apply]
  ->  02 data desc.    ->  [supply the analysis code; choose the outcomes]
  ->  03 project desc. ->  [review the JSON + open questions]
  ->  04 check  ->  05 paradigm
```

`restructure` first: it needs only the raw drop and the project code. `02` before
`03`, because a description cannot name an outcome column that does not exist yet.

## Rules that hold for every agent

- **Never rename stimulus files.** `.sce` files reference them verbatim, and Linux is
  case-sensitive where the acquisition machines were not.
- **Never delete `.log` files.** They are the project's empirical oracle.
- **Never state a count you did not read from a tool's output this session.**
- **Never invent an outcome column.** If `suggest_outcomes.py` does not list it, it
  does not exist.
- **One tsv per grain.** Never merge per-trial and derived rows into one table.
- **Every PDF ends up in `Projects/<CODE>/literature/`** and is extracted to text —
  agents cannot read binaries.
- **Work sequentially.** No background or parallel sub-agents; if one returns in
  seconds with empty output, it failed.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Agent missing from the list | Its file isn't named exactly `CLAUDE.md` — run `--status` |
| Agent ignores its instructions | Launched with `claude` instead of `./beehub-agent` |
| Agent keeps asking me questions | `Agent/notes/<CODE>.md` has unanswered `??` |
| Agent invents outcome columns | `suggest_outcomes.py` exits 1 — run the derivation first |
| Agent claims to have read a PDF | It cannot; run `extract_docs.py` |
| `--status` shows "DANGLING" | Role file was moved or renamed |
| Changes to a `CLAUDE.md` do nothing | Session must be restarted |
| `Permission denied` on a script | `chmod +x <script>` |
| PsychoPy imports fail | Wrong env; `mamba activate psychopy`, then relaunch |
