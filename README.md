# Adding a New Project to BEE Hub

## What is BEE Hub?

**BEE Hub** (Behavioral Experimental Exploration Hub) is an open-source, Git-versioned platform for storing, analysing, and discovering behavioral paradigms alongside their critical validation metrics. The core problem it addresses is the paradigm selection bottleneck: when designing a new experiment, researchers currently have no efficient way to identify a paradigm with known reliability, demonstrated effects, and established statistical power. General sharing platforms such as OSF or Pavlovia facilitate data sharing but lack dedicated infrastructure for the metrics that matter most for experimental implementation — test-retest reliability (ICC), effect sizes, sample characteristics, and cognitive domain classification.

BEE Hub fills this gap by hosting curated, piloted, or published experiments together with their datasets, analysis code, and a standardized reliability profile for each paradigm. Every project follows a consistent BIDS-inspired folder structure, is version-controlled, and adheres to FAIR principles (Findable, Accessible, Interoperable, Reusable). The interactive dashboard allows researchers to search, filter, and compare paradigms by modality, cognitive domain, sample size, ICC, and consistency — making reliability benchmarks directly visible and comparable across studies. The structured output is also designed to be meta-analysis ready, enabling large-scale synthesis of field-wide reproducibility patterns.

---

This document covers everything needed to add a new project so that the full BEE Hub pipeline — analysis, HTML reports, interactive dashboard, and paradigm pages — discovers and processes it automatically.

---

## Overview: How the Pipeline Works

The three scripts run in order. Each one depends on the output of the previous:

```
01_multi_project_overview.py   →   reads  TSV files / participants.tsv
                                          bibliography.json  (optional)
                                   writes MYPROJECT_overview.html
                                          MYPROJECT_data.json

02_generate_paradigm.py        →   reads  MYPROJECT_data.json
                                          paradigm/ folder
                                   writes MYPROJECT_paradigm.html

03_generate_dashboard.py       →   reads  MYPROJECT_data.json  (all projects)
                                   writes dashboard.html
```

Run them from the `BEEHub/` root:

```bash
python code/01_multi_project_overview.py
python code/02_generate_paradigm.py
python code/03_generate_dashboard.py
```

Or pass a custom base path as the first argument:

```bash
python code/01_multi_project_overview.py /path/to/BEEHub
```

---

## Step 1 — Create the Project Folder

All projects live under `BEEHub/Projects/`. The folder name **is** the project identifier and must match the name used everywhere else (filenames, BIDS labels, Python dict key):

- All-caps alphanumeric only: `MYPROJECT`
- No spaces, hyphens, or special characters
- The folder name and the identifier must be identical — a mismatch is the most common reason a project silently fails

```
BEEHub/
├── beehub_logo.svg              ← dashboard header logo (right side)
├── logo_memoslap.png            ← dashboard header logo (left side)
└── Projects/
    └── MYPROJECT/
        ├── participants.tsv
        ├── bibliography.json        ← optional, see Step 6
        └── bids_data/
            └── sub-001/
                ├── ses-1/
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_RT_beh.tsv
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_RT_beh.json
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_ACC_beh.tsv
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_ACC_beh.json
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_ACCBIN_beh.tsv
                │   └── sub-001_ses-1_task-MYPROJECT_acq-1_ACCBIN_beh.json
                └── ses-2/
                    └── ...
```

**BIDS filename rule:**
```
sub-<label>_ses-<label>_task-<PROJECTNAME>_acq-<label>_<OUTCOME>_beh.tsv
```
The `task-` field must match the project folder name exactly (case-sensitive). The `acq-` field can be any integer; it is parsed from the filename but not used analytically.

---

## Step 2 — participants.tsv

Place this file directly in `BEEHub/Projects/MYPROJECT/`. It is required for demographics and for linking subjects across sessions.

Required columns (tab-separated, `n/a` for missing values):

| Column | Type | Description |
|---|---|---|
| `participant_id` | string | BIDS subject label, e.g. `sub-001` |
| `sex` | string | `male`, `female`, or `non binary` |
| `age` | float | Age in years |

Rows where `participant_id` is `n/a` are automatically excluded from all analyses.

**Example:**

```tsv
participant_id	sex	age
sub-001	female	24.3
sub-002	male	31.0
sub-003	n/a	n/a
```

---

## Step 3 — Outcome TSV Files

Each session requires **three separate TSV files**, one per outcome type. The script loads them by suffix: `*_RT_beh.tsv`, `*_ACC_beh.tsv`, `*_ACCBIN_beh.tsv`. At least one of RT or ACCBIN must be present for a project to be analysed.

The first two columns are always `onset` and `duration`. The third is the primary outcome. Additional columns are optional but should be consistent across all three files for the same session.

---

### 3a. `*_RT_beh.tsv` — Reaction Time

