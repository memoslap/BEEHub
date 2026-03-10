#!/usr/bin/env python3
"""
Generate HTML Report from Saved Reliability Metrics
Modern Metallic/Neon Design
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
        
        if not self.metrics_dir.exists():
            print(f"\n❌ Metrics directory not found: {self.metrics_dir}")
            print("   Please run 'generate_project_metrics.py' first")
            return False
        
        index_file = self.metrics_dir / "projects_index.json"
        if not index_file.exists():
            print(f"\n❌ Index file not found: {index_file}")
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
        
        try:
            with open(index_file, 'r') as f:
                self.index_data = json.load(f)
            print(f"\n   ✅ Loaded index file")
            print(f"   Found projects: {', '.join(self.index_data.get('projects', []))}")
        except Exception as e:
            print(f"\n❌ Error loading index file: {e}")
            return False
        
        projects = self.index_data.get('projects', [])
        if not projects:
            print("\n   ⚠️  No projects found in index file")
            return False
        
        for project in projects:
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
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return np.nan
        return np.nan
    
    def generate_html(self, output_path='reliability_report.html'):
        """Generate comprehensive HTML report with modern metallic design"""
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        total_subjects = 0
        for project in self.projects_data:
            total_subjects += self.projects_data[project].get('n_subjects', 0)
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test-Retest Reliability Report • Metallic Edition</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --chrome-100: #f8f9fc;
            --chrome-200: #e9ecef;
            --chrome-300: #dee2e6;
            --chrome-400: #ced4da;
            --chrome-500: #adb5bd;
            --chrome-600: #6c757d;
            --chrome-700: #495057;
            --chrome-800: #343a40;
            --chrome-900: #212529;
            
            --neon-blue: #4d6cf5;
            --neon-blue-glow: rgba(77, 108, 245, 0.4);
            --neon-cyan: #20c9c9;
            --neon-cyan-glow: rgba(32, 201, 201, 0.3);
            --neon-purple: #9d4edd;
            --neon-purple-glow: rgba(157, 78, 221, 0.3);
            --neon-pink: #ff70a6;
            --neon-pink-glow: rgba(255, 112, 166, 0.3);
            --neon-green: #70e000;
            --neon-green-glow: rgba(112, 224, 0, 0.3);
            --neon-yellow: #ffd166;
            --neon-yellow-glow: rgba(255, 209, 102, 0.3);
            
            --glass-bg: rgba(255, 255, 255, 0.25);
            --glass-border: rgba(255, 255, 255, 0.5);
            --glass-shadow: rgba(31, 38, 135, 0.1);
            
            --metallic-gradient: linear-gradient(145deg, #e6e9f0, #dce1e8);
            --metallic-shine: linear-gradient(145deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%);
            --neon-gradient: linear-gradient(135deg, var(--neon-blue), var(--neon-purple));
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Space Grotesk', sans-serif;
            background: radial-gradient(circle at 20% 30%, #1a1b2f, #0c0d1c);
            color: #ffffff;
            line-height: 1.6;
            padding: 40px 20px;
            min-height: 100vh;
            position: relative;
        }}
        
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 30%, rgba(77, 108, 245, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 80% 70%, rgba(157, 78, 221, 0.05) 0%, transparent 50%),
                radial-gradient(circle at 40% 80%, rgba(32, 201, 201, 0.05) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}
        
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }}
        
        /* Metallic Header */
        .header {{
            background: linear-gradient(145deg, #2c3e50, #1a2634);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 40px;
            padding: 50px;
            margin-bottom: 50px;
            box-shadow: 
                0 25px 40px -20px rgba(0,0,0,0.5),
                inset 0 -2px 0 rgba(255,255,255,0.1),
                inset 0 2px 0 rgba(255,255,255,0.2);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.1) 0%, transparent 70%);
            pointer-events: none;
        }}
        
        .header::after {{
            content: '⚡';
            position: absolute;
            right: 40px;
            bottom: 20px;
            font-size: 140px;
            opacity: 0.1;
            color: var(--neon-cyan);
            text-shadow: 0 0 20px var(--neon-cyan-glow);
            animation: pulse 4s ease-in-out infinite;
        }}
        
        h1 {{
            font-size: 48px;
            font-weight: 700;
            margin-bottom: 15px;
            background: linear-gradient(135deg, #ffffff, #e0e0ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 20px rgba(77, 108, 245, 0.3);
            letter-spacing: -0.02em;
        }}
        
        /* Neon Cards */
        .project-card {{
            background: rgba(18, 22, 35, 0.8);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 32px;
            padding: 40px;
            margin-bottom: 50px;
            box-shadow: 
                0 20px 40px -15px rgba(0,0,0,0.6),
                inset 0 0 0 1px rgba(255,255,255,0.05);
            position: relative;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        
        .project-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            border-radius: 32px;
            padding: 2px;
            background: linear-gradient(145deg, 
                rgba(255,255,255,0.2),
                rgba(255,255,255,0.05),
                transparent 80%
            );
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }}
        
        .project-card:hover {{
            transform: translateY(-8px);
            box-shadow: 
                0 30px 50px -20px rgba(77, 108, 245, 0.3),
                inset 0 0 0 1px rgba(255,255,255,0.1);
            background: rgba(22, 26, 45, 0.9);
        }}
        
        .project-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }}
        
        .project-title {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        
        .project-icon {{
            font-size: 48px;
            filter: drop-shadow(0 0 15px rgba(77, 108, 245, 0.5));
            animation: float 3s ease-in-out infinite;
        }}
        
        h2 {{
            font-size: 32px;
            font-weight: 600;
            margin: 0;
            background: linear-gradient(145deg, #fff, #b8c1ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.01em;
        }}
        
        /* Metallic Badges */
        .badge {{
            padding: 10px 22px;
            border-radius: 100px;
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.2);
            color: white;
            box-shadow: inset 0 1px 2px rgba(255,255,255,0.3);
        }}
        
        .badge-subjects {{
            background: linear-gradient(145deg, var(--neon-blue), #3849b0);
            border: none;
            box-shadow: 0 5px 15px var(--neon-blue-glow);
        }}
        
        .badge-sessions {{
            background: linear-gradient(145deg, var(--neon-cyan), #1a8c8c);
            border: none;
            box-shadow: 0 5px 15px var(--neon-cyan-glow);
        }}
        
        /* Neon Grid */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 30px;
            margin: 40px 0;
        }}
        
        .metric-card {{
            background: rgba(10, 12, 20, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 25px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }}
        
        .metric-card::after {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.05), transparent);
            transition: left 0.7s ease;
        }}
        
        .metric-card:hover::after {{
            left: 100%;
        }}
        
        .metric-card:hover {{
            border-color: var(--neon-blue);
            box-shadow: 0 0 30px var(--neon-blue-glow);
            transform: scale(1.02);
        }}
        
        .metric-title {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--chrome-400);
            margin-bottom: 15px;
            font-weight: 500;
        }}
        
        .metric-value {{
            font-size: 42px;
            font-weight: 700;
            background: linear-gradient(145deg, #fff, #b8c1ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
            line-height: 1;
        }}
        
        .metric-stats {{
            font-size: 14px;
            color: var(--chrome-400);
            display: flex;
            gap: 15px;
        }}
        
        .metric-stats span {{
            color: var(--neon-cyan);
            font-weight: 600;
        }}
        
        /* Neon Info Box */
        .info-box {{
            background: linear-gradient(145deg, rgba(77, 108, 245, 0.1), rgba(157, 78, 221, 0.1));
            backdrop-filter: blur(12px);
            border: 1px solid rgba(77, 108, 245, 0.3);
            border-radius: 24px;
            padding: 30px;
            margin: 30px 0;
            box-shadow: 0 0 30px rgba(77, 108, 245, 0.1);
            position: relative;
            overflow: hidden;
        }}
        
        .info-box::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: conic-gradient(
                transparent,
                rgba(77, 108, 245, 0.1),
                transparent 30%
            );
            animation: rotate 10s linear infinite;
        }}
        
        /* Glass Table */
        .table-container {{
            overflow-x: auto;
            margin: 40px 0;
            border-radius: 24px;
            background: rgba(10, 12, 20, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            background: transparent;
        }}
        
        th {{
            background: linear-gradient(145deg, rgba(77, 108, 245, 0.3), rgba(157, 78, 221, 0.3));
            color: white;
            padding: 20px;
            text-align: left;
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            font-size: 13px;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }}
        
        td {{
            padding: 18px 20px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            color: var(--chrome-200);
        }}
        
        tr:hover td {{
            background: rgba(77, 108, 245, 0.1);
            color: white;
        }}
        
        /* Neon Comparison */
        .comparison-highlight {{
            background: linear-gradient(145deg, rgba(255, 112, 166, 0.1), rgba(157, 78, 221, 0.1));
            border-left: 4px solid var(--neon-pink);
            position: relative;
        }}
        
        .comparison-highlight::before {{
            content: '⚡';
            position: absolute;
            right: 20px;
            top: 50%;
            transform: translateY(-50%);
            font-size: 24px;
            color: var(--neon-pink);
            text-shadow: 0 0 15px var(--neon-pink-glow);
            animation: pulse 2s ease-in-out infinite;
        }}
        
        .better {{
            background: linear-gradient(145deg, #70e000, #38b000);
            padding: 6px 16px;
            border-radius: 100px;
            font-size: 12px;
            font-weight: 700;
            color: white;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 20px var(--neon-green-glow);
            border: 1px solid rgba(255,255,255,0.3);
        }}
        
        .positive-diff {{
            color: var(--neon-green);
            font-weight: 700;
            text-shadow: 0 0 10px var(--neon-green-glow);
        }}
        
        .negative-diff {{
            color: #ff6b6b;
            font-weight: 700;
            text-shadow: 0 0 10px rgba(255,107,107,0.3);
        }}
        
        /* Animations */
        @keyframes pulse {{
            0%, 100% {{ opacity: 0.1; }}
            50% {{ opacity: 0.2; }}
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-5px); }}
        }}
        
        @keyframes rotate {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        
        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 0 20px var(--neon-blue-glow); }}
            50% {{ box-shadow: 0 0 40px var(--neon-blue-glow); }}
        }}
        
        /* Footer */
        .footer {{
            margin-top: 80px;
            text-align: center;
            color: var(--chrome-400);
            font-size: 13px;
            padding: 30px;
            border-top: 1px solid rgba(255,255,255,0.1);
            position: relative;
        }}
        
        .footer::before {{
            content: '';
            position: absolute;
            top: -1px;
            left: 30%;
            width: 40%;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--neon-blue), var(--neon-purple), transparent);
        }}
        
        /* Loading Bars */
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            margin-top: 15px;
            overflow: hidden;
            position: relative;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--neon-blue), var(--neon-purple));
            border-radius: 4px;
            position: relative;
            animation: shimmer 2s infinite;
        }}
        
        @keyframes shimmer {{
            0% {{ opacity: 1; }}
            50% {{ opacity: 0.8; }}
            100% {{ opacity: 1; }}
        }}
        
        /* Responsive */
        @media (max-width: 768px) {{
            .header {{ padding: 30px; }}
            h1 {{ font-size: 32px; }}
            .project-card {{ padding: 25px; }}
            .metric-value {{ font-size: 32px; }}
        }}
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(10, 12, 20, 0.9);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: linear-gradient(145deg, var(--neon-blue), var(--neon-purple));
            border-radius: 10px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: linear-gradient(145deg, var(--neon-cyan), var(--neon-blue));
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Metallic Header -->
        <div class="header">
            <h1>⚡ TEST-RETEST RELIABILITY</h1>
            <p style="font-size: 20px; opacity: 0.9; margin-top: 15px; color: #e0e0ff; text-shadow: 0 0 10px rgba(77,108,245,0.5);">
                Cross-Project Comparison • Metallic Edition
            </p>
            <div style="display: flex; gap: 40px; margin-top: 30px; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">📅</span>
                    <span style="color: #b8c1ff;">{timestamp}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">🎯</span>
                    <span style="color: #b8c1ff;">{len(self.projects_data)} Projects</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 24px;">👥</span>
                    <span style="color: #b8c1ff;">{total_subjects} Subjects</span>
                </div>
            </div>
        </div>
'''
        
        if not self.projects_data:
            html_content += '''
        <div class="project-card" style="border-left: 4px solid #ff6b6b;">
            <div style="display: flex; align-items: center; gap: 20px;">
                <span style="font-size: 48px;">⚠️</span>
                <div>
                    <h3 style="color: #ff6b6b; margin-bottom: 10px;">No Project Data Found</h3>
                    <p style="color: #adb5bd;">Please run 'generate_project_metrics.py' first to generate metrics for your projects.</p>
                </div>
            </div>
        </div>
        '''
        else:
            for project in self.projects_data.keys():
                project_data = self.projects_data[project]
                summary = project_data.get('summary', {})
                n_subjects = project_data.get('n_subjects', 0)
                generated = project_data.get('generated', 'Unknown')
                
                # Project-specific neon colors
                if 'APPL' in project.upper():
                    neon_color = 'var(--neon-blue)'
                    icon = '🎯'
                    accent_gradient = 'linear-gradient(145deg, #4d6cf5, #9d4edd)'
                elif 'OLMM' in project.upper():
                    neon_color = 'var(--neon-cyan)'
                    icon = '🧠'
                    accent_gradient = 'linear-gradient(145deg, #20c9c9, #4d6cf5)'
                else:
                    neon_color = 'var(--neon-purple)'
                    icon = '📊'
                    accent_gradient = 'linear-gradient(145deg, #9d4edd, #ff70a6)'
                
                html_content += f'''
        <div class="project-card" style="border-top: 4px solid {neon_color};">
            <div class="project-header">
                <div class="project-title">
                    <span class="project-icon">{icon}</span>
                    <h2>{project} Project</h2>
                </div>
                <div style="display: flex; gap: 15px;">
                    <span class="badge badge-subjects">👥 {n_subjects} SUBJECTS</span>
                    <span class="badge badge-sessions">🔄 SES-3 / SES-4</span>
                </div>
            </div>
            
            <div style="display: flex; gap: 20px; margin-bottom: 30px; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.05); padding: 8px 16px; border-radius: 100px; font-size: 12px; color: #b8c1ff;">
                    ⏱️ Generated: {generated[:10] if generated != 'Unknown' else 'Unknown'}
                </span>
            </div>
            
            <div class="metrics-grid">
'''
                
                key_metrics = [
                    ('🎯', 'Accuracy Reliability', 'accuracy_pearson_r', 'Pearson r'),
                    ('📊', 'Accuracy Agreement', 'accuracy_cohen_kappa', "Cohen's κ"),
                    ('⚡', 'RT Reliability', 'rt_pearson_r', 'Pearson r'),
                    ('✅', 'Percent Agreement', 'accuracy_percent_agreement', '% Agreement'),
                    ('📚', 'Learning Stage', 'learning_stage_agreement', 'Consistency'),
                    ('🔄', 'Response Bias', 'response_bias_stability', 'Stability')
                ]
                
                for icon_metric, label, metric, metric_label in key_metrics:
                    mean_val = self.get_metric_value(project, metric, 'mean')
                    std_val = self.get_metric_value(project, metric, 'std')
                    n_val = self.get_metric_value(project, metric, 'n')
                    
                    if not np.isnan(mean_val):
                        html_content += f'''
                <div class="metric-card">
                    <div class="metric-title">{icon_metric} {label}</div>
                    <div class="metric-value">{mean_val:.3f}</div>
                    <div class="metric-stats">
                        <span>±{std_val:.3f}</span> SD • <span>{int(n_val) if not np.isnan(n_val) else 0}</span> subjects
                    </div>
                    <div style="margin-top: 15px; font-size: 11px; color: #6c757d;">
                        {metric_label}
                    </div>
                </div>
                    '''
                
                html_content += '''
            </div>
'''
                
                acc_ses3 = self.get_metric_value(project, 'learning_accuracy_ses3', 'mean')
                acc_ses4 = self.get_metric_value(project, 'learning_accuracy_ses4', 'mean')
                rt_ses3 = self.get_metric_value(project, 'learning_rt_mean_ses3', 'mean')
                rt_ses4 = self.get_metric_value(project, 'learning_rt_mean_ses4', 'mean')
                
                if not np.isnan(acc_ses3) and not np.isnan(acc_ses4):
                    html_content += f'''
            <div class="info-box">
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <span style="font-size: 32px;">📈</span>
                    <h3 style="color: white; margin: 0;">Performance Summary</h3>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px;">
                    <div>
                        <div style="color: #b8c1ff; margin-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 2px;">
                            Accuracy
                        </div>
                        <div style="display: flex; align-items: baseline; gap: 20px;">
                            <div>
                                <span style="font-size: 28px; font-weight: 700; color: white;">{acc_ses3:.1%}</span>
                                <span style="color: #6c757d; margin-left: 5px;">ses-3</span>
                            </div>
                            <span style="color: #4d6cf5;">→</span>
                            <div>
                                <span style="font-size: 28px; font-weight: 700; color: white;">{acc_ses4:.1%}</span>
                                <span style="color: #6c757d; margin-left: 5px;">ses-4</span>
                            </div>
                        </div>
                        <div class="progress-bar" style="margin-top: 15px;">
                            <div class="progress-fill" style="width: {min(acc_ses4 * 100, 100)}%;"></div>
                        </div>
                    </div>
                    <div>
                        <div style="color: #b8c1ff; margin-bottom: 10px; font-size: 13px; text-transform: uppercase; letter-spacing: 2px;">
                            Response Time
                        </div>
                        <div style="display: flex; align-items: baseline; gap: 20px;">
                            <div>
                                <span style="font-size: 28px; font-weight: 700; color: white;">{rt_ses3:.0f}</span>
                                <span style="color: #6c757d; margin-left: 5px;">ms</span>
                            </div>
                            <span style="color: #4d6cf5;">→</span>
                            <div>
                                <span style="font-size: 28px; font-weight: 700; color: white;">{rt_ses4:.0f}</span>
                                <span style="color: #6c757d; margin-left: 5px;">ms</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
'''
                
                html_content += '''
            <h3 style="display: flex; align-items: center; gap: 12px; margin: 40px 0 20px;">
                <span style="font-size: 28px;">📋</span>
                <span style="background: linear-gradient(145deg, #fff, #b8c1ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Detailed Reliability Metrics
                </span>
            </h3>
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
                        <td style="color: white;">{label}</td>
                        <td>{mean_val:.3f}</td>
                        <td>{std_val:.3f}</td>
                        <td>{median_val:.3f}</td>
                        <td>{q25_val:.3f}</td>
                        <td>{q75_val:.3f}</td>
                        <td><span style="background: rgba(77,108,245,0.2); padding: 4px 12px; border-radius: 100px;">{int(n_val) if not np.isnan(n_val) else 0}</span></td>
                    </tr>
                    '''
                
                html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
            
            if len(self.projects_data) >= 2:
                projects_list = list(self.projects_data.keys())
                
                html_content += f'''
        <div class="project-card" style="border-top: 4px solid var(--neon-pink);">
            <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 40px;">
                <span style="font-size: 48px;">⚔️</span>
                <div>
                    <h2 style="margin: 0; background: linear-gradient(145deg, #ff70a6, #9d4edd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        Cross-Project Battle
                    </h2>
                    <p style="color: #b8c1ff; margin-top: 8px;">Direct comparison of reliability metrics</p>
                </div>
            </div>
            
            <div class="metrics-grid">
'''
                
                for i, proj1 in enumerate(projects_list):
                    for j, proj2 in enumerate(projects_list):
                        if i < j:
                            acc1 = self.get_metric_value(proj1, 'accuracy_pearson_r', 'mean')
                            acc2 = self.get_metric_value(proj2, 'accuracy_pearson_r', 'mean')
                            rt1 = self.get_metric_value(proj1, 'rt_pearson_r', 'mean')
                            rt2 = self.get_metric_value(proj2, 'rt_pearson_r', 'mean')
                            
                            if not (np.isnan(acc1) or np.isnan(acc2)):
                                acc_diff = acc1 - acc2
                                rt_diff = rt1 - rt2 if not (np.isnan(rt1) or np.isnan(rt2)) else np.nan
                                
                                better_acc = proj1 if acc_diff > 0 else proj2
                                better_rt = proj1 if rt_diff > 0 else proj2 if not np.isnan(rt_diff) else 'N/A'
                                
                                html_content += f'''
                <div class="metric-card comparison-highlight">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <span style="font-size: 24px; font-weight: 700; background: linear-gradient(145deg, #ff70a6, #9d4edd); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            {proj1} vs {proj2}
                        </span>
                        <span style="font-size: 20px;">⚡</span>
                    </div>
                    
                    <div style="display: grid; gap: 20px;">
                        <div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #b8c1ff;">Accuracy Reliability</span>
                                <span style="font-weight: 700;">
                                    <span style="color: white;">{acc1:.3f}</span> vs 
                                    <span style="color: white;">{acc2:.3f}</span>
                                </span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 20px; font-weight: 700;" class="{"positive-diff" if acc_diff > 0 else "negative-diff"}">
                                    {acc_diff:+.3f}
                                </span>
                                <span class="better">🏆 {better_acc}</span>
                            </div>
                        </div>
                        
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                <span style="color: #b8c1ff;">RT Reliability</span>
                                <span style="font-weight: 700;">
                                    <span style="color: white;">{rt1:.3f}</span> vs 
                                    <span style="color: white;">{rt2:.3f}</span>
                                </span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="font-size: 20px; font-weight: 700;" class="{"positive-diff" if rt_diff > 0 else "negative-diff" if rt_diff < 0 else ''}">
                                    {rt_diff:+.3f if not np.isnan(rt_diff) else 'N/A'}
                                </span>
                                <span class="better">🏆 {better_rt}</span>
                            </div>
                        </div>
                    </div>
                </div>
                '''
                
                html_content += '''
            </div>
            
            <h3 style="display: flex; align-items: center; gap: 12px; margin: 50px 0 20px;">
                <span style="font-size: 28px;">📊</span>
                <span style="background: linear-gradient(145deg, #fff, #b8c1ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Project Comparison Matrix
                </span>
            </h3>
            <div class="table-container">
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Metric</th>
'''
                
                for project in projects_list:
                    html_content += f'<th style="background: linear-gradient(145deg, rgba(77,108,245,0.4), rgba(157,78,221,0.4));">{project}</th>'
                html_content += '<th>Difference</th><th>Winner</th>'
                html_content += '''
                        </tr>
                    </thead>
                    <tbody>
'''
                
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
                    
                    if len(values) >= 2 and not (np.isnan(values[0]) or np.isnan(values[1])):
                        diff = values[0] - values[1]
                        better = projects_list[0] if diff > 0 else projects_list[1]
                        diff_class = 'positive-diff' if diff > 0 else 'negative-diff'
                        diff_display = f'{diff:+.3f}'
                        winner_display = f'<span class="better">{better}</span>'
                    else:
                        diff_display = 'N/A'
                        winner_display = '<span style="color: #6c757d;">N/A</span>'
                        diff_class = ''
                    
                    html_content += '<tr>'
                    html_content += f'<td style="color: white; font-weight: 500;">{label}</td>'
                    
                    for val in values:
                        if not np.isnan(val):
                            html_content += f'<td style="font-size: 16px; font-weight: 600;">{val:.3f}</td>'
                        else:
                            html_content += '<td style="color: #6c757d;">—</td>'
                    
                    html_content += f'<td class="{diff_class}" style="font-size: 16px; font-weight: 700;">{diff_display}</td>'
                    html_content += f'<td>{winner_display}</td>'
                    html_content += '</tr>'
                
                html_content += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
        
        html_content += f'''
        <div class="footer">
            <div style="display: flex; justify-content: center; gap: 60px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 20px;">⚡</span>
                    <span>Pearson/Spearman Correlations</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 20px;">📊</span>
                    <span>Cohen's Kappa</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 20px;">🔄</span>
                    <span>Intraclass Correlation</span>
                </div>
            </div>
            <p style="color: #6c757d; margin-bottom: 10px;">
                ⚡ Test-Retest Reliability Analysis • Behavioral Experiments Hub
            </p>
            <p style="color: #495057; font-size: 11px;">
                Generated by generate_reliability_report.py • {timestamp}
            </p>
            <p style="color: #495057; font-size: 11px; margin-top: 20px;">
                <span style="color: #4d6cf5;">⬤</span> Metallic Edition 
                <span style="color: #9d4edd; margin-left: 15px;">⬤</span> Neon Pulse 
                <span style="color: #20c9c9; margin-left: 15px;">⬤</span> Glass Morphism
            </p>
        </div>
    </div>
</body>
</html>
'''
        
        output_path = Path(output_path)
        output_path.parent.mkdir(exist_ok=True, parents=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n{'='*70}")
        print(f"✅ METALLIC HTML REPORT GENERATED")
        print(f"{'='*70}")
        print(f"\n📁 Report saved to: {output_path.absolute()}")
        print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")
        print(f"\n🌐 Open in browser to experience the metallic/neon design")
        print(f"\n✨ Features:")
        print(f"   • Metallic gradients and glass morphism")
        print(f"   • Neon glow effects and animations")
        print(f"   • Cyberpunk color scheme")
        print(f"   • Interactive hover states")
        print(f"   • Project battle comparisons")
        
        return html_content

def main():
    """Main execution function"""
    metrics_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
    
    generator = ReliabilityReportGenerator(metrics_dir)
    
    if generator.load_all_metrics():
        output_path = metrics_dir / "test_retest_reliability_report_metallic.html"
        generator.generate_html(output_path)
    else:
        print("\n❌ Failed to load any project metrics.")
        print("\nPlease run the following command first:")
        print("   python generate_project_metrics.py")

if __name__ == "__main__":
    main()