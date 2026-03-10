#!/usr/bin/env python3
"""
Generate Dummy Behavioral Experiment Projects
Creates 6 realistic projects with different paradigms.

Each subject-session produces SEPARATE TSV files per outcome measure:
  - *_RT_beh.tsv     : onset, duration, response_time_ms, trial_type, learning_stage, stimulus, response_port
  - *_ACC_beh.tsv    : onset, duration, accuracy, trial_type, learning_stage, stimulus
  - *_ACCBIN_beh.tsv : onset, duration, accuracy_binary, trial_type, learning_stage, stimulus

Each TSV is accompanied by a matching JSON sidecar.

Author: Behavioral_Exp_Hub
Date: 2024
"""

import pandas as pd
import numpy as np
from pathlib import Path
import random
import json

np.random.seed(42)
random.seed(42)


# ---------------------------------------------------------------------------
# Outcome-measure definitions (single source of truth)
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
            "onset":            {"Description": "Stimulus onset in seconds from t0 (first Pulse 30).", "Units": "seconds"},
            "duration":         {"Description": "RT converted to seconds (stimulus onset to button press).", "Units": "seconds"},
            "response_time_ms": {"Description": "Reaction time from stimulus onset to first button press.", "Units": "milliseconds"},
            "trial_type":       {"Description": "Trial condition.", "Levels": {"learning": "Learning trial", "control": "Control trial"}},
            "learning_stage":   {"Description": "Learning stage within the session (e.g. LS1-LS4)."},
            "stimulus":         {"Description": "Filename or path of the presented stimulus."},
            "response_port":    {
                "Description": "Hardware port of the participant response button.",
                "Levels": {"98": "Button 1 (OLMM)", "97": "Button 2 (OLMM)",
                           "99": "Button 1 (APPL)", "100": "Button 2 (APPL)", "n/a": "No response"}
            }
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
            "onset":          {"Description": "Stimulus onset in seconds from t0 (first Pulse 30).", "Units": "seconds"},
            "duration":       {"Description": "RT converted to seconds (stimulus onset to button press).", "Units": "seconds"},
            "accuracy":       {"Description": "Response accuracy.",
                               "Levels": {"correct": "Correct response", "incorrect": "Incorrect response", "n/a": "No feedback"}},
            "trial_type":     {"Description": "Trial condition.", "Levels": {"learning": "Learning trial", "control": "Control trial"}},
            "learning_stage": {"Description": "Learning stage within the session (e.g. LS1-LS4)."},
            "stimulus":       {"Description": "Filename or path of the presented stimulus."}
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
            "onset":           {"Description": "Stimulus onset in seconds from t0 (first Pulse 30).", "Units": "seconds"},
            "duration":        {"Description": "RT converted to seconds (stimulus onset to button press).", "Units": "seconds"},
            "accuracy_binary": {"Description": "Binary response accuracy.",
                                "Levels": {"1": "Correct", "0": "Incorrect", "n/a": "No feedback"}},
            "trial_type":      {"Description": "Trial condition.", "Levels": {"learning": "Learning trial", "control": "Control trial"}},
            "learning_stage":  {"Description": "Learning stage within the session (e.g. LS1-LS4)."},
            "stimulus":        {"Description": "Filename or path of the presented stimulus."}
        }
    }
}


def save_outcome_tsvs(df: pd.DataFrame, session_path: Path, stem: str, project_name: str):
    """
    Write one TSV + one JSON sidecar per outcome measure for a single session.

    File naming:
        <stem>_RT_beh.tsv     /  <stem>_RT_beh.json
        <stem>_ACC_beh.tsv    /  <stem>_ACC_beh.json
        <stem>_ACCBIN_beh.tsv /  <stem>_ACCBIN_beh.json
    """
    for meta in OUTCOME_METADATA.values():
        present_cols = [c for c in meta["columns"] if c in df.columns]
        out_df = df[present_cols].copy()

        tsv_name = f"{stem}_{meta['suffix']}_beh.tsv"
        out_df.to_csv(session_path / tsv_name, sep='\t', index=False, na_rep='n/a')

        sidecar = {
            "TaskName":        project_name,
            "TaskDescription": f"{meta['description']} ({project_name} project)"
        }
        sidecar.update(meta["column_descriptions"])

        with open(session_path / tsv_name.replace('.tsv', '.json'), 'w') as fh:
            json.dump(sidecar, fh, indent=2)


