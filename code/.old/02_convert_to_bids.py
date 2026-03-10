#!/usr/bin/env python3
"""
Script 2: Convert Behavioral Log Files to BIDS TSV Format

Produces THREE separate TSV files per session (one per outcome measure):

  *_RT_beh.tsv
    columns: onset | duration | response_time_ms | trial_type | learning_stage | stimulus | response_port

  *_ACC_beh.tsv
    columns: onset | duration | accuracy | trial_type | learning_stage | stimulus

  *_ACCBIN_beh.tsv
    columns: onset | duration | accuracy_binary | trial_type | learning_stage | stimulus

Each TSV is accompanied by a matching JSON sidecar.

Parsing rules:
  - t0 = first Pulse 30 event
  - Learning trials: 'block' in stimulus code
  - Control trials:  'crt' in stimulus code
  - Response:        Port Input 99 / 100 (APPL) or 98 / 97 (OLMM)
  - Accuracy:        from subsequent feedback picture event

Author: Behavioral_Exp_Hub
Date: 2024
"""

import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Outcome-measure definitions (single source of truth, shared with generator)
# ---------------------------------------------------------------------------

OUTCOME_METADATA = {
    "RT": {
        "suffix": "RT",
        "columns": [
            "onset", "duration", "response_time_ms",
            "trial_type", "learning_stage", "stimulus", "response_port"
        ],
        "description": "Reaction time (RT) per trial — time from stimulus onset to first button press.",
        "column_descriptions": {
            "onset":            {"Description": "Stimulus onset in seconds from t0 (first Pulse 30). "
                                                "Presentation software stores times in 1/10000 s units.",
                                 "Units": "seconds"},
            "duration":         {"Description": "RT converted to seconds (stimulus onset to button press).",
                                 "Units": "seconds"},
            "response_time_ms": {"Description": "Reaction time from stimulus onset to first button press. "
                                                "Converted from Presentation 1/10000 s units.",
                                 "Units": "milliseconds"},
            "trial_type":       {"Description": "Trial condition.",
                                 "Levels": {"learning": "Learning trial (contains 'block' in code)",
                                            "control":  "Control trial (contains 'crt' in code)"}},
            "learning_stage":   {"Description": "Learning stage identifier (LS1-LS4)."},
            "stimulus":         {"Description": "Stimulus filename presented."},
            "response_port":    {"Description": "Port number of participant response.",
                                 "Levels": {"98": "Button 1 (OLMM)", "97": "Button 2 (OLMM)",
                                            "99": "Button 1 (APPL)", "100": "Button 2 (APPL)",
                                            "n/a": "No response recorded"}}
        }
    },
    "ACC": {
        "suffix": "ACC",
        "columns": [
            "onset", "duration", "accuracy",
            "trial_type", "learning_stage", "stimulus"
        ],
        "description": "Accuracy (ACC) per trial: correct / incorrect / n/a.",
        "column_descriptions": {
            "onset":          {"Description": "Stimulus onset in seconds from t0 (first Pulse 30).",
                               "Units": "seconds"},
            "duration":       {"Description": "RT converted to seconds (stimulus onset to button press).",
                               "Units": "seconds"},
            "accuracy":       {"Description": "Response accuracy from feedback trial.",
                               "Levels": {"correct": "Correct response",
                                          "incorrect": "Incorrect response (Falsch)",
                                          "n/a": "No feedback available"}},
            "trial_type":     {"Description": "Trial condition.",
                               "Levels": {"learning": "Learning trial", "control": "Control trial"}},
            "learning_stage": {"Description": "Learning stage identifier (LS1-LS4)."},
            "stimulus":       {"Description": "Stimulus filename presented."}
        }
    },
    "ACCBIN": {
        "suffix": "ACCBIN",
        "columns": [
            "onset", "duration", "accuracy_binary",
            "trial_type", "learning_stage", "stimulus"
        ],
        "description": "Binary-coded accuracy (ACCBIN) per trial: 1 = correct, 0 = incorrect.",
        "column_descriptions": {
            "onset":           {"Description": "Stimulus onset in seconds from t0 (first Pulse 30).",
                                "Units": "seconds"},
            "duration":        {"Description": "RT converted to seconds (stimulus onset to button press).",
                                "Units": "seconds"},
            "accuracy_binary": {"Description": "Binary response accuracy from feedback trial.",
                                "Levels": {"1": "Correct", "0": "Incorrect", "n/a": "No feedback"}},
            "trial_type":      {"Description": "Trial condition.",
                                "Levels": {"learning": "Learning trial", "control": "Control trial"}},
            "learning_stage":  {"Description": "Learning stage identifier (LS1-LS4)."},
            "stimulus":        {"Description": "Stimulus filename presented."}
        }
    }
}


