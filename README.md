![BEE Hub](beehub_logo.png)

## What is Research BEE Hub?

**Research BEE Hub** (Research Behavioral Experiments Hub) is an open-source, Git-versioned platform for storing, analysing, and discovering behavioral paradigms alongside their critical validation metrics. The core problem it addresses is the paradigm selection bottleneck: when designing a new experiment, researchers currently have no efficient way to identify a paradigm with known reliability, demonstrated effects, and established statistical power. General sharing platforms such as OSF or Pavlovia facilitate data sharing but lack dedicated infrastructure for the metrics that also matter for experimental implementation — test-retest reliability (ICC), effect sizes, and sample characteristics.

Research BEE Hub fills this gap by hosting curated, piloted, or published experiments together with their datasets, analysis code, and a standardized reliability profile for each paradigm. Every project follows a consistent BIDS-inspired folder structure, is version-controlled, and adheres to FAIR principles (Findable, Accessible, Interoperable, Reusable). The interactive dashboard allows researchers to search, filter, and compare paradigms by modality, cognitive domain, sample size, and ICC — making reliability benchmarks directly visible and comparable across studies. The structured output is also designed to be meta-analysis ready, enabling large-scale synthesis of field-wide reproducibility patterns.

---

This document covers everything needed to add a new project so that the full BEE Hub pipeline — analysis, HTML reports, interactive dashboard, and paradigm pages — discovers and processes it automatically.

> **Two things must exist before any script will process your project:**
> 1. A correctly named and structured folder with BIDS-compliant TSV data files (Steps 1–4)
> 2. A `MYPROJECT_description.json` file with an `outcome_measures` array (Step 5)
>
> Without the TSV data the analysis script has nothing to compute. Without the description JSON all metadata fields fall back to `"unknown"` and the paradigm page renders with no content.

---

## Overview: How the Pipeline Works

### Before running the scripts — create your description JSON

Use the interactive web form **`01_description_form.html`** to generate a valid `MYPROJECT_description.json` without writing JSON by hand:

1. Open `BEEHub/code/01_description_form.html` in any modern browser (no server required — it runs fully offline)
2. Fill in the seven wizard steps: Identity → Description → Classification → Procedure → Software → **Outcome Measures** → Review & Download
3. The JSON preview on the right updates live as you type
4. Click **Download JSON File** — the file is saved to your Downloads folder
5. Move the downloaded file to `BEEHub/Projects/MYPROJECT/MYPROJECT_description.json`

The form validates required fields and prevents common mistakes. It is the recommended way to create description files for all new projects.

### The three analysis scripts run in order

Each one depends on the output of the previous:

```
[01_description_form.html]     ← browser tool, run first, produces description JSON

reliability_metrics.py         ← shared module, imported automatically (do not run directly)

01_multi_project_overview.py   →   reads  TSV files / participants.tsv
                                          MYPROJECT_description.json
                                          bibliography.json  (optional)
                                   writes MYPROJECT_overview.html
                                          MYPROJECT_data.json

02_generate_paradigm.py        →   reads  MYPROJECT_data.json
                                          MYPROJECT_description.json
                                          paradigm/ folder
                                   writes MYPROJECT_paradigm.html

03_generate_dashboard.py       →   reads  MYPROJECT_data.json  (all projects)
                                   writes dashboard.html
```

Run the scripts from the `BEEHub/` root:

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

> **This step is mandatory.** The analysis script (`01_multi_project_overview.py`) discovers projects by scanning `BEEHub/Projects/`. If the folder does not exist, or exists but contains no valid BIDS TSV files, the project is silently skipped.

All projects live under `BEEHub/Projects/`. The folder name **is** the project identifier:

- All-caps alphanumeric only: `MYPROJECT`
- No spaces, hyphens, or special characters
- The folder name must be **identical** in: the folder itself, the `task-` BIDS field inside every TSV filename, and the prefix of `MYPROJECT_description.json`

