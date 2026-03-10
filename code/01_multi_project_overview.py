#!/usr/bin/env python3
"""
Multi-Project Overview Dashboard
Creates comprehensive graphical overview with violin plots, scatter plots, and radar charts
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats
from typing import Dict, List, Tuple
from pathlib import Path
import warnings
import sys
warnings.filterwarnings('ignore')

class ProjectOverviewGenerator:
    """Generates comprehensive overview dashboard for all projects"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
        # Project descriptions and characteristics
        self.project_descriptions = {
            'APPL': {
                'full_name': 'Associative Pseudoword Learning',
                'description': 'Language learning task with novel pseudoword associations',
                'modality': 'linguistic',
                'cognitive_domain': 'memory',
                'task_type': 'learning',
                'difficulty': 'moderate'
            },
            'OLMM': {
                'full_name': 'Object Memory Location Mapping',
                'description': 'Visual-spatial memory task with object-location associations',
                'modality': 'visual-spatial',
                'cognitive_domain': 'memory',
                'task_type': 'encoding-retrieval',
                'difficulty': 'moderate'
            },
            'FACEMEM': {
                'full_name': 'Face Memory Recognition',
                'description': 'Face recognition and episodic memory task',
                'modality': 'visual',
                'cognitive_domain': 'memory',
                'task_type': 'recognition',
                'difficulty': 'easy-moderate'
            },
            'VERBGEN': {
                'full_name': 'Verb Generation Task',
                'description': 'Semantic retrieval and verb generation from nouns',
                'modality': 'linguistic',
                'cognitive_domain': 'semantic_memory',
                'task_type': 'generation',
                'difficulty': 'hard'
            },
            'SPATNAV': {
                'full_name': 'Spatial Navigation Learning',
                'description': 'Virtual navigation and spatial orientation task',
                'modality': 'visual-spatial',
                'cognitive_domain': 'spatial_cognition',
                'task_type': 'navigation',
                'difficulty': 'very_hard'
            },
            'NBACK': {
                'full_name': 'N-Back Working Memory',
                'description': 'Working memory task with n-back manipulation',
                'modality': 'visual',
                'cognitive_domain': 'working_memory',
                'task_type': 'monitoring',
                'difficulty': 'moderate-hard'
            },
            'EMOTREG': {
                'full_name': 'Emotion Regulation Task',
                'description': 'Cognitive reappraisal of emotional stimuli',
                'modality': 'visual-emotional',
                'cognitive_domain': 'emotion_regulation',
                'task_type': 'regulation',
                'difficulty': 'hard'
            },
            'STROOP': {
                'full_name': 'Stroop Color-Word Interference',
                'description': 'Classic cognitive control and interference task',
                'modality': 'visual',
                'cognitive_domain': 'cognitive_control',
                'task_type': 'interference',
                'difficulty': 'moderate'
            }
        }
        
        # Fixed outcome-file suffixes and their primary columns.
        # Each outcome has its own dedicated TSV: *_RT_beh.tsv, *_ACC_beh.tsv, *_ACCBIN_beh.tsv
        self.outcome_files = {
            'RT':     {'suffix': '_RT_beh.tsv',     'column': 'response_time_ms'},
            'ACC':    {'suffix': '_ACC_beh.tsv',     'column': 'accuracy'},
            'ACCBIN': {'suffix': '_ACCBIN_beh.tsv',  'column': 'accuracy_binary'},
        }
    
    def find_projects(self) -> List[str]:
        """Find all project folders"""
        projects_path = self.base_path / "Projects"
        if not projects_path.exists():
            return []
        
        project_folders = [d.name for d in projects_path.iterdir() if d.is_dir()]
        print(f"Found projects: {project_folders}")
        return project_folders
    
    def load_outcome_data(self, project_name: str, outcome: str) -> pd.DataFrame:
        """
        Load all TSV files for a specific outcome measure (RT, ACC, or ACCBIN).
        Scans flat bids_data/ and the BIDS sub-*/ses-*/ hierarchy.
        Adds subject_id and session columns from filename BIDS entities.
        """
        bids_path = self.base_path / "Projects" / project_name / "bids_data"
        if not bids_path.exists():
            return pd.DataFrame()

        suffix = self.outcome_files[outcome]['suffix']
        all_data = []

        # Flat files directly in bids_data/
        for f in bids_path.glob(f"*{suffix}"):
            df = self._load_outcome_file(f)
            if not df.empty:
                all_data.append(df)

        # BIDS hierarchy: sub-*/ses-*/
        for subject_dir in bids_path.glob("sub-*"):
            if not subject_dir.is_dir():
                continue
            for session_dir in subject_dir.glob("ses-*"):
                if not session_dir.is_dir():
                    continue
                for f in session_dir.glob(f"*{suffix}"):
                    df = self._load_outcome_file(f)
                    if not df.empty:
                        all_data.append(df)

        return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

    def _load_outcome_file(self, filepath: Path) -> pd.DataFrame:
        """Load a single outcome TSV and attach subject_id / session from the filename."""
        file_info = {}
        for part in filepath.name.split('_'):
            if '-' in part:
                key, value = part.split('-', 1)
                file_info[key] = value
        try:
            df = pd.read_csv(filepath, sep='\t')
            df['subject_id'] = file_info.get('sub', 'unknown')
            df['session']    = file_info.get('ses', 'unknown')
            return df
        except Exception:
            return pd.DataFrame()

    def load_participants_data(self, project_name: str) -> pd.DataFrame:
        """Load participants.tsv file"""
        participants_file = self.base_path / "Projects" / project_name / "participants.tsv"
        
        if not participants_file.exists():
            return pd.DataFrame()
        
        df = pd.read_csv(participants_file, sep='\t')
        df = df[df['participant_id'] != 'n/a'].copy()
        df['age'] = pd.to_numeric(df['age'], errors='coerce')
        
        return df
    
    def calculate_icc(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Calculate ICC(3,1) — two-way mixed model, absolute agreement, single measures.
        Session effects (column variance) are partialled out of the error term but
        are NOT included in the denominator, making this a consistency estimate.
        Formula: ICC(3,1) = (MSr - MSe) / (MSr + (k-1)*MSe)
        """
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        
        n = len(data1)
        k = 2
        
        data = np.column_stack([data1, data2])
        grand_mean = np.mean(data)
        row_means = np.mean(data, axis=1)
        col_means = np.mean(data, axis=0)
        
        ss_total = np.sum((data - grand_mean) ** 2)
        ss_rows  = k * np.sum((row_means - grand_mean) ** 2)
        ss_cols  = n * np.sum((col_means - grand_mean) ** 2)
        ss_error = ss_total - ss_rows - ss_cols
        
        ms_rows  = ss_rows  / (n - 1)
        ms_error = ss_error / ((n - 1) * (k - 1))
        
        icc = (ms_rows - ms_error) / (ms_rows + (k - 1) * ms_error)
        return icc
    
    def analyze_project(self, project_name: str) -> Dict:
        """Comprehensive analysis of a project"""
        print(f"\nAnalyzing project: {project_name}")
        
        # Load data
        participants = self.load_participants_data(project_name)

        # Load each outcome from its dedicated TSV
        rt_data   = self.load_outcome_data(project_name, 'RT')      # response_time_ms
        acc_data  = self.load_outcome_data(project_name, 'ACC')     # accuracy (correct/incorrect)
        accbin_data = self.load_outcome_data(project_name, 'ACCBIN') # accuracy_binary (0/1)

        # At least one outcome must be present
        if participants.empty or (rt_data.empty and acc_data.empty):
            print(f"  No valid data for {project_name}")
            return None

        rt_col     = 'response_time_ms' if not rt_data.empty else None
        acc_col    = 'accuracy_binary'  if not accbin_data.empty else None  # use binary for stats

        # Get project description
        proj_desc = self.project_descriptions.get(project_name, {
            'full_name': project_name,
            'description': 'Behavioral task',
            'modality': 'unknown',
            'cognitive_domain': 'unknown',
            'task_type': 'unknown',
            'difficulty': 'unknown'
        })
        
        # Demographics
        demographics = {
            'n_participants': len(participants),
            'age_mean': float(participants['age'].mean()) if not participants['age'].isna().all() else None,
            'age_std':  float(participants['age'].std())  if not participants['age'].isna().all() else None,
            'age_min':  float(participants['age'].min())  if not participants['age'].isna().all() else None,
            'age_max':  float(participants['age'].max())  if not participants['age'].isna().all() else None,
            'sex_distribution': participants['sex'].value_counts().to_dict()
        }
        
        # Trial types (read from RT file, fall back to ACC)
        ref_data   = rt_data if not rt_data.empty else acc_data
        trial_types = ref_data['trial_type'].unique().tolist() if 'trial_type' in ref_data.columns else []
        sessions    = ref_data['session'].unique().tolist()    if 'session'    in ref_data.columns else []

        # Collect data by trial type and session
        data_by_condition = {}

        for trial_type in trial_types if trial_types else ['all']:
            for session in sessions if sessions else ['all']:
                # --- RT ---
                rt_vals = []
                if not rt_data.empty:
                    df_rt = rt_data.copy()
                    if trial_types:
                        df_rt = df_rt[df_rt['trial_type'] == trial_type]
                    if sessions:
                        df_rt = df_rt[df_rt['session'] == session]
                    rt_vals = pd.to_numeric(df_rt['response_time_ms'], errors='coerce').dropna().tolist()

                # --- ACC (binary for mean/std stats) ---
                acc_vals = []
                subject_acc_pct = []
                if not accbin_data.empty:
                    df_acc = accbin_data.copy()
                    if trial_types:
                        df_acc = df_acc[df_acc['trial_type'] == trial_type]
                    if sessions:
                        df_acc = df_acc[df_acc['session'] == session]
                    acc_vals = pd.to_numeric(df_acc['accuracy_binary'], errors='coerce').dropna().tolist()
                    if 'subject_id' in df_acc.columns:
                        for subj in df_acc['subject_id'].unique():
                            subj_acc = pd.to_numeric(
                                df_acc[df_acc['subject_id'] == subj]['accuracy_binary'],
                                errors='coerce').dropna().values
                            if len(subj_acc) > 0:
                                subject_acc_pct.append(float(np.mean(subj_acc) * 100))

                key = f"{trial_type}_ses{session}"
                data_by_condition[key] = {
                    'trial_type':            trial_type,
                    'session':               session,
                    'rt_values':             rt_vals,
                    'rt_mean':               float(np.mean(rt_vals))   if rt_vals  else None,
                    'rt_std':                float(np.std(rt_vals))    if rt_vals  else None,
                    'rt_median':             float(np.median(rt_vals)) if rt_vals  else None,
                    'acc_values':            acc_vals,
                    'acc_mean':              float(np.mean(acc_vals))  if acc_vals else None,
                    'acc_std':               float(np.std(acc_vals))   if acc_vals else None,
                    'subject_acc_percentages': subject_acc_pct,
                    'n_trials':              len(rt_vals) if rt_vals else len(acc_vals),
                }
        
        # Reliability — pass RT and ACCBIN DataFrames directly.
        # Split into task conditions and control/rest conditions so the project
        # HTML can show two separate radar plots.
        _EXCLUDE_TYPES = {'control', 'rest', 'baseline', 'fixation', 'fix',
                          'instruction', 'pause', 'break', 'catch', 'null'}

        def _is_control(t):
            return (t.lower() in _EXCLUDE_TYPES
                    or t.lower().startswith('ctrl')
                    or t.lower().startswith('rest'))

        task_trial_types    = [t for t in trial_types if not _is_control(t)]
        control_trial_types = [t for t in trial_types if     _is_control(t)]

        reliability         = self._calculate_reliability(rt_data, accbin_data, task_trial_types)
        control_reliability = self._calculate_reliability(rt_data, accbin_data, control_trial_types)

        # ── Learning-stage breakdown (individual project view only) ──────────
        # Detect whether a learning_stage column exists in the RT or ACC data.
        # If so, compute mean RT and mean accuracy per stage × trial_type so the
        # project HTML can show progression charts.  This data is intentionally
        # NOT passed to the radar / reliability metrics.
        learning_stage_data = {}
        stage_col = 'learning_stage'
        ref_ls = rt_data if not rt_data.empty else accbin_data

        # A column is considered "has stages" only when it exists AND contains at
        # least one non-null, non-empty, non-'n/a' value.
        def _has_real_stages(df: pd.DataFrame) -> bool:
            if df.empty or stage_col not in df.columns:
                return False
            valid = (df[stage_col]
                     .dropna()
                     .astype(str)
                     .str.strip()
                     .pipe(lambda s: s[s.ne('') & s.str.lower().ne('n/a')]))
            return len(valid) > 0

        has_stages = _has_real_stages(ref_ls)

        if has_stages:
            # Canonical stage list: drop null, empty, and literal 'n/a' values
            raw_stages = ref_ls[stage_col].dropna().astype(str).str.strip()
            raw_stages = raw_stages[raw_stages.ne('') & raw_stages.str.lower().ne('n/a')]
            all_stages = sorted(raw_stages.unique().tolist(), key=lambda s: str(s))
            for tt in trial_types if trial_types else ['all']:
                stage_rt_means   = []
                stage_rt_sems    = []
                stage_acc_means  = []
                stage_acc_sems   = []

                for stage in all_stages:
                    # RT per stage — match exact string value
                    if not rt_data.empty:
                        df_s = rt_data.copy()
                        if trial_types:
                            df_s = df_s[df_s['trial_type'] == tt]
                        df_s = df_s[df_s[stage_col].astype(str).str.strip() == stage]
                        vals = pd.to_numeric(df_s['response_time_ms'], errors='coerce').dropna()
                        stage_rt_means.append(float(vals.mean()) if len(vals) else None)
                        stage_rt_sems.append(float(vals.sem())  if len(vals) > 1 else None)
                    else:
                        stage_rt_means.append(None)
                        stage_rt_sems.append(None)

                    # ACC per stage (binary → percentage)
                    if not accbin_data.empty:
                        df_s = accbin_data.copy()
                        if trial_types:
                            df_s = df_s[df_s['trial_type'] == tt]
                        df_s = df_s[df_s[stage_col].astype(str).str.strip() == stage]
                        vals = pd.to_numeric(df_s['accuracy_binary'], errors='coerce').dropna()
                        stage_acc_means.append(float(vals.mean() * 100) if len(vals) else None)
                        stage_acc_sems.append(float(vals.sem()  * 100) if len(vals) > 1 else None)
                    else:
                        stage_acc_means.append(None)
                        stage_acc_sems.append(None)

                learning_stage_data[tt] = {
                    'stages':          all_stages,
                    'rt_means':        stage_rt_means,
                    'rt_sems':         stage_rt_sems,
                    'acc_means':       stage_acc_means,
                    'acc_sems':        stage_acc_sems,
                }

        # Compile report
        report = {
            'project_name':            project_name,
            'project_info':            proj_desc,
            'demographics':            demographics,
            'trial_types':             trial_types if trial_types else ['all'],
            'sessions':                sessions    if sessions    else ['all'],
            'data_by_condition':       data_by_condition,
            'reliability_metrics':     reliability,
            'control_reliability':     control_reliability,   # control/rest trial types only
            'learning_stage_data':     learning_stage_data,   # empty dict if no stage column
            'column_names': {
                'rt_column':  rt_col,
                'acc_column': acc_col
            }
        }
        
        return report
    
    def calculate_cohens_d(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Calculate Cohen's d for paired samples"""
        if len(data1) != len(data2) or len(data1) == 0:
            return np.nan
        
        diff = data1 - data2
        std_diff = np.std(diff, ddof=1)
        if std_diff == 0:
            return 0.0
        return np.mean(diff) / std_diff
    
    def calculate_pearson_r(self, data1: np.ndarray, data2: np.ndarray) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(data1) != len(data2) or len(data1) < 2:
            return np.nan
        
        try:
            r, p = stats.pearsonr(data1, data2)
            return r
        except:
            return np.nan
    
    def calculate_cv(self, data: np.ndarray) -> float:
        """Calculate coefficient of variation"""
        if len(data) == 0:
            return np.nan
        
        mean = np.mean(data)
        if mean == 0:
            return np.nan
        
        return (np.std(data, ddof=1) / mean) * 100
    
    def _calculate_reliability(self, rt_data: pd.DataFrame, accbin_data: pd.DataFrame,
                               trial_types: List[str]) -> Dict:
        """Calculate comprehensive reliability metrics from separate RT and ACCBIN DataFrames."""

        reliability = {}

        for trial_type in (trial_types if trial_types else ['all']):

            # --- filter by trial_type ---
            if trial_types:
                df_rt  = rt_data[rt_data['trial_type']  == trial_type].copy() if not rt_data.empty  else pd.DataFrame()
                df_acc = accbin_data[accbin_data['trial_type'] == trial_type].copy() if not accbin_data.empty else pd.DataFrame()
            else:
                df_rt  = rt_data.copy()  if not rt_data.empty  else pd.DataFrame()
                df_acc = accbin_data.copy() if not accbin_data.empty else pd.DataFrame()

            # Determine sessions from whichever DataFrame is available
            ref = df_rt if not df_rt.empty else df_acc
            if ref.empty or 'session' not in ref.columns:
                continue
            sessions = sorted(ref['session'].unique())
            if len(sessions) < 2:
                continue

            # Subjects with data in both sessions
            def multi_session_subjects(df):
                if df.empty or 'subject_id' not in df.columns:
                    return []
                counts = df.groupby('subject_id')['session'].nunique()
                return counts[counts >= 2].index.tolist()

            rt_subjects  = multi_session_subjects(df_rt)
            acc_subjects = multi_session_subjects(df_acc)

            rt_iccs, acc_iccs = [], []
            rt_cohens_d, acc_cohens_d = [], []
            rt_pearson_r, acc_pearson_r = [], []
            rt_cv_ses1, rt_cv_ses2 = [], []
            acc_cv_ses1, acc_cv_ses2 = [], []

            for subject in rt_subjects:
                subj = df_rt[df_rt['subject_id'] == subject]
                s1 = pd.to_numeric(subj[subj['session'] == sessions[0]]['response_time_ms'], errors='coerce').dropna().values
                s2 = pd.to_numeric(subj[subj['session'] == sessions[1]]['response_time_ms'], errors='coerce').dropna().values
                n  = min(len(s1), len(s2))
                if n > 5:
                    icc = self.calculate_icc(s1[:n], s2[:n])
                    if not np.isnan(icc): rt_iccs.append(icc)
                    d = self.calculate_cohens_d(s1[:n], s2[:n])
                    if not np.isnan(d): rt_cohens_d.append(d)
                    r = self.calculate_pearson_r(s1[:n], s2[:n])
                    if not np.isnan(r): rt_pearson_r.append(r)
                if len(s1) > 1:
                    cv = self.calculate_cv(s1)
                    if not np.isnan(cv): rt_cv_ses1.append(cv)
                if len(s2) > 1:
                    cv = self.calculate_cv(s2)
                    if not np.isnan(cv): rt_cv_ses2.append(cv)

            for subject in acc_subjects:
                subj = df_acc[df_acc['subject_id'] == subject]
                s1 = pd.to_numeric(subj[subj['session'] == sessions[0]]['accuracy_binary'], errors='coerce').dropna().values
                s2 = pd.to_numeric(subj[subj['session'] == sessions[1]]['accuracy_binary'], errors='coerce').dropna().values
                n  = min(len(s1), len(s2))
                if n > 5:
                    icc = self.calculate_icc(s1[:n], s2[:n])
                    if not np.isnan(icc): acc_iccs.append(icc)
                    d = self.calculate_cohens_d(s1[:n], s2[:n])
                    if not np.isnan(d): acc_cohens_d.append(d)
                    r = self.calculate_pearson_r(s1[:n], s2[:n])
                    if not np.isnan(r): acc_pearson_r.append(r)
                if len(s1) > 1:
                    cv = self.calculate_cv(s1)
                    if not np.isnan(cv): acc_cv_ses1.append(cv)
                if len(s2) > 1:
                    cv = self.calculate_cv(s2)
                    if not np.isnan(cv): acc_cv_ses2.append(cv)
            
            reliability[trial_type] = {
                # ICC metrics
                'rt_icc_mean': float(np.mean(rt_iccs)) if rt_iccs else None,
                'rt_icc_std': float(np.std(rt_iccs)) if rt_iccs else None,
                'rt_icc_min': float(np.min(rt_iccs)) if rt_iccs else None,
                'rt_icc_max': float(np.max(rt_iccs)) if rt_iccs else None,
                'acc_icc_mean': float(np.mean(acc_iccs)) if acc_iccs else None,
                'acc_icc_std': float(np.std(acc_iccs)) if acc_iccs else None,
                'acc_icc_min': float(np.min(acc_iccs)) if acc_iccs else None,
                'acc_icc_max': float(np.max(acc_iccs)) if acc_iccs else None,
                # Cohen's d metrics
                'rt_cohens_d_mean': float(np.mean(rt_cohens_d)) if rt_cohens_d else None,
                'rt_cohens_d_std': float(np.std(rt_cohens_d)) if rt_cohens_d else None,
                'acc_cohens_d_mean': float(np.mean(acc_cohens_d)) if acc_cohens_d else None,
                'acc_cohens_d_std': float(np.std(acc_cohens_d)) if acc_cohens_d else None,
                # Pearson r metrics
                'rt_pearson_r_mean': float(np.mean(rt_pearson_r)) if rt_pearson_r else None,
                'rt_pearson_r_std': float(np.std(rt_pearson_r)) if rt_pearson_r else None,
                'acc_pearson_r_mean': float(np.mean(acc_pearson_r)) if acc_pearson_r else None,
                'acc_pearson_r_std': float(np.std(acc_pearson_r)) if acc_pearson_r else None,
                # Coefficient of Variation (within-subject variability)
                'rt_cv_mean': float(np.mean(rt_cv_ses1 + rt_cv_ses2)) if (rt_cv_ses1 or rt_cv_ses2) else None,
                'rt_cv_std': float(np.std(rt_cv_ses1 + rt_cv_ses2)) if (rt_cv_ses1 or rt_cv_ses2) else None,
                'acc_cv_mean': float(np.mean(acc_cv_ses1 + acc_cv_ses2)) if (acc_cv_ses1 or acc_cv_ses2) else None,
                'acc_cv_std': float(np.std(acc_cv_ses1 + acc_cv_ses2)) if (acc_cv_ses1 or acc_cv_ses2) else None,
                # Sample sizes
                'n_subjects_rt':  len(rt_subjects),
                'n_subjects_acc': len(acc_subjects),
                'n_subjects': max(len(rt_subjects), len(acc_subjects)),
            }
        
        return reliability
    
    def generate_dashboard_html(self, all_reports: List[Dict]) -> str:
        """Generate comprehensive dashboard HTML"""
        
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Project Overview Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #e8e8e8 0%, #f5f5f5 50%, #ffffff 100%);
            color: #333;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, rgba(208, 208, 208, 0.9) 0%, rgba(232, 232, 232, 0.95) 50%, rgba(240, 240, 240, 0.98) 100%);
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 
                0 10px 40px rgba(64, 158, 128, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.8),
                inset 0 -1px 0 rgba(64, 158, 128, 0.15);
            border: 1px solid rgba(64, 224, 208, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                #2d8659 0%,
                #40e0d0 15%,
                #409e80 30%,
                #48d1cc 50%,
                #409e80 70%,
                #40e0d0 85%,
                #2d8659 100%
            );
            opacity: 0.8;
        }
        
        h1 {
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #409e80 15%,
                #2d8659 30%,
                #40e0d0 50%,
                #2d8659 70%,
                #409e80 85%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: -1px;
        }
        
        .subtitle {
            color: #1e5f44;
            font-size: 1.3em;
            font-weight: 300;
        }
        
        .project-section {
            background: linear-gradient(135deg, rgba(250, 250, 250, 0.95) 0%, rgba(255, 255, 255, 0.98) 50%, rgba(248, 248, 248, 0.95) 100%);
            margin-bottom: 50px;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(64, 224, 208, 0.3);
        }
        
        .project-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #505050;
        }
        
        .project-title-section {
            flex: 1;
        }
        
        .project-name {
            background: linear-gradient(135deg, 
                #409e80 0%,
                #2d8659 25%,
                #40e0d0 50%,
                #2d8659 75%,
                #409e80 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.2em;
            margin-bottom: 8px;
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        
        .project-full-name {
            color: #888;
            font-size: 1.1em;
            margin-bottom: 12px;
            font-style: italic;
        }
        
        .project-description {
            color: #999;
            font-size: 1em;
            line-height: 1.5;
        }
        
        .project-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .metric-box {
            background: linear-gradient(180deg, #ffffff 0%, #f8f8f8 100%);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid #454545;
        }
        
        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #d0d0d0;
            margin-bottom: 5px;
        }
        
        .metric-label {
            font-size: 0.85em;
            color: #888;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        
        .chart-container {
            background: linear-gradient(135deg, rgba(250, 250, 250, 0.95) 0%, rgba(255, 255, 255, 0.98) 50%, rgba(248, 248, 248, 0.95) 100%);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid rgba(64, 158, 128, 0.2);
            box-shadow: 0 4px 16px rgba(64, 158, 128, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }
        
        .chart-title {
            color: #1e5f44;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(64, 158, 128, 0.3);
        }
        
        .radar-container {
            grid-column: 1 / -1;
            max-width: 100%;
            min-height: 950px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .full-width-container {
            grid-column: 1 / -1;
        }
        
        .metric-info {
            background: linear-gradient(135deg, rgba(250, 250, 250, 0.95) 0%, rgba(255, 255, 255, 0.98) 50%, rgba(248, 248, 248, 0.95) 100%);
            padding: 30px;
            border-radius: 12px;
            margin-top: 30px;
            border: 1px solid rgba(64, 224, 208, 0.3);
            box-shadow: 0 6px 20px rgba(64, 158, 128, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.8);
        }
        
        .metric-info h3 {
            color: #1e5f44;
            font-size: 1.4em;
            margin-bottom: 25px;
            text-align: center;
            padding-bottom: 15px;
            border-bottom: 3px solid #505050;
            letter-spacing: 1px;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 100%);
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #2d8659;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
        }
        
        .metric-name {
            color: #2d8659;
            font-weight: bold;
            font-size: 1.2em;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .metric-icon {
            font-size: 1.3em;
        }
        
        .metric-desc {
            color: #1e5f44;
            font-size: 1em;
            line-height: 1.7;
            margin-bottom: 15px;
        }
        
        .metric-what {
            color: #888;
            font-size: 0.95em;
            margin-bottom: 12px;
            padding: 10px;
            background: #1a1a1a;
            border-radius: 6px;
            border-left: 3px solid #409e80;
        }
        
        .metric-what strong {
            color: #409e80;
        }
        
        .metric-formula {
            background: #0f0f0f;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            color: #2d8659;
            margin-top: 12px;
            border: 1px solid #2a2a2a;
            line-height: 1.8;
        }
        
        .metric-formula .formula-line {
            display: block;
            margin: 5px 0;
        }
        
        .metric-formula .formula-main {
            color: #2d8659;
            font-weight: bold;
            font-size: 1.05em;
        }
        
        .metric-formula .formula-range {
            color: #ffa726;
            margin-top: 8px;
            display: block;
        }
        
        .bullet-points {
            margin: 10px 0;
            padding-left: 0;
            list-style: none;
        }
        
        .bullet-points li {
            padding: 6px 0 6px 25px;
            position: relative;
            color: #666;
            line-height: 1.6;
        }
        
        .bullet-points li:before {
            content: "▸";
            position: absolute;
            left: 5px;
            color: #2d8659;
            font-weight: bold;
        }
        
        .characteristics {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 15px;
        }
        
        .char-badge {
            background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.9em;
            border: 1px solid #555;
            color: #1e5f44;
        }
        
        .char-badge.modality { border-color: #2d8659; color: #2d8659; }
        .char-badge.domain { border-color: #409e80; color: #409e80; }
        .char-badge.difficulty { border-color: #ffa726; color: #ffa726; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 MULTI-PROJECT OVERVIEW</h1>
        <p class="subtitle">Comprehensive Behavioral Data Analysis Dashboard</p>
    </div>
"""
        
        # Generate section for each project
        for report in all_reports:
            html += self._generate_project_section(report)
        
        html += """
</body>
</html>"""
        
        return html
    
    def _generate_project_section(self, report: Dict) -> str:
        """Generate HTML section for a single project"""
        
        proj_name = report['project_name']
        proj_info = report['project_info']
        demo = report['demographics']
        data_by_cond = report['data_by_condition']
        reliability = report['reliability_metrics']
        
        html = f"""
    <div class="project-section">
        <div class="project-header">
            <div class="project-title-section">
                <div class="project-name">{proj_name}</div>
                <div class="project-full-name">{proj_info['full_name']}</div>
                <div class="project-description">{proj_info['description']}</div>
                <div class="characteristics">
                    <span class="char-badge modality">📊 {proj_info['modality']}</span>
                    <span class="char-badge domain">🧠 {proj_info['cognitive_domain']}</span>
                    <span class="char-badge difficulty">⚡ {proj_info['difficulty']}</span>
                </div>
            </div>
        </div>
        
        <div class="project-metrics">
            <div class="metric-box">
                <div class="metric-value">{demo['n_participants']}</div>
                <div class="metric-label">Participants</div>
            </div>
"""
        
        if demo['age_mean']:
            html += f"""
            <div class="metric-box">
                <div class="metric-value">{demo['age_mean']:.1f}</div>
                <div class="metric-label">Mean Age</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{demo['age_std']:.1f}</div>
                <div class="metric-label">Age SD</div>
            </div>
"""
        
        # Add sex distribution
        for sex, count in demo['sex_distribution'].items():
            html += f"""
            <div class="metric-box">
                <div class="metric-value">{count}</div>
                <div class="metric-label">{sex.capitalize()}</div>
            </div>
"""
        
        html += """
        </div>
        
        <div class="charts-grid">
"""
        
        # RT Violin Plot
        html += f"""
            <div class="chart-container">
                <div class="chart-title">⏱️ Reaction Time Distribution</div>
                <div id="{proj_name}_rt_violin"></div>
            </div>
"""
        
        # Accuracy Violin Plot
        html += f"""
            <div class="chart-container">
                <div class="chart-title">🎯 Accuracy Distribution</div>
                <div id="{proj_name}_acc_violin"></div>
            </div>
"""
        
        # RT Scatter Plot
        html += f"""
            <div class="chart-container">
                <div class="chart-title">📍 RT Scatter (Outlier Detection)</div>
                <div id="{proj_name}_rt_scatter"></div>
            </div>
"""
        
        # Accuracy Scatter Plot
        html += f"""
            <div class="chart-container">
                <div class="chart-title">📍 Accuracy Scatter (Outlier Detection)</div>
                <div id="{proj_name}_acc_scatter"></div>
            </div>
"""
        
        # Learning-stage progression charts — above radar
        if report.get('learning_stage_data'):
            html += f"""
            <div class="chart-container">
                <div class="chart-title">RT Progression across Learning Stages</div>
                <div id="{proj_name}_stage_rt"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Accuracy Progression across Learning Stages</div>
                <div id="{proj_name}_stage_acc"></div>
            </div>
"""

        # Radar Chart for reliability — full width, below stage charts
        if reliability:
            html += f"""
            <div class="chart-container full-width-container">
                <div class="chart-title">📡 Reliability Metrics Radar</div>
                <div id="{proj_name}_radar"></div>
            </div>
"""
        
        html += """
        </div>
    </div>
    
    <script>
"""
        
        # Generate plots
        html += self._generate_plots_js(proj_name, data_by_cond, reliability,
                                        report['trial_types'],
                                        report.get('learning_stage_data', {}),
                                        report.get('control_reliability', {}))
        
        html += """
    </script>
"""
        
        return html
    
    def _generate_plots_js(self, proj_name: str, data_by_cond: Dict,
                          reliability: Dict, trial_types: List[str],
                          learning_stage_data: Dict = None,
                          control_reliability: Dict = None) -> str:
        """Generate JavaScript for all plots"""
        
        js = ""
        if control_reliability is None:
            control_reliability = {}
        
        # Color mapping
        colors = {
            'learning': '#2d8659',
            'control': '#409e80',
            'encoding': '#409e80',
            'retrieval': '#26c6da',
            'study': '#40e0d0',
            'test': '#ffa726',
            'generate': '#2d8659',
            'repeat': '#409e80',
            'navigation': '#7e57c2',
            'pointing': '#26a69a',
            '2back': '#ec407a',
            '0back': '#2d8659',
            'regulate': '#5c6bc0',
            'observe': '#409e80',
            'incongruent': '#40e0d0',
            'congruent': '#2d8659',
            'all': '#8e24aa'
        }
        
        # RT Violin Plot
        rt_traces = []
        for key, data in data_by_cond.items():
            if data['rt_values']:
                trial_type = data['trial_type']
                session = data['session']
                color = colors.get(trial_type, '#8e24aa')
                
                label = f"{trial_type} (ses-{session})" if session != 'all' else trial_type
                
                rt_traces.append({
                    'y': data['rt_values'],
                    'type': 'violin',
                    'name': label,
                    'box': {'visible': True},
                    'meanline': {'visible': True},
                    'marker': {'color': color},
                    'line': {'color': color}
                })
        
        if rt_traces:
            # Clamp y-axis: use IQR fence (Q1 - 2*IQR, Q3 + 2*IQR) so extreme
            # outliers don't stretch the plot to unusable proportions
            all_rt_vals = []
            for key, data in data_by_cond.items():
                all_rt_vals.extend(data.get('rt_values', []))
            if all_rt_vals:
                q1  = float(np.percentile(all_rt_vals, 25))
                q3  = float(np.percentile(all_rt_vals, 75))
                iqr = q3 - q1
                rt_y_min = max(0,    q1 - 2.5 * iqr)
                rt_y_max = min(5000, q3 + 2.5 * iqr)
            else:
                rt_y_min, rt_y_max = 0, 2000

            js += f"""
        var rtTraces = {json.dumps(rt_traces)};
        var rtLayout = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            height: 420,
            yaxis: {{
                title: 'Reaction Time (ms)',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 14}},
                range: [{rt_y_min:.0f}, {rt_y_max:.0f}]
            }},
            xaxis: {{gridcolor: "rgba(64, 158, 128, 0.2)"}},
            showlegend: true,
            legend: {{
                bgcolor: "rgba(240, 240, 240, 0.9)",
                bordercolor: "rgba(64, 158, 128, 0.3)",
                borderwidth: 1
            }},
            violingap: 0.3,
            violinmode: 'group',
            margin: {{l: 60, r: 30, t: 30, b: 50}}
        }};
        Plotly.newPlot('{proj_name}_rt_violin', rtTraces, rtLayout, {{responsive: true}});
"""
        
        # Accuracy Violin Plot - SUBJECT-LEVEL PERCENTAGES
        acc_traces = []
        for key, data in data_by_cond.items():
            # Use subject-level accuracy percentages
            if data.get('subject_acc_percentages'):
                trial_type = data['trial_type']
                session = data['session']
                color = colors.get(trial_type, '#8e24aa')
                
                label = f"{trial_type} (ses-{session})" if session != 'all' else trial_type
                
                acc_traces.append({
                    'y': data['subject_acc_percentages'],
                    'type': 'violin',
                    'name': label,
                    'box': {'visible': True},
                    'meanline': {'visible': True},
                    'spanmode': 'hard',   # clamp KDE to actual data range, no bleed beyond 0/100
                    'bandwidth': 4,       # moderate smoothing — avoids over-sharp edges at boundaries
                    'points': 'all',      # show individual subject dots alongside violin
                    'jitter': 0.3,
                    'pointpos': 0,
                    'marker': {
                        'color': color,
                        'size': 5,
                        'opacity': 0.6
                    },
                    'line': {'color': color},
                    'fillcolor': color.replace(')', ', 0.25)').replace('rgb', 'rgba') if color.startswith('rgb') else color,
                })
        
        if acc_traces:
            # Compute a sensible y-range with padding so violins never look clipped
            all_acc_vals = []
            for key, data in data_by_cond.items():
                all_acc_vals.extend(data.get('subject_acc_percentages', []))
            y_min = max(0,   min(all_acc_vals) - 8) if all_acc_vals else 0
            y_max = min(105, max(all_acc_vals) + 8) if all_acc_vals else 105

            js += f"""
        var accTraces = {json.dumps(acc_traces)};
        var accLayout = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            height: 420,
            yaxis: {{
                title: 'Accuracy (%) per Subject',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                range: [{y_min}, {y_max}],
                titlefont: {{size: 14}},
                zeroline: false
            }},
            xaxis: {{gridcolor: "rgba(64, 158, 128, 0.2)"}},
            showlegend: true,
            legend: {{
                bgcolor: "rgba(240, 240, 240, 0.9)",
                bordercolor: "rgba(64, 158, 128, 0.3)",
                borderwidth: 1
            }},
            margin: {{l: 60, r: 30, t: 30, b: 50}},
            violingap: 0.3,
            violinmode: 'group'
        }};
        Plotly.newPlot('{proj_name}_acc_violin', accTraces, accLayout, {{responsive: true}});
"""
        
        # RT Scatter Plot (outlier detection)
        if rt_traces:
            rt_scatter_data = []
            for key, data in data_by_cond.items():
                if data['rt_values']:
                    trial_type = data['trial_type']
                    session = data['session']
                    color = colors.get(trial_type, '#8e24aa')
                    
                    label = f"{trial_type} (ses-{session})" if session != 'all' else trial_type
                    
                    # Add trial index
                    x_vals = list(range(len(data['rt_values'])))
                    
                    rt_scatter_data.append({
                        'x': x_vals,
                        'y': data['rt_values'],
                        'mode': 'markers',
                        'name': label,
                        'marker': {
                            'size': 6,
                            'color': color,
                            'opacity': 0.6
                        }
                    })
            
            js += f"""
        var rtScatter = {json.dumps(rt_scatter_data)};
        var rtScatterLayout = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            yaxis: {{
                title: 'Reaction Time (ms)',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 14}}
            }},
            xaxis: {{
                title: 'Trial Index',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 14}}
            }},
            showlegend: true,
            legend: {{
                bgcolor: "rgba(240, 240, 240, 0.9)",
                bordercolor: "rgba(64, 158, 128, 0.3)",
                borderwidth: 1
            }},
            hovermode: 'closest',
            margin: {{l: 60, r: 30, t: 30, b: 50}}
        }};
        Plotly.newPlot('{proj_name}_rt_scatter', rtScatter, rtScatterLayout, {{responsive: true}});
