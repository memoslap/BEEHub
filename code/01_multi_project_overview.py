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
from typing import Dict, List, Tuple
import warnings
import sys
warnings.filterwarnings('ignore')

# ── Reliability metrics — all calculations live in reliability_metrics.py ────
# Import from the same directory as this script so it works regardless of the
# current working directory.
try:
    import importlib.util as _ilu
    _rm_candidates = [
        Path(__file__).resolve().parent / "reliability_metrics.py",
        Path(__file__).resolve().parent.parent / "reliability_metrics.py",
    ]
    _rm_mod = None
    for _c in _rm_candidates:
        if _c.exists():
            _spec = _ilu.spec_from_file_location("reliability_metrics", _c)
            _rm_mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_rm_mod)
            break
    if _rm_mod is None:
        raise ImportError("reliability_metrics.py not found next to this script.")
    from reliability_metrics import (  # type: ignore  # noqa: E402
        ReliabilityMetrics,
        split_trial_types,
        ALL_METRIC_IDS,
        DEFAULT_OUTCOMES,
        ACCBIN_ID,
        DEFAULT_DISPLAY_PRIORITY,
    )
except ImportError:
    from reliability_metrics import (ReliabilityMetrics, split_trial_types,
                                     ALL_METRIC_IDS, DEFAULT_OUTCOMES, ACCBIN_ID,
                                     DEFAULT_DISPLAY_PRIORITY)

