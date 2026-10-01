# Stage commands — reference card

Run everything from the repo root:
`/media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub`

Two rules that cause most errors:

- The agent ID is the **filename without `.md`** — `02_restructure`, not `02_restructure.md`.
- `opencode run` always needs a prompt in quotes. Bare `opencode` (TUI) does not,
  but then it takes a *directory* as its argument, so never pass it text.

Examples below use project code `MT` and the drop `MouseTracking Data`.
Swap those for another project.

---

## 00 — What is waiting? (no model)

```bash
bash Agent/tools/check_intake.sh
```

## 01 — Intake: read the paper, survey, plan

Read-only, so `--auto` is safe.

```bash
opencode run --auto --agent 01_intake \
  "Survey the 'MouseTracking Data' drop."
```

Make it investigate rather than ask you cold:

```bash
opencode run --auto --agent 01_intake \
  "Survey the 'MouseTracking Data' drop. For every open question, gather the
   evidence first with head -1, grep and ./inventory_sessions.sh and put it in
   the plan beside the question. Present evidence, not recommendations."
```

## 02 — Restructure: build Projects/MT/

**Use the TUI.** `--apply` is gated by an `ask` rule, and `--auto` would approve it.

```bash
opencode --agent 02_restructure
```

then type:

```
Project code MT. The rename map at
"Convert/MouseTracking Data/_intake/rename_map.tsv" is already validated.
Run the dry run, show me the result, and stop before --apply.
```

Dry run only, non-interactive, if you just want the report:

```bash
opencode run --auto --agent 02_restructure \
  "Dry-run 'Convert/MouseTracking Data/_intake/rename_map.tsv' and report. Do not apply."
```

Or skip the agent entirely — the map is data, the tool does the work:

```bash
python3 Agent/tools/apply_rename_map.py "Convert/MouseTracking Data/_intake/rename_map.tsv"
python3 Agent/tools/apply_rename_map.py "Convert/MouseTracking Data/_intake/rename_map.tsv" --apply
```

## 03 — Code check: is the analysis code sound?

```bash
opencode run --auto --agent 03_code-check \
  "Audit the R and Python code in Projects/MT/code. Establish the run order from
   what each script reads and writes. Write Projects/MT/agent_out/03_code_check.md."
```

## 04 — Paper claims: the numbers to test later

```bash
opencode run --auto --agent 04_paper-claims \
  "Read the paper in Projects/MT/literature and write Projects/MT/code/paper_claims.yaml.
   Do not add source: blocks."
```

## 05 — Data description: derivations, outcomes

**TUI** — it stops for your decisions and for approval before running code.

```bash
opencode --agent 05_data-description
```

```
Project MT. Start at Stage 1: run suggest_outcomes.py and tell me whether a
derivation is needed.
```

Expect exit 1 there: the raw tables hold identifiers and trajectory arrays, which
is the signal that the three R scripts are the derivation. That is the tool
working, not a failure.

## 06 — Project description

**TUI** — you review the JSON it writes.

```bash
opencode --agent 06_project-description
```

```
Project MT. Write Projects/MT/MT_description.json. Take the outcomes from
Agent/notes/MT.md; do not choose them yourself.
```

## 07 — Paradigm (PsychoPy)

Activate the env **before** launching, never inside a command:

```bash
mamba activate psychopy
opencode --agent 07_paradigm
```

```
Project MT. The paradigm is already PsychoPy (Program_final_german). Do not
rewrite it — verify it runs with check_paradigm.py and report what blocks it.
```

Expect the BOM failure on `go_nogo_dm.py` and
`hover_up_click_007b_review_lastrun.py` — intake already found it. The gate
prints the exact `sed` fix; apply it to a copy in `tmp/` first if you want to be
careful.

Run the gate yourself without an agent:

```bash
python3 Agent/tools/check_paradigm.py "Projects/MT/paradigm/psychopy/go_nogo_dm.py"
python3 Agent/tools/check_paradigm.py "Projects/MT/paradigm/psychopy/go_nogo_dm.py" --launch
```

Add `--generated` **only** for files an agent generated — house style does not
bind the project's original code.

## 08 — Check: audit the finished project

```bash
opencode run --auto --agent 08_check \
  "Audit Projects/MT. Calibrate first: run the same audit on Projects/APPL,
   which is already correct. If it reports violations there, your audit is wrong."
```

---

## Resuming

`opencode run` exits after each turn.

```bash
opencode --continue                    # TUI, last session, NO prompt argument
opencode sessions                      # list session IDs
opencode run --session <id> --auto --agent 01_intake "follow-up text"
```

`opencode --continue "some text"` fails with *Failed to change directory* —
bare `opencode` takes a directory, not a message.

## Which mode

| Stages | Mode | Why |
|---|---|---|
| 01, 03, 04, 08 | `run --auto` | read-only; nothing to approve |
| 02, 05, 07 | `opencode` TUI | an `ask` rule is the approval gate; `--auto` would bypass it |
| any | plain `run` (no `--auto`) | avoid — anything needing approval is silently auto-rejected |
