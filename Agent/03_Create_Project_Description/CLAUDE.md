# BEEHub Project-Description Agent — restructured project → project description

You write **exactly one file**:

    Projects/<CODE>/<CODE>_description.json

It is yours; nobody else writes it. Use `Projects/FLOW/FLOW_description.json` as the
reference for shape.

`bids_data/dataset_description.json` is written by the **Data-Description agent**,
which runs before you. Do not write or edit it, and do not treat it as missing work.

The Data-Description agent has also already established which columns are the
outcomes and recorded them in `Agent/notes/<CODE>.md`. **Read those before writing
`outcome_measures` — you do not choose the outcomes yourself.**

## YOU ARE READ-ONLY OTHERWISE
Do not rename, move, delete or create anything else. If you want to tidy something up,
note it and stop — that is the Restructure agent's job, and it has already run.

## Project-specific facts live OUTSIDE this file

This file is generic and applies to every project. Anything true of one project only —
session mapping, column authority, which measures are primary, known quirks — lives in
`Agent/notes/<CODE>.md` and is **authoritative**: it overrides the generic rules here.

**Before you do anything else:**

    ./Agent/notes/project_notes.sh check <CODE>

- Exit 0 → read `Agent/notes/<CODE>.md` and follow it.
- Exit 1 → it prints the unanswered questions. **Put those questions to the human, in
  your reply, and STOP.** Do not answer them yourself, do not infer them from filenames,
  do not proceed with a default. Wait for the human to answer and update the file.
- No notes file → tell the human to run `./Agent/notes/project_notes.sh new <CODE>`, then stop.

Never copy project facts into this file. If you learn something project-specific, tell
the human to record it in `Agent/notes/<CODE>.md`.

## The layout you are describing
```
Projects/<CODE>/
├── <CODE>_description.json     ← YOU WRITE
├── bids_data/
│   ├── dataset_description.json  ← written by the Data-Description agent
│   ├── participants.tsv          n subjects, groups, demographics
│   └── sub-*/ses-*/beh/          measured data (+ sidecars)
├── literature/                 papers, protocols — YOUR MAIN EVIDENCE
├── paradigm/                   psychopy/, presentation/, pygame/
├── raw_logs/                   Presentation .log runtime files
└── sourcedata/raw/             originals
```

## Method: evidence first, in this order
1. **`literature/`** — the paper is the single best source. Read its Methods. It answers
   full_name, background, procedure, trial_structure, design, timing, keywords.
2. **`bids_data/participants.tsv`** and the `sub-*/ses-*/` structure — subject count,
   `n_sessions`. Cheap and reliable.
3. **`code/` or analysis scripts** — name the **outcome measures** directly. Better
   evidence than prose.
4. **`paradigm/`** — `.py`/`.psyexp`/`.exp`/`.sce` and condition tables answer
   response_device, timing, software, implementations.
5. **Measured data** — `sub-*/ses-*/beh/*.tsv` give real trial counts and column names.

**Do not read large files whole.** `head -1` for headers, `grep`, line ranges. Prefer
`Agent/05_Paradigm/probes/<TAG>_probe.md` if one exists — measured and pre-digested.

## The file you write — `<CODE>_description.json`
**`01_description_form.html` (repo root) is the schema authority.** It is the human
version of this same job, and it emits exactly the JSON you must emit. When this file
and the form disagree, the form wins — say so and continue.

Keys, in this order:
```
full_name, short_description, long_description, background,
procedure, trial_structure, design,
modality, cognitive_domain, task_type, language, experimental_context,
software_original, language_original, implementations[], keywords[],
response_device, timing{}, outcome_measures[], n_sessions, software
```
- **`project_code` is not a key.** It only names the file: `<CODE>_description.json`.
- `timing` is an **object**, not a list: named keys with numeric (or `[min, max]`)
  values — `block_duration_s`, `task_timeout_s`, `n_blocks_per_session`, … Use the
  names the paradigm actually uses.
- Omit any key you cannot evidence; the form omits empty fields rather than nulling them.

### Controlled vocabularies — use one of these exactly
```
modality:              visual | auditory | linguistic | tactile | multimodal |
                       virtual environment
experimental_context:  behavioral | mri | eeg | pet | eye_tracking | fnirs | meg
language:              german | english | french | spanish | dutch | italian |
                       language-independent
cognitive_domain:      working memory | episodic memory | declarative memory |
                       spatial memory | semantic memory | spatial cognition |
                       cognitive control | emotion regulation | attention |
                       language | perception | learning
task_type:             continuous performance / n-back | associative learning |
                       recognition memory | object-location binding |
                       virtual navigation and pointing | color-word interference |
                       cognitive reappraisal | covert verb generation | go / no-go |
                       flanker | task switching | oddball / P300 | stop-signal
```
A genuinely new value is allowed (the form has a free-text box for each), but prefer an
existing term and flag any new one in `_open_questions`. Re-read the form's `<option>`
lists if this project looks unusual — the lists there are current, this copy may lag.

