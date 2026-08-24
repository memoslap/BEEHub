#!/usr/bin/env python3
"""
convert_MT.py — the MT transformation script.

    python convert_MT.py                      # dry run, all stages (DEFAULT)
    python convert_MT.py --apply
    python convert_MT.py --apply --stage bids
    python convert_MT.py --apply --stage derivatives
    python convert_MT.py --apply --stage kinematics

Three stages, deliberately separate:

  STAGE 1  sourcedata/raw/*.csv  ->  bids_data/sub-*/ses-*/beh/*_task-gonogo_beh.tsv
           Projection onto the analysis column set. No values are computed.

  STAGE 2  bids_data/...beh.tsv  ->  derivatives/<desc>/...desc-<desc>_beh.tsv
           Trial-level stopping metrics, ported from 1__compute_stopping.R.

  STAGE 3  bids_data + derivatives/<desc>  ->  derivatives/kinematics/
           Time-weighted trajectory kinematics, ported from 3__Kinematics.R.
           Reads the stopping derivative because the analysis epoch is defined by
           rt_combined: go trials 0 -> rt, no-go trials 0 -> rt + 150 ms.

Why stage 2 does NOT write into the bids_data TSVs
--------------------------------------------------
BIDS requires derivatives of raw data to be kept separate from the raw data, and
there is a practical reason beyond compliance: every number stage 2 produces is a
function of NOGO_CONFIG (v_thresh, min_still_sec, post_still_criterion, ...).
Merged into the raw file, you could never re-run with a different threshold, and
nothing would record which threshold produced the numbers sitting in the file.
The R script exists precisely because an earlier authoritative accuracy column
turned out to be wrong; baking in a second one invites the same failure. Stage 2
therefore writes a parallel tree, and the parameters go into its
dataset_description.json. A re-run with different settings becomes a second
`desc-` label rather than an overwrite.

Join key
--------
Stage 1 writes a `trial_index` column (1-based, after non-trial rows are removed).
It is the ONLY reliable key: block_number has 15 distinct values across 606
trials, trials_count is a per-block constant, and block_number+trials_count+digit
reaches only 108 distinct combinations. Stage 2 carries trial_index through, so a
derivative row can always be traced to its source row without relying on order.

Fidelity to the R script
------------------------
Ported behaviour-for-behaviour, including its quirks. Two are worth naming:

1. `compute_nogo_stop`'s comment says the post-stop check validates the period
   AFTER the detected stop. The code does `tail(v, n_post)` — the last n_post
   samples of the TRIAL.

   **`--post-window trial` is the DEFAULT**, because the goal is to reproduce
   the published numbers and the published numbers came from the R *code*.
   `--post-window after-stop` implements the comment instead. The difference
   between the two is not noise to be suppressed: it IS the finding. On
   sub-001_ses-01 it moves no-go accuracy from 0.980 to 0.940, flipping 6 of
   100 no-go trials. Run both and report the delta.

2. `align_to_n` repeats a length-1 vector rather than discarding it, and pads
   button vectors with 0 but coordinates with NaN. Preserved exactly.

Verify a port before trusting it: run the R script and this script on the same
input and compare `accuracy` and `rt_combined` trial by trial. I have not been
able to do that here, so treat stage 2 as unvalidated until you have.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Configuration — mirrors the R script's BOX_CONFIG / NOGO_CONFIG
# ---------------------------------------------------------------------------
BOX_CONFIG = {
    "x_min": 150.0, "x_max": 250.0,
    "y_min": 250.0, "y_max": 350.0,
    "include_boundary": False,        # strict > and <, as in the R script
}

NOGO_CONFIG = {
    "v_thresh": 10.0,                 # pixels/sec below which a sample is "still"
    "min_still_sec": 0.15,
    "post_still_sec": 0.25,
    "deadline_sec": 1.5,
    "dist_thresh_no_move": 5.0,       # pixels
    "post_still_criterion": 0.9,
}

# The no-go kinematics epoch runs to 150 ms after the detected stop — the paper's
# "stabilised epoch", which ensures the full braking phase is captured.
# CAUTION: 3__Kinematics.R declares its own POST_STILL_SEC <- 0.150, which is NOT
# the same quantity as 1__compute_stopping.R's post_still_sec = 0.25 despite the
# near-identical name. The stopping value sizes the post-stop stillness CHECK; this
# one sizes the kinematics WINDOW. Using 0.25 here inflates every no-go duration by
# 100 ms and depresses no-go velocity and acceleration by ~15%.
KIN_EPOCH_TAIL_SEC = 0.150

TASK = "gonogo"
DESC = "stopping"

KEPT_COLUMNS = [
    "block_number", "block_type", "is_practice",
    "trials_count", "digit", "trial_type", "correct_response",
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.leftButton",
    "mouse_resp.midButton", "mouse_resp.rightButton", "mouse_resp.time",
    "click_pos_x", "click_pos_y", "iti_duration", "participant",
]
TRIAL_MARKER_COLUMN = "trial_type"
MULTI_VALUE_COLUMNS = {
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.time",
    "mouse_resp.leftButton", "mouse_resp.midButton", "mouse_resp.rightButton",
}
# ---------------------------------------------------------------------------
# Curation policy — which participants belong in this dataset at all.
# ---------------------------------------------------------------------------
# BEEHub curates FINALISED datasets: what the published analysis actually used,
# not everything that was ever collected. That is a deliberate departure from the
# usual BIDS convention, where a raw dataset records all collected data and
# exclusions live only in participants.tsv.
#
# The policy has to be enforced HERE, because sourcedata/raw still contains all
# 50 raw CSVs. Deleting subject directories by hand does not hold: the next
# `--stage bids --apply` would silently recreate them.
#
# Pass --include-excluded to build the complete collected dataset instead.
EXCLUDED_SUBJECTS: dict[int, str] = {
    2:  "no second session — cannot enter a test-retest analysis",
    4:  "no second session — cannot enter a test-retest analysis",
    25: "excluded from the published analysis: 49% go accuracy in ses-01; "
        "hardcoded as subject_id != 25 in 1__compute_stopping.R and 2__ER_RT.R",
}

RAW_MARKER = "_go_nogo_dm_"
NA = "n/a"

# Stage 4 — per-outcome files for the overview generator.
# id -> (column name in the emitted file, source, source column)
OUTCOME_SPEC = {
    "ACCBIN":   ("accuracy_binary",   "stop", "accuracy"),
    "RT":       ("response_time_ms",  "stop", "rt_combined"),
    "PATHLEN":  ("path_length",       "kin",  "path_length"),
    "VELOCITY": ("mean_velocity",     "kin",  "mean_velocity"),
    "ACCEL":    ("mean_acceleration", "kin",  "mean_acceleration"),
}

KIN_COLUMNS = [
    "trial_index", "trial_type", "block_number", "block_type", "is_practice",
    "kin_parse_failed", "kin_n_samples", "duration", "path_length",
    "max_velocity", "mean_velocity", "max_acceleration", "mean_acceleration",
]

DERIVED_COLUMNS = [
    "trial_index", "trial_type", "block_number", "block_type", "is_practice",
    "n_left_clicks", "go_first_left_inside", "go_first_left_rt",
    "parse_failed_time", "parse_failed_xy", "parse_failed_buttons",
    "mismatched_lengths", "any_rb_nonzero", "any_mb_nonzero",
    "any_click", "any_left", "any_right",
    "nogo_stop_time", "nogo_stopped", "nogo_outcome", "nogo_parse_failed",
    "rt_combined", "accuracy",
]

log = logging.getLogger("convert_MT")


def raise_field_size_limit() -> int:
    """Lift csv's 128 KB field cap; raw rows carry whole trajectories per cell."""
    limit = sys.maxsize
    while True:
        try:
            csv.field_size_limit(limit)
            return limit
        except OverflowError:
            limit //= 2


