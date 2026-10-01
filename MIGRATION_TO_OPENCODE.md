# BEEHub agents: Claude Code → OpenCode — what changed and why

This package replaces the five `Agent/*/CLAUDE.md` role files, the intake design
note, `HOUSE_STYLE.md` and `CONVERSION_WORKFLOW.md` with an OpenCode V2
configuration: one `AGENTS.md`, eight agents, nine skills, and seven generic
tools. Nothing in it is named after, or specific to, any project.

---

## 1. Why the old files had to be rewritten, not just moved

Three facts from OpenCode's V2 documentation drive everything below:

| Fact | Consequence |
|---|---|
| V2 recognizes `AGENTS.md` only and does not use `CLAUDE.md` as a fallback. | Your five `CLAUDE.md` files and the root `CLAUDE.md` symlink are **invisible** to OpenCode today. No agent was reading any of them. |
| The config `instructions` array is accepted but not resolved in V2. | You cannot point OpenCode at the old files from config either. |
| Legacy fields `temperature`, `top_p`, `prompt`, `permission`, `tools`, `disable`, `maxSteps` must not be used in V2 agents; permissions are an ordered list of `{action, resource, effect}` rules where the last match wins. | Agent files must be written in the new schema. This includes `code-check.md` and `paper-claims.md` **that I gave you earlier in this conversation — they used V1 fields and were wrong.** Both are rewritten here. |

Sources: `opencode.ai/v2/docs/instructions`, `/agents`, `/skills` (fetched 24 Sep 2026).

---

## 2. New layout

```
BEEHub/
├── AGENTS.md                       NEW  rules for every agent (loaded every session)
├── .opencode/
│   ├── agents/                     NEW  numbered by EXECUTION ORDER
│   │   ├── 01_intake.md                 primary — survey, read paper, plan, stop
│   │   ├── 02_restructure.md            rename map → dry run → apply
│   │   ├── 03_code-check.md             static audit of R/Python      (from this chat)
│   │   ├── 04_paper-claims.md           paper numbers → claims YAML   (from this chat)
│   │   ├── 05_data-description.md       derivations, reproduction, outcomes
│   │   ├── 06_project-description.md    <CODE>_description.json
│   │   ├── 07_paradigm.md               Presentation / PsychoPy / other
│   │   └── 08_check.md                  read-only audit
│   └── skills/                     NEW  NOT numbered — shared between stages
│       ├── read-paper/                  PDF → text/PNG, what to extract
│       ├── beehub-layout/               target tree + naming rules
│       ├── static-code-check/           check_code.py usage and reading
│       ├── reproduce-results/           claims + run + compare
│       ├── derivation-contract/         --input/--output/--params
│       ├── outcome-selection/           suggest_outcomes + role rules
│       ├── description-schema/          keys, vocabularies, outcome fields
│       ├── psychopy-house-style/        was HOUSE_STYLE.md
│       └── presentation-to-psychopy/    was CONVERSION_WORKFLOW.md
└── Agent/tools/                    NEW  every generic tool; NOT numbered — shared
    ├── check_intake.sh                  moved + edited (3 lines + next-step text)
    ├── suggest_outcomes.py              moved, usage examples neutralised
    ├── apply_rename_map.py              NEW — replaces migrate_<CODE>.sh + clean_<CODE>.py
    ├── run_derivation.py                NEW — was referenced but did not exist
    ├── pdf_for_agent.py                 from this chat, now a uv script
    ├── check_code.py                    from this chat
    └── reproduce_check.py               from this chat
```

---

## 3. File-by-file