```
BEEHub/
├── beehub_logo.svg
├── logo_memoslap.png
└── Projects/
    └── MYPROJECT/
        ├── participants.tsv
        ├── MYPROJECT_description.json
        ├── bibliography.json            ← optional
        └── bids_data/
            └── sub-001/
                ├── ses-1/
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_ACCBIN_beh.tsv
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_ACCBIN_beh.json
                │   ├── sub-001_ses-1_task-MYPROJECT_acq-1_RT_beh.tsv
                │   └── sub-001_ses-1_task-MYPROJECT_acq-1_RT_beh.json
                └── ses-2/
                    └── ...
```

**BIDS filename rule:**
```
sub-<label>_ses-<label>_task-<PROJECTNAME>_acq-<label>_<OUTCOME>_beh.tsv
```
The `task-` field must match the project folder name exactly (case-sensitive). The `<OUTCOME>` suffix must match the `id` declared in `outcome_measures` (e.g. `ACCBIN`, `RT`).

---

## Step 2 — participants.tsv

Place this file directly in `BEEHub/Projects/MYPROJECT/`. Required columns (tab-separated):

| Column | Type | Description |
|---|---|---|
| `participant_id` | string | BIDS subject label, e.g. `sub-001` |
| `sex` | string | `male`, `female`, or `non binary` |
| `age` | float | Age in years |

Rows where `participant_id` is `n/a` are automatically excluded from all analyses.

---

## Step 3 — Outcome TSV Files

The pipeline loads outcome files by the `suffix` declared in `outcome_measures` (see Step 5). Each session folder should contain one TSV per outcome type you wish to analyse.

**Default outcomes** (used when `outcome_measures` is absent from the description JSON):

| Outcome ID | Suffix | Primary column | Role |
|---|---|---|---|
| `ACCBIN` | `*_ACCBIN_beh.tsv` | `accuracy_binary` | Binary accuracy (0/1) — primary visual outcome, ICC shown on dashboard card |
| `RT` | `*_RT_beh.tsv` | `response_time_ms` | Reaction time — filtered to correct trials when ACCBIN present; Within-session CV reported |

If you declare custom `outcome_measures` you only need to provide the TSV files that actually exist for your paradigm — missing files are silently skipped.

### 3a. `*_ACCBIN_beh.tsv` — Binary Accuracy (primary outcome)

| Column | Type | Required | Description |
|---|---|---|---|
| `onset` | float | ✅ | Stimulus onset in **seconds** |
| `duration` | float | ✅ | Trial duration in **seconds** |
| `accuracy_binary` | int | ✅ | `1` = correct, `0` = incorrect — integer only, never float or string |
| `trial_type` | string | ✅ | Condition label, e.g. `learning`, `control` |
| `learning_stage` | string | optional | Sub-phase label, e.g. `LS1`. Triggers stage progression charts when present |
| `stimulus` | string | optional | Stimulus filename or identifier |

**Example:**
```tsv
onset	duration	accuracy_binary	trial_type	learning_stage	stimulus
0.000	1.141	1	learning	LS1	stimuli/STIM_000.jpg
3.598	0.696	1	learning	LS1	stimuli/STIM_001.jpg
8.114	1.320	0	control	LS1	stimuli/STIM_002.jpg
```

### 3b. `*_RT_beh.tsv` — Reaction Time

| Column | Type | Required | Description |
|---|---|---|---|
| `onset` | float | ✅ | Stimulus onset in **seconds** |
| `duration` | float | ✅ | Trial duration in **seconds** |
| `response_time_ms` | float | ✅ | Reaction time in **milliseconds** |
| `trial_type` | string | ✅ | Same condition labels as ACCBIN file |
| `learning_stage` | string | optional | Same stage labels as ACCBIN file |
| `stimulus` | string | optional | Same stimulus identifiers |

> **Correct-trial filtering:** When an `ACCBIN` file is present and the RT outcome has `is_primary: true`, only trials where `accuracy_binary == 1` are used for RT reliability calculations. This mirrors the ICC computation in published reliability studies.

