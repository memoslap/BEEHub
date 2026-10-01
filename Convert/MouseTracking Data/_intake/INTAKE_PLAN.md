# INTAKE_PLAN — "MouseTracking Data"

Drop: `Convert/MouseTracking Data/`
Paper: Mahesan et al. (2026), *Inhibition in motion: Test-retest reliability of inhibitory kinematics in a go/no-go mouse tracking task*, bioRxiv 2026.05.06.722889.

---

## 1. What this is

| Fact | Value | Evidence |
|---|---|---|
| Task type | Go/no-go mouse-tracking task | Paper abstract (p.1): "completed the task in two sessions … test-retest reliability of standard behavioral measures (error rates and reaction times), and three kinematic features" |
| Cognitive domain | Response inhibition | Paper title: "inhibitory kinematics in a go/no-go mouse tracking task"; Methods §2.3 (p.6): "successful inhibition was characterized by significantly shorter path lengths and reduced mean velocity and acceleration compared to go trials" |
| Modality | Mouse (cursor) tracking via USB optical mouse | Paper Methods §2.2 (p.6): "Participants performed the task using a standard USB optical mouse; … Mouse sensitivity was set to the default condition (50% velocity)" |
| Language of materials | German | `Program_final_german/` folder name; paper Methods (p.6): "using the German version of the Edinburgh Handedness Inventory" |
| Experimental context | Test–retest reliability study, two sessions ~1 week apart | Paper Methods §2.1 (p.5): "Each participant completed the study in two experimental sessions, separated by a mean test-retest interval of 9.6 days (range: 7 - 16 days)" |
| Original software | PsychoPy | `README_MT.md` (p.27): "one CSV per participant per session, as recorded directly by the task software (PsychoPy)"; `Program_final_german/go_nogo_dm.py` and `hover_up_click_007b_review.psyexp` present |
| n recruited | 26 participants | Paper Methods §2.1 (p.5): "A total of 26 participants took part in the study (15 female, 1 diverse; mean age: 22.9 years; range: 18 - 33 years)" |
| n analysed | 23 participants (26 − 2 who did not attend session 2 − 1 with low accuracy) | Paper Methods §2.5 (p.7): "Two participants did not attend the second session and were therefore excluded from all analyses. One additional participant was excluded due to low accuracy on go trials in the go/no-go block during session 1 (49%)" |
| Sessions | 2 (session 1, session 2) | Paper Methods §2.1 (p.5): "Each participant completed the study in two experimental sessions" |
| Blocks per session | 13 blocks: 5 go-only (18 trials each) + 8 mixed go/no-go (60 trials each) | Paper Methods §2.3 (p.6): "The main experiment then consisted of repeated sequences of three blocks: one go-only block (18 trials) followed by two mixed go/no-go blocks (60 trials each; 80% go, 20% no-go). This sequence was then repeated four times. The session concluded with a final go-only block … resulting in a total of five go-only blocks and eight mixed go/no-go blocks" |
| Trials per session | (5 × 18) + (8 × 60) = 90 + 480 = 570 | Computed from block structure above (paper Methods §2.3, p.6) |
| Outcome measures | Error rate, RT (go RT / no-go stopping latency), path length, mean velocity, mean acceleration | Paper abstract (p.1): "standard behavioral measures (error rates and reaction times), and three kinematic features: path length, mean velocity, and mean acceleration" |
| Analysis | 2(session) × 2(trial-type) repeated-measures ANOVA + ICC(3,1) two-way mixed test–retest reliability | Paper Methods §2.5 (p.7): "We used a 2 (session: session 1, session 2) × 2 (trial-type: go, no-go) repeated measures within-subjects design … the intraclass correlation coefficient based on a two-way mixed-effects model (ICC(3,1))" |

**Session inventory (from tool, not from paper):**

```
$ ./inventory_sessions.sh "Convert/MouseTracking Data/Raw Data"
26 participants, 50 data files.
24 participants have sessions [a b]; 2 participants have only [a].
Participant 2 has [a] — expected [a b].
Participant 4 has [a] — expected [a b].
2 of 26 participants are INCOMPLETE.
```

