"""
olm_bids_builder.py
===================

Helper for the MeMoSLAP OLM (Object–Location Memory) project.

Converts one Presentation (.log) file into the three BIDS-style behavioural
files the dashboard expects:

    sub-XXX_ses-Y_task-OLM_acq-Z_RT_beh.tsv     (+ sidecar .json)
    sub-XXX_ses-Y_task-OLM_acq-Z_ACC_beh.tsv    (+ sidecar .json)
    sub-XXX_ses-Y_task-OLM_acq-Z_ACCBIN_beh.tsv (+ sidecar .json)

The conversion logic is a faithful port of Mohamed Abdelmotaleb's R script
(Behavioural_sham_sham.R, 2025), so the resulting dashboard numbers match
Abdelmotaleb et al., Brain and Behavior 2025 (doi:10.1002/brb3.70658):

    * learning accuracy climbs ~60% → ~85% across stages 1–4
    * learning RT (correct trials) ~1.1–1.3 s, decreasing across stages
    * learning trials slower than control trials at every stage
    * across-session ICCs: accuracy ≈ 0.80, RT ≈ 0.71

The previous pipeline got dramatically different RT ICCs (~0.06) because it
read absolute timestamps instead of Presentation's per-trial TTime and
attached the feedback filename instead of the stimulus filename. Both bugs
are fixed here.

Public API
----------
    parse_log(log_path)                  -> pandas.DataFrame (one row per trial)
    write_bids_files(trials_df, out_dir, sub, ses, acq)
    build_one(log_path, bids_root)       -> writes all six files for one run
    build_all(raw_logs_root, bids_root)  -> walks raw_logs/sub-*/ses-*/
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

# Presentation stores TTime in 1/10000 s units (0.1 ms). R script: RT / 10000.
TTIME_UNITS_PER_SECOND = 10_000

# Event-code regexes
_BLOCK_RE    = re.compile(r"block([1-6])")
_CTRL_RE     = re.compile(r"crt([12])")
_STAGE_RE    = re.compile(r"LS([1-4])")
_FEEDBACK_RE = re.compile(r"^(correct|incorrect|to late)\b", re.IGNORECASE)

# BIDS filename template — matches OLM_tree.txt layout
_FILENAME_TEMPLATE = "sub-{sub}_ses-{ses}_task-OLM_acq-{acq}_{suffix}_beh.{ext}"

# Filename parser for raw log files, e.g. sub-001_ses-3_task-OLM_acq-1_beh.log
_LOGNAME_RE = re.compile(
    r"sub-(?P<sub>[0-9A-Za-z]+)_ses-(?P<ses>[0-9A-Za-z]+)"
    r"_task-OLM_acq-(?P<acq>[0-9A-Za-z]+)_beh\.log$"
)


# ──────────────────────────────────────────────────────────────────────────────
# Log parsing
# ──────────────────────────────────────────────────────────────────────────────

def _read_raw_log(log_path: Path) -> pd.DataFrame:
    """Read a Presentation .log exactly the way the R script does.

    The file has three header lines (Scenario / Logfile written / blank),
    followed by a tab-separated table starting with "Subject\tTrial\t…".
    """
    df = pd.read_csv(
        log_path, sep="\t", skiprows=3,
        engine="python", on_bad_lines="skip",
        dtype=str,                     # we'll coerce numeric columns explicitly
    )
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"Event Type": "Event_Type"})
    # Numeric columns we actually use
    for col in ("Time", "TTime"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _tag_block(code: str) -> str | None:
    """block1…block6 → '1'…'6'; crt1/crt2 → 'c1'/'c2'."""
    if not isinstance(code, str):
        return None
    m = _BLOCK_RE.search(code)
    if m:
        return m.group(1)
    m = _CTRL_RE.search(code)
    if m:
        return f"c{m.group(1)}"
    return None


def _tag_stage(code: str) -> str | None:
    if not isinstance(code, str):
        return None
    m = _STAGE_RE.search(code)
    return m.group(1) if m else None


def parse_log(log_path: str | Path) -> pd.DataFrame:
    """Parse one Presentation .log into one row per trial.

    Returned columns
    ----------------
    onset              stimulus onset in seconds, from the first recorded Pulse 30
    response_time_s    stimulus-to-first-response interval in seconds (NaN if no resp)
    response_time_ms   same, in milliseconds
    trial_type         "learning" | "control"
    learning_stage     "LS1" | "LS2" | "LS3" | "LS4"
    block              "1".."6" for learning, "c1"/"c2" for control
    stimulus           filename of the house image actually presented
    response_port      Presentation port code (98, 97, …) or NaN
    accuracy           "correct" | "incorrect" | "to late"
    accuracy_binary    1 if correct, 0 otherwise; NaN if no feedback was recorded
    """
    log_path = Path(log_path)
    raw = _read_raw_log(log_path)

    # ── 1. Anchor t0 to the first Pulse 30 (first scanner trigger) ───────────
    pulses = raw.loc[(raw["Event_Type"] == "Pulse") & (raw["Code"].astype(str) == "30"),
                     "Time"]
    t0 = float(pulses.iloc[0]) if not pulses.empty else 0.0

    # ── 2. Drop "extra Pic Time" rows (R script does this) ───────────────────
    raw = raw[raw["Code"].astype(str) != "extra Pic Time"].reset_index(drop=True)

    # ── 3. Walk once; pair each stimulus with its Response and feedback ──────
    #
    # Event ordering inside one trial (after "extra Pic Time" rows are dropped):
    #     Picture   <stimulus>;blockN;LSM      ← opens the trial
    #     Port Input  98|97                    ← button press (port code)
    #     Response  1                          ← same clock as the Port Input;
    #                                            TTime = stimulus-to-press in 0.1 ms
    #     Picture   correct|incorrect|to late  ← feedback, closes the trial
    #
    # Scanner triggers (port 115 / Pulse 30) interleave these rows and must be
    # ignored. The button's port number is therefore carried by the Port Input
    # that *immediately precedes* the Response, not any earlier 115.
    trials: list[dict] = []
    current: dict | None = None          # trial currently being built
    pending_port: str | None = None      # most recent non-115 Port Input
    rt_ttime: float | None = None        # TTime of first Response after stimulus

    for row in raw.itertuples(index=False):
        code = str(row.Code) if row.Code is not None else ""
        et   = row.Event_Type

        # 3a. A stimulus row starts a new trial when it carries block/LS tags
        if et == "Picture" and (_BLOCK_RE.search(code) or _CTRL_RE.search(code)):
            # Close previous trial if somehow still open without feedback
            if current is not None:
                trials.append(current)
            stim = code.split(";")[0]
            current = {
                "onset_raw":      row.Time,
                "stimulus":       stim,
                "block":          _tag_block(code),
                "learning_stage": f"LS{_tag_stage(code)}" if _tag_stage(code) else None,
                "trial_type":     "control" if _tag_block(code) and
                                              _tag_block(code).startswith("c")
                                           else "learning",
                "response_time_s": float("nan"),
                "response_port":   None,
                "accuracy":        None,
            }
            pending_port = None
            rt_ttime = None
            continue

        # 3b. Remember the most recent non-115 Port Input (that's the button)
        if et == "Port Input" and current is not None and code != "115":
            pending_port = code

        # 3c. First Response after the stimulus fixes RT and consumes the port
        if et == "Response" and current is not None and rt_ttime is None:
            rt_ttime = row.TTime
            if pending_port is not None:
                current["response_port"] = pending_port

        # 3d. Feedback row closes the trial
        if et == "Picture" and _FEEDBACK_RE.match(code):
            if current is None:
                continue   # stray feedback (shouldn't happen in well-formed logs)
            verdict = _FEEDBACK_RE.match(code).group(1).lower()
            current["accuracy"] = "to late" if verdict == "to late" else verdict
            if rt_ttime is not None and pd.notna(rt_ttime):
                current["response_time_s"] = rt_ttime / TTIME_UNITS_PER_SECOND
            trials.append(current)
            current = None
            pending_port = None
            rt_ttime = None

    # Any trial left open at EOF gets appended as-is (usually none)
    if current is not None:
        trials.append(current)

    if not trials:
        return pd.DataFrame(columns=[
            "onset", "response_time_s", "response_time_ms",
            "trial_type", "learning_stage", "block",
            "stimulus", "response_port",
            "accuracy", "accuracy_binary",
        ])

    df = pd.DataFrame(trials)
    df["onset"]            = (df["onset_raw"] - t0) / 1000.0   # Time is ms units
    df["response_time_ms"] = df["response_time_s"] * 1000.0
    df["accuracy_binary"]  = df["accuracy"].map(
        {"correct": 1, "incorrect": 0, "to late": 0}
    )

    df = df.drop(columns=["onset_raw"])
    df = df[[
        "onset", "response_time_s", "response_time_ms",
        "trial_type", "learning_stage", "block",
        "stimulus", "response_port",
        "accuracy", "accuracy_binary",
    ]]
    return df


# ──────────────────────────────────────────────────────────────────────────────
# Writing BIDS files
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_na(x) -> str:
    """Format missing values as BIDS-standard 'n/a'."""
    return "n/a" if x is None or (isinstance(x, float) and pd.isna(x)) else x


def _rt_tsv(trials: pd.DataFrame) -> pd.DataFrame:
    """TSV for the _RT_ outcome. onset + duration + response_time_ms + context."""
    out = pd.DataFrame({
        "onset":             trials["onset"].round(3),
        "duration":          trials["response_time_s"].round(3),
        "response_time_ms":  trials["response_time_ms"].round(1),
        "trial_type":        trials["trial_type"],
        "learning_stage":    trials["learning_stage"],
        "stimulus":          trials["stimulus"],
        "response_port":     trials["response_port"],
    })
    return out


def _acc_tsv(trials: pd.DataFrame) -> pd.DataFrame:
    """TSV for the _ACC_ outcome (labelled correct/incorrect/to late)."""
    out = pd.DataFrame({
        "onset":             trials["onset"].round(3),
        "duration":          trials["response_time_s"].round(3),
        "accuracy":          trials["accuracy"],
        "trial_type":        trials["trial_type"],
        "learning_stage":    trials["learning_stage"],
        "stimulus":          trials["stimulus"],
        "response_port":     trials["response_port"],
    })
    return out


def _accbin_tsv(trials: pd.DataFrame) -> pd.DataFrame:
    """TSV for the _ACCBIN_ outcome (binary 1/0 — this is what ICC uses)."""
    out = pd.DataFrame({
        "onset":             trials["onset"].round(3),
        "duration":          trials["response_time_s"].round(3),
        "accuracy_binary":   trials["accuracy_binary"],
        "trial_type":        trials["trial_type"],
        "learning_stage":    trials["learning_stage"],
        "stimulus":          trials["stimulus"],
    })
    return out


# ── Sidecar JSONs (stable schema, shared across all subjects) ────────────────

_SIDECAR_RT = {
    "TaskName": "OLM",
    "TaskDescription": (
        "Reaction time per trial (stimulus onset → first button press), "
        "derived from Presentation TTime on the matched Response event. "
        "Object-Location Memory task (Abdelmotaleb et al. 2025)."
    ),
    "onset":            {"Description": "Stimulus onset in seconds from t0 "
                                        "(first Pulse 30).",
                         "Units": "seconds"},
    "duration":         {"Description": "Reaction time in seconds "
                                        "(stimulus onset to first button press).",
                         "Units": "seconds"},
    "response_time_ms": {"Description": "Reaction time from stimulus onset "
                                        "to first button press. Converted from "
                                        "Presentation 1/10000 s TTime units.",
                         "Units": "milliseconds"},
    "trial_type":       {"Description": "Trial condition.",
                         "Levels": {
                             "learning": "Object-location learning trial "
                                         "(Code contains block1..block6).",
                             "control":  "Right/left control trial "
                                         "(Code contains crt1/crt2)."}},
    "learning_stage":   {"Description": "Learning stage identifier LS1–LS4."},
    "stimulus":         {"Description": "Filename of the house image presented "
                                        "on the street map (NOT the feedback image)."},
    "response_port":    {"Description": "Presentation port code of the first "
                                        "participant button press. 115 is the "
                                        "scanner trigger and is never used here.",
                         "Levels": {"98": "Button 1 (yes)",
                                    "97": "Button 2 (no)",
                                    "n/a": "No response within 2.5 s"}},
}

_SIDECAR_ACC = {
    "TaskName": "OLM",
    "TaskDescription": "Trial accuracy (correct / incorrect / to late) "
                       "from the feedback code.",
    "onset":            _SIDECAR_RT["onset"],
    "duration":         _SIDECAR_RT["duration"],
    "accuracy":         {"Description": "Verdict reported by Presentation "
                                        "in the feedback event.",
                         "Levels": {"correct":   "Participant's yes/no matched",
                                    "incorrect": "Participant's yes/no mismatched",
                                    "to late":   "No response within 2.5 s"}},
    "trial_type":       _SIDECAR_RT["trial_type"],
    "learning_stage":   _SIDECAR_RT["learning_stage"],
    "stimulus":         _SIDECAR_RT["stimulus"],
    "response_port":    _SIDECAR_RT["response_port"],
}

_SIDECAR_ACCBIN = {
    "TaskName": "OLM",
    "TaskDescription": "Binary trial accuracy (1 = correct, 0 = incorrect or no response).",
    "onset":            _SIDECAR_RT["onset"],
    "duration":         _SIDECAR_RT["duration"],
    "accuracy_binary":  {"Description": "1 if the trial's feedback code started "
                                        "with 'correct', else 0. This is the "
                                        "column used for test–retest ICCs.",
                         "Levels": {"1": "correct", "0": "incorrect or missed"}},
    "trial_type":       _SIDECAR_RT["trial_type"],
    "learning_stage":   _SIDECAR_RT["learning_stage"],
    "stimulus":         _SIDECAR_RT["stimulus"],
}


@dataclass(frozen=True)
class _OutcomeSpec:
    suffix: str
    builder: callable
    sidecar: dict


_OUTCOMES: tuple[_OutcomeSpec, ...] = (
    _OutcomeSpec("RT",     _rt_tsv,     _SIDECAR_RT),
    _OutcomeSpec("ACC",    _acc_tsv,    _SIDECAR_ACC),
    _OutcomeSpec("ACCBIN", _accbin_tsv, _SIDECAR_ACCBIN),
)


def write_bids_files(
    trials: pd.DataFrame,
    out_dir: str | Path,
    sub: str,
    ses: str,
    acq: str,
) -> list[Path]:
    """Write the six files (3×tsv + 3×json) for one run and return their paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    for spec in _OUTCOMES:
        tsv = spec.builder(trials)
        tsv_path = out_dir / _FILENAME_TEMPLATE.format(
            sub=sub, ses=ses, acq=acq, suffix=spec.suffix, ext="tsv"
        )
        json_path = tsv_path.with_suffix(".json")

        # BIDS convention: missing values → "n/a"
        tsv.to_csv(tsv_path, sep="\t", index=False, na_rep="n/a")
        json_path.write_text(json.dumps(spec.sidecar, indent=2))

        written.extend([tsv_path, json_path])

    return written


