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
- Are any participants known to be incomplete? **CONFIRMED 2026-08.** Participants
  **2 and 4** have session `a` only. `sourcedata/raw/` holds **50** raw per-session
  CSVs plus `go_nogo_compiledData.csv`. 26 participants x 2 sessions - 2 = 50.
- **Historical defect, fixed 2026-08:** an earlier conversion produced only **48**
  `_beh.tsv` files — `sub-002` and `sub-004` were absent from `bids_data/` entirely,
  not merely missing `ses-02`. The two incomplete participants had been silently
  dropped rather than reported. Both are now present with `ses-01` only. Any analysis
  run before 2026-08 was missing them.

## Data columns
- Which file is the **column authority**? `go_nogo_compiledData.csv`. Its header defines
  the analysed column set: **15 source columns**. **Never read it whole — `head -1`
  only.**
- **The `_beh.tsv` files carry 16 columns, not 15.** The 16th is `trial_index`, a
  1-based counter generated during conversion after non-trial rows are removed. It is
  **not** a source column and does not weaken the compiled header's authority. It exists
  because nothing in the 15 identifies a trial: `block_number` has 15 distinct values
  across 606 trials, `trials_count` is a per-block constant of 18 (not a within-block
  counter, despite its name), and `block_number + trials_count + digit` reaches only 108
  distinct combinations. Without `trial_index`, the only key joining a derivative back to
  its source row is row order — which fails silently. Decided by the PI, 2026-08.
- Raw column count: **207** = 206 named + 1 trailing blank field (PsychoPy writes a
  trailing comma). **191 dropped.** The migration plan's "206 columns" was off by one;
  its "191 dropped" was correct. The blank field must not be recorded as a column named
  `""` in the sidecar.
- **Two header ORDERS exist across the 50 files (33 / 17), with IDENTICAL column sets.**
  Harmless: conversion extracts by name, never by position. The divergence starts at
  `response_box_clicked` / `click_pos_x` / `click_pos_y` — columns PsychoPy only creates
  when a click occurs — so the split most likely reflects whether a session's first trial
  was go or no-go. Both groups span the same date range and mix `a` and `b` sessions, so
  it is *not* a mid-study software change. Do not "fix" it.
- Per-trial mouse-trajectory columns (`mouse_resp.x`, `.y`, `.time`, `.leftButton`,
  `.midButton`, `.rightButton`) are JSON arrays inside single cells — keep them as
  strings, one row per trial. The sidecar declares `"Delimiter": ","` on each, which is
  the BIDS-sanctioned way to describe a list-valued cell.
- Column names contain dots (`mouse_resp.x`). BIDS RECOMMENDS snake_case but does not
  require it, and these names are the join to the analysis scripts and to the column
  authority. **Do not rename them.**
- Trajectory sampling rate: **~60 Hz** (median inter-sample interval 16.7 ms), median
  ~42 samples per trial, median trajectory duration 0.66 s. Relevant because the stopping
  parameters are expressed in seconds: `min_still_sec = 0.15` is ~9 samples,
  `post_still_sec = 0.25` is ~15.
- Trajectory coordinates are in PsychoPy **pixels**, the same space as the target box
  (`x` 150–250, `y` 250–350). Verified: `click_pos_x` values fall inside that range.

## Outcome measures
- Which measures does the analysis produce, and where are they defined?
  **RESOLVED 2026-08 — the R scripts are now present** in `Projects/MT/code/`:
  `1__compute_stopping.R` (stopping behaviour), `2__ER_RT.R` (error rate, reaction
  time), `3__Kinematics.R` (trajectory kinematics). The earlier warning that they were
  missing from the drop no longer applies.
- `1__compute_stopping.R` has been ported to Python as stage 2 of
  `Projects/MT/code/convert_MT.py`. **The port is not yet validated against the R
  original** — run both on the same input and compare `accuracy` and `rt_combined` trial
  by trial before relying on it.
- Which is **primary** and which **secondary**? **?? Not yet decided — the PI must
  choose.** Three candidate DVs exist. The agent must NOT pick: leave `role` unset and
  record an entry in `_open_questions` naming the candidates.

## Paradigm
- Software the paradigm was built in: PsychoPy (`Program_final_german/`). The
  `hover_up_click_007b_review_lastrun.py` is generated from the matching `.psyexp` and
  must travel with it.
- Language(s) of the presented material: german
- Anything the agent must NOT touch or rename:
  - `Slide7.PNG`, `Slide8.PNG` — stimulus images referenced by the experiment.
  - The `.psyexp` / `_lastrun.py` pair — rename either and the link breaks.
  - The condition tables `go_nogo.xlsx`, `go_nogo_prac.xlsx`, `go_only.xlsx`,
    `gopractice.xlsx`, `block_sequence.xlsx` — referenced by filename from the PsychoPy
    script.

## Known quirks
Free text. Anything irregular a human already knows.

- **Phantom trial rows.** Every raw CSV contains 611 written rows: 4 leading
  welcome/instruction rows, 606 real trials, and 1 trailing end-of-experiment row. The
  5 non-trial rows carry `participant` but no trial data, so a "drop rows where every
  cell is empty" filter does **not** remove them. They must be dropped on the
  `trial_type` marker. A `_beh.tsv` with **611 rows is wrong**; the correct count is
  **606**, uniform across all 50 sessions. Output produced before 2026-08 by
  `clean_MT (copy).py` (which lacked the filter) has the phantom rows and must be
  regenerated.
