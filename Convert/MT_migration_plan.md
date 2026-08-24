# MT Migration Plan — Stage 1

**Source:** `Convert/MouseTracking Data/`
**Target:** `Projects/MT/`
**Task label:** `gonogo` (per `Agent/notes/MT.md`)
**Project notes:** `Agent/notes/MT.md` — all questions answered, exit 0.

---

## 1. Inventory

### Participants and sessions (from `ls` of 50 CSVs)

| Participant | Sessions present | BIDS sessions |
|-------------|------------------|---------------|
| 1           | a, b             | ses-01, ses-02 |
| 2           | a                | ses-01 |
| 3–26        | a, b             | ses-01, ses-02 |

- **26 participants**, **50 raw data files** (4 are session-a-only: participants 2 and 4).
- Sessions: `a` → `ses-01`, `b` → `ses-02` (confirmed chronological by acquisition dates in filenames).
- **Anomaly:** Participants 2 and 4 are incomplete (session a only).

### File counts and sizes

| Category | Count | Size |
|----------|-------|------|
| Raw `.csv` files (per participant-session) | 50 | ~952 MB (952,198,016 bytes) |
| `go_nogo_compiledData.csv` (compiled/analysed) | 1 | ~43 MB (45,138,414 bytes, 23,040 rows) |
| PsychoPy program files | 12 | ~792 KB |
| PDF preprint | 1 | ~1.3 MB |
| README files | 2 | ~3 KB |
| `__pycache__/` artefact | 1 | ~14 KB (exclude) |
| **Total source files** | **~66** | **~997 MB** |

### Column analysis

- **Raw PsychoPy CSV:** 206 columns (including trailing empty column). Contains trial-by-trial mouse trajectory data (x/y positions at high frequency stored as JSON-like arrays in single cells), response data, timing data, block metadata, and participant/session/date fields at the end.
- **Compiled CSV (column authority):** 15 columns — `block_number, trials_count, digit, trial_type, correct_response, mouse_resp.x, mouse_resp.y, mouse_resp.leftButton, mouse_resp.midButton, mouse_resp.rightButton, mouse_resp.time, click_pos_x, click_pos_y, iti_duration, participant`.
- Per project notes: the compiled CSV header defines the *analysed* column set. Each raw CSV must be cleaned to this column set when producing `_beh.tsv` files.

---

## 2. Rename Map

### 2a. Raw data files → `bids_data/sub-<NNN>/ses-<NN>/beh/`

Every `Raw Data/<N><letter>_go_nogo_dm_<date>.csv` becomes one `_beh.tsv` file.

| Current file | BIDS destination | Reason |
|---|---|---|
| `Raw Data/1a_go_nogo_dm_*.csv` | `bids_data/sub-001/ses-01/beh/sub-001_ses-01_task-gonogo_beh.tsv` | Participant 1, session a → ses-01 |
| `Raw Data/1b_go_nogo_dm_*.csv` | `bids_data/sub-001/ses-02/beh/sub-001_ses-02_task-gonogo_beh.tsv` | Participant 1, session b → ses-02 |
| `Raw Data/2a_go_nogo_dm_*.csv` | `bids_data/sub-002/ses-01/beh/sub-002_ses-01_task-gonogo_beh.tsv` | Participant 2, session a → ses-01 (incomplete: no ses-02) |
| `Raw Data/4a_go_nogo_dm_*.csv` | `bids_data/sub-004/ses-01/beh/sub-004_ses-01_task-gonogo_beh.tsv` | Participant 4, session a → ses-01 (incomplete: no ses-02) |
| `Raw Data/5a_go_nogo_dm_*.csv` | `bids_data/sub-005/ses-01/beh/sub-005_ses-01_task-gonogo_beh.tsv` | Participant 5, session a → ses-01 |
| `Raw Data/5b_go_nogo_dm_*.csv` | `bids_data/sub-005/ses-02/beh/sub-005_ses-02_task-gonogo_beh.tsv` | Participant 5, session b → ses-02 |
| ... (pattern continues for all 26 participants) | ... | ... |
| `Raw Data/26b_go_nogo_dm_*.csv` | `bids_data/sub-026/ses-02/beh/sub-026_ses-02_task-gonogo_beh.tsv` | Participant 26, session b → ses-02 |

**Naming convention:** `<N><letter>` → `sub-<NNN>` (zero-pad to 3 digits), `<letter>`: `a` → `ses-01`, `b` → `ses-02`. The `_go_nogo_dm_<date>.csv` suffix is replaced by the BIDS-compliant `_task-gonogo_beh.tsv` suffix.

### 2b. Compiled CSV → `sourcedata/raw/`

| Current file | BIDS destination | Reason |
|---|---|---|
| `go_nogo_compiledData.csv` | `sourcedata/raw/go_nogo_compiledData.csv` | Original analysis file, untouched — preserves column authority reference |

### 2c. PDF → `literature/`

| Current file | BIDS destination | Reason |
|---|---|---|
| `Mahesan et al. 2026 - bioRxiv.pdf` | `literature/Mahesan_2026_biorxiv.pdf` | Per project notes: renamed to author-year-keyword format |

### 2d. Paradigm files → `paradigm/psychopy/`

