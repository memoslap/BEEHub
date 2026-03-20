#!/usr/bin/env python3
"""
reliability_metrics.py
=======================
Centralised reliability-metric computation for BEEHub.

All statistical building blocks (ICC, Cohen's d, Pearson r, CV) and the
full per-paradigm reliability pipeline live here so they can be imported
by 01_multi_project_overview.py and any future scripts without code
duplication.

Adding a new metric
-------------------
1. Add a ``calculate_<name>`` static/class method that accepts numpy arrays
   and returns a float (np.nan on failure).
2. Wire it up inside ``compute_reliability_dict`` alongside the existing
   metrics — add the key(s) to the returned dict.
3. To expose it in the radar plot normalisation, add a branch in
   ``normalise_for_radar``.

That's it — the rest of the pipeline picks it up automatically.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Trial-type classification helpers
# ─────────────────────────────────────────────────────────────────────────────

#: Exact trial-type names considered "control / rest" conditions.
CONTROL_TYPES: frozenset = frozenset({
    'control', 'rest', 'baseline', 'fixation', 'fix',
    'instruction', 'pause', 'break', 'catch', 'null',
})


def is_control_trial_type(trial_type: str) -> bool:
    """Return True when *trial_type* should be treated as a control condition.

    A trial type is control when its lower-case form is in
    :data:`CONTROL_TYPES` or when it starts with ``ctrl`` / ``rest``.
    """
    t = trial_type.lower()
    return t in CONTROL_TYPES or t.startswith('ctrl') or t.startswith('rest')


def split_trial_types(
    trial_types: List[str],
) -> Tuple[List[str], List[str]]:
    """Split *trial_types* into *(task_types, control_types)*."""
    task    = [t for t in trial_types if not is_control_trial_type(t)]
    control = [t for t in trial_types if     is_control_trial_type(t)]
    return task, control


# ─────────────────────────────────────────────────────────────────────────────
# Metric definitions — each metric is a named entry so it is easy to add more
# ─────────────────────────────────────────────────────────────────────────────

#: Registry of all available metrics.
#: Each entry is a dict with:
#:   label       — short human-readable name
#:   description — one-sentence explanation
#:   keys_rt     — key names written into the reliability dict for RT
#:   keys_acc    — key names written into the reliability dict for Acc
#:   radar_rt    — key used when building the radar (None = not shown)
#:   radar_acc   — key used when building the radar (None = not shown)
METRIC_REGISTRY: List[Dict] = [
    {
        "id":          "icc",
        "label":       "ICC(3,1)",
        "description": "Intraclass Correlation — two-way mixed, consistency estimate.",
        "keys_rt":     ["rt_icc_mean", "rt_icc_std", "rt_icc_min", "rt_icc_max"],
        "keys_acc":    ["acc_icc_mean", "acc_icc_std", "acc_icc_min", "acc_icc_max"],
        "radar_rt":    "rt_icc_mean",
        "radar_acc":   "acc_icc_mean",
        "radar_label_rt":  "{tt} RT ICC",
        "radar_label_acc": "{tt} Acc ICC",
    },
    {
        "id":          "pearson_r",
        "label":       "Pearson r",
        "description": "Linear correlation between session 1 and session 2 means.",
        "keys_rt":     ["rt_pearson_r_mean", "rt_pearson_r_std"],
        "keys_acc":    ["acc_pearson_r_mean", "acc_pearson_r_std"],
        "radar_rt":    "rt_pearson_r_mean",
        "radar_acc":   "acc_pearson_r_mean",
        "radar_label_rt":  "{tt} RT Pearson r",
        "radar_label_acc": "{tt} Acc Pearson r",
    },
    {
        "id":          "cohens_d",
        "label":       "Stability (Cohen's d)",
        "description": "Session-shift stability — inverted Cohen's d, higher = more stable.",
        "keys_rt":     ["rt_cohens_d_mean", "rt_cohens_d_std"],
        "keys_acc":    ["acc_cohens_d_mean", "acc_cohens_d_std"],
        "radar_rt":    "rt_cohens_d_mean",
        "radar_acc":   "acc_cohens_d_mean",
        "radar_label_rt":  "{tt} RT Stability",
        "radar_label_acc": "{tt} Acc Stability",
    },
    {
        "id":          "cv",
        "label":       "Consistency (CV)",
        "description": "Within-session trial variability — inverted CV, higher = more consistent.",
        "keys_rt":     ["rt_cv_mean", "rt_cv_std"],
        "keys_acc":    ["acc_cv_mean", "acc_cv_std"],
        "radar_rt":    "rt_cv_mean",
        "radar_acc":   "acc_cv_mean",
        "radar_label_rt":  "{tt} RT Consistency",
        "radar_label_acc": "{tt} Acc Consistency",
    },
]

#: Convenience lookup: metric_id → registry entry
METRIC_BY_ID: Dict[str, Dict] = {m["id"]: m for m in METRIC_REGISTRY}

#: All metric IDs in display order
ALL_METRIC_IDS: List[str] = [m["id"] for m in METRIC_REGISTRY]


# ─────────────────────────────────────────────────────────────────────────────
# Core statistical calculators
# ─────────────────────────────────────────────────────────────────────────────

class ReliabilityMetrics:
    """Stateless collection of reliability-metric calculators and the full
    reliability-pipeline that drives ``01_multi_project_overview.py``.

    All ``calculate_*`` methods are *static* — they can be called without an
    instance.  ``compute_reliability_dict`` is a *class* method that ties
    everything together and returns the per-trial-type reliability dict that
    the rest of the pipeline expects.
    """

    # ── Low-level calculators ────────────────────────────────────────────────

    @staticmethod
    def calculate_icc(data1: np.ndarray, data2: np.ndarray) -> float:
        """ICC(3,1) — two-way mixed, consistency, single measures.

        Formula: (MSr - MSe) / (MSr + (k-1)*MSe)
        Session effects are partialled out of the error term but NOT added to
        the denominator (consistency rather than absolute-agreement estimate).
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
    def calculate_cohens_d(data1: np.ndarray, data2: np.ndarray) -> float:
        """Paired Cohen's d: mean(diff) / SD(diff)."""
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        diff = data1 - data2
        std_diff = np.std(diff, ddof=1)
        if std_diff == 0:
            return 0.0
        return np.mean(diff) / std_diff

    @staticmethod
    def calculate_pearson_r(data1: np.ndarray, data2: np.ndarray) -> float:
        """Pearson correlation between two paired arrays."""
        if len(data1) != len(data2) or len(data1) < 2:
            return np.nan
        try:
            r, _ = stats.pearsonr(data1, data2)
            return float(r)
        except Exception:
            return np.nan

    @staticmethod
    def calculate_cv(data: np.ndarray) -> float:
        """Coefficient of Variation (%) for a single session's trial values."""
        if len(data) == 0:
            return np.nan
        mean = np.mean(data)
        if mean == 0:
            return np.nan
        return (np.std(data, ddof=1) / mean) * 100

    # ── Normalisation for radar plots ────────────────────────────────────────

    @staticmethod
    def normalise_for_radar(
        metric_id: str,
        value: float,
        is_rt: bool,
    ) -> Optional[float]:
        """Map a raw metric value to [0, 1] for radar-plot display.

        Returns None when the value is None or NaN, which tells the caller
        to skip this spoke entirely.

        Normalisation rules:
        - ICC / Pearson r  → clamped to [0, 1]
        - Cohen's d        → 1 - |d| / 2  (capped at d = 2, so score ≥ 0)
        - CV               → 1 - CV / 50  (CV = 50 % → score = 0)
        """
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return None

        if metric_id in ("icc", "pearson_r"):
            return float(max(0.0, min(1.0, value)))

        if metric_id == "cohens_d":
            d_abs = min(abs(value), 2.0)
            return float(max(0.0, min(1.0, 1.0 - d_abs / 2.0)))

        if metric_id == "cv":
            return float(max(0.0, min(1.0, 1.0 - value / 50.0)))

        # ── Extend here for new metrics ──────────────────────────────────────
        # Example skeleton:
        #   if metric_id == "my_new_metric":
        #       return float(max(0.0, min(1.0, some_transform(value))))

        return float(max(0.0, min(1.0, value)))  # safe default

    # ── Full reliability pipeline ────────────────────────────────────────────

    @classmethod
    def compute_reliability_dict(
        cls,
        rt_data: pd.DataFrame,
        accbin_data: pd.DataFrame,
        trial_types: List[str],
    ) -> Dict:
        """Compute all reliability metrics for each trial type.

        RT reliability is computed on **correct responses only**
        (``accuracy_binary == 1``).  Accuracy reliability uses all trials with
        a valid (non-NaN) ``accuracy_binary`` value.

        Returns a dict keyed by trial-type name, each value being a flat dict
        of all metric keys (see :data:`METRIC_REGISTRY`) plus the per-subject
        session means used by the test-retest scatter plots.
        """
        reliability: Dict = {}

        for trial_type in (trial_types if trial_types else ['all']):

            # ── Filter by trial type ─────────────────────────────────────────
            if trial_types:
                df_rt  = (rt_data[rt_data['trial_type'] == trial_type].copy()
                          if not rt_data.empty else pd.DataFrame())
                df_acc = (accbin_data[accbin_data['trial_type'] == trial_type].copy()
                          if not accbin_data.empty else pd.DataFrame())
            else:
                df_rt  = rt_data.copy()  if not rt_data.empty  else pd.DataFrame()
                df_acc = accbin_data.copy() if not accbin_data.empty else pd.DataFrame()

            # ── RT: keep correct responses only ─────────────────────────────
            if not df_rt.empty and not df_acc.empty:
                def _add_idx(df: pd.DataFrame) -> pd.DataFrame:
                    df = df.copy()
                    df['_trial_idx'] = df.groupby(['subject_id', 'session']).cumcount()
                    return df

                df_rt_idx  = _add_idx(df_rt)
                df_acc_idx = _add_idx(df_acc)
                acc_key = df_acc_idx[
                    ['subject_id', 'session', '_trial_idx', 'accuracy_binary']
                ].copy()
                acc_key['accuracy_binary'] = pd.to_numeric(
                    acc_key['accuracy_binary'], errors='coerce'
                )
                df_rt_merged = df_rt_idx.merge(
                    acc_key,
                    on=['subject_id', 'session', '_trial_idx'],
                    how='left',
                    suffixes=('', '_acc'),
                )
                df_rt = df_rt_merged[df_rt_merged['accuracy_binary'] == 1].drop(
                    columns=['_trial_idx', 'accuracy_binary'], errors='ignore'
                )

            # ── Determine sessions ───────────────────────────────────────────
            ref = df_rt if not df_rt.empty else df_acc
            if ref.empty or 'session' not in ref.columns:
                continue
            sessions = sorted(ref['session'].unique())
            if len(sessions) < 2:
                continue

            def _multi_session_subjects(df: pd.DataFrame) -> List:
                if df.empty or 'subject_id' not in df.columns:
                    return []
                counts = df.groupby('subject_id')['session'].nunique()
                return counts[counts >= 2].index.tolist()

            rt_subjects  = _multi_session_subjects(df_rt)
            acc_subjects = _multi_session_subjects(df_acc)

            # ── Collect per-subject session means ────────────────────────────
            rt_s1_means, rt_s2_means = [], []
            rt_cv_ses1,  rt_cv_ses2  = [], []

            for subject in rt_subjects:
                subj = df_rt[df_rt['subject_id'] == subject]
                s1 = pd.to_numeric(
                    subj[subj['session'] == sessions[0]]['response_time_ms'],
                    errors='coerce',
                ).dropna().values
                s2 = pd.to_numeric(
                    subj[subj['session'] == sessions[1]]['response_time_ms'],
                    errors='coerce',
                ).dropna().values
                if len(s1) > 0 and len(s2) > 0:
                    rt_s1_means.append(float(np.mean(s1)))
                    rt_s2_means.append(float(np.mean(s2)))
                if len(s1) > 1:
                    cv = cls.calculate_cv(s1)
                    if not np.isnan(cv):
                        rt_cv_ses1.append(cv)
                if len(s2) > 1:
                    cv = cls.calculate_cv(s2)
                    if not np.isnan(cv):
                        rt_cv_ses2.append(cv)

            acc_s1_means, acc_s2_means = [], []
            acc_cv_ses1,  acc_cv_ses2  = [], []

            for subject in acc_subjects:
                subj = df_acc[df_acc['subject_id'] == subject]
                s1 = pd.to_numeric(
                    subj[subj['session'] == sessions[0]]['accuracy_binary'],
                    errors='coerce',
                ).dropna().values
                s2 = pd.to_numeric(
                    subj[subj['session'] == sessions[1]]['accuracy_binary'],
                    errors='coerce',
                ).dropna().values
                if len(s1) > 0 and len(s2) > 0:
                    acc_s1_means.append(float(np.mean(s1)))
                    acc_s2_means.append(float(np.mean(s2)))
                if len(s1) > 1:
                    cv = cls.calculate_cv(s1)
                    if not np.isnan(cv):
                        acc_cv_ses1.append(cv)
                if len(s2) > 1:
                    cv = cls.calculate_cv(s2)
                    if not np.isnan(cv):
                        acc_cv_ses2.append(cv)

            # ── Compute aggregated metrics ───────────────────────────────────
            rt_s1  = np.array(rt_s1_means)
            rt_s2  = np.array(rt_s2_means)
            acc_s1 = np.array(acc_s1_means)
            acc_s2 = np.array(acc_s2_means)

            def _safe(arr):
                return [v for v in arr if not np.isnan(v)]

            rt_iccs      = _safe([cls.calculate_icc(rt_s1, rt_s2)]       if len(rt_s1) > 2 else [])
            rt_pearson_r = _safe([cls.calculate_pearson_r(rt_s1, rt_s2)] if len(rt_s1) > 2 else [])
            rt_cohens_d  = _safe([cls.calculate_cohens_d(rt_s1, rt_s2)]  if len(rt_s1) > 2 else [])

            acc_iccs      = _safe([cls.calculate_icc(acc_s1, acc_s2)]       if len(acc_s1) > 2 else [])
            acc_pearson_r = _safe([cls.calculate_pearson_r(acc_s1, acc_s2)] if len(acc_s1) > 2 else [])
            acc_cohens_d  = _safe([cls.calculate_cohens_d(acc_s1, acc_s2)]  if len(acc_s1) > 2 else [])

            def _mean(lst): return float(np.mean(lst)) if lst else None
            def _std(lst):  return float(np.std(lst))  if lst else None
            def _min(lst):  return float(np.min(lst))  if lst else None
            def _max(lst):  return float(np.max(lst))  if lst else None

            reliability[trial_type] = {
                # ICC
                'rt_icc_mean':       _mean(rt_iccs),
                'rt_icc_std':        _std(rt_iccs),
                'rt_icc_min':        _min(rt_iccs),
                'rt_icc_max':        _max(rt_iccs),
                'acc_icc_mean':      _mean(acc_iccs),
                'acc_icc_std':       _std(acc_iccs),
                'acc_icc_min':       _min(acc_iccs),
                'acc_icc_max':       _max(acc_iccs),
                # Cohen's d
                'rt_cohens_d_mean':  _mean(rt_cohens_d),
                'rt_cohens_d_std':   _std(rt_cohens_d),
                'acc_cohens_d_mean': _mean(acc_cohens_d),
                'acc_cohens_d_std':  _std(acc_cohens_d),
                # Pearson r
                'rt_pearson_r_mean':  _mean(rt_pearson_r),
                'rt_pearson_r_std':   _std(rt_pearson_r),
                'acc_pearson_r_mean': _mean(acc_pearson_r),
                'acc_pearson_r_std':  _std(acc_pearson_r),
                # CV (within-subject variability)
                'rt_cv_mean':  _mean(rt_cv_ses1 + rt_cv_ses2),
                'rt_cv_std':   _std(rt_cv_ses1  + rt_cv_ses2),
                'acc_cv_mean': _mean(acc_cv_ses1 + acc_cv_ses2),
                'acc_cv_std':  _std(acc_cv_ses1  + acc_cv_ses2),
                # Sample sizes
                'n_subjects_rt':  len(rt_subjects),
                'n_subjects_acc': len(acc_subjects),
                'n_subjects':     max(len(rt_subjects), len(acc_subjects)),
                # Per-subject means for scatter plots
                'rt_s1_means':   rt_s1_means,
                'rt_s2_means':   rt_s2_means,
                'rt_subjects':   rt_subjects,
                'acc_s1_means':  [float(v * 100) for v in acc_s1_means],
                'acc_s2_means':  [float(v * 100) for v in acc_s2_means],
                'acc_subjects':  acc_subjects,
                'session_labels': [str(sessions[0]), str(sessions[1])],

                # ── Add new metrics here — follow the pattern above ──────────
            }

        return reliability

    # ── Radar spoke builder ───────────────────────────────────────────────────

    @classmethod
    def build_radar_spokes(
        cls,
        rel_dict: Dict,
        selected_metric_ids: Optional[List[str]] = None,
    ) -> Tuple[List[str], List[float]]:
        """Return *(categories, values)* for a Plotly scatterpolar trace.

        Parameters
        ----------
        rel_dict:
            Per-trial-type reliability dict as returned by
            :meth:`compute_reliability_dict`.
        selected_metric_ids:
            Subset of metric IDs to include (from :data:`ALL_METRIC_IDS`).
            Pass ``None`` or an empty list to include all metrics.
        """
        ids_to_show = selected_metric_ids if selected_metric_ids else ALL_METRIC_IDS

        categories: List[str] = []
        values:     List[float] = []

        for tt, metrics in rel_dict.items():
            for mid in ids_to_show:
                reg = METRIC_BY_ID.get(mid)
                if reg is None:
                    continue

                # RT spoke
                rt_key = reg["radar_rt"]
                if rt_key and metrics.get(rt_key) is not None:
                    norm = cls.normalise_for_radar(mid, metrics[rt_key], is_rt=True)
                    if norm is not None:
                        categories.append(reg["radar_label_rt"].format(tt=tt))
                        values.append(norm)

                # Acc spoke
                acc_key = reg["radar_acc"]
                if acc_key and metrics.get(acc_key) is not None:
                    norm = cls.normalise_for_radar(mid, metrics[acc_key], is_rt=False)
                    if norm is not None:
                        categories.append(reg["radar_label_acc"].format(tt=tt))
                        values.append(norm)

        return categories, values
