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

import warnings
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple

# pingouin is the canonical implementation for ICC / Cronbach / effect-size
# (Vallat 2018, J Open Source Softw). Tested against pingouin >= 0.5.
# When unavailable, we fall back to the home-grown ANOVA computation but
# without analytical confidence intervals or the F-test, and emit a warning.
try:
    import pingouin as _pg
    _PINGOUIN_AVAILABLE = True
    _PINGOUIN_VERSION = _pg.__version__
except ImportError:
    _pg = None
    _PINGOUIN_AVAILABLE = False
    _PINGOUIN_VERSION = None


def get_metrics_provenance() -> Dict:
    """Return a small dict describing which library produced the metrics.

    Stored alongside the reliability output so a reader knows how the
    numbers were computed and can reproduce them.
    """
    import sys
    import scipy
    return {
        'pingouin_version': _PINGOUIN_VERSION,
        'pingouin_used':    _PINGOUIN_AVAILABLE,
        'numpy_version':    np.__version__,
        'pandas_version':   pd.__version__,
        'scipy_version':    scipy.__version__,
        'python_version':   '.'.join(map(str, sys.version_info[:3])),
    }


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
        "description": "Intraclass Correlation — two-way mixed, consistency, single measures ICC(C,1). "
                       "Computed at the learning-stage level (subject × stage means). "
                       "Reported with 95% CI and F-test.",
        "radar_label": "{tt} {label} ICC(3,1)",
        "normalise":   "icc",
    },
    {
        "id":          "icc_agreement",
        "label":       "ICC Agreement",
        "description": "Intraclass Correlation — two-way mixed, absolute agreement, single measures ICC(A,1). "
                       "Penalises systematic session shifts. Computed at the learning-stage level. "
                       "Reported with 95% CI and F-test.",
        "radar_label": "{tt} {label} ICC(2,1)",
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
        "id":          "cronbach_alpha",
        "label":       "Internal consistency (α)",
        "description": "Cronbach's α / KR-20 across trials within session 1. "
                       "Distinct from test-retest: measures within-session item homogeneity.",
        "radar_label": "{tt} {label} α",
        "normalise":   "icc",          # α is in [0,1] (negative values clamped)
    },
    {
        "id":          "session_shift_d",
        "label":       "Session-shift stability",
        "description": "Paired Cohen's d on session-level means (s1 − s2) / SD_diff. "
                       "Inverted on the radar — higher = smaller drift between sessions. "
                       "NOT a paradigm effect size — see paradigm_effect_size for that.",
        "radar_label": "{tt} {label} Session stability",
        "normalise":   "cohens_d",
    },
    {
        "id":          "paradigm_effect_size",
        "label":       "Paradigm effect size",
        "description": "Within-session standardised mean difference (Hedges' g) for the "
                       "paradigm's main contrast — e.g. last vs first learning stage, or "
                       "load vs control. Captures paradigm sensitivity, not reliability.",
        "radar_label": "{tt} {label} Effect size",
        "normalise":   "effect_size",
    },
    {
        "id":             "cv",
        "label":          "Within-session CV",
        "description":    "Within-session trial-level coefficient of variation for continuous outcomes. "
                          "Inverted on the radar — higher = lower noise. "
                          "Not computed for binary accuracy (Bernoulli CV is a deterministic "
                          "re-expression of the mean and conveys no independent information).",
        "radar_label":    "{tt} {label} Trial CV",
        "normalise":      "cv",
        "skip_for_binary": True,   # never show CV spoke / slider for binary outcomes
    },
]

