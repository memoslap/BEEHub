# Getting started with OpenCode in BEEHub

Agent files are numbered by execution order, so `ls .opencode/agents/` *is* the
pipeline. Skills and tools are not numbered — they are shared between stages.

## 1. Fix the layout first

Everything resolves relative to the **git root** (`BEEHub/`), which is where
`Convert/`, `Projects/` and `opencode.json` already live. The agent package must
sit there too, not in a subfolder:

```bash
cd /media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub

# only if the package is still under beehub-opencode/
mv beehub-opencode/AGENTS.md              ./
mv beehub-opencode/Agent_OpenCode         ./
mkdir -p Agent
mv beehub-opencode/Agent/tools ./Agent/
mv beehub-opencode/Agent/notes ./Agent/
[ -d .opencode ] || mv beehub-opencode/.opencode ./
rmdir beehub-opencode/Agent beehub-opencode 2>/dev/null

chmod +x Agent/tools/*

# scratch space the agents may write to freely
mkdir -p tmp
grep -qx 'tmp/' .gitignore 2>/dev/null || echo 'tmp/' >> .gitignore

ls -d AGENTS.md .opencode Agent/tools Agent/notes Convert Projects opencode.json tmp
```

All eight must exist. **Always launch OpenCode from `BEEHub/`**, never from a
subdirectory — a relative path like `Projects/**` means nothing from anywhere else.

## 2. Check it works (3 minutes, do not skip)

```bash
opencode --version                    # V2 or V1? decides which permission block applies
opencode debug config                 # is the config you expect being loaded?
bash Agent/tools/check_intake.sh      # should list drops in Convert/
```

Then:

```bash
opencode run --auto --agent 01_intake "In two sentences: what is your role, and what may you not do?"
```

If it answers as "opencode" or sounds generic, the agent file was not loaded. Try
`.opencode/agent/` instead of `.opencode/agents/` — versions differ. If the agent
is not found at all, try hyphens (`01-intake.md`): underscores in agent IDs are
undocumented and untested.

```bash
opencode run --auto --agent 08_check "Run: python3 Agent/tools/apply_rename_map.py x --apply"
```

This **must be refused** — `--auto` approves things that would ask, but explicit
denies still hold. If it runs, the safety rules are not active; fix that before
converting anything real.

## 3. Interactive or not

| | When |
|---|---|
| `opencode` (TUI) | **Default.** You see each tool call and approve it. Required for stages 02, 05, 07, where an `ask` rule is the approval gate. |
| `opencode run --auto …` | Read-only stages (01, 03, 04, 08) and smoke tests. |
| `opencode run …` | **Avoid.** Non-interactive with no `--auto`: anything that would ask is silently auto-rejected, and the agent looks broken. |

Resuming matters, because `run` exits after every turn:

```bash
opencode --continue                   # TUI, last session — no other arguments
opencode sessions                     # list IDs
opencode run --session <id> --auto --agent 01_intake "…"
```

`opencode --continue "my answer"` does **not** work: bare `opencode` takes a
*directory*, so your text becomes a path and it fails with "Failed to change
directory". Type into the TUI instead.

## 4. Convert a project

```bash
mamba activate psychopy        # before launching; only stage 07 needs it
opencode                       # starts on 01_intake
```

One stage per session. Each agent tells you the next command. **Bold** rows are
yours — the agents stop and wait there by design.

| # | Command | Ends with |
|---|---|---|
| 00 | `bash Agent/tools/check_intake.sh` | lists unhandled drops — no model |
| 01 | `opencode --agent 01_intake` | `_intake/INTAKE_PLAN.md` + `Agent/notes/<CODE>.md` — **you approve** |
| 02 | `opencode --agent 02_restructure` | rename map → dry run → **you approve `--apply`** |
| 03 | `opencode --agent 03_code-check` | `agent_out/03_code_check.md` |
| 04 | `opencode --agent 04_paper-claims` | `code/paper_claims.yaml` |
| 05 | `opencode --agent 05_data-description` | derivations + **you choose the outcomes** |
| 06 | `opencode --agent 06_project-description` | `<CODE>_description.json` — **you review it** |
| 07 | `opencode --agent 07_paradigm` | paradigm gate passes |
| 08 | `opencode --agent 08_check` | `agent_out/08_check.md` |