**Example:**
```tsv
onset	duration	response_time_ms	trial_type	learning_stage	stimulus
0.000	1.141	1141.2	learning	LS1	stimuli/STIM_000.jpg
3.598	0.696	695.6	learning	LS1	stimuli/STIM_001.jpg
8.114	1.320	1320.0	control	LS1	stimuli/STIM_002.jpg
```

---

## Step 4 — JSON Sidecar Files

Each TSV must have a matching JSON sidecar with the same filename stem. Minimum content:

```json
{
  "TaskName": "MYPROJECT",
  "TaskDescription": "Brief description of the task.",
  "onset":              { "Description": "Stimulus onset in seconds from t0.", "Units": "seconds" },
  "duration":           { "Description": "Trial duration in seconds.",         "Units": "seconds" },
  "accuracy_binary":    { "Description": "1 = correct, 0 = incorrect.",        "Levels": {"0": "incorrect", "1": "correct"} }
}
```

---

## Step 5 — Add a Description JSON

Place a `MYPROJECT_description.json` file directly in `BEEHub/Projects/MYPROJECT/`. This file drives all metadata shown in the overview HTML, paradigm page, and dashboard filters. It also controls which outcome files are loaded and in what priority order.

> **Recommended:** Use **`BEEHub/code/01_description_form.html`** — open in any browser, fill in the seven steps, click Download. The **Outcome Measures** step (Step 6 of the wizard) lets you define custom outcomes with priority, suffix, column name, and display flags.

### Outcome Measures — the most important field

The `outcome_measures` array tells the pipeline which TSV files to load, which column to read, how to display the data, and which outcome's ICC to show on the dashboard card.

```json
"outcome_measures": [
  {
    "id":               "ACCBIN",
    "suffix":           "_ACCBIN_beh.tsv",
    "column":           "accuracy_binary",
    "label":            "Accuracy",
    "axis_label":       "Accuracy (%)",
    "higher_is_better": true,
    "is_binary":        true,
    "is_primary":       false,
    "is_helper":        false,
    "display_priority": 1
  },
  {
    "id":               "RT",
    "suffix":           "_RT_beh.tsv",
    "column":           "response_time_ms",
    "label":            "Reaction Time",
    "axis_label":       "RT (ms)",
    "higher_is_better": false,
    "is_binary":        false,
    "is_primary":       true,
    "is_helper":        false,
    "display_priority": 2
  }
]
```

#### Field reference

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | string | — | Unique outcome identifier. Must match the `<OUTCOME>` suffix in TSV filenames (e.g. `ACCBIN` → `*_ACCBIN_beh.tsv`) |
| `suffix` | string | — | TSV filename suffix used to find the files, e.g. `_ACCBIN_beh.tsv` |
| `column` | string | — | Column name in the TSV that holds the primary values, e.g. `accuracy_binary`, `response_time_ms` |
| `label` | string | `id` | Human-readable label for plot titles and dashboard card |
| `axis_label` | string | `column` | Y-axis label on violin and scatter plots |
| `higher_is_better` | bool | `true` | Used for future display logic (currently stored, not rendered) |
| `is_binary` | bool | `false` | **True** when values are 0/1. Violin plots show subject-level mean percentages rather than raw trial values. **No CV or Accuracy % is computed or displayed** for binary outcomes — see note below |
| `is_primary` | bool | `false` | **True** for the RT outcome when correct-trial filtering is desired. Triggers RT filtering: only trials where the paired `ACCBIN` value equals 1 are included in RT reliability calculations |
| `is_helper` | bool | `false` | **True** to use this outcome for filtering only — it is loaded but **never plotted** and never gets its own chart divs. Use this for a pure binary mask that you do not want to display |
| `display_priority` | int | position in list | **1 = most important.** The dashboard card ICC stat shows the ICC of the highest-priority outcome that actually has data. If the priority-1 outcome has no data, the next in line is used automatically |