- 26 participants on disk: IDs 1–26.
- 50 raw CSV files.
- Participants 2 and 4 have only session `a` (no session `b` file).

---

## 2. What is there

| Item | Type | Count | Proposed destination under `Projects/<CODE>/` |
|---|---|---|---|
| `Mahesan et al. 2026 - bioRxiv.pdf` | Paper PDF | 1 | `literature/Mahesan_2026_mousetracking_gonogo.pdf` |
| `README_MT.md` | Author README | 1 | `literature/README_MT.md` (or keep at drop root; see Assumption A4) |
| `Raw Data/` (50 CSVs, one per participant-session) | Raw trial-by-trial trajectories | 50 | `sourcedata/raw/` (original names preserved) |
| `go_nogo_compiledData.csv` (45 MB) | Pre-compiled trimmed dataset | 1 | `code/` or `derivatives/` (see Assumption A5) |
| `1. compute_stopping.R` | Analysis script | 1 | `code/1. compute_stopping.R` |
| `2. ER_RT.R` | Analysis script | 1 | `code/2. ER_RT.R` |
| `3. Kinematics.R` | Analysis script | 1 | `code/3. Kinematics.R` |
| `Program_final_german/go_nogo_dm.py` | PsychoPy experiment script | 1 | `paradigm/psychopy/go_nogo_dm.py` |
| `Program_final_german/hover_up_click_007b_review.psyexp` | PsychoPy experiment | 1 | `paradigm/psychopy/hover_up_click_007b_review.psyexp` |
| `Program_final_german/hover_up_click_007b_review_lastrun.py` | PsychoPy script | 1 | `paradigm/psychopy/hover_up_click_007b_review_lastrun.py` |
| `Program_final_german/block_sequence.xlsx` | Condition file | 1 | `paradigm/psychopy/block_sequence.xlsx` |
| `Program_final_german/go_nogo_prac.xlsx` | Condition file | 1 | `paradigm/psychopy/go_nogo_prac.xlsx` |
| `Program_final_german/go_nogo.xlsx` | Condition file | 1 | `paradigm/psychopy/go_nogo.xlsx` |
| `Program_final_german/go_only.xlsx` | Condition file | 1 | `paradigm/psychopy/go_only.xlsx` |
| `Program_final_german/gopractice.xlsx` | Condition file | 1 | `paradigm/psychopy/gopractice.xlsx` |
| `Program_final_german/Instructions (1).pptx` | Instructions slide deck | 1 | `literature/` or `paradigm/psychopy/` (see Assumption A6) |
| `Program_final_german/Slide7.PNG`, `Slide8.PNG` | Instruction images | 2 | `paradigm/psychopy/` (referenced by `.psyexp`) |
| `Program_final_german/readme.md` | Empty file (0 bytes) | 1 | `skip` (empty, no content) |

**Total files to migrate: 68** (excluding `_intake/`).

---

## 3. What is correct

- **Paper and data agree on n = 26 participants.** Paper: "A total of 26 participants took part" (p.5). Tool: 26 participants on disk. ✓
- **Paper and data agree on two-session design.** Paper: "two experimental sessions" (p.5). Data: files suffixed `a` and `b` for each participant. ✓
- **Paper documents the missing session-b files for participants 2 and 4.** Paper Methods §2.5 (p.7): "Two participants did not attend the second session and were therefore excluded from all analyses." The tool flags these as INCOMPLETE, but the paper explains why. The missing `b` files for participants 2 and 4 are expected, not anomalous. ✓
- **`2. ER_RT.R` and `3. Kinematics.R` parse cleanly** (no syntax errors). They have absolute-path warnings only.
- **Run order is clear from `README_MT.md`:** `1. compute_stopping.R` → `2. ER_RT.R` → `3. Kinematics.R`. The R scripts read from `go_nogo_scored_final.csv` / `.xlsx` (not directly from `Raw Data/`), so `1. compute_stopping.R` must run first to produce those intermediate files.
- **All 50 raw CSVs have consistent naming** matching the convention in `README_MT.md`: `[subject]a|b_go_nogo_dm_[date]_[time].csv`.