"""
        
        # Accuracy Scatter Plot - PERCENTAGE PER SESSION PER SUBJECT
        if acc_traces:
            acc_scatter_data = []
            
            for key, data in data_by_cond.items():
                # Use subject-level accuracy percentages instead of trial-level
                if data.get('subject_acc_percentages'):
                    trial_type = data['trial_type']
                    session = data['session']
                    color = colors.get(trial_type, '#8e24aa')
                    
                    label = f"{trial_type} (ses-{session})" if session != 'all' else trial_type
                    
                    acc_pct_list = data['subject_acc_percentages']
                    x_vals = list(range(len(acc_pct_list)))
                    subject_labels = [f"Subject {i+1}" for i in range(len(acc_pct_list))]
                    
                    acc_scatter_data.append({
                        'x': x_vals,
                        'y': acc_pct_list,
                        'mode': 'markers',
                        'name': label,
                        'text': subject_labels,
                        'hovertemplate': '%{text}<br>Accuracy: %{y:.1f}%<extra></extra>',
                        'marker': {
                            'size': 10,
                            'color': color,
                            'opacity': 0.7,
                            'line': {'width': 1, 'color': '#ffffff'}
                        }
                    })
            
            if acc_scatter_data:
                js += f"""
        var accScatter = {json.dumps(acc_scatter_data)};
        var accScatterLayout = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            yaxis: {{
                title: 'Accuracy (%) per Subject',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                range: [{y_min}, {y_max}],
                titlefont: {{size: 14}},
                zeroline: false
            }},
            xaxis: {{
                title: 'Subject Index',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 14}}
            }},
            showlegend: true,
            legend: {{
                bgcolor: "rgba(240, 240, 240, 0.9)",
                bordercolor: "rgba(64, 158, 128, 0.3)",
                borderwidth: 1
            }},
            hovermode: 'closest',
            margin: {{l: 60, r: 30, t: 30, b: 50}}
        }};
        Plotly.newPlot('{proj_name}_acc_scatter', accScatter, accScatterLayout, {{responsive: true}});