> **Binary accuracy and CV:** For outcomes with `is_binary: true`, the pipeline intentionally does **not** compute or display a within-session CV or an Accuracy % metric. Bernoulli CV is a deterministic re-expression of the mean (CV = √((1−p)/p) · 100), which means it carries no independent information beyond the ICC. Reliability for binary accuracy is instead fully represented by ICC(A), ICC(C), Cronbach's α (KR-20), and Pearson r. The dashboard card shows ICC only for binary primary outcomes — no CV column, no Accuracy % column.

#### Priority rules and fallback behaviour

The pipeline applies `display_priority` at every step:

1. **Which ICC appears on the dashboard card** — the outcome with the lowest `display_priority` number that has real ICC data wins. Label on the card reads `"{label} ICC"` (e.g. "Accuracy ICC", "Reaction Time ICC").
2. **Which violin/scatter plots are generated** — only outcomes where data was actually found. If `_ACCBIN_beh.tsv` is missing, no Accuracy violin is created; no empty boxes appear.
3. **Which CV slider appears in the dashboard** — only for continuous (non-binary) outcomes. Binary accuracy outcomes have no CV slider.

Default priority (used when `outcome_measures` is absent):

| Outcome | Priority | Role |
|---|---|---|
| ACCBIN | 1 | Binary accuracy — ICC shown on dashboard card |
| RT | 2 | Reaction time — CV computed and shown; filtered to correct trials via ACCBIN |

#### Adding a custom outcome

For paradigms that produce scores, distances, ratings, or other continuous measures, add a custom entry:

```json
{
  "id":               "SCORE",
  "suffix":           "_SCORE_beh.tsv",
  "column":           "score",
  "label":            "Game Score",
  "axis_label":       "Score (pts)",
  "higher_is_better": true,
  "is_binary":        false,
  "is_primary":       false,
  "is_helper":        false,
  "display_priority": 1
}
```

The `01_description_form.html` wizard generates these entries through the Outcome Measures step — no manual JSON editing required.

### Full schema

```json
{
  "full_name":          "My New Paradigm",
  "short_description":  "One sentence describing what participants do.",
  "long_description":   "Two to three paragraph scientific description.",
  "background":         "Neuroscientific context and prior literature.",
  "procedure":          "Session-by-session procedure.",
  "trial_structure":    "Exact trial timing per trial type.",
  "design":             "Repeated-measures details — sessions and intervals.",
  "modality":           "visual | auditory | linguistic | tactile | multimodal | virtual environment",
  "cognitive_domain":   "working memory | episodic memory | declarative memory | spatial memory | semantic memory | spatial cognition | cognitive control | emotion regulation | attention | language | perception | learning",
  "task_type":          "associative learning | recognition memory | n-back | color-word interference | cognitive reappraisal | virtual navigation | go/no-go | flanker | task switching | stop-signal",
  "language":           "german | english | french | spanish | dutch | italian | language-independent",
  "recording_modality": "behavioral | mri | eeg | pet | eye_tracking | fnirs | meg",
  "software_original":  "E-Prime 3.0 | PsychoPy | Presentation (Neurobehavioral Systems) | Unity 3D",
  "language_original":  "german | english | …",
  "implementations": [
    {
      "software":             "E-Prime 3.0",
      "type":                 "original",
      "languages_available":  ["german"],
      "folder":               "paradigm/eprime"
    },
    {
      "software":             "PsychoPy",
      "type":                 "compatible",
      "languages_available":  ["german", "english"],
      "folder":               "paradigm/psychopy"
    }
  ],
  "keywords":        ["keyword1", "keyword2"],
  "timing":          { "stimulus_duration_s": 2.5, "isi_range_s": [2, 4] },
  "software":        "E-Prime 3.0",
  "response_device": "two-button response box | keyboard | joystick",
  "n_sessions":      2,
  "outcome_measures": [ ... ]
}
```

### Content split between pages

