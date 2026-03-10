#!/usr/bin/env python3
"""
Generate Test-Retest Reliability Metrics for Individual Projects
Saves metrics as JSON files that can be later aggregated
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import cohen_kappa_score
import warnings
warnings.filterwarnings('ignore')

class ProjectMetricsGenerator:
    def __init__(self, project_name, base_path):
        self.project_name = project_name
        self.base_path = Path(base_path)
        self.sessions = ['ses-3', 'ses-4']
        self.output_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def load_project_data(self):
        """Load all TSV files for the project"""
        project_data = {session: [] for session in self.sessions}
        project_path = self.base_path / self.project_name / 'bids_data' 
        
        if not project_path.exists():
            print(f"⚠️  Path not found: {project_path}")
            return project_data
        
        for session in self.sessions:
            # Try different naming patterns
            patterns = [
                f'*{session}*_task-APPL*_beh.tsv',
                f'*{session}*_beh.tsv',
                f'sub-*_{session}_*.tsv'
            ]
            
            for pattern in patterns:
                session_files = list(project_path.rglob(pattern))
                if session_files:
                    break
            
            for file_path in session_files:
                try:
                    df = pd.read_csv(file_path, sep='\t', na_values=['n/a','N/A'])
                    # Extract subject ID
                    subject = file_path.stem.split('_')[0]
                    df['subject'] = subject
                    df['session'] = session
                    project_data[session].append(df)
                    print(f"  ✅ Loaded: {file_path.name}")
                except Exception as e:
                    print(f"  ❌ Error loading {file_path.name}: {e}")
        
        return project_data
    
    def compute_icc(self, x, y):
        """Compute Intraclass Correlation Coefficient (ICC)"""
        if len(x) < 2 or len(y) < 2:
            return np.nan
        df = pd.DataFrame({'ses3': x, 'ses4': y})
        df['mean'] = df.mean(axis=1)
        df['diff'] = df['ses3'] - df['ses4']
        ms_between = np.var(df['mean']) * 2
        ms_within = np.var(df['diff']) / 2
        if ms_between + ms_within > 0:
            return ms_between / (ms_between + ms_within)
        return np.nan
    
    def compute_reliability_metrics(self, df_ses3, df_ses4):
        """Compute all test-retest reliability metrics for a subject"""
        metrics = {
            'subject': df_ses3['subject'].iloc[0] if not df_ses3.empty else None,
            'project': self.project_name,
            'n_trials_ses3': len(df_ses3),
            'n_trials_ses4': len(df_ses4)
        }
        
        # Separate learning and control trials
        learning_ses3 = df_ses3[df_ses3['trial_type'] == 'learning'].copy()
        learning_ses4 = df_ses4[df_ses4['trial_type'] == 'learning'].copy()
        control_ses3 = df_ses3[df_ses3['trial_type'] == 'control'].copy()
        control_ses4 = df_ses4[df_ses4['trial_type'] == 'control'].copy()
        
        # Add trial counts
        metrics.update({
            'n_learning_trials_ses3': len(learning_ses3),
            'n_learning_trials_ses4': len(learning_ses4),
            'n_control_trials_ses3': len(control_ses3),
            'n_control_trials_ses4': len(control_ses4)
        })
        
        # 1. OVERALL PERFORMANCE METRICS
        # Learning accuracy
        metrics['learning_accuracy_ses3'] = learning_ses3['accuracy_binary'].mean() if len(learning_ses3) > 0 else np.nan
        metrics['learning_accuracy_ses4'] = learning_ses4['accuracy_binary'].mean() if len(learning_ses4) > 0 else np.nan
        #metrics['learning_accuracy_diff'] = metrics['learning_accuracy_ses3'] - metrics['learning_accuracy_ses4']
        metrics['learning_accuracy_diff'] = (
        (metrics['learning_accuracy_ses3'] or 0)
            - (metrics['learning_accuracy_ses4'] or 0)
            if pd.notna(metrics['learning_accuracy_ses3']) and pd.notna(metrics['learning_accuracy_ses4'])
            else np.nan
            )
        
        # Control accuracy (should be near ceiling)
        metrics['control_accuracy_ses3'] = control_ses3['accuracy_binary'].mean() if len(control_ses3) > 0 else np.nan
        metrics['control_accuracy_ses4'] = control_ses4['accuracy_binary'].mean() if len(control_ses4) > 0 else np.nan
        
        # Mean RT (correct trials only)
        correct_learning_ses3 = learning_ses3[learning_ses3['accuracy_binary'] == 1]
        correct_learning_ses4 = learning_ses4[learning_ses4['accuracy_binary'] == 1]
        
        metrics['learning_rt_mean_ses3'] = correct_learning_ses3['response_time_ms'].mean() if len(correct_learning_ses3) > 0 else np.nan
        metrics['learning_rt_mean_ses4'] = correct_learning_ses4['response_time_ms'].mean() if len(correct_learning_ses4) > 0 else np.nan
        metrics['learning_rt_diff'] = metrics['learning_rt_mean_ses3'] - metrics['learning_rt_mean_ses4']
        
        # Response bias (preference for port 100)
        metrics['response_bias_ses3'] = (learning_ses3['response_port'] == 100).mean() if len(learning_ses3) > 0 else np.nan
        metrics['response_bias_ses4'] = (learning_ses4['response_port'] == 100).mean() if len(learning_ses4) > 0 else np.nan
        metrics['response_bias_stability'] = 1 - abs(metrics['response_bias_ses3'] - metrics['response_bias_ses4'])
        
        # 2. STIMULUS-LEVEL RELIABILITY METRICS
        # Extract stimulus IDs
        learning_ses3['stim_id'] = learning_ses3['stimulus'].str.extract(r'PICTURE_(\d+)\.jpg')[0]
        learning_ses4['stim_id'] = learning_ses4['stimulus'].str.extract(r'PICTURE_(\d+)\.jpg')[0]
        




        
        # Merge on stimulus ID
        merged = pd.merge(
            learning_ses3[['stim_id', 'accuracy_binary', 'response_time_ms', 'learning_stage']],
            learning_ses4[['stim_id', 'accuracy_binary', 'response_time_ms', 'learning_stage']],
            on='stim_id',
            suffixes=('_ses3', '_ses4')
        )
        
        metrics['n_common_stimuli'] = len(merged)
        
        if len(merged) >= 2:
            # 2.1 ACCURACY RELIABILITY
            acc_ses3 = merged['accuracy_binary_ses3'].values
            acc_ses4 = merged['accuracy_binary_ses4'].values
            
            # Pearson/Spearman correlations
            if np.std(acc_ses3) > 0 and np.std(acc_ses4) > 0:
                metrics['accuracy_pearson_r'] = pearsonr(acc_ses3, acc_ses4)[0]
                metrics['accuracy_spearman_r'] = spearmanr(acc_ses3, acc_ses4)[0]
            else:
                metrics['accuracy_pearson_r'] = np.nan
                metrics['accuracy_spearman_r'] = np.nan
            
            # Cohen's Kappa
            try:
                metrics['accuracy_cohen_kappa'] = cohen_kappa_score(acc_ses3, acc_ses4)
            except:
                metrics['accuracy_cohen_kappa'] = np.nan
            
            # Percent agreement
            metrics['accuracy_percent_agreement'] = np.mean(acc_ses3 == acc_ses4)
            
            # 2.2 RESPONSE TIME RELIABILITY (correct trials only)
            correct_both = merged[(merged['accuracy_binary_ses3'] == 1) & (merged['accuracy_binary_ses4'] == 1)]
            
            if len(correct_both) >= 2:
                rt_ses3 = correct_both['response_time_ms_ses3'].values
                rt_ses4 = correct_both['response_time_ms_ses4'].values
                
                metrics['rt_pearson_r'] = pearsonr(rt_ses3, rt_ses4)[0]
                metrics['rt_spearman_r'] = spearmanr(rt_ses3, rt_ses4)[0]
                metrics['rt_icc'] = self.compute_icc(rt_ses3, rt_ses4)
                metrics['rt_mean_difference'] = np.mean(rt_ses3 - rt_ses4)
                metrics['rt_std_difference'] = np.std(rt_ses3 - rt_ses4)
                metrics['rt_cohen_d'] = metrics['rt_mean_difference'] / metrics['rt_std_difference'] if metrics['rt_std_difference'] > 0 else np.nan
                metrics['n_correct_both'] = len(correct_both)
            else:
                metrics['rt_pearson_r'] = np.nan
                metrics['rt_spearman_r'] = np.nan
                metrics['rt_icc'] = np.nan
                metrics['rt_mean_difference'] = np.nan
                metrics['rt_std_difference'] = np.nan
                metrics['rt_cohen_d'] = np.nan
                metrics['n_correct_both'] = len(correct_both)
            
            # 2.3 LEARNING STAGE CONSISTENCY
            metrics['learning_stage_agreement'] = np.mean(merged['learning_stage_ses3'] == merged['learning_stage_ses4'])
            
            # 2.4 BY-LEARNING STAGE RELIABILITY
            for stage in ['LS1', 'LS2', 'LS3', 'LS4']:
                stage_data = merged[merged['learning_stage_ses3'] == stage]
                if len(stage_data) >= 2:
                    metrics[f'accuracy_reliability_{stage}'] = stage_data['accuracy_binary_ses3'].corr(
                        stage_data['accuracy_binary_ses4']) if stage_data['accuracy_binary_ses3'].std() > 0 else np.nan
                else:
                    metrics[f'accuracy_reliability_{stage}'] = np.nan
        
        return metrics
    
    def generate_project_metrics(self):
        """Generate and save metrics for the entire project"""
        print(f"\n📊 Generating metrics for {self.project_name}...")
        
        # Load data
        project_data = self.load_project_data()
        
        ses3_data = pd.concat(project_data['ses-3'], ignore_index=True) if project_data['ses-3'] else pd.DataFrame()
        ses4_data = pd.concat(project_data['ses-4'], ignore_index=True) if project_data['ses-4'] else pd.DataFrame()
        
        if ses3_data.empty or ses4_data.empty:
            print(f"  ❌ No data found for {self.project_name}")
            return None
        
        # Find subjects with both sessions
        subjects_ses3 = set(ses3_data['subject'].unique())
        subjects_ses4 = set(ses4_data['subject'].unique())
        common_subjects = subjects_ses3.intersection(subjects_ses4)
        
        print(f"  📍 Found {len(common_subjects)} subjects with both sessions")
        
        # Compute metrics for each subject
        subject_metrics = []
        for subject in common_subjects:
            df_ses3 = ses3_data[ses3_data['subject'] == subject]
            df_ses4 = ses4_data[ses4_data['subject'] == subject]
            
            metrics = self.compute_reliability_metrics(df_ses3, df_ses4)
            if metrics and metrics.get('subject'):
                subject_metrics.append(metrics)
        
        if not subject_metrics:
            print(f"  ❌ No valid metrics computed for {self.project_name}")
            return None
        
        # Convert to DataFrame
        df_metrics = pd.DataFrame(subject_metrics)
        
        # Compute summary statistics
        summary_stats = self.compute_summary_statistics(df_metrics)
        
        # Save individual subject metrics
        subject_file = self.output_dir / f"{self.project_name}_subject_metrics.json"
        with open(subject_file, 'w') as f:
            json.dump({
                'project': self.project_name,
                'generated': pd.Timestamp.now().isoformat(),
                'n_subjects': len(df_metrics),
                'subjects': subject_metrics
            }, f, indent=2, default=str)
        print(f"  💾 Saved subject-level metrics: {subject_file}")
        
        # Save summary statistics
        summary_file = self.output_dir / f"{self.project_name}_summary.json"
        with open(summary_file, 'w') as f:
            json.dump({
                'project': self.project_name,
                'generated': pd.Timestamp.now().isoformat(),
                'n_subjects': len(df_metrics),
                'summary': summary_stats
            }, f, indent=2, default=str)
        print(f"  💾 Saved summary statistics: {summary_file}")
        
        # Save as CSV for easy viewing
        csv_file = self.output_dir / f"{self.project_name}_metrics.csv"
        df_metrics.to_csv(csv_file, index=False)
        print(f"  💾 Saved CSV: {csv_file}")
        
        return {
            'project': self.project_name,
            'n_subjects': len(df_metrics),
            'subject_metrics': subject_metrics,
            'summary': summary_stats,
            'df': df_metrics
        }
    
    def compute_summary_statistics(self, df):
        """Compute summary statistics for numeric columns"""
        summary = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            valid_data = df[col].dropna()
            if len(valid_data) > 0:
                summary[col] = {
                    'mean': float(valid_data.mean()),
                    'std': float(valid_data.std()),
                    'median': float(valid_data.median()),
                    'min': float(valid_data.min()),
                    'max': float(valid_data.max()),
                    'q25': float(valid_data.quantile(0.25)),
                    'q75': float(valid_data.quantile(0.75)),
                    'n': int(len(valid_data)),
                    'n_missing': int(df[col].isna().sum())
                }
        
        return summary

def main():
    """Generate metrics for all projects"""
    print("=" * 70)
    print("📈 PROJECT-SPECIFIC RELIABILITY METRICS GENERATOR")
    print("=" * 70)
    
    base_path = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects")
    projects = ['APPL', 'OLMM']  # Add more projects here as needed
    
    all_results = {}
    
    for project in projects:
        generator = ProjectMetricsGenerator(project, base_path)
        result = generator.generate_project_metrics()
        if result:
            all_results[project] = result
    
    # Save master index file
    output_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
    index_file = output_dir / "projects_index.json"
    
    index_data = {
        'generated': pd.Timestamp.now().isoformat(),
        'projects': list(all_results.keys()),
        'n_subjects': {proj: data['n_subjects'] for proj, data in all_results.items()},
        'files': {
            'subject_metrics': {proj: f"{proj}_subject_metrics.json" for proj in all_results.keys()},
            'summary': {proj: f"{proj}_summary.json" for proj in all_results.keys()},
            'csv': {proj: f"{proj}_metrics.csv" for proj in all_results.keys()}
        }
    }
    
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✅ METRICS GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"\n📁 Output directory: {output_dir}")
    print(f"\n📊 Generated metrics for: {', '.join(all_results.keys())}")
    print(f"   Total subjects: {sum(data['n_subjects'] for data in all_results.values())}")
    print(f"\n📄 Files created:")
    print(f"   • Subject-level metrics: [project]_subject_metrics.json")
    print(f"   • Summary statistics: [project]_summary.json")
    print(f"   • CSV tables: [project]_metrics.csv")
    print(f"   • Master index: projects_index.json")
    print(f"\n👉 Next step: Run 'generate_reliability_report.py' to create HTML report")

if __name__ == "__main__":
    main()