"""
        
        # ── Radar helper — reusable for both task and control ────────────
        def _build_radar_js(rel_dict, div_id):
            categories = []
            values = []
            for trial_type, metrics in rel_dict.items():
                if metrics.get('rt_icc_mean') is not None:
                    categories.append(f'{trial_type} RT ICC')
                    values.append(max(0, min(1, metrics['rt_icc_mean'])))
                if metrics.get('acc_icc_mean') is not None:
                    categories.append(f'{trial_type} Acc ICC')
                    values.append(max(0, min(1, metrics['acc_icc_mean'])))
                if metrics.get('rt_pearson_r_mean') is not None:
                    categories.append(f'{trial_type} RT Pearson r')
                    values.append(max(0, min(1, metrics['rt_pearson_r_mean'])))
                if metrics.get('acc_pearson_r_mean') is not None:
                    categories.append(f'{trial_type} Acc Pearson r')
                    values.append(max(0, min(1, metrics['acc_pearson_r_mean'])))
                if metrics.get('rt_cohens_d_mean') is not None:
                    d_abs = abs(metrics['rt_cohens_d_mean'])
                    categories.append(f'{trial_type} RT Stability')
                    values.append(max(0, min(1, 1 - (d_abs / 2))))
                if metrics.get('acc_cohens_d_mean') is not None:
                    d_abs = abs(metrics['acc_cohens_d_mean'])
                    categories.append(f'{trial_type} Acc Stability')
                    values.append(max(0, min(1, 1 - (d_abs / 2))))
                if metrics.get('rt_cv_mean') is not None:
                    categories.append(f'{trial_type} RT Consistency')
                    values.append(max(0, min(1, 1 - (metrics['rt_cv_mean'] / 50))))
                if metrics.get('acc_cv_mean') is not None:
                    categories.append(f'{trial_type} Acc Consistency')
                    values.append(max(0, min(1, 1 - (metrics['acc_cv_mean'] / 50))))
            if not categories:
                return ''
            categories.append(categories[0])
            values.append(values[0])
            radar_data = [{
                'type': 'scatterpolar',
                'r': values,
                'theta': categories,
                'fill': 'toself',
                'fillcolor': 'rgba(64, 224, 208, 0.15)',
                'line': {'color': '#40e0d0', 'width': 3},
                'marker': {'color': '#40e0d0', 'size': 10}
            }]
            return f"""
        var radarData_{div_id} = {json.dumps(radar_data)};
        var radarLayout_{div_id} = {{
            polar: {{
                bgcolor: 'rgba(15, 25, 20, 0.97)',
                radialaxis: {{
                    visible: true,
                    range: [0, 1],
                    gridcolor: "rgba(64, 224, 208, 0.2)",
                    linecolor: "rgba(64, 224, 208, 0.3)",
                    tickfont: {{color: 'rgba(64, 224, 208, 0.7)', size: 12}},
                    tickcolor: "rgba(64, 224, 208, 0.4)"
                }},
                angularaxis: {{
                    gridcolor: "rgba(45, 134, 89, 0.35)",
                    linecolor: "rgba(64, 224, 208, 0.3)",
                    tickfont: {{color: 'rgba(200, 230, 215, 0.9)', size: 13}}
                }}
            }},
            plot_bgcolor: "rgba(15, 25, 20, 0.97)",
            paper_bgcolor: "rgba(15, 25, 20, 0.97)",
            font: {{color: 'rgba(200, 230, 215, 0.9)', size: 14}},
            showlegend: false,
            height: 800,
            width: 1200,
            margin: {{l: 140, r: 140, t: 100, b: 100}}
        }};
        Plotly.newPlot('{div_id}', radarData_{div_id}, radarLayout_{div_id}, {{responsive: true}});