| Field | `_overview.html` | `_paradigm.html` | Dashboard filter |
|---|---|---|---|
| `short_description` | ✅ header | ✅ | — |
| `long_description` | — | ✅ | — |
| `background` | ✅ header | ✅ | — |
| `procedure` | — | ✅ | — |
| `trial_structure` | — | ✅ | — |
| `design` | — | ✅ | — |
| `response_device` | — | ✅ | — |
| `timing` | — | ✅ chips | — |
| `keywords` | — | ✅ chips | — |
| `modality` | ✅ badge | ✅ | ✅ Stimulus Modality |
| `recording_modality` | — | ✅ | ✅ Recording Modality |
| `cognitive_domain` | ✅ badge | ✅ | ✅ Cognitive Domain |
| `task_type` | ✅ badge | ✅ | — |
| `language` | ✅ tag | — | ✅ Language |
| `implementations` | — | ✅ | — |
| `outcome_measures` | ✅ determines plots | ✅ determines plots | ✅ ICC card source |

---

## Step 6 — Reliability Metrics Module (`reliability_metrics.py`)

All statistical computation is centralised in `BEEHub/code/reliability_metrics.py`. This module is imported automatically by `01_multi_project_overview.py` — **do not run it directly**.

### How it works

For each outcome declared in `outcome_measures`, `compute_for_outcome()` is called with the loaded DataFrame and the outcome's column name. Results are keyed by `{id.lower()}_{metric}` — e.g. `accbin_icc`, `rt_cv_mean`. All per-outcome results are then merged into a single reliability dict per trial type and stored in the JSON under `reliability_metrics` (task trials) and `control_reliability` (control/rest conditions).

### Metrics computed

| Metric | Key pattern | Applies to | Description |
|---|---|---|---|
| **ICC(C,1)** | `{oid}_icc`, `{oid}_icc_ci_low/high`, `{oid}_icc_F/df1/df2/p` | All outcomes | Two-way mixed, consistency, single measures. Computed at learning-stage level when `learning_stage` column is present, otherwise at session level. Backed by pingouin ≥ 0.5 |
| **ICC(A,1)** | `{oid}_icc_agreement`, `{oid}_icc_agreement_ci_low/high`, …`_F/df1/df2/p` | All outcomes | Two-way mixed, absolute agreement. Penalises systematic session shifts. Shown on dashboard card in preference to ICC(C,1) when available |
| **Pearson r** | `{oid}_pearson_r` | All outcomes | Linear correlation between session 1 and session 2 subject-level means |
| **Session-shift stability** | `{oid}_session_shift_d` | All outcomes | Paired Cohen's d on session means. Small \|d\| = stable across retests. Displayed as `1 − (\|d\| / 2)` on radar (inverted — higher = more stable). Not a paradigm effect size |
| **Paradigm effect size** | `{oid}_paradigm_effect_size`, …`_ci_low/high`, …`_contrast`, …`_n` | All outcomes | Hedges' g for the within-session main contrast (e.g. last vs first learning stage, incongruent vs congruent). Bootstrapped 95% CI via pingouin |
| **Cronbach's α / KR-20** | `{oid}_cronbach_alpha`, …`_ci_low/high`, …`_n_items` | All outcomes | Internal consistency across session-1 trials. For binary outcomes this is KR-20. Capped at 100 items |
| **Within-session CV** | `{oid}_cv_mean`, `{oid}_cv_std` | **Continuous outcomes only** | Trial-level coefficient of variation within each session. **Not computed for binary outcomes** (Bernoulli CV is deterministic given the mean). The CV slider and CV radar spoke are absent for binary accuracy outcomes |

Reliability is only calculated when a subject has data in at least 2 sessions.

### ICC computation detail

ICC is computed at the **learning-stage level** when a `learning_stage` column is present — i.e. one mean per subject × stage × session — matching the methodology of published reliability studies (e.g. Abdelmotaleb et al., 2025). When no `learning_stage` column is present, session-level subject means are used as fallback. Both consistency ICC(C,1) and agreement ICC(A,1) are always reported.

### Adding a new metric

1. Add a `calculate_<name>(data1, data2)` static method to `ReliabilityMetrics`
2. Wire it up inside `compute_for_outcome` — add keys to the returned dict
3. Add a normalisation branch in `normalise_for_radar`
4. Add an entry to `METRIC_REGISTRY` with `id`, `label`, `radar_label`, `normalise`, and optionally `skip_for_binary: True` if the metric is not meaningful for 0/1 data

