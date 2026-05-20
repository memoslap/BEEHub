# BEEHub reliability_metrics.py — pingouin migration

**pingouin version pinned: 0.6.1** (Vallat 2018, JOSS).

## What changed

### 1. ICC now uses pingouin and returns a full result dict

Before: `calculate_icc(data1, data2)` → `float`
After: `calculate_icc(data1, data2)` → `{'icc', 'ci_low', 'ci_high', 'F', 'df1', 'df2', 'p'}`

Backed by `pingouin.intraclass_corr` (the McGraw & Wong 1996 / Liljequist
et al. 2019 implementation, identical to R's `irr::icc`). When pingouin
is unavailable the home-grown ANOVA formula is used as a fallback, but
without CIs.

### 2. JSON schema gained CI/F/df/p fields

Per outcome (e.g. `accbin`), per trial type (e.g. `learning`):

```
accbin_icc                      → 0.640        (point estimate)
accbin_icc_ci_low               → 0.29         (NEW — analytical 95% CI low)
accbin_icc_ci_high              → 0.84         (NEW — analytical 95% CI high)
accbin_icc_F                    → 4.56         (NEW — F statistic)
accbin_icc_df1                  → 19           (NEW — between-subjects df)
accbin_icc_df2                  → 19           (NEW — error df)
accbin_icc_p                    → 8.85e-04     (NEW — F-test p-value)
accbin_icc_agreement            → 0.652        (point — ICC(A,1))
accbin_icc_agreement_ci_low/_ci_high/_F/_df1/_df2/_p   (NEW)
```

Removed (uninformative — single ICC value, so std/min/max=0 always):
`_icc_std`, `_icc_min`, `_icc_max`, same for `_icc_agreement`,
`_pearson_r`, `_cohens_d`.

### 3. Session-shift stability separated from paradigm effect size

The old `cohens_d` field measured *between-session drift* (a reliability
concept) but was labelled "Stability" on the radar. It now has two
disjoint fields:

- `accbin_session_shift_d`           — paired d on session means; small |d| ⇒ stable
- `accbin_paradigm_effect_size`      — Hedges' g for the paradigm's main contrast
  - `_paradigm_effect_size_ci_low`   — bootstrap CI (BCa, n_boot=2000)
  - `_paradigm_effect_size_ci_high`
  - `_paradigm_effect_size_contrast` — e.g. `LS4_vs_LS1` for OLM
  - `_paradigm_effect_size_type`     — `hedges` (default) or `cohen`
  - `_paradigm_effect_size_n`        — number of paired observations used

For OLM this auto-computes Stage 4 vs Stage 1 within session 1. For an
n-back paradigm it would compute the highest vs lowest stage; for any
paradigm without learning stages the field is NaN, and a project can
declare its own contrast via `_description.json` later.

### 4. Internal consistency added (Cronbach's α / KR-20)

`pingouin.cronbach_alpha` on a wide (subject × trial-index) matrix from
session 1. For binary outcomes this is mathematically KR-20.

```
accbin_cronbach_alpha            → 0.808
accbin_cronbach_alpha_ci_low     → 0.667
accbin_cronbach_alpha_ci_high    → 0.910
accbin_cronbach_alpha_n_items    → 98
```

Capped at 100 items per outcome to stay fast on large paradigms.

### 5. Provenance recorded

Top-level `_provenance` field in every project's `_data.json`:

```json
{
  "pingouin_version": "0.6.1",
  "pingouin_used": true,
  "numpy_version": "...",
  "pandas_version": "...",
  "scipy_version": "...",
  "python_version": "..."
}
```

So future readers know exactly how the metrics were computed.

### 6. Backward compatibility

Every old key (`_icc_mean`, `_icc_agreement_mean`, `_pearson_r_mean`,
`_cohens_d_mean`, `_cv_mean`) is **still present** as an alias to the
new bare key. `01_multi_project_overview.py` and
`03_generate_dashboard.py` continue to work without modification.

The metric registry has a new `paradigm_effect_size`, `cronbach_alpha`
and renamed `session_shift_d` (with `cohens_d` as a backward-compat
alias). `build_radar_spokes` understands both old and new key names.

## Changes to 01_description_form.html

The Outcomes step of the description-builder wizard now exposes three
fields that previously required hand-editing the JSON:

- **"Requires correct-trial filter"** checkbox — emits both
  `requires_correct_filter` (the new canonical name) and `is_primary`
  (legacy alias the pipeline currently reads). The pipeline accepts
  either, so the rename can complete in a follow-up PR without
  breaking the form.
- **"Helper outcome (load but don't plot)"** checkbox — emits
  `is_helper`. Use for raw ACC (trichotomous correct / incorrect /
  too-late) when you only want ACCBIN plotted but still need ACC
  loaded for downstream filtering.
- **"Paradigm contrast for Hedges' g"** text input — emits
  `paradigm_contrast` as `"<levelA>_vs_<levelB>"` (e.g. `LS4_vs_LS1`,
  `incongruent_vs_congruent`, `2back_vs_0back`). The pipeline applies
  this contrast for the within-session paradigm effect size when
  declared; falls back to last_vs_first stage when blank or when
  either level is missing from the data.

The Outcomes step also gained an explainer paragraph listing what the
pipeline now computes per declared outcome (ICC with CI/F/p, Cronbach
α with CI, Hedges' g with bootstrap CI, etc).

`renderOutcomeList`, `addOutcome`, and `buildJSON` were updated
correspondingly. All existing fields are preserved exactly as-is, so
old JSON files load and round-trip without change.

## Changes to environment.yml

- `pingouin>=0.5.0` promoted from optional / commented-out to a real
  required pip dependency, with a comment noting that the pipeline
  still falls back to the home-grown ANOVA path if pingouin is
  somehow unavailable (just without CIs).

## Changes to reliability_metrics.py

(In addition to the pingouin migration described above.)

- `compute_for_outcome` gained a `paradigm_contrast` parameter. When
  supplied as `"A_vs_B"` and both levels exist in `learning_stage`,
  the within-session Hedges' g uses that contrast; otherwise it falls
  back to `<last_stage>_vs_<first_stage>`.
- A non-existent contrast (e.g. user typo) silently falls back rather
  than throwing — this is intentional, so a stale JSON doesn't break
  the whole report.

## How to deploy

1. `conda env update -f environment.yml` (or `pip install pingouin>=0.5.0`)
2. Drop in **all four** updated files:
   - `code/reliability_metrics.py`
   - `code/01_multi_project_overview.py`
   - `code/03_generate_dashboard.py`
   - `01_description_form.html`
3. Re-run `python 01_multi_project_overview.py` for each project — all
   eight current projects will pick up the new fields automatically;
   none of the existing rendering breaks.
4. Re-run `python 03_generate_dashboard.py` — the new metric dropdown
   options, sliders, and explanation cards appear automatically once at
   least one project's `_data.json` contains the new fields.
5. Existing `_description.json` files keep working unchanged. When you
   next edit one through the form, the new fields appear in the JSON
   output with safe defaults (all checkboxes off,
   `paradigm_contrast` absent).

## Changes to 01_multi_project_overview.py

- **Provenance + schema version added to every `_data.json`** so a
  reader knows which library produced the metrics.
- **Scatter labels show ICC + 95% CI**: legend reads `ICC(A)=0.80
  [0.74, 0.85]  ICC(C)=0.78 [0.71, 0.84]` instead of bare point
  estimates.
- **Stats banner under each scatter** shows F(df1,df2), p-value,
  Hedges' g (paradigm effect size with contrast tag), and Cronbach α
  per trial type.
- Existing radar / cards / progression plots unchanged.

## Changes to 03_generate_dashboard.py

- **Metric dropdown** rewritten: ICC Consistency, ICC Agreement,
  Pearson r, Internal consistency (α), Session-shift stability,
  Paradigm effect size, Within-session CV.
- **Slider builder** now supports a fallback list of keys per metric,
  so the same JS reads both new (`rt_icc`) and legacy (`rt_icc_mean`)
  schemas. Mixed projects work fine.
- **Two new explanation cards** added to the reliability panel:
  Cronbach's α / KR-20 (with Pike et al. 2022 reference) and Paradigm
  effect size (with Hedges 1981, Lakens 2013 references). Old "Stability
  &mdash; Cohen's d" card rewritten as "Session-shift stability" with
  explicit framing of why this is *not* a paradigm effect size.
- **Project-card stat box** now shows the 95% CI under the ICC point
  estimate when the project contributes a single ICC value.
- **JS normalisation map** and color palettes extended with
  `cronbach_alpha`, `session_shift_d`, `paradigm_effect_size`. The
  legacy `cohens_d` id remains in the JS as an alias so old-format
  projects still render.
- **Server-side range computation** scans both new and legacy keys,
  uses wider bounds for `paradigm_effect_size` (effect sizes can be
  much greater than 1), and clamps `cronbach_alpha` to [-0.5, 1].
- **Dead code preserved**: `_perProjectMean` (declared but unused)
  was left as-is to keep the diff focused.

## Validation

- **Synthetic OLM-regime test** (20 subjects × 4 stages × 60 trials):
  - ACCBIN ICC(C,1) = 0.933 [0.900, 0.960], F(79,79)=28.8, p≈0
  - Paradigm ES (LS4 vs LS1) = g = 3.33 [2.49, 4.12]
  - Cronbach α = 0.808 [0.667, 0.910] across 98 items
  - Control trials correctly show ICC≈0 (ceiling effect, no signal)
- **Real session-level OLM means** (the 20 paired means in your
  existing `OLM_data.json`):
  - ACCBIN ICC(C,1) = 0.640 [0.29, 0.84] (n=20 session-level)
  - RT  ICC(C,1) = 0.888 [0.74, 0.95] (n=20 session-level)
  - Pearson r exactly matches old output (numerical equivalence)

Note: when run on actual stage-level TSVs (n=80), ICC will be more
precise — closer to the paper's `0.801 [0.737, 0.850]`.

## Not done in this round (separate, smaller PRs)

- Rename `is_primary: True` → `requires_correct_filter: True` in
  `DEFAULT_OUTCOMES` (semantic overloading I flagged separately)
- Per-version (acq-1 vs acq-2) reliability breakdown
- Inter-session-interval extraction from onset timestamps
- Power / minimum-detectable-effect computation
- Schema validator (`bee-validator.py`)
- Controlled vocabulary for `cognitive_domain`

## Caveat about the BIDS data loader (pre-existing, unrelated)

`01_multi_project_overview.py`'s `load_outcome_data` uses
`session_dir.glob("*{suffix}")` to find TSVs, which expects them
*directly* under `sub-*/ses-*/` rather than under
`sub-*/ses-*/beh/` (the canonical BIDS-Behavioural location). My
synthetic integration test had to flatten its output for `01` to
read it; whatever layout your real project tree uses, it presumably
already works with the existing loader. If you want to switch to the
canonical BIDS-Behavioural layout later, change line ~229 from
`session_dir.glob(...)` to `session_dir.rglob(...)` — this is
unrelated to the pingouin migration.