"""

        # Task radar
        if reliability:
            js += _build_radar_js(reliability, f'{proj_name}_radar_task')

        # Control / rest radar
        if control_reliability:
            js += _build_radar_js(control_reliability, f'{proj_name}_radar_control')
        
        # ── Learning-stage progression plots (individual project view only) ──
        if learning_stage_data:
            # Use proj_name prefix when available (dashboard mode), else bare ids
            rt_div  = f"{proj_name}_stage_rt"  if proj_name else "stage_rt"
            acc_div = f"{proj_name}_stage_acc" if proj_name else "stage_acc"

            stage_colors = [
                '#2d8659', '#409e80', '#40e0d0', '#26c6da',
                '#ffa726', '#ec407a', '#7e57c2', '#5c6bc0'
            ]

            rt_stage_traces  = []
            acc_stage_traces = []

            for idx, (tt, stage_info) in enumerate(learning_stage_data.items()):
                color = stage_colors[idx % len(stage_colors)]
                stages = stage_info['stages']

                # RT trace
                rt_y    = [v if v is not None else 'null' for v in stage_info['rt_means']]
                rt_err  = [v if v is not None else 0       for v in stage_info['rt_sems']]
                if any(v != 'null' for v in rt_y):
                    rt_stage_traces.append({
                        'x': stages,
                        'y': stage_info['rt_means'],
                        'error_y': {'type': 'data', 'array': rt_err, 'visible': True,
                                    'color': color, 'thickness': 1.5, 'width': 4},
                        'mode': 'lines+markers',
                        'name': tt,
                        'line':   {'color': color, 'width': 2.5},
                        'marker': {'color': color, 'size': 8},
                    })

                # ACC trace
                acc_y   = [v if v is not None else 'null' for v in stage_info['acc_means']]
                acc_err = [v if v is not None else 0       for v in stage_info['acc_sems']]
                if any(v != 'null' for v in acc_y):
                    acc_stage_traces.append({
                        'x': stages,
                        'y': stage_info['acc_means'],
                        'error_y': {'type': 'data', 'array': acc_err, 'visible': True,
                                    'color': color, 'thickness': 1.5, 'width': 4},
                        'mode': 'lines+markers',
                        'name': tt,
                        'line':   {'color': color, 'width': 2.5},
                        'marker': {'color': color, 'size': 8},
                    })

            shared_layout = {
                'plot_bgcolor':  'rgba(255,255,255,0.95)',
                'paper_bgcolor': 'rgba(250,250,250,0.5)',
                'font': {'color': '#333', 'size': 12},
                'xaxis': {'title': 'Learning Stage',
                          'gridcolor': 'rgba(64,158,128,0.2)',
                          'titlefont': {'size': 14}},
                'showlegend': True,
                'legend': {'bgcolor': 'rgba(240,240,240,0.9)',
                           'bordercolor': 'rgba(64,158,128,0.3)', 'borderwidth': 1},
                'margin': {'l': 70, 'r': 30, 't': 30, 'b': 60},
            }

            if rt_stage_traces:
                rt_layout = dict(shared_layout)
                rt_layout['yaxis'] = {'title': 'Mean RT (ms)',
                                      'gridcolor': 'rgba(64,158,128,0.2)',
                                      'titlefont': {'size': 14}}
                js += f"""
        var stageRtTraces = {json.dumps(rt_stage_traces)};
        var stageRtLayout = {json.dumps(rt_layout)};
        Plotly.newPlot('{rt_div}', stageRtTraces, stageRtLayout, {{responsive: true}});