### Adding a new outcome type

No changes to `reliability_metrics.py` are needed. Declare the outcome in `outcome_measures` in the description JSON — the pipeline calls `compute_for_outcome` for it automatically.

---

## Step 7 — Register Metadata (legacy fallback)

If no `outcome_measures` is present in the description JSON, the pipeline falls back to `DEFAULT_OUTCOMES` defined in `reliability_metrics.py`:

```python
DEFAULT_OUTCOMES = [
  { "id": "ACCBIN", "display_priority": 1, "is_binary": True,  ... },
  { "id": "RT",     "display_priority": 2, "is_primary": True, ... },
]
```

This fallback loads `*_ACCBIN_beh.tsv` and `*_RT_beh.tsv` and behaves identically to an explicit declaration. Override it by adding `outcome_measures` to your description JSON.

---

## Step 8 — Add a Bibliography (optional but recommended)

Place a `bibliography.json` file directly in `BEEHub/Projects/MYPROJECT/`. When present, the individual project report renders a **Related Publications** box sorted newest-first.

**v2 schema (recommended):**

```json
{
  "_schema": "bibliography_json_v2",
  "publications": [
    {
      "id": "pub_001",
      "title": "Full paper title here",
      "authors": ["Lastname A", "Lastname B"],
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
  ]
}
```

---

## Step 9 — Add a Paradigm Short Version and Demo (optional)

Place a short-version PsychoPy script to trigger the **Paradigm** button on the dashboard card:

| Priority | Path |
|---|---|
| 1st | `Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_paradigm_short/MYPROJECT_short_version.py` |
| 2nd | `Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_short_version.py` |
| 3rd | `Projects/MYPROJECT/paradigm/MYPROJECT_short_version.py` |

To enable the **Launch Interactive Demo** button place a self-contained HTML demo at:
```
Projects/MYPROJECT/paradigm/psychopy/MYPROJECT_paradigm_short/MYPROJECT_demo.html
```

---

## Step 10 — Generated Output Files

| File | Created by | Description |
|---|---|---|
| `MYPROJECT_data.json` | `01_multi_project_overview.py` | Analysis results including `outcome_measures`, `primary_icc_key`, `reliability_metrics`, `control_reliability`, `data_by_condition` |
| `MYPROJECT_overview.html` | `01_multi_project_overview.py` | Per-project report. Charts are generated **only for outcomes with actual data** — no empty boxes for missing files |
| `MYPROJECT_paradigm.html` | `02_generate_paradigm.py` | Paradigm landing page |
| `dashboard.html` | `03_generate_dashboard.py` | Interactive dashboard. Project cards show ICC of the **highest-priority outcome with data**. CV stat is shown only for continuous primary outcomes — binary accuracy projects show 3 stat cells (Subjects, Mean Age, ICC) |

---

## Reliability Metrics Reference

> **Task trials only:** All reliability metrics exclude any `trial_type` matching: `control`, `rest`, `baseline`, `fixation`, `fix`, `instruction`, `pause`, `break`, `catch`, `null`, or any label starting with `ctrl` or `rest`. Control conditions are stored separately as `control_reliability` but do not contribute to dashboard ICC values.