| Current file | BIDS destination | Reason |
|---|---|---|
| `Program_final_german/go_nogo_dm.py` | `paradigm/psychopy/go_nogo_dm.py` | Main PsychoPy experiment script |
| `Program_final_german/hover_up_click_007b_review.psyexp` | `paradigm/psychopy/hover_up_click_007b_review.psyexp` | PsychoPy experiment definition |
| `Program_final_german/hover_up_click_007b_review_lastrun.py` | `paradigm/psychopy/hover_up_click_007b_review_lastrun.py` | Auto-generated from matching .psyexp — must stay paired |
| `Program_final_german/go_nogo.xlsx` | `paradigm/psychopy/go_nogo.xlsx` | Condition table, referenced by filename from PsychoPy script |
| `Program_final_german/go_nogo_prac.xlsx` | `paradigm/psychopy/go_nogo_prac.xlsx` | Condition table, referenced by filename |
| `Program_final_german/go_only.xlsx` | `paradigm/psychopy/go_only.xlsx` | Condition table, referenced by filename |
| `Program_final_german/gopractice.xlsx` | `paradigm/psychopy/gopractice.xlsx` | Condition table, referenced by filename |
| `Program_final_german/block_sequence.xlsx` | `paradigm/psychopy/block_sequence.xlsx` | Block sequence table, referenced by filename |
| `Program_final_german/Slide7.PNG` | `paradigm/psychopy/Slide7.PNG` | Stimulus image — **never rename** (hard-coded references) |
| `Program_final_german/Slide8.PNG` | `paradigm/psychopy/Slide8.PNG` | Stimulus image — **never rename** (hard-coded references) |
| `Program_final_german/Instructions (1).pptx` | `literature/instructions_de.pptx` | Per project notes: space/parentheses removed; goes to literature as instructional material |
| `Program_final_german/readme.md` | `paradigm/psychopy/readme.md` | Empty file (0 bytes) — keep as-is for documentation |

### 2e. README files

| Current file | BIDS destination | Reason |
|---|---|---|
| `README_MT.md` | `bids_data/README.md` | Project-level README in bids_data |
| `Program_final_german/readme.md` | `paradigm/psychopy/readme.md` | Already listed under paradigm above |

---

## 3. Content transformation (clean script)

The `clean_MT.py` script must:

1. Read each raw PsychoPy CSV (UTF-8 with BOM, 206 columns).
2. Keep **exactly** the 15 columns from `go_nogo_compiledData.csv` header:
   `block_number, trials_count, digit, trial_type, correct_response, mouse_resp.x, mouse_resp.y, mouse_resp.leftButton, mouse_resp.midButton, mouse_resp.rightButton, mouse_resp.time, click_pos_x, click_pos_y, iti_duration, participant`
3. Write as `.tsv` (tab-separated).
4. Add the `_beh.json` column dictionary sidecar at the `bids_data/` root (inherited by all runs), documenting:
   - The 15 kept columns with types
   - All 191 dropped columns (list them)
5. The `participant` column value in the source is like `1a` or `26b` — this is a byproduct of the cleaned file and will be replaced by BIDS identifiers in the directory structure.

---

## 4. Exclusions

| Pattern | Action |
|---|---|
| `__pycache__/` directory | Exclude; already exists in Convert/, add to `.gitignore` |
| `*.pyc` files | Exclude; add to `.gitignore` |
| Prior migration artifacts (`migrate_MT.sh`, `clean_MT.py`, `MT_migration_plan.md`, `migrate_MT.log`) | Move aside (renamed with `_STALE` suffix) — do not delete |

---

## 5. Open questions for the PI

(As flagged in `Agent/notes/MT.md` — not for me to decide)

1. **Primary vs secondary outcome measures:** Three candidates exist. The PI must choose which is primary and which are secondary.
2. **Analysis scripts location:** The R scripts (`1. compute_stopping.R`, `2. ER_RT.R`, `3. Kinematics.R`) referenced in the README are NOT present in the drop. The PI should locate them.

---

## 6. Target layout summary

```
Projects/MT/
├── MT_description.json             (written by Describe agent, not this migration)
├── bids_data/
│   ├── dataset_description.json    (written by Describe agent)
│   ├── participants.tsv            (one row per subject — Describe agent or migration)
│   ├── participants.json           (column dictionary — migration or Describe)
│   ├── README.md                   ← from README_MT.md
│   ├── task-gonogo_beh.json        ← column dictionary (15 kept + 191 dropped)
│   └── sub-001/
│       ├── ses-01/
│       │   └── beh/
│       │       ├── sub-001_ses-01_task-gonogo_beh.tsv
│       │       └── sub-001_ses-01_session.json
│       ├── ses-02/
│       │   └── beh/
│       │       ├── sub-001_ses-02_task-gonogo_beh.tsv
│       │       └── sub-001_ses-02_session.json
│       └── ... (sub-002 through sub-026, same structure)
├── literature/
│   ├── Mahesan_2026_biorxiv.pdf
│   └── instructions_de.pptx
├── paradigm/
│   └── psychopy/
│       ├── go_nogo_dm.py
│       ├── hover_up_click_007b_review.psyexp
│       ├── hover_up_click_007b_review_lastrun.py
│       ├── go_nogo.xlsx
│       ├── go_nogo_prac.xlsx
│       ├── go_only.xlsx
│       ├── gopractice.xlsx
│       ├── block_sequence.xlsx
│       ├── Slide7.PNG
│       ├── Slide8.PNG
│       └── readme.md
└── sourcedata/
    └── raw/
        └── go_nogo_compiledData.csv
```

---

## 7. Verification commands (post-migration)

```bash
# Tree matches target layout?
find Projects/MT -maxdepth 2 -type d

# Every source PDF arrived?
find Projects/MT/literature -name '*.pdf'

# Nothing PDF-like left in Convert/MouseTracking Data/?
find "Convert/MouseTracking Data" -name '*.pdf'

# BIDS data files present?
ls Projects/MT/bids_data/sub-*/ses-*/beh | head

# File count: 50 raw CSVs = 50 _beh.tsv files
find Projects/MT/bids_data -name '*_beh.tsv' | wc -l

# Originals preserved in sourcedata/raw/
ls Projects/MT/sourcedata/raw/
```