| Old | New | What changed | Why |
|---|---|---|---|
| `Agent/00_Intake_agent/00_Intake_agent.md` | `agents/01_intake.md` | Now reads the paper and runs `check_code.py` during survey. Writes only into `Convert/<drop>/_intake/`. **Does not dispatch** — ends with the next command. | See §4.4. You asked for "read the PDF first, then plan what is there, what is correct, what to do next"; the plan template now has exactly those sections. |
| `Agent/01_Renaming_Restructure/CLAUDE.md` | `agents/02_restructure.md` + skill `beehub-layout` | Writes a **rename map (data)** instead of `migrate_<CODE>.sh` / `clean_<CODE>.py` **(code)**. Applying requires human approval via permission prompt. | §4.1 — your requirement of no project-named scripts. |
| `Agent/02_Create_Data_Description/CLAUDE.md` | `agents/05_data-description.md` + skills `derivation-contract`, `outcome-selection`, `reproduce-results` | Declares derivations in `code/derivations.json`; new Stage 4 checks reproduction against the paper. Hand-writing `.tsv` is blocked by permission. | §4.5, §4.6 |
| `Agent/03_Create_Project_Description/CLAUDE.md` | `agents/06_project-description.md` + skill `description-schema` | Roles always explicit (contradiction resolved, §5). Can write only `*_description.json` and reports. | §5 |
| `Agent/04_Check_structure/CLAUDE.md` | `agents/08_check.md` | Adds calibration against a known-good project first; re-validates the rename map; checks description columns are real. Wrong paths fixed. | The old "Agent/Paradigm/…" paths did not exist. |
| `Agent/05_Paradigm/CLAUDE.md` | `agents/07_paradigm.md` | Branches on source type: Presentation → manifest workflow; **already PsychoPy → verify, don't rewrite**; other → report and stop. Claude CLI rules removed. | It only handled Presentation. A PsychoPy-source project (the MT test case) had no path through it. |
| `Agent/05_Paradigm/HOUSE_STYLE.md` | skill `psychopy-house-style` | Rules unchanged. The OLM size table is removed; sizes come from the source or the notes. Now says house style binds *generated* code only. | Project-specific sizes; and the old wording implied rewriting human-made originals. |
| `Agent/05_Paradigm/CONVERSION_WORKFLOW.md` | skill `presentation-to-psychopy` | OLM SET_A paths replaced by placeholders driven by `target.env`; probe made Pass 0; provenance names the session's model instead of a hard-coded one. | Project-specific paths. |
| `AGENT_IMPLEMENTATION_PLAN.md` | **not ported** | — | It is design history plus OLM-specific findings plus Claude Code install instructions. Its generic content (probe, manifest, gate, "logs are the oracle") is in the paradigm skill. Move the OLM findings to `Agent/notes/OLM.md`. |
| (duplicated in 3 files) "Project notes gate", "Counts come from tools" | `AGENTS.md` rules 4–5 | Stated once. | The three copies had already drifted — two different paths to `project_notes.sh`. |

---

## 4. Design decisions

### 4.1 Per-project scripts → one tool plus a data file

The Restructure agent used to write `Convert/migrate_<CODE>.sh` and
`Convert/clean_<CODE>.py` for every project. Now it writes
`Convert/<drop>/_intake/rename_map.tsv` and `Agent/tools/apply_rename_map.py`
executes it.

Why this is better beyond your naming requirement: the map is reviewable in a
spreadsheet, the safety rules (dry run default, never delete, idempotent,
checksum-verified) are implemented once and tested, and a small model writing a
TSV is far more reliable than one writing a correct bash migration script.

The `review` action is a mechanical gate: the tool refuses `--apply` while any row
still says `review`. So "never silently decide" is enforced, not requested.

**Behaviour change:** sources are copied, not moved. Originals stay in `Convert/<drop>/`
until you remove them; `touch .beehub_done` marks the drop handled. The old
instruction "`Convert/` holds only your scripts" conflicted with "never delete"
anyway.

### 4.2 Prose rules → enforced permissions

V2 permissions let each agent's write scope be enforced. Examples:

| Old prose rule | Now |
|---|---|
| "You may write exactly three things" (data-description) | `edit` denied everywhere except those paths |
| "Never write or edit an existing .tsv" | `edit` on `**/*.tsv` denied |
| "Apply only on explicit instruction" (restructure) | `apply_rename_map.py *--apply*` → `ask` |
| "Show the diff and stop before running" (data-description) | `run_derivation.py` → `ask`; `--dry-run` → `allow` |
| "Intake is read-only except its plan" | `edit` allowed only in `Convert/*/_intake/**` |
| "Never delete" | `rm`, `mv`, `git rm`, `find … -delete` denied in every agent |