- Trial composition per session: **506 go, 100 no-go**.
- `1__compute_stopping.R` contains a **code/comment contradiction**: the docstring for
  `compute_nogo_stop` says the post-stop check validates the period *after* the detected
  stop, but the code uses `tail(v, n_post)` — the last samples of the *trial*. The Python
  port reproduces the **code** by default (`--post-window trial`) and offers
  `--post-window after-stop` for what the comment describes. **?? Which was intended?
  The two disagree whenever a stop is detected well before the deadline.**
- `Instructions (1).pptx` — space and parentheses in the filename must go, becomes
  `literature/instructions_de.pptx`.
- `Mahesan et al. 2026 - bioRxiv.pdf` becomes `literature/Mahesan_2026_biorxiv.pdf`.
- Two READMEs exist: `README_MT.md` (drop root) and `Program_final_german/readme.md`.
  They are different files — keep both, don't overwrite one with the other.
- `__pycache__/` and `*.pyc` are build artefacts — exclude and gitignore.
- The earlier migration artefacts in `Convert/` were written against the **old** target
  layout (no `literature/`, `ses-1` not `ses-01`) and must not be reused.
  `Convert/clean_MT.py` additionally crashed on `relative_to(Path.cwd())` unless run
  from the repo root, and lost the `csv.field_size_limit` call needed for trajectory
  cells over 128 KB. Superseded by `Projects/MT/code/convert_MT.py`.
- Raw data size: the migration plan measured ~952 MB across the 50 CSVs; the earlier
  note in this file said ~909 MB. **?? Which is right — remeasure.** Either way, never
  read one whole.
- **Two constants named alike mean different things.** `1__compute_stopping.R` has
  `post_still_sec = 0.25` (sizes the post-stop stillness CHECK). `3__Kinematics.R`
  has `POST_STILL_SEC <- 0.150` (sizes the no-go kinematics WINDOW). They are not
  the same quantity. Using 0.25 for the epoch inflates every no-go duration by
  100 ms and depresses no-go velocity and acceleration by ~15%, while leaving path
  length, all go measures, and ALL ICCs correct — so reliability checks alone will
  not detect it.

## Derivatives
- `Projects/MT/derivatives/stopping/` holds trial-level stopping metrics, generated by
  stage 2 of `convert_MT.py`. **Derived values are never written into `bids_data/`**:
  BIDS requires derivatives to be kept separate, and every value depends on
  `NOGO_CONFIG`, so merging them would make the raw files a function of analysis choices
  with no record of which parameters produced them.
- The parameters used are recorded in the derivative's `dataset_description.json` under
  `GeneratedBy[0].Parameters`. A re-run with different settings should become a second
  `desc-` label, not an overwrite.
- Reference values from `sub-001_ses-01` (2026-08, `--post-window trial`): go accuracy
  0.982 over 506 trials, no-go accuracy 0.980 over 100 trials, go RT median 0.725 s,
  no-go stop latency median 0.445 s, zero parse failures. Useful as a regression check.

---

## Provenance
Record who said what, so a stale note can be spotted later.

| Fact | Source | Date |
|---|---|---|
| Full study name, authors | `dataset_description.json` (existing stub) | 2026-07 |
| `a` to ses-01, `b` to ses-02 | derived from acquisition dates in filenames | 2026-07 |
| participants 2 and 4 incomplete | file listing | 2026-07 |
| compiled CSV is column authority | PI | 2026-07 |
| task label `gonogo` | PI | 2026-07 |
| 50 raw CSVs confirmed; 48 `_beh.tsv` was a defect | `convert_MT.py` stage 1 run | 2026-08 |
| 207 raw columns (206 + 1 blank), 191 dropped | header count across all 50 files | 2026-08 |
| two header orders, identical column sets | `diff_headers.py` | 2026-08 |
| 611 written rows = 4 + 606 + 1; 606 trials | row counts, all 50 files | 2026-08 |
| 506 go / 100 no-go per session | `sub-001_ses-01` counts | 2026-08 |
| ~60 Hz sampling, pixel coordinates | measured from `mouse_resp.time` / `.x` | 2026-08 |
| `trial_index` as 16th column | PI decision | 2026-08 |
| R scripts now present in `Projects/MT/code/` | directory listing | 2026-08 |
| stopping metrics go to `derivatives/`, not raw | BIDS spec (derivatives separation) | 2026-08 |
| `sub-001_ses-01` reference accuracies | `convert_MT.py` stage 2 run | 2026-08 |

## Reproduction status (2026-08)

Independently reproduced from raw PsychoPy CSVs via convert_MT.py + reproduce_paper_MT.py:
N=23, outlier rates, error rates, RTs, path length (go/no-go), no-go velocity and
acceleration, and ALL TEN ICCs with confidence intervals — all matching the preprint.

Residual: go mean velocity +1.31% and go mean acceleration +1.34% versus published,
with go path length exact. Hypothesis: the published go figures may be ratio-of-means
rather than mean-of-ratios; the discrepancy would then appear only where duration is
variable, i.e. go trials. ?? Confirm with the PI against go_nogo_scored_final.xlsx.

Two porting hazards found, both recorded in the R scripts' favour:
- post_still_sec (0.25, stopping check) vs POST_STILL_SEC (0.150, kinematics epoch)
  are different quantities with near-identical names. Confusing them inflates no-go
  duration by 100 ms; it leaves path length, all go measures and ALL ICCs correct,
  so reliability checks alone cannot detect it.
- The compute_nogo_stop docstring contradicts its own code; the code matches the
  paper's Methods. The docstring is stale.