| Column | Type | Required | Description |
|---|---|---|---|
| `onset` | float | ✅ | Stimulus onset in **seconds** from experiment start |
| `duration` | float | ✅ | Time from stimulus onset to response, in **seconds** |
| `response_time_ms` | float | ✅ | Reaction time in **milliseconds** — this is the primary analysis column |
| `trial_type` | string | ✅ | Condition label, e.g. `learning`, `control`. No spaces — use underscores |
| `learning_stage` | string | optional | Within-session stage label, e.g. `LS1`, `Block2`. Include when your paradigm has meaningful sub-phases — the individual project report will automatically generate stage progression charts. Omit or use `n/a` if not applicable |
| `stimulus` | string | optional | Filename or identifier of the presented stimulus |
| `response_port` | string / int | optional | Hardware response port number, or `n/a` |

**Example:**

```tsv
onset	duration	response_time_ms	trial_type	learning_stage	stimulus	response_port
0.000	1.141	1141.2	learning	LS1	stimuli/STIM_000.jpg	99
3.598	0.696	695.6	learning	LS1	stimuli/STIM_001.jpg	100
8.114	1.320	1320.0	control	LS1	stimuli/STIM_002.jpg	99
```

---

### 3b. `*_ACC_beh.tsv` — Categorical Accuracy

| Column | Type | Required | Description |
|---|---|---|---|
| `onset` | float | ✅ | Same trial onsets as `_RT_beh.tsv` |
| `duration` | float | ✅ | Same durations as `_RT_beh.tsv` |
| `accuracy` | string | ✅ | `correct`, `incorrect`, or `n/a` |
| `trial_type` | string | ✅ | Same condition labels as `_RT_beh.tsv` |
| `learning_stage` | string | optional | Same stage labels as `_RT_beh.tsv` |
| `stimulus` | string | optional | Same stimulus identifiers |

**Example:**

```tsv
onset	duration	accuracy	trial_type	learning_stage	stimulus
0.000	1.141	correct	learning	LS1	stimuli/STIM_000.jpg
3.598	0.696	correct	learning	LS1	stimuli/STIM_001.jpg
8.114	1.320	incorrect	control	LS1	stimuli/STIM_002.jpg
```

---

### 3c. `*_ACCBIN_beh.tsv` — Binary Accuracy

This file is used for all quantitative accuracy statistics and reliability calculations. The `accuracy_binary` column must be integer `0` or `1` — **not** a float or a string.

| Column | Type | Required | Description |
|---|---|---|---|
| `onset` | float | ✅ | Same trial onsets as `_RT_beh.tsv` |
| `duration` | float | ✅ | Same durations as `_RT_beh.tsv` |
| `accuracy_binary` | int | ✅ | `1` = correct, `0` = incorrect, `n/a` = missing |
| `trial_type` | string | ✅ | Same condition labels as `_RT_beh.tsv` |
| `learning_stage` | string | optional | Same stage labels as `_RT_beh.tsv` |
| `stimulus` | string | optional | Same stimulus identifiers |

**Example:**

```tsv
onset	duration	accuracy_binary	trial_type	learning_stage	stimulus
0.000	1.141	1	learning	LS1	stimuli/STIM_000.jpg
3.598	0.696	1	learning	LS1	stimuli/STIM_001.jpg
8.114	1.320	0	control	LS1	stimuli/STIM_002.jpg
```

---

## Step 4 — JSON Sidecar Files

Each TSV must have a matching JSON sidecar with the same stem (e.g. `sub-001_ses-1_task-MYPROJECT_acq-1_RT_beh.json`). The sidecar is not read by any analysis script but is required for BIDS compliance. Minimum content:

```json
{
  "TaskName": "MYPROJECT",
  "TaskDescription": "Brief description of the task.",
  "onset":            { "Description": "Stimulus onset in seconds from t0.", "Units": "seconds" },
  "duration":         { "Description": "Response time in seconds.",           "Units": "seconds" },
  "response_time_ms": { "Description": "Reaction time.",                      "Units": "milliseconds" }
}
```

---

## Step 5 — Register the Project in `01_multi_project_overview.py`

Open `code/01_multi_project_overview.py` and add an entry to `self.project_descriptions` inside `ProjectOverviewGenerator.__init__`. This controls the metadata shown in the dashboard cards, filters, and project reports:

```python
'MYPROJECT': {
    'full_name':        'My New Paradigm',
    'description':      'One-sentence description of what participants do.',
    'modality':         'visual',           # visual | linguistic | visual-spatial | visual-emotional
    'cognitive_domain': 'working_memory',   # memory | working_memory | semantic_memory |
                                            # spatial_cognition | cognitive_control |
                                            # emotion_regulation
    'task_type':        'monitoring',       # learning | recognition | generation |
                                            # interference | monitoring | navigation |
                                            # encoding-retrieval | regulation
    'difficulty':       'moderate',         # easy | easy-moderate | moderate |
                                            # moderate-hard | hard | very_hard
},
```