class ProjectOverviewGenerator:
    """Generates comprehensive overview dashboard for all projects"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)

    def _resolve_outcomes(self, project_name: str) -> List[Dict]:
        """Return the outcome list for a project.

        Priority:
        1. ``outcome_measures`` declared in ``<project>_description.json``
        2. ``DEFAULT_OUTCOMES`` from reliability_metrics (RT / ACC / ACCBIN)

        Each entry must have at minimum:
            id, suffix, column, label, axis_label, higher_is_better

        Optional flags (default False):
            is_primary  – this outcome's ACCBIN sibling filters correct trials
            is_binary   – values are 0/1 → displayed as percentages
        """
        desc = self.load_description(project_name)
        custom = desc.get('outcome_measures')
        if custom and isinstance(custom, list) and len(custom) > 0:
            for rank, om in enumerate(custom, start=1):
                om.setdefault('higher_is_better', True)
                om.setdefault('is_primary', False)
                om.setdefault('is_binary', False)
                om.setdefault('is_helper', False)   # True = used for filtering only, not plotted
                om.setdefault('display_priority', rank)
            return custom
        return DEFAULT_OUTCOMES

    def load_description(self, project_name: str) -> Dict:
        """Load project description from <project>/<project>_description.json.

        Returns a dict with at minimum the keys used by the HTML templates
        (full_name, short_description, modality, cognitive_domain, task_type,
        difficulty). Additional rich fields (long_description, background,
        procedure, trial_structure, keywords, design, timing, software) are
        included when present and rendered in the paradigm info panel.

        Falls back gracefully to minimal defaults if the file is absent or
        unparseable — the rest of the pipeline continues normally.
        """
        desc_path = (self.base_path / "Projects" / project_name
                     / f"{project_name}_description.json")
        defaults = {
            'full_name':          project_name,
            'short_description':  'Behavioral task',
            'modality':           'unknown',
            'cognitive_domain':   'unknown',
            'task_type':          'unknown',
            'language':           'unknown',
        }
        if not desc_path.exists():
            return defaults
        try:
            with open(desc_path, encoding='utf-8') as fh:
                data = json.load(fh)
            # Ensure all required keys are present
            for k, v in defaults.items():
                data.setdefault(k, v)
            # Legacy compat: 'description' field used in older JSON → map to short_description
            if 'description' in data and 'short_description' not in data:
                data['short_description'] = data['description']
            return data
        except Exception as e:
            print(f"  Warning: could not load {desc_path.name}: {e}")
            return defaults
    
    def _build_paradigm_panel(self, proj_info: Dict) -> str:
        """Return an HTML <div class='paradigm-panel'> for the overview/dashboard.

        Shows: badge row (no icons), short description, background.
        Detailed sections (procedure, trial structure, design, timing, software,
        keywords) are intentionally omitted here — they live in the paradigm HTML
        generated by 02_generate_paradigm.py.
        """
        short  = proj_info.get('short_description') or proj_info.get('description', '')
        bg     = proj_info.get('background', '')
        modality   = proj_info.get('modality', '')
        domain     = proj_info.get('cognitive_domain', '')
        task_type  = proj_info.get('task_type', '')
        difficulty = proj_info.get('difficulty', '')
        n_sessions = proj_info.get('n_sessions', '')

        # ── Badge row — no icons ─────────────────────────────────────────
        badge_values = [modality, domain, task_type, difficulty]
        if n_sessions:
            badge_values.append(f'{n_sessions} sessions')
        badges_html = ''.join(
            f'<span class="char-badge">{v}</span>'
            for v in badge_values if v and v != 'unknown'
        )

        # ── Description ──────────────────────────────────────────────────
        desc_html = f'<p class="paradigm-text">{short}</p>' if short else ''

        # ── Background (single section, full-width) ───────────────────────
        bg_html = ''
        if bg:
            bg_html = f'''
            <div class="paradigm-panel-grid" style="margin-top:14px;">
                <div class="paradigm-full">
                    <div class="paradigm-section-title">Background</div>
                    <p class="paradigm-text">{bg}</p>
                </div>
            </div>'''

        return f'''<div class="paradigm-panel">
            <div class="char-badges">{badges_html}</div>
            {desc_html}
            {bg_html}
        </div>'''

    def find_projects(self) -> List[str]:
        """Find all project folders"""
        projects_path = self.base_path / "Projects"
        if not projects_path.exists():
            return []
        
        project_folders = [d.name for d in projects_path.iterdir() if d.is_dir()]
        print(f"Found projects: {project_folders}")
        return project_folders
    
    def load_outcome_data(self, project_name: str, outcome) -> pd.DataFrame:
        """Load all TSV files for one outcome measure.

        *outcome* may be:
        - a dict entry from ``_resolve_outcomes`` (preferred), or
        - a legacy string key ``'RT'`` / ``'ACC'`` / ``'ACCBIN'`` (kept for
          backward-compatibility — maps to DEFAULT_OUTCOMES).

        Scans flat bids_data/ and the BIDS sub-*/ses-*/ hierarchy.
        """
        # ── Legacy string key support ────────────────────────────────────────
        if isinstance(outcome, str):
            _legacy = {o['id']: o for o in DEFAULT_OUTCOMES}
            outcome = _legacy.get(outcome, {'id': outcome,
                                            'suffix': f'_{outcome}_beh.tsv',
                                            'column': outcome.lower()})

        bids_path = self.base_path / "Projects" / project_name / "bids_data"
        if not bids_path.exists():
            return pd.DataFrame()

        suffix   = outcome['suffix']
        all_data = []

        for f in bids_path.glob(f"*{suffix}"):
            df = self._load_outcome_file(f)
            if not df.empty:
                all_data.append(df)

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
    
    # ── Metric calculations — delegated to ReliabilityMetrics ────────────────
    # These thin wrappers keep backward-compatibility for any external code
    # that calls generator.calculate_icc(...) etc. directly.

    def calculate_icc(self, data1: np.ndarray, data2: np.ndarray) -> float:
        return ReliabilityMetrics.calculate_icc(data1, data2)
    
    def analyze_project(self, project_name: str) -> Dict:
        """Comprehensive analysis of a project.

        Works with any set of outcome measures — either the standard RT/ACC
        pair or custom outcomes declared in the project's _description.json
        under the ``outcome_measures`` key.
        """
        print(f"\nAnalyzing project: {project_name}")

        # ── Resolve outcomes for this project ────────────────────────────────
        outcomes    = self._resolve_outcomes(project_name)
        # Separate the binary-accuracy outcome used for correct-trial filtering
        accbin_out  = next((o for o in outcomes if o.get('is_binary') or
                            o['id'] == ACCBIN_ID), None)
        # Primary outcomes to visualise and compute reliability for
        # (everything except a pure binary helper like ACCBIN)
        vis_outcomes = [o for o in outcomes if not o.get('is_helper', False)]

        # ── Load data ────────────────────────────────────────────────────────
        participants = self.load_participants_data(project_name)
        loaded: Dict[str, pd.DataFrame] = {}
        for om in outcomes:
            loaded[om['id']] = self.load_outcome_data(project_name, om)

        accbin_data = loaded.get(ACCBIN_ID, pd.DataFrame())
        if accbin_out and accbin_out['id'] != ACCBIN_ID:
            accbin_data = loaded.get(accbin_out['id'], pd.DataFrame())

        # At least one visualisable outcome must be present
        if participants.empty or all(loaded[o['id']].empty for o in vis_outcomes):
            print(f"  No valid data for {project_name}")
            return None

        # ── Get project description ───────────────────────────────────────────
        proj_desc = self.load_description(project_name)

        # ── Demographics ─────────────────────────────────────────────────────
        demographics = {
            'n_participants': len(participants),
            'age_mean': float(participants['age'].mean()) if not participants['age'].isna().all() else None,
            'age_std':  float(participants['age'].std())  if not participants['age'].isna().all() else None,
            'age_min':  float(participants['age'].min())  if not participants['age'].isna().all() else None,
            'age_max':  float(participants['age'].max())  if not participants['age'].isna().all() else None,
            'sex_distribution': participants['sex'].value_counts().to_dict()
        }

        # ── Trial types / sessions from first non-empty outcome ───────────────
        ref_df = next((loaded[o['id']] for o in vis_outcomes
                       if not loaded[o['id']].empty), pd.DataFrame())
        trial_types = (ref_df['trial_type'].unique().tolist()
                       if 'trial_type' in ref_df.columns else [])
        sessions    = (ref_df['session'].unique().tolist()
                       if 'session'    in ref_df.columns else [])

        # ── Correct-trial filtering for primary outcomes ──────────────────────
        corrected: Dict[str, pd.DataFrame] = {}
        for om in vis_outcomes:
            df_om = loaded[om['id']]
            if df_om.empty:
                corrected[om['id']] = df_om
                continue
            if om.get('is_primary', False) and not accbin_data.empty:
                def _add_idx(df):
                    df = df.copy()
                    df['_trial_idx'] = df.groupby(['subject_id', 'session']).cumcount()
                    return df
                om_idx  = _add_idx(df_om)
                acc_idx = _add_idx(accbin_data)
                acc_key = acc_idx[['subject_id', 'session', '_trial_idx',
                                   'accuracy_binary']].copy()
                acc_key['accuracy_binary'] = pd.to_numeric(
                    acc_key['accuracy_binary'], errors='coerce')
                merged = om_idx.merge(acc_key, on=['subject_id', 'session', '_trial_idx'],
                                      how='left', suffixes=('', '_acc'))
                corrected[om['id']] = merged[merged['accuracy_binary'] == 1].drop(
                    columns=['_trial_idx', 'accuracy_binary'], errors='ignore')
            else:
                corrected[om['id']] = df_om

        # ── data_by_condition — generic over all visual outcomes ──────────────
        data_by_condition = {}
        for trial_type in trial_types if trial_types else ['all']:
            for session in sessions if sessions else ['all']:
                key = f"{trial_type}_ses{session}"
                entry: Dict = {
                    'trial_type': trial_type,
                    'session':    session,
                    'outcomes':   {},
                    # Legacy keys for backward-compatible HTML templates:
                    'rt_values':             [],  'rt_mean':  None,
                    'rt_std':                None, 'rt_median': None,
                    'acc_values':            [],  'acc_mean': None,
                    'acc_std':               None,
                    'subject_acc_percentages': [],
                    'n_trials':              0,
                }
                for om in vis_outcomes:
                    df_src = corrected.get(om['id'], pd.DataFrame())
                    if df_src.empty:
                        continue
                    dff = df_src.copy()
                    if trial_types:
                        dff = dff[dff['trial_type'] == trial_type]
                    if sessions:
                        dff = dff[dff['session'] == session]
                    col  = om['column']
                    vals = (pd.to_numeric(dff[col], errors='coerce').dropna().tolist()
                            if col in dff.columns else [])
                    subj_pct = []
                    if om.get('is_binary', False) and 'subject_id' in dff.columns:
                        for subj in dff['subject_id'].unique():
                            sv = pd.to_numeric(
                                dff[dff['subject_id'] == subj][col],
                                errors='coerce').dropna().values
                            if len(sv) > 0:
                                subj_pct.append(float(np.mean(sv) * 100))
                    entry['outcomes'][om['id']] = {
                        'id':               om['id'],
                        'label':            om['label'],
                        'axis_label':       om['axis_label'],
                        'column':           col,
                        'is_binary':        om.get('is_binary', False),
                        'higher_is_better': om.get('higher_is_better', True),
                        'values':           vals,
                        'mean':             float(np.mean(vals))   if vals else None,
                        'std':              float(np.std(vals))    if vals else None,
                        'median':           float(np.median(vals)) if vals else None,
                        'subject_pct':      subj_pct,
                    }
                    # Legacy compat
                    if om['id'] == 'RT':
                        entry['rt_values'] = vals
                        entry['rt_mean']   = entry['outcomes']['RT']['mean']
                        entry['rt_std']    = entry['outcomes']['RT']['std']
                        entry['rt_median'] = entry['outcomes']['RT']['median']
                    if om['id'] == 'ACCBIN':
                        entry['acc_values']              = vals
                        entry['acc_mean']                = entry['outcomes']['ACCBIN']['mean']
                        entry['acc_std']                 = entry['outcomes']['ACCBIN']['std']
                        entry['subject_acc_percentages'] = subj_pct
                entry['n_trials'] = max(
                    (len(entry['outcomes'][o['id']]['values'])
                     for o in vis_outcomes if o['id'] in entry['outcomes']),
                    default=0)
                data_by_condition[key] = entry

        # ── Reliability — computed per outcome, then merged ───────────────────
        task_trial_types, control_trial_types = split_trial_types(trial_types)

        def _compute_rel(tt_list):
            out_rels = []
            for om in vis_outcomes:
                df_om = loaded[om['id']]
                if df_om.empty:
                    continue
                rel = ReliabilityMetrics.compute_for_outcome(
                    df_om, om['column'], om['id'], tt_list,
                    accbin_df=accbin_data if om.get('is_primary') else None,
                    filter_correct=om.get('is_primary', False),
                )
                out_rels.append(rel)
            return ReliabilityMetrics.merge_outcome_reliabilities(out_rels)

        reliability         = _compute_rel(task_trial_types)
        control_reliability = _compute_rel(control_trial_types)

        # Outcome metadata stored in report for use by JS templates
        outcome_meta = [
            {
                'id':               o['id'],
                'label':            o['label'],
                'axis_label':       o['axis_label'],
                'is_binary':        o.get('is_binary', False),
                'display_priority': o.get('display_priority', DEFAULT_DISPLAY_PRIORITY),
            }
            for o in vis_outcomes
        ]
        # ── Learning-stage breakdown (individual project view only) ──────────
        # Detect whether a learning_stage column exists in the RT or ACC data.
        # If so, compute mean RT and mean accuracy per stage × trial_type so the
        # project HTML can show progression charts.  This data is intentionally
        # NOT passed to the radar / reliability metrics.
        # ── Learning-stage breakdown ─────────────────────────────────────────
        # Use the first non-empty visual outcome as the reference for stage
        # detection; compute per-stage means for ALL visual outcomes.
        learning_stage_data = {}
        stage_col = 'learning_stage'
        ref_ls = ref_df   # first non-empty outcome DataFrame, determined above

        def _has_real_stages(df: pd.DataFrame) -> bool:
            if df.empty or stage_col not in df.columns:
                return False
            valid = (df[stage_col].dropna().astype(str).str.strip()
                     .pipe(lambda s: s[s.ne('') & s.str.lower().ne('n/a')]))
            return len(valid) > 0

        has_stages = _has_real_stages(ref_ls)

        if has_stages:
            raw_stages = ref_ls[stage_col].dropna().astype(str).str.strip()
            raw_stages = raw_stages[raw_stages.ne('') & raw_stages.str.lower().ne('n/a')]
            all_stages = sorted(raw_stages.unique().tolist(), key=lambda s: str(s))

            for tt in trial_types if trial_types else ['all']:
                # Build per-stage stats for each visual outcome
                stage_outcomes: Dict[str, Dict] = {}
                for om in vis_outcomes:
                    df_om = loaded[om['id']]
                    if df_om.empty or stage_col not in df_om.columns:
                        continue
                    col = om['column']
                    scale = 100 if om.get('is_binary', False) else 1
                    means, sems = [], []
                    for stage in all_stages:
                        dfs = df_om.copy()
                        if trial_types:
                            dfs = dfs[dfs['trial_type'] == tt]
                        dfs = dfs[dfs[stage_col].astype(str).str.strip() == stage]
                        vals = pd.to_numeric(dfs[col], errors='coerce').dropna() if col in dfs else pd.Series([], dtype=float)
                        means.append(float(vals.mean() * scale) if len(vals) else None)
                        sems.append(float(vals.sem()  * scale) if len(vals) > 1 else None)
                    stage_outcomes[om['id']] = {'means': means, 'sems': sems}

                if not stage_outcomes:
                    continue

                # Legacy keys for backward-compatible HTML (RT + ACC)
                rt_om  = next((o for o in vis_outcomes if o['id'] == 'RT'), None)
                acc_om = next((o for o in vis_outcomes if o.get('is_binary')), None)
                learning_stage_data[tt] = {
                    'stages':       all_stages,
                    'outcomes':     stage_outcomes,
                    # Legacy:
                    'rt_means':     stage_outcomes.get('RT', {}).get('means', [None]*len(all_stages)),
                    'rt_sems':      stage_outcomes.get('RT', {}).get('sems',  [None]*len(all_stages)),
                    'acc_means':    stage_outcomes.get('ACCBIN', {}).get('means', [None]*len(all_stages)),
                    'acc_sems':     stage_outcomes.get('ACCBIN', {}).get('sems',  [None]*len(all_stages)),
                }

        # ── Pick the primary ICC key for the dashboard card ─────────────────
        # Select the ICC key of the highest-priority outcome that actually has
        # data in the reliability dict.  Fallback chain: ACCBIN → RT → first
        # outcome with any ICC value.
        def _pick_primary_icc_key(meta: list, rel: dict) -> str:
            # Try each outcome in priority order
            sorted_meta = sorted(meta, key=lambda o: o.get('display_priority', DEFAULT_DISPLAY_PRIORITY))
            for om in sorted_meta:
                key = f"{om['id'].lower()}_icc_mean"
                if any(m.get(key) is not None for m in rel.values()):
                    return key
            # Fallback: return the first icc_mean key that has actual data
            for m in rel.values():
                for k, v in m.items():
                    if k.endswith('_icc_mean') and v is not None:
                        return k
            return None

        # Compile report
        report = {
            'project_name':            project_name,
            'project_info':            proj_desc,
            'demographics':            demographics,
            'trial_types':             trial_types if trial_types else ['all'],
            'sessions':                sessions    if sessions    else ['all'],
            'data_by_condition':       data_by_condition,
            'reliability_metrics':     reliability,
            'control_reliability':     control_reliability,
            'learning_stage_data':     learning_stage_data,
            'outcome_measures':        outcome_meta,
            'primary_icc_key':         _pick_primary_icc_key(outcome_meta, reliability),
            'column_names': {
                'rt_column':  next((o['column'] for o in vis_outcomes
                                    if o['id'] == 'RT'), None),
                'acc_column': next((o['column'] for o in outcomes
                                    if o.get('is_binary')), None),
            }
        }
        
        return report
    
    def calculate_cohens_d(self, data1: np.ndarray, data2: np.ndarray) -> float:
        return ReliabilityMetrics.calculate_cohens_d(data1, data2)

    def calculate_pearson_r(self, data1: np.ndarray, data2: np.ndarray) -> float:
        return ReliabilityMetrics.calculate_pearson_r(data1, data2)

    def calculate_cv(self, data: np.ndarray) -> float:
        return ReliabilityMetrics.calculate_cv(data)
    
    def _calculate_reliability(self, rt_data: pd.DataFrame, accbin_data: pd.DataFrame,
                               trial_types: List[str]) -> Dict:
        """Delegate to ReliabilityMetrics.compute_reliability_dict.

        Keeping this thin wrapper preserves the existing call-sites in
        analyse_project() unchanged.
        """
        return ReliabilityMetrics.compute_reliability_dict(rt_data, accbin_data, trial_types)

    
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
            background: linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(220,240,230,0.9) 100%);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.88em;
            border: 1px solid rgba(64,158,128,0.45);
            color: #2d7a52;
            font-weight: 500;
        }

        .char-badge.modality { border-color: #2d8659; color: #2d8659; }
        .char-badge.domain { border-color: #409e80; color: #409e80; }
        .char-badge.difficulty { border-color: #ffa726; color: #ffa726; }

        /* ── Paradigm info panel (dashboard card) ── */
        .paradigm-panel {
            background: linear-gradient(135deg, rgba(240,250,245,0.85) 0%, rgba(248,255,252,0.9) 100%);
            border: 1px solid rgba(64,158,128,0.2);
            border-radius: 10px;
            padding: 16px 20px;
            margin-top: 10px;
        }
        .paradigm-panel-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px 28px;
            margin-top: 12px;
        }
        .paradigm-section-title {
            color: #1e5f44;
            font-size: 0.72em;
            font-weight: 700;
            letter-spacing: 1.1px;
            text-transform: uppercase;
            margin-bottom: 4px;
            padding-bottom: 3px;
            border-bottom: 1px solid rgba(64,158,128,0.2);
        }
        .paradigm-text { color: #3a5a4a; font-size: 0.92em; line-height: 1.6; }
        .paradigm-full { grid-column: 1 / -1; }
        .keyword-list { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
        .keyword-chip {
            background: rgba(64,158,128,0.10);
            border: 1px solid rgba(64,158,128,0.28);
            border-radius: 10px;
            padding: 2px 9px;
            font-size: 0.80em;
            color: #2d7a52;
        }
        .timing-grid { display: flex; gap: 10px; flex-wrap: wrap; }
        .timing-item {
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(64,158,128,0.18);
            border-radius: 6px;
            padding: 3px 10px;
            font-size: 0.82em;
            color: #3a5a4a;
        }
        .timing-item span { font-weight: 600; color: #1e5f44; }
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
        
        paradigm_panel_html = self._build_paradigm_panel(proj_info)

        html = f"""
    <div class="project-section">
        <div class="project-header">
            <div class="project-title-section">
                <div class="project-name">{proj_name}</div>
                <div class="project-full-name">{proj_info['full_name']}</div>
                {paradigm_panel_html}
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
        
        # ── Violin + Scatter divs — only for outcomes that have actual data ───
        outcome_meta_local = report.get('outcome_measures') or [
            {'id': 'RT',     'label': 'Reaction Time', 'axis_label': 'RT (ms)',      'is_binary': False},
            {'id': 'ACCBIN', 'label': 'Accuracy',      'axis_label': 'Accuracy (%)', 'is_binary': True},
        ]
        # Determine which outcomes have at least one non-empty value in data_by_condition
        def _outcome_has_data(om_id, is_bin, dbc):
            for cond in dbc.values():
                odata = cond.get('outcomes', {}).get(om_id)
                if odata is not None:
                    vals = odata.get('subject_pct', []) if is_bin else odata.get('values', [])
                    if vals:
                        return True
                # Legacy fallback check
                if om_id == 'RT' and cond.get('rt_values'):
                    return True
                if om_id in ('ACCBIN', 'ACC') and cond.get('subject_acc_percentages'):
                    return True
            return False

        active_outcomes = [
            om for om in outcome_meta_local
            if _outcome_has_data(om['id'], om.get('is_binary', False), data_by_cond)
        ]

        for om in active_outcomes:
            om_id  = om['id'].lower()
            om_lbl = om['label']
            html += f"""
            <div class="chart-container">
                <div class="chart-title">{om_lbl} Distribution</div>
                <div id="{proj_name}_{om_id}_violin"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">{om_lbl} Test-Retest (mean per subject)</div>
                <div id="{proj_name}_{om_id}_scatter"></div>
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
                                        report.get('control_reliability', {}),
                                        outcome_meta=active_outcomes)
        
        html += """
    </script>