"""

            if acc_stage_traces:
                acc_layout = dict(shared_layout)
                acc_layout['yaxis'] = {'title': 'Mean Accuracy (%)',
                                       'gridcolor': 'rgba(64,158,128,0.2)',
                                       'range': [0, 100],
                                       'titlefont': {'size': 14}}
                js += f"""
        var stageAccTraces = {json.dumps(acc_stage_traces)};
        var stageAccLayout = {json.dumps(acc_layout)};
        Plotly.newPlot('{acc_div}', stageAccTraces, stageAccLayout, {{responsive: true}});
"""

        return js
    
    def save_dashboard(self, html_content: str, output_path: str = None):
        """Save dashboard HTML"""
        if output_path is None:
            output_path = self.base_path / "multi_project_overview.html"
        else:
            output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nDashboard saved: {output_path}")
        return output_path
    
    def save_json_reports(self, all_reports: List[Dict]):
        """Save all reports as JSON"""
        output_path = self.base_path / "all_projects_data.json"
        
        with open(output_path, 'w') as f:
            json.dump(all_reports, f, indent=2)
        
        print(f"JSON data saved: {output_path}")
        return output_path
    
    def run(self):
        """Run complete analysis - generate individual project reports"""
        print("=" * 70)
        print("Generating Individual Project Reports")
        print("=" * 70)
        
        projects = self.find_projects()
        
        for project in projects:
            report = self.analyze_project(project)
            if report:
                # Generate individual HTML
                html = self.generate_project_html(report)
                self.save_project_html(project, html)
                
                # Save individual JSON
                self.save_project_json(project, report)
        
        print(f"\n✅ Reports generated for {len(projects)} projects!")
        print("=" * 70)
    
    def load_bibliography(self, project_name: str) -> list:
        """Load bibliography.json from the project folder.

        Supports two formats:
          v2  (recommended) — top-level 'publications' key containing an array of
              self-contained publication objects, each with an optional 'key_findings'
              sub-object.  Schema marker: '_schema': 'bibliography_json_v2'.

          v1  (legacy) — flat dict with 'citation_1', 'citation_2', … sibling keys.
              'key_findings' is a separate top-level key; its 'reliability' block is
              merged into the first citation found so ICC values are not lost.

        Returns a list of citation dicts (empty when file absent or unparseable).
        """
        bib_path = self.base_path / "Projects" / project_name / "bibliography.json"
        if not bib_path.exists():
            return []
        try:
            with open(bib_path, encoding="utf-8") as f:
                raw = json.load(f)
        except Exception as e:
            print(f"  Could not read bibliography for {project_name}: {e}")
            return []

        # ── v2 format ────────────────────────────────────────────────────────
        if "publications" in raw and isinstance(raw["publications"], list):
            return [p for p in raw["publications"] if isinstance(p, dict)]

        # ── v1 legacy format ─────────────────────────────────────────────────
        citations = []
        for key, value in raw.items():
            if key.startswith("citation_") and isinstance(value, dict):
                citations.append(value)

        # Merge top-level key_findings.reliability into the first citation so
        # ICC values are surfaced in the card even in the old layout.
        if citations and "key_findings" in raw:
            kf = raw["key_findings"]
            if isinstance(kf, dict) and "reliability" in kf:
                citations[0].setdefault("key_findings", {})["reliability"] = kf["reliability"]

        return citations

    def generate_project_html(self, report: Dict) -> str:
        """Generate HTML for a single project"""
        
        proj_name = report['project_name']
        proj_info = report['project_info']
        demo = report['demographics']
        data_by_cond = report['data_by_condition']
        reliability = report['reliability_metrics']
        control_reliability = report.get('control_reliability', {})

        age_str = f"{demo['age_mean']:.1f} ± {demo['age_std']:.1f}" if demo['age_mean'] else "N/A"
        sex_counts = demo['sex_distribution']
        male_count = sex_counts.get('male', 0)
        female_count = sex_counts.get('female', 0)
        sex_str = f"{male_count}/{female_count}"

        # Load optional bibliography
        bibliography = self.load_bibliography(proj_name)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{proj_name} - Project Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #e8e8e8 0%, #f5f5f5 50%, #ffffff 100%);
            color: #333;
            padding: 20px;
        }}

        .container {{ max-width: 1600px; margin: 0 auto; }}

        .header {{
            background: linear-gradient(135deg,
                rgba(210,228,220,0.92) 0%,
                rgba(228,240,234,0.96) 35%,
                rgba(242,248,245,0.98) 60%,
                rgba(220,235,228,0.95) 100%);
            padding: 40px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow:
                0 8px 32px rgba(45,134,89,0.18),
                0 2px 8px rgba(64,224,208,0.12),
                inset 0 1px 0 rgba(255,255,255,0.95),
                inset 0 -1px 0 rgba(64,158,128,0.12);
            border: 1px solid rgba(100,180,150,0.45);
            position: relative;
            overflow: hidden;
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 4px;
            background: linear-gradient(90deg,
                #2d8659 0%, #5ab88a 20%, #a8d8c0 40%,
                #40e0d0 50%, #a8d8c0 60%, #5ab88a 80%, #2d8659 100%);
        }}

        /* subtle metallic sheen overlay */
        .header::after {{
            content: '';
            position: absolute;
            top: 0; left: -60%; right: 0; bottom: 0;
            background: linear-gradient(105deg,
                transparent 40%,
                rgba(255,255,255,0.22) 50%,
                transparent 60%);
            pointer-events: none;
        }}

        .project-name {{
            background: linear-gradient(135deg,
                #1a5c3f 0%, #2d8659 25%, #4aad7a 45%,
                #40e0d0 55%, #4aad7a 70%, #2d8659 85%, #1a5c3f 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3em;
            margin-bottom: 8px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}

        .project-full-name {{
            color: #3a7a5a;
            font-size: 1.4em;
            margin-bottom: 12px;
            font-style: italic;
        }}

        .project-description {{
            color: #4a6e5a;
            font-size: 1.05em;
            line-height: 1.6;
            margin-bottom: 20px;
        }}

        .char-badges {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 4px; }}
        .char-badge {{
            background: linear-gradient(135deg,
                rgba(255,255,255,0.85) 0%, rgba(220,240,230,0.9) 100%);
            padding: 7px 16px;
            border-radius: 20px;
            font-size: 0.92em;
            border: 1px solid rgba(64,158,128,0.45);
            color: #2d7a52;
            font-weight: 500;
            box-shadow: 0 1px 4px rgba(64,158,128,0.15),
                        inset 0 1px 0 rgba(255,255,255,0.8);
        }}

        .metrics-row {{
            display: flex; gap: 30px; margin-top: 22px;
            padding-top: 18px;
            border-top: 1px solid rgba(64,158,128,0.3);
        }}
        .metric-item {{ font-size: 1.05em; }}
        .metric-label {{ color: #7a9e8a; font-size: 0.9em; margin-right: 6px; }}
        .metric-value {{
            background: linear-gradient(135deg, #1a5c3f 0%, #2d8659 50%, #409e80 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(600px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }}

        .chart-container {{
            background: linear-gradient(135deg, rgba(250,250,250,0.95) 0%, rgba(255,255,255,0.98) 50%, rgba(248,248,248,0.95) 100%);
            padding: 25px; border-radius: 12px;
            border: 1px solid rgba(64,158,128,0.2);
            box-shadow: 0 4px 16px rgba(64,158,128,0.12), inset 0 1px 0 rgba(255,255,255,0.8);
        }}

        .chart-title {{
            color: #1e5f44; font-size: 1.3em; font-weight: 600;
            margin-bottom: 15px; padding-bottom: 10px;
            border-bottom: 2px solid rgba(64,158,128,0.3);
        }}

        .full-width-container {{ grid-column: 1 / -1; }}

        .radar-container {{
            grid-column: 1 / -1;
            width: 100%;
        }}

        /* ── Reliability explanation panel ─────────────────────────── */
        .reliability-panel {{
            grid-column: 1 / -1;
            background: linear-gradient(135deg, rgba(15,25,20,0.97) 0%, rgba(20,35,28,0.98) 50%, rgba(15,25,20,0.97) 100%);
            border-radius: 16px;
            border: 1px solid rgba(64,224,208,0.25);
            box-shadow:
                0 12px 40px rgba(0,0,0,0.5),
                inset 0 1px 0 rgba(64,224,208,0.15),
                inset 0 -1px 0 rgba(45,134,89,0.1);
            overflow: hidden;
            position: relative;
        }}

        .reliability-panel::before {{
            content: '';
            position: absolute; top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg,
                #1e5f44 0%, #2d8659 20%, #40e0d0 40%,
                #409e80 60%, #40e0d0 80%, #2d8659 100%);
        }}

        .reliability-panel-header {{
            padding: 32px 40px 24px;
            border-bottom: 1px solid rgba(64,158,128,0.2);
        }}

        .reliability-panel-title {{
            background: linear-gradient(135deg,
                #40e0d0 0%, #2d8659 30%, #409e80 60%, #40e0d0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.5em;
            font-weight: 700;
            letter-spacing: 2px;
            text-transform: uppercase;
        }}

        .reliability-panel-subtitle {{
            color: rgba(64,224,208,0.5);
            font-size: 0.9em;
            margin-top: 6px;
            font-style: italic;
        }}

        .metric-cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 24px;
            padding: 32px 40px 40px;
        }}

        .metric-card {{
            background: linear-gradient(160deg,
                rgba(30,50,40,0.8) 0%,
                rgba(20,38,30,0.9) 50%,
                rgba(15,28,22,0.95) 100%);
            border-radius: 12px;
            border: 1px solid rgba(64,158,128,0.3);
            border-left: 3px solid #2d8659;
            overflow: hidden;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(45,134,89,0.3);
            border-left-color: #40e0d0;
        }}

        .metric-card-header {{
            padding: 18px 22px 14px;
            border-bottom: 1px solid rgba(64,158,128,0.2);
            background: linear-gradient(90deg, rgba(45,134,89,0.15) 0%, transparent 100%);
        }}

        .metric-card-name {{
            color: #40e0d0;
            font-size: 1.1em;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        .metric-card-tagline {{
            color: rgba(64,224,208,0.55);
            font-size: 0.85em;
            margin-top: 4px;
            font-style: italic;
        }}

        .metric-card-body {{ padding: 16px 22px 20px; }}

        .metric-card-points {{
            list-style: none;
            margin-bottom: 16px;
        }}

        .metric-card-points li {{
            color: rgba(200,220,210,0.8);
            font-size: 0.9em;
            line-height: 1.7;
            padding-left: 16px;
            position: relative;
        }}

        .metric-card-points li::before {{
            content: '›';
            position: absolute; left: 0;
            color: #2d8659;
            font-weight: bold;
            font-size: 1.2em;
            line-height: 1.4;
        }}

        .formula-box {{
            background: rgba(0,0,0,0.4);
            border: 1px solid rgba(45,134,89,0.4);
            border-radius: 8px;
            padding: 14px 16px;
            font-family: 'Courier New', monospace;
        }}

        .formula-main {{
            color: #40e0d0;
            font-size: 0.9em;
            font-weight: 600;
            display: block;
            margin-bottom: 6px;
            line-height: 1.5;
        }}

        .formula-sub {{
            color: rgba(64,224,208,0.5);
            font-size: 0.78em;
            display: block;
            line-height: 1.6;
        }}

        .formula-range {{
            color: #ffa726;
            font-size: 0.82em;
            display: block;
            margin-top: 8px;
            font-style: normal;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
        }}

        .btn-container {{
            display: flex;
            margin-top: 40px;
            margin-bottom: 20px;
        }}

        .btn-secondary {{
            padding: 18px 35px;
            border: 1px solid rgba(64,224,208,0.35);
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            background: linear-gradient(135deg,
                rgba(15,25,20,0.97) 0%,
                rgba(30,50,40,0.95) 50%,
                rgba(20,35,28,0.97) 100%
            );
            color: #40e0d0;
            min-width: 200px;
            box-shadow:
                0 4px 16px rgba(0,0,0,0.4),
                inset 0 1px 0 rgba(64,224,208,0.15),
                inset 0 -1px 0 rgba(45,134,89,0.1);
        }}

        .btn-secondary:hover {{
            background: linear-gradient(135deg,
                rgba(20,35,28,0.98) 0%,
                rgba(45,80,60,0.95) 50%,
                rgba(30,50,40,0.98) 100%
            );
            border-color: #40e0d0;
            color: #7fffd4;
            transform: translateY(-2px);
            box-shadow:
                0 8px 24px rgba(45,134,89,0.35),
                inset 0 1px 0 rgba(64,224,208,0.2),
                inset 0 -1px 0 rgba(45,134,89,0.15);
        }}

        /* ── Publications box ── */
        .publications-box {{
            background: linear-gradient(135deg,
                rgba(210,228,220,0.88) 0%,
                rgba(228,240,234,0.93) 35%,
                rgba(242,248,245,0.96) 60%,
                rgba(218,236,228,0.90) 100%);
            border: 1px solid rgba(100,180,150,0.45);
            border-radius: 15px;
            padding: 30px 38px;
            margin-bottom: 30px;
            position: relative;
            overflow: hidden;
            box-shadow:
                0 6px 24px rgba(45,134,89,0.16),
                0 2px 6px rgba(64,224,208,0.10),
                inset 0 1px 0 rgba(255,255,255,0.92),
                inset 0 -1px 0 rgba(64,158,128,0.10);
        }}

        .publications-box::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #2d8659 0%, #5ab88a 20%, #a8d8c0 40%,
                #40e0d0 50%, #a8d8c0 60%, #5ab88a 80%, #2d8659 100%);
        }}

        /* metallic sheen */
        .publications-box::after {{
            content: '';
            position: absolute;
            top: 0; left: -60%; right: 0; bottom: 0;
            background: linear-gradient(105deg,
                transparent 40%,
                rgba(255,255,255,0.18) 50%,
                transparent 60%);
            pointer-events: none;
        }}

        .publications-title {{
            background: linear-gradient(135deg,
                #1a5c3f 0%, #2d8659 30%, #409e80 55%, #2d8659 75%, #1a5c3f 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.3em;
            font-weight: 600;
            letter-spacing: -0.2px;
            margin-bottom: 20px;
            padding-bottom: 14px;
            border-bottom: 1px solid rgba(64,158,128,0.3);
        }}

        .pub-list {{
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}

        .pub-card {{
            background: linear-gradient(135deg,
                rgba(255,255,255,0.75) 0%,
                rgba(240,250,246,0.85) 100%);
            border: 1px solid rgba(100,180,150,0.3);
            border-radius: 10px;
            padding: 16px 20px;
            display: flex;
            align-items: flex-start;
            gap: 16px;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
            box-shadow: 0 1px 4px rgba(64,158,128,0.08),
                        inset 0 1px 0 rgba(255,255,255,0.9);
        }}

        .pub-card:hover {{
            border-color: rgba(64,224,208,0.5);
            box-shadow: 0 4px 14px rgba(64,158,128,0.18),
                        inset 0 1px 0 rgba(255,255,255,0.9);
        }}

        .pub-number {{
            flex-shrink: 0;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: linear-gradient(135deg, #2d8659 0%, #5ab88a 50%, #40e0d0 100%);
            color: #fff;
            font-size: 0.8em;
            font-weight: 700;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 2px;
            box-shadow: 0 2px 6px rgba(45,134,89,0.3);
        }}

        .pub-content {{
            flex: 1;
            min-width: 0;
        }}

        .pub-title {{
            color: #1a4a30;
            font-size: 0.97em;
            font-weight: 600;
            line-height: 1.5;
            margin-bottom: 5px;
        }}

        .pub-title a {{
            color: inherit;
            text-decoration: none;
        }}

        .pub-title a:hover {{
            color: #2d8659;
            text-decoration: underline;
        }}

        .pub-authors {{
            color: #5a7a68;
            font-size: 0.86em;
            margin-bottom: 9px;
            line-height: 1.5;
        }}

        .pub-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            align-items: center;
        }}

        .pub-badge {{
            padding: 3px 11px;
            border-radius: 20px;
            font-size: 0.78em;
            font-weight: 500;
            border: 1px solid;
        }}

        .pub-badge.journal {{
            color: #1e6644;
            border-color: rgba(45,134,89,0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(210,240,226,0.8) 100%);
        }}

        .pub-badge.year {{
            color: #2d5a40;
            border-color: rgba(64,158,128,0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(200,232,218,0.8) 100%);
        }}

        .pub-badge.doi {{
            color: #1e7a68;
            border-color: rgba(64,200,180,0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(200,240,234,0.8) 100%);
        }}

        .pub-badge.oa {{
            color: #7a5a10;
            border-color: rgba(200,160,40,0.4);
            background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(250,240,200,0.8) 100%);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="project-name">{proj_name}</div>
            <div class="project-full-name">{proj_info['full_name']}</div>
            <div class="project-description">{proj_info['description']}</div>
            <div class="char-badges">
                <span class="char-badge">{proj_info['modality']}</span>
                <span class="char-badge">{proj_info['cognitive_domain']}</span>
            </div>
            <div class="metrics-row">
                <div class="metric-item">
                    <span class="metric-label">Participants:</span>
                    <span class="metric-value">{demo['n_participants']}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Age:</span>
                    <span class="metric-value">{age_str} years</span>
                </div>
                <div class="metric-item">
                    <span class="metric-label">Male / Female:</span>
                    <span class="metric-value">{sex_str}</span>
                </div>
            </div>
        </div>
"""

        # ── Publications box (only rendered when bibliography.json exists) ──
        if bibliography:
            def _fmt_authors(authors: list) -> str:
                """Return 'First Author et al.' for 4+ authors, else join all."""
                if not authors:
                    return "Unknown authors"
                if len(authors) <= 3:
                    return ", ".join(authors)
                return f"{authors[0]} et al."

            pub_cards_html = ""
            # Sort newest-first, entries without a year go last
            sorted_pubs = sorted(bibliography, key=lambda p: p.get("year") or 0, reverse=True)
            for idx, pub in enumerate(sorted_pubs, start=1):
                title   = pub.get("title", "Untitled")
                authors = _fmt_authors(pub.get("authors", []))
                journal = pub.get("journal", "")
                year    = pub.get("year", "")
                volume  = pub.get("volume", "")
                pages   = pub.get("pages", "")
                doi     = pub.get("doi", "")
                oa      = pub.get("open_access", False)

                # Journal + volume/pages string
                journal_str = journal
                if volume:
                    journal_str += f", {volume}"
                if pages:
                    journal_str += f":{pages}"

                # DOI link
                doi_url = pub.get("url", f"https://doi.org/{doi}" if doi else "")
                if doi_url:
                    doi_html = f'<a class="pub-badge doi" href="{doi_url}" target="_blank" rel="noopener">DOI: {doi}</a>'
                elif doi:
                    doi_html = f'<span class="pub-badge doi">DOI: {doi}</span>'
                else:
                    doi_html = ""

                oa_html = '<span class="pub-badge oa">Open Access</span>' if oa else ""

                title_html = (
                    f'<a href="{doi_url}" target="_blank" rel="noopener">{title}</a>'
                    if doi_url else title
                )

                pub_cards_html += f"""
                    <div class="pub-card">
                        <div class="pub-number">{idx}</div>
                        <div class="pub-content">
                            <div class="pub-title">{title_html}</div>
                            <div class="pub-authors">{authors}</div>
                            <div class="pub-meta">
                                {"" if not journal_str else f'<span class="pub-badge journal">{journal_str}</span>'}
                                {"" if not year else f'<span class="pub-badge year">{year}</span>'}
                                {doi_html}
                                {oa_html}
                            </div>
                        </div>
                    </div>"""

            html += f"""
        <div class="publications-box">
            <div class="publications-title">Related Publications</div>
            <div class="pub-list">{pub_cards_html}
            </div>
        </div>
"""

        html += """
        <div class="charts-grid">
"""

        # ── Standard per-condition plots ──────────────────────────────────
        html += f"""
            <div class="chart-container">
                <div class="chart-title">Reaction Time Distribution</div>
                <div id="{proj_name}_rt_violin"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Accuracy Distribution</div>
                <div id="{proj_name}_acc_violin"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">RT Scatter — Outlier Detection</div>
                <div id="{proj_name}_rt_scatter"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Accuracy Scatter — Outlier Detection</div>
                <div id="{proj_name}_acc_scatter"></div>
            </div>
"""

        # ── Learning-stage progression (full-width, before radar) ─────────
        if report.get('learning_stage_data'):
            html += f"""
            <div class="chart-container">
                <div class="chart-title">RT Progression across Learning Stages</div>
                <div id="{proj_name}_stage_rt"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Accuracy Progression across Learning Stages</div>
                <div id="{proj_name}_stage_acc"></div>
            </div>
"""

        # ── Reliability radars (full-width) ──────────────────────────────
        if reliability:
            html += f"""
            <div class="chart-container full-width-container">
                <div class="chart-title">Reliability Metrics Radar — Task Conditions</div>
                <div id="{proj_name}_radar_task"></div>
            </div>
"""
        if control_reliability:
            html += f"""
            <div class="chart-container full-width-container">
                <div class="chart-title">Reliability Metrics Radar — Control / Rest Conditions</div>
                <div id="{proj_name}_radar_control"></div>
            </div>
"""

        # ── Reliability explanation panel removed — now lives in the main dashboard ──

        html += """
        </div>
    </div>

    <div class="container">
        <div class="btn-container">
            <a href="../../dashboard.html" class="btn-secondary">← Back to Dashboard</a>
        </div>
    </div>

    <script>
"""
        html += self._generate_plots_js(proj_name, data_by_cond, reliability,
                                        report['trial_types'],
                                        report.get('learning_stage_data', {}),
                                        control_reliability)
        html += """
    </script>
</body>
</html>"""
        return html
    
    def save_project_html(self, project_name: str, html_content: str):
        """Save project HTML report"""
        output_path = self.base_path / "Projects" / project_name / f"{project_name}_overview.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  Saved HTML: {output_path}")
        return output_path
    
    def save_project_json(self, project_name: str, report: Dict):
        """Save project JSON report"""
        output_path = self.base_path / "Projects" / project_name / f"{project_name}_data.json"
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"  Saved JSON: {output_path}")
        return output_path


def main():

    _SCRIPT_DIR = Path(__file__).resolve().parent          # → .../BEEHub/code/
    _DEFAULT_BASE = _SCRIPT_DIR.parent                    # → .../BEEHub/
    
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
        print(base_path)
    else:
        base_path = str(_DEFAULT_BASE)
        
    
    generator = ProjectOverviewGenerator(base_path)
    generator.run()


if __name__ == "__main__":
    main()
