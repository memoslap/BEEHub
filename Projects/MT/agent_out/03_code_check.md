# 03 — Static code check: Projects/MT/code

Checker: `uv run Agent/tools/check_code.py "Projects/MT/code" --json`

## Summary

| Metric | Count |
|--------|-------|
| Files checked | 3 (all R) |
| Parse errors | 0 |
| Warnings (absolute paths) | 6 |
| Missing inputs | 2 |

## Run order

| Step | Script | Input | Output |
|------|--------|-------|--------|
| 1 | `1. compute_stopping.R` | `go_nogo_s.xlsx` (hard-coded Windows path) | `go_nogo_scored_final.csv` (line 921) and `go_nogo_scored_final.xlsx` (line 938–940, derived via `sub("\\.csv$", ".xlsx", output_path)` at line 925) |
| 2 | `2. ER_RT.R` | `go_nogo_scored_final.xlsx` (line 17) | `performance_reliability_tables_complete.xlsx` (line 18) |
| 3 | `3. Kinematics.R` | `go_nogo_scored_final.xlsx` (line 46) | `3. Kinematics_results01_CORRECTED.xlsx` (line 47) |

Scripts 2 and 3 both read the xlsx written by script 1 and have no dependency on each other. They can run in any order (or in parallel) after script 1 completes.

## Per-file findings

### `1. compute_stopping.R` (1016 lines)

| Line | Finding | Blocks |
|------|---------|--------|
| 26 | Hard-coded path `C:/1_DevuMahesan_Data/.../go_nogo_s.xlsx` | Script cannot run on this machine; path must be replaced |
| 27 | Hard-coded path `C:/1_DevuMahesan_Data/.../go_nogo_scored_final.csv` | Output directory does not exist here; path must be replaced |

Parses: yes. No syntax errors.

### `2. ER_RT.R` (268 lines)

| Line | Finding | Blocks |
|------|---------|--------|
| 17 | Hard-coded path `C:/1_DevuMahesan_Data/.../go_nogo_scored_final.xlsx` | Script cannot run; input file not present at this path |
| 18 | Hard-coded path `C:/1_DevuMahesan_Data/.../performance_reliability_tables_complete.xlsx` | Output directory does not exist here |

Parses: yes. No syntax errors.

### `3. Kinematics.R` (754 lines)

| Line | Finding | Blocks |
|------|---------|--------|
| 46 | Hard-coded path `C:/1_DevuMahesan_Data/.../go_nogo_scored_final.xlsx` | Script cannot run; input file not present at this path |
| 47 | Hard-coded path `C:/1_DevuMahesan_Data/.../3. Kinematics_results01_CORRECTED.xlsx` | Output directory does not exist here |

Parses: yes. No syntax errors.

## Inputs and outputs

### Present in `Projects/MT/code/`

| File | Size | Role |
|------|------|------|
| `go_nogo_compiledData.csv` | 45 MB | **Not read by any script.** Column headers: `block_number, trials_count, digit, trial_type, correct_response, mouse_resp.x, mouse_resp.y, mouse_resp.leftButton, mouse_resp.midButton, mouse_resp.rightButton, mouse_resp.time, click_pos_x, click_pos_y, iti_duration, participant`. This appears to be the raw trial-level export. None of the three scripts reference it. |

### Referenced but absent

| File | Referenced by | Expected location |
|------|--------------|-------------------|
| `go_nogo_s.xlsx` | Script 1, line 26 | Not in `Projects/MT/code/`. Likely a pre-filtered or reformatted version of the compiled data. |
| `go_nogo_scored_final.xlsx` | Scripts 2 & 3, lines 17/46 | Produced by script 1 (line 938). Absent until script 1 runs. |

### Produced (outputs)

| File | Produced by |
|------|------------|
| `go_nogo_scored_final.csv` | Script 1, line 921 |
| `go_nogo_scored_final.xlsx` | Script 1, line 938 |
| `performance_reliability_tables_complete.xlsx` | Script 2, line 250 |
| `3. Kinematics_results01_CORRECTED.xlsx` | Script 3, line 725 |

## Dependencies

| Package | Script 1 | Script 2 | Script 3 |
|---------|----------|----------|----------|
| readxl | ✓ | ✓ | ✓ |
| dplyr | ✓ | ✓ | ✓ |
| tidyr | ✓ | ✓ | ✓ |
| jsonlite | ✓ | | ✓ |
| writexl | ✓ | ✓ | ✓ |
| stringr | ✓ | | |
| ggplot2 | ✓ | | |
| purrr | ✓ | | ✓ |
| ez | | ✓ | ✓ |
| irr | | ✓ | ✓ |
| pacman | ✓ (bootstrap) | | |

All scripts use `library()` or `pacman::p_load()` for their dependencies. No Python imports.

## Verdict

**Blocked.** All three scripts use hard-coded Windows absolute paths that do not exist on this system. Script 1's input file (`go_nogo_s.xlsx`) is not present in the repository. Additionally, no script reads `go_nogo_compiledData.csv`, which is the only data file present — the provenance of `go_nogo_s.xlsx` relative to it is unclear.