---

## 4. What is missing or wrong

### 4.1 Code check — 2 errors, 8 warnings

**ERRORS (2):**

| File | Line | Issue |
|---|---|---|
| `Program_final_german/go_nogo_dm.py` | 1 | Syntax error: invalid non-printable character U+FEFF (UTF-8 BOM at start of file). The file cannot be parsed by Python as-is. |
| `Program_final_german/hover_up_click_007b_review_lastrun.py` | 1 | Syntax error: invalid non-printable character U+FEFF (same BOM issue). |

Both are `.py` files in the paradigm folder. The BOM is a Windows/Notepad artifact. This will block the `07_paradigm` stage (PsychoPy verification) until the BOM is stripped.

**WARNINGS (8) — all absolute paths:**

| File | Line(s) | Absolute path |
|---|---|---|
| `1. compute_stopping.R` | 26, 27 | `C:/1_DevuMahesan_Data/…/go_nogo_s.xlsx` and `go_nogo_scored_final.csv` |
| `2. ER_RT.R` | 17, 18 | `C:/1_DevuMahesan_Data/…/go_nogo_scored_final.xlsx` and `performance_reliability_tables_complete.xlsx` |
| `3. Kinematics.R` | 46, 47 | `C:/1_DevuMahesan_Data/…/go_nogo_scored_final.xlsx` and `3. Kinematics_results01_CORRECTED.xlsx` |
| `go_nogo_dm.py` | 129 | `C:\1_DevuMahesan_Data\…\go_nogo_dm.py` (self-reference) |
| `hover_up_click_007b_review_lastrun.py` | 129 | `C:\1_DevuMahesan_Data\…\hover_up_click_007b_review_lastrun.py` (self-reference) |

All R scripts and the main PsychoPy script reference a Windows path `C:/1_DevuMahesan_Data/…` that does not exist on this machine. The R pipeline will not run without path fixes.

### 4.2 Paper vs data disagreement — participant 4

The paper says "Two participants did not attend the second session" (p.7). The tool confirms exactly two participants (2 and 4) have only session `a`. **This is consistent** — the paper's statement is confirmed by the data. However, the paper does not identify *which* two participants, so we cannot confirm from the paper alone that they are specifically participants 2 and 4. The data (file names) tell us they are 2 and 4. This is a **minor gap**: the paper is anonymous on this point; the file names disambiguate.

### 4.3 Missing intermediate files

The R scripts read from files that are **not present in the drop**:
- `go_nogo_s.xlsx` (read by `1. compute_stopping.R`)
- `go_nogo_scored_final.csv` / `.xlsx` (read by `2. ER_RT.R` and `3. Kinematics.R`)
- `performance_reliability_tables_complete.xlsx` (written by `2. ER_RT.R`)
- `3. Kinematics_results01_CORRECTED.xlsx` (written by `3. Kinematics.R`)

These are the outputs of `1. compute_stopping.R` and the subsequent scripts. They are **not included in the drop** — they must be generated by running the pipeline. This means `05_data-description` will need to run the R pipeline (after path fixes) to produce `derivatives/`.

### 4.4 `go_nogo_compiledData.csv` (45 MB)

This file is described in `README_MT.md` as "A pre-compiled dataset built from the raw files above, trimmed down to the columns most relevant for analysis." It is **not** the same as the R-script output (`go_nogo_scored_final.csv`). Its relationship to the pipeline is unclear — it may be an earlier or parallel compilation. **Need to confirm with human** whether this is a deliverable to keep, or an intermediate that can be regenerated.

### 4.5 `Project_notes.sh` does not exist

