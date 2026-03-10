#!/usr/bin/env python3
"""
Generate Individual HTML Reports for Each Project
Creates detailed standalone reports with visualizations
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

class IndividualProjectReporter:
    def __init__(self, metrics_dir):
        self.metrics_dir = Path(metrics_dir)
        self.output_dir = metrics_dir / "individual_reports"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def load_project_data(self, project):
        """Load metrics for a specific project"""
        csv_file = self.metrics_dir / f"{project}_metrics.csv"
        summary_file = self.metrics_dir / f"{project}_summary.json"
        
        if not csv_file.exists() or not summary_file.exists():
            return None, None
        
        df = pd.read_csv(csv_file)
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        return df, summary
    
    def create_accuracy_reliability_plot(self, df, project):
        """Create accuracy reliability scatter plot"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['learning_accuracy_ses3'],
            y=df['learning_accuracy_ses4'],
            mode='markers',
            marker=dict(
                size=12,
                color=df['accuracy_pearson_r'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Pearson r"),
                line=dict(width=1, color='white')
            ),
            text=df['subject'],
            hovertemplate='<b>Subject: %{text}</b><br>' +
                         'Ses-3: %{x:.2%}<br>' +
                         'Ses-4: %{y:.2%}<br>' +
                         'Reliability: %{marker.color:.3f}<br>' +
                         '<extra></extra>'
        ))
        
        # Add diagonal line
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            line=dict(dash='dash', color='rgba(255,255,255,0.5)', width=2),
            name='Perfect Reliability',
            hovertemplate='<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Accuracy Test-Retest Reliability - {project}',
                font=dict(size=20, color='white')
            ),
            xaxis=dict(
                title='Session 3 Accuracy',
                tickformat='.0%',
                gridcolor='rgba(255,255,255,0.1)',
                range=[0, 1.05]
            ),
            yaxis=dict(
                title='Session 4 Accuracy',
                tickformat='.0%',
                gridcolor='rgba(255,255,255,0.1)',
                range=[0, 1.05]
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            hoverlabel=dict(bgcolor='black', font=dict(color='white')),
            width=800,
            height=600
        )
        
        return fig
    
    def create_rt_reliability_plot(self, df, project):
        """Create RT reliability scatter plot"""
        # Filter subjects with valid RT correlations
        df_rt = df.dropna(subset=['rt_pearson_r', 'learning_rt_mean_ses3', 'learning_rt_mean_ses4'])
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df_rt['learning_rt_mean_ses3'],
            y=df_rt['learning_rt_mean_ses4'],
            mode='markers',
            marker=dict(
                size=12,
                color=df_rt['rt_pearson_r'],
                colorscale='Plasma',
                showscale=True,
                colorbar=dict(title="Pearson r"),
                line=dict(width=1, color='white')
            ),
            text=df_rt['subject'],
            hovertemplate='<b>Subject: %{text}</b><br>' +
                         'Ses-3 RT: %{x:.0f}ms<br>' +
                         'Ses-4 RT: %{y:.0f}ms<br>' +
                         'Reliability: %{marker.color:.3f}<br>' +
                         '<extra></extra>'
        ))
        
        # Add diagonal line
        rt_max = max(df_rt['learning_rt_mean_ses3'].max(), df_rt['learning_rt_mean_ses4'].max()) * 1.1
        
        fig.add_trace(go.Scatter(
            x=[0, rt_max],
            y=[0, rt_max],
            mode='lines',
            line=dict(dash='dash', color='rgba(255,255,255,0.5)', width=2),
            name='Perfect Reliability',
            hovertemplate='<extra></extra>'
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Response Time Test-Retest Reliability - {project}',
                font=dict(size=20, color='white')
            ),
            xaxis=dict(
                title='Session 3 RT (ms)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            yaxis=dict(
                title='Session 4 RT (ms)',
                gridcolor='rgba(255,255,255,0.1)'
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            hoverlabel=dict(bgcolor='black', font=dict(color='white')),
            width=800,
            height=600
        )
        
        return fig
    
    def create_metrics_radar_chart(self, summary, project):
        """Create radar chart for key reliability metrics"""
        metrics = [
            'accuracy_pearson_r',
            'accuracy_cohen_kappa',
            'accuracy_percent_agreement',
            'rt_pearson_r',
            'rt_icc',
            'learning_stage_agreement',
            'response_bias_stability'
        ]
        
        labels = [
            'Accuracy<br>Pearson r',
            'Accuracy<br>Cohen\'s κ',
            'Accuracy<br>% Agreement',
            'RT<br>Pearson r',
            'RT<br>ICC',
            'Learning Stage<br>Consistency',
            'Response Bias<br>Stability'
        ]
        
        values = []
        for metric in metrics:
            val = summary.get('summary', {}).get(metric, {}).get('mean', np.nan)
            values.append(val if not np.isnan(val) else 0)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=project,
            line=dict(color='#4d6cf5', width=3),
            fillcolor='rgba(77, 108, 245, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1],
                    color='white',
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                angularaxis=dict(
                    color='white',
                    gridcolor='rgba(255,255,255,0.2)'
                ),
                bgcolor='rgba(0,0,0,0)'
            ),
            title=dict(
                text=f'Reliability Metrics Profile - {project}',
                font=dict(size=20, color='white')
            ),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            width=800,
            height=600
        )
        
        return fig
    
    def create_performance_boxplots(self, df, project):
        """Create boxplots comparing session performance"""
        # Prepare data
        acc_ses3 = df['learning_accuracy_ses3'].dropna()
        acc_ses4 = df['learning_accuracy_ses4'].dropna()
        rt_ses3 = df['learning_rt_mean_ses3'].dropna()
        rt_ses4 = df['learning_rt_mean_ses4'].dropna()
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Accuracy', 'Response Time'],
            specs=[[{'type': 'box'}, {'type': 'box'}]]
        )
        
        # Accuracy boxplot
        fig.add_trace(
            go.Box(
                y=acc_ses3,
                name='Session 3',
                marker_color='#4d6cf5',
                boxmean='sd'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Box(
                y=acc_ses4,
                name='Session 4',
                marker_color='#9d4edd',
                boxmean='sd'
            ),
            row=1, col=1
        )
        
        # RT boxplot
        fig.add_trace(
            go.Box(
                y=rt_ses3,
                name='Session 3',
                marker_color='#4d6cf5',
                boxmean='sd'
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Box(
                y=rt_ses4,
                name='Session 4',
                marker_color='#9d4edd',
                boxmean='sd'
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title=dict(
                text=f'Performance Distribution - {project}',
                font=dict(size=20, color='white')
            ),
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            width=1000,
            height=500
        )
        
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', row=1, col=1)
        fig.update_xaxes(gridcolor='rgba(255,255,255,0.1)', row=1, col=2)
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', tickformat='.0%', row=1, col=1)
        fig.update_yaxes(gridcolor='rgba(255,255,255,0.1)', row=1, col=2)
        
        return fig
    
    def create_reliability_heatmap(self, df, project):
        """Create correlation heatmap of reliability metrics"""
        # Select reliability metrics
        metrics = [
            'accuracy_pearson_r',
            'accuracy_cohen_kappa',
            'accuracy_percent_agreement',
            'rt_pearson_r',
            'rt_icc',
            'learning_stage_agreement',
            'response_bias_stability',
            'n_common_stimuli'
        ]
        
        # Filter available metrics
        available_metrics = [m for m in metrics if m in df.columns]
        corr_df = df[available_metrics].dropna()
        
        if len(corr_df) < 2:
            return None
        
        corr_matrix = corr_df.corr()
        
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='Viridis',
            zmin=-1, zmax=1,
            text=corr_matrix.values.round(2),
            texttemplate='%{text}',
            textfont={'color': 'white', 'size': 10},
            hoverongaps=False,
            colorbar=dict(title='Correlation', tickfont=dict(color='white'))
        ))
        
        fig.update_layout(
            title=dict(
                text=f'Reliability Metrics Correlation - {project}',
                font=dict(size=20, color='white')
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            width=800,
            height=800,
            xaxis=dict(tickangle=45, tickfont=dict(color='white')),
            yaxis=dict(tickfont=dict(color='white'))
        )
        
        return fig
    
    def fig_to_html(self, fig):
        """Convert plotly figure to HTML div"""
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def generate_project_report(self, project):
        """Generate individual HTML report for a project"""
        print(f"\n📊 Generating report for {project}...")
        
        df, summary = self.load_project_data(project)
        if df is None:
            print(f"   ❌ No data found for {project}")
            return
        
        # Create visualizations
        print(f"   🎨 Creating visualizations...")
        
        acc_plot = self.create_accuracy_reliability_plot(df, project)
        rt_plot = self.create_rt_reliability_plot(df, project)
        radar_plot = self.create_metrics_radar_chart(summary, project)
        boxplot = self.create_performance_boxplots(df, project)
        heatmap = self.create_reliability_heatmap(df, project)
        
        # Get summary statistics
        n_subjects = len(df)
        acc_mean = df['accuracy_pearson_r'].mean()
        acc_std = df['accuracy_pearson_r'].std()
        rt_mean = df['rt_pearson_r'].mean()
        rt_std = df['rt_pearson_r'].std()
        
        # Generate HTML
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project} - Test-Retest Reliability Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        :root {{
            --primary: {'#4d6cf5' if 'APPL' in project.upper() else '#20c9c9' if 'OLMM' in project.upper() else '#9d4edd'};
            --primary-glow: {'rgba(77,108,245,0.3)' if 'APPL' in project.upper() else 'rgba(32,201,201,0.3)' if 'OLMM' in project.upper() else 'rgba(157,78,221,0.3)'};
            --gradient: linear-gradient(135deg, {('#4d6cf5, #9d4edd' if 'APPL' in project.upper() else '#20c9c9, #4d6cf5' if 'OLMM' in project.upper() else '#9d4edd, #ff70a6')});
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 20% 30%, #0a0c14, #030405);
            color: #ffffff;
            line-height: 1.6;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(10, 12, 20, 0.98));
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 30px;
            padding: 40px;
            margin-bottom: 40px;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 30%, var(--primary-glow), transparent 70%);
            pointer-events: none;
        }}
        
        .project-badge {{
            display: inline-block;
            padding: 12px 30px;
            background: var(--gradient);
            border-radius: 50px;
            font-weight: 700;
            font-size: 18px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px var(--primary-glow);
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 25px;
            margin: 40px 0;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 25px;
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            border-color: var(--primary);
            box-shadow: 0 10px 30px var(--primary-glow);
        }}
        
        .stat-label {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: #a0a0b0;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 42px;
            font-weight: 700;
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
        }}
        
        .stat-desc {{
            font-size: 14px;
            color: #b0b0c0;
            margin-top: 10px;
        }}
        
        .viz-container {{
            background: rgba(20, 25, 40, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 30px;
            padding: 30px;
            margin: 40px 0;
        }}
        
        .section-title {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .section-title span {{
            font-size: 32px;
        }}
        
        .metrics-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .metrics-table th {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-radius: 10px 10px 0 0;
        }}
        
        .metrics-table td {{
            padding: 15px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        
        .metrics-table tr:hover td {{
            background: rgba(255,255,255,0.05);
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            color: #808090;
            font-size: 13px;
            padding: 30px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }}
        
        .plot-wrapper {{
            margin: 30px 0;
            border-radius: 15px;
            overflow: hidden;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="project-badge">{project} PROJECT</div>
            <h1 style="font-size: 48px; margin-bottom: 20px;">Test-Retest Reliability Analysis</h1>
            <p style="font-size: 18px; color: #b0b0c0;">Sessions: ses-3 / ses-4 • Subjects: {n_subjects} • Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Subjects</div>
                <div class="stat-value">{n_subjects}</div>
                <div class="stat-desc">with complete ses-3/ses-4 data</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Accuracy Reliability</div>
                <div class="stat-value">{acc_mean:.3f}</div>
                <div class="stat-desc">±{acc_std:.3f} SD • Pearson r</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">RT Reliability</div>
                <div class="stat-value">{rt_mean:.3f}</div>
                <div class="stat-desc">±{rt_std:.3f} SD • Pearson r</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Common Stimuli</div>
                <div class="stat-value">{df['n_common_stimuli'].mean():.0f}</div>
                <div class="stat-desc">average per subject</div>
            </div>
        </div>
        
        <div class="viz-container">
            <div class="section-title">
                <span>🎯</span> Accuracy Reliability
            </div>
            <div class="plot-wrapper">
                {self.fig_to_html(acc_plot)}
            </div>
        </div>
        
        <div class="viz-container">
            <div class="section-title">
                <span>⚡</span> Response Time Reliability
            </div>
            <div class="plot-wrapper">
                {self.fig_to_html(rt_plot)}
            </div>
        </div>
        
        <div class="viz-container">
            <div class="section-title">
                <span>📊</span> Performance Distribution
            </div>
            <div class="plot-wrapper">
                {self.fig_to_html(boxplot)}
            </div>
        </div>
        
        <div class="viz-container">
            <div class="section-title">
                <span>🕸️</span> Reliability Profile
            </div>
            <div class="plot-wrapper">
                {self.fig_to_html(radar_plot)}
            </div>
        </div>
'''
        
        if heatmap:
            html_content += f'''
        <div class="viz-container">
            <div class="section-title">
                <span>🔥</span> Metrics Correlation
            </div>
            <div class="plot-wrapper">
                {self.fig_to_html(heatmap)}
            </div>
        </div>
'''
        
        html_content += f'''
        <div class="viz-container">
            <div class="section-title">
                <span>📋</span> Subject-Level Metrics
            </div>
            <div style="overflow-x: auto;">
                <table class="metrics-table">
                    <thead>
                        <tr>
                            <th>Subject</th>
                            <th>Accuracy r</th>
                            <th>Cohen's κ</th>
                            <th>% Agreement</th>
                            <th>RT r</th>
                            <th>RT ICC</th>
                            <th>Learning Stage</th>
                            <th>Bias Stability</th>
                            <th>Common Stimuli</th>
                        </tr>
                    </thead>
                    <tbody>
'''
        
        # Add subject rows
        for _, row in df.head(20).iterrows():
            html_content += f'''
                        <tr>
                            <td><strong>{row['subject']}</strong></td>
                            <td>{row['accuracy_pearson_r']:.3f}</td>
                            <td>{row['accuracy_cohen_kappa']:.3f}</td>
                            <td>{row['accuracy_percent_agreement']:.1%}</td>
                            <td>{row['rt_pearson_r']:.3f}</td>
                            <td>{row['rt_icc']:.3f}</td>
                            <td>{row['learning_stage_agreement']:.1%}</td>
                            <td>{row['response_bias_stability']:.1%}</td>
                            <td>{row['n_common_stimuli']:.0f}</td>
                        </tr>
            '''
        
        if len(df) > 20:
            html_content += f'''
                        <tr>
                            <td colspan="9" style="text-align: center; font-style: italic;">
                                ... and {len(df) - 20} more subjects
                            </td>
                        </tr>
            '''
        
        html_content += f'''
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>⚡ {project} Test-Retest Reliability Report</p>
            <p>Generated by Behavioral Experiments Hub • {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
        </div>
    </div>
</body>
</html>
'''
        
        # Save report
        output_file = self.output_dir / f"{project}_reliability_report.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"   ✅ Saved: {output_file}")
        return output_file
    
    def generate_all_reports(self):
        """Generate reports for all projects"""
        print("\n" + "="*70)
        print("📈 INDIVIDUAL PROJECT REPORTS GENERATOR")
        print("="*70)
        
        # Find all project CSV files
        csv_files = list(self.metrics_dir.glob("*_metrics.csv"))
        projects = [f.stem.replace("_metrics", "") for f in csv_files]
        
        generated = []
        for project in projects:
            report_file = self.generate_project_report(project)
            if report_file:
                generated.append(project)
        
        print(f"\n{'='*70}")
        print(f"✅ GENERATED {len(generated)} PROJECT REPORTS")
        print(f"{'='*70}")
        print(f"\n📁 Reports saved to: {self.output_dir}")
        for project in generated:
            print(f"   • {project}_reliability_report.html")
        
        return generated

def main():
    metrics_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
    reporter = IndividualProjectReporter(metrics_dir)
    reporter.generate_all_reports()

if __name__ == "__main__":
    main()