"""
        
        return html
    
    def _generate_plots_js(self, proj_name: str, data_by_cond: Dict,
                          reliability: Dict, trial_types: List[str],
                          learning_stage_data: Dict = None,
                          control_reliability: Dict = None,
                          outcome_meta: List[Dict] = None) -> str:
        """Generate JavaScript for all plots.

        outcome_meta: list of outcome dicts from the report (id, label,
        axis_label, is_binary).  When None, falls back to legacy RT/ACC.
        """
        js = ""
        if control_reliability is None:
            control_reliability = {}
        if outcome_meta is None:
            # Legacy fallback
            outcome_meta = [
                {'id': 'RT',     'label': 'Reaction Time', 'axis_label': 'RT (ms)',      'is_binary': False},
                {'id': 'ACCBIN', 'label': 'Accuracy',      'axis_label': 'Accuracy (%)', 'is_binary': True},
            ]
        
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
        
        # ── Violin plots — one per visual outcome ────────────────────────────
        for om in outcome_meta:
            om_id    = om['id']
            is_bin   = om.get('is_binary', False)
            ax_label = om['axis_label']
            div_id   = f"{proj_name}_{om_id.lower()}_violin"

            traces = []
            all_vals = []
            for key, data in data_by_cond.items():
                odata = data.get('outcomes', {}).get(om_id)
                if odata is None:
                    # Legacy fallback
                    if om_id == 'RT':
                        vals = data.get('rt_values', [])
                    elif om_id in ('ACCBIN', 'ACC'):
                        vals = data.get('subject_acc_percentages', [])
                    else:
                        continue
                else:
                    vals = odata['subject_pct'] if is_bin else odata['values']

                if not vals:
                    continue
                all_vals.extend(vals)
                trial_type = data['trial_type']
                session    = data['session']
                color      = colors.get(trial_type, '#8e24aa')
                lbl        = f"{trial_type} (ses-{session})" if session != 'all' else trial_type
                trace = {
                    'y': vals, 'type': 'violin', 'name': lbl,
                    'box': {'visible': True}, 'meanline': {'visible': True},
                    'marker': {'color': color}, 'line': {'color': color},
                }
                if is_bin:
                    trace.update({
                        'spanmode': 'hard', 'bandwidth': 4,
                        'points': 'all', 'jitter': 0.3, 'pointpos': 0,
                        'marker': {'color': color, 'size': 5, 'opacity': 0.6},
                        'fillcolor': color,
                    })
                traces.append(trace)

            if not traces:
                continue

            if is_bin:
                y_min = max(0,   min(all_vals) - 8) if all_vals else 0
                y_max = min(105, max(all_vals) + 8) if all_vals else 105
                range_str = f"[{y_min}, {y_max}]"
            else:
                if all_vals:
                    q1  = float(np.percentile(all_vals, 25))
                    q3  = float(np.percentile(all_vals, 75))
                    iqr = q3 - q1
                    y_min = max(0, q1 - 2.5 * iqr)
                    y_max = q3 + 2.5 * iqr
                else:
                    y_min, y_max = 0, 2000
                range_str = f"[{y_min:.0f}, {y_max:.0f}]"

            js += f"""
        var traces_{om_id} = {json.dumps(traces)};
        var layout_{om_id} = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            height: 420,
            yaxis: {{
                title: '{ax_label}',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 14}},
                range: {range_str}
            }},
            xaxis: {{gridcolor: "rgba(64, 158, 128, 0.2)"}},
            showlegend: true,
            legend: {{bgcolor: "rgba(240,240,240,0.9)",
                      bordercolor: "rgba(64,158,128,0.3)", borderwidth: 1}},
            violingap: 0.3, violinmode: 'group',
            margin: {{l: 60, r: 30, t: 30, b: 50}}
        }};
        Plotly.newPlot('{div_id}', traces_{om_id}, layout_{om_id}, {{responsive: true}});
