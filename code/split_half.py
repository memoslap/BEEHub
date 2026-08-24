"""
split_half.py — permutation split-half internal consistency for R-BEEHub.

Why this exists
---------------
Cronbach's alpha assumes a set of comparable items and is a poor fit for
trial-level behavioural measures, and it is actively misleading for DIFFERENCE
scores (Stroop interference, dot-probe bias, go/no-go contrasts), where the
subtraction removes much of the between-subject variance that alpha rewards.

The permutation split-half approach used by the R package `splithalf`
(Parsons, 2021) handles both cases: split a participant's trials at random into
two halves, score each half, correlate the halves across participants, apply the
Spearman-Brown correction, and repeat many times to obtain a DISTRIBUTION of
estimates rather than a single value that depends on one arbitrary split.

This is a from-scratch Python implementation of that estimator, so R-BEEHub can
report it without a cross-language runtime dependency. It is NOT a port of the
`splithalf` source and does not reproduce its API; results should be expected to
agree in distribution, not bit-for-bit. Validate against `splithalf` on a shared
dataset before relying on the two interchangeably.

Reference for the method:
    Parsons, S. (2021). splithalf: robust estimates of split half reliability.
    Journal of Open Source Software, 6(60), 3041. doi:10.21105/joss.03041
    Spearman-Brown: Spearman (1910); Brown (1910).
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Sequence

import numpy as np


@dataclass
class SplitHalfResult:
    """One reliability estimate with its uncertainty."""
    estimate: float           # median of the corrected distribution
    ci_low: float             # 2.5th percentile
    ci_high: float            # 97.5th percentile
    n_subjects: int
    n_permutations: int
    min_trials: int           # smallest per-subject trial count entering the estimate
    score: str                # "mean" or "difference"
    raw_median: float         # median BEFORE Spearman-Brown correction

    def to_dict(self) -> dict:
        return asdict(self)


def _spearman_brown(r: np.ndarray) -> np.ndarray:
    """Correct a half-test correlation to full-test length.

    Undefined at r = -1; those permutations are dropped by the caller rather
    than clipped, so a degenerate split cannot silently bias the distribution.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        return 2.0 * r / (1.0 + r)


def _score_halves(trials: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    """Randomly halve one subject's trials and return the mean of each half."""
    n = trials.shape[0]
    idx = rng.permutation(n)
    h = n // 2
    return float(np.mean(trials[idx[:h]])), float(np.mean(trials[idx[h:2 * h]]))


def split_half(
    subject_trials: Sequence[np.ndarray],
    n_permutations: int = 5000,
    seed: int | None = 42,
) -> SplitHalfResult:
    """Permutation split-half reliability of a simple (non-difference) measure.

    Parameters
    ----------
    subject_trials
        One 1-D array of trial-level values per subject. Arrays may differ in
        length; subjects with fewer than 4 usable trials are excluded, since a
        two-trial half cannot be scored meaningfully.
    n_permutations
        Number of random splits. 5000 is ample; the estimate stabilises well
        before that for typical designs.
    seed
        Fixed by default so a reported value is reproducible. Set to None for a
        different draw.
    """
    usable = [np.asarray(t, dtype=float) for t in subject_trials]
    usable = [t[np.isfinite(t)] for t in usable]
    usable = [t for t in usable if t.size >= 4]
    if len(usable) < 3:
        raise ValueError(
            f"need >=3 subjects with >=4 usable trials, got {len(usable)}"
        )

    rng = np.random.default_rng(seed)
    raw = np.empty(n_permutations)
    for p in range(n_permutations):
        a = np.empty(len(usable))
        b = np.empty(len(usable))
        for i, t in enumerate(usable):
            a[i], b[i] = _score_halves(t, rng)
        # Guard against a constant half, where the correlation is undefined.
        if np.std(a) == 0 or np.std(b) == 0:
            raw[p] = np.nan
        else:
            raw[p] = np.corrcoef(a, b)[0, 1]

    return _summarise(raw, len(usable), n_permutations,
                      min(t.size for t in usable), "mean")


def split_half_difference(
    subject_condition_a: Sequence[np.ndarray],
    subject_condition_b: Sequence[np.ndarray],
    n_permutations: int = 5000,
    seed: int | None = 42,
) -> SplitHalfResult:
    """Permutation split-half reliability of a DIFFERENCE score (A minus B).

    Trials are split within each condition separately, so each half yields a
    complete difference score. This is the case where Cronbach's alpha is least
    appropriate and where this estimator matters most.
    """
    a_list = [np.asarray(t, dtype=float) for t in subject_condition_a]
    b_list = [np.asarray(t, dtype=float) for t in subject_condition_b]
    if len(a_list) != len(b_list):
        raise ValueError("condition A and B must have the same number of subjects")

    keep = [
        i for i in range(len(a_list))
        if np.isfinite(a_list[i]).sum() >= 4 and np.isfinite(b_list[i]).sum() >= 4
    ]
    if len(keep) < 3:
        raise ValueError(
            f"need >=3 subjects with >=4 usable trials in BOTH conditions, got {len(keep)}"
        )
    a_list = [a_list[i][np.isfinite(a_list[i])] for i in keep]
    b_list = [b_list[i][np.isfinite(b_list[i])] for i in keep]

    rng = np.random.default_rng(seed)
    raw = np.empty(n_permutations)
    for p in range(n_permutations):
        d1 = np.empty(len(a_list))
        d2 = np.empty(len(a_list))
        for i in range(len(a_list)):
            a1, a2 = _score_halves(a_list[i], rng)
            b1, b2 = _score_halves(b_list[i], rng)
            d1[i] = a1 - b1
            d2[i] = a2 - b2
        if np.std(d1) == 0 or np.std(d2) == 0:
            raw[p] = np.nan
        else:
            raw[p] = np.corrcoef(d1, d2)[0, 1]

    min_tr = min(min(t.size for t in a_list), min(t.size for t in b_list))
    return _summarise(raw, len(a_list), n_permutations, min_tr, "difference")


def _summarise(raw: np.ndarray, n_sub: int, n_perm: int,
               min_trials: int, score: str) -> SplitHalfResult:
    raw = raw[np.isfinite(raw)]
    if raw.size == 0:
        raise ValueError("no permutation produced a defined correlation")
    corrected = _spearman_brown(raw)
    corrected = corrected[np.isfinite(corrected)]
    return SplitHalfResult(
        estimate=float(np.median(corrected)),
        ci_low=float(np.percentile(corrected, 2.5)),
        ci_high=float(np.percentile(corrected, 97.5)),
        n_subjects=n_sub,
        n_permutations=int(raw.size),
        min_trials=int(min_trials),
        score=score,
        raw_median=float(np.median(raw)),
    )