def save_outcome_tsvs(df: pd.DataFrame, out_dir: Path, stem: str, project_name: str):
    """
    Write one TSV + one JSON sidecar per outcome measure.

    File naming:
        <stem>_RT_beh.tsv     /  <stem>_RT_beh.json
        <stem>_ACC_beh.tsv    /  <stem>_ACC_beh.json
        <stem>_ACCBIN_beh.tsv /  <stem>_ACCBIN_beh.json
    """
    for meta in OUTCOME_METADATA.values():
        present_cols = [c for c in meta["columns"] if c in df.columns]
        out_df = df[present_cols].copy()

        tsv_name = f"{stem}_{meta['suffix']}_beh.tsv"
        out_df.to_csv(out_dir / tsv_name, sep='\t', index=False, na_rep='n/a')
        logger.info(f"  Wrote {tsv_name}")

        sidecar = {
            "TaskName":        project_name,
            "TaskDescription": f"{meta['description']} ({project_name} project)"
        }
        sidecar.update(meta["column_descriptions"])

        with open(out_dir / tsv_name.replace('.tsv', '.json'), 'w') as fh:
            json.dump(sidecar, fh, indent=2)


# ---------------------------------------------------------------------------
# Log file parser
# ---------------------------------------------------------------------------

class LogFileParser:
    """Parser for Presentation behavioral log files."""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.filename      = Path(log_file_path).name
        self.t0            = None  # first Pulse 30 timestamp

    def parse(self) -> pd.DataFrame:
        logger.info(f"Parsing: {self.filename}")

        with open(self.log_file_path, 'r', encoding='utf-8', errors='replace') as fh:
            lines = fh.readlines()

        self.t0 = self._find_t0(lines)
        if self.t0 is None:
            logger.error("Could not find t0 (Pulse 30)")
            return pd.DataFrame()
        logger.info(f"  t0 = {self.t0}")

        events       = self._parse_events(lines)
        measurements = self._extract_measurements(events)
        df           = pd.DataFrame(measurements)
        logger.info(f"  Extracted {len(df)} trials from {self.filename}")
        return df

    def _find_t0(self, lines):
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) >= 5:
                try:
                    if parts[2] == 'Pulse' and parts[3] == '30':
                        return int(parts[4])
                except (ValueError, IndexError):
                    pass
        return None

    def _parse_events(self, lines):
        events = []
        for line in lines:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            if parts[0] in ['Subject', 'Scenario', 'Logfile'] or not line.strip():
                continue
            try:
                events.append({
                    'subject':    parts[0],
                    'trial':      int(parts[1]) if parts[1].isdigit() else None,
                    'event_type': parts[2],
                    'code':       parts[3],
                    'time':       int(parts[4]),
                    'ttime':      int(parts[5]) if len(parts) > 5 and parts[5].strip() else 0
                })
            except (ValueError, IndexError):
                pass
        return events

    def _extract_measurements(self, events):
        measurements = []
        i = 0
        while i < len(events):
            ev = events[i]
            if ev['event_type'] == 'Picture':
                code       = ev['code']
                skip_words = ['bubbles/', 'fix', 'extra pic', 'to late', 'hello',
                              'intro', 'korrekt', 'falsch', 'correct', 'incorrect']
                if any(x in code.lower() for x in skip_words):
                    i += 1
                    continue
                if ';' not in code or 'LS' not in code.upper():
                    i += 1
                    continue
                if 'block' in code.lower() or 'crt' in code.lower():
                    m = self._parse_measurement(events, i)
                    if m:
                        measurements.append(m)
            i += 1
        return measurements

    def _parse_measurement(self, events, start_idx) -> Optional[dict]:
        stimulus_event = events[start_idx]
        code           = stimulus_event['code']
        parts          = code.split(';')

        if len(parts) == 3:
            # OLMM format: filename;block_info;LS
            stimulus       = parts[0].strip()
            block_info     = parts[1].strip()
            learning_stage = parts[2].upper().strip()
        elif len(parts) >= 5:
            # APPL format: path/file;word1;word2;c_or_i;block_info;LS
            stimulus       = parts[0].strip()
            block_info     = parts[4].strip() if len(parts) > 4 else ''
            learning_stage = parts[5].upper().strip() if len(parts) > 5 else ''
        else:
            return None

        if   'control/'  in stimulus.lower():  trial_type = 'control'
        elif 'learning/' in stimulus.lower():  trial_type = 'learning'
        elif 'crt'   in block_info.lower():    trial_type = 'control'
        elif 'block' in block_info.lower():    trial_type = 'learning'
        else:                                  return None

        # Onset — Presentation time units are 1/10000 s
        onset_sec = (stimulus_event['time'] - self.t0) / 10000.0

        # Response (Port Input)
        response_time = None
        response_port = None
        for j in range(start_idx + 1, min(start_idx + 15, len(events))):
            ev = events[j]
            if ev['event_type'] == 'Picture':
                c = ev['code']
                if ';block' in c.lower() or ';crt' in c.lower():
                    break
            if ev['event_type'] == 'Port Input' and ev['code'] in ['98', '97', '99', '100']:
                response_time = (ev['time'] - stimulus_event['time']) / 10.0  # -> ms
                response_port = ev['code']
                break

        # Accuracy from feedback picture
        accuracy        = 'n/a'
        accuracy_binary = 'n/a'
        for j in range(start_idx + 1, min(start_idx + 15, len(events))):
            ev = events[j]
            if ev['event_type'] != 'Picture':
                continue
            ev_code = ev['code']
            if ';block' in ev_code.lower() or ';crt' in ev_code.lower():
                break
            if ';' in ev_code:
                fb_parts = ev_code.split(';')
                if len(fb_parts) >= 2:
                    fb_type = fb_parts[0].lower()
                    fb_stim = fb_parts[1]
                    if fb_stim == stimulus or fb_stim in stimulus:
                        if fb_type == 'correct':
                            accuracy, accuracy_binary = 'correct', 1
                        elif fb_type in ['incorrect', 'falsch']:
                            accuracy, accuracy_binary = 'incorrect', 0
                        break
            if ev_code.lower().startswith('korrekt'):
                accuracy, accuracy_binary = 'correct', 1
                break
            elif ev_code.lower().startswith('falsch'):
                accuracy, accuracy_binary = 'incorrect', 0
                break

        return {
            'onset':            round(onset_sec, 3),
            'duration':         round(response_time / 1000.0, 3) if response_time is not None else 'n/a',
            'response_time_ms': round(response_time, 1)          if response_time is not None else 'n/a',
            'trial_type':       trial_type,
            'learning_stage':   learning_stage,
            'stimulus':         stimulus,
            'response_port':    response_port if response_port else 'n/a',
            'accuracy':         accuracy,
            'accuracy_binary':  accuracy_binary,
        }