Reports in `agent_out/` carry the number of the stage that wrote them.

Nothing is deleted at any point. Originals stay in `Convert/<drop>/` until you
run `touch "Convert/<drop>/.beehub_done"`.

## 5. Project facts live in one file

`Agent/notes/<CODE>.md` is authoritative and overrides every generic rule. Stage
01 drafts it from `Agent/notes/_TEMPLATE.md` once you have answered its
questions; later stages read it and **stop if any `?` remains**. That is the
mechanism for "ask, don't guess" — a `?` is a question nobody has answered yet.

If an agent keeps asking something you already decided, the answer is not in
that file. Put it there rather than repeating it in chat.

## 6. `tmp/` is where fixing happens

Agents may write freely in `tmp/` and almost nowhere else. That is deliberate:
when something needs trying — a path fix, a BOM strip, a trial conversion, a
reproduction run — it happens on a copy in `tmp/`, and `Projects/` only ever
receives a result you agreed to.

```
tmp/<CODE>_<what>/        one named folder per task
```

`rm` stays denied everywhere, including inside `tmp/`, so agents cannot clean up
after themselves — a deletion pattern one character wrong is unrecoverable, and
the saving is a few megabytes. Empty it yourself when it gets large:

```bash
du -sh tmp/* | sort -h | tail
rm -rf tmp/<something>          # you, not the agent
```

It is git-ignored, so nothing there is ever committed. Which also means: never
the only copy of anything.

## 7. Make the agent gather evidence, not ask you cold

You will often be unfamiliar with the project. Stage 01 is instructed to
investigate before asking, but you can push it further:

```
Before I decide, investigate and show me the evidence:
compare the column headers of <A> against what <script> computes — quote the
column names from each side, don't summarise from memory.
Present findings as evidence, not a recommendation. I'll make the call.
```

It cannot read whole data files — `cat *.csv` is denied and `AGENTS.md` rule 8
forbids it. Expect `head -1`, `grep` and `wc -l`. If it tries to work around
that by reading a 45 MB CSV through `python3`, push back: the finding should
come from headers and counts.

## 8. Known gaps

| Gap | Effect |
|---|---|
| `Agent/05_Paradigm/` tooling is gone (`probe.sh`, `check_runs.sh`, `target.env`, `paradigm_template.py`) | Presentation → PsychoPy conversion cannot run. Verifying existing PsychoPy still works via `check_paradigm.py`. Restore with `git log --diff-filter=D -- 'Agent/05_Paradigm/*'` |
| `project_notes.sh` is gone | Replaced by reading `Agent/notes/<CODE>.md` directly — no script needed |
| Outcomes in `derivatives/` | `suggest_outcomes.py` finds them, but `outcome_measures[]` has no field naming the tree — see `MIGRATION_TO_OPENCODE.md` §5b |
| `display_priority` role fallback | Still live in the dashboard scripts. Write explicit roles into existing `*_description.json` **before** removing it — §5a |

## 9. When something looks wrong

| Symptom | Look at |
|---|---|
| `Error: Forbidden` before any tool call | the API key — `opencode debug config \| grep -i apikey`; a literal `{file:…}` means substitution didn't run |
| Tool calls "auto-rejecting" | you used `opencode run` without `--auto` |
| "Failed to change directory to …<your prompt>" | `opencode --continue` takes no prompt; use the TUI or `run --session` |
| Agent ignores its instructions | launched from a subdirectory, or `agents/` vs `agent/` |
| Agent asks what you already answered | it belongs in `Agent/notes/<CODE>.md` |
| Agent states a count you doubt | ask for the command; `AGENTS.md` rule 4 forbids unsourced counts |
| Stage 07 BOM error | the gate prints the exact `sed` fix — apply it with your approval |
| Rename map won't apply | a `review` row remains, or a target conflicts — the tool names it |
| "cannot locate the BEEHub repository root" | run from inside the repo, or pass `--root /path/to/BEEHub`, or `export BEEHUB_ROOT=…`. The layout is wrong — see §1 |
| An agent proposes `exec(open(tool).read())` or an inline reimplementation | say no. That bypasses the tested tool. Fix the underlying cause instead |

`Agent_OpenCode/MIGRATION_TO_OPENCODE.md` §8 lists what could not be verified
without an OpenCode install.
