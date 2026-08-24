#!/usr/bin/env python3
"""
build_flow_bids.py — raw FLOW logs  →  clean BIDS bids_data/ tree
================================================================

Rebuilds Projects/FLOW/bids_data/ from the raw PsychoPy exports so that the
FLOW overview page ends up as tidy as OLM's: **two headline outcomes, nothing
else**.

    FLOWIDX  — subjective flow index from the Likert scale:
               sum over the 3 items of ( -mean(B) + 2*mean(F) - mean(O) )
    TASKIDX  — the same -B + 2F - O contrast applied to a *behavioural* measure
               (which measure is configurable — see TASK_MEASURE below)

Both are ONE value per subject x session, which is exactly the shape an ICC
needs (subject x session matrix).  Per-trial RT/ACC/DIFF files are *not*
emitted, because those were what cluttered the FLOW overview with five plots
and a degenerate FLOWIDX violin (the same value repeated across three
conditions).

Trial-level data is still written to ``_events.tsv`` for provenance and
reanalysis — BIDS treats events.tsv as the record of what happened, and the
BEEHub outcome loader ignores it (it only globs the ``_<OUTCOME>_beh.tsv``
suffixes declared in outcome_measures).

Usage
-----
    python build_flow_bids.py  <source_data>  <out_bids_dir>  [--task-measure M]

ONE source root. The task CSVs, Likert CSVs and the demographics JSON all live
under it, in the layout the study already uses:

    source_data/
      sub-003/
        task/    sub-003_task_20260428_105509.csv   (one per session)
        likert/  sub-003_likert_20260428_105509.csv (one per session)
        json/    sub-003.json                       (demographics + BDI/FKS/FAM)
        html/    ...                                (ignored)

Discovery is recursive and driven by FILENAME, not folder name, so the
subdirectory names (task/, likert/, json/) are a convention rather than a
requirement — a flat dump of the same files works identically.

Sessions are assigned per subject by chronological order of the timestamp in the
filename (earliest = ses-01), and task/Likert files are paired by that timestamp.

Partial sessions are kept, not dropped: sub-005 has a second task file with no
matching Likert file, so that session yields FlowIndex_Task and events but no
FlowIndex_Likert. Discarding the whole session would throw away real task data.

Verification
------------
The FLOWIDX formula was validated against the project's existing
FlowIndex_Likert_beh.tsv files for sub-003: it reproduces 16.6667 (ses-01) and 16.3333
(ses-02) exactly.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

TASK_NAME = "FLOW"

#: Likert items, in the order they appear in the raw likert CSV.
LIKERT_ITEMS = ["q1_love_again", "q2_well_matched", "q3_thrilled"]

#: The flow-index contrast weights.  Keys must match the `condition` column.
FLOW_WEIGHTS = {"B": -1.0, "F": 2.0, "O": -1.0}

#: Which behavioural measure the -B + 2F - O contrast is applied to for TASKIDX.
#: Override on the command line with --task-measure.
#:
#:   difficulty_level  — achieved arithmetic difficulty. Recommended default:
#:                       the adaptive staircase makes this the measure that
#:                       actually carries between-subject variance.
#:   response_time_ms  — correct trials only. Heavily influenced by Overload
#:                       timeouts, so interpret with care.
#:   accuracy          — NOT recommended: the staircase pins Flow accuracy near
#:                       ~0.6 and Boredom at ceiling, so the contrast is
#:                       structurally near zero (-0.03 / -0.09 for sub-003) and
#:                       will have almost no variance to correlate across
#:                       sessions.
TASK_MEASURE = "difficulty_level"

#: Set to True to restrict RT to correct trials before averaging.
RT_CORRECT_ONLY = True

#: Single trial_type level for these session-level indices.
#:
#: These indices are contrasts computed ACROSS the B/F/O conditions, so no single
#: condition label is truthful. The earlier placeholder "composite" was actively
#: misleading in the figures — it appeared in the legend where readers expect a
#: CONDITION, implying FLOW has a condition called "composite". "all_conditions"
#: says what is actually true: every condition contributed to this value.
#:
#: (The overview additionally suppresses this label in legends/banners when a
#: project has only one trial type, so it should not clutter the figure at all.)
#: Must not collide with BEEHub's control keywords (control/rest/baseline/...),
#: or the metric would be filed under control_reliability instead of the task cell.
TRIAL_TYPE_LABEL = "all_conditions"

#: How FLOWIDX rows (= Cronbach alpha "items") are formed.
#:   'item-replicate' -> 9 items (3 Likert items x 3 replicates). RECOMMENDED:
#:        with only 3 items, alpha is capped low by Spearman-Brown (r=0.3 -> 0.56)
#:        purely because of item count. 9 items lifts the same r=0.3 to ~0.79.
#:   'replicate'      -> 3 items (one total per replicate).
#: The subject x session MEAN is identical either way, so the ICC never changes.
ALPHA_BASIS = "item-replicate"

#: Optional explicit {(subject, raw_timestamp): session_label} override.
SESSION_MAP: dict = {}

#: Number of COMPLETE sessions a subject must have to be included.
#: A session counts as complete only if BOTH the task CSV and the Likert CSV are
#: present — a task run with no Likert run (sub-005 ses-02) is not complete.
#:
#: DEFAULT IS 1, i.e. NO EXCLUSION.
#:
#: It is tempting to drop single-session subjects here, so that the demographics
#: header, the violins and the ICC all describe one identical sample. Resist it:
#: the BIDS tree is the RAW RECORD of what was collected, and silently omitting
#: five participants from it means nobody downstream can ever recompute anything
#: with them — the session-1 distribution, dropout analyses, or a later reliability
#: estimate once their second session is run.
#:
#: Exclusion is an ANALYSIS decision, not a file-writing decision, and the
#: analysis layer already makes the gap visible: the overview banner prints
#: "n = N paired" next to every ICC, so a header of 29 participants alongside an
#: ICC on 24 is transparent rather than misleading.
#:
#: 0 = no filtering (every collected session is written, partial ones included).
#: Set --required-sessions 2 if you deliberately want a complete-cases-only tree.
REQUIRED_COMPLETE_SESSIONS = 0

RAW_RE = re.compile(r"^(sub-\d+)_(task|likert)_(\d{8}_\d{6})\.csv$")


# ─────────────────────────────────────────────────────────────────────────────
# Raw log discovery
# ─────────────────────────────────────────────────────────────────────────────

def discover_raw(source_dir: Path) -> dict:
    """Group raw CSVs into {subject: {timestamp: {'task': p, 'likert': p}}}.

    Recursive, filename-driven: works for source_data/sub-XXX/task/*.csv and for
    a flat folder alike. A timestamp with only one of the two kinds present is
    still returned — the caller decides what it can build from it.
    """
    found: dict = {}
    for f in sorted(source_dir.rglob("*.csv")):
        m = RAW_RE.match(f.name)
        if not m:
            continue
        sub, kind, ts = m.groups()
        found.setdefault(sub, {}).setdefault(ts, {})[kind] = f
    return found


def discover_demographics(source_dir: Path) -> dict:
    """Find the per-participant questionnaire exports: {subject: path}.

    Matches ONLY `sub-XXX.json` so the BIDS sidecars (`*_beh.json`,
    `*_session.json`) and dataset_description.json can never be mistaken for one.
    """
    found: dict = {}
    for f in sorted(source_dir.rglob("*.json")):
        m = re.match(r"^(sub-\d+)\.json$", f.name)
        if m:
            found[m.group(1)] = f
    return found


def assign_sessions(runs: dict) -> list:
    """Chronological order → ses-01, ses-02, …  Returns [(ses_label, ts, files)]."""
    out = []
    for i, ts in enumerate(sorted(runs.keys()), start=1):
        out.append((f"ses-{i:02d}", ts, runs[ts]))
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Core computation
# ─────────────────────────────────────────────────────────────────────────────

def _weighted_contrast(cond_means: pd.Series) -> float | None:
    """Apply FLOW_WEIGHTS to a {condition: value} Series. None if a level is missing."""
    if not set(FLOW_WEIGHTS).issubset(set(cond_means.index)):
        return None
    return float(sum(w * cond_means[c] for c, w in FLOW_WEIGHTS.items()))


def compute_flow_replicates(likert: pd.DataFrame) -> tuple:
    """Decompose the flow index into its replicate x item cells.

    Each condition (B/F/O) is presented 3 times per session, so the three
    occurrences can be paired by ordinal position into 3 *replicates* of the
    -B + 2F - O contrast:

        replicate 1 = (1st B, 1st F, 1st O)
        replicate 2 = (2nd B, 2nd F, 2nd O)
        ...

    For each replicate r and Likert item i we get one contrast

        c[r][i] = -B[r][i] + 2*F[r][i] - O[r][i]          in [-12, +12]

    The session flow index is then simply

        flow_index = mean_over_replicates( sum_over_items c[r][i] )
                   = mean( 3 * c[r][i] )  over all r,i cells

    Both expressions are algebraically identical, which is what makes this
    decomposition *lossless*: emitting the cells instead of a single number
    leaves every subject x session mean — and therefore the ICC — unchanged.

    Returns
    -------
    (flow_index, cells_df, item_means_df)
        ``cells_df`` has one row per (replicate, item) with columns
        ``replicate``, ``item``, ``contrast`` (in [-12,12]) and ``scaled``
        (= 3*contrast, i.e. on the index's own [-36,36] scale).
    """
    items = [c for c in LIKERT_ITEMS if c in likert.columns]
    if not items:
        raise ValueError(f"none of {LIKERT_ITEMS} found in likert CSV")

    d = likert.copy()
    # ordinal replicate index within each condition (1st B, 2nd B, ...)
    d["_rep"] = d.groupby("condition").cumcount() + 1

    n_rep = int(min(d[d.condition == c]["_rep"].max() for c in FLOW_WEIGHTS
                    if (d.condition == c).any()) or 0)
    if n_rep < 1 or not set(FLOW_WEIGHTS).issubset(set(d["condition"].unique())):
        raise ValueError(f"likert data missing one of conditions {list(FLOW_WEIGHTS)}")

    rows = []
    for r in range(1, n_rep + 1):
        block = d[d["_rep"] == r].set_index("condition")
        for it in items:
            c = sum(w * float(block.loc[cond, it]) for cond, w in FLOW_WEIGHTS.items())
            rows.append({"replicate": r, "item": it,
                         "contrast": c, "scaled": 3.0 * c})
    cells = pd.DataFrame(rows)

    # Session index — identical to the classic per-condition-mean formula.
    flow_index = float(cells.groupby("replicate")["contrast"].sum().mean())

    item_means = d.groupby("condition")[items].mean()
    return flow_index, cells, item_means


def compute_task_replicates(task: pd.DataFrame, measure: str, parcels: int = 1) -> tuple:
    """Per-replicate (and optionally per-parcel) -B + 2F - O on a behavioural measure.

    Task blocks mirror the Likert blocks (each condition 3x per session), so the
    same ordinal pairing gives 3 replicates.

    ``parcels`` adds a SECOND axis so k can exceed 3.  Each block's trials are
    split into ``parcels`` consecutive chunks; the contrast is then computed
    within each (replicate, parcel) cell:

        k = 3 replicates x ``parcels``      (parcels=3 -> k=9)

    ⚠ Parcels are NOT equivalent to the Likert items.  q1/q2/q3 are three
    genuinely different questions; trial parcels are arbitrary slices of the
    SAME measurement, and consecutive trials within a block are autocorrelated
    (the staircase drifts, practice accrues).  Inter-parcel correlations are
    therefore inflated relative to true distinct items, which biases Cronbach's
    alpha UPWARD.  Use parcels>1 for a more stable estimate, but report it as
    a parcel-based (split-half-like) coefficient, not as an item alpha.

    Returns (session_value, rows_df, cond_means).  ``session_value`` is the mean
    of the emitted rows, so the subject x session mean — and hence the ICC — is
    exactly the mean of what is written to disk.
    """
    df = task.copy()
    for col in ("is_correct", "is_timeout"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().eq("true").astype(int)

    if measure == "accuracy":
        df["_v"] = df["is_correct"]
    elif measure == "response_time_ms":
        if RT_CORRECT_ONLY and "is_correct" in df.columns:
            df = df[df["is_correct"] == 1]
        df["_v"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    else:
        df["_v"] = pd.to_numeric(df[measure], errors="coerce")
    df = df.dropna(subset=["_v"]).sort_values(["block", "trial"])

    cond_means = df.groupby("condition")["_v"].mean()

    # ordinal replicate of each condition, derived from block order
    blk_order = (df[["block", "condition"]].drop_duplicates().sort_values("block"))
    blk_order["_rep"] = blk_order.groupby("condition").cumcount() + 1
    rep_of_block = dict(zip(blk_order["block"], blk_order["_rep"]))
    df["_rep"] = df["block"].map(rep_of_block)

    # split each block's trials into `parcels` consecutive chunks
    def _parcel(g):
        g = g.copy()
        g["_parcel"] = [min(parcels - 1, int(i * parcels / len(g))) + 1
                        for i in range(len(g))]
        return g
    df = df.groupby("block", group_keys=False).apply(_parcel)

    cell = (df.groupby(["_rep", "_parcel", "condition"], as_index=False)["_v"].mean())

    rows = []
    for r in sorted(cell["_rep"].dropna().unique()):
        for p in range(1, parcels + 1):
            sub = cell[(cell["_rep"] == r) & (cell["_parcel"] == p)] \
                    .set_index("condition")["_v"]
            v = _weighted_contrast(sub)
            if v is not None:
                rows.append({"replicate": int(r), "parcel": p, "task_flow_index": v})

    if not rows:
        return None, pd.DataFrame(), cond_means
    rows_df = pd.DataFrame(rows)
    return float(rows_df["task_flow_index"].mean()), rows_df, cond_means


def compute_task_index(task: pd.DataFrame, measure: str) -> tuple:
    """-B + 2F - O applied to a behavioural measure. Returns (value, cond_means)."""
    df = task.copy()
    # normalise the boolean-ish columns coming out of PsychoPy ("True"/"False")
    for col in ("is_correct", "is_timeout"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().eq("true").astype(int)

    if measure == "accuracy":
        df["_v"] = df["is_correct"]
    elif measure == "response_time_ms":
        if RT_CORRECT_ONLY and "is_correct" in df.columns:
            df = df[df["is_correct"] == 1]
        df["_v"] = pd.to_numeric(df["response_time_ms"], errors="coerce")
    else:
        df["_v"] = pd.to_numeric(df[measure], errors="coerce")

    df = df.dropna(subset=["_v"])
    means = df.groupby("condition")["_v"].mean()
    return _weighted_contrast(means), means


# ─────────────────────────────────────────────────────────────────────────────
# Writers
# ─────────────────────────────────────────────────────────────────────────────

def _write_tsv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, sep="\t", index=False, na_rep="n/a")


def _write_json(obj: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def write_flowidx(out_dir: Path, stem: str, flow_index: float, cells: pd.DataFrame,
                  item_means: pd.DataFrame, basis: str) -> None:
    """Write FlowIndex_Likert_beh.tsv with one row per alpha 'item'.

    basis='item-replicate' (default, k=9): one row per (replicate x Likert item),
        value = 3 * contrast, i.e. rescaled onto the index's own [-36, +36]
        metric so that the MEAN of the rows is exactly the session flow index.
    basis='replicate' (k=3): one row per replicate, value = sum of the 3 item
        contrasts for that replicate.

    In BOTH cases the per-(subject, session) mean equals the classic session
    flow index, so the ICC is bit-for-bit identical to the single-value version.
    Only the internal-consistency (Cronbach alpha / KR-20) estimate changes,
    because that is computed across rows.
    """
    if basis == "replicate":
        rep = (cells.groupby("replicate")["contrast"].sum()
                    .reset_index(name="flow_index"))
        rows = pd.DataFrame({
            "trial_type": TRIAL_TYPE_LABEL,
            "replicate":  rep["replicate"],
            "item":       "all_items",
            "flow_index": rep["flow_index"],
        })
    else:
        rows = pd.DataFrame({
            "trial_type": TRIAL_TYPE_LABEL,
            "replicate":  cells["replicate"],
            "item":       cells["item"],
            "flow_index": cells["scaled"],
        })

    _write_tsv(rows, out_dir / f"{stem}_FlowIndex_Likert_beh.tsv")
    _write_json(flowidx_sidecar(flow_index, item_means, basis, len(rows)),
                out_dir / f"{stem}_FlowIndex_Likert_beh.json")


def write_taskidx(out_dir: Path, stem: str, value: float, reps: pd.DataFrame,
                  measure: str, cond_means: pd.Series) -> None:
    """Write FlowIndex_Task_beh.tsv — one row per replicate (k=3)."""
    rows = pd.DataFrame({
        "trial_type":      TRIAL_TYPE_LABEL,
        "replicate":       reps["replicate"],
        "parcel":          reps["parcel"],
        "task_flow_index": reps["task_flow_index"],
    })
    _write_tsv(rows, out_dir / f"{stem}_FlowIndex_Task_beh.tsv")
    _write_json(taskidx_sidecar(measure, cond_means, value, len(rows)),
                out_dir / f"{stem}_FlowIndex_Task_beh.json")


def build_events(task: pd.DataFrame) -> pd.DataFrame:
    """BIDS events.tsv — full trial record, kept for provenance/reanalysis."""
    df = task.copy()
    for col in ("is_correct", "is_timeout"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.lower().eq("true").astype(int)

    # onset in seconds, relative to the first trial of the session
    if "trial_onset_timestamp" in df.columns:
        ts = pd.to_datetime(df["trial_onset_timestamp"], errors="coerce")
        onset = (ts - ts.min()).dt.total_seconds()
    else:
        onset = pd.Series([pd.NA] * len(df))

    rt_s = pd.to_numeric(df.get("response_time_ms"), errors="coerce") / 1000.0

    ev = pd.DataFrame({
        "onset":            onset.round(3),
        "duration":         rt_s.round(3),
        "trial_type":       TASK_NAME + "_" + df["condition"].astype(str),
        "condition":        df["condition"],
        "block":            df.get("block"),
        "trial":            df.get("trial"),
        "difficulty_level": df.get("difficulty_level"),
        "expression":       df.get("expression"),
        "correct_answer":   df.get("correct_answer"),
        "user_answer":      df.get("user_answer"),
        "response_time_ms": pd.to_numeric(df.get("response_time_ms"), errors="coerce"),
        "is_correct":       df.get("is_correct"),
        "is_timeout":       df.get("is_timeout"),
    })
    return ev


EVENTS_SIDECAR = {
    "TaskName": TASK_NAME,
    "TaskDescription": ("Mental-arithmetic flow paradigm. Boredom (B), Flow (F) and "
                        "Overload (O) blocks differing only in difficulty; the Flow "
                        "condition tracks the participant's skill via an adaptive staircase."),
    "onset":            {"Description": "Trial onset, seconds from first trial of the session.",
                         "Units": "seconds"},
    "duration":         {"Description": "Response time for the trial.", "Units": "seconds"},
    "trial_type":       {"Description": "Condition label, prefixed with the task name.",
                         "Levels": {"FLOW_B": "Boredom", "FLOW_F": "Flow", "FLOW_O": "Overload"}},
    "condition":        {"Description": "Raw condition code.",
                         "Levels": {"B": "Boredom", "F": "Flow", "O": "Overload"}},
    "difficulty_level": {"Description": "Arithmetic difficulty level of the trial."},
    "response_time_ms": {"Description": "Response time.", "Units": "milliseconds"},
    "is_correct":       {"Description": "Trial correct.", "Levels": {"0": "incorrect", "1": "correct"}},
    "is_timeout":       {"Description": "Trial timed out (scored incorrect).",
                         "Levels": {"0": "responded", "1": "timeout"}},
}


#: Theoretical bounds. Per item the contrast -B + 2F - O with Likert in [1,7]
#: ranges over [-1*7 + 2*1 - 7, -1*1 + 2*7 - 1] = [-12, +12]; summed over the
#: 3 items the index spans [-36, +36], with 0 = "Flow rated no better than
#: Boredom/Overload". Emitted into the sidecar so plots can use a fixed axis
#: and a zero reference line instead of auto-scaling.
INDEX_BOUNDS = [-36.0, 36.0]
INDEX_NEUTRAL = 0.0


def flowidx_sidecar(flow_index: float, means: pd.DataFrame,
                    basis: str, n_rows: int) -> dict:
    return {
        "TaskName": TASK_NAME,
        "MeasurementToolMetadata": {
            "Description": "Subjective flow index derived from three 7-point Likert items "
                           "administered after every task block. Each condition (B/F/O) is "
                           "presented 3 times per session, so the contrast is computed "
                           "3 times (once per ordinal replicate)."
        },
        "trial_type": {
            "Description": "Single level: these are session-level composites collapsed "
                           "across the B/F/O conditions, not per-condition values.",
            "Levels": {TRIAL_TYPE_LABEL: "Session composite across conditions"},
        },
        "replicate": {
            "Description": "Ordinal replicate of the B/F/O cycle within the session "
                           "(1 = first occurrence of each condition, etc.).",
        },
        "item": {
            "Description": "Likert item the row's contrast was computed from "
                           "('all_items' when rows are replicate totals).",
        },
        "flow_index": {
            "Description": ("Subjective flow index. Contrast (-1*Boredom + 2*Flow "
                            "- 1*Overload) applied to the Likert responses. Rows are the "
                            "internal-consistency items; their MEAN is the session flow index."),
            "Formula": "mean_over_rows(...) == mean_r( sum_i ( -B[r][i] + 2*F[r][i] - O[r][i] ) )",
            "AlphaBasis": basis,
            "NumberOfItems": int(n_rows),
            "SessionFlowIndex": round(float(flow_index), 6),
            "Items": LIKERT_ITEMS,
            "ItemRange": [1, 7],
            "Weights": FLOW_WEIGHTS,
            "Bounds": INDEX_BOUNDS,
            "NeutralValue": INDEX_NEUTRAL,
            "Units": "arbitrary (Likert composite)",
            "Interpretation": ("Higher = more flow in the Flow condition relative to "
                               "Boredom and Overload. 0 = no preference. Negative = Flow "
                               "rated no better than the control conditions."),
            "ConditionItemMeans": {c: {i: round(float(means.loc[c, i]), 4)
                                       for i in means.columns}
                                   for c in means.index},
        },
    }


def taskidx_sidecar(measure: str, means: pd.Series,
                    value: float, n_rows: int) -> dict:
    return {
        "TaskName": TASK_NAME,
        "trial_type": {
            "Description": "Single level: session composite across conditions.",
            "Levels": {TRIAL_TYPE_LABEL: "Session composite across conditions"},
        },
        "replicate": {
            "Description": "Ordinal replicate of the B/F/O cycle within the session.",
        },
        "task_flow_index": {
            "Description": (f"Behavioural flow contrast: -B + 2F - O applied to the "
                            f"block-level mean of '{measure}'. One row per replicate; "
                            f"their mean is the session value."),
            "Formula": "-mean(B) + 2*mean(F) - mean(O), per replicate",
            "SourceMeasure": measure,
            "RestrictedToCorrectTrials": bool(RT_CORRECT_ONLY and measure == "response_time_ms"),
            "Weights": FLOW_WEIGHTS,
            "NumberOfItems": int(n_rows),
            "SessionValue": round(float(value), 6),
            "ConditionMeans": {str(c): round(float(v), 4) for c, v in means.items()},
        },
    }


DATASET_DESCRIPTION = {
    "Name": "FLOW — Mental Arithmetic Flow Paradigm",
    "BIDSVersion": "1.8.0",
    "DatasetType": "raw",
    "Authors": ["MemoSlap Lab"],
}


# ─────────────────────────────────────────────────────────────────────────────
# participants.tsv / participants.json from the questionnaire JSONs
# ─────────────────────────────────────────────────────────────────────────────
#
# The source questionnaire exports (one sub-XXX.json per participant) are in
# German. Everything study-specific lives in the tables below, so adapting this
# to another study/language means editing data, not code.

#: Maps the raw `geschlecht` string onto BIDS-style values.
#: Keys are compared casefolded + stripped.
SEX_MAP = {
    "männlich": "male",   "maennlich": "male",   "m": "male",
    "weiblich": "female", "w": "female", "f": "female",
    "divers": "other",    "non-binär": "other",  "nonbinaer": "other",
}

#: Values that mean "the participant was asked and declined to say".
#: This is NOT the same as the field being absent, and BIDS' catch-all "n/a"
#: would conflate the two — so declined answers get their own level.
NOT_SPECIFIED_TOKENS = {
    "keine angabe", "k.a.", "ka", "keine_angabe",
    "nicht angegeben", "prefer not to say", "no answer",
}

#: Ordered levels used in participants.json and in the overview's counts.
SEX_LEVELS = ["male", "female", "other", "not_specified", "n/a"]

#: Where the demographics live inside each participant JSON.
DEMOG_KEY   = "demographics"
SEX_FIELD   = "geschlecht"
AGE_FIELD   = "alter"


def _norm(v) -> str:
    return str(v).strip().casefold() if v is not None else ""


def parse_sex(raw) -> str:
    """German sex string -> male / female / other / not_specified / n/a."""
    s = _norm(raw)
    if s in NOT_SPECIFIED_TOKENS:
        return "not_specified"      # asked, declined
    if s in SEX_MAP:
        return SEX_MAP[s]
    if s == "":
        return "n/a"                # field absent or empty
    return "n/a"                    # unrecognised -> missing, and warned about


def parse_age(raw):
    """German age value -> int, or None. 'keine Angabe' -> None (declined)."""
    if raw is None:
        return None, "n/a"
    if _norm(raw) in NOT_SPECIFIED_TOKENS:
        return None, "not_specified"
    try:
        return int(float(str(raw).replace(",", ".").strip())), "ok"
    except (TypeError, ValueError):
        return None, "n/a"


def _questionnaire_extras(doc: dict) -> dict:
    """Pull the scored questionnaire summaries, when present.

    These are free (already computed in the export) and are genuinely useful as
    participant-level covariates, so they are carried into participants.tsv.
    Missing questionnaires simply yield n/a.
    """
    out = {}
    bdi = doc.get("BDI_II", {}).get("totals", {}).get("gesamt")
    try:
        out["bdi_total"] = int(str(bdi).strip())
    except (TypeError, ValueError):
        out["bdi_total"] = None
    for key, col in (("FKS_dispositional", "fks_mean"), ("FAM_Freude", "fam_mean")):
        v = doc.get(key, {}).get("mean_score")
        try:
            out[col] = float(v)
        except (TypeError, ValueError):
            out[col] = None
    return out


def build_participants(demog_dir: Path, out_dir: Path,
                       subjects: list | None = None) -> tuple:
    """Generate participants.tsv + participants.json from the sub-XXX.json exports.

    Returns (DataFrame, warnings).

    ``subjects`` is the ANALYSED sample (i.e. after the completeness filter).
    When given, the table is restricted to exactly those subjects — a JSON for
    an excluded participant is ignored. Otherwise participants.tsv would keep
    describing all 29 recruited people while the violins and the ICC describe
    only the 24 with two complete sessions, and the header's "Participants: N"
    would contradict the ICC's "n paired".

    Subjects in ``subjects`` with no JSON still get an all-n/a row, so nobody is
    silently dropped from the table.
    """
    warns: list = []
    docs: dict = {}
    if demog_dir and demog_dir.exists():
        for f in sorted(demog_dir.rglob("*.json")):
            m = re.match(r"^(sub-\d+)\.json$", f.name)
            if not m:
                continue
            try:
                docs[m.group(1)] = json.loads(f.read_text(encoding="utf-8"))
            except Exception as e:
                warns.append(f"{f.name}: unreadable ({e})")
    elif demog_dir:
        warns.append(f"demographics dir not found: {demog_dir}")

    if subjects:
        ids = sorted(subjects)
        unused = sorted(set(docs) - set(ids))
        if unused:
            warns.append(f"{len(unused)} demographics JSON(s) ignored — subject not in "
                         f"the analysed sample: {', '.join(unused)}")
    else:
        ids = sorted(docs)
    rows = []
    for sid in ids:
        doc = docs.get(sid)
        if doc is None:
            warns.append(f"{sid}: no demographics JSON — row written as n/a")
            rows.append({"participant_id": sid, "sex": "n/a", "age": None,
                         "bdi_total": None, "fks_mean": None, "fam_mean": None})
            continue
        d = doc.get(DEMOG_KEY, {}) or {}
        raw_sex = d.get(SEX_FIELD)
        sex = parse_sex(raw_sex)
        if sex == "n/a" and _norm(raw_sex) not in ("",):
            warns.append(f"{sid}: unrecognised {SEX_FIELD}={raw_sex!r} -> n/a")
        age, age_status = parse_age(d.get(AGE_FIELD))
        if age_status == "not_specified":
            warns.append(f"{sid}: age declined ('keine Angabe')")
        row = {"participant_id": sid, "sex": sex, "age": age}
        row.update(_questionnaire_extras(doc))
        rows.append(row)

    df = pd.DataFrame(rows, columns=["participant_id", "sex", "age",
                                     "bdi_total", "fks_mean", "fam_mean"])
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_tsv(df, out_dir / "participants.tsv")
    _write_json({
        "participant_id": {"Description": "BIDS participant identifier"},
        "sex": {
            "Description": "Self-reported sex, mapped from the German questionnaire "
                           "field 'geschlecht'.",
            "Levels": {
                "male": "männlich",
                "female": "weiblich",
                "other": "divers / non-binary",
                "not_specified": "Participant was asked and declined to answer "
                                 "('keine Angabe'). Distinct from n/a, which means "
                                 "the value is missing or was never collected.",
                "n/a": "Missing / not collected / unrecognised value",
            },
        },
        "age": {"Description": "Age at the demographics assessment. n/a if declined "
                               "('keine Angabe') or missing.",
                "Units": "years"},
        "bdi_total": {"Description": "Beck Depression Inventory II total score.",
                      "MinValue": 0, "MaxValue": 63},
        "fks_mean": {"Description": "Flow-Kurzskala (dispositional, Rheinberg et al. 2003) "
                                    "mean item score.",
                     "MinValue": 1, "MaxValue": 7},
        "fam_mean": {"Description": "FAM Freude subscale (Rheinberg et al. 2001, adapted) "
                                    "mean item score.",
                     "MinValue": 1, "MaxValue": 7},
    }, out_dir / "participants.json")
    return df, warns


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source_dir", type=Path,
                    help="the ONE source_data root (task CSVs, likert CSVs and "
                         "sub-XXX.json demographics are all discovered under it)")
    ap.add_argument("out_dir", type=Path, help="target bids_data/ folder")
    ap.add_argument("--task-measure", default=TASK_MEASURE,
                    choices=["difficulty_level", "response_time_ms", "accuracy"],
                    help=f"measure the -B+2F-O contrast is applied to (default: {TASK_MEASURE})")
    ap.add_argument("--required-sessions", type=int, default=REQUIRED_COMPLETE_SESSIONS,
                    metavar="N",
                    help="keep only subjects with N COMPLETE sessions (task AND likert). "
                         f"Default {REQUIRED_COMPLETE_SESSIONS}.")
    ap.add_argument("--keep-incomplete", action="store_true",
                    help="disable the completeness filter and build every session found")
    ap.add_argument("--no-participants", action="store_true",
                    help="do not (re)build participants.tsv/.json from the sub-XXX.json files")
    ap.add_argument("--task-parcels", type=int, default=1, metavar="P",
                    help="split each task block into P consecutive trial parcels, giving "
                         "k = 3 x P items for TASKIDX (P=3 -> k=9). NOTE: parcels are "
                         "autocorrelated slices of the same measure, so alpha is biased "
                         "upward relative to the Likert item alpha. Default 1 (k=3).")
    ap.add_argument("--alpha-basis", default=ALPHA_BASIS,
                    choices=["item-replicate", "replicate"],
                    help="how FLOWIDX rows (Cronbach alpha items) are formed "
                         f"(default: {ALPHA_BASIS} = 9 items)")
    ap.add_argument("--no-events", action="store_true", help="skip writing events.tsv")
    args = ap.parse_args()

    raw = discover_raw(args.source_dir)
    if not raw:
        print(f"✗ no CSVs matching sub-XXX_(task|likert)_TIMESTAMP.csv "
              f"under {args.source_dir}")
        return 1
    demo_files = discover_demographics(args.source_dir)
    print(f"Found {len(raw)} subject(s), {len(demo_files)} demographics JSON(s) "
          f"under {args.source_dir}")

    # ── Completeness filter ──────────────────────────────────────────────────
    n_req = 0 if args.keep_incomplete else args.required_sessions
    excluded: list = []
    if n_req:
        kept = {}
        for sub, runs in raw.items():
            complete = {ts: f for ts, f in runs.items()
                        if "task" in f and "likert" in f}
            n_partial = len(runs) - len(complete)
            if len(complete) >= n_req:
                # keep ONLY the complete sessions, and only the first n_req of
                # them (chronologically) so every subject contributes the same
                # design — otherwise a 3rd session would silently shift which
                # pair the ICC is computed from.
                keep_ts = sorted(complete)[:n_req]
                kept[sub] = {ts: complete[ts] for ts in keep_ts}
                if n_partial or len(complete) > n_req:
                    excluded.append(
                        f"{sub}: kept {n_req} complete session(s); dropped "
                        f"{n_partial} incomplete + {len(complete) - n_req} extra")
            else:
                excluded.append(
                    f"{sub}: EXCLUDED — {len(complete)} complete session(s) "
                    f"(need {n_req}); {n_partial} incomplete")
        raw = kept
        print(f"  → {len(raw)} subject(s) with {n_req} complete session(s); "
              f"{len(excluded)} note(s)")
    if not raw:
        print("✗ no subjects left after the completeness filter. "
              "Use --keep-incomplete to build everything.")
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(DATASET_DESCRIPTION, args.out_dir / "dataset_description.json")

    subjects_seen, rows_written, warnings = [], 0, []

    for sub in sorted(raw):
        subjects_seen.append(sub)
        for ses, ts, files in assign_sessions(raw[sub]):
            has_task   = "task" in files
            has_likert = "likert" in files
            if not has_task and not has_likert:
                continue
            # Partial sessions are BUILT, not skipped. Dropping a session because
            # one of the two files is missing would silently discard real data
            # (sub-005 has a task run with no Likert run).
            if not has_likert:
                warnings.append(f"{sub} {ses}: no Likert CSV — "
                                f"FlowIndex_Likert omitted for this session")
            if not has_task:
                warnings.append(f"{sub} {ses}: no task CSV — "
                                f"FlowIndex_Task and events omitted for this session")

            out_dir = args.out_dir / sub / ses / "beh"
            stem    = f"{sub}_{ses}_task-{TASK_NAME}_run-01"

            fidx, n_items, tidx, treps = None, 0, None, []

            # ── FlowIndex_Likert (subjective composite) ──────────────────────
            if has_likert:
                likert_df = pd.read_csv(files["likert"])
                try:
                    fidx, cells, item_means = compute_flow_replicates(likert_df)
                    write_flowidx(out_dir, stem, fidx, cells, item_means, args.alpha_basis)
                    n_items = (len(cells) if args.alpha_basis == "item-replicate"
                               else cells["replicate"].nunique())
                except Exception as e:
                    warnings.append(f"{sub} {ses}: FlowIndex_Likert not written — {e}")
                    fidx = None

            # ── FlowIndex_Task + events ──────────────────────────────────────
            if has_task:
                task_df = pd.read_csv(files["task"])
                tidx, treps, cond_means = compute_task_replicates(
                    task_df, args.task_measure, parcels=args.task_parcels)
                if tidx is None:
                    warnings.append(f"{sub} {ses}: FlowIndex_Task not written — "
                                    f"a condition (B/F/O) is missing")
                else:
                    write_taskidx(out_dir, stem, tidx, treps,
                                  args.task_measure, cond_means)
                if not args.no_events:
                    _write_tsv(build_events(task_df), out_dir / f"{stem}_events.tsv")
                    _write_json(EVENTS_SIDECAR, out_dir / f"{stem}_events.json")

            _write_json({"AcquisitionDateTime": ts, "RunCount": 1,
                         "SourceCSVs": {k: files[k].name
                                        for k in ("task", "likert") if k in files}},
                        out_dir / f"{sub}_{ses}_session.json")

            rows_written += 1
            f_str = f"{fidx:.3f}" if fidx is not None else "  --  "
            t_str = f"{tidx:.3f}" if tidx is not None else "  --  "
            print(f"  ✓ {sub} {ses}   Likert={f_str:>8} (k={n_items})   "
                  f"Task={t_str:>8} (k={len(treps)})")

    # ── participants.tsv / participants.json ─────────────────────────────────
    # Built from the same source root: the German questionnaire exports at
    # source_data/sub-XXX/json/sub-XXX.json.
    if not args.no_participants:
        pdf, pwarns = build_participants(args.source_dir, args.out_dir,
                                         subjects=subjects_seen)
        warnings.extend(pwarns)
        counts = pdf["sex"].value_counts().to_dict()
        n_age = int(pdf["age"].notna().sum())
        print("\n  participants.tsv: "
              + ", ".join(f"{counts.get(l, 0)} {l}" for l in SEX_LEVELS
                          if counts.get(l, 0))
              + f" | age present for {n_age}/{len(pdf)}")

    print(f"\n✅ {rows_written} session(s) across {len(subjects_seen)} subject(s) → {args.out_dir}")
    if excluded:
        print("\n▸ completeness filter:")
        for e in excluded:
            print(f"   - {e}")
    if warnings:
        print("\n⚠ warnings:")
        for w in warnings:
            print(f"   - {w}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