# ===========================================================================
# Ported utilities (R: section 2)
# ===========================================================================
def safe_parse_vec(s: str | None) -> tuple[np.ndarray, bool]:
    """R safe_parse_vec: returns (vec, parse_failed). Empty/NA/bad JSON -> failed."""
    if s is None:
        return np.empty(0), True
    s = s.strip()
    if s == "" or s == NA:
        return np.empty(0), True
    try:
        obj = json.loads(s)
    except (ValueError, TypeError):
        return np.empty(0), True
    if not isinstance(obj, list):
        obj = [obj]
    out = np.empty(len(obj), dtype=float)
    for i, v in enumerate(obj):
        try:
            out[i] = float(v)
        except (TypeError, ValueError):
            out[i] = np.nan          # R: as.numeric() with a warning -> NA
    return out, False


def align_to_n(v: np.ndarray, n: int, pad: float = np.nan) -> np.ndarray:
    """R align_to_n. A length-1 vector is REPEATED, not discarded."""
    if v.size == 0:
        return np.full(n, pad, dtype=float)
    if v.size == n:
        return v
    if v.size == 1 and n > 1:
        return np.full(n, v[0], dtype=float)
    if v.size > n:
        return v[:n]
    return np.concatenate([v, np.full(n - v.size, pad, dtype=float)])


def inside_box(x: np.ndarray, y: np.ndarray, box: dict) -> np.ndarray:
    if box["include_boundary"]:
        return ((x >= box["x_min"]) & (x <= box["x_max"])
                & (y >= box["y_min"]) & (y <= box["y_max"]))
    return ((x > box["x_min"]) & (x < box["x_max"])
            & (y > box["y_min"]) & (y < box["y_max"]))