`Agent/notes/project_notes.sh` is referenced in `AGENTS.md` but the file does not exist on disk (`Agent/` contains only `tools/`; `Agent_OpenCode/` contains only two `.md` files). This means the notes-check step (`./Agent/notes/project_notes.sh check <CODE>`) cannot be run. The notes file `Agent/notes/<CODE>.md` will need to be created manually (or the script restored). **Need to confirm with human** (Q8).

### 4.6 Paper vs code — practice block (NEW)

Paper Methods §2.3 (p.6) describes a **no-go-only practice block**. The code (`block_sequence.xlsx`) has **no no-go-only block**: practice is `go_only_prac` (18 go) + `go_nogo_prac` (14 go / 4 nogo). `gopractice.xlsx` (18 go trials) exists but is **not referenced** by the code (dead file). This is a paper-vs-code disagreement that needs the human to say which is authoritative.

### 4.7 Paper vs code — main-block count (NEW)

Paper §2.3 says the main experiment had "five go-only blocks and eight mixed go/no-go blocks" = **13 main blocks**. `block_sequence.xlsx` has 16 rows total = **13 main** (5 `go_only` + 8 `go_nogo`) + **2 practice** (`go_only_prac` + `go_nogo_prac`). So the code and paper **agree on 13 main blocks**; the only difference is the paper describes practice separately and the xlsx lists it in the same table. **Likely a non-issue — confirm the code's block layout is authoritative.**

### 4.8 Anomalies

- **Space in drop name**: `MouseTracking Data` — all paths must be quoted.
- **Empty file**: `Program_final_german/readme.md` is 0 bytes. Skip.
- **Instruction file with space**: `Program_final_german/Instructions (1).pptx` — space and `(1)` suffix in filename.
- **Participants 2 and 4 have only session `a`**: documented in paper as "did not attend the second session." Not an anomaly — expected. Report but do not impute.
- **Leftover filename**: `hover_up_click_007b_review.psyexp` / `_lastrun.py` carry a stale `hover_up_click` name but `expName = go_nogo_dm` internally (one paradigm — see A10).

---

## 5. Stages that will run

| Stage | Agent | What it will do for this drop |
|---|---|---|
| 02 | `02_restructure` | Write rename map: 50 raw CSVs → `sourcedata/raw/`; 3 R scripts → `code/`; 7 paradigm files → `paradigm/psychopy/`; 1 PDF → `literature/`; 1 README → `literature/`; 1 compiled CSV → (pending A5). Dry-run, then human approves `--apply`. |
| 03 | `03_code-check` | Re-run `check_code.py` on `Projects/<CODE>/code/` and `paradigm/psychopy/`. Confirm the 2 BOM errors and 8 path warnings persist (they will — they are in the source). Report run order and dependencies. |
| 04 | `04_paper-claims` | Extract numeric results from paper: ICC values (go: .75–.85, no-go: .59–.83), error rates (no-go 12%, go 4%), RT values, F-statistics. Write `code/paper_claims.yaml`. |
| 05 | `05_data-description` | Wire the R pipeline into the derivation contract. **Blocker:** R scripts have absolute Windows paths that must be fixed before they can run. After path fixes, run `1. compute_stopping.R` → `2. ER_RT.R` → `3. Kinematics.R` to produce `derivatives/`. Write `bids_data/dataset_description.json`. Human chooses primary/secondary outcomes. |
| 06 | `06_project-description` | Write `<CODE>_description.json` from paper, restructured data, and recorded outcomes. |
| 07 | `07_paradigm` | **Blocker:** `go_nogo_dm.py` has a BOM syntax error. Must strip BOM before PsychoPy verification. Then verify `go_nogo_dm.py` runs in the `psychopy` mamba env. |
| 08 | `08_check` | Read-only audit of finished project. |

**Stages that may be skipped or deferred:**
- If the human decides `go_nogo_compiledData.csv` is the analysis-ready table and the R pipeline is not needed, stage 05 could be simplified. But this needs confirmation.
- If the human decides the paradigm is only for reference and does not need to run, stage 07 could be deferred. But BEEHub's purpose includes making the paradigm runnable, so this is recommended.