**Permissions are a seatbelt, not a sandbox.** `edit` rules cover the edit/write
tools, not files written by a shell command. `rm *` matches commands that *start*
with `rm`; `cd x && rm y` does not match it. The rules stop ordinary mistakes by a
well-behaved model; they do not contain a hostile one.

### 4.3 Skills for anything reused or only occasionally needed

`AGENTS.md` is loaded into every session, so it holds only what every stage needs.
Procedures live in skills, which OpenCode loads on demand via its `skill` tool — so
the 150-line Presentation workflow costs nothing in a restructure session. Skills
that several agents share (`read-paper` is used by three) exist once.

### 4.4 Intake plans; it does not dispatch

The old design had Intake dispatch the pipeline after approval. I removed that:

- Your own intake note says a 30–35B local model as dispatcher is the weak spot.
- Several stages need a conversation with you mid-task (outcome choice, JSON
  review). Subagents run in a child session with fresh context. I could not verify
  that a subagent can put a question to you and wait; if it cannot, those stages
  would silently default. Running each stage as its own session avoids the question.
- The confirmation gate becomes physical: you launch each stage.

Every agent ends by printing the next command, so the chain stays easy to follow.

### 4.5 `derivations.json` added

`run_derivation.py <CODE>` needs a machine-readable declaration, but the old design
put it only in the notes (prose) and in `<CODE>_description.json` (written *later*,
by the next agent). Now: `Projects/<CODE>/code/derivations.json`, written by
data-description, read by the runner, copied into the description by
project-description.

### 4.6 Code check and reproduction are pipeline stages

`code-check` and `paper-claims` run after restructure; data-description Stage 4
maps claims to outputs (human confirms each mapping) and runs the comparison.
Mismatches are findings to report, never failures to "fix".

---

## 5. Contradictions found in the old files, and the resolution

| # | Contradiction | Resolution |
|---|---|---|
| 1 | Project-description: roles may fall back to `display_priority`. Data-description and `suggest_outcomes.py`: "R-BEEHub does not infer a hierarchy from display_priority". | **Resolved in favour of explicit roles — see §5a.** `role` is now a required field with three states (`primary` / `secondary` / `undecided`). The fallback is removed from all agent and skill files. ⚠️ Action required in the Python pipeline — §5a. |
| 2 | Pipeline order: folder numbers (01 restructure, 02 data, 03 project, 04 check, 05 paradigm) vs intake note (…→ 03 paradigm → 04 check) vs `check_intake.sh` (02 describe → 03 paradigm). | intake → restructure → code-check → paper-claims → data-description → project-description → paradigm → check. Check last, because it audits the finished project. |
| 3 | `project_notes.sh` at `./project_notes.sh` (restructure) vs `./Agent/notes/project_notes.sh` (others). | Tree shows `Agent/notes/project_notes.sh`. Used everywhere. |
| 4 | `suggest_outcomes.py`, `inventory_sessions.sh`, `run_derivation.py` referenced under `Agent/tools/`; actual locations differ; `run_derivation.py` exists nowhere. | `Agent/tools/` created; `run_derivation.py` written. |
| 5 | Paradigm files referenced as `Agent/`, `Agent/Paradigm/`, `Agent/03_Paradigm/`, `Agent/05_Paradigm/`. | Tree shows `Agent/05_Paradigm/`. Used everywhere. |
| 6 | Derived files: "beside their source in `bids_data/`" (data-description) vs existing projects keep them in `derivatives/<name>/`. `suggest_outcomes.py` scanned only `bids_data/`. | **Resolved:** `derivatives/<name>/` stays beside `bids_data/`, and `suggest_outcomes.py` now scans both. It prints a `scanned:` line and labels every candidate with its tree. ⚠️ Remaining gap: `outcome_measures[]` has no field naming the tree — see §5b. |
| 7 | "Never delete" vs "Convert/ must hold only your scripts after migration". | Copy, don't move; mark the drop `.beehub_done`. |

### 5a. Outcome roles — decision: explicit only

**`role` is now required on every `outcome_measures[]` entry**, with three states:

| State | Meaning | Effect |
|---|---|---|
| `"primary"` / `"secondary"` | the PI has chosen | enters the cross-project comparison |
| `"undecided"` | the PI has not chosen yet | project reported, withheld from comparison |
| key absent | pipeline failure | check agent raises 🚨 BLOCKING |