def interp_xy(t: np.ndarray, x: np.ndarray, y: np.ndarray,
              tq: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """R interp_xy via approx(rule = 1): NA outside the data range, no extrapolation."""
    ok = np.isfinite(t) & np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 2:
        return np.full(tq.shape, np.nan), np.full(tq.shape, np.nan)
    to, xo, yo = t[ok], x[ok], y[ok]
    order = np.argsort(to, kind="stable")
    to, xo, yo = to[order], xo[order], yo[order]
    xi = np.interp(tq, to, xo)
    yi = np.interp(tq, to, yo)
    # rule = 1: outside the range is NA, not the nearest endpoint.
    outside = (tq < to[0]) | (tq > to[-1])
    xi = np.where(outside, np.nan, xi)
    yi = np.where(outside, np.nan, yi)
    return xi, yi


# ===========================================================================
# Ported core (R: section 3)
# ===========================================================================
def extract_left_clicks(x_s, y_s, t_s, lb_s, rb_s, mb_s, box) -> dict:
    px, px_f = safe_parse_vec(x_s)
    py, py_f = safe_parse_vec(y_s)
    pt, pt_f = safe_parse_vec(t_s)
    plb, plb_f = safe_parse_vec(lb_s)
    prb, prb_f = safe_parse_vec(rb_s)
    pmb, pmb_f = safe_parse_vec(mb_s)

    qc = {
        "parse_failed_time": pt_f,
        "parse_failed_xy": px_f or py_f,
        "parse_failed_buttons": plb_f or prb_f or pmb_f,
    }
    lens = [v.size for v, f in
            ((px, px_f), (py, py_f), (pt, pt_f), (plb, plb_f), (prb, prb_f), (pmb, pmb_f))
            if not f]
    qc["mismatched_lengths"] = bool(lens) and len(set(lens)) > 1 and (max(lens) - min(lens)) > 1

    if qc["parse_failed_time"] or pt.size < 2:
        qc["any_rb_nonzero"] = None
        qc["any_mb_nonzero"] = None
        return {"clicks": [], "qc": qc}

    nT = pt.size
    t = pt
    x = align_to_n(px, nT, np.nan)
    y = align_to_n(py, nT, np.nan)
    lb = align_to_n(plb, nT, 0.0)
    rb = align_to_n(prb, nT, 0.0)
    mb = align_to_n(pmb, nT, 0.0)

    t_rel = t - t[0]

    lb_down = lb > 0
    prev = np.concatenate([[False], lb_down[:-1]])     # R lag(default = FALSE)
    onsets = np.flatnonzero(lb_down & ~prev)

    qc["any_rb_nonzero"] = bool(np.any(rb > 0))
    qc["any_mb_nonzero"] = bool(np.any(mb > 0))

    if onsets.size == 0:
        return {"clicks": [], "qc": qc}

    t_click = t_rel[onsets]
    xi, yi = interp_xy(t_rel, x, y, t_click)
    ins = inside_box(xi, yi, box)

    keep = np.isfinite(t_click) & np.isfinite(xi) & np.isfinite(yi)
    clicks = [{"rt": float(a), "x": float(b), "y": float(c), "inside": bool(d)}
              for a, b, c, d in zip(t_click[keep], xi[keep], yi[keep], ins[keep])]
    return {"clicks": clicks, "qc": qc}


def compute_any_click(lb_s, rb_s, mb_s) -> dict:
    plb, plb_f = safe_parse_vec(lb_s)
    prb, prb_f = safe_parse_vec(rb_s)
    pmb, pmb_f = safe_parse_vec(mb_s)
    failed = plb_f or prb_f or pmb_f
    if failed:
        # R returns NA, not FALSE: a corrupt trial must not score as "no click".
        return {"parse_failed_buttons": True, "any_click": None,
                "any_left": None, "any_right": None}
    any_l = bool(np.any(plb > 0))
    any_r = bool(np.any(prb > 0))
    any_m = bool(np.any(pmb > 0))
    return {"parse_failed_buttons": False, "any_click": any_l or any_r or any_m,
            "any_left": any_l, "any_right": any_r}


def compute_nogo_stop(x_s, y_s, t_s, cfg, post_window: str = "trial") -> dict:
    def out(st, stopped, outcome, pf):
        return {"stop_time": st, "stopped": stopped, "outcome": outcome,
                "parse_failed": pf}

    pt, pt_f = safe_parse_vec(t_s)
    px, px_f = safe_parse_vec(x_s)
    py, py_f = safe_parse_vec(y_s)

    if pt_f or pt.size < 3:
        return out(None, False, "too_short_or_bad_time", True)

    nT = pt.size
    t = pt
    x = align_to_n(px, nT, np.nan)
    y = align_to_n(py, nT, np.nan)

    valid = np.isfinite(x) & np.isfinite(y)
    if valid.sum() < 3:
        return out(None, False, "missing_xy", px_f or py_f)

    last = int(np.flatnonzero(valid)[-1])          # R: max(which(valid)), 1-based
    x, y, t = x[:last + 1], y[:last + 1], t[:last + 1]
    t_rel = t - t[0]

    dt = np.diff(t_rel)
    dt = np.where(dt <= 0, np.nan, dt)
    with np.errstate(invalid="ignore"):
        sample_dt = float(np.nanmedian(dt)) if np.any(np.isfinite(dt)) else np.nan
    if not math.isfinite(sample_dt) or sample_dt <= 0:
        return out(None, False, "bad_sampling_rate", True)

    with np.errstate(invalid="ignore", divide="ignore"):
        v_raw = np.sqrt(np.diff(x) ** 2 + np.diff(y) ** 2) / dt
    v_raw = np.where(np.isfinite(v_raw), v_raw, np.nan)
    v = np.concatenate([[np.nan], v_raw])          # R pads at the START

    full_like_deadline = (math.isfinite(float(np.max(t_rel)))
                          and float(np.max(t_rel)) >= cfg["deadline_sec"] - 2 * sample_dt)

    max_v = float(np.nanmax(v_raw)) if np.any(np.isfinite(v_raw)) else math.inf
    dist = np.sqrt((x - x[0]) ** 2 + (y - y[0]) ** 2)
    max_dist = float(np.nanmax(dist)) if np.any(np.isfinite(dist)) else math.inf

    if max_v < cfg["v_thresh"] and max_dist < cfg["dist_thresh_no_move"]:
        return out(0.0, True,
                   "no_movement_full_duration" if full_like_deadline else "no_movement_early",
                   False)

    if not np.any(np.isfinite(v_raw)):
        return out(None, False, "velocity_all_na", True)

    peak_r = int(np.argmax(np.where(np.isfinite(v), v, -np.inf))) + 1     # 1-based
    n_still = math.ceil(cfg["min_still_sec"] / sample_dt)

    if len(v) - n_still + 1 <= peak_r + 1:
        return out(None, False, "too_short_after_peak", False)

    stop_idx_r = None
    for i in range(peak_r + 1, len(v) - n_still + 2):        # R's inclusive range
        w = v[i - 1: i - 1 + n_still]
        fin = np.isfinite(w)
        if fin.sum() >= n_still * 0.5 and np.all(w[fin] < cfg["v_thresh"]):
            stop_idx_r = i
            break

    if stop_idx_r is None:
        return out(None, False,
                   "no_stop_timeout" if full_like_deadline else "no_stop_early", False)

    stop_time = float(t_rel[stop_idx_r - 1])
    n_post = math.ceil(cfg["post_still_sec"] / sample_dt)

    if post_window == "after-stop":
        v_post = v[stop_idx_r - 1: stop_idx_r - 1 + n_post]
    else:
        v_post = v[-min(len(v), n_post):]                    # R: tail(v, n_post)

    fin = v_post[np.isfinite(v_post)]
    post_ok = bool(fin.size) and float(np.mean(fin < cfg["v_thresh"])) >= cfg["post_still_criterion"]

    if post_ok:
        return out(stop_time, True,
                   "stopped_near_deadline" if full_like_deadline else "stopped_early", False)
    return out(None, False,
               "no_stop_timeout" if full_like_deadline else "no_stop_early", False)


def score_trial(row: dict, post_window: str) -> dict:
    left = extract_left_clicks(row["mouse_resp.x"], row["mouse_resp.y"],
                               row["mouse_resp.time"], row["mouse_resp.leftButton"],
                               row["mouse_resp.rightButton"], row["mouse_resp.midButton"],
                               BOX_CONFIG)
    ci = compute_any_click(row["mouse_resp.leftButton"], row["mouse_resp.rightButton"],
                           row["mouse_resp.midButton"])
    st = compute_nogo_stop(row["mouse_resp.x"], row["mouse_resp.y"],
                           row["mouse_resp.time"], NOGO_CONFIG, post_window)

    clicks = left["clicks"]
    n_left = len(clicks)
    first_inside = bool(n_left > 0 and clicks[0]["inside"])
    first_rt = clicks[0]["rt"] if n_left > 0 else None
    qc = left["qc"]

    m = {
        "n_left_clicks": n_left,
        "go_first_left_inside": first_inside,
        "go_first_left_rt": first_rt,
        "parse_failed_time": qc["parse_failed_time"],
        "parse_failed_xy": qc["parse_failed_xy"],
        "parse_failed_buttons": qc["parse_failed_buttons"],
        "mismatched_lengths": qc["mismatched_lengths"],
        "any_rb_nonzero": qc.get("any_rb_nonzero"),
        "any_mb_nonzero": qc.get("any_mb_nonzero"),
        "any_click": ci["any_click"],
        "any_left": ci["any_left"],
        "any_right": ci["any_right"],
        "nogo_stop_time": st["stop_time"],
        "nogo_stopped": st["stopped"],
        "nogo_outcome": st["outcome"],
        "nogo_parse_failed": bool(st["parse_failed"] or ci["parse_failed_buttons"]),
    }

    tt = row.get("trial_type")
    no_move = m["nogo_outcome"] in ("no_movement_full_duration", "no_movement_early")

    if tt == "go" and m["go_first_left_inside"]:
        rt = m["go_first_left_rt"]
    elif (tt == "nogo" and m["nogo_stopped"]
          and m["any_click"] is not None and not m["any_click"]):
        rt = 0.0 if no_move else m["nogo_stop_time"]
    else:
        rt = None
    m["rt_combined"] = rt

    if tt == "go":
        if m["parse_failed_time"] or m["parse_failed_xy"] or m["parse_failed_buttons"]:
            acc = None
        else:
            acc = int(bool(m["go_first_left_inside"] and m["n_left_clicks"] == 1
                           and not m["any_rb_nonzero"] and not m["any_mb_nonzero"]))
    elif tt == "nogo":
        acc = None if (m["nogo_parse_failed"] or m["any_click"] is None) \
            else int(bool(m["nogo_stopped"] and not m["any_click"]))
    else:
        acc = None
    m["accuracy"] = acc
    return m


# ===========================================================================
# Ported from 3__Kinematics.R
# ===========================================================================
def align_to_n_strict(v: np.ndarray, n: int) -> np.ndarray:
    """R align_to_n_strict. NOTE: unlike align_to_n in the stopping script, a
    length-1 vector is NOT repeated — it is padded with NaN. The two scripts
    genuinely differ here; both are reproduced as written."""
    if v.size == 0:
        return np.full(n, np.nan)
    if v.size >= n:
        return v[:n]
    return np.concatenate([v, np.full(n - v.size, np.nan)])


def compute_kinematics(x_s, y_s, t_s, end_time: float) -> dict:
    """R compute_kinematics. Time-weighted means, as in the paper's Methods."""
    def empty(failed: bool, n: int = 0) -> dict:
        return {"kin_parse_failed": failed, "kin_n_samples": n,
                "duration": None, "path_length": None, "max_velocity": None,
                "mean_velocity": None, "max_acceleration": None,
                "mean_acceleration": None}

    px, px_f = safe_parse_vec(x_s)
    py, py_f = safe_parse_vec(y_s)
    pt, pt_f = safe_parse_vec(t_s)
    if px_f or py_f or pt_f or pt.size < 3:
        return empty(True)

    nT = pt.size
    x = align_to_n_strict(px, nT)
    y = align_to_n_strict(py, nT)
    t_rel = pt - pt[0]

    keep = np.flatnonzero(t_rel <= end_time)      # analysis window
    if keep.size < 3:
        return empty(False, int(keep.size))
    x, y, t_rel = x[keep], y[keep], t_rel[keep]

    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(t_rel)
    x, y, t_rel = x[ok], y[ok], t_rel[ok]
    if t_rel.size < 3:
        return empty(False, int(t_rel.size))

    # R duplicated(): keep first occurrence of each timestamp.
    _, first = np.unique(t_rel, return_index=True)
    idx = np.sort(first)
    x2, y2, t2 = x[idx], y[idx], t_rel[idx]
    if t2.size < 3 or np.any(np.diff(t2) <= 0):
        return empty(False, int(t2.size))

    dx, dy, dt = np.diff(x2), np.diff(y2), np.diff(t2)
    ds = np.sqrt(dx ** 2 + dy ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        v = ds / dt

    duration = float(t2[-1] - t2[0])
    path_len = float(np.sum(ds))
    mean_v = path_len / duration if math.isfinite(duration) and duration > 0 else None
    max_v = float(np.max(v[np.isfinite(v)])) if np.any(np.isfinite(v)) else None

    mean_a = max_a = None
    if v.size >= 2:
        dv = np.diff(v)
        dt_a = dt[1:]                              # R: dt[-1], the LATTER intervals
        with np.errstate(divide="ignore", invalid="ignore"):
            a = dv / dt_a
        ok_a = np.isfinite(a) & np.isfinite(dt_a) & (dt_a > 0)
        if ok_a.sum() > 0:
            mean_a = float(np.sum(np.abs(a[ok_a]) * dt_a[ok_a]) / np.sum(dt_a[ok_a]))
        fin = np.isfinite(a)
        if fin.any():
            max_a = float(np.max(np.abs(a[fin])))

    return {"kin_parse_failed": False, "kin_n_samples": int(t2.size),
            "duration": duration, "path_length": path_len,
            "max_velocity": max_v, "mean_velocity": mean_v,
            "max_acceleration": max_a, "mean_acceleration": mean_a}


# ===========================================================================
# Stage 1 — raw CSV -> BIDS TSV
# ===========================================================================
def read_header(p: Path) -> list[str]:
    with p.open(newline="", encoding="utf-8-sig") as fh:
        return next(csv.reader(fh))


def stage1(repo: Path, apply: bool, trial_index: bool,
           include_excluded: bool = False) -> int:
    raw_dir = repo / "Projects" / "MT" / "sourcedata" / "raw"
    bids = repo / "Projects" / "MT" / "bids_data"
    if not raw_dir.is_dir():
        log.error("Source not found: %s", raw_dir)
        return 1

    files = sorted(p for p in raw_dir.glob("*.csv") if RAW_MARKER in p.name)
    skipped = sorted(p.name for p in raw_dir.glob("*.csv") if RAW_MARKER not in p.name)
    log.info("STAGE 1: %d raw CSVs (skipping %d non-raw: %s)",
             len(files), len(skipped), ", ".join(skipped) or "none")

    # --- curation policy --------------------------------------------------
    if include_excluded:
        log.warning("  --include-excluded: building the COMPLETE collected dataset, "
                    "including sub-%s. This is NOT the curated BEEHub dataset.",
                    ", sub-".join(f"{n:03d}" for n in sorted(EXCLUDED_SUBJECTS)))
    else:
        keep, dropped = [], []
        for f in files:
            n = int(f.name.split("_")[0][:-1])
            (dropped if n in EXCLUDED_SUBJECTS else keep).append((n, f))
        files = [f for _, f in keep]
        if dropped:
            log.info("  curation policy: excluding %d session(s) from %d subject(s)",
                     len(dropped), len({n for n, _ in dropped}))
            for n in sorted({n for n, _ in dropped}):
                log.info("    sub-%03d — %s", n, EXCLUDED_SUBJECTS[n])
            log.info("    raw CSVs stay in sourcedata/raw/; --include-excluded builds them")
        stale = [f"sub-{n:03d}" for n in sorted(EXCLUDED_SUBJECTS)
                 if (bids / f"sub-{n:03d}").is_dir()]
        if stale:
            log.warning("  %s exist(s) under bids_data but are excluded by the current "
                        "policy — left in place, remove by hand if that is intended",
                        ", ".join(stale))

    if not files:
        log.error("No files matching %r", RAW_MARKER)
        return 1

    sets, orders = {}, set()
    for f in files:
        h = read_header(f)
        orders.add(tuple(h))
        sets.setdefault(frozenset(c for c in h if c.strip()), []).append(f.name)
    if len(orders) > 1:
        log.info("  %d column ORDERS — harmless, extraction is by name", len(orders))
    bad = {n[0]: [c for c in KEPT_COLUMNS if c not in s] for s, n in sets.items()
           if any(c not in s for c in KEPT_COLUMNS)}
    if bad:
        log.error("Missing required column(s); aborting, nothing written.")
        for n, miss in bad.items():
            log.error("  e.g. %s lacks %s", n, miss)
        return 1

    all_cols = frozenset().union(*sets)
    dropped = sorted(c for c in all_cols if c not in KEPT_COLUMNS)
    log.info("  keeping %d columns, dropping %d",
             len(KEPT_COLUMNS) + (1 if trial_index else 0), len(dropped))

    totals = []
    for f in files:
        prefix = f.name.split("_")[0]
        sub = f"sub-{int(prefix[:-1]):03d}"
        ses = f"ses-{ {'a': '01', 'b': '02'}[prefix[-1]] }"
        dest = bids / sub / ses / "beh" / f"{sub}_{ses}_task-{TASK}_beh.tsv"

        with f.open(newline="", encoding="utf-8-sig") as fh:
            r = csv.reader(fh)
            header = next(r)
            idx = {c: header.index(c) for c in KEPT_COLUMNS}
            ti = header.index(TRIAL_MARKER_COLUMN)
            rows, n_drop = [], 0
            for raw in r:
                if not any(c.strip() for c in raw):
                    continue
                if ti >= len(raw) or not raw[ti].strip():
                    n_drop += 1
                    continue
                vals = [(raw[idx[c]].strip() if idx[c] < len(raw) else "") for c in KEPT_COLUMNS]
                rows.append([v if v else NA for v in vals])

        out_header = (["trial_index"] if trial_index else []) + KEPT_COLUMNS
        if trial_index:
            rows = [[str(i)] + r_ for i, r_ in enumerate(rows, 1)]

        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter="\t", lineterminator="\n")
                w.writerow(out_header)
                w.writerows(rows)
        log.info("  %s %-42s -> %s (%d trials, %d non-trial rows)",
                 "[WROTE]  " if apply else "[DRY-RUN]", f.name,
                 dest.relative_to(repo), len(rows), n_drop)
        totals.append((sub, ses, len(rows), n_drop))

    sidecar = build_bids_sidecar(dropped, trial_index)
    root = bids / f"task-{TASK}_beh.json"
    if apply:
        bids.mkdir(parents=True, exist_ok=True)
        root.write_text(json.dumps(sidecar, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    log.info("  %s root dictionary -> %s",
             "[WROTE]  " if apply else "[DRY-RUN]", root.relative_to(repo))

    log.info("  files=%d trials=%d non-trial rows removed=%d",
             len(totals), sum(t[2] for t in totals), sum(t[3] for t in totals))
    counts = sorted({t[2] for t in totals})
    if len(counts) > 1:
        log.warning("  trial counts differ across sessions: %s", counts)
    subs = {}
    for sub, ses, *_ in totals:
        subs.setdefault(sub, []).append(ses)
    inc = {s: v for s, v in subs.items() if len(v) < 2}
    if inc:
        log.warning("  single-session subjects (reported, not filled in): %s",
                    ", ".join(f"{s} ({v[0]})" for s, v in sorted(inc.items())))
    return 0


def build_bids_sidecar(dropped: list[str], trial_index: bool) -> dict:
    d: dict = {
        "TaskName": TASK,
        "TaskDescription": (
            "Mouse-tracking go/no-go task. A digit is presented; participants click a "
            "target box on go trials and withhold the movement on no-go trials. The "
            "full mouse trajectory is recorded for every trial."
        ),
    }
    if trial_index:
        d["trial_index"] = {"Description":
            "1-based position of the trial within the session, after non-trial rows "
            "are removed. Generated during conversion; not a source column. It is the "
            "only reliable key for joining derivatives back to this file."}
    desc = {
        "block_number": "Block index within the session, 1-15.",
        "block_type": "Which condition table generated the block. This is the column "
                      "that identifies the analysed subset: the published analysis "
                      "uses go_nogo blocks only.",
        "is_practice": "Whether the block was practice. Needed IN ADDITION to "
                       "block_type, because block 1 is go_only AND practice.",
        "trials_count": "Number of trials in the block. Constant within a block.",
        "digit": "Stimulus digit presented (1-9, excluding 5).",
        "trial_type": "Trial condition.",
        "correct_response": "Response required on this trial.",
        "mouse_resp.x": "Mouse x-position trajectory.",
        "mouse_resp.y": "Mouse y-position trajectory.",
        "mouse_resp.leftButton": "Left mouse button state at each sample.",
        "mouse_resp.midButton": "Middle mouse button state at each sample.",
        "mouse_resp.rightButton": "Right mouse button state at each sample.",
        "mouse_resp.time": "Sample timestamps, seconds. Approximately 60 Hz.",
        "click_pos_x": "Final click x-position. n/a when no click was made.",
        "click_pos_y": "Final click y-position. n/a when no click was made.",
        "iti_duration": "Inter-trial interval.",
        "participant": "Source participant identifier (e.g. '1a'), kept for provenance.",
    }
    units = {"mouse_resp.x": "pixels", "mouse_resp.y": "pixels",
             "mouse_resp.time": "seconds", "click_pos_x": "pixels",
             "click_pos_y": "pixels", "iti_duration": "seconds"}
    levels = {
        "block_type": {
            "go_nogo": "Mixed go/no-go block, 60 trials, 80/20. Eight per session "
                       "(blocks 4, 5, 7, 8, 10, 11, 13, 14). The analysed subset.",
            "go_only": "Go-only block, 18 trials. Six per session (block 1, which is "
                       "practice, plus blocks 3, 6, 9, 12, 15).",
            "go_nogo_prac": "Mixed practice block, 18 trials (block 2)."},
        "is_practice": {"0": "Main experiment", "1": "Practice block"},
        "trial_type": {"go": "Go trial: a click is required.",
                       "nogo": "No-go trial: the response must be withheld."},
        "correct_response": {"click": "A click inside the target box.",
                             "none": "No response."},
    }
    for c in KEPT_COLUMNS:
        e: dict = {"Description": desc[c]}
        if c in units:
            e["Units"] = units[c]
        if c in levels:
            e["Levels"] = levels[c]
        if c in MULTI_VALUE_COLUMNS:
            e["Delimiter"] = ","
        d[c] = e
    d["dropped_columns"] = dropped
    d["dropped_column_count"] = len(dropped)
    return d


# ===========================================================================
# Stage 2 — BIDS TSV -> derivatives
# ===========================================================================
def fmt(v) -> str:
    if v is None:
        return NA
    if isinstance(v, bool):
        return "1" if v else "0"
    if isinstance(v, float):
        return NA if not math.isfinite(v) else f"{v:.6f}"
    return str(v)


def stage2(repo: Path, apply: bool, post_window: str) -> int:
    bids = repo / "Projects" / "MT" / "bids_data"
    deriv = repo / "Projects" / "MT" / "derivatives" / DESC
    srcs = sorted(bids.rglob(f"sub-*_task-{TASK}_beh.tsv"))
    log.info("STAGE 2: %d source TSVs, post_window=%s", len(srcs), post_window)
    if not srcs:
        log.error("No stage-1 output found under %s — run stage 1 first", bids)
        return 1

    n_trials = 0
    outcomes: dict[str, int] = {}
    acc_na = 0
    for src in srcs:
        with src.open(newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        if "trial_index" not in (rows[0] if rows else {}):
            log.warning("  %s has no trial_index column; falling back to row order",
                        src.name)

        out_rows = []
        for i, r in enumerate(rows, 1):
            m = score_trial(r, post_window)
            m["trial_index"] = r.get("trial_index", str(i))
            for c in ("trial_type", "block_number", "block_type", "is_practice"):
                m[c] = r.get(c)
            out_rows.append([fmt(m.get(c)) for c in DERIVED_COLUMNS])
            outcomes[m["nogo_outcome"]] = outcomes.get(m["nogo_outcome"], 0) + 1
            if m["accuracy"] is None:
                acc_na += 1
        n_trials += len(out_rows)

        rel = src.relative_to(bids)
        dest = deriv / rel.parent / rel.name.replace(
            f"_task-{TASK}_beh.tsv", f"_task-{TASK}_desc-{DESC}_beh.tsv")
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter="\t", lineterminator="\n")
                w.writerow(DERIVED_COLUMNS)
                w.writerows(out_rows)
        log.info("  %s %-46s -> %s (%d trials)",
                 "[WROTE]  " if apply else "[DRY-RUN]", src.name,
                 dest.relative_to(repo), len(out_rows))

    if apply:
        deriv.mkdir(parents=True, exist_ok=True)
        (deriv / "dataset_description.json").write_text(
            json.dumps({
                "Name": "MT stopping metrics",
                "BIDSVersion": "1.10.0",
                "DatasetType": "derivative",
                "GeneratedBy": [{
                    "Name": "convert_MT.py",
                    "Description": "Trial-level stopping metrics ported from "
                                   "1__compute_stopping.R.",
                    "Parameters": {"BOX_CONFIG": BOX_CONFIG,
                                   "NOGO_CONFIG": NOGO_CONFIG,
                                   "post_window": post_window},
                }],
                "SourceDatasets": [{"URL": "../../bids_data"}],
            }, indent=2) + "\n", encoding="utf-8")
        (deriv / f"task-{TASK}_desc-{DESC}_beh.json").write_text(
            json.dumps(build_deriv_sidecar(), indent=2) + "\n", encoding="utf-8")
        log.info("  [WROTE]   dataset_description.json + root dictionary")

    log.info("  trials scored: %d   accuracy n/a: %d (%.2f%%)",
             n_trials, acc_na, 100 * acc_na / n_trials if n_trials else 0)
    log.info("  nogo_outcome distribution:")
    for k, v in sorted(outcomes.items(), key=lambda kv: -kv[1]):
        log.info("    %-28s %6d", k, v)
    return 0


def stage3(repo: Path, apply: bool, desc: str) -> int:
    """Kinematics. Reads the STOPPING derivative, because the analysis epoch is
    defined by rt_combined: go trials run 0 -> rt_combined, no-go trials
    0 -> rt_combined + 150 ms (the stabilisation window)."""
    bids = repo / "Projects" / "MT" / "bids_data"
    stop = repo / "Projects" / "MT" / "derivatives" / desc
    out_root = repo / "Projects" / "MT" / "derivatives" / "kinematics"

    srcs = sorted(bids.rglob(f"sub-*_task-{TASK}_beh.tsv"))
    log.info("STAGE 3 (kinematics): %d source TSVs, epoch from derivatives/%s",
             len(srcs), desc)
    if not srcs:
        log.error("No stage-1 output found under %s", bids)
        return 1

    n_in = n_out = 0
    for src in srcs:
        rel = src.relative_to(bids)
        stop_tsv = stop / rel.parent / rel.name.replace(
            f"_task-{TASK}_beh.tsv", f"_task-{TASK}_desc-{desc}_beh.tsv")
        if not stop_tsv.is_file():
            log.error("  missing stopping derivative for %s — run stage 2 first", rel)
            return 1

        with src.open(newline="", encoding="utf-8") as fh:
            raw = list(csv.DictReader(fh, delimiter="\t"))
        with stop_tsv.open(newline="", encoding="utf-8") as fh:
            sc = list(csv.DictReader(fh, delimiter="\t"))
        if len(raw) != len(sc):
            log.error("  row count mismatch for %s (%d vs %d)", rel, len(raw), len(sc))
            return 1

        rows = []
        for r, m in zip(raw, sc):
            n_in += 1
            acc, rt = m.get("accuracy"), m.get("rt_combined")
            rtv = float(rt) if rt not in (None, "", NA) else float("nan")
            # R df_filtered: correct trials only, finite rt_combined > 0.
            if acc != "1" or not math.isfinite(rtv) or rtv <= 0:
                continue
            end_t = rtv + KIN_EPOCH_TAIL_SEC if r["trial_type"] == "nogo" else rtv
            k = compute_kinematics(r["mouse_resp.x"], r["mouse_resp.y"],
                                   r["mouse_resp.time"], end_t)
            # R post-filter on df_kin.
            if (k["kin_parse_failed"] or k["kin_n_samples"] < 3
                    or k["duration"] is None or not math.isfinite(k["duration"])
                    or k["duration"] <= 0
                    or k["max_velocity"] is None or k["mean_velocity"] is None
                    or k["path_length"] is None):
                continue
            for c in ("trial_index", "trial_type", "block_number", "block_type",
                      "is_practice"):
                k[c] = m.get(c, r.get(c))
            rows.append([fmt(k.get(c)) for c in KIN_COLUMNS])
        n_out += len(rows)

        dest = out_root / rel.parent / rel.name.replace(
            f"_task-{TASK}_beh.tsv", f"_task-{TASK}_desc-kinematics_beh.tsv")
        if apply:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("w", newline="", encoding="utf-8") as fh:
                w = csv.writer(fh, delimiter="\t", lineterminator="\n")
                w.writerow(KIN_COLUMNS)
                w.writerows(rows)
        log.info("  %s %-46s -> %s (%d of %d trials)",
                 "[WROTE]  " if apply else "[DRY-RUN]", src.name,
                 dest.relative_to(repo), len(rows), len(raw))

    if apply:
        out_root.mkdir(parents=True, exist_ok=True)
        (out_root / "dataset_description.json").write_text(json.dumps({
            "Name": "MT kinematics",
            "BIDSVersion": "1.10.0",
            "DatasetType": "derivative",
            "GeneratedBy": [{"Name": "convert_MT.py stage 3",
                             "Description": "Time-weighted trajectory kinematics "
                                            "ported from 3__Kinematics.R.",
                             "Parameters": {"kin_epoch_tail_sec": KIN_EPOCH_TAIL_SEC,
                                            "epoch_source": f"derivatives/{desc}"}}],
            "SourceDatasets": [{"URL": "../../bids_data"}, {"URL": f"../{desc}"}],
        }, indent=2) + "\n", encoding="utf-8")
        log.info("  [WROTE]   dataset_description.json")

    log.info("  trials in: %d   kinematics computed: %d (%.1f%%)",
             n_in, n_out, 100 * n_out / n_in if n_in else 0)
    return 0


def stage4(repo: Path, apply: bool, desc: str) -> int:
    """Emit one file per outcome per subject-session, for the overview generator.

    Design notes that matter:

    * Restricted to the ANALYSED subset (block_type == 'go_nogo'), because the
      overview aggregates whatever it finds and the published analysis uses the
      eight mixed blocks only. Practice and go-only blocks would silently shift
      every mean.
    * Every outcome file for a given subject-session has the SAME rows in the
      SAME order, keyed by trial_index. The generator's `requires_correct_filter`
      merges outcomes positionally via cumcount, so mismatched row sets would
      align the wrong trials to the wrong accuracy values.
    * Values are already restricted where the analysis demands it — RT only on
      correct trials with rt > 0, kinematics only where the R filter passed — so
      `requires_correct_filter` is false for all of them and the fragile
      positional merge is never exercised.
    * NOT trimmed. The +/-2.5 SD cell-wise trim the paper applies happens at
      analysis time, not in a data file. The overview's numbers will therefore
      differ modestly from the published ones; reproduce_paper_MT.py, which does
      trim, stays the authority for published-comparable values.
    """
    bids = repo / "Projects" / "MT" / "bids_data"
    stop_root = repo / "Projects" / "MT" / "derivatives" / desc
    kin_root = repo / "Projects" / "MT" / "derivatives" / "kinematics"

    srcs = sorted(bids.rglob(f"sub-*_task-{TASK}_beh.tsv"))
    log.info("STAGE 4 (outcome files): %d sessions x %d outcomes",
             len(srcs), len(OUTCOME_SPEC))
    if not srcs:
        log.error("No stage-1 output under %s", bids)
        return 1

    n_rows = 0
    for src in srcs:
        rel = src.relative_to(bids)
        stem = src.name[:-len(f"_task-{TASK}_beh.tsv")]

        def read(root: Path, label: str) -> dict:
            f = root / rel.parent / rel.name.replace(
                f"_task-{TASK}_beh.tsv", f"_task-{TASK}_desc-{label}_beh.tsv")
            if not f.is_file():
                return {}
            with f.open(newline="", encoding="utf-8") as fh:
                return {r["trial_index"]: r for r in csv.DictReader(fh, delimiter="\t")}

        stop_by_idx = read(stop_root, desc)
        kin_by_idx = read(kin_root, "kinematics")
        if not stop_by_idx:
            log.error("  no stopping derivative for %s — run stage 2 first", rel)
            return 1

        with src.open(newline="", encoding="utf-8") as fh:
            trials = [r for r in csv.DictReader(fh, delimiter="\t")
                      if r.get("block_type") == "go_nogo"]

        for oid, (colname, source, srccol) in OUTCOME_SPEC.items():
            rows = []
            for t in trials:
                ti = t["trial_index"]
                rec = (stop_by_idx if source == "stop" else kin_by_idx).get(ti)
                v = rec.get(srccol, NA) if rec else NA
                if oid == "RT" and v not in (NA, "", None):
                    v = f"{float(v) * 1000.0:.3f}"      # seconds -> ms, as published
                rows.append([ti, t["trial_type"], t["block_number"],
                             v if v not in ("", None) else NA])
            n_rows += len(rows)

            dest = (bids / rel.parent /
                    f"{stem}_task-{TASK}_run-01_{oid}_beh.tsv")
            if apply:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("w", newline="", encoding="utf-8") as fh:
                    w = csv.writer(fh, delimiter="\t", lineterminator="\n")
                    w.writerow(["trial_index", "trial_type", "block_number", colname])
                    w.writerows(rows)

        log.info("  %s %-30s -> %d outcome files x %d trials",
                 "[WROTE]  " if apply else "[DRY-RUN]", stem,
                 len(OUTCOME_SPEC), len(trials))

    if apply:
        for oid, (colname, _, _) in OUTCOME_SPEC.items():
            (bids / f"task-{TASK}_{oid}_beh.json").write_text(
                json.dumps(build_outcome_sidecar(oid, colname), indent=2) + "\n",
                encoding="utf-8")
        log.info("  [WROTE]   %d root outcome dictionaries", len(OUTCOME_SPEC))

    log.info("  rows written: %d across %d files", n_rows, len(srcs) * len(OUTCOME_SPEC))
    return 0


def build_outcome_sidecar(oid: str, colname: str) -> dict:
    desc = {
        "accuracy_binary": ("Trial accuracy. Go: first left click inside the target "
                            "box, exactly one click, no other button. No-go: a "
                            "validated stop and no button press.", None),
        "response_time_ms": ("Go: latency to the first inside-box click. No-go: "
                             "stopping latency, 0 where no movement was initiated. "
                             "n/a on incorrect trials.", "milliseconds"),
        "path_length": ("Cursor distance travelled over the analysis epoch. Correct "
                        "trials only.", "pixels"),
        "mean_velocity": ("Path length divided by movement duration. Correct trials "
                          "only.", "pixels/second"),
        "mean_acceleration": ("Time-weighted mean absolute acceleration. Correct "
                              "trials only.", "pixels/second^2"),
    }[colname]
    d: dict = {
        "TaskName": TASK,
        "Description": f"Per-trial {colname} for the analysed subset "
                       "(block_type == 'go_nogo', the eight mixed blocks). Values "
                       "are NOT outlier-trimmed.",
        "Sources": ["derivatives/stopping", "derivatives/kinematics"],
        "trial_index": {"Description": "Join key to the source _beh.tsv."},
        "trial_type": {"Description": "Trial condition.",
                       "Levels": {"go": "Go trial", "nogo": "No-go trial"}},
        "block_number": {"Description": "Block index within the session."},
        colname: {"Description": desc[0]},
    }
    if desc[1]:
        d[colname]["Units"] = desc[1]
    if colname == "accuracy_binary":
        d[colname]["Levels"] = {"0": "incorrect", "1": "correct"}
    return d


def build_deriv_sidecar() -> dict:
    d = {
        "Description": "Trial-level go/no-go stopping metrics, one row per source trial.",
        "Sources": ["bids_data/sub-*/ses-*/beh/*_task-gonogo_beh.tsv"],
        "trial_index": {"Description": "Join key. Matches trial_index in the source TSV."},
        "trial_type": {"Description": "Copied from the source for convenience."},
        "block_number": {"Description": "Copied from the source."},
        "block_type": {"Description": "Copied from the source. Filter to 'go_nogo' to "
                                      "reproduce the published analysis."},
        "is_practice": {"Description": "Copied from the source."},
        "n_left_clicks": {"Description": "Number of left-button press ONSETS (0->1)."},
        "go_first_left_inside": {"Description": "First left click fell inside the target box.",
                                 "Levels": {"0": "outside or no click", "1": "inside"}},
        "go_first_left_rt": {"Description": "Time of the first left-click onset, from trial onset.",
                             "Units": "seconds"},
        "parse_failed_time": {"Description": "mouse_resp.time could not be parsed."},
        "parse_failed_xy": {"Description": "mouse_resp.x or .y could not be parsed."},
        "parse_failed_buttons": {"Description": "A button channel could not be parsed."},
        "mismatched_lengths": {"Description": "Parsed channels differ in length by more than one sample."},
        "any_rb_nonzero": {"Description": "Right button pressed at any point."},
        "any_mb_nonzero": {"Description": "Middle button pressed at any point."},
        "any_click": {"Description": "Any button pressed. n/a when parsing failed, so a "
                                     "corrupt trial cannot score as a correct withhold."},
        "any_left": {"Description": "Left button pressed at any point."},
        "any_right": {"Description": "Right button pressed at any point."},
        "nogo_stop_time": {"Description": "Stopping latency. 0 means no movement was initiated. "
                                          "n/a when no stop was detected.", "Units": "seconds"},
        "nogo_stopped": {"Description": "A sustained stop was detected and validated."},
        "nogo_outcome": {"Description": "Categorical stopping outcome.",
                         "Levels": {
                             "no_movement_full_duration": "Never moved; trial ran to the deadline.",
                             "no_movement_early": "Never moved; trial ended early.",
                             "stopped_early": "Moved, then stopped before the deadline.",
                             "stopped_near_deadline": "Moved, then stopped near the deadline.",
                             "no_stop_early": "Moved and did not stop; ended early.",
                             "no_stop_timeout": "Moved and did not stop; ran to the deadline.",
                             "too_short_or_bad_time": "Fewer than 3 timestamps.",
                             "too_short_after_peak": "Too few samples after peak velocity.",
                             "missing_xy": "Fewer than 3 valid coordinate pairs.",
                             "bad_sampling_rate": "Median sample interval not positive and finite.",
                             "velocity_all_na": "No finite velocity could be computed."}},
        "nogo_parse_failed": {"Description": "Stopping or button parsing failed for this trial."},
        "rt_combined": {"Description": "Go: first-inside-click latency. No-go: stop latency, "
                                       "0 if never moved. n/a otherwise.", "Units": "seconds"},
        "accuracy": {"Description": "Recomputed trial accuracy. n/a when parsing failed.",
                     "Levels": {"0": "incorrect", "1": "correct"}},
    }
    return d


# ===========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write files (default: dry run)")
    ap.add_argument("--stage",
                    choices=["bids", "derivatives", "kinematics", "outcomes",
                             "all"], default="all")
    ap.add_argument("--include-excluded", action="store_true",
                    help="build every collected subject, including those the "
                         "curation policy excludes (see EXCLUDED_SUBJECTS). The "
                         "default builds the curated dataset only.")
    ap.add_argument("--no-trial-index", action="store_true",
                    help="omit trial_index (reverts to the 15-column source set)")
    ap.add_argument("--post-window", choices=["trial", "after-stop"], default="trial",
                    help="which samples validate the stop. 'trial' (DEFAULT) reproduces "
                         "the R code's tail(v, n_post) and therefore the published "
                         "numbers. 'after-stop' implements what the R comment says "
                         "instead. Comparing the two quantifies that discrepancy.")
    ap.add_argument("--desc", default=DESC,
                    help="BIDS desc- label for the derivative tree (default "
                         f"'{DESC}'). Use a DIFFERENT label for any alternative "
                         "parameterisation so a validated derivative is never "
                         "overwritten. Must be alphanumeric.")
    ap.add_argument("--repo", type=Path, default=None)
    args = ap.parse_args()
    if not args.desc.isalnum():
        log.error("--desc must be alphanumeric (BIDS label rule): %r", args.desc)
        return 2
    globals()["DESC"] = args.desc

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    raise_field_size_limit()

    repo = args.repo.resolve() if args.repo else Path(__file__).resolve().parent
    while not (repo / "Projects").is_dir() and repo != repo.parent:
        repo = repo.parent
    if not (repo / "Projects").is_dir():
        log.error("Could not locate the repository root")
        return 2

    log.info("=== convert_MT.py ===")
    log.info("Repo: %s", repo)
    log.info("Mode: %s", "APPLY" if args.apply else "DRY RUN (nothing written)")

    rc = 0
    if args.stage in ("bids", "all"):
        rc = stage1(repo, args.apply, not args.no_trial_index,
                    args.include_excluded)
        if rc:
            return rc
    if args.stage in ("derivatives", "all"):
        if not args.apply and args.stage == "all":
            log.info("STAGE 2: dry run reads the EXISTING stage-1 output, which stage 1 "
                     "has not yet updated. Numbers below may reflect the old files.")
        rc = stage2(repo, args.apply, args.post_window)  # writes derivatives/<desc>
        if rc:
            return rc
    if args.stage in ("kinematics", "all"):
        rc = stage3(repo, args.apply, args.desc)
        if rc:
            return rc
    if args.stage in ("outcomes", "all"):
        rc = stage4(repo, args.apply, args.desc)
    if not args.apply:
        log.info("Nothing was written. Re-run with --apply.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