"""

        # ── Test-Retest Scatter — one plot per visual outcome ───────────────
        all_rel = {**reliability, **control_reliability}
        for om in outcome_meta:
            om_id    = om['id'].lower()
            ax_label = om['axis_label']
            div_id   = f"{proj_name}_{om_id}_scatter"
            scatter_data = []
            all_scatter  = []
            for trial_type, metrics in all_rel.items():
                s1       = metrics.get(f'{om_id}_s1_means', [])
                s2       = metrics.get(f'{om_id}_s2_means', [])
                subj_ids = metrics.get(f'{om_id}_subjects', [])
                ses_lbl  = metrics.get('session_labels', ['ses-1', 'ses-2'])
                if not s1 or not s2:
                    continue
                color   = colors.get(trial_type, '#8e24aa')
                all_scatter.extend(s1 + s2)
                icc_val = metrics.get(f'{om_id}_icc_mean')
                icc_str = f'  ICC={icc_val:.2f}' if icc_val is not None else ''
                dec     = 1 if om.get('is_binary') else 0
                hover   = [f'sub-{sid}<br>{ses_lbl[0]}: {x:.{dec}f}<br>{ses_lbl[1]}: {y:.{dec}f}'
                           for sid, x, y in zip(subj_ids, s1, s2)]
                scatter_data.append({
                    'x': s1, 'y': s2, 'mode': 'markers',
                    'name': f'{trial_type}{icc_str}', 'text': hover,
                    'hovertemplate': '%{text}<extra></extra>',
                    'marker': {'size': 9, 'color': color, 'opacity': 0.75,
                               'line': {'width': 1, 'color': '#ffffff'}},
                })

            if scatter_data and all_scatter:
                ax_min = max(0, min(all_scatter) * 0.92)
                ax_max = max(all_scatter) * 1.08
                ses_lbl = list(reliability.values())[0].get('session_labels', ['ses-1', 'ses-2']) if reliability else ['ses-1', 'ses-2']
                scatter_data.append({
                    'x': [ax_min, ax_max], 'y': [ax_min, ax_max],
                    'mode': 'lines', 'name': 'Identity (perfect retest)',
                    'line': {'color': 'rgba(150,150,150,0.5)', 'width': 1.5, 'dash': 'dash'},
                    'hoverinfo': 'skip',
                })
                js += f"""
        var scatter_{om_id} = {json.dumps(scatter_data)};
        var scatterLayout_{om_id} = {{
            plot_bgcolor: "rgba(255, 255, 255, 0.95)",
            paper_bgcolor: "rgba(250, 250, 250, 0.5)",
            font: {{color: '#333', size: 12}},
            xaxis: {{
                title: '{ax_label} — {ses_lbl[0]}',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 13}},
                range: [{ax_min:.1f}, {ax_max:.1f}]
            }},
            yaxis: {{
                title: '{ax_label} — {ses_lbl[1]}',
                gridcolor: "rgba(64, 158, 128, 0.2)",
                titlefont: {{size: 13}},
                range: [{ax_min:.1f}, {ax_max:.1f}],
                zeroline: false
            }},
            showlegend: true,
            legend: {{bgcolor: "rgba(240,240,240,0.9)",
                      bordercolor: "rgba(64,158,128,0.3)", borderwidth: 1}},
            hovermode: 'closest',
            margin: {{l: 70, r: 30, t: 30, b: 60}}
        }};
        Plotly.newPlot('{div_id}', scatter_{om_id}, scatterLayout_{om_id}, {{responsive: true}});