### `outcome_measures[]` — transcribe from the notes, do not invent
The chosen columns, roles, labels and flags are already in
`Agent/notes/<CODE>.md` under "Derived outcomes". Transcribe them. Verify each
`column` and `suffix` against a real file before writing it. Up to SIX entries:
one `"role": "primary"`, at most one `"role": "secondary"`, and up to four unroled.

Also copy the notes' "Derivation" block into a top-level `derivations` array if one
is present.

Field reference:
Required in every entry (the form drops any entry missing the first three):
`id` (UPPERCASE), `suffix`, `column`, `label`, `axis_label`, `higher_is_better`,
`is_binary`, `requires_correct_filter`, `is_helper`, `display_priority`.
Optional: `role`, `axis_range` `[min, max]`, `reference_line`, `plot_unit`
(`trial`|`subject`), `is_global: false`, `paradigm_contrast`.
- `column` **must name a real column** in the `.tsv` — the ICC is computed on it.
  Verify with `head -1` before writing it. If unsure, omit the entry and open a question.
- `suffix` must match the real filename ending exactly (e.g. `_FlowIndex_Task_beh.tsv`).
- `display_priority` ranks them: 1 = most important.
- `plot_unit: "subject"` whenever rows are not independent observations (session
  composites, replicates, internal-consistency items). Default is `trial`.
- `is_global: false` for a paradigm-specific measure (a flow index, a d-prime) so it
  stays out of cross-project raw-value sliders but still competes in the role comparison.

### Roles — the two prioritised outcomes
Roles live **inside `outcome_measures`**, not in a separate block. Two ways, in
precedence order (this is exactly what the pipeline does):
1. **Explicit:** put `"role": "primary"` on one entry and `"role": "secondary"` on
   another. Exactly one of each.
2. **Implicit fallback:** if no entry declares a role, `display_priority` decides —
   lowest number becomes primary, next becomes secondary.

Explicit is better: it survives re-ordering. FLOW currently relies on the fallback.

⚠️ **`is_primary` does NOT mean "the primary outcome."** In the form it is emitted as a
duplicate of `requires_correct_filter` ("restrict this measure to correct trials"), a
legacy name kept until the rename lands. Never set `is_primary` to mark a headline
measure — use `role`. Getting this backwards silently filters the wrong trials.

`main_metrics[]` is **not** read by the pipeline (it appears nowhere in
`01_multi_project_overview_ROLE.py` or `03_generate_dashboard_ROLE.py`) and is not
produced by the form. FLOW has one as extra human-facing metadata. Do not add it; if
you copy FLOW as a template, drop that block.

### Two extra keys for the human review step
Append `_open_questions` (and `_provenance` for non-obvious fields) at the end:
```json
"_provenance": {
  "cognitive_domain": "literature/<paper>.pdf, Methods p.4",
  "n_sessions": "participants.tsv + sub-*/ses-* structure",
  "outcome_measures": "code/<analysis script>"
},
"_open_questions": [
  {"field": "outcome_measures", "why": "three candidate DVs; which is primary?"}
]
```

## Hard rules
1. **Never invent an answer.** Unsupported field → omit it (or `null`) plus an
   `_open_questions` entry. Never `"TBD"`. A plausible-sounding guess is worse than a
   blank, because nobody downstream can tell it was a guess.
2. **Take outcomes from the notes, not from your own reading.** The Data-Description
   agent and the human already decided them. If `Agent/notes/<CODE>.md` has no
   "Derived outcomes" block, STOP and say the Data-Description agent has not run.
3. **Prefer measured over stated.** If the paper says 40 trials and the data show 56,
   report the measured value and flag the discrepancy.
4. **Do not guess the project code.** It determines the output path. If not stated, ask.
5. **Verify every `column` and `suffix` against real files** before writing them.
6. **Report irregularities** (subjects with missing sessions) in `_open_questions`; do not
   quietly average over them.

## Report when done
State: the file path written, fields filled, fields omitted, evidence sources used, and
read out `_open_questions`. Then STOP.

## Counts come from tools, never from your own reading

You may not state any count — participants, sessions, files, trials, blocks — that you
did not read out of a command's output in THIS session. Run it, then quote it:

    ./Agent/tools/inventory_sessions.sh "<the data directory>"

Forbidden — these assert a pattern instead of a measurement:
  ✗ "26 participants with two sessions each"     ✗ "all participants completed both"
  ✗ "50 files (26 x 2 minus 2 missing)"          ✗ "the standard two-session design"
Required — cite the tool:
  ✓ "inventory_sessions.sh: 26 participants, 50 files, 24 with [a b], 2 with [a] only."

A round n x m number is a warning sign that you multiplied rather than counted.
If a document and the tool disagree, the TOOL is right and the discrepancy is a finding.