---

## 6. Assumptions

| # | Assumption | Rationale |
|---|---|---|
| A1 | Session mapping: `a` → `ses-01`, `b` → `ses-02` | `README_MT.md` (p.34): "a / b suffix — session: a = Session 1, b = Session 2 (sessions ~1 week apart)". Paper Methods §2.1 (p.5) confirms two sessions. **Confirmed by human 2026-09-24.** |
| A2 | Task label: `task-gonogo` | Paper title and `README_MT.md` both use "go/no-go". BIDS `task-` must be alphanumeric: `gonogo`. **Confirmed by human 2026-09-24.** |
| A3 | Project code: **not invented** — awaiting human decision. | Per rules, I do not invent a project code. Suggest `MT` (MouseTracking) or `GNG` (GoNoGo) or `MAH` (Mahesan). **Needs human decision.** |
| A4 | `README_MT.md` goes to `literature/` | It is an author-provided orientation document, not analysis code or paradigm. **Confirmed by human 2026-09-24.** |
| A5 | `go_nogo_compiledData.csv` (45 MB) is kept in `code/` as a reference compilation, not used as the primary analysis table. The R pipeline output (`derivatives/`) is the authoritative analysis table. | The README describes it as "pre-compiled … trimmed down to the columns most relevant for analysis" but the R scripts do not read from it. **Resolved by human 2026-09-24 (Q4/Q6): keep as reference, exclude flagged columns from statistics; raw files are column authority.** |
| A6 | `Instructions (1).pptx` goes to `literature/` | It is an instruction document, not a paradigm condition file. The `.png` slides (`Slide7.PNG`, `Slide8.PNG`) go to `paradigm/psychopy/` because they are referenced by the `.psyexp`. |
| A7 | Participants 2 and 4 (missing session `b`) are **not imputed** and **not dropped** — they are kept in `sourcedata/raw/` with their single session, and flagged in `participants.tsv` as having only `ses-01`. The paper says they were "excluded from all analyses," so they will be absent from `derivatives/` but present in `bids_data/` with a note. | BEEHub rule: "Anomalies are reported, not fixed." The paper documents their exclusion. **Confirmed by human 2026-09-24.** |
| A8 | The 2 BOM errors in `.py` files will be fixed (BOM stripped) during `07_paradigm`, not during `02_restructure`. The BOM is a content issue, not a naming issue. | `02_restructure` handles renames/copies; content fixes belong to the paradigm stage. **Needs human confirmation.** |
| A9 | The absolute Windows paths in R scripts will be fixed during `05_data-description` when wiring the derivation contract. | The derivation contract requires `--input`/`--output` flags; the hardcoded paths will be replaced. **Needs human confirmation.** |
| A10 | `go_nogo_dm.py` is the generated script of `hover_up_click_007b_review.psyexp`; the three files (`go_nogo_dm.py`, `hover_up_click_007b_review.psyexp`, `hover_up_click_007b_review_lastrun.py`) are **one** paradigm (`go_nogo_dm`), not practice/main and not separate tasks. The `.psyexp` is the paradigm source; `go_nogo_dm.py` is its generated script; `_lastrun.py` is a re-saved copy of the same script. | `go_nogo_dm.py` line 43: `expName = 'go_nogo_dm'  # from the Builder filename that created this script`; `hover_up_click_007b_review.psyexp` line 49: `expName = go_nogo_dm`; `hover_up_click_007b_review_lastrun.py` line 43: `expName = 'go_nogo_dm'`. All 50 raw session files are named `*_go_nogo_dm_*` with `expName` = `go_nogo_dm`; none reference `hover_up_click`. The `hover_up_click_007b_review` filename is a leftover from an earlier Builder version. **Resolved by human 2026-09-24: one paradigm.** |
| A11 | `go_nogo_compiledData.csv` is kept in `code/` as a reference compilation. It is a **lossy projection** of the raw data: 15 columns (endpoints, RT-ish, no trajectories/kinematics, no `accuracy_type`/`rt`/`correct`, no `block_type`/`session`), only the 8 mixed go/no-go blocks (block_number ∈ {4,5,7,8,10,11,13,14}), 384 go + 96 nogo per participant. Its flagged columns (mouse buttons, `iti_duration`, `trials_count`) are **kept but excluded from statistics**. The raw files (206 columns incl. all kinematics) are the column authority. | Verified against `go_nogo.xlsx` (60 trials: 48 go/12 nogo) and paper p.8–9 ("60 trials each; 80% go, 20% no-go"). **Resolved by human 2026-09-24 (Q4/Q6): keep, exclude flagged columns from statistics.** |

