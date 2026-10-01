---
name: derivation-contract
description: How to wire a project's delivered analysis script into BEEHub's derivation contract (--input/--output/--params), declare it in derivations.json, and run it with run_derivation.py. Use when tables are not directly analysable.
---

# The derivation contract

Every derivation script is called as:

```
<interpreter> <script> --input <abs dir> --output <abs dir> [--params <abs json>]
```

It reads only from `--input`, writes only into `--output`, never modifies anything
that existed under `--input`, and exits non-zero on failure. `run_derivation.py`
**enforces** all four and fails loudly otherwise.

## Adapting delivered code — change as little as possible

You are wiring, not rewriting. The algorithm stays exactly as delivered. Usually:

- replace hard-coded paths with the two arguments;
- lift constants into `--params`, keeping the delivered values as defaults;
- make output names carry a `desc-<label>` entity:
  `sub-007_ses-02_task-<TASK>_desc-<label>_beh.tsv`.

R argument parsing:

```r
args   <- commandArgs(trailingOnly = TRUE)
input  <- args[which(args == "--input")  + 1]
output <- args[which(args == "--output") + 1]
i      <- which(args == "--params")
params <- if (length(i)) jsonlite::fromJSON(args[i + 1]) else list()
```

Python: `argparse` with the same three options.

Show the human the diff and **stop for approval** before running.

## Declare it — `Projects/<CODE>/code/derivations.json`

```json
[
  {
    "name": "<label>",
    "script": "code/<file>",
    "input": "bids_data",
    "output": "derivatives/<label>",
    "params": "code/<label>_params.json",
    "output_glob": "sub-*/ses-*/beh/*_desc-<label>_beh.tsv"
  }
]
```

Paths relative to `Projects/<CODE>/`. `params` optional.

`derivatives/` sits **beside** `bids_data/`, never inside it. Each
`derivatives/<name>/` is its own BIDS derivative dataset and needs its own
`dataset_description.json`:

```json
{
  "Name": "<label>",
  "BIDSVersion": "1.10.0",
  "DatasetType": "derivative",
  "GeneratedBy": [{"Name": "<script filename>", "Version": "<git sha>",
                   "Description": "<one sentence>"}]
}
```

It mirrors the raw layout (`sub-*/ses-*/beh/`), so `suggest_outcomes.py` finds
derived outcomes there automatically.

## Run

```bash
python3 Agent/tools/run_derivation.py <CODE> --dry-run
python3 Agent/tools/run_derivation.py <CODE>
```

On failure read `Projects/<CODE>/code/derivation.log`, fix the real cause, re-run.
Never report success while it fails.

## Never

Rename or overwrite a source table. Write a derived `.tsv` by hand. Invent or
"improve" the analysis. No delivered code → say so and stop; that is a question
for the PI.