`display_priority` orders the dashboard and carries no scientific meaning.

Reasoning:

1. **Reliability differs systematically between measure types** within one
   paradigm, so which column is primary moves a project's position in the
   cross-project comparison. A defaulted primary makes that position an artifact
   of file ordering rather than a research priority.
2. **`display_priority` is presentational.** Inferring from it means reordering a
   dashboard for readability silently changes a scientific claim, with no diff in
   any result.
3. **A defaulted role is indistinguishable downstream from a declared one** — the
   same objection your files already make to `"TBD"` and to guessed values.
4. **It is fragile:** adding a measure with `display_priority: 1` silently demotes
   the previous primary.
5. The fallback's only benefit is avoiding exclusion, but **exclusion is the
   honest state** for a project whose primary outcome was never specified.

Distinguishing `"undecided"` from a missing key matters: they look identical in a
dashboard but one is a pending research decision and the other is a bug. The
check agent treats them differently.

**⚠️ Action required, which I could not do.** I have not seen
`code/01_multi_project_overview_ROLE.py` or `code/03_generate_dashboard_ROLE.py`,
so I cannot tell how the fallback is implemented there. Before removing it:

1. Write explicit roles into every existing `*_description.json`. Your notes say
   at least one project currently relies on the fallback — removing it first
   would silently drop that project out of the comparison.
2. Then remove the `display_priority` fallback from both scripts and make a
   missing `role` an error rather than a default.
3. Handle `"undecided"` as "report, do not compare".

Do these in that order. Step 2 before step 1 changes published results.

### 5b. Outcomes in `derivatives/` — one gap remains

`suggest_outcomes.py` now scans `Projects/<CODE>/bids_data/` **and** every
`Projects/<CODE>/derivatives/<name>/` tree. Tested: a project whose raw tables
hold only identifiers and trajectory arrays reports "no viable column, derivation
required" (exit 1), and the same project after a derivation run reports the
derived columns with their tree (exit 0).

The gap: `outcome_measures[]` has `suffix` but no field saying **which tree** the
file is in. A measure in `derivatives/kinematics/` and one in `bids_data/` can
have indistinguishable entries. I did not invent a key for this. The skill tells
the agent to record the tree in the `derivations[]` entry's `output` and raise an
`_open_questions` note. **Check how the dashboard resolves `suffix`** — if it
globs `bids_data/` only, derived outcomes will not be found and a `location` key
(or resolution via `derivations[]`) is needed.

### 5c. Numbering — agents only

Agent files carry their execution order (`01_intake.md` … `08_check.md`), so the
directory listing *is* the pipeline. `agent_out/` reports carry the number of the
stage that wrote them (`03_code_check.md` comes from `03_code-check`), so a
project's report folder reads in order too.

**Skills and tools are deliberately not numbered.** They are shared: `read-paper`
is loaded by stages 01, 04 and 06; `check_code.py` runs in 01, 03 and 05. A number
would assert an execution order they do not have. Skill names are also constrained
by OpenCode to `^[a-z0-9]+(-[a-z0-9]+)*$` matching the folder name, so `01_read_paper`
would be rejected outright. `AGENTS.md` carries a stage → skills → tools table
instead, which gives the readability without the false ordering.

⚠️ The agent ID is the filename, so these IDs now contain an underscore
(`opencode --agent 01_intake`). OpenCode documents no charset restriction for
agent IDs — unlike skills — but I could not test it. If an agent is not found,
rename to hyphens (`01-intake.md`) and update the references.

---

## 6. Deliberately not changed

These scripts are referenced but I have not seen their contents, so I did not move
or edit them — their internal paths may assume their current location:

`inventory_sessions.sh` (repo root), `Agent/notes/project_notes.sh`,
`Agent/05_Paradigm/{probe,check_runs,lint_style,make_prompts}.sh`,
`Agent/bids_repair.py`.

⚠️ The old docs named three different locations for the paradigm scripts. If
`check_runs.sh` calls `lint_style.sh` by an old path, the gate is broken today.
Worth one `grep -n "Agent/" Agent/05_Paradigm/*.sh`.

