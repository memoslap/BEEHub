#!/usr/bin/env python3
"""
Generate HTML Report from Saved Reliability Metrics
Loads pre-computed metrics from JSON files and creates comparison report
Fixed version with proper error handling and data loading
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from scipy.stats import ttest_ind
import warnings
warnings.filterwarnings('ignore')

class ReliabilityReportGenerator:
    def __init__(self, metrics_dir):
        self.metrics_dir = Path(metrics_dir)
        self.projects_data = {}
        self.subject_dfs = {}
        self.index_data = None
        
    def load_all_metrics(self):
        """Load all pre-computed metrics from JSON files"""
        print("=" * 70)
        print("📊 RELIABILITY REPORT GENERATOR")
        print("=" * 70)
        print(f"\n📂 Loading pre-computed reliability metrics...")
        print(f"   Metrics directory: {self.metrics_dir}")
        
        # Check if metrics directory exists
        if not self.metrics_dir.exists():
            print(f"\n❌ Metrics directory not found: {self.metrics_dir}")
            print("   Please run 'generate_project_metrics.py' first")
            return False
        
        # Load index file
        index_file = self.metrics_dir / "projects_index.json"
        if not index_file.exists():
            print(f"\n❌ Index file not found: {index_file}")
            print("   Please run 'generate_project_metrics.py' first")
            
            # Try to find any summary files as fallback
            summary_files = list(self.metrics_dir.glob("*_summary.json"))
            if summary_files:
                print(f"\n   Found {len(summary_files)} summary files without index.")
                print("   Attempting to load them directly...")
                
                for summary_file in summary_files:
                    try:
                        with open(summary_file, 'r') as f:
                            data = json.load(f)
                            project = data.get('project', summary_file.stem.replace('_summary', ''))
                            self.projects_data[project] = data
                            print(f"   ✅ Loaded {project} directly")
                    except Exception as e:
                        print(f"   ❌ Error loading {summary_file.name}: {e}")
                
                return len(self.projects_data) > 0
            return False
        
        # Load index file
        try:
            with open(index_file, 'r') as f:
                self.index_data = json.load(f)
            print(f"\n   ✅ Loaded index file")
            print(f"   Found projects: {', '.join(self.index_data.get('projects', []))}")
        except Exception as e:
            print(f"\n❌ Error loading index file: {e}")
            return False
        
        # Load summary statistics for each project
        projects = self.index_data.get('projects', [])
        if not projects:
            print("\n   ⚠️  No projects found in index file")
            return False
        
        for project in projects:
            # Try to load summary file
            summary_file = self.metrics_dir / self.index_data['files']['summary'].get(project, f"{project}_summary.json")
            if summary_file.exists():
                try:
                    with open(summary_file, 'r') as f:
                        self.projects_data[project] = json.load(f)
                    print(f"   ✅ Loaded {project}: {self.projects_data[project].get('n_subjects', 0)} subjects")
                except Exception as e:
                    print(f"   ❌ Error loading {project} summary: {e}")
            else:
                print(f"   ⚠️  Summary file not found for {project}: {summary_file}")
            
            # Try to load CSV for subject-level data
            csv_file = self.metrics_dir / self.index_data['files']['csv'].get(project, f"{project}_metrics.csv")
            if csv_file.exists():
                try:
                    self.subject_dfs[project] = pd.read_csv(csv_file)
                    print(f"   ✅ Loaded {project} CSV: {len(self.subject_dfs[project])} subjects")
                except Exception as e:
                    print(f"   ❌ Error loading {project} CSV: {e}")
        
        return len(self.projects_data) > 0
    
    def get_metric_value(self, project, metric, stat='mean'):
        """Extract specific metric value from summary data"""
        if project not in self.projects_data:
            return np.nan
        
        project_data = self.projects_data[project]
        summary = project_data.get('summary', {})
        
        if metric in summary:
            metric_stats = summary[metric]
            if stat in metric_stats:
                value = metric_stats[stat]
                # Convert to float if possible
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return np.nan
        return np.nan
    
    def format_metric(self, value, decimals=3):
        """Format metric value for display"""
        if value is None or pd.isna(value):
            return 'N/A'
        if isinstance(value, (int, float)):
            return f"{value:.{decimals}f}"
        return str(value)
    
    def get_all_projects_metric_comparison(self, metric, stat='mean'):
        """Get a metric value for all projects"""
        values = {}
        for project in self.projects_data.keys():
            values[project] = self.get_metric_value(project, metric, stat)
        return values
    
    def generate_html(self, output_path='reliability_report.html'):
        """Generate comprehensive HTML report"""
        
        # Get generation timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate total subjects
        total_subjects = 0
        for project in self.projects_data:
            total_subjects += self.projects_data[project].get('n_subjects', 0)
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test-Retest Reliability Report - Cross-Project Comparison</title>
    <style>
        :root {{
            --primary: #4361ee;
            --secondary: #3f37c9;
            --success: #4cc9f0;
            --warning: #f72585;
            --info: #4895ef;
            --light: #f8f9fa;
            --dark: #212529;
            --gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
            color: var(--dark);
            line-height: 1.6;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            background: var(--gradient);
            color: white;
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '📊';
            position: absolute;
            right: 40px;
            bottom: 20px;
            font-size: 120px;
            opacity: 0.1;
        }}
        
        h1 {{
            font-size: 36px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        h2 {{
            font-size: 24px;
            margin-bottom: 20px;
            color: var(--primary);
            border-bottom: 3px solid var(--primary);
            padding-bottom: 10px;
            display: inline-block;
        }}
        
        h3 {{
            font-size: 20px;
            margin: 30px 0 20px;
            color: var(--dark);
        }}
        
        .project-card {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.1);
        }}
        
        .project-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }}
        
        .project-title {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .project-icon {{
            font-size: 40px;
        }}
        
        .badge {{
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            color: white;
        }}
        
        .badge-subjects {{
            background: var(--primary);
        }}
        
        .badge-sessions {{
            background: var(--success);
            color: var(--dark);
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 30px 0;
        }}
        
        .metric-card {{
            background: var(--light);
            border-radius: 15px;
            padding: 20px;
            border-left: 5px solid var(--primary);
            transition: all 0.3s ease;
        }}
        
        .metric-card:hover {{
            background: white;
            box-shadow: 0 5px 20px rgba(67, 97, 238, 0.1);
        }}
        
        .metric-title {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 32px;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 5px;
        }}
        
        .metric-stats {{
            font-size: 13px;
            color: #666;
        }}
        
        .metric-stats span {{
            font-weight: 600;
            color: var(--dark);
        }}
        
        .table-container {{
            overflow-x: auto;
            margin: 30px 0;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
        }}
        
        th {{
            background: var(--primary);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tr:hover td {{
            background: #f5f5f5;
        }}
        
        .comparison-table td:first-child {{
            font-weight: 600;
        }}
        
        .better {{
            background: #d4edda;
            color: #155724;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
        }}
        
        .worse {{
            background: #f8d7da;
            color: #721c24;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 13px;
            font-weight: 600;
            display: inline-block;
        }}
        
        .positive-diff {{
            color: #28a745;
            font-weight: 700;
        }}
        
        .negative-diff {{
            color: #dc3545;
            font-weight: 700;
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            color: #666;
            font-size: 13px;
            padding: 20px;
            border-top: 1px solid #ddd;
        }}
        
        .info-box {{
            background: #e7f3ff;
            border-left: 5px solid var(--info);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .warning-box {{
            background: #fff3cd;
            border-left: 5px solid #ffc107;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 10px;
            background: #eee;
            border-radius: 5px;
            margin-top: 10px;
        }}
        
        .progress-fill {{
            height: 10px;
            background: var(--gradient);
            border-radius: 5px;
        }}
        
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 200px;
            background: var(--dark);
            color: white;
            text-align: center;
            padding: 10px;
            border-radius: 6px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        
        @media (max-width: 768px) {{
            .header {{ padding: 30px; }}
            h1 {{ font-size: 28px; }}
            .metrics-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Test-Retest Reliability Report</h1>
            <p style="font-size: 18px; opacity: 0.95; margin-top: 10px;">Cross-Project Comparison of Behavioral Metrics</p>
            <div style="display: flex; gap: 30px; margin-top: 20px; flex-wrap: wrap;">
                <div><span style="font-weight: 700;">Generated:</span> {timestamp}</div>
                <div><span style="font-weight: 700;">Projects:</span> {len(self.projects_data)}</div>
                <div><span style="font-weight: 700;">Total Subjects:</span> {total_subjects}</div>
                <div><span style="font-weight: 700;">Metrics Directory:</span> {self.metrics_dir.name}</div>
            </div>
        </div>
'''
        
        # Check if we have any projects
        if not self.projects_data:
            html_content += '''
        <div class="warning-box">
            <strong>⚠️ No Project Data Found</strong><br>
            <p>No reliability metrics were found. Please run 'generate_project_metrics.py' first to generate metrics for your projects.</p>
        </div>
        '''
        else:
            # Generate individual project sections
            for project in self.projects_data.keys():
                project_data = self.projects_data[project]
                summary = project_data.get('summary', {})
                n_subjects = project_data.get('n_subjects', 0)
                generated = project_data.get('generated', 'Unknown')
                
                # Determine project icon
                project_icon = '🎯' if 'APPL' in project.upper() else '🧠' if 'OLMM' in project.upper() else '📊'
                
                html_content += f'''
        <div class="project-card">
            <div class="project-header">
                <div class="project-title">
                    <span class="project-icon">{project_icon}</span>
                    <h2 style="margin: 0; border-bottom: none;">{project} Project</h2>
                </div>
                <div style="display: flex; gap: 15px;">
                    <span class="badge badge-subjects">Subjects: {n_subjects}</span>
                    <span class="badge badge-sessions">Sessions: ses-3, ses-4</span>
                </div>
            </div>
            <div style="font-size: 12px; color: #666; margin-bottom: 20px;">
                Generated: {generated[:10] if generated != 'Unknown' else 'Unknown'}
            </div>
            
            <div class="metrics-grid">
'''
                
                # Key metrics cards
                key_metrics = [
                    ('🎯', 'Accuracy Reliability', 'accuracy_pearson_r', 'Pearson r'),
                    ('📊', 'Accuracy Agreement', 'accuracy_cohen_kappa', "Cohen's κ"),
                    ('⚡', 'RT Reliability', 'rt_pearson_r', 'Pearson r'),
                    ('✅', 'Percent Agreement', 'accuracy_percent_agreement', '% Agreement'),
                    ('📚', 'Learning Stage', 'learning_stage_agreement', 'Consistency'),
                    ('🔄', 'Response Bias', 'response_bias_stability', 'Stability')
                ]
                
                for icon, label, metric, metric_label in key_metrics:
                    mean_val = self.get_metric_value(project, metric, 'mean')
                    std_val = self.get_metric_value(project, metric, 'std')
                    n_val = self.get_metric_value(project, metric, 'n')
                    
                    if not np.isnan(mean_val):
                        html_content += f'''
                <div class="metric-card">
                    <div class="metric-title">{icon} {label} <span style="font-weight: normal; color: #999;">({metric_label})</span></div>
                    <div class="metric-value">{mean_val:.3f}</div>
                    <div class="metric-stats">
                        <span>±{std_val:.3f}</span> (SD) • n={int(n_val) if not np.isnan(n_val) else 0}
                    </div>
                </div>
                    '''
                
                html_content += '''
            </div>
'''
                
                # Performance summary
                acc_ses3 = self.get_metric_value(project, 'learning_accuracy_ses3', 'mean')
                acc_ses4 = self.get_metric_value(project, 'learning_accuracy_ses4', 'mean')
                rt_ses3 = self.get_metric_value(project, 'learning_rt_mean_ses3', 'mean')
                rt_ses4 = self.get_metric_value(project, 'learning_rt_mean_ses4', 'mean')
                
                if not np.isnan(acc_ses3) and not np.isnan(acc_ses4):
                    html_content += f'''
            <div class="info-box">
                <strong>📋 Performance Summary</strong><br>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                    <div>🎯 Accuracy: <strong>{acc_ses3:.1%}</strong> (ses-3) → <strong>{acc_ses4:.1%}</strong> (ses-4)</div>
                    <div>⚡ Response Time: <strong>{rt_ses3:.0f}ms</strong> (ses-3) → <strong>{rt_ses4:.0f}ms</strong> (ses-4)</div>
                </div>
            </div>
'''
                
                # Detailed metrics table
                html_content += '''
            <h3>📊 Detailed Reliability Metrics</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Metric</th>
                            <th>Mean</th>
                            <th>SD</th>
                            <th>Median</th>
                            <th>25th %ile</th>
                            <th>75th %ile</th>
                            <th>N</th>
                        </tr>
                    </thead>
                    <tbody>
'''
                
                # Detailed metrics table rows
                detailed_metrics = [
                    ('Accuracy (Pearson r)', 'accuracy_pearson_r'),
                    ('Accuracy (Spearman r)', 'accuracy_spearman_r'),
                    ('Accuracy (Cohen\'s κ)', 'accuracy_cohen_kappa'),
                    ('Accuracy (% Agreement)', 'accuracy_percent_agreement'),
                    ('RT (Pearson r)', 'rt_pearson_r'),
                    ('RT (Spearman r)', 'rt_spearman_r'),
                    ('RT (ICC)', 'rt_icc'),
                    ('RT Mean Difference (ms)', 'rt_mean_difference'),
                    ('RT Cohen\'s d', 'rt_cohen_d'),
                    ('Learning Stage Agreement', 'learning_stage_agreement'),
                    ('Response Bias Stability', 'response_bias_stability'),
                    ('Common Stimuli (n)', 'n_common_stimuli'),
                    ('Correct Trials Both (n)', 'n_correct_both')
                ]
                
                for label, metric in detailed_metrics:
                    mean_val = self.get_metric_value(project, metric, 'mean')
                    std_val = self.get_metric_value(project, metric, 'std')
                    median_val = self.get_metric_value(project, metric, 'median')
                    q25_val = self.get_metric_value(project, metric, 'q25')
                    q75_val = self.get_metric_value(project, metric, 'q75')
                    n_val = self.get_metric_value(project, metric, 'n')
                    
                    if not np.isnan(mean_val):
                        html_content += f'''
                    <tr>
                        <td>{label}</td>
                        <td>{mean_val:.3f}</td>
                        <td>{std_val:.3f}</td>
                        <td>{median_val:.3f}</td>
                        <td>{q25_val:.3f}</td>
                        <td>{q75_val:.3f}</td>
                        <td>{int(n_val) if not np.isnan(n_val) else 0}</td>
                    </tr>
                    '''
                
                html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
            
            # Cross-project comparison section
            if len(self.projects_data) >= 2:
                html_content += '''
        <div class="project-card">
            <h2 style="border-bottom-color: var(--warning);">🔄 Cross-Project Comparison</h2>
            
            <div class="metrics-grid">
'''
                
                # Statistical comparison between projects
                projects_list = list(self.projects_data.keys())
                
                # Accuracy reliability comparison
                acc_values = []
                acc_errors = []
                for proj in projects_list:
                    mean_val = self.get_metric_value(proj, 'accuracy_pearson_r', 'mean')
                    std_val = self.get_metric_value(proj, 'accuracy_pearson_r', 'std')
                    if not np.isnan(mean_val):
                        acc_values.append(mean_val)
                        acc_errors.append(std_val)
                    else:
                        acc_values.append(np.nan)
                        acc_errors.append(np.nan)
                
                # RT reliability comparison
                rt_values = []
                rt_errors = []
                for proj in projects_list:
                    mean_val = self.get_metric_value(proj, 'rt_pearson_r', 'mean')
                    std_val = self.get_metric_value(proj, 'rt_pearson_r', 'std')
                    if not np.isnan(mean_val):
                        rt_values.append(mean_val)
                        rt_errors.append(std_val)
                    else:
                        rt_values.append(np.nan)
                        rt_errors.append(np.nan)
                
                # Display comparison cards
                for i, proj1 in enumerate(projects_list):
                    for j, proj2 in enumerate(projects_list):
                        if i < j:  # Only compare each pair once
                            acc_diff = acc_values[i] - acc_values[j] if not (np.isnan(acc_values[i]) or np.isnan(acc_values[j])) else np.nan
                            rt_diff = rt_values[i] - rt_values[j] if not (np.isnan(rt_values[i]) or np.isnan(rt_values[j])) else np.nan
                            
                            html_content += f'''
                <div class="metric-card" style="border-left-color: var(--warning);">
                    <div class="metric-title">{proj1} vs {proj2}</div>
                    <div style="margin-top: 15px;">
                        <div style="font-size: 16px; font-weight: 600; margin-bottom: 10px;">Accuracy Reliability</div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>{proj1}: <strong>{acc_values[i]:.3f}</strong></span>
                            <span>{proj2}: <strong>{acc_values[j]:.3f}</strong></span>
                        </div>
                        <div style="font-size: 18px; font-weight: 700; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            Difference: <span class="{'positive-diff' if acc_diff > 0 else 'negative-diff' if acc_diff < 0 else ''}">{acc_diff:+.3f}</span>
                            <span style="font-size: 14px; font-weight: normal; margin-left: 10px;">
                                Better: <span class="better">{proj1 if acc_diff > 0 else proj2 if acc_diff < 0 else 'Equal'}</span>
                            </span>
                        </div>
                        
                        <div style="font-size: 16px; font-weight: 600; margin: 20px 0 10px;">RT Reliability</div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                            <span>{proj1}: <strong>{rt_values[i]:.3f}</strong></span>
                            <span>{proj2}: <strong>{rt_values[j]:.3f}</strong></span>
                        </div>
                        <div style="font-size: 18px; font-weight: 700; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            Difference: <span class="{'positive-diff' if rt_diff > 0 else 'negative-diff' if rt_diff < 0 else ''}">{rt_diff:+.3f}</span>
                            <span style="font-size: 14px; font-weight: normal; margin-left: 10px;">
                                Better: <span class="better">{proj1 if rt_diff > 0 else proj2 if rt_diff < 0 else 'Equal'}</span>
                            </span>
                        </div>
                    </div>
                </div>
                '''
                
                html_content += '''
            </div>
            
            <h3>📋 Project Comparison Summary</h3>
            <div class="table-container">
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
'''
                
                # Add project headers
                for project in projects_list:
                    html_content += f'<th>{project}</th>'
                html_content += '<th>Difference</th><th>Better Reliability</th>'
                html_content += '''
                        </tr>
                    </thead>
                    <tbody>
'''
                
                # Comparison metrics
                comparison_metrics = [
                    ('Accuracy (Pearson r)', 'accuracy_pearson_r'),
                    ('Accuracy (Cohen\'s κ)', 'accuracy_cohen_kappa'),
                    ('Accuracy (% Agreement)', 'accuracy_percent_agreement'),
                    ('RT (Pearson r)', 'rt_pearson_r'),
                    ('RT (ICC)', 'rt_icc'),
                    ('Learning Stage Agreement', 'learning_stage_agreement'),
                    ('Response Bias Stability', 'response_bias_stability')
                ]
                
                for label, metric in comparison_metrics:
                    values = []
                    for project in projects_list:
                        val = self.get_metric_value(project, metric, 'mean')
                        values.append(val)
                    
                    # Calculate difference between first two projects
                    if len(values) >= 2 and not (np.isnan(values[0]) or np.isnan(values[1])):
                        diff = values[0] - values[1]
                        better = projects_list[0] if diff > 0 else projects_list[1] if diff < 0 else 'Equal'
                        diff_class = 'positive-diff' if diff > 0 else 'negative-diff' if diff < 0 else ''
                    else:
                        diff = np.nan
                        better = 'N/A'
                        diff_class = ''
                    
                    html_content += '<tr>'
                    html_content += f'<td>{label}</td>'
                    
                    for val in values:
                        if not np.isnan(val):
                            html_content += f'<td>{val:.3f}</td>'
                        else:
                            html_content += '<td>N/A</td>'
                    
                    if not np.isnan(diff):
                        html_content += f'<td class="{diff_class}">{diff:+.3f}</td>'
                    else:
                        html_content += '<td>N/A</td>'
                    
                    html_content += f'<td><span class="better">{better}</span></td>'
                    html_content += '</tr>'
                
                html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
        
        # Add footer
        html_content += f'''
        <div class="footer">
            <p>🧪 Test-Retest Reliability Analysis | Behavioral Experiments Hub</p>
            <p>Metrics computed using Pearson/Spearman correlations, Cohen's Kappa, and ICC</p>
            <p>📁 Metrics source: {self.metrics_dir}</p>
            <p>⚠️ N/A indicates insufficient data for reliability computation</p>
            <p style="margin-top: 20px; font-size: 11px;">Generated by generate_reliability_report.py • {timestamp}</p>
        </div>
    </div>
</body>
</html>
'''
        
        # Save HTML report
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n{'='*70}")
        print(f"✅ HTML REPORT GENERATED")
        print(f"{'='*70}")
        print(f"\n📁 Report saved to: {output_path.absolute()}")
        print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"\n🌐 Open in browser to view the interactive report")
        
        return html_content

def main():
    """Main execution function"""
    # Set metrics directory
    metrics_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
    
    # Initialize report generator
    generator = ReliabilityReportGenerator(metrics_dir)
    
    # Load all metrics
    if generator.load_all_metrics():
        # Generate HTML report
        output_path = metrics_dir / "test_retest_reliability_report.html"
        generator.generate_html(output_path)
    else:
        print("\n❌ Failed to load any project metrics.")
        print("\nPlease run the following command first:")
        print("   python generate_project_metrics.py")
        print("\nThis will generate the necessary metrics files in:")
        print(f"   {metrics_dir}")

if __name__ == "__main__":
    main()