# Backward-compat: old "cohens_d" id maps to the new session_shift_d
# so existing JSON files / dashboards keep working.
METRIC_BY_ID: Dict[str, Dict] = {m["id"]: m for m in METRIC_REGISTRY}
METRIC_BY_ID["cohens_d"] = METRIC_BY_ID["session_shift_d"]
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

    # ── ICC ─────────────────────────────────────────────────────────────────
    #
    # Returns a *full* result dict (point estimate, 95% CI, F, df1, df2, p)
    # rather than a bare float, because a reliability point estimate without
    # its CI is not meaningfully comparable across paradigms.
    #
    # Backed by pingouin.intraclass_corr (Vallat 2018), which implements the
    # six McGraw & Wong (1996) variants and matches R's irr::icc.  When
    # pingouin is unavailable we fall back to the home-grown ANOVA formulas
    # (point estimate only — no CI, no F-test).

    _NAN_ICC: Dict = {
        'icc': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
        'F': np.nan, 'df1': np.nan, 'df2': np.nan, 'p': np.nan,
    }

    @staticmethod
    def _icc_long_df(data1: np.ndarray, data2: np.ndarray) -> Optional[pd.DataFrame]:
        """Stack two paired vectors into the long format pingouin expects."""
        if len(data1) != len(data2) or len(data1) == 0:
            return None
        n = len(data1)
        return pd.DataFrame({
            'target': list(range(n)) * 2,
            'rater':  ['s1'] * n + ['s2'] * n,
            'value':  np.concatenate([np.asarray(data1, dtype=float),
                                      np.asarray(data2, dtype=float)]),
        })

    @classmethod
    def _icc_via_pingouin(cls, df: pd.DataFrame, icc_type: str) -> Dict:
        """Return one of the six ICC variants as a result dict.

        ``icc_type`` ∈ {'ICC(C,1)', 'ICC(A,1)', 'ICC(1,1)', 'ICC(C,k)', ...}.
        """
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = _pg.intraclass_corr(data=df, targets='target',
                                          raters='rater', ratings='value',
                                          nan_policy='omit')
            row = res[res['Type'] == icc_type].iloc[0]
            ci = row['CI95']
            ci_low, ci_high = (float(ci[0]), float(ci[1])) if ci is not None else (np.nan, np.nan)
            return {
                'icc':    float(row['ICC']),
                'ci_low': ci_low,
                'ci_high': ci_high,
                'F':      float(row['F']),
                'df1':    float(row['df1']),
                'df2':    float(row['df2']),
                'p':      float(row['pval']),
            }
        except Exception:
            return dict(cls._NAN_ICC)

    @classmethod
    def calculate_icc(cls, data1: np.ndarray, data2: np.ndarray) -> Dict:
        """ICC(C,1) — two-way mixed, consistency, single measures.

        Returns a dict with keys: ``icc, ci_low, ci_high, F, df1, df2, p``.
        Use ``result['icc']`` for the bare point estimate.
        """
        df = cls._icc_long_df(data1, data2)
        if df is None:
            return dict(cls._NAN_ICC)
        if _PINGOUIN_AVAILABLE:
            return cls._icc_via_pingouin(df, 'ICC(C,1)')
        # Fallback: ANOVA from sums-of-squares, point estimate only
        return cls._icc_fallback(data1, data2, kind='consistency')

    @classmethod
    def calculate_icc_agreement(cls, data1: np.ndarray, data2: np.ndarray) -> Dict:
        """ICC(A,1) — two-way mixed, absolute agreement, single measures.

        Matches R ``irr::icc(model='twoway', type='agreement', unit='single')``
        and pingouin's ``ICC(A,1)``.
        """
        df = cls._icc_long_df(data1, data2)
        if df is None:
            return dict(cls._NAN_ICC)
        if _PINGOUIN_AVAILABLE:
            return cls._icc_via_pingouin(df, 'ICC(A,1)')
        return cls._icc_fallback(data1, data2, kind='agreement')

    @staticmethod
    def _icc_fallback(data1: np.ndarray, data2: np.ndarray, kind: str = 'consistency') -> Dict:
        """ANOVA-based ICC fallback — point estimate only, no CI."""
        n, k = len(data1), 2
        data = np.column_stack([data1, data2])
        grand_mean = np.mean(data)
        row_means  = np.mean(data, axis=1)
        col_means  = np.mean(data, axis=0)
        ss_rows  = k * np.sum((row_means  - grand_mean) ** 2)
        ss_cols  = n * np.sum((col_means  - grand_mean) ** 2)
        ss_error = np.sum((data - grand_mean) ** 2) - ss_rows - ss_cols
        ms_rows  = ss_rows  / (n - 1) if n > 1 else np.nan
        ms_cols  = ss_cols  / (k - 1)
        ms_error = ss_error / ((n - 1) * (k - 1)) if n > 1 else np.nan
        if kind == 'consistency':
            denom = ms_rows + (k - 1) * ms_error
        else:  # agreement
            denom = ms_rows + (k - 1) * ms_error + (k / n) * (ms_cols - ms_error)
        icc = (ms_rows - ms_error) / denom if denom not in (0, np.nan) else np.nan
        return {'icc': float(icc), 'ci_low': np.nan, 'ci_high': np.nan,
                'F': np.nan, 'df1': np.nan, 'df2': np.nan, 'p': np.nan}

    # ── Effect sizes ────────────────────────────────────────────────────────

    @staticmethod
    def calculate_cohens_d_paired(data1: np.ndarray, data2: np.ndarray) -> float:
        """Paired Cohen's d (mean of differences / SD of differences).

        Used for **session-shift stability** — small d means the paradigm's
        score is stable across retests.  This is *not* the paradigm's effect
        size; for that, see ``calculate_paradigm_effect_size``.
        """
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        diff = np.asarray(data1) - np.asarray(data2)
        std_diff = np.std(diff, ddof=1)
        if std_diff == 0:
            return 0.0
        return float(np.mean(diff) / std_diff)

    # Backward-compat alias.
    calculate_cohens_d = calculate_cohens_d_paired

    @classmethod
    def calculate_paradigm_effect_size(
        cls,
        cond_a: np.ndarray,
        cond_b: np.ndarray,
        paired: bool = True,
        eftype: str = 'hedges',
    ) -> Dict:
        """Within-session effect size for a paradigm contrast.

        Examples of contrasts:
          * Stage 4 vs Stage 1   → "learning effect"
          * Learning vs Control  → "task sensitivity"
          * Incongruent vs Congruent (Stroop), 2-back vs 0-back (n-back), etc.

        Returns a dict with point estimate, 95% bootstrap CI, n, and the
        descriptive statistics needed to interpret it.

        Parameters
        ----------
        cond_a, cond_b : array-like
            Per-subject means for the two conditions.  Must be paired
            (same subject in same position) when ``paired=True``.
        eftype : {'hedges', 'cohen'}
            Standardised mean difference. Hedges' g is recommended for
            small samples (n < 50) — it applies the small-sample bias
            correction.
        """
        a = np.asarray(cond_a, dtype=float)
        b = np.asarray(cond_b, dtype=float)
        a = a[~np.isnan(a)]
        b = b[~np.isnan(b)]
        if paired:
            n = min(len(a), len(b))
            a, b = a[:n], b[:n]
        if len(a) < 2 or len(b) < 2:
            return {'effect_size': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
                    'eftype': eftype, 'paired': paired, 'n': 0,
                    'mean_a': np.nan, 'mean_b': np.nan, 'mean_diff': np.nan}
        if _PINGOUIN_AVAILABLE:
            try:
                es = float(_pg.compute_effsize(a, b, paired=paired, eftype=eftype))
                # Bootstrap CI: pingouin accepts 'hedges'/'cohen' as a string
                # and handles paired resampling internally.
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ci = _pg.compute_bootci(
                        x=a, y=b, func=eftype,
                        paired=paired, method='bca', n_boot=2000, seed=42,
                    )
                ci_low, ci_high = float(ci[0]), float(ci[1])
            except Exception:
                es = cls._smd_fallback(a, b, eftype)
                ci_low = ci_high = np.nan
        else:
            es = cls._smd_fallback(a, b, eftype)
            ci_low = ci_high = np.nan
        return {
            'effect_size': es,
            'ci_low':      ci_low,
            'ci_high':     ci_high,
            'eftype':      eftype,
            'paired':      paired,
            'n':           int(len(a)),
            'mean_a':      float(np.mean(a)),
            'mean_b':      float(np.mean(b)),
            'mean_diff':   float(np.mean(a) - np.mean(b)),
        }

    @staticmethod
    def _smd_fallback(a: np.ndarray, b: np.ndarray, eftype: str) -> float:
        """Standardised mean difference fallback (no pingouin)."""
        pooled = np.sqrt((np.var(a, ddof=1) + np.var(b, ddof=1)) / 2)
        if pooled == 0:
            return 0.0
        d = (np.mean(a) - np.mean(b)) / pooled
        if eftype == 'hedges':
            n = len(a) + len(b)
            d *= (1 - 3 / (4 * n - 9)) if n > 3 else 1.0
        return float(d)

    # ── Internal consistency ────────────────────────────────────────────────

    @classmethod
    def calculate_cronbach_alpha(cls, trial_matrix: pd.DataFrame) -> Dict:
        """Cronbach's α / KR-20 with 95% CI.

        Parameters
        ----------
        trial_matrix : pd.DataFrame
            Wide-format dataframe of shape (n_subjects, n_trials).
            Rows are subjects, columns are trials/items.  For binary
            accuracy data this reduces to KR-20.

        Returns dict with ``alpha, ci_low, ci_high, n_items, n_subjects``.
        Returns NaNs when fewer than 2 items or 2 subjects are available.
        """
        if trial_matrix is None or trial_matrix.empty:
            return {'alpha': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
                    'n_items': 0, 'n_subjects': 0}
        # Drop columns that are constant (variance = 0) — they break alpha
        nonconst = trial_matrix.loc[:, trial_matrix.nunique(dropna=True) > 1]
        if nonconst.shape[1] < 2 or nonconst.shape[0] < 2:
            return {'alpha': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
                    'n_items': int(nonconst.shape[1]),
                    'n_subjects': int(nonconst.shape[0])}
        if _PINGOUIN_AVAILABLE:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    alpha, ci = _pg.cronbach_alpha(data=nonconst)
                return {'alpha': float(alpha),
                        'ci_low': float(ci[0]), 'ci_high': float(ci[1]),
                        'n_items': int(nonconst.shape[1]),
                        'n_subjects': int(nonconst.shape[0])}
            except Exception:
                pass
        # Fallback — closed-form alpha, no CI
        item_var = nonconst.var(axis=0, ddof=1).sum()
        total_var = nonconst.sum(axis=1).var(ddof=1)
        k = nonconst.shape[1]
        alpha = (k / (k - 1)) * (1 - item_var / total_var) if total_var > 0 else np.nan
        return {'alpha': float(alpha), 'ci_low': np.nan, 'ci_high': np.nan,
                'n_items': int(nonconst.shape[1]),
                'n_subjects': int(nonconst.shape[0])}

    @staticmethod
    def calculate_split_half(trial_matrix: pd.DataFrame) -> Dict:
        """Spearman-Brown corrected odd/even split-half reliability.

        Useful for RT (continuous) where Cronbach is harder to interpret.
        """
        if trial_matrix is None or trial_matrix.empty or trial_matrix.shape[1] < 2:
            return {'split_half': np.nan, 'spearman_brown': np.nan, 'n_items': 0}
        odd  = trial_matrix.iloc[:, 0::2].mean(axis=1)
        even = trial_matrix.iloc[:, 1::2].mean(axis=1)
        valid = (~odd.isna()) & (~even.isna())
        if valid.sum() < 3:
            return {'split_half': np.nan, 'spearman_brown': np.nan,
                    'n_items': int(trial_matrix.shape[1])}
        try:
            r, _ = stats.pearsonr(odd[valid], even[valid])
        except Exception:
            return {'split_half': np.nan, 'spearman_brown': np.nan,
                    'n_items': int(trial_matrix.shape[1])}
        sb = (2 * r) / (1 + r) if (1 + r) != 0 else np.nan
        return {'split_half': float(r), 'spearman_brown': float(sb),
                'n_items': int(trial_matrix.shape[1])}

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

    # ── Condition-axis helpers (multi-condition paradigms, e.g. FLOW) ─────────
    #
    # The default pipeline treats every non-control ``trial_type`` as an
    # independent "task" cell and reports one ICC per cell.  Paradigms whose
    # scientific signal lives in a *contrast between conditions* (Flow vs
    # Boredom) or in a *composite of conditions* (flow index = -B + 2F - O)
    # have no home in that model.  The two methods below add that home without
    # touching the existing per-cell behaviour.

    @staticmethod
    def resolve_contrast_levels(
        contrast: Optional[str],
        available_levels: List[str],
    ) -> Optional[Tuple[str, str]]:
        """Resolve a ``"A_vs_B"`` contrast string against a set of labels.

        Matches either a full label (``"FLOW_F"``) or a case-insensitive
        suffix/token (``"flow"`` matches ``"FLOW_F"``).  Returns
        ``(level_a, level_b)`` as the *actual* labels present, or ``None`` when
        either side cannot be resolved unambiguously.

        This is what lets ``paradigm_contrast="flow_vs_boredom"`` work when the
        conditions live in the ``trial_type`` / ``condition`` column rather than
        in ``learning_stage``.
        """
        if not contrast or '_vs_' not in contrast:
            return None
        a_tok, b_tok = (s.strip() for s in contrast.split('_vs_', 1))
        levels = [str(l) for l in available_levels]
        # suffix after the last '_' — for FLOW_B/FLOW_O/FLOW_F this is B/O/F
        suffix = {l: l.rsplit('_', 1)[-1] for l in levels}
        all_suffix_single = levels and all(len(s) == 1 for s in suffix.values())

        def _uniq(cands: List[str]) -> Optional[str]:
            return cands[0] if len(cands) == 1 else None

        def _match(tok: str) -> Optional[str]:
            t = tok.lower()
            # 1) exact (case-insensitive) full-label match
            hit = _uniq([l for l in levels if l.lower() == t])
            if hit:
                return hit
            # 2) token equals the label suffix, e.g. 'f' vs 'FLOW_F'
            hit = _uniq([l for l in levels if suffix[l].lower() == t])
            if hit:
                return hit
            # 3) token's initial equals a single-char suffix, e.g.
            #    'flow'->'f' == 'F' in FLOW_F.  Only when every label uses a
            #    single-character suffix (the B/O/F condition-code pattern) so
            #    this heuristic cannot misfire on multi-letter stage labels.
            if all_suffix_single and t:
                hit = _uniq([l for l in levels if suffix[l].lower() == t[0]])
                if hit:
                    return hit
            # 4) token uniquely contained in exactly one label
            hit = _uniq([l for l in levels if t in l.lower()])
            if hit:
                return hit
            return None

        a, b = _match(a_tok), _match(b_tok)
        if a is None or b is None or a == b:
            return None
        return (a, b)

    @classmethod
    def compute_condition_contrast(
        cls,
        df: pd.DataFrame,
        column: str,
        level_a: str,
        level_b: str,
        session,
        level_col: str = 'trial_type',
    ) -> Dict:
        """Within-session Hedges' g between two *conditions* (paired by subject).

        Unlike the stage-based path inside ``compute_for_outcome``, this reads
        the condition labels from ``level_col`` (default ``trial_type``) so it
        works for paradigms whose contrast is across conditions rather than
        across learning stages.  Computed on a single session (``session``) so
        it measures paradigm sensitivity uncontaminated by retest effects.
        """
        empty = {
            'effect_size': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
            'eftype': 'hedges', 'paired': True, 'n': 0,
            'mean_a': np.nan, 'mean_b': np.nan, 'mean_diff': np.nan,
            'contrast': f'{level_a}_vs_{level_b}',
        }
        if df.empty or level_col not in df.columns or 'session' not in df.columns:
            return empty
        d = df[df['session'] == session]
        if d.empty or 'subject_id' not in d.columns:
            return empty
        a_vals, b_vals = [], []
        for subj in d['subject_id'].unique():
            sd = d[d['subject_id'] == subj]
            va = pd.to_numeric(sd[sd[level_col].astype(str) == str(level_a)][column],
                               errors='coerce').dropna()
            vb = pd.to_numeric(sd[sd[level_col].astype(str) == str(level_b)][column],
                               errors='coerce').dropna()
            if len(va) and len(vb):
                a_vals.append(float(va.mean()))
                b_vals.append(float(vb.mean()))
        if len(a_vals) < 3:
            return empty
        res = cls.calculate_paradigm_effect_size(a_vals, b_vals)
        res['contrast'] = f'{level_a}_vs_{level_b}'
        return res

    @classmethod
    def compute_composite_index_reliability(
        cls,
        df: pd.DataFrame,
        weights: Dict[str, float],
        value_columns: List[str],
        level_col: str = 'condition',
        outcome_id: str = 'composite',
    ) -> Dict:
        """Test-retest reliability of a *cross-condition composite* score.

        Designed for scores such as the FLOW subjective flow index,
        ``(-B + 2F - O)`` summed across the three Likert items.  For each
        (subject, session) it forms one composite value:

            composite = Sum_conditions  weight[condition] * mean(value_columns)

        then computes ICC(C,1), ICC(A,1), Pearson r, and session-shift d on the
        paired subject-level composites across the first two sessions.

        Parameters
        ----------
        df : DataFrame
            Long block/trial frame containing ``subject_id``, ``session``,
            ``level_col`` and every column in ``value_columns``.
        weights : {condition_label: weight}
            e.g. ``{"B": -1, "F": 2, "O": -1}``.  Condition labels are matched
            case-insensitively against ``level_col``.
        value_columns : list of str
            Columns averaged (then summed) to form the per-condition score --
            e.g. the three Likert item columns.  A single column is fine.
        level_col : str
            Column holding the condition label (default ``condition``).

        Returns a flat dict keyed like the per-outcome dicts
        (``{oid}_icc``, ``{oid}_icc_agreement``, ``{oid}_pearson_r``,
        ``{oid}_session_shift_d`` ...) so it merges into ``reliability_metrics``
        with no special-casing downstream.
        """
        oid = outcome_id.lower()
        nan_out = {
            f'{oid}_icc': np.nan, f'{oid}_icc_ci_low': np.nan, f'{oid}_icc_ci_high': np.nan,
            f'{oid}_icc_agreement': np.nan,
            f'{oid}_icc_agreement_ci_low': np.nan, f'{oid}_icc_agreement_ci_high': np.nan,
            f'{oid}_pearson_r': np.nan, f'{oid}_session_shift_d': np.nan,
            f'{oid}_n_subjects': 0, f'{oid}_s1_means': [], f'{oid}_s2_means': [],
            f'{oid}_subjects': [], f'{oid}_is_composite': True,
            f'{oid}_composite_weights': dict(weights),
            # legacy aliases
            f'{oid}_icc_mean': np.nan, f'{oid}_icc_agreement_mean': np.nan,
            f'{oid}_pearson_r_mean': np.nan, f'{oid}_cohens_d_mean': np.nan,
        }
        need = {'subject_id', 'session', level_col}
        if df.empty or not need.issubset(df.columns):
            return nan_out
        cols_present = [c for c in value_columns if c in df.columns]
        if not cols_present:
            return nan_out

        # lower-cased weight lookup
        wmap = {str(k).lower(): float(v) for k, v in weights.items()}
        sessions = sorted(df['session'].unique())
        if len(sessions) < 2:
            return nan_out
        s1, s2 = sessions[0], sessions[1]

        def _subject_session_composite(sd: pd.DataFrame) -> Optional[float]:
            total, seen = 0.0, 0
            for cond_label, w in wmap.items():
                rows = sd[sd[level_col].astype(str).str.lower() == cond_label]
                if rows.empty:
                    continue
                # per-condition score = mean over value columns of their means
                per_col = []
                for c in cols_present:
                    vals = pd.to_numeric(rows[c], errors='coerce').dropna()
                    if len(vals):
                        per_col.append(float(vals.mean()))
                if per_col:
                    total += w * float(np.mean(per_col))
                    seen += 1
            # require every weighted condition to be present
            return total if seen == len(wmap) else None

        subjects, v1, v2 = [], [], []
        for subj in df['subject_id'].unique():
            sd1 = df[(df['subject_id'] == subj) & (df['session'] == s1)]
            sd2 = df[(df['subject_id'] == subj) & (df['session'] == s2)]
            c1 = _subject_session_composite(sd1) if not sd1.empty else None
            c2 = _subject_session_composite(sd2) if not sd2.empty else None
            if c1 is not None and c2 is not None:
                subjects.append(subj)
                v1.append(c1)
                v2.append(c2)

        if len(subjects) < 3:
            out = dict(nan_out)
            out[f'{oid}_n_subjects'] = len(subjects)
            out[f'{oid}_s1_means'] = v1
            out[f'{oid}_s2_means'] = v2
            out[f'{oid}_subjects'] = subjects
            return out

        a1, a2 = np.array(v1), np.array(v2)
        icc_c = cls.calculate_icc(a1, a2)
        icc_a = cls.calculate_icc_agreement(a1, a2)
        pear  = cls.calculate_pearson_r(a1, a2)
        shift = cls.calculate_cohens_d_paired(a1, a2)
        return {
            f'{oid}_icc': icc_c['icc'],
            f'{oid}_icc_ci_low': icc_c['ci_low'], f'{oid}_icc_ci_high': icc_c['ci_high'],
            f'{oid}_icc_F': icc_c['F'], f'{oid}_icc_p': icc_c['p'],
            f'{oid}_icc_agreement': icc_a['icc'],
            f'{oid}_icc_agreement_ci_low': icc_a['ci_low'],
            f'{oid}_icc_agreement_ci_high': icc_a['ci_high'],
            f'{oid}_icc_agreement_F': icc_a['F'], f'{oid}_icc_agreement_p': icc_a['p'],
            f'{oid}_pearson_r': pear,
            f'{oid}_session_shift_d': shift,
            f'{oid}_n_subjects': len(subjects),
            f'{oid}_s1_means': v1, f'{oid}_s2_means': v2, f'{oid}_subjects': subjects,
            f'{oid}_is_composite': True, f'{oid}_composite_weights': dict(weights),
            'session_labels': [str(s1), str(s2)],
            # legacy aliases so existing dashboard key-matching still finds it
            f'{oid}_icc_mean': icc_c['icc'],
            f'{oid}_icc_agreement_mean': icc_a['icc'],
            f'{oid}_pearson_r_mean': pear,
            f'{oid}_cohens_d_mean': shift,
        }

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
        if rule == "effect_size":
            # Bigger |g| is better here (paradigm sensitivity), capped at 1.5
            # (commonly considered "very large").  Sign is irrelevant —
            # paradigm could be calibrated either way.
            return float(max(0.0, min(1.0, abs(value) / 1.5)))
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
        paradigm_contrast: Optional[str] = None,
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

        Parameters
        ----------
        paradigm_contrast : str, optional
            ``"<levelA>_vs_<levelB>"`` — pins the within-session contrast
            used for Hedges' g (paradigm effect size).  Both levels must
            appear in the ``learning_stage`` column.  When omitted, the
            pipeline falls back to its default of
            ``<last_stage>_vs_<first_stage>``.  Useful for non-OLM paradigms
            where the meaningful contrast is e.g.
            ``incongruent_vs_congruent`` (Stroop) or ``2back_vs_0back``.
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
            # session-level vectors for Pearson/Cohen, plus CV for continuous outcomes.
            # Binary accuracy: cv_all stays empty (CV not meaningful for 0/1 data).
            s1_means, s2_means, cv_all = [], [], []

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

                # Within-session dispersion / performance display metric.
                # Continuous outcomes: coefficient of variation (CV).
                # Binary accuracy: do NOT compute Bernoulli CV. For 0/1 data,
                # SD is forced to be √(p(1−p)), so CV = √((1−p)/p)·100 is a
                # deterministic re-expression of the mean accuracy. Instead,
                # store mean accuracy as a percentage so the dashboard can show
                # an interpretable Accuracy % slider/card rather than a fake
                # or missing "Accuracy CV".
                #
                # Detection: (a) explicit outcome_id allow-list or (b) the
                # actual values are a subset of {0, 1}. (b) catches the
                # legacy wrapper path (compute_reliability_dict) which passes
                # outcome_id='ACC' for binary accuracy_binary data.
                vals_union = set(v1_all.unique()) | set(v2_all.unique())
                is_binary = (outcome_id in BINARY_OUTCOME_IDS or
                             (len(vals_union) > 0 and vals_union <= {0, 1, 0.0, 1.0}))
                if not is_binary:
                    # Continuous outcome: compute within-session CV
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

            # ── ICC: full result dicts (point + CI + F + df + p) ─────────────
            if len(icc_s1) > 2:
                icc_consistency = cls.calculate_icc(icc_s1, icc_s2)
                icc_agreement   = cls.calculate_icc_agreement(icc_s1, icc_s2)
            else:
                icc_consistency = dict(cls._NAN_ICC)
                icc_agreement   = dict(cls._NAN_ICC)

            # Pearson r (session-level means)
            pearson = (cls.calculate_pearson_r(s1, s2)
                       if len(s1) > 2 else np.nan)

            # Session-shift "stability" (paired Cohen's d on session means).
            # Renamed from cohens_d to make the semantic explicit: this is
            # *between-session drift*, not a paradigm effect size.
            session_shift_d = (cls.calculate_cohens_d_paired(s1, s2)
                               if len(s1) > 2 else np.nan)

            # ── Paradigm effect size: Stage N vs Stage 1 (within session 1) ──
            # Captures the learning effect / paradigm sensitivity, separate
            # from the test-retest stability above.  Computed on session-1
            # data so it is uncontaminated by retest effects.  Generalises
            # to any paradigm with a stage / load / condition gradient — e.g.
            # 2-back vs 0-back, incongruent vs congruent.
            paradigm_es: Dict = {
                'effect_size': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
                'eftype': 'hedges', 'paired': True, 'n': 0,
                'mean_a': np.nan, 'mean_b': np.nan, 'mean_diff': np.nan,
                'contrast': None,
            }
            if has_stages:
                stages_sorted = sorted(
                    dff['learning_stage'].dropna().astype(str).unique(),
                    key=lambda s: (len(s), s)
                )
                # Resolve which two levels to contrast.  Priority:
                # 1. caller-supplied paradigm_contrast="A_vs_B"
                # 2. default: <last_stage>_vs_<first_stage>
                first_st, last_st = None, None
                if paradigm_contrast and '_vs_' in paradigm_contrast:
                    a, b = paradigm_contrast.split('_vs_', 1)
                    a, b = a.strip(), b.strip()
                    present = set(stages_sorted)
                    if a in present and b in present:
                        last_st, first_st = a, b
                if first_st is None and len(stages_sorted) >= 2:
                    first_st, last_st = stages_sorted[0], stages_sorted[-1]
                if first_st is not None and last_st is not None:
                    s1_dff = dff[dff['session'] == sessions[0]]
                    a, b = [], []
                    for subj in subjects:
                        sub_a = pd.to_numeric(
                            s1_dff[(s1_dff['subject_id'] == subj) &
                                   (s1_dff['learning_stage'].astype(str) == last_st)][column],
                            errors='coerce').dropna()
                        sub_b = pd.to_numeric(
                            s1_dff[(s1_dff['subject_id'] == subj) &
                                   (s1_dff['learning_stage'].astype(str) == first_st)][column],
                            errors='coerce').dropna()
                        if len(sub_a) and len(sub_b):
                            a.append(float(sub_a.mean()))
                            b.append(float(sub_b.mean()))
                    if len(a) >= 3:
                        paradigm_es = cls.calculate_paradigm_effect_size(a, b)
                        paradigm_es['contrast'] = f'{last_st}_vs_{first_st}'

            # ── Condition-axis fallback for the paradigm contrast ────────────
            # When there is no learning_stage axis (or the requested contrast
            # levels are not stages) but the contrast names two *conditions*
            # present in the trial_type column — e.g. paradigm_contrast=
            # "flow_vs_boredom" over FLOW_F / FLOW_B — compute Hedges' g across
            # those conditions on the full (unfiltered-by-tt) frame.  This is
            # the same value for every trial-type cell, so it is only computed
            # once and reused.  Without this, multi-condition paradigms report
            # no paradigm effect size at all.
            if (np.isnan(paradigm_es.get('effect_size', np.nan))
                    and paradigm_contrast and '_vs_' in paradigm_contrast
                    and 'trial_type' in df.columns):
                levels = df['trial_type'].dropna().astype(str).unique().tolist()
                resolved = cls.resolve_contrast_levels(paradigm_contrast, levels)
                if resolved is not None:
                    lvl_a, lvl_b = resolved
                    cc = cls.compute_condition_contrast(
                        df, column, lvl_a, lvl_b, sessions[0],
                        level_col='trial_type')
                    if not np.isnan(cc.get('effect_size', np.nan)):
                        paradigm_es = cc

            # ── Internal consistency: Cronbach's α on session-1 trials ───────
            # Builds a (subject × trial-index) wide matrix from session 1.
            # For binary outcomes this is KR-20.  Uses pingouin's
            # cronbach_alpha when available — gives a 95% CI for free.
            cron: Dict = {'alpha': np.nan, 'ci_low': np.nan, 'ci_high': np.nan,
                          'n_items': 0, 'n_subjects': 0}
            try:
                s1_only = dff[dff['session'] == sessions[0]].copy()
                if not s1_only.empty:
                    s1_only['_tidx'] = s1_only.groupby('subject_id').cumcount()
                    wide = (s1_only.pivot_table(index='subject_id',
                                                columns='_tidx',
                                                values=column,
                                                aggfunc='first'))
                    wide = wide.apply(pd.to_numeric, errors='coerce')
                    if wide.shape[1] > 100:
                        # Cap at 100 items to keep alpha meaningful and fast
                        wide = wide.iloc[:, :100]
                    cron = cls.calculate_cronbach_alpha(wide)
            except Exception:
                pass

            # ── CV / Accuracy % display metric ───────────────────────────────
            # Continuous outcomes keep trial-level CV.
            # Binary outcomes: cv_mean stays None (Bernoulli CV is not meaningful).
            # accuracy_percent_* is intentionally NOT stored — binary accuracy is
            # represented by the ICC / α metrics on the raw 0/1 data.
            cv_mean = float(np.mean(cv_all)) if cv_all else None
            cv_std  = float(np.std(cv_all))  if cv_all else None

            reliability[trial_type] = {
                # ─── ICC consistency, ICC(C,1) ─────────────────────────────
                f'{oid}_icc':                  icc_consistency['icc'],
                f'{oid}_icc_ci_low':           icc_consistency['ci_low'],
                f'{oid}_icc_ci_high':          icc_consistency['ci_high'],
                f'{oid}_icc_F':                icc_consistency['F'],
                f'{oid}_icc_df1':              icc_consistency['df1'],
                f'{oid}_icc_df2':              icc_consistency['df2'],
                f'{oid}_icc_p':                icc_consistency['p'],
                # ─── ICC absolute agreement, ICC(A,1) ──────────────────────
                f'{oid}_icc_agreement':        icc_agreement['icc'],
                f'{oid}_icc_agreement_ci_low': icc_agreement['ci_low'],
                f'{oid}_icc_agreement_ci_high':icc_agreement['ci_high'],
                f'{oid}_icc_agreement_F':      icc_agreement['F'],
                f'{oid}_icc_agreement_df1':    icc_agreement['df1'],
                f'{oid}_icc_agreement_df2':    icc_agreement['df2'],
                f'{oid}_icc_agreement_p':      icc_agreement['p'],
                f'{oid}_icc_n_observations':   len(stage_s1),
                # ─── Pearson r (session-level) ──────────────────────────────
                f'{oid}_pearson_r':            pearson,
                # ─── Session-shift stability (renamed from cohens_d) ────────
                # Paired Cohen's d on session means.  Small |d| ⇒ stable.
                f'{oid}_session_shift_d':      session_shift_d,
                # ─── Paradigm effect size (within-session contrast) ─────────
                f'{oid}_paradigm_effect_size':           paradigm_es['effect_size'],
                f'{oid}_paradigm_effect_size_ci_low':    paradigm_es['ci_low'],
                f'{oid}_paradigm_effect_size_ci_high':   paradigm_es['ci_high'],
                f'{oid}_paradigm_effect_size_type':      paradigm_es['eftype'],
                f'{oid}_paradigm_effect_size_contrast':  paradigm_es['contrast'],
                f'{oid}_paradigm_effect_size_n':         paradigm_es['n'],
                # ─── Internal consistency ───────────────────────────────────
                f'{oid}_cronbach_alpha':         cron['alpha'],
                f'{oid}_cronbach_alpha_ci_low':  cron['ci_low'],
                f'{oid}_cronbach_alpha_ci_high': cron['ci_high'],
                f'{oid}_cronbach_alpha_n_items': cron['n_items'],
                # ─── CV (continuous outcomes only) ──────────────────────────
                # Binary accuracy: CV is not stored at all — Bernoulli CV is a
                # deterministic re-expression of the mean (CV = √((1−p)/p)·100)
                # and carries no independent information.  accuracy_percent_* is
                # also not stored; binary accuracy is conveyed by the ICC / α
                # metrics which operate on the 0/1 values directly.
                f'{oid}_cv_mean':              cv_mean,
                f'{oid}_cv_std':               cv_std,
                # ─── Metadata + raw paired vectors ──────────────────────────
                f'{oid}_n_subjects':           len(subjects),
                f'{oid}_s1_means':             s1_means,
                f'{oid}_s2_means':             s2_means,
                f'{oid}_subjects':             subjects,
                'session_labels':              [str(sessions[0]), str(sessions[1])],
                # ─── Backward-compat aliases (so existing dashboards keep working) ─
                # Same numbers, old key names.  Drop these in a future major version.
                f'{oid}_icc_mean':             icc_consistency['icc'],
                f'{oid}_icc_agreement_mean':   icc_agreement['icc'],
                f'{oid}_pearson_r_mean':       pearson,
                f'{oid}_cohens_d_mean':        session_shift_d,
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
        outcome_ids: Optional[List[str]] = None,
        show_trial_type: bool = True,
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
        outcome_ids:
            The outcome IDs actually declared by the project (lower-cased).

            Strongly recommended.  Metric keys are ``f'{outcome_id}{suffix}'``,
            so recovering the outcome id from a key means splitting on a
            delimiter that also occurs *inside* ids.  The legacy fallback below
            guesses, and to stay safe it discards any id containing an
            underscore — which silently drops every spoke for outcomes named
            e.g. ``FlowIndex_Likert``, leaving an empty radar with no error.
            Passing the ids removes the guesswork entirely.
        """
        ids_to_show = selected_metric_ids if selected_metric_ids else ALL_METRIC_IDS
        olabels = outcome_labels or {}

        # Map metric_id → list of key suffixes to try (new schema first,
        # then the legacy `_<id>_mean` suffix for backward-compat with older
        # JSON files).  cv is special: it always lived under `_cv_mean`.
        suffix_map: Dict[str, List[str]] = {
            'icc':                   ['_icc',                   '_icc_mean'],
            'icc_agreement':         ['_icc_agreement',         '_icc_agreement_mean'],
            'pearson_r':             ['_pearson_r',             '_pearson_r_mean'],
            'cronbach_alpha':        ['_cronbach_alpha'],
            'session_shift_d':       ['_session_shift_d',       '_cohens_d_mean'],
            'cohens_d':              ['_cohens_d_mean',         '_session_shift_d'],  # legacy id
            'paradigm_effect_size':  ['_paradigm_effect_size'],
            'cv':                    ['_cv_mean'],
        }

        categories: List[str] = []
        values:     List[float] = []
        seen_pairs = set()  # avoid duplicate spokes when both new+legacy keys present

        known_ids = [str(o).lower() for o in (outcome_ids or [])]

        def _label(reg, tt, human):
            # With a single trial type the prefix names a condition that does
            # not exist (see the violin/banner suppression) — drop it.
            lbl = reg['radar_label'].format(tt=(tt if show_trial_type else ''),
                                            label=human)
            return ' '.join(lbl.split())

        def _add(tt, mid, oid, val, reg):
            if val is None:
                return
            if reg.get('skip_for_binary') and oid.lower() in BINARY_OUTCOME_IDS:
                return
            pair_key = (tt, mid, oid)
            if pair_key in seen_pairs:
                return
            norm = cls.normalise_for_radar(mid, val)
            if norm is None:
                return
            human = olabels.get(oid, oid.upper())
            categories.append(_label(reg, tt, human))
            values.append(norm)
            seen_pairs.add(pair_key)

        for tt, metrics in rel_dict.items():
            for mid in ids_to_show:
                reg = METRIC_BY_ID.get(mid)
                if reg is None:
                    continue
                suffixes = suffix_map.get(mid, [f'_{mid}_mean'])

                if known_ids:
                    # Exact lookup — no parsing, so underscores in outcome ids
                    # (FlowIndex_Likert, rt_congruent, …) are handled correctly.
                    for oid in known_ids:
                        for suffix in suffixes:
                            if f'{oid}{suffix}' in metrics:
                                _add(tt, mid, oid, metrics[f'{oid}{suffix}'], reg)
                                break
                    continue

                # ── Legacy fallback: infer the id from the key (guesses) ──────
                for suffix in suffixes:
                    for key, val in metrics.items():
                        if not key.endswith(suffix) or val is None:
                            continue
                        oid = key[: -len(suffix)]
                        if not oid or oid.count('_') > 0:
                            continue
                        _add(tt, mid, oid, val, reg)

        return categories, values