class DummyProjectGenerator:
    """Generates realistic dummy behavioral experiment projects."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

        self.paradigms = {
            'FACEMEM': {
                'name': 'Face Memory Recognition',
                'trial_types': ['study', 'test'],
                'n_stimuli_per_type': {'study': 30, 'test': 30},
                'trials_per_stimulus': 3,
                'learning_rt_range':  (800, 1800),
                'learning_acc_range': (0.70, 0.95),
                'control_rt_range':   (600, 1300),
                'control_acc_range':  (0.80, 0.98),
                'learning_stages': ['Phase1', 'Phase2', 'Phase3'],
                # Trait SD vs session-noise SD → target RT ICC ≈ 0.62, Acc ICC ≈ 0.55
                'rt_trait_sd':    0.10,   # stable between-subject speed difference
                'rt_noise_sd':    0.08,   # per-session noise on top of trait
                'acc_trait_sd':   0.08,   # stable between-subject accuracy difference
                'acc_noise_sd':   0.07,
            },
            'VERBGEN': {
                'name': 'Verb Generation Task',
                'trial_types': ['generate', 'repeat'],
                'n_stimuli_per_type': {'generate': 25, 'repeat': 15},
                'trials_per_stimulus': 5,
                'learning_rt_range':  (1200, 3000),
                'learning_acc_range': (0.60, 0.85),
                'control_rt_range':   (500, 1000),
                'control_acc_range':  (0.90, 1.0),
                'learning_stages': ['Run1', 'Run2', 'Run3', 'Run4'],
                # Target RT ICC ≈ 0.45, Acc ICC ≈ 0.50  (verb generation is noisy)
                'rt_trait_sd':    0.12,
                'rt_noise_sd':    0.10,
                'acc_trait_sd':   0.08,
                'acc_noise_sd':   0.07,
            },
            'SPATNAV': {
                'name': 'Spatial Navigation Learning',
                'trial_types': ['navigation', 'pointing'],
                'n_stimuli_per_type': {'navigation': 12, 'pointing': 12},
                'trials_per_stimulus': 6,
                'learning_rt_range':  (2000, 5000),
                'learning_acc_range': (0.55, 0.80),
                'control_rt_range':   (800, 1500),
                'control_acc_range':  (0.85, 0.98),
                'learning_stages': ['Trial1', 'Trial2', 'Trial3'],
                # Target RT ICC ≈ 0.65, Acc ICC ≈ 0.60
                'rt_trait_sd':    0.11,
                'rt_noise_sd':    0.08,
                'acc_trait_sd':   0.09,
                'acc_noise_sd':   0.07,
            },
            'NBACK': {
                'name': 'N-Back Working Memory',
                'trial_types': ['2back', '0back'],
                'n_stimuli_per_type': {'2back': 40, '0back': 20},
                'trials_per_stimulus': 3,
                'learning_rt_range':  (600, 1400),
                'learning_acc_range': (0.70, 0.92),
                'control_rt_range':   (400, 800),
                'control_acc_range':  (0.92, 1.0),
                'learning_stages': ['Block1', 'Block2', 'Block3', 'Block4'],
                # Target RT ICC ≈ 0.80, Acc ICC ≈ 0.75  (WM tasks are reliable)
                'rt_trait_sd':    0.14,
                'rt_noise_sd':    0.05,
                'acc_trait_sd':   0.12,
                'acc_noise_sd':   0.05,
            },
            'EMOTREG': {
                'name': 'Emotion Regulation Task',
                'trial_types': ['regulate', 'observe'],
                'n_stimuli_per_type': {'regulate': 30, 'observe': 20},
                'trials_per_stimulus': 4,
                'learning_rt_range':  (1500, 3500),
                'learning_acc_range': (0.65, 0.88),
                'control_rt_range':   (800, 1600),
                'control_acc_range':  (0.80, 0.95),
                'learning_stages': ['Run1', 'Run2', 'Run3'],
                # Target RT ICC ≈ 0.45, Acc ICC ≈ 0.50  (emotion tasks are noisy)
                'rt_trait_sd':    0.12,
                'rt_noise_sd':    0.10,
                'acc_trait_sd':   0.08,
                'acc_noise_sd':   0.07,
            },
            'STROOP': {
                'name': 'Stroop Color-Word Interference',
                'trial_types': ['incongruent', 'congruent'],
                'n_stimuli_per_type': {'incongruent': 30, 'congruent': 30},
                'trials_per_stimulus': 5,
                'learning_rt_range':  (700, 1500),
                'learning_acc_range': (0.75, 0.95),
                'control_rt_range':   (500, 900),
                'control_acc_range':  (0.90, 1.0),
                'learning_stages': ['Block1', 'Block2', 'Block3'],
                # Target RT ICC ≈ 0.85, Acc ICC ≈ 0.78  (Stroop is highly reliable)
                'rt_trait_sd':    0.15,
                'rt_noise_sd':    0.04,
                'acc_trait_sd':   0.13,
                'acc_noise_sd':   0.05,
            }
        }

    def _generate_participants(self, n: int = 50) -> pd.DataFrame:
        rows = []
        for i in range(1, n + 1):
            if random.random() < 0.85:
                age = np.random.normal(26, 4) if random.random() < 0.8 else np.random.normal(35, 6)
                rows.append({
                    'participant_id': f'sub-{i:03d}',
                    'sex': random.choices(['male', 'female', 'non binary'], weights=[0.42, 0.55, 0.03])[0],
                    'age': round(max(18.0, min(65.0, age)), 1)
                })
            else:
                rows.append({'participant_id': 'n/a', 'sex': 'n/a', 'age': 'n/a'})
        return pd.DataFrame(rows)

    def _generate_trials(self, paradigm: dict,
                         rt_trait: float = 1.0,
                         acc_trait: float = 0.0) -> pd.DataFrame:
        """Generate a combined trial DataFrame for one session.

        Parameters
        ----------
        rt_trait : float
            Stable subject-level speed multiplier (e.g. 0.90 = fast, 1.10 = slow).
            Applied to all RTs so the subject's mean persists across sessions.
        acc_trait : float
            Stable subject-level accuracy offset added to acc_prob before clipping.
            Positive → subject is generally more accurate; negative → less accurate.
        """
        learning_type = paradigm['trial_types'][0]
        control_type  = paradigm['trial_types'][1]
        rows          = []
        onset_time    = 0.0

        for stage in paradigm['learning_stages']:
            si = paradigm['learning_stages'].index(stage)

            for stim_idx in range(paradigm['n_stimuli_per_type'][learning_type]):
                for rep in range(paradigm['trials_per_stimulus']):
                    factor   = max(0.7, 1.0 - si * 0.15 - rep * 0.05)
                    # rt_trait scales the base RT — stable individual differences in speed
                    rt       = np.random.uniform(*paradigm['learning_rt_range']) * factor * rt_trait
                    acc_prob = min(0.98, np.random.uniform(*paradigm['learning_acc_range'])
                                   + si * 0.08 + rep * 0.02 + acc_trait)
                    acc_prob = max(0.02, acc_prob)
                    correct  = int(random.random() < acc_prob)
                    duration = rt / 1000.0
                    rows.append(dict(
                        onset=round(onset_time, 3), duration=round(duration, 3),
                        response_time_ms=round(rt, 1),
                        trial_type=learning_type, learning_stage=stage,
                        stimulus=f'{learning_type}/STIM_{stim_idx:03d}.jpg',
                        response_port=random.choice([99, 100]),
                        accuracy='correct' if correct else 'incorrect',
                        accuracy_binary=correct
                    ))
                    onset_time += duration + np.random.uniform(2, 4)

            for stim_idx in range(paradigm['n_stimuli_per_type'][control_type]):
                for rep in range(paradigm['trials_per_stimulus']):
                    rt       = np.random.uniform(*paradigm['control_rt_range']) * rt_trait
                    acc_prob = min(0.98, np.random.uniform(*paradigm['control_acc_range']) + acc_trait)
                    acc_prob = max(0.02, acc_prob)
                    correct  = int(random.random() < acc_prob)
                    duration = rt / 1000.0
                    rows.append(dict(
                        onset=round(onset_time, 3), duration=round(duration, 3),
                        response_time_ms=round(rt, 1),
                        trial_type=control_type, learning_stage=stage,
                        stimulus=f'{control_type}/STIM_{stim_idx:03d}.jpg',
                        response_port=random.choice([99, 100]),
                        accuracy='correct' if correct else 'incorrect',
                        accuracy_binary=correct
                    ))
                    onset_time += duration + np.random.uniform(2, 4)

        return pd.DataFrame(rows)

    def generate_project(self, project_name: str, n_subjects: int = 50):
        print(f"\nGenerating project: {project_name}")

        paradigm     = self.paradigms[project_name]
        project_path = self.base_path / "Projects" / project_name
        project_path.mkdir(parents=True, exist_ok=True)

        participants = self._generate_participants(n_subjects)
        participants.to_csv(project_path / "participants.tsv", sep='\t', index=False)
        print(f"  Created participants.tsv  ({len(participants)} entries)")

        valid   = participants[participants['participant_id'] != 'n/a']
        n_valid = len(valid)
        n_files = 0

        # ── Stable subject-level traits ──────────────────────────────────────
        # Each subject gets a fixed speed multiplier (rt_trait) and accuracy
        # offset (acc_trait) drawn from a Normal distribution. These represent
        # genuine individual differences that persist across sessions, which is
        # what drives test-retest ICC.
        #
        # The ratio of trait_sd to session_noise_sd controls the ICC:
        #   ICC ≈ trait_var / (trait_var + noise_var)
        #
        rt_trait_sd   = paradigm.get('rt_trait_sd',  0.10)
        rt_noise_sd   = paradigm.get('rt_noise_sd',  0.08)
        acc_trait_sd  = paradigm.get('acc_trait_sd', 0.08)
        acc_noise_sd  = paradigm.get('acc_noise_sd', 0.07)

        rt_traits  = np.random.normal(1.0, rt_trait_sd,  n_valid)   # speed multiplier per subject
        acc_traits = np.random.normal(0.0, acc_trait_sd, n_valid)   # accuracy offset per subject

        for idx, (_, row) in enumerate(valid.iterrows()):
            sub_id    = row['participant_id'].replace('sub-', '')
            rt_trait  = rt_traits[idx]
            acc_trait = acc_traits[idx]

            for ses in range(1, 3):
                ses_path = project_path / "bids_data" / f"sub-{sub_id}" / f"ses-{ses}"
                ses_path.mkdir(parents=True, exist_ok=True)

                # Add small session-level noise on top of the stable trait so
                # sessions aren't identical, but the subject's rank is preserved
                rt_ses  = rt_trait  + np.random.normal(0, rt_noise_sd)
                acc_ses = acc_trait + np.random.normal(0, acc_noise_sd)

                df = self._generate_trials(paradigm, rt_trait=rt_ses, acc_trait=acc_ses)
                df['duration'] = (df['response_time_ms'] / 1000.0).round(3)

                acq  = random.randint(1, 3)
                stem = f"sub-{sub_id}_ses-{ses}_task-{project_name}_acq-{acq}"
                save_outcome_tsvs(df, ses_path, stem, project_name)
                n_files += 3

        # Expected ICC given trait/noise SDs (analytical approximation)
        expected_icc_rt  = rt_trait_sd**2  / (rt_trait_sd**2  + rt_noise_sd**2)
        expected_icc_acc = acc_trait_sd**2 / (acc_trait_sd**2 + acc_noise_sd**2)

        print(f"  Created {n_files} TSV files  (RT / ACC / ACCBIN per session, each with JSON sidecar)")
        print(f"  Paradigm  : {paradigm['name']}")
        print(f"  Conditions: {paradigm['trial_types'][0]}  vs  {paradigm['trial_types'][1]}")
        print(f"  Expected RT ICC  ≈ {expected_icc_rt:.2f}  (trait_sd={rt_trait_sd}, noise_sd={rt_noise_sd})")
        print(f"  Expected Acc ICC ≈ {expected_icc_acc:.2f}  (trait_sd={acc_trait_sd}, noise_sd={acc_noise_sd})")

    def generate_all_projects(self):
        print("=" * 70)
        print("Generating 6 Dummy Behavioral Experiment Projects")
        print("Note: APPL and OLMM are real projects and will not be overwritten")
        print("=" * 70)
        print()
        print("Per-session file naming convention:")
        print("  <sub>_<ses>_task-<PROJ>_acq-<N>_RT_beh.tsv")
        print("    columns: onset | duration | response_time_ms | trial_type | learning_stage | stimulus | response_port")
        print()
        print("  <sub>_<ses>_task-<PROJ>_acq-<N>_ACC_beh.tsv")
        print("    columns: onset | duration | accuracy | trial_type | learning_stage | stimulus")
        print()
        print("  <sub>_<ses>_task-<PROJ>_acq-<N>_ACCBIN_beh.tsv")
        print("    columns: onset | duration | accuracy_binary | trial_type | learning_stage | stimulus")
        print()
        print("  (each .tsv has a matching .json sidecar)")
        print()

        for pname in self.paradigms:
            n = random.randint(50, 80) if pname in ['FACEMEM', 'VERBGEN'] else random.randint(30, 60)
            self.generate_project(pname, n_subjects=n)

        print("\n" + "=" * 70)
        print("Project Generation Complete!")
        print("=" * 70)
        print("\nProject Summary:")
        print("-" * 70)
        for pname, p in self.paradigms.items():
            print(f"\n{pname}: {p['name']}")
            print(f"  Conditions : {p['trial_types'][0]}  vs  {p['trial_types'][1]}")
            print(f"  Expected RT: {p['trial_types'][0]} ~{p['learning_rt_range'][0]}-{p['learning_rt_range'][1]} ms")
            print(f"               {p['trial_types'][1]} ~{p['control_rt_range'][0]}-{p['control_rt_range'][1]} ms")


def main():
    import sys
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/Git_repository/BEEHub"
    DummyProjectGenerator(base_path).generate_all_projects()
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("\n1. Organize raw log files:")
    print("   python 01_organize_log_files.py --source-dir <DATA_DIR>")
    print("\n2. Convert log files to BIDS TSVs:")
    print("   python 02_convert_to_bids.py")
    print("\n3. Compute reliability metrics:")
    print("   python 03_compute_reliability.py\n")


if __name__ == "__main__":
    main()
