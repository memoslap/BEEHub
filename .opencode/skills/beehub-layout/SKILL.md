---
name: beehub-layout
description: The canonical Projects/<CODE>/ folder layout, BIDS file-naming rules, and where every file type belongs. Use when planning a migration, writing a rename map, or auditing structure.
---

# BEEHub project layout

Match this exactly. Omit folders a project does not have; never create empty ones.

```
Projects/<CODE>/
├── <CODE>_description.json        project-description agent only
├── agent_out/                     agent reports, intake plan
├── bids_data/
│   ├── dataset_description.json   data-description agent only
│   ├── participants.tsv           one row per subject
│   ├── participants.json          column dictionary
│   ├── README.md
│   ├── task-<TASK>_beh.json       ONE top-level column dictionary, inherited
│   └── sub-<NNN>/ses-<NN>/beh/
│       ├── sub-<NNN>_ses-<NN>_task-<TASK>[_run-<NN>]_beh.tsv
│       └── sub-<NNN>_ses-<NN>_session.json
├── code/                          analysis scripts, derivations.json, paper_claims.yaml
├── derivatives/<name>/            outputs of declared derivations — BESIDE
│   ├── dataset_description.json   bids_data, never inside it; mirrors its
│   └── sub-<NNN>/ses-<NN>/beh/    sub-/ses- layout
├── literature/                    ALL PDFs, .pptx/.docx instructions
├── paradigm/
│   ├── psychopy/                  .py, .psyexp, condition .xlsx
│   ├── presentation/              .exp, sce/, Stimuli/
│   └── pygame/
├── raw_logs/                      Presentation .log runtime files
└── sourcedata/raw/                ORIGINALS, untouched, original names
```

## Naming

`sub-<NNN>_ses-<NN>_task-<label>[_acq-<N>][_run-<NN>]_beh.tsv`

- `sub-` zero-padded to 3 digits, `ses-` to 2. Never mix widths in one dataset
  (`apply_rename_map.py` warns if you do).
- `task-` alphanumeric only: `stop_signal` → `task-stopsignal`.
- Source session markers (letters, dates, suffixes) → `ses-NN` only via a mapping
  **stated in the plan and confirmed by the human**. Never infer it.
- Behavioural data → `.tsv` in `bids_data/`; the original stays in
  `sourcedata/raw/` under its original name.

## Placement rules

- **Every PDF → `literature/`**, renamed `<FirstAuthor>_<Year>_<keyword>.pdf`.
  A PDF left behind is a migration failure: later agents read `literature/` as
  their main evidence.
- **Analysis code → `code/`**, original names.
- **Paradigm trees are copied whole** (`copytree`) — never rename inside them.
  `.exp`/`.sce`/`.psyexp`/condition files reference stimuli and each other by
  exact, case-sensitive name.
- **One grain per TSV.** Per-trial rows and derived per-subject measures never
  share a table.
- **Exclude** `Thumbs.db`, `desktop.ini`, `~$*`, `__pycache__/`, `*.pyc`,
  `* (copy).*` — mark them `skip` in the rename map with the reason.

## Anomalies are reported, not fixed

Incomplete subjects, duplicates, numbering gaps, files with a different column
structure: list each. Never invent a placeholder session or silently drop a file.