# ---------------------------------------------------------------------------
# Per-project processing
# ---------------------------------------------------------------------------

def _bids_location(log_file: Path) -> Tuple[str, str]:
    """Extract sub-XXX and ses-Y from the log file path or filename."""
    subject_dir = session_dir = None
    for i, part in enumerate(log_file.parts):
        if part.startswith('sub-'):
            subject_dir = part
            if i + 1 < len(log_file.parts) and log_file.parts[i + 1].startswith('ses-'):
                session_dir = log_file.parts[i + 1]
            break

    if not subject_dir or not session_dir:
        sub_m = re.search(r'(sub-[A-Za-z0-9]+)', log_file.name)
        ses_m = re.search(r'(ses-[A-Za-z0-9]+)', log_file.name)
        subject_dir = sub_m.group(1) if sub_m else 'sub-unknown'
        session_dir = ses_m.group(1) if ses_m else 'ses-unknown'

    return subject_dir, session_dir


def convert_log_to_bids(log_file: str, bids_root: str, project_name: str) -> bool:
    """Parse one log file and write RT / ACC / ACCBIN TSVs + JSON sidecars."""
    try:
        df = LogFileParser(log_file).parse()
        if df.empty:
            logger.warning(f"No data extracted from {Path(log_file).name}")
            return False

        log_path                 = Path(log_file)
        subject_dir, session_dir = _bids_location(log_path)
        out_dir                  = Path(bids_root) / subject_dir / session_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        stem = log_path.stem
        if stem.endswith('_beh'):
            stem = stem[:-4]

        save_outcome_tsvs(df, out_dir, stem, project_name)
        return True

    except Exception as exc:
        import traceback
        logger.error(f"Error converting {Path(log_file).name}: {exc}")
        logger.error(traceback.format_exc())
        return False