| Metric | What it measures | Range | Binary outcomes |
|---|---|---|---|
| **ICC(A,1)** | Two-way mixed, absolute agreement — penalises systematic session drift | −1 → 1, higher better | ✅ computed |
| **ICC(C,1)** | Two-way mixed, consistency — session means partialled out | −1 → 1, higher better | ✅ computed |
| **Pearson r** | Linear correlation between session 1 and session 2 subject means | −1 → 1, higher better | ✅ computed |
| **Session-shift stability** (paired Cohen's d) | Absence of systematic shift between sessions. Displayed as `1 − (\|d\| / 2)` | 0 → 1, higher better | ✅ computed |
| **Paradigm effect size** (Hedges' g) | Within-session main contrast — paradigm sensitivity | unbounded, larger better | ✅ computed |
| **Cronbach's α / KR-20** | Within-session internal consistency across trials | −∞ → 1, higher better | ✅ computed (KR-20) |
| **Within-session CV** | Trial-level variability within a session. Displayed as `1 − CV/50` on radar | 0 → 1, higher better | ❌ not computed — Bernoulli CV is deterministic |

Reliability requires: subject present in ≥ 2 sessions with ≥ 1 value per session.

---

## Data Format Rules

| Rule | Detail |
|---|---|
| **File format** | Tab-separated (`\t`), UTF-8 encoded |
| **Missing values** | Always `n/a` (lowercase), never empty cells |
| **Decimal separator** | Period `.` — never comma |
| **onset / duration** | Always **seconds** |
| **response_time_ms** | Always **milliseconds** |
| **accuracy_binary** | Integer `0` or `1` only — not `0.0`, not `"correct"` |
| **trial_type** | Consistent across all TSVs for the same session; no spaces |
| **learning_stage** | Consistent across all TSVs; sorted alphanumerically for progression charts |
| **Subject labels** | `sub-<digits>`, zero-padded recommended (`sub-001`) |
| **Session labels** | `ses-<digit(s)>`, e.g. `ses-1`, `ses-2` |
| **Project identifier** | Folder name, `task-` field, description JSON, and TSV `<OUTCOME>` suffix must all match exactly |

---

## Checklist Before Running

**Folder & BIDS data**
- [ ] `Projects/MYPROJECT/` folder exists with the exact all-caps identifier
- [ ] `participants.tsv` present with `participant_id`, `sex`, `age` columns
- [ ] At least one subject has a `bids_data/sub-XXX/ses-Y/` folder with ≥ 2 sessions
- [ ] TSV files present for each outcome declared in `outcome_measures`
- [ ] Each TSV has a matching `.json` sidecar
- [ ] `task-` field in every filename matches the project folder name exactly
- [ ] `trial_type` column present and consistent across all TSV types per session
- [ ] `accuracy_binary` values are integer `0` or `1` — not float, not string
- [ ] No empty cells — all missing values written as `n/a`

**Description JSON**
- [ ] `MYPROJECT_description.json` created via `01_description_form.html` or written manually
- [ ] Placed at `Projects/MYPROJECT/MYPROJECT_description.json`
- [ ] Contains `full_name`, `short_description`, `modality`, `recording_modality`, `cognitive_domain`, `task_type`, `language`
- [ ] `outcome_measures` array present with at minimum one entry for your primary accuracy/score outcome
- [ ] Each outcome entry has `id`, `suffix`, `column`, `display_priority`
- [ ] The highest-priority outcome has `display_priority: 1` and its TSV file exists
- [ ] Binary accuracy outcomes have `is_binary: true` so violin plots show percentages (note: no CV computed)
- [ ] The RT outcome (if present) has `is_primary: true` to enable correct-trial filtering
- [ ] File is valid UTF-8 JSON

**Optional**
- [ ] `bibliography.json` in `Projects/MYPROJECT/` — v2 schema with `publications` array
- [ ] Short-version PsychoPy script in the correct location for the Paradigm button
- [ ] `MYPROJECT_demo.html` for the Launch Demo button
- [ ] `beehub_logo.svg` and `logo_memoslap.png` present in the `BEEHub/` root

---

## AI Assistance Statement

This repository was developed with the assistance of **Claude Sonnet 4.6** (Anthropic, 2025), accessed via [claude.ai](https://claude.ai).

All scientific content, paradigm designs, experimental parameters, data structures, and research decisions were conceived and validated by the authors. Claude was used as a coding and documentation assistant throughout iterative development.

> Anthropic. (2025). *Claude Sonnet 4.6*. https://www.anthropic.com

---

*BEE Hub is developed and maintained by the [MemoSlap Lab](https://github.com/memoslap). Contributions, bug reports, and paradigm submissions are welcome via GitHub Issues and Pull Requests.*