If you skip this step the project still analyses correctly — it just shows `unknown` for all metadata fields and won't benefit from dashboard filtering.

---

## Step 6 — Add a Bibliography (optional but recommended)

Place a `bibliography.json` file directly in `BEEHub/Projects/MYPROJECT/`. When present, the individual project report (`MYPROJECT_overview.html`) automatically renders a **Related Publications** box with all entries sorted newest-first. The file is silently ignored if absent or unparseable.

### Supported formats

**v2 (recommended)** — a top-level `publications` array where each entry is a self-contained object:

```json
{
  "_schema": "bibliography_json_v2",
  "publications": [
    {
      "id": "pub_001",
      "title": "Full paper title here",
      "authors": ["Lastname A", "Lastname B", "Lastname C"],
      "journal": "Journal Name",
      "volume": "12",
      "pages": "45--67",
      "year": 2024,
      "doi": "10.1234/example.doi",
      "url": "https://doi.org/10.1234/example.doi",
      "open_access": true,
      "key_findings": {
        "reliability": {
          "behavioral_accuracy_icc": 0.80,
          "reaction_time_icc": 0.71
        }
      },
      "bibtex": "@article{...}"
    }
  ],
  "_metadata": {
    "project": "MYPROJECT",
    "last_updated": "2024-06-01"
  }
}
```

**v1 (legacy)** — flat dict with `citation_1`, `citation_2`, … sibling keys and an optional top-level `key_findings` block. Still parsed correctly but v2 is preferred for all new projects.

### Field reference

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | ✅ | Full paper title — rendered as a clickable link when `doi` or `url` is present |
| `authors` | array of strings | ✅ | Author list. Four or more entries are collapsed to `First Author et al.` in the display |
| `journal` | string | ✅ | Journal or venue name |
| `year` | integer | ✅ | Publication year — used for sorting newest-first; entries without a year sort to the bottom |
| `doi` | string | recommended | DOI without the `https://doi.org/` prefix |
| `url` | string | optional | Full URL — overrides the auto-generated DOI link if provided |
| `open_access` | boolean | optional | When `true`, an Open Access badge is shown on the publication card |
| `volume`, `pages` | string | optional | Displayed as a journal badge alongside the journal name |
| `key_findings.reliability` | object | optional | ICC and other reliability values from the publication — stored for downstream use, not currently rendered in the UI |
| `bibtex` | string | optional | Full BibTeX entry — stored for export, not rendered |

### Notes

- The file must be valid UTF-8 JSON. A parse error prints a warning and the publications box is silently omitted.
- In v1 legacy format the top-level `key_findings.reliability` block is automatically merged into the first citation so ICC values are not lost.

---

## Step 7 — Add a Paradigm Short Version (optional)

If you want the **Paradigm** button to appear on the project's dashboard card, place a short-version PsychoPy script at one of these locations (checked in order):

| Priority | Path |
|---|---|
| 1st (preferred) | `Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_paradigm_short/MYPROJECT_short_version.py` |
| 2nd | `Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_short_version.py` |
| 3rd | `Projects/MYPROJECT/paradigm/MYPROJECT_short_version.py` |

The folder name and all filenames must use the **exact same identifier** as the project folder. A mismatch in capitalisation or spelling (e.g. folder `OLMM` but file `OLLM_short_version.py`) will silently prevent the button from appearing.

To also enable the **Launch Interactive Demo** button on the paradigm page, place an HTML demo at:

```
Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_paradigm_short/MYPROJECT_demo.html
```

The full expected layout for a project with all assets is:

```
Projects/MYPROJECT/
├── participants.tsv
├── bibliography.json                        ← publications, see Step 6
├── bids_data/
│   └── ...
└── paradigm/
    ├── psychopy/
    │   ├── MYPROJECT_paradigm_short/
    │   │   ├── MYPROJECT_short_version.py   ← triggers Paradigm button
    │   │   ├── MYPROJECT_demo.html          ← triggers Launch Demo button
    │   │   └── Stimuli/
    │   │       └── ...
    │   └── MYPROJECT_full_version.py        ← full experiment (optional)
    └── presentation/
        └── ...                              ← Presentation software files (optional)
```

---

## Step 8 — Generated Output Files

After running the scripts, the following files are created automatically. **Do not edit them by hand** — they are regenerated each run:

| File | Created by | Description |
|---|---|---|
| `Projects/MYPROJECT/MYPROJECT_data.json` | `01_multi_project_overview.py` | Analysis results used by all downstream scripts |
| `Projects/MYPROJECT/MYPROJECT_overview.html` | `01_multi_project_overview.py` | Individual project report with violin plots, scatter plots, reliability radar, stage charts, and publications box |
| `Projects/MYPROJECT/MYPROJECT_paradigm.html` | `02_generate_paradigm.py` | Paradigm landing page with demo link and GitHub links (only created when a short version exists) |
| `dashboard.html` | `03_generate_dashboard.py` | Interactive multi-project dashboard with filters, ICC radars, and project cards |