def process_project(projects_dir: str, project_name: str):
    """Convert all log files for a single project."""
    project_path  = Path(projects_dir) / project_name
    raw_logs_path = project_path / "raw_logs"
    bids_root     = project_path / "bids_data"

    if not raw_logs_path.exists():
        logger.error(f"Raw logs directory not found: {raw_logs_path}")
        return

    bids_root.mkdir(parents=True, exist_ok=True)
    log_files = list(raw_logs_path.rglob("*.log"))

    if not log_files:
        logger.warning(f"No log files found in {raw_logs_path}")
        return

    logger.info(f"\nProcessing project: {project_name}  ({len(log_files)} log files)")
    ok = sum(convert_log_to_bids(str(lf), str(bids_root), project_name) for lf in log_files)
    logger.info(f"Converted {ok}/{len(log_files)} files  ->  {ok * 3} TSV files written")

    desc = {
        "Name":        f"{project_name} Behavioral Dataset",
        "BIDSVersion": "1.6.0",
        "DatasetType": "raw",
        "Authors":     ["Behavioral_Exp_Hub Contributors"],
        "GeneratedBy": [{
            "Name":        "Behavioral_Exp_Hub Conversion Pipeline",
            "Version":     "3.0",
            "Description": "Produces one TSV per outcome measure (RT / ACC / ACCBIN) with JSON sidecars.",
            "CodeURL":     "https://github.com/yourusername/BEHub"
        }]
    }
    with open(bids_root / "dataset_description.json", 'w') as fh:
        json.dump(desc, fh, indent=2)
    logger.info("Created dataset_description.json")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Convert behavioral log files to per-outcome-measure BIDS TSV files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output per session
------------------
  <sub>_<ses>_task-<PROJ>_acq-<N>_RT_beh.tsv
    onset | duration | response_time_ms | trial_type | learning_stage | stimulus | response_port

  <sub>_<ses>_task-<PROJ>_acq-<N>_ACC_beh.tsv
    onset | duration | accuracy | trial_type | learning_stage | stimulus

  <sub>_<ses>_task-<PROJ>_acq-<N>_ACCBIN_beh.tsv
    onset | duration | accuracy_binary | trial_type | learning_stage | stimulus

  (each .tsv has a matching .json sidecar)

Examples
--------
  python 02_convert_to_bids.py --project-name OLMM
  python 02_convert_to_bids.py
  python 02_convert_to_bids.py --projects-dir /path/to/Projects
        """
    )

    script_dir           = Path(__file__).parent
    default_projects_dir = script_dir.parent / "Projects"

    parser.add_argument('--projects-dir',  type=str, default=str(default_projects_dir),
                        help=f'Base directory containing project folders (default: {default_projects_dir})')
    parser.add_argument('--project-name',  type=str,
                        help='Specific project to process (all projects if omitted)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    print("\n" + "=" * 70)
    print("BEHAVIORAL LOG -> BIDS CONVERTER  (per-outcome TSV mode)")
    print("=" * 70)
    print("\nOutput per session:")
    print("  *_RT_beh.tsv     <- response_time_ms  (+ response_port)")
    print("  *_ACC_beh.tsv    <- accuracy           (correct / incorrect / n/a)")
    print("  *_ACCBIN_beh.tsv <- accuracy_binary    (0 / 1)")
    print("  (+ matching .json sidecars)")
    print()

    projects_path = Path(args.projects_dir)
    if not projects_path.exists():
        logger.error(f"Projects directory not found: {args.projects_dir}")
        return

    projects = [args.project_name] if args.project_name else [d.name for d in projects_path.iterdir() if d.is_dir()]
    logger.info(f"Projects to process: {', '.join(projects)}")

    for project in projects:
        process_project(args.projects_dir, project)

    print("\n" + "=" * 70)
    print("BIDS conversion complete!")
    print("\nNext step:  python 03_compute_reliability.py")
    print("=" * 70)


if __name__ == "__main__":
    main()
