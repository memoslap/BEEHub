# BEEHub — instructions for every agent

BEEHub turns research projects dropped into `Convert/` into a uniform layout under
`Projects/<CODE>/` (BIDS behavioural data, paper, paradigm, description JSON), so
reliability can be compared across projects. These rules apply to **every** agent
in `.opencode/agents/`. Role-specific instructions live in the agent file;
reusable procedures live in `.opencode/skills/` and are loaded on demand.

## The pipeline

One stage per session, in this order. Each stage ends by telling the human the
next command. **Bold** rows are human decisions — the agent stops and waits.

| # | Agent | Does | Produces | Skills it loads |
|---|---|---|---|---|
| 00 | *(no model)* `bash Agent/tools/check_intake.sh` | lists unhandled drops | — | — |
| 01 | `01_intake` | reads the paper, surveys the drop, checks its code | `Convert/<drop>/_intake/INTAKE_PLAN.md` | `read-paper`, `static-code-check`, `beehub-layout` |
| — | **human** | approves the plan, answers its questions | `Agent/notes/<CODE>.md` | — |
| 02 | `02_restructure` | writes a rename map, dry-runs it | `Projects/<CODE>/` tree | `beehub-layout` |
| — | **human** | approves `--apply` | — | — |
| 03 | `03_code-check` | static audit of the migrated R/Python | `agent_out/03_code_check.md` | `static-code-check` |
| 04 | `04_paper-claims` | the paper's numeric results | `code/paper_claims.yaml` | `read-paper`, `reproduce-results` |
| 05 | `05_data-description` | derivations, reproduction check, dataset metadata | `bids_data/dataset_description.json`, `derivatives/` | `derivation-contract`, `outcome-selection`, `reproduce-results`, `static-code-check` |
| — | **human** | chooses primary/secondary outcomes | notes | — |
| 06 | `06_project-description` | the project description | `<CODE>_description.json` | `description-schema`, `read-paper`, `outcome-selection` |
| — | **human** | reviews the JSON | — | — |
| 07 | `07_paradigm` | verifies PsychoPy paradigms run (Presentation conversion is blocked — see the skill) | `paradigm/psychopy/` | `psychopy-house-style`, `presentation-to-psychopy` |
| 08 | `08_check` | read-only audit of the finished project | `agent_out/08_check.md` | `beehub-layout`, `description-schema`, `psychopy-house-style` |

Start a stage: `opencode --agent 01_intake` (interactive) or
`opencode run --agent 01_intake "<instruction>"`.

Agent files are numbered by execution order. **Skills and tools are not
numbered** — they are shared between stages (`read-paper` is used by 01, 04 and
06; `check_code.py` by 01, 03 and 05), so a number would imply an order that does
not exist. The table above is the order; the skill list is what each stage needs.

## Rules that hold everywhere

1. **Never delete.** Not files, not folders, not data. Copying is the default;
   originals stay where they were until a human removes them.
2. **Never invent.** Not a project code, a session mapping, a column name, a
   file path, an outcome, a parameter, or an API symbol. If you cannot evidence
   it, say so and ask.
3. **Ask, then stop.** When you need a decision, put the question to the human
   and end your turn. Do not proceed with a default.
4. **Counts come from tools.** Never state a count of participants, sessions,
   files, trials or blocks that you did not read from a command's output in this
   session. Quote the command. A round n × m number means you multiplied instead
   of counting. If a document and a tool disagree, the tool is right and the
   disagreement is a finding.
5. **Project facts live in `Agent/notes/<CODE>.md`**, not in agent or skill files.
   That file is authoritative and overrides the generic rules here. Read it
   before any project work — there is no script, just read the file:

   ```bash
   cat "Agent/notes/<CODE>.md"        # small, hand-written; safe to read whole
   ```

   - **File exists, no `?` left** → follow it.
   - **File exists with `?` lines** → those are unanswered. Put exactly those
     questions to the human and stop. Do not answer them yourself, do not infer
     them from filenames, do not proceed with a default.
   - **No file** → only `01_intake` may create one, by copying
     `Agent/notes/_TEMPLATE.md` and filling in what the human has confirmed.
     Every other agent stops and says the intake stage has not run.

   Learn something project-specific? Add it to that file, never to a skill or an
   agent file.