The dashboard reads two logo files from the `BEEHub/` root (the same folder as `dashboard.html`). Both must be present for the header logos to display:

| File | Position |
|---|---|
| `logo_memoslap.png` | Left side of header |
| `beehub_logo.svg` | Right side of header |

---

## Reliability Metrics Reference

The analysis computes four reliability metrics per trial type, calculated per subject across sessions and then averaged. The dashboard filter and project cards display these values.

> **Important — task trials only:** ICC(3,1) and all other reliability metrics are computed exclusively on **task trial types**. Any `trial_type` value matching the following labels is automatically excluded: `control`, `rest`, `baseline`, `fixation`, `fix`, `instruction`, `pause`, `break`, `catch`, `null`. These conditions are stored separately in the JSON output as `control_reliability` but do not contribute to dashboard ICC charts or the overall ICC score shown on project cards.

| Metric | Source column | What it measures |
|---|---|---|
| **ICC(3,1)** (Intraclass Correlation) | `response_time_ms`, `accuracy_binary` | Two-way mixed model, consistency estimate. Session mean differences are partialled out but not penalised in the denominator. **Task trials only — control and rest conditions are always excluded.** Range −1 → 1; higher is better |
| **Pearson r** | `response_time_ms`, `accuracy_binary` | Linear correlation between Session 1 and Session 2 values. Sensitive to association, not absolute agreement |
| **Stability** (from Cohen's d) | `response_time_ms`, `accuracy_binary` | Absence of systematic shift between sessions. Displayed as `1 − (|d| / 2)`; range 0 → 1; higher means less practice or fatigue effect |
| **Consistency CV** | `response_time_ms`, `accuracy_binary` | Within-session trial-to-trial variability. Calculated as `(SD / Mean) × 100`; lower CV = more consistent responding |

Reliability is only calculated when:
- A subject has data in **at least 2 sessions**
- A subject has **at least 6 matched trials** in each of those sessions

Subjects with only one session contribute to descriptive statistics (demographics, condition means) but not to any reliability metric.

---

## Data Format Rules

| Rule | Detail |
|---|---|
| **File format** | Tab-separated (`\t`), UTF-8 encoded |
| **Missing values** | Always `n/a` (lowercase), never empty cells |
| **Column order** | `onset`, `duration`, primary-outcome column, then optional columns in any order |
| **Decimal separator** | Period `.` — never comma |
| **onset / duration units** | Always **seconds** |
| **response_time_ms units** | Always **milliseconds** |
| **accuracy_binary values** | Integer `0` or `1` only — not `0.0`, not `"correct"` |
| **trial_type values** | Consistent across all three TSVs for the same session; no spaces (use underscores) |
| **learning_stage values** | Consistent across all three TSVs; stages are sorted alphanumerically for progression charts |
| **Subject labels** | `sub-<digits>`, zero-padded to three digits recommended (`sub-001`) |
| **Session labels** | `ses-<digit(s)>`, e.g. `ses-1`, `ses-2` |
| **Project identifier** | Folder name, `task-` BIDS field, Python dict key, and all filenames must all use the **exact same string** |
| **bibliography.json** | Valid UTF-8 JSON; v2 schema with a top-level `publications` array preferred; parse errors are warned and the publications box is silently skipped |

---

## Checklist Before Running

- [ ] `Projects/MYPROJECT/` folder exists with the exact identifier
- [ ] `participants.tsv` present with `participant_id`, `sex`, `age` columns
- [ ] At least one subject has `bids_data/sub-XXX/ses-Y/` folder
- [ ] Each session has `*_RT_beh.tsv`, `*_ACC_beh.tsv`, `*_ACCBIN_beh.tsv` plus matching `.json` sidecars
- [ ] `task-` field in every filename matches the project folder name exactly
- [ ] `trial_type` column present and identical across all three TSV types per session
- [ ] `learning_stage` column included and consistent (if stages are meaningful)
- [ ] `accuracy_binary` values are integer `0` / `1`, not float or string
- [ ] No empty cells — all missing values are `n/a`
- [ ] Project description added to `self.project_descriptions` in `01_multi_project_overview.py`
- [ ] If providing a bibliography: `bibliography.json` placed in `Projects/MYPROJECT/`, valid UTF-8 JSON, v2 schema with a `publications` array
- [ ] If providing a short version: folder name and filename both use the exact project identifier
- [ ] `beehub_logo.svg` and `logo_memoslap.png` present in `BEEHub/` root for dashboard header logos