`make_prompts.sh` prints prompts written for the `claude` CLI. They paste into
OpenCode unchanged; porting them to OpenCode *commands* is a later improvement.

---

## 7. What was tested

| Tool | Tested |
|---|---|
| `apply_rename_map.py` | dry run; apply; idempotent re-apply (`done: 5`); CSV→TSV with `n/a` fill; `copytree` excluding `Thumbs.db`; sources untouched; refusal on `review` row, missing source, duplicate target, content conflict, target outside `Projects/`, `Projects/../..` traversal; mixed-padding warning |
| `run_derivation.py` | success; exit 0 with no output; crash; **script modifying a source table (caught)**; missing script and missing interpreter |
| `check_intake.sh` | syntax; runs from `Agent/tools/`; `_intake/` excluded so its logs are not mistaken for run logs |
| `suggest_outcomes.py` | scans `bids_data/` + every `derivatives/<name>/`; exit 1 when raw tables hold only ids/arrays; exit 0 once a derivation exists, labelling each candidate with its tree |
| `pdf_for_agent.py` | runs via `uv run`, text + PNG split |
| `check_code.py`, `reproduce_check.py` | tested earlier in this conversation |
| agents | all eight parse as YAML, V2 permission shape, no legacy fields |
| skills | names match folder and the spec regex; descriptions within 1024 chars |

**Not tested:** anything inside OpenCode itself. I have no OpenCode install here.

---

## 8. Verify these yourself — I could not

1. **Your OpenCode version.** `opencode --version`. Everything here is V2 schema.
   On V1, the `permissions:` blocks will not work — see `opencode.ai/v2/docs/migrate-v1`.
2. **Glob semantics in permission resources** — whether `*` crosses `/`, and
   whether shell `*` matches across spaces. Test one deny before relying on it:
   ask the `check` agent to run `python3 Agent/tools/apply_rename_map.py x --apply`;
   it must be refused.
3. **`opencode --agent <name>`** — confirm with `opencode --help`.
4. **Whether the read tool shows PNGs to the model.** If not, attach pages with
   `opencode run -f`.
5. **R parse path in `check_code.py`** — untested (no `Rscript` here).

---

## 9. Install

```bash
cd /media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub
tar xzf beehub-opencode.tar.gz   # adds AGENTS.md, .opencode/, Agent/tools/, Agent_OpenCode/MIGRATION_TO_OPENCODE.md
chmod +x Agent/tools/*

# Retire the old copies so two versions cannot drift apart
mkdir -p Agent/_claude_legacy
git mv Agent/02_Create_Data_Description/suggest_outcomes.py Agent/_claude_legacy/suggest_outcomes.py
git mv check_intake.sh                        Agent/_claude_legacy/check_intake_root.sh
git mv Agent/00_Intake_agent/check_intake.sh  Agent/_claude_legacy/check_intake_00.sh
git mv Agent/00_Intake_agent/00_Intake_agent.md Agent/_claude_legacy/00_Intake_agent.md
for d in Agent/0*_*/; do
  [ -f "$d/CLAUDE.md" ] && git mv "$d/CLAUDE.md" "Agent/_claude_legacy/$(basename "$d").md"
done
git rm CLAUDE.md                      # the root symlink — OpenCode ignores it
git status --short                    # review before committing
```

Merge into your existing `opencode.json` (do not overwrite — it holds your
provider configuration):

```jsonc
{
  "default_agent": "01_intake",
  "permissions": [
    { "action": "shell", "resource": "rm *",      "effect": "deny" },
    { "action": "shell", "resource": "git push*", "effect": "ask"  }
  ]
}
```

⚠️ Global permissions are applied **before** agent rules, and the last match wins.
An agent's own `shell: * → ask` therefore overrides a global `rm → deny` for that
agent. That is why every agent file repeats its denies at the end — keep them
there when you edit.

Smoke test:

```bash
opencode run --agent 01_intake "In two sentences: what is your role, and what may you not do?"
opencode run --agent 08_check  "Run: python3 Agent/tools/apply_rename_map.py x --apply"   # must be refused
bash Agent/tools/check_intake.sh
```

If the first answer sounds generic ("I am opencode…"), the agent file was not
loaded — check `opencode debug config`.
