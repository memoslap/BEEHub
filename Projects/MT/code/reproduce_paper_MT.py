#!/usr/bin/env python3
"""
reproduce_paper_MT.py — recompute the preprint's error-rate and RT numbers from the
BIDS derivatives and print them beside the published values.

    python reproduce_paper_MT.py
    python reproduce_paper_MT.py --post-window-compare   # both settings side by side

READ-ONLY. Prints a comparison table; writes nothing.

Purpose
-------
The R pipeline's output (`go_nogo_scored_final.xlsx`) is not in the repository —
it lives on the PI's Windows drive — so the Python port of `1__compute_stopping.R`
cannot be validated against it directly. The preprint's reported numbers are the
next best reference, and arguably a better one: agreeing with them validates the
whole chain (conversion -> stopping -> scoring), not just one step.

Disagreement is a finding, not a failure. Report the delta rather than tuning
parameters until the numbers match.

Analysis definition, from `2__ER_RT.R` plus the paper's Methods
--------------------------------------------------------------
* Mixed blocks only. `block_type == "go_nogo"` — eight blocks of 60 trials per
  session. This filter is NOT in the R script, because its input
  (`go_nogo_compiledData.csv`, 23,040 rows = 48 sessions x 480 trials) was
  already restricted to those blocks upstream. Working from the BIDS files, the
  filter has to be applied here.
* Practice excluded. Implied by the block filter, applied explicitly anyway.
* `subject_id != 25` — both R scripts hardcode this. The paper describes one
  participant excluded for 49% go accuracy in session 1.
* Participants without both sessions excluded (subjects 2 and 4). The paper
  analyses 23 of 26.
* error = 1 - accuracy, averaged per participant x session x trial_type.
* RT on correct trials with finite `rt_combined > 0`, then cell-wise
  (participant x session x trial_type) removal of values beyond +/- 2.5 SD.
* ICC(3,1), two-way mixed, consistency, single measurement.

Published targets (Mahesan et al. 2026, bioRxiv 10.64898/2026.05.06.722889)
---------------------------------------------------------------------------
    N analysed             23
    RT outliers removed    2.1%
    Error rate  go          4%      no-go   12%
    RT          go        582 ms    no-go  445 ms
    ICC error   go        .75 [.50, .89]    no-go  .59 [.25, .81]
    ICC RT      go        .85 [.67, .93]    no-go  .79 [.57, .91]

ICC(3,1) is implemented here from the two-way ANOVA mean squares rather than
taken from a library, so that the formula is visible and checkable:

    ICC(3,1) = (MSR - MSE) / (MSR + (k-1) * MSE)

with MSR the between-subjects mean square, MSE the residual mean square, and
k the number of sessions. The CI uses the F distribution as in McGraw & Wong
(1996). Cross-check against R's `irr::icc(model="twoway", type="consistency",
unit="single")` before publishing anything.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

EXCLUDE_SUBJECTS = {25}          # hardcoded in both R scripts
ANALYSED_BLOCK_TYPE = "go_nogo"
SD_CUTOFF = 2.5

PUBLISHED = {
    "n": 23,
    "outlier_pct": 2.1,
    "er": {"go": 0.04, "nogo": 0.12},
    "rt_ms": {"go": 582.0, "nogo": 445.0},
    "icc_er": {"go": (0.75, 0.50, 0.89), "nogo": (0.59, 0.25, 0.81)},
    "icc_rt": {"go": (0.85, 0.67, 0.93), "nogo": (0.79, 0.57, 0.91)},
    # Kinematics: paper section 3.2. Outlier removal 2.4 / 1.5 / 2.3 %.
    "kin": {
        "path_length":       {"go": 598.0, "nogo": 542.0, "pct": 2.4,
                              "icc": {"go": (0.78, 0.55, 0.90), "nogo": (0.83, 0.65, 0.93)}},
        "mean_velocity":     {"go": 1091.0, "nogo": 934.0, "pct": 1.5,
                              "icc": {"go": (0.83, 0.64, 0.92), "nogo": (0.72, 0.44, 0.87)}},
        "mean_acceleration": {"go": 25884.0, "nogo": 22264.0, "pct": 2.3,
                              "icc": {"go": (0.77, 0.53, 0.90), "nogo": (0.70, 0.41, 0.86)}},
    },
}


def icc31(m: np.ndarray) -> tuple[float, float, float, int]:
    """ICC(3,1) with a 95% CI. `m` is subjects x sessions, complete cases only."""
    m = m[~np.isnan(m).any(axis=1)]
    n, k = m.shape
    if n < 3:
        return float("nan"), float("nan"), float("nan"), n
    grand = m.mean()
    msr = k * ((m.mean(axis=1) - grand) ** 2).sum() / (n - 1)          # between subjects
    msc = n * ((m.mean(axis=0) - grand) ** 2).sum() / (k - 1)          # between sessions
    sst = ((m - grand) ** 2).sum()
    mse = (sst - msr * (n - 1) - msc * (k - 1)) / ((n - 1) * (k - 1))  # residual
    if msr + (k - 1) * mse == 0:
        return float("nan"), float("nan"), float("nan"), n
    est = (msr - mse) / (msr + (k - 1) * mse)
    f = msr / mse if mse > 0 else np.inf
    fl = f / stats.f.ppf(0.975, n - 1, (n - 1) * (k - 1))
    fu = f * stats.f.ppf(0.975, (n - 1) * (k - 1), n - 1)
    return est, (fl - 1) / (fl + k - 1), (fu - 1) / (fu + k - 1), n


def load(deriv: Path) -> list[dict]:
    rows = []
    for f in sorted(deriv.rglob("sub-*_desc-*_beh.tsv")):
        parts = f.name.split("_")
        sub = int(parts[0][4:])
        ses = parts[1][4:]
        with f.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                r["_sub"], r["_ses"] = sub, ses
                rows.append(r)
    return rows


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


def analyse(rows: list[dict], verbose: bool = True) -> dict:
    total = len(rows)
    if "block_type" not in (rows[0] if rows else {}):
        print("  ! derivatives carry no block_type column — regenerate with the "
              "current convert_MT.py, otherwise practice and go-only blocks are "
              "silently included and every number below will be wrong.")
        return {}

    rows = [r for r in rows if r.get("block_type") == ANALYSED_BLOCK_TYPE]
    rows = [r for r in rows if r["_sub"] not in EXCLUDE_SUBJECTS]

    sessions = defaultdict(set)
    for r in rows:
        sessions[r["_sub"]].add(r["_ses"])
    complete = {s for s, v in sessions.items() if len(v) >= 2}
    dropped_incomplete = sorted(set(sessions) - complete)
    rows = [r for r in rows if r["_sub"] in complete]

    if verbose:
        print(f"  trials total            : {total}")
        print(f"  after block/subject filt: {len(rows)}")
        print(f"  subjects analysed       : {len(complete)}   "
              f"(published: {PUBLISHED['n']})")
        if dropped_incomplete:
            print(f"  dropped, single session : {dropped_incomplete}")
        print(f"  excluded by rule        : {sorted(EXCLUDE_SUBJECTS)}")

    # ---- error rate ------------------------------------------------------
    er_cell: dict = defaultdict(list)
    for r in rows:
        a = num(r["accuracy"])
        if not np.isnan(a):
            er_cell[(r["_sub"], r["_ses"], r["trial_type"])].append(1.0 - a)
    er = {k: float(np.mean(v)) for k, v in er_cell.items()}

    # ---- RT: correct trials, rt > 0, then cell-wise +/-2.5 SD ------------
    rt_cell: dict = defaultdict(list)
    for r in rows:
        if num(r["accuracy"]) == 1.0:
            t = num(r["rt_combined"])
            if np.isfinite(t) and t > 0:
                rt_cell[(r["_sub"], r["_ses"], r["trial_type"])].append(t)

    kept, removed = defaultdict(list), 0
    for k, v in rt_cell.items():
        a = np.asarray(v)
        mu, sd = a.mean(), a.std(ddof=1) if a.size > 1 else 0.0
        keep = a if sd == 0 else a[(a >= mu - SD_CUTOFF * sd) & (a <= mu + SD_CUTOFF * sd)]
        removed += a.size - keep.size
        kept[k] = keep
    n_rt = sum(len(v) for v in rt_cell.values())
    pct_out = 100 * removed / n_rt if n_rt else float("nan")
    rt = {k: float(np.mean(v)) for k, v in kept.items() if len(v)}

    if verbose:
        print(f"  RT trials               : {n_rt}")
        print(f"  RT outliers removed     : {removed} ({pct_out:.2f}%)   "
              f"(published: {PUBLISHED['outlier_pct']}%)")

    def matrix(d, tt):
        subs = sorted(complete)
        return np.array([[d.get((s, "01", tt), np.nan),
                          d.get((s, "02", tt), np.nan)] for s in subs])

    out = {"n": len(complete), "pct_out": pct_out}
    for tt in ("go", "nogo"):
        out[f"er_{tt}"] = float(np.nanmean(matrix(er, tt)))
        out[f"rt_{tt}"] = float(np.nanmean(matrix(rt, tt))) * 1000.0
        out[f"icc_er_{tt}"] = icc31(matrix(er, tt))
        out[f"icc_rt_{tt}"] = icc31(matrix(rt, tt))
    return out


def report(res: dict) -> None:
    if not res:
        return
    print(f"\n  {'measure':<26}{'recomputed':>14}{'published':>14}{'delta':>12}")
    print("  " + "-" * 66)

    def line(label, got, want, fmt="{:.3f}", scale=1.0):
        if got is None or not np.isfinite(got):
            print(f"  {label:<26}{'n/a':>14}{fmt.format(want):>14}{'':>12}")
            return
        d = got - want
        print(f"  {label:<26}{fmt.format(got):>14}{fmt.format(want):>14}"
              f"{d:>+12.3f}")

    line("N analysed", res["n"], PUBLISHED["n"], "{:.0f}")
    line("RT outliers %", res["pct_out"], PUBLISHED["outlier_pct"], "{:.2f}")
    for tt in ("go", "nogo"):
        line(f"error rate {tt}", res[f"er_{tt}"], PUBLISHED["er"][tt])
    for tt in ("go", "nogo"):
        line(f"RT {tt} (ms)", res[f"rt_{tt}"], PUBLISHED["rt_ms"][tt], "{:.1f}")
    print()
    for key, pub in (("icc_er", "icc_er"), ("icc_rt", "icc_rt")):
        for tt in ("go", "nogo"):
            est, lo, hi, n = res[f"{key}_{tt}"]
            p, pl, ph = PUBLISHED[pub][tt]
            label = f"ICC {key[4:]} {tt}"
            if np.isfinite(est):
                print(f"  {label:<26}{est:>8.2f} [{lo:.2f},{hi:.2f}]"
                      f"{p:>7.2f} [{pl:.2f},{ph:.2f}]{est - p:>+12.2f}")
            else:
                print(f"  {label:<26}{'n/a (n=' + str(n) + ')':>14}"
                      f"{p:>7.2f} [{pl:.2f},{ph:.2f}]")


def analyse_kinematics(deriv: Path) -> dict:
    """Per-metric cell-wise +/-2.5 SD trimming, exactly as R trim_outliers does:
    the trimming is redone independently for each metric, so the trials entering
    path_length are not the same set as those entering mean_velocity."""
    rows = []
    for f in sorted(deriv.rglob("sub-*_desc-kinematics_beh.tsv")):
        parts = f.name.split("_")
        sub, ses = int(parts[0][4:]), parts[1][4:]
        with f.open(newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                r["_sub"], r["_ses"] = sub, ses
                rows.append(r)
    if not rows:
        return {}

    rows = [r for r in rows if r.get("block_type") == ANALYSED_BLOCK_TYPE
            and r["_sub"] not in EXCLUDE_SUBJECTS]
    ses_of = defaultdict(set)
    for r in rows:
        ses_of[r["_sub"]].add(r["_ses"])
    complete = sorted({s for s, v in ses_of.items() if len(v) >= 2})
    rows = [r for r in rows if r["_sub"] in complete]

    out = {"n": len(complete)}
    for metric, pub in PUBLISHED["kin"].items():
        cell = defaultdict(list)
        for r in rows:
            v = num(r.get(metric))
            if np.isfinite(v):
                cell[(r["_sub"], r["_ses"], r["trial_type"])].append(v)
        kept, before, removed = {}, 0, 0
        for k, vals in cell.items():
            a = np.asarray(vals)
            before += a.size
            sd = a.std(ddof=1) if a.size > 1 else 0.0
            k2 = a if not (np.isfinite(sd) and sd > 0) else a[np.abs(a - a.mean()) <= SD_CUTOFF * sd]
            removed += a.size - k2.size
            kept[k] = k2
        means = {k: float(np.mean(v)) for k, v in kept.items() if len(v)}
        res = {"pct": 100 * removed / before if before else float("nan")}
        for tt in ("go", "nogo"):
            m = np.array([[means.get((s, "01", tt), np.nan),
                           means.get((s, "02", tt), np.nan)] for s in complete])
            res[tt] = float(np.nanmean(m))
            res[f"icc_{tt}"] = icc31(m)
        out[metric] = res
    return out


def report_kinematics(res: dict) -> None:
    if not res:
        print("\n  No kinematics derivative found. Run:")
        print("    python convert_MT.py --stage kinematics --apply")
        return
    print(f"\n  KINEMATICS (n={res['n']})")
    print(f"  {'measure':<26}{'recomputed':>14}{'published':>14}{'delta':>12}")
    print("  " + "-" * 66)
    for metric, pub in PUBLISHED["kin"].items():
        r = res.get(metric)
        if not r:
            continue
        print(f"  {metric + ' outliers %':<26}{r['pct']:>14.2f}{pub['pct']:>14.2f}"
              f"{r['pct'] - pub['pct']:>+12.2f}")
        for tt in ("go", "nogo"):
            print(f"  {metric + ' ' + tt:<26}{r[tt]:>14.1f}{pub[tt]:>14.1f}"
                  f"{r[tt] - pub[tt]:>+12.1f}")
        for tt in ("go", "nogo"):
            est, lo, hi, n = r[f"icc_{tt}"]
            p, pl, ph = pub["icc"][tt]
            lbl = f"ICC {metric} {tt}"
            if np.isfinite(est):
                print(f"  {lbl:<26}{est:>8.2f} [{lo:.2f},{hi:.2f}]"
                      f"{p:>7.2f} [{pl:.2f},{ph:.2f}]{est - p:>+12.2f}")
            else:
                print(f"  {lbl:<26}{'n/a (n=' + str(n) + ')':>14}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deriv", type=Path, default=None)
    ap.add_argument("--repo", type=Path, default=None)
    args = ap.parse_args()

    if args.deriv:
        deriv = args.deriv
    else:
        repo = (args.repo or Path(__file__).resolve().parent)
        while not (repo / "Projects").is_dir() and repo != repo.parent:
            repo = repo.parent
        deriv = repo / "Projects" / "MT" / "derivatives" / "stopping"
    if not deriv.is_dir():
        print(f"ERROR: {deriv} not found. Run convert_MT.py --apply first.",
              file=sys.stderr)
        return 2

    print(f"derivatives: {deriv}\n")
    rows = load(deriv)
    if not rows:
        print("No derivative TSVs found.", file=sys.stderr)
        return 2
    report(analyse(rows))
    kin = deriv.parent / "kinematics"
    report_kinematics(analyse_kinematics(kin) if kin.is_dir() else {})
    return 0


if __name__ == "__main__":
    sys.exit(main())
