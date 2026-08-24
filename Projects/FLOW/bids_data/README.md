# FLOW — Mental Arithmetic Flow Paradigm

BEEHub project folder for the experimentally-induced flow paradigm based on
Ulrich et al. (2014, 2016, 2018, 2022) and Katahira et al. (2018).

## Project structure

```
FLOW/
├── FLOW_description.json          ← machine-readable paradigm metadata
├── README.md                       ← this file
│
├── paradigm/                       ← experiment code
│   ├── psychopy/
│   │   └── math_paradigm.psyexp    ← original PsychoPy builder file
│   └── pygame/
│       ├── math_paradigm_pygame.py ← standalone pygame port
│       └── README_pygame.md        ← pygame-specific install / run notes
│
├── literature/                     ← key references
│   ├── Ulrich_2016_SCAN.pdf                       ← BOLD block-design, primary neural signatures
│   ├── Ulrich_2018_ExpBrainRes_tDCS.pdf           ← tDCS causal manipulation of MPFC
│   ├── Ulrich_2022_NeuroImageReports_replication.pdf ← decisive Bayesian replication (N=41)
│   ├── Ulrich_2022_FrontHumNeurosci_insula.pdf    ← right anterior insula connectivity
│   └── Katahira_2018_EEG.pdf                      ← EEG correlates (frontal theta, alpha)
│
└── bids_data/                      ← participant data in BIDS-behavioural format
    ├── dataset_description.json
    ├── participants.tsv / .json
    ├── phenotype/                  ← BDI-II, FAM, FKS, demographics
    ├── task-FLOW_beh.json
    ├── task-FLOW_events.json
    └── sub-XXX/ses-YY/beh/         ← per-subject, per-session trial-level TSVs
```

## How to (re-)generate the paradigm HTML

The `FLOW_description.json` file at the project root is the input the BEEHub
paradigm-card generator consumes. To produce a paradigm HTML page from it:

1. Open `01_description_form.html` (the BEEHub Description JSON Builder).
2. Drag-and-drop / paste in the contents of `FLOW_description.json`, **or**
   skip the builder entirely — the JSON is already valid and complete.
3. The downstream BEEHub pipeline picks up
   `BEEHub/Projects/FLOW/FLOW_description.json` and renders the paradigm card,
   filter facets, and outcome panels automatically.

## Conditions (summary)

| Code | Name       | Difficulty                                     | Expected subjective state |
|------|------------|-------------------------------------------------|---------------------------|
| B    | Boredom    | Fixed: 1-digit + (100-109), sum ≤ 110           | low arousal, low flow     |
| F    | Flow       | Adaptive: starts at calibrated skill level      | high subjective flow      |
| O    | Overload   | Adaptive but starts 3 levels above skill        | frustration, low control  |

## Key outcome measures

- **FLOWIDX** — subjective flow index `(-B + 2F - O)` summed across 3 Likert items
  (primary outcome, exhibits invU shape with peak at Flow)
- **ACC** — arithmetic accuracy (proportion correct per condition)
- **RT** — response time on correct trials (ms)
- **ACCBIN** — per-trial binary correctness (helper, used to filter RT)
- **DIFF** — achieved difficulty level (per-trial)

Additional psychophysiological/imaging read-outs reported in the literature
(electrodermal activity, BOLD activation maps, frontal theta EEG) are not stored
in this BEEHub project but are documented in the `literature/` folder.

## Citing

If you use this paradigm please cite:

- Ulrich, M., Keller, J., Hoenig, K., Waller, C., & Grön, G. (2014). Neural
  correlates of experimentally induced flow experiences. *NeuroImage*, 86,
  194-202.
- Ulrich, M., Keller, J., & Grön, G. (2016). Neural signatures of
  experimentally induced flow experiences identified in a typical fMRI block
  design with BOLD imaging. *Social Cognitive and Affective Neuroscience*,
  11(3), 496-507.
