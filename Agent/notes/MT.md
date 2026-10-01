# Project notes — MT

Facts the agents cannot work out for themselves. **Authoritative**: these override the
generic rules in any agent's CLAUDE.md.

A double question-mark marks an unanswered question. An agent that finds one must **ask
the human and stop** — it may not answer on its own. Delete a question only by answering
it; write `n/a` if it genuinely does not apply.

---

## Identity
- Project code: `MT`
- Full study name: Mouse Tracking Go/No-Go Study
- Task label (BIDS `task-`, alphanumeric, no separators): `gonogo`

## Sessions
- How many sessions per participant? 2 (test-retest)
- How does the source encode the session? Filename prefix `<N><letter>`, e.g.
  `12b_go_nogo_dm_2025-05-14_16h31.40.550.csv` -> participant 12, session `b`
- Mapping to BIDS session numbers: `a` -> `ses-01`, `b` -> `ses-02`.
  Evidence: the `a` file's acquisition date always precedes the `b` file's for the same
  participant (1a 2025-04-30 < 1b 2025-05-16; 10a 05-05 < 10b 05-14; 26a 05-16 < 26b
  05-26). Session letters are chronological, so `a` is the first session.
- Are any participants known to be incomplete? Yes - participants **2 and 4** have
  session `a` only. Expect **50** raw data files, not 52.
  **The agent must still confirm this with `./inventory_sessions.sh` and quote the
  output - this line records what the human already knows, it is not a substitute for
  measuring.**

## Data columns
- Which file is the **column authority**? `go_nogo_compiledData.csv` (~44 MB, in the
  drop root). Its header defines the analysed column set. **Never read it whole -
  `head -1` only.** The raw PsychoPy exports carry far more columns than the analysis
  uses.
- Any columns that must be kept or dropped regardless? Keep exactly the compiled file's
  column set when cleaning each raw `.csv` into `_beh.tsv`; record every dropped column
  in the `_beh.json` sidecar. Do not guess which columns matter. Per-trial
  mouse-trajectory columns (`mouse_resp.x`, `.y`, `.time`, ...) are JSON-like arrays
  inside single cells - keep them as strings, one row per trial.

## Outcome measures
- Which measures does the analysis produce, and where are they defined?
  The analysis scripts are the authority - reported as `01_compute_stopping.R`
  (stopping behaviour), `02_ER_RT.R` (error rate, reaction time), `03_Kinematics.R`
  (trajectory kinematics).
  These `.R` files **are present** in the drop root (confirmed by `ls -la` and by the
  stage-02 dry run, which resolved all three). They are copied to `Projects/MT/code/`
  by the rename map (rows 4-6). No need to locate them externally.
- Which is **primary** and which **secondary**? **DECIDED (PI, 2026-09-25).**
  - **Primary:** `rt_combined` (shortcut `rt`) — Go reaction time, seconds, go trials.
    `higher_is_better: no` (faster is better). Label "Go RT". Axis "Reaction time (s)".
  - **Secondary:** `accuracy` (shortcut `acc`) — correct (1) / incorrect (0), binary.
    `higher_is_better: yes`. Label "Accuracy". Axis "Accuracy (correct = 1)".
  - **General ICC:** `nogo_stop_time` (shortcut `stop`) — No-Go stopping time, seconds,
    nogo trials. `higher_is_better: no` (faster is better). Label "Stop time".
    Axis "Stopping time (s)".
  All three come from `derivatives/scored/` (the `scored` derivation).

## Derivation
- Script: `code/compute_stopping.R` (declared in `code/derivations.json`, label `scored`)
- Input: `bids_data/sub-*/ses-*/beh/*_task-gonogo_beh.tsv` (raw per-trial mouse-tracking samples)
- Output: `derivatives/scored/sub-*/ses-*/beh/*_task-gonogo_desc-scored_beh.tsv` (50 tables)
- Parameters (as run): target-box entry threshold and NoGo stopping detection as defined
  by the delivered script (delivered constants used as `--params` defaults); no exclusions
  applied beyond the script's own stopping logic.
- What it computes: per-trial Go/No-Go scoring of raw mouse-tracking samples — target-box
  entry, NoGo stopping detection, and the resulting RT, stopping time, accuracy, path
  length, velocity, and acceleration per trial.

## Paradigm
- Software the paradigm was built in: PsychoPy (`Program_final_german/`). The
  `hover_up_click_007b_review_lastrun.py` is generated from the matching `.psyexp` and
  must travel with it.
- Language(s) of the presented material: german
- Anything the agent must NOT touch or rename:
  - `Slide7.PNG`, `Slide8.PNG` - stimulus images referenced by the experiment.
  - The `.psyexp` / `_lastrun.py` pair - rename either and the link breaks.
  - The condition tables `go_nogo.xlsx`, `go_nogo_prac.xlsx`, `go_only.xlsx`,
    `gopractice.xlsx`, `block_sequence.xlsx` - referenced by filename from the PsychoPy
    script.

## Known quirks
Free text. Anything irregular a human already knows.

- `Instructions (1).pptx` - space and parentheses in the filename must go, becomes
  `literature/instructions_de.pptx` (map row updated 2026-09-25).
- `Mahesan et al. 2026 - bioRxiv.pdf` becomes `literature/Mahesan_2026_biorxiv.pdf`.
  This is the describe agent's main evidence; it must not be left in `Convert/`.
- Two READMEs exist: `README_MT.md` (drop root) and `Program_final_german/readme.md`.
  They are different files - keep both, don't overwrite one with the other.
- `__pycache__/` and `*.pyc` are build artefacts - exclude and gitignore.
- A previous migration attempt is referenced in the notes (`migrate_MT.sh`,
  `clean_MT.py`, `MT_migration_plan.md`, `migrate_MT.log`), but **none of these files
  exist in the drop** (confirmed by `ls -la` on 2026-09-25). No `skip` rows were added
  for them in the rename map because they have no source path. If they are created
  later, add `skip` rows with the reason: "written against the old target layout
  (no `literature/`, `ses-1` not `ses-01`); do not reuse, regenerate fresh".
- Raw data is ~909 MB across 50 CSVs. Never read one whole.

---

## Provenance
Record who said what, so a stale note can be spotted later.

| Fact | Source | Date |
|---|---|---|
| Full study name, authors | `dataset_description.json` (existing stub) | 2026-07 |
| `a` to ses-01, `b` to ses-02 | derived from acquisition dates in filenames | 2026-07 |
| participants 2 and 4 incomplete | file listing; re-verify with `inventory_sessions.sh` | 2026-07 |
| compiled CSV is column authority | PI | 2026-07 |
| three candidate DVs / R scripts | PI; scripts confirmed present in drop 2026-09-25 | 2026-07, 2026-09 |
| task label `gonogo` | PI | 2026-07 |
| primary=rt, secondary=accuracy, ICC=stop | PI | 2026-09-25 |