---

## 7. Tell me before I start

1. **Project code**: What is the project code? Suggest `MT` (MouseTracking), `GNG` (GoNoGo), or `MAH` (Mahesan). Or choose your own. → **fill-in** — **OPEN**
2. **Session mapping rule**: Confirm `a` → `ses-01`, `b` → `ses-02`? → **ANSWERED: yes (2026-09-24)**
3. **Task label**: Confirm `task-gonogo`? → **ANSWERED: yes, `gonogo` (2026-09-24)**
4. **Column authority**: When there are multiple tables (raw CSVs, `go_nogo_compiledData.csv`, R pipeline output in `derivatives/`), which is the column authority for the BIDS `task-gonogo_beh.tsv` files? → **ANSWERED (2026-09-24): the raw CSVs are the column authority (206 columns incl. all kinematics); the compiled CSV is a lossy reference kept but with its flagged columns excluded from statistics; the R pipeline output is the derivatives table.**
5. **Participants 2 and 4**: Confirm they are kept in `bids_data/` with only `ses-01` and flagged, not imputed or dropped? → **ANSWERED: yes (2026-09-24)**
6. **`go_nogo_compiledData.csv`**: Keep as reference in `code/`, or is it the analysis table? → **ANSWERED (2026-09-24): keep as reference; flagged columns (mouse buttons, `iti_duration`, `trials_count`) kept but excluded from statistics.**
7. **`hover_up_click_007b_review.psyexp`**: Is this part of the same paradigm or a separate task? → **ANSWERED (2026-09-24): one paradigm (`go_nogo_dm`). The `.psyexp` is the source; `go_nogo_dm.py` is its generated script; `_lastrun.py` is a re-saved copy. Verify `go_nogo_dm.py` in `07_paradigm`.**
8. **Notes file**: `Agent/notes/project_notes.sh` does not exist. Should I create `Agent/notes/<CODE>.md` manually, or is the script located elsewhere? → **fill-in** — **OPEN** (see §4.5; the script is absent from this checkout)
9. **Practice-block discrepancy**: Paper §2.3 says practice included a **no-go-only** block; `block_sequence.xlsx` defines practice as `go_only_prac` (18 go) + `go_nogo_prac` (14 go / 4 nogo) — there is **no no-go-only block** in the code. `gopractice.xlsx` (18 go, unreferenced by the code) is a dead file. Which is authoritative? → **fill-in** (record as anomaly / which to trust)
10. **Main-block count**: Paper §2.3 says "five go-only blocks and eight mixed go/no-go blocks" = 13 main blocks; `block_sequence.xlsx` lists 15 main blocks (5 `go_only` + 8 `go_nogo`) **plus** 2 practice blocks. The 13 vs 15 count differs because the paper counts practice separately. Is the code's 16-block layout (2 practice + 15 main) the truth? → **fill-in** (confirm code is authoritative for block layout)

---

## 8. Next command

**Open questions remaining:** Q1 (project code) and Q8 (notes file), plus Q9/Q10 (paper-vs-code practice-block and main-block-count discrepancies — likely non-issues, confirm).

Once the human answers:

1. Record **all** answers (Q1–Q10) in `Agent/notes/<CODE>.md` (create the file if it does not exist — `project_notes.sh` is absent, see §4.5).
2. Run: `opencode --agent 02_restructure`