"""

        # ── Radar helper — delegates to ReliabilityMetrics.build_radar_spokes ──
        def _build_radar_js(rel_dict, div_id, color='#40e0d0', fill='rgba(64, 224, 208, 0.15)',
                            selected_metrics=None):
            categories, values = ReliabilityMetrics.build_radar_spokes(rel_dict, selected_metrics)
            if not categories:
                return ''
            categories.append(categories[0])
            values.append(values[0])
            radar_data = [{
                'type': 'scatterpolar',
                'r': values,
                'theta': categories,
                'fill': 'toself',
                'fillcolor': fill,
                'line': {'color': color, 'width': 3},
                'marker': {'color': color, 'size': 10}
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

        # Control / rest radar — different colour so it is visually distinct
        if control_reliability:
            js += _build_radar_js(control_reliability, f'{proj_name}_radar_control',
                                  color='#ffa726', fill='rgba(255, 167, 38, 0.15)')
        
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
                all_rt_stage = [v for t in rt_stage_traces for v in t['y'] if v is not None]
                rt_y_pad = (max(all_rt_stage) - min(all_rt_stage)) * 0.12 if all_rt_stage else 100
                rt_stage_y_min = max(0, min(all_rt_stage) - rt_y_pad) if all_rt_stage else 0
                rt_stage_y_max = (max(all_rt_stage) + rt_y_pad)       if all_rt_stage else 2000
                rt_layout = dict(shared_layout)
                rt_layout['yaxis'] = {'title': 'Mean RT (ms)',
                                      'gridcolor': 'rgba(64,158,128,0.2)',
                                      'range': [rt_stage_y_min, rt_stage_y_max],
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
            margin-bottom: 8px;
            font-style: italic;
        }}

        .project-description {{
            color: #4a6e5a;
            font-size: 1.05em;
            line-height: 1.6;
            margin-bottom: 16px;
        }}

        .char-badges {{ display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 16px; }}
        .char-badge {{
            background: linear-gradient(135deg,
                rgba(255,255,255,0.85) 0%, rgba(220,240,230,0.9) 100%);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.88em;
            border: 1px solid rgba(64,158,128,0.45);
            color: #2d7a52;
            font-weight: 500;
            box-shadow: 0 1px 4px rgba(64,158,128,0.15),
                        inset 0 1px 0 rgba(255,255,255,0.8);
        }}

        /* ── Paradigm info panel ─────────────────────────────────────── */
        .paradigm-panel {{
            background: linear-gradient(135deg,
                rgba(240,250,245,0.9) 0%, rgba(248,255,252,0.95) 50%, rgba(240,250,245,0.9) 100%);
            border: 1px solid rgba(64,158,128,0.25);
            border-radius: 12px;
            padding: 24px 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 16px rgba(64,158,128,0.08),
                        inset 0 1px 0 rgba(255,255,255,0.9);
        }}

        .paradigm-panel-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px 36px;
            margin-top: 16px;
        }}

        .paradigm-section-title {{
            color: #1e5f44;
            font-size: 0.78em;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-bottom: 6px;
            padding-bottom: 4px;
            border-bottom: 1px solid rgba(64,158,128,0.25);
        }}

        .paradigm-text {{
            color: #3a5a4a;
            font-size: 0.96em;
            line-height: 1.65;
        }}

        .paradigm-full {{
            grid-column: 1 / -1;
        }}

        .keyword-list {{
            display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px;
        }}

        .keyword-chip {{
            background: rgba(64,158,128,0.10);
            border: 1px solid rgba(64,158,128,0.30);
            border-radius: 12px;
            padding: 3px 10px;
            font-size: 0.82em;
            color: #2d7a52;
        }}

        .timing-grid {{
            display: flex; gap: 16px; flex-wrap: wrap;
        }}

        .timing-item {{
            background: rgba(255,255,255,0.7);
            border: 1px solid rgba(64,158,128,0.2);
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 0.85em;
            color: #3a5a4a;
        }}

        .timing-item span {{
            font-weight: 600;
            color: #1e5f44;
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
            {self._build_paradigm_panel(proj_info)}
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

        # ── Per-outcome plots — only for outcomes with actual data ─────────
        om_meta_divs = report.get('outcome_measures') or [
            {'id': 'RT',     'label': 'Reaction Time', 'axis_label': 'RT (ms)',      'is_binary': False},
            {'id': 'ACCBIN', 'label': 'Accuracy',      'axis_label': 'Accuracy (%)', 'is_binary': True},
        ]
        def _has_data(om_id, is_bin, dbc):
            for cond in dbc.values():
                odata = cond.get('outcomes', {}).get(om_id)
                if odata is not None:
                    chk = odata.get('subject_pct', []) if is_bin else odata.get('values', [])
                    if chk:
                        return True
                if om_id == 'RT' and cond.get('rt_values'):
                    return True
                if om_id in ('ACCBIN', 'ACC') and cond.get('subject_acc_percentages'):
                    return True
            return False

        active_om = [o for o in om_meta_divs
                     if _has_data(o['id'], o.get('is_binary', False), data_by_cond)]

        for om in active_om:
            oid  = om['id'].lower()
            olbl = om['label']
            html += f"""
            <div class="chart-container">
                <div class="chart-title">{olbl} Distribution</div>
                <div id="{proj_name}_{oid}_violin"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">{olbl} Test-Retest (mean per subject)</div>
                <div id="{proj_name}_{oid}_scatter"></div>
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
                                        control_reliability,
                                        outcome_meta=active_om)
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
