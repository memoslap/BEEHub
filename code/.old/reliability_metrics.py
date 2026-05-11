#!/usr/bin/env python3
"""
reliability_metrics.py
=======================
Centralised reliability-metric computation for BEEHub.

All statistical building blocks (ICC, Cohen's d, Pearson r, CV) and the
full per-paradigm reliability pipeline live here so they can be imported
by 01_multi_project_overview.py and any future scripts without code
duplication.

Adding a new reliability metric
--------------------------------
1. Add a ``calculate_<n>`` static/class method.
2. Wire it up inside ``compute_for_outcome`` — add the key(s) to the
   returned dict.
3. Add a branch in ``normalise_for_radar``.

Supporting a new outcome type (e.g. SCORE, DIST)
--------------------------------------------------
No changes needed here.  Declare the outcome in the project's
``_description.json`` under ``outcome_measures`` and
``01_multi_project_overview.py`` will call ``compute_for_outcome``
with the right DataFrame and column name automatically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Default outcome measures — used when a project has no custom declaration
# ─────────────────────────────────────────────────────────────────────────────

#: Built-in outcomes every project is expected to have.
#: Each entry mirrors the ``outcome_measures`` schema in _description.json.
DEFAULT_OUTCOMES: List[Dict] = [
    {
        "id":               "RT",
        "suffix":           "_RT_beh.tsv",
        "column":           "response_time_ms",
        "label":            "Reaction Time",
        "axis_label":       "RT (ms)",
        "higher_is_better": False,
        "is_primary":       True,    # RT filtering: only correct trials (needs ACCBIN)
        "display_priority": 2,       # 1 = most important for dashboard card
    },
    {
        "id":               "ACC",
        "suffix":           "_ACC_beh.tsv",
        "column":           "accuracy",
        "label":            "Accuracy",
        "axis_label":       "Accuracy",
        "higher_is_better": True,
        "is_primary":       False,
        "display_priority": 3,
    },
    {
        "id":               "ACCBIN",
        "suffix":           "_ACCBIN_beh.tsv",
        "column":           "accuracy_binary",
        "label":            "Accuracy (binary)",
        "axis_label":       "Accuracy (%)",
        "higher_is_better": True,
        "is_binary":        True,    # values 0/1 → displayed as percentages in violin
        "is_primary":       False,
        "display_priority": 1,       # highest priority for dashboard card ICC
        # Note: is_helper=False (default) → ACCBIN IS plotted as a visual outcome
        # Set is_helper=True only if you want ACCBIN used for filtering only (no plot)
    },
]

#: Default display priority for outcomes not in DEFAULT_OUTCOMES.
DEFAULT_DISPLAY_PRIORITY: int = 99

#: Outcome IDs that are treated as binary (0/1) accuracy flags.
BINARY_OUTCOME_IDS: frozenset = frozenset({"ACCBIN"})

#: Outcome ID used for correct-trial RT filtering.
ACCBIN_ID: str = "ACCBIN"


# ─────────────────────────────────────────────────────────────────────────────
# Trial-type classification helpers
# ─────────────────────────────────────────────────────────────────────────────

CONTROL_TYPES: frozenset = frozenset({
    'control', 'rest', 'baseline', 'fixation', 'fix',
    'instruction', 'pause', 'break', 'catch', 'null',
})


def is_control_trial_type(trial_type: str) -> bool:
    t = trial_type.lower()
    return t in CONTROL_TYPES or t.startswith('ctrl') or t.startswith('rest')


def split_trial_types(trial_types: List[str]) -> Tuple[List[str], List[str]]:
    task    = [t for t in trial_types if not is_control_trial_type(t)]
    control = [t for t in trial_types if     is_control_trial_type(t)]
    return task, control


# ─────────────────────────────────────────────────────────────────────────────
# Metric registry
# ─────────────────────────────────────────────────────────────────────────────

#: Each metric entry now uses generic ``{oid}`` placeholder instead of
#: hard-coded ``rt`` / ``acc`` prefixes so keys are built at runtime per
#: outcome.  The radar label templates still use ``{tt}`` for trial type
#: and ``{label}`` for the outcome's human label.
METRIC_REGISTRY: List[Dict] = [
    {
        "id":          "icc",
        "label":       "ICC Consistency",
        "description": "Intraclass Correlation — two-way mixed, consistency estimate ICC(C,1). "
                       "Computed at the learning-stage level (subject × stage means).",
        "radar_label": "{tt} {label} ICC(C)",
        "normalise":   "icc",
    },
    {
        "id":          "icc_agreement",
        "label":       "ICC Agreement",
        "description": "Intraclass Correlation — two-way mixed, absolute agreement ICC(A,1). "
                       "Penalises systematic session shifts. Computed at the learning-stage level.",
        "radar_label": "{tt} {label} ICC(A)",
        "normalise":   "icc",
    },
    {
        "id":          "pearson_r",
        "label":       "Pearson r",
        "description": "Linear correlation between session 1 and session 2 means.",
        "radar_label": "{tt} {label} Pearson r",
        "normalise":   "icc",          # same clamp [0,1]
    },
    {
        "id":          "cohens_d",
        "label":       "Stability (Cohen\u2019s d)",
        "description": "Session-shift stability — inverted Cohen's d, higher = more stable.",
        "radar_label": "{tt} {label} Stability",
        "normalise":   "cohens_d",
    },
    {
        "id":          "cv",
        "label":       "Consistency (CV)",
        "description": "Within-session trial variability — inverted CV, higher = more consistent.",
        "radar_label": "{tt} {label} Consistency",
        "normalise":   "cv",
    },
]

METRIC_BY_ID: Dict[str, Dict] = {m["id"]: m for m in METRIC_REGISTRY}
ALL_METRIC_IDS: List[str] = [m["id"] for m in METRIC_REGISTRY]


def _metric_key(outcome_id: str, metric_id: str, stat: str = "mean") -> str:
    """Build a reliability-dict key like ``rt_icc_mean`` or ``score_cv_std``.

    The outcome_id is lowercased so ``RT`` → ``rt_icc_mean`` (unchanged from
    the old hard-coded keys, keeping full backward-compatibility).
    """
    return f"{outcome_id.lower()}_{metric_id}_{stat}"


# ─────────────────────────────────────────────────────────────────────────────
# Core statistical calculators
# ─────────────────────────────────────────────────────────────────────────────

class ReliabilityMetrics:

    @staticmethod
    def calculate_icc(data1: np.ndarray, data2: np.ndarray) -> float:
        """ICC(C,1) — two-way mixed, consistency, single measures.

        Formula: (MS_rows − MS_error) / (MS_rows + (k−1)·MS_error)
        """
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        n, k = len(data1), 2
        data = np.column_stack([data1, data2])
        grand_mean = np.mean(data)
        row_means  = np.mean(data, axis=1)
        col_means  = np.mean(data, axis=0)
        ss_rows  = k * np.sum((row_means  - grand_mean) ** 2)
        ss_cols  = n * np.sum((col_means  - grand_mean) ** 2)
        ss_error = np.sum((data - grand_mean) ** 2) - ss_rows - ss_cols
        ms_rows  = ss_rows  / (n - 1)
        ms_error = ss_error / ((n - 1) * (k - 1))
        return (ms_rows - ms_error) / (ms_rows + (k - 1) * ms_error)

    @staticmethod
    def calculate_icc_agreement(data1: np.ndarray, data2: np.ndarray) -> float:
        """ICC(A,1) — two-way mixed, absolute agreement, single measures.

        Matches R's ``irr::icc(model='twoway', type='agreement', unit='single')``.
        Formula: (MS_rows − MS_error) / (MS_rows + (k−1)·MS_error + k/n·(MS_cols − MS_error))
        """
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        n, k = len(data1), 2
        data = np.column_stack([data1, data2])
        grand_mean = np.mean(data)
        row_means  = np.mean(data, axis=1)
        col_means  = np.mean(data, axis=0)
        ss_rows  = k * np.sum((row_means  - grand_mean) ** 2)
        ss_cols  = n * np.sum((col_means  - grand_mean) ** 2)
        ss_error = np.sum((data - grand_mean) ** 2) - ss_rows - ss_cols
        ms_rows  = ss_rows  / (n - 1)
        ms_cols  = ss_cols  / (k - 1)
        ms_error = ss_error / ((n - 1) * (k - 1))
        denom = ms_rows + (k - 1) * ms_error + (k / n) * (ms_cols - ms_error)
        if denom == 0:
            return np.nan
        return (ms_rows - ms_error) / denom

    @staticmethod
    def calculate_cohens_d(data1: np.ndarray, data2: np.ndarray) -> float:
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        diff = data1 - data2
        std_diff = np.std(diff, ddof=1)
        if std_diff == 0:
            return 0.0
        return np.mean(diff) / std_diff

    @staticmethod
    def calculate_pearson_r(data1: np.ndarray, data2: np.ndarray) -> float:
        if len(data1) != len(data2) or len(data1) < 2:
            return np.nan
        try:
            r, _ = stats.pearsonr(data1, data2)
            return float(r)
        except Exception:
            return np.nan

    @staticmethod
    def calculate_cv(data: np.ndarray) -> float:
        if len(data) == 0:
            return np.nan
        mean = np.mean(data)
        if mean == 0:
            return np.nan
        return (np.std(data, ddof=1) / mean) * 100

    # ── Normalisation ────────────────────────────────────────────────────────

    @staticmethod
    def normalise_for_radar(metric_id: str, value: float, is_rt: bool = True) -> Optional[float]:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None
        rule = METRIC_BY_ID.get(metric_id, {}).get("normalise", "icc")
        if rule == "icc":
            return float(max(0.0, min(1.0, value)))
        if rule == "cohens_d":
            d_abs = min(abs(value), 2.0)
            return float(max(0.0, min(1.0, 1.0 - d_abs / 2.0)))
        if rule == "cv":
            return float(max(0.0, min(1.0, 1.0 - value / 50.0)))
        return float(max(0.0, min(1.0, value)))

    # ── Per-outcome reliability pipeline ─────────────────────────────────────

    @classmethod
    def compute_for_outcome(
        cls,
        df: pd.DataFrame,
        column: str,
        outcome_id: str,
        trial_types: List[str],
        accbin_df: Optional[pd.DataFrame] = None,
        filter_correct: bool = False,
    ) -> Dict:
        """Compute all reliability metrics for *one* outcome across trial types.

        ICC is now computed at the **learning-stage level** (one mean per
        subject × stage × session) to match the methodology of Abdelmotaleb
        et al. (2025) and the R ``irr::icc`` call used in the paper.  When
        no ``learning_stage`` column is present, the code falls back to the
        previous session-level approach.

        Both ICC(C,1) (consistency) and ICC(A,1) (absolute agreement) are
        computed and stored under separate keys.

        Pearson r and Cohen's d are computed on session-level means (overall
        mean per subject per session) because they describe the between-session
        relationship at the subject level, not the stage level.
        """
        reliability: Dict = {}
        oid = outcome_id.lower()

        for trial_type in (trial_types if trial_types else ['all']):
            if trial_types:
                dff = df[df['trial_type'] == trial_type].copy() if not df.empty else pd.DataFrame()
            else:
                dff = df.copy() if not df.empty else pd.DataFrame()

            # ── Optional correct-trial filter ────────────────────────────────
            if filter_correct and accbin_df is not None and not accbin_df.empty and not dff.empty:
                if trial_types:
                    ab = accbin_df[accbin_df['trial_type'] == trial_type].copy()
                else:
                    ab = accbin_df.copy()

                def _idx(d):
                    d = d.copy()
                    d['_tidx'] = d.groupby(['subject_id', 'session']).cumcount()
                    return d

                dff_i = _idx(dff)
                ab_i  = _idx(ab)[['subject_id', 'session', '_tidx', 'accuracy_binary']].copy()
                ab_i['accuracy_binary'] = pd.to_numeric(ab_i['accuracy_binary'], errors='coerce')
                merged = dff_i.merge(ab_i, on=['subject_id', 'session', '_tidx'],
                                     how='left', suffixes=('', '_ab'))
                dff = merged[merged['accuracy_binary'] == 1].drop(
                    columns=['_tidx', 'accuracy_binary'], errors='ignore')

            # ── Sessions ─────────────────────────────────────────────────────
            if dff.empty or 'session' not in dff.columns:
                continue
            sessions = sorted(dff['session'].unique())
            if len(sessions) < 2:
                continue

            def _multi(d):
                if d.empty or 'subject_id' not in d.columns:
                    return []
                c = d.groupby('subject_id')['session'].nunique()
                return c[c >= 2].index.tolist()

            subjects = _multi(dff)

            # ── Stage-level means for ICC ────────────────────────────────────
            # Group by (subject_id, learning_stage, session) → mean value.
            # This yields N_subjects × N_stages rows per session, matching
            # the R code: group_by(ID, Stage, Session) %>% summarize(mean=...)
            has_stages = ('learning_stage' in dff.columns and
                          dff['learning_stage'].dropna().astype(str).str.strip()
                          .pipe(lambda s: s[s.ne('') & s.str.lower().ne('n/a')]).nunique() > 1)

            stage_s1, stage_s2 = [], []  # stage-level paired vectors for ICC
            s1_means, s2_means, cv_all = [], [], []  # session-level for Pearson/Cohen/CV

            for subject in subjects:
                subj = dff[dff['subject_id'] == subject]
                v1_all = pd.to_numeric(subj[subj['session'] == sessions[0]][column],
                                       errors='coerce').dropna()
                v2_all = pd.to_numeric(subj[subj['session'] == sessions[1]][column],
                                       errors='coerce').dropna()
                if len(v1_all) == 0 or len(v2_all) == 0:
                    continue

                # Session-level means (for Pearson r, Cohen's d, scatter plots)
                s1_means.append(float(v1_all.mean()))
                s2_means.append(float(v2_all.mean()))

                # CV per session
                # Skip CV for binary outcomes (ACCBIN etc.): for a 0/1
                # Bernoulli variable, SD is forced to be √(p(1−p)), so
                # CV = √((1−p)/p)·100 is a deterministic function of the
                # mean accuracy and carries no information about measurement
                # consistency. Leaving cv_all empty here lets downstream code
                # (build_radar_spokes, normalise_for_radar) drop the spoke
                # entirely rather than render a misleading low value.
                #
                # Detection: (a) explicit outcome_id allow-list or (b) the
                # actual values are a subset of {0, 1}. (b) catches the
                # legacy wrapper path (compute_reliability_dict) which passes
                # outcome_id='ACC' for binary accuracy_binary data.
                vals_union = set(v1_all.unique()) | set(v2_all.unique())
                is_binary = (outcome_id in BINARY_OUTCOME_IDS or
                             (len(vals_union) > 0 and vals_union <= {0, 1, 0.0, 1.0}))
                if not is_binary:
                    for v in (v1_all.values, v2_all.values):
                        if len(v) > 1:
                            cv = cls.calculate_cv(v)
                            if not np.isnan(cv):
                                cv_all.append(cv)

                # Stage-level means (for ICC)
                if has_stages:
                    subj_s1 = subj[subj['session'] == sessions[0]]
                    subj_s2 = subj[subj['session'] == sessions[1]]
                    stages_present = sorted(
                        set(subj_s1['learning_stage'].dropna().unique()) &
                        set(subj_s2['learning_stage'].dropna().unique())
                    )
                    for stage in stages_present:
                        sv1 = pd.to_numeric(
                            subj_s1[subj_s1['learning_stage'] == stage][column],
                            errors='coerce').dropna()
                        sv2 = pd.to_numeric(
                            subj_s2[subj_s2['learning_stage'] == stage][column],
                            errors='coerce').dropna()
                        if len(sv1) > 0 and len(sv2) > 0:
                            stage_s1.append(float(sv1.mean()))
                            stage_s2.append(float(sv2.mean()))

            # If no stage-level data, fall back to session-level for ICC
            if not stage_s1:
                stage_s1 = list(s1_means)
                stage_s2 = list(s2_means)

            s1 = np.array(s1_means)
            s2 = np.array(s2_means)
            icc_s1 = np.array(stage_s1)
            icc_s2 = np.array(stage_s2)

            def _safe(lst):
                return [v for v in lst if not np.isnan(v)]

            # ICC computed on stage-level paired means
            iccs       = _safe([cls.calculate_icc(icc_s1, icc_s2)]           if len(icc_s1) > 2 else [])
            iccs_agree = _safe([cls.calculate_icc_agreement(icc_s1, icc_s2)] if len(icc_s1) > 2 else [])
            # Pearson and Cohen's d on session-level means
            pearson    = _safe([cls.calculate_pearson_r(s1, s2)] if len(s1) > 2 else [])
            cohens     = _safe([cls.calculate_cohens_d(s1, s2)]  if len(s1) > 2 else [])

            def _m(lst): return float(np.mean(lst)) if lst else None
            def _s(lst): return float(np.std(lst))  if lst else None
            def _n(lst): return float(np.min(lst))  if lst else None
            def _x(lst): return float(np.max(lst))  if lst else None

            reliability[trial_type] = {
                # ICC consistency (stage-level)
                f'{oid}_icc_mean':                _m(iccs),
                f'{oid}_icc_std':                 _s(iccs),
                f'{oid}_icc_min':                 _n(iccs),
                f'{oid}_icc_max':                 _x(iccs),
                # ICC absolute agreement (stage-level)
                f'{oid}_icc_agreement_mean':       _m(iccs_agree),
                f'{oid}_icc_agreement_std':        _s(iccs_agree),
                f'{oid}_icc_agreement_min':        _n(iccs_agree),
                f'{oid}_icc_agreement_max':        _x(iccs_agree),
                # Stage-level info
                f'{oid}_icc_n_observations':       len(stage_s1),
                # Pearson r (session-level)
                f'{oid}_pearson_r_mean':           _m(pearson),
                f'{oid}_pearson_r_std':            _s(pearson),
                # Cohen's d (session-level)
                f'{oid}_cohens_d_mean':            _m(cohens),
                f'{oid}_cohens_d_std':             _s(cohens),
                # CV (within-session trial-level)
                f'{oid}_cv_mean':                  _m(cv_all),
                f'{oid}_cv_std':                   _s(cv_all),
                # Metadata
                f'{oid}_n_subjects':               len(subjects),
                f'{oid}_s1_means':                 s1_means,
                f'{oid}_s2_means':                 s2_means,
                f'{oid}_subjects':                 subjects,
                'session_labels':                  [str(sessions[0]), str(sessions[1])],
            }

        return reliability

    @classmethod
    def merge_outcome_reliabilities(cls, outcome_rels: List[Dict]) -> Dict:
        """Merge per-outcome reliability dicts into one unified dict per trial type.

        All outcome dicts must share the same trial-type keys.  Keys from
        later dicts are added to the same trial-type entry without overwriting.
        ``session_labels`` is taken from the first non-empty source.
        """
        merged: Dict = {}
        for orel in outcome_rels:
            for tt, metrics in orel.items():
                if tt not in merged:
                    merged[tt] = {}
                for k, v in metrics.items():
                    if k not in merged[tt]:   # first writer wins for session_labels
                        merged[tt][k] = v
        return merged

    # ── Legacy shim — keeps existing call sites working ──────────────────────

    @classmethod
    def compute_reliability_dict(
        cls,
        rt_data: pd.DataFrame,
        accbin_data: pd.DataFrame,
        trial_types: List[str],
    ) -> Dict:
        """Backward-compatible wrapper around compute_for_outcome.

        Called by the thin wrappers in ProjectOverviewGenerator so existing
        code that passes rt_data / accbin_data directly continues to work.
        Merges RT and ACCBIN reliability into a single dict.
        """
        rt_rel  = cls.compute_for_outcome(
            rt_data, 'response_time_ms', 'RT', trial_types,
            accbin_df=accbin_data, filter_correct=True,
        ) if not rt_data.empty else {}

        acc_rel = cls.compute_for_outcome(
            accbin_data, 'accuracy_binary', 'ACC', trial_types,
        ) if not accbin_data.empty else {}

        return cls.merge_outcome_reliabilities([rt_rel, acc_rel])

    # ── Radar spoke builder ───────────────────────────────────────────────────

    @classmethod
    def build_radar_spokes(
        cls,
        rel_dict: Dict,
        selected_metric_ids: Optional[List[str]] = None,
        outcome_labels: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[str], List[float]]:
        """Return *(categories, values)* for a Plotly scatterpolar trace.

        Parameters
        ----------
        rel_dict:
            Merged per-trial-type reliability dict.
        selected_metric_ids:
            Subset of metric IDs to include.  None = all.
        outcome_labels:
            Mapping outcome_id.lower() → human label (e.g. ``{'rt': 'RT',
            'score': 'Score'}``).  Used in spoke labels.
        """
        ids_to_show = selected_metric_ids if selected_metric_ids else ALL_METRIC_IDS
        olabels = outcome_labels or {}

        categories: List[str] = []
        values:     List[float] = []

        for tt, metrics in rel_dict.items():
            for mid in ids_to_show:
                reg = METRIC_BY_ID.get(mid)
                if reg is None:
                    continue
                # Find all keys that match this metric in the merged dict
                suffix = f'_{mid}_mean'
                for key, val in metrics.items():
                    if not key.endswith(suffix) or val is None:
                        continue
                    oid = key[: -len(suffix)]                     # e.g. 'rt', 'score'
                    human = olabels.get(oid, oid.upper())
                    norm = cls.normalise_for_radar(mid, val)
                    if norm is not None:
                        label = reg['radar_label'].format(tt=tt, label=human)
                        categories.append(label)
                        values.append(norm)

        return categories, values