# MouseTracking Data — README

This folder contains the data, materials, and analysis code for the go/no-go mouse-tracking study described in the attached preprint (Mahesan et al., 2026). It accompanies a shared dataset sent via Nextcloud — this file is meant to orient anyone picking up the data for the first time.

## Study in one sentence
Participants completed a mouse-tracking go/no-go task in two sessions ~1 week apart; the study tests whether behavioral (error rate, RT) and kinematic (path length, mean velocity, mean acceleration) measures of response inhibition are reliable across sessions (test–retest reliability via ICC).

## Folder contents

```
MouseTracking Data/
├── Mahesan et al. 2026 - bioRxiv.pdf
├── go_nogo_compiledData.csv
├── 1. compute_stopping.R
├── 2. ER_RT.R
├── 3. Kinematics.R
└── Raw Data/
    ├── 5a_go_nogo_dm_2025-05-02_11h11.19.108.csv
    ├── 5b_go_nogo_dm_2025-05-14_09h03.55.358.csv
    └── ... (one file per participant per session)
```

### `Mahesan et al. 2026 - bioRxiv.pdf`
The preprint itself. Describes the task design, the stopping/kinematic algorithms, and the statistical analyses — read this first, since the R scripts implement exactly what's described in the Methods section.

### `Raw Data/` folder
Individual, trial-by-trial mouse-tracking output, one CSV per participant per session, as recorded directly by the task software (PsychoPy).

**Naming convention:**
```
[subject]_go_nogo_dm_[date]_[time].csv
```
- **subject number** (e.g. `5`, `6`, `24`) — anonymized participant ID
- **a / b suffix** — session: `a` = Session 1, `b` = Session 2 (sessions ~1 week apart)
- **date_time** — auto-generated timestamp of when that session was recorded

Example: `5a_go_nogo_dm_2025-05-02_11h11.19.108.csv` → participant 5, Session 1, recorded 2 May 2025.

> ⚠️ These are large, high-frequency raw trajectory files (mouse x/y position sampled with timestamps for every trial) — this is the input the R pipeline below processes.

### `go_nogo_compiledData.csv`
A pre-compiled dataset built from the raw files above, trimmed down to the columns most relevant for analysis.

### R analysis scripts — **run in numbered order**
The scripts have a dependency chain, so they must be run in this sequence:

1. **`1. compute_stopping.R`** — run this first. Reads the raw trial-level trajectories from `Raw Data/` and computes, for each no-go trial, the point at which the participant successfully stopped (velocity-threshold method, see paper Methods §2.4). It outputs a processed file that scripts 2 and 3 both depend on.
2. **`2. ER_RT.R`** — computes error rates and reaction times (go RT / no-go stopping latency) per participant/session/trial-type, then runs the repeated-measures ANOVA (session × trial-type) and the ICC(3,1) test–retest reliability analyses reported in the paper.
3. **`3. Kinematics.R`** — computes the three kinematic measures (path length, mean velocity, mean acceleration), then runs the same ANOVA and ICC analyses on those.

## Suggested workflow
1. Skim the preprint for context (Methods §2.3–2.5 map directly onto the scripts).
2. Run `1. compute_stopping.R` on the `Raw Data/` folder.
3. Run `2. ER_RT.R` and `3. Kinematics.R` (both need the output of step 1).