# ──────────────────────────────────────────────────────────────────────────────
# High-level runners
# ──────────────────────────────────────────────────────────────────────────────

def _parse_log_filename(log_path: Path) -> tuple[str, str, str]:
    m = _LOGNAME_RE.search(log_path.name)
    if not m:
        raise ValueError(f"Unrecognised OLM log filename: {log_path.name}")
    return m.group("sub"), m.group("ses"), m.group("acq")


def build_one(log_path: str | Path, bids_root: str | Path) -> list[Path]:
    """Parse one log file and write its BIDS run files under
    ``bids_root/sub-XXX/ses-Y/``.
    """
    log_path  = Path(log_path)
    bids_root = Path(bids_root)

    sub, ses, acq = _parse_log_filename(log_path)
    trials = parse_log(log_path)
    out_dir = bids_root / f"sub-{sub}" / f"ses-{ses}"
    return write_bids_files(trials, out_dir, sub, ses, acq)


def build_all(
    raw_logs_root: str | Path,
    bids_root: str | Path,
    verbose: bool = True,
) -> dict[str, list[Path]]:
    """Walk raw_logs/sub-*/ses-*/ and rebuild bids_data/ for every log found.

    Returns a mapping ``{log_filename: [written_files]}``.
    """
    raw_logs_root = Path(raw_logs_root)
    bids_root     = Path(bids_root)

    results: dict[str, list[Path]] = {}
    logs = sorted(raw_logs_root.glob("sub-*/ses-*/*_task-OLM_*_beh.log"))

    if verbose:
        print(f"Found {len(logs)} log file(s) under {raw_logs_root}")

    for log_path in logs:
        try:
            written = build_one(log_path, bids_root)
            results[log_path.name] = written
            if verbose:
                print(f"  ✓ {log_path.name} → {len(written)} files")
        except Exception as exc:
            results[log_path.name] = []
            if verbose:
                print(f"  ✗ {log_path.name}: {exc!r}")

    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Rebuild OLM bids_data/ from raw Presentation logs."
    )
    parser.add_argument("raw_logs", help="Path to raw_logs/ root.")
    parser.add_argument("bids_data", help="Path to bids_data/ root (will be written into).")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-file progress output.")
    args = parser.parse_args()

    build_all(args.raw_logs, args.bids_data, verbose=not args.quiet)
