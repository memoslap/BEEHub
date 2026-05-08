"""
verify_olm_bids.py
==================

Cross-check the rebuilt ``bids_data/`` against the numbers reported in
Abdelmotaleb et al. (Brain and Behavior, 2025).

Aggregation follows the paper's R script (``Behavioural_sham_sham.R``)
*and* the Behavioral_Exp_Hub pipeline's ``reliability_metrics.py``:

    * ICC is computed at the (subject × stage) level — one mean per cell,
      giving 20 subjects × 4 stages = 80 paired observations per session.
      This matches the paper's reported F(159, 159) and F(159, 133).
    * Accuracy uses ACCBIN (1 = correct, 0 = incorrect *or* "to late"),
      unfiltered.
    * RT uses all trials with a recorded response (R script: line 195–200,
      ``summarize(mean_learning_RT = mean(RT, na.rm = TRUE))``). It is NOT
      gated on correctness — that would drop cells where a subject has zero
      correct trials in a stage, diverge from the paper, and inflate the ICC.

For visualisation, the per-stage accuracy curve (Figure 2A) and RT curve
(Figure 2B) are reported using the same aggregation as the paper:
accuracy = all trials; RT = all trials.

Run it after ``olm_bids_builder.build_all(...)``; a line-by-line scorecard
compares the observed numbers against the paper's reported values.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# I/O
# ──────────────────────────────────────────────────────────────────────────────

_NAME_RE = re.compile(
    r"sub-(?P<sub>[^_]+)_ses-(?P<ses>[^_]+)_task-OLM_acq-(?P<acq>[^_]+)_"
    r"(?P<outcome>RT|ACC|ACCBIN)_beh\.tsv$"
)


def _read_tsv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", na_values=["n/a"])
    m = _NAME_RE.search(path.name)
    if not m:
        return pd.DataFrame()
    df["subject_id"] = m.group("sub")
    df["session"]    = m.group("ses")
    df["acq"]        = m.group("acq")
    return df


def load_rt_and_accbin(bids_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    rt_parts, ab_parts = [], []
    for p in bids_root.glob("sub-*/ses-*/*_RT_beh.tsv"):
        rt_parts.append(_read_tsv(p))
    for p in bids_root.glob("sub-*/ses-*/*_ACCBIN_beh.tsv"):
        ab_parts.append(_read_tsv(p))
    rt = pd.concat(rt_parts, ignore_index=True) if rt_parts else pd.DataFrame()
    ab = pd.concat(ab_parts, ignore_index=True) if ab_parts else pd.DataFrame()
    return rt, ab


# ──────────────────────────────────────────────────────────────────────────────
# Stage-level aggregation (matches paper's R script + reliability_metrics.py)
# ──────────────────────────────────────────────────────────────────────────────

def stage_means(df: pd.DataFrame, value_col: str,
                trial_type: str = "learning") -> pd.DataFrame:
    """Return one row per (subject_id, session, learning_stage) with the mean
    of ``value_col`` over the trials in that cell.

    This is the granularity the paper's R script uses for ICC
    (``group_by(Subject, Stage) %>% summarize(mean_X = mean(X, na.rm=TRUE))``)
    and that ``reliability_metrics.py`` uses (one mean per subject × stage ×
    session, feeding ~20 × 4 = 80 paired rows into the ICC).
    """
    sub = df[df["trial_type"] == trial_type].copy()
    sub[value_col] = pd.to_numeric(sub[value_col], errors="coerce")
    return (sub.dropna(subset=[value_col])
               .groupby(["subject_id", "session", "learning_stage"])[value_col]
               .mean().reset_index(name="stage_mean"))


def stage_mean_group(stage_df: pd.DataFrame) -> pd.DataFrame:
    """Collapse per-subject stage means to group means per stage — this is
    what Figure 2 plots (one point per stage, averaged over subjects)."""
    return (stage_df.groupby("learning_stage")["stage_mean"]
                    .agg(["mean", "std", "count"]))


# ──────────────────────────────────────────────────────────────────────────────
# ICC(A,1) — two-way mixed-effects, absolute agreement, single measurement
# ──────────────────────────────────────────────────────────────────────────────

def icc_a_1(s1: np.ndarray, s2: np.ndarray) -> float:
    """ICC(A,1) per McGraw & Wong (1996), matching R's irr::icc(model='twoway',
    type='agreement', unit='single'). Accepts two aligned 1D vectors of paired
    measurements (n observations × 2 sessions).
    """
    arr = np.column_stack([np.asarray(s1, dtype=float),
                           np.asarray(s2, dtype=float)])
    arr = arr[~np.isnan(arr).any(axis=1)]
    n, k = arr.shape
    if n < 2 or k < 2:
        return float("nan")

    grand = arr.mean()
    row_m = arr.mean(axis=1)
    col_m = arr.mean(axis=0)

    SST = ((arr - grand) ** 2).sum()
    SSR = k * ((row_m - grand) ** 2).sum()
    SSC = n * ((col_m - grand) ** 2).sum()
    SSE = SST - SSR - SSC

    MSR = SSR / (n - 1)
    MSC = SSC / (k - 1)
    MSE = SSE / ((n - 1) * (k - 1))

    denom = MSR + (k - 1) * MSE + k * (MSC - MSE) / n
    if denom == 0:
        return float("nan")
    return (MSR - MSE) / denom


def paired_stage_vectors(stage_df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, int]:
    """Pivot the (subject × session × stage) long table to paired vectors
    aligned on (subject, stage). Returns (s1, s2, n_pairs_kept)."""
    sessions = sorted(stage_df["session"].unique())
    if len(sessions) < 2:
        return np.array([]), np.array([]), 0
    s_a, s_b = sessions[0], sessions[1]
    wide = (stage_df
            .pivot_table(index=["subject_id", "learning_stage"],
                         columns="session", values="stage_mean", aggfunc="first")
            .dropna(subset=[s_a, s_b]))
    return wide[s_a].to_numpy(), wide[s_b].to_numpy(), len(wide)


# ──────────────────────────────────────────────────────────────────────────────
# Main report
# ──────────────────────────────────────────────────────────────────────────────

_EXPECTED = {
    "learning_accuracy_stage1": (0.60, 0.10, "Paper Fig. 2A: ~60%"),
    "learning_accuracy_stage4": (0.85, 0.10, "Paper Fig. 2A: ~85% (possibly higher w/ ceiling)"),
    "learning_rt_stage1_ms":    (1250,  200, "Paper Fig. 2B: ~1.2–1.3 s"),
    "learning_rt_stage4_ms":    (1050,  200, "Paper Fig. 2B: ~1.05 s"),
    "acc_icc":                  (0.801, 0.08, "Paper reports 0.801 [0.737, 0.850]"),
    "rt_icc":                   (0.705, 0.10, "Paper reports 0.705 [0.613, 0.777]"),
}


def _flag(value: float, target: float, tol: float) -> str:
    if np.isnan(value):
        return "  –   "
    return "  ✓  " if abs(value - target) <= tol else "  ✗  "


def report(bids_root: str | Path) -> dict[str, float]:
    bids_root = Path(bids_root)
    rt, ab = load_rt_and_accbin(bids_root)

    if rt.empty or ab.empty:
        print(f"No files found under {bids_root}")
        return {}

    n_subs  = ab["subject_id"].nunique()
    n_sess  = ab.groupby("subject_id")["session"].nunique().tolist()
    both_s  = sum(1 for x in n_sess if x == 2)
    print(f"Loaded {len(ab)} accbin rows and {len(rt)} RT rows "
          f"from {n_subs} subject(s), {both_s} with two sessions.")
    print()

    # ── Stage-level means (one row per subject × session × stage) ────────────
    # Accuracy: from ACCBIN, ungated.
    # RT: from RT TSV, ungated (matches the R script — see line 195-200 of
    #     Behavioural_sham_sham.R, which averages RT without filtering on
    #     correctness).
    acc_stage_learn = stage_means(ab, "accuracy_binary",  trial_type="learning")
    acc_stage_ctrl  = stage_means(ab, "accuracy_binary",  trial_type="control")
    rt_stage_learn  = stage_means(rt, "response_time_ms", trial_type="learning")
    rt_stage_ctrl   = stage_means(rt, "response_time_ms", trial_type="control")

    # ── Per-stage group summaries (reproduce Figure 2) ──────────────────────
    print("─── Learning accuracy per stage (Figure 2A) ────────────────────")
    print(stage_mean_group(acc_stage_learn).round(3))
    print()
    print("─── Control accuracy per stage ─────────────────────────────────")
    print(stage_mean_group(acc_stage_ctrl).round(3))
    print()
    print("─── Learning RT per stage (ms, Figure 2B) ──────────────────────")
    print(stage_mean_group(rt_stage_learn).round(0))
    print()
    print("─── Control RT per stage (ms) ──────────────────────────────────")
    print(stage_mean_group(rt_stage_ctrl).round(0))
    print()

    # ── Across-session ICCs on stage-level paired vectors ────────────────────
    acc_s1, acc_s2, acc_n = paired_stage_vectors(acc_stage_learn)
    rt_s1,  rt_s2,  rt_n  = paired_stage_vectors(rt_stage_learn)
    acc_icc = icc_a_1(acc_s1, acc_s2)
    rt_icc  = icc_a_1(rt_s1,  rt_s2)

    acc_per_stage = stage_mean_group(acc_stage_learn)["mean"]
    rt_per_stage  = stage_mean_group(rt_stage_learn)["mean"]

    results = {
        "learning_accuracy_stage1": float(acc_per_stage.get("LS1", np.nan)),
        "learning_accuracy_stage4": float(acc_per_stage.get("LS4", np.nan)),
        "learning_rt_stage1_ms":    float(rt_per_stage.get("LS1", np.nan)),
        "learning_rt_stage4_ms":    float(rt_per_stage.get("LS4", np.nan)),
        "acc_icc":                  float(acc_icc),
        "rt_icc":                   float(rt_icc),
    }

    print(f"─── ICC inputs ─────────────────────────────────────────────────")
    print(f"  accuracy paired (subject × stage) rows: {acc_n}")
    print(f"  RT       paired (subject × stage) rows: {rt_n}")
    print(f"  (paper used 20 subjects × 4 stages = 80; F(159, …) df)")
    print()

    print("─── Scorecard vs. Abdelmotaleb et al. 2025 ─────────────────────")
    print(f"{'metric':<30} {'observed':>12} {'expected':>12}  {'note'}")
    for key, (target, tol, note) in _EXPECTED.items():
        obs = results[key]
        print(f"{key:<30} {obs:>12.3f} {target:>12.3f} {_flag(obs,target,tol)} {note}")
    print()
    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Verify rebuilt OLM bids_data/")
    p.add_argument("bids_root", help="Path to bids_data/ root.")
    args = p.parse_args()
    report(args.bids_root)
