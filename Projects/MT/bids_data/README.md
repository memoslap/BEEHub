# Go/No-Go mouse-tracking (MT) — BIDS behavioural data

Two-session (ses-01 / ses-02) Go/No-Go mouse-tracking task, n = 23 participants (24 sessions; sub-002 and sub-004 have ses-01 only). No participant is excluded from analysis.

## Layout
- `participants.tsv` — per-participant demographics (23 rows)
- `participants.json` — column descriptions
- `sub-<id>/ses-<n>/beh/` — per-session trial-level `.tsv` files (`*_task-gonogo_beh.tsv`) and scored derivatives
  (`*_task-gonogo_desc-scored_beh.tsv`)
- `task-gonogo_beh.json` — task / event metadata
- `dataset_description.json` — dataset metadata

## Derivations
Scored trial tables are produced by `code/1. compute_stopping.R` (label `scored`, params `code/scored_params.json`) into `derivatives/scored/`.