6. **Scratch work goes in `tmp/`.** It is the one place you may write freely:
   trial conversions, a copy of a file you want to experiment on, intermediate
   output, a diff you are building. Use it instead of editing a real file to
   "see if that fixes it" — `tmp/` is where fixing problems happens, and
   `Projects/` only ever receives a result you and the human have agreed on.

   Rules: make a named subfolder per task (`tmp/<CODE>_<what>/`), never put
   anything there that exists nowhere else, and **do not delete anything** — not
   even your own scratch. `rm` is denied for every agent, including inside
   `tmp/`, because a deletion pattern that is one character wrong is
   unrecoverable and the saving is a few megabytes. The human empties `tmp/`.
7. **Paths contain spaces.** Quote every path in every shell command.
   If a tool reports it cannot locate the repository root, do **not** work around
   it by re-implementing the tool inline or by `exec`-ing its source. Pass
   `--root "<path to the directory holding Projects/>"` and say in your report
   that the layout needs fixing.
8. **Do not read large files whole.** `head -1` for headers, `wc -l`, `grep`,
   line ranges. Never `cat` a data file, a log, or a PDF.
9. **Never `"TBD"`.** Unknown → omit the key and record an open question.

## Where things are

| What | Path |
|---|---|
| Incoming drops | `Convert/<drop>/` (read-only for all agents) |
| Intake working files | `Convert/<drop>/_intake/` |
| Finished projects | `Projects/<CODE>/` |
| Agent reports | `Projects/<CODE>/agent_out/` |
| Scratch space | `tmp/` (git-ignored; yours to delete) |
| Repo root | wherever `Projects/` is. Tools find it themselves; `--root DIR` or `$BEEHUB_ROOT` overrides |
| Project facts | `Agent/notes/<CODE>.md` |
| Generic tools | `Agent/tools/` |
| Notes template | `Agent/notes/_TEMPLATE.md` |
| Session counter | `./inventory_sessions.sh "<data dir>"` |
| Schema authority for descriptions | `01_description_form.html` |

### Tools (all generic — no tool is named after a project, none is numbered)

| Tool | Used by | Does |
|---|---|---|
| `Agent/tools/check_intake.sh` | 00 | Lists unhandled drops. No model. |
| `uv run Agent/tools/pdf_for_agent.py "<pdf>" -o "<dir>"` | 01, 04, 06 | Paper → text `.md` + PNGs of image-only pages |
| `uv run Agent/tools/check_code.py "<dir>"` | 01, 03, 05 | Static check of `.R`/`.py`: parse, paths, inputs, deps |
| `python3 Agent/tools/apply_rename_map.py "<map.tsv>" [--apply]` | 02, 08 | Executes a reviewed rename map. Dry run by default. |
| `python3 Agent/tools/suggest_outcomes.py <CODE>` | 05, 08 | Which columns in `bids_data/` and `derivatives/` can be ICC outcomes |
| `python3 Agent/tools/run_derivation.py <CODE> [--dry-run]` | 05 | Runs declared derivations under the contract |
| `uv run Agent/tools/reproduce_check.py run\|compare …` | 05 | Runs analysis in isolation; compares to paper claims |
| `python3 Agent/tools/check_paradigm.py "<file>" [--launch] [--generated]` | 07 | Does the PsychoPy script compile, find its assets, and start? |
| `./inventory_sessions.sh "<data dir>"` | 01, 02, 05, 06, 08 | Counts subjects and sessions |

## Environment

- PsychoPy work runs in the `psychopy` mamba env. Activate it **before** starting
  OpenCode. Never run `mamba activate` inside a command; use
  `mamba run -n psychopy <cmd>` if you must target it explicitly.
- `uv run` scripts fetch their own dependencies; do not `pip install` for them.
- Code you write for the pipeline never calls an LLM API. Model work happens only
  inside OpenCode sessions.
