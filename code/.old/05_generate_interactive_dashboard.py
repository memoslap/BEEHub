#!/usr/bin/env python3
"""
Generate Interactive Combined Dashboard with Search/Filter Capabilities
Creates a comprehensive dashboard with visualizations and dynamic filtering
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

class InteractiveDashboardGenerator:
    def __init__(self, metrics_dir):
        self.metrics_dir = Path(metrics_dir)
        self.output_dir = metrics_dir / "dashboard"
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.all_data = None
        self.summaries = {}
        
    def load_all_data(self):
        """Load all project metrics into a single dataframe"""
        print("\n📂 Loading all project metrics...")
        
        csv_files = list(self.metrics_dir.glob("*_metrics.csv"))
        all_dfs = []
        
        for csv_file in csv_files:
            project = csv_file.stem.replace("_metrics", "")
            df = pd.read_csv(csv_file)
            df['project'] = project
            all_dfs.append(df)
            
            # Load summary
            summary_file = self.metrics_dir / f"{project}_summary.json"
            if summary_file.exists():
                with open(summary_file, 'r') as f:
                    self.summaries[project] = json.load(f)
        
        if all_dfs:
            self.all_data = pd.concat(all_dfs, ignore_index=True)
            print(f"   ✅ Loaded {len(all_dfs)} projects, {len(self.all_data)} subjects")
            return True
        return False
    
    def create_project_comparison_barplot(self):
        """Create bar plot comparing projects on key metrics"""
        metrics = [
            ('accuracy_pearson_r', 'Accuracy Reliability (Pearson r)'),
            ('accuracy_cohen_kappa', 'Accuracy Reliability (Cohen\'s κ)'),
            ('rt_pearson_r', 'RT Reliability (Pearson r)'),
            ('learning_stage_agreement', 'Learning Stage Consistency'),
            ('response_bias_stability', 'Response Bias Stability')
        ]
        
        fig = go.Figure()
        
        for i, (metric, label) in enumerate(metrics):
            project_values = []
            project_errors = []
            projects = []
            
            for project in self.all_data['project'].unique():
                df_proj = self.all_data[self.all_data['project'] == project]
                values = df_proj[metric].dropna()
                
                if len(values) > 0:
                    project_values.append(values.mean())
                    project_errors.append(values.std())
                    projects.append(project)
            
            fig.add_trace(go.Bar(
                name=label,
                x=projects,
                y=project_values,
                error_y=dict(type='data', array=project_errors, visible=True),
                marker_color=px.colors.qualitative.Plotly[i],
                text=[f'{v:.3f}' for v in project_values],
                textposition='auto',
            ))
        
        fig.update_layout(
            title=dict(
                text='Project Comparison: Key Reliability Metrics',
                font=dict(size=24, color='white'),
                x=0.5
            ),
            barmode='group',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=12),
            legend=dict(
                font=dict(color='white'),
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            xaxis=dict(
                title='Project',
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                title='Reliability Coefficient',
                gridcolor='rgba(255,255,255,0.1)',
                tickfont=dict(color='white'),
                range=[0, 1]
            ),
            height=600,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        return fig
    
    def create_subject_scatter_matrix(self):
        """Create scatter matrix of key metrics colored by project"""
        metrics = [
            'accuracy_pearson_r',
            'rt_pearson_r',
            'learning_accuracy_ses3',
            'learning_rt_mean_ses3',
            'n_common_stimuli'
        ]
        
        labels = {
            'accuracy_pearson_r': 'Accuracy Reliability',
            'rt_pearson_r': 'RT Reliability',
            'learning_accuracy_ses3': 'Accuracy (Ses-3)',
            'learning_rt_mean_ses3': 'RT (Ses-3)',
            'n_common_stimuli': 'Common Stimuli'
        }
        
        df_plot = self.all_data[metrics + ['project']].dropna()
        
        fig = px.scatter_matrix(
            df_plot,
            dimensions=metrics,
            color='project',
            labels=labels,
            color_discrete_sequence=px.colors.qualitative.Plotly,
            opacity=0.7
        )
        
        fig.update_traces(
            diagonal_visible=False,
            showupperhalf=False,
            marker=dict(size=8, line=dict(width=1, color='white'))
        )
        
        fig.update_layout(
            title=dict(
                text='Subject-Level Metrics: Multi-Dimensional Comparison',
                font=dict(size=24, color='white'),
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=800,
            width=1200
        )
        
        # Update axis labels
        for i in range(len(metrics)):
            for j in range(len(metrics)):
                fig.update_xaxes(title_text=labels[metrics[j]], row=i+1, col=j+1, 
                               color='white', gridcolor='rgba(255,255,255,0.1)')
                fig.update_yaxes(title_text=labels[metrics[i]], row=i+1, col=j+1,
                               color='white', gridcolor='rgba(255,255,255,0.1)')
        
        return fig
    
    def create_bubble_chart(self):
        """Create bubble chart: Accuracy Reliability vs RT Reliability vs Subjects"""
        project_stats = []
        
        for project in self.all_data['project'].unique():
            df_proj = self.all_data[self.all_data['project'] == project]
            
            acc_rel = df_proj['accuracy_pearson_r'].mean()
            rt_rel = df_proj['rt_pearson_r'].mean()
            n_subjects = len(df_proj)
            acc_std = df_proj['accuracy_pearson_r'].std()
            
            project_stats.append({
                'project': project,
                'accuracy_reliability': acc_rel,
                'rt_reliability': rt_rel,
                'n_subjects': n_subjects,
                'accuracy_std': acc_std
            })
        
        df_stats = pd.DataFrame(project_stats)
        
        fig = px.scatter(
            df_stats,
            x='accuracy_reliability',
            y='rt_reliability',
            size='n_subjects',
            color='project',
            text='project',
            size_max=60,
            hover_data={'accuracy_std': True},
            color_discrete_sequence=px.colors.qualitative.Plotly
        )
        
        fig.update_traces(
            textposition='top center',
            marker=dict(line=dict(width=2, color='white'))
        )
        
        fig.update_layout(
            title=dict(
                text='Project Performance Bubble Chart',
                font=dict(size=24, color='white'),
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(
                title='Accuracy Reliability (Pearson r)',
                gridcolor='rgba(255,255,255,0.1)',
                range=[0, 1],
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                title='RT Reliability (Pearson r)',
                gridcolor='rgba(255,255,255,0.1)',
                range=[0, 1],
                tickfont=dict(color='white')
            ),
            height=600,
            hoverlabel=dict(font=dict(color='white'))
        )
        
        return fig
    
    def create_violin_plots(self):
        """Create violin plots comparing distributions across projects"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Accuracy Reliability', 'RT Reliability', 
                          'Accuracy Performance', 'RT Performance'],
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # Accuracy Reliability
        for project in self.all_data['project'].unique():
            df_proj = self.all_data[self.all_data['project'] == project]
            values = df_proj['accuracy_pearson_r'].dropna()
            
            fig.add_trace(
                go.Violin(
                    y=values,
                    name=project,
                    legendgroup=project,
                    scalegroup=project,
                    side='positive',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    box_visible=True,
                    meanline_visible=True
                ),
                row=1, col=1
            )
        
        # RT Reliability
        for project in self.all_data['project'].unique():
            df_proj = self.all_data[self.all_data['project'] == project]
            values = df_proj['rt_pearson_r'].dropna()
            
            fig.add_trace(
                go.Violin(
                    y=values,
                    name=project,
                    legendgroup=project,
                    scalegroup=project,
                    side='positive',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    box_visible=True,
                    meanline_visible=True,
                    showlegend=False
                ),
                row=1, col=2
            )
        
        # Accuracy Performance
        for project in self.all_data['project'].unique():
            df_proj = self.all_data[self.all_data['project'] == project]
            values_ses3 = df_proj['learning_accuracy_ses3'].dropna()
            values_ses4 = df_proj['learning_accuracy_ses4'].dropna()
            
            fig.add_trace(
                go.Violin(
                    y=values_ses3,
                    name=f'{project} (ses-3)',
                    legendgroup=project,
                    scalegroup=project,
                    side='negative',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    opacity=0.7,
                    showlegend=False
                ),
                row=2, col=1
            )
            
            fig.add_trace(
                go.Violin(
                    y=values_ses4,
                    name=f'{project} (ses-4)',
                    legendgroup=project,
                    scalegroup=project,
                    side='positive',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    opacity=0.7,
                    showlegend=False
                ),
                row=2, col=1
            )
        
        # RT Performance
        for project in self.all_data['project'].unique():
            df_proj = self.all_data[self.all_data['project'] == project]
            values_ses3 = df_proj['learning_rt_mean_ses3'].dropna()
            values_ses4 = df_proj['learning_rt_mean_ses4'].dropna()
            
            fig.add_trace(
                go.Violin(
                    y=values_ses3,
                    name=f'{project} (ses-3)',
                    legendgroup=project,
                    scalegroup=project,
                    side='negative',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    opacity=0.7,
                    showlegend=False
                ),
                row=2, col=2
            )
            
            fig.add_trace(
                go.Violin(
                    y=values_ses4,
                    name=f'{project} (ses-4)',
                    legendgroup=project,
                    scalegroup=project,
                    side='positive',
                    line_color=px.colors.qualitative.Plotly[list(self.all_data['project'].unique()).index(project)],
                    opacity=0.7,
                    showlegend=False
                ),
                row=2, col=2
            )
        
        fig.update_layout(
            title=dict(
                text='Distribution Comparison Across Projects',
                font=dict(size=24, color='white'),
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=800,
            showlegend=True,
            legend=dict(font=dict(color='white'))
        )
        
        fig.update_xaxes(title_text='Project', gridcolor='rgba(255,255,255,0.1)', tickfont=dict(color='white'))
        fig.update_yaxes(title_text='Reliability Coefficient', gridcolor='rgba(255,255,255,0.1)', 
                        tickfont=dict(color='white'), row=1, col=1)
        fig.update_yaxes(title_text='Reliability Coefficient', gridcolor='rgba(255,255,255,0.1)', 
                        tickfont=dict(color='white'), row=1, col=2)
        fig.update_yaxes(title_text='Accuracy', tickformat='.0%', gridcolor='rgba(255,255,255,0.1)', 
                        tickfont=dict(color='white'), row=2, col=1)
        fig.update_yaxes(title_text='RT (ms)', gridcolor='rgba(255,255,255,0.1)', 
                        tickfont=dict(color='white'), row=2, col=2)
        
        return fig
    
    def create_parallel_coordinates(self):
        """Create parallel coordinates plot for multi-dimensional comparison"""
        metrics = [
            'accuracy_pearson_r',
            'rt_pearson_r',
            'learning_stage_agreement',
            'response_bias_stability',
            'n_common_stimuli'
        ]
        
        df_plot = self.all_data[metrics + ['project']].dropna().copy()
        
        # Normalize for coloring
        df_plot['acc_rel_norm'] = (df_plot['accuracy_pearson_r'] - df_plot['accuracy_pearson_r'].min()) / \
                                  (df_plot['accuracy_pearson_r'].max() - df_plot['accuracy_pearson_r'].min())
        
        # Create dimension mapping
        dimensions = []
        for i, metric in enumerate(metrics):
            dimensions.append(
                dict(
                    range=[df_plot[metric].min(), df_plot[metric].max()],
                    label=metric.replace('_', ' ').title(),
                    values=df_plot[metric],
                    tickvals=[df_plot[metric].min(), df_plot[metric].max()],
                    ticktext=[f'{df_plot[metric].min():.2f}', f'{df_plot[metric].max():.2f}']
                )
            )
        
        # Add project dimension
        project_codes = {proj: i for i, proj in enumerate(df_plot['project'].unique())}
        df_plot['project_code'] = df_plot['project'].map(project_codes)
        
        dimensions.append(
            dict(
                range=[0, len(project_codes)-1],
                label='Project',
                values=df_plot['project_code'],
                tickvals=list(project_codes.values()),
                ticktext=list(project_codes.keys())
            )
        )
        
        fig = go.Figure(data=
            go.Parcoords(
                line=dict(
                    color=df_plot['acc_rel_norm'],
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title='Accuracy<br>Reliability', tickfont=dict(color='white'))
                ),
                dimensions=dimensions
            )
        )
        
        fig.update_layout(
            title=dict(
                text='Parallel Coordinates: Subject-Level Multi-Metric Profile',
                font=dict(size=24, color='white'),
                x=0.5
            ),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=600,
            margin=dict(l=100, r=100, t=100, b=50)
        )
        
        return fig
    
    def fig_to_html(self, fig):
        """Convert plotly figure to HTML div"""
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    def generate_dashboard(self):
        """Generate interactive dashboard with search/filter capabilities"""
        if not self.load_all_data():
            print("❌ No data loaded. Cannot generate dashboard.")
            return
        
        print("\n🎨 Creating visualizations...")
        
        # Create all visualizations
        comparison_bar = self.create_project_comparison_barplot()
        scatter_matrix = self.create_subject_scatter_matrix()
        bubble_chart = self.create_bubble_chart()
        violin_plots = self.create_violin_plots()
        parallel_coords = self.create_parallel_coordinates()
        
        print("💾 Generating HTML dashboard...")
        
        # Convert projects list to JavaScript array
        projects_list = list(self.all_data['project'].unique())
        projects_js = json.dumps(projects_list)
        
        # Get all metrics for filtering
        all_metrics = [
            'accuracy_pearson_r', 'accuracy_cohen_kappa', 'accuracy_percent_agreement',
            'rt_pearson_r', 'rt_icc', 'learning_stage_agreement', 
            'response_bias_stability', 'n_common_stimuli', 'n_correct_both',
            'learning_accuracy_ses3', 'learning_accuracy_ses4',
            'learning_rt_mean_ses3', 'learning_rt_mean_ses4'
        ]
        
        metrics_labels = {
            'accuracy_pearson_r': 'Accuracy Reliability (Pearson r)',
            'accuracy_cohen_kappa': 'Accuracy Reliability (Cohen\'s κ)',
            'accuracy_percent_agreement': 'Accuracy % Agreement',
            'rt_pearson_r': 'RT Reliability (Pearson r)',
            'rt_icc': 'RT Reliability (ICC)',
            'learning_stage_agreement': 'Learning Stage Consistency',
            'response_bias_stability': 'Response Bias Stability',
            'n_common_stimuli': 'Number of Common Stimuli',
            'n_correct_both': 'Number of Correct Trials (Both)',
            'learning_accuracy_ses3': 'Accuracy Session 3',
            'learning_accuracy_ses4': 'Accuracy Session 4',
            'learning_rt_mean_ses3': 'RT Mean Session 3',
            'learning_rt_mean_ses4': 'RT Mean Session 4'
        }
        
        # Convert subject data to JSON for filtering
        subject_data_json = self.all_data.to_json(orient='records', date_format='iso')
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BEHub • Interactive Reliability Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0a0c14;
            --bg-card: rgba(20, 25, 40, 0.9);
            --bg-card-hover: rgba(30, 35, 55, 0.95);
            --border: rgba(255, 255, 255, 0.1);
            --border-hover: rgba(77, 108, 245, 0.5);
            --text-primary: #ffffff;
            --text-secondary: #b0b0c0;
            --text-muted: #808090;
            --accent-blue: #4d6cf5;
            --accent-cyan: #20c9c9;
            --accent-purple: #9d4edd;
            --accent-pink: #ff70a6;
            --gradient-blue: linear-gradient(135deg, #4d6cf5, #9d4edd);
            --gradient-cyan: linear-gradient(135deg, #20c9c9, #4d6cf5);
            --gradient-purple: linear-gradient(135deg, #9d4edd, #ff70a6);
            --shadow: 0 20px 40px -15px rgba(0,0,0,0.6);
            --shadow-glow: 0 10px 30px rgba(77,108,245,0.2);
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: radial-gradient(circle at 20% 30%, #0a0c14, #030405);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 30px;
        }}
        
        .dashboard {{
            max-width: 1800px;
            margin: 0 auto;
        }}
        
        /* Header */
        .dashboard-header {{
            background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(10, 12, 20, 0.98));
            border: 1px solid var(--border);
            border-radius: 30px;
            padding: 40px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }}
        
        .dashboard-header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 30%, rgba(77,108,245,0.1), transparent 70%);
            pointer-events: none;
        }}
        
        .title {{
            font-size: 48px;
            font-weight: 800;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #ffffff, #b8c1ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }}
        
        .stats-bar {{
            display: flex;
            gap: 40px;
            flex-wrap: wrap;
        }}
        
        .stat-pill {{
            background: rgba(255,255,255,0.05);
            padding: 12px 25px;
            border-radius: 50px;
            border: 1px solid var(--border);
            font-size: 16px;
        }}
        
        .stat-pill strong {{
            color: var(--accent-blue);
            font-size: 20px;
            margin-right: 8px;
        }}
        
        /* Filter Section */
        .filter-section {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .filter-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }}
        
        .filter-group {{
            background: rgba(255,255,255,0.03);
            border-radius: 15px;
            padding: 20px;
        }}
        
        .filter-title {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-secondary);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-options {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}
        
        .filter-chip {{
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            border-radius: 50px;
            padding: 8px 18px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            color: var(--text-secondary);
        }}
        
        .filter-chip:hover {{
            background: var(--accent-blue);
            color: white;
            border-color: var(--accent-blue);
        }}
        
        .filter-chip.active {{
            background: var(--gradient-blue);
            color: white;
            border: none;
        }}
        
        .slider-container {{
            margin-top: 15px;
        }}
        
        .slider-label {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            color: var(--text-secondary);
            font-size: 13px;
        }}
        
        input[type=range] {{
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            outline: none;
            -webkit-appearance: none;
        }}
        
        input[type=range]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 18px;
            height: 18px;
            background: var(--accent-blue);
            border-radius: 50%;
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 0 20px var(--accent-blue);
        }}
        
        .search-box {{
            width: 100%;
            padding: 15px 20px;
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--border);
            border-radius: 15px;
            color: white;
            font-size: 16px;
            transition: all 0.3s ease;
        }}
        
        .search-box:focus {{
            border-color: var(--accent-blue);
            box-shadow: 0 0 30px rgba(77,108,245,0.2);
            outline: none;
        }}
        
        /* Metrics Cards */
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card:hover {{
            background: var(--bg-card-hover);
            border-color: var(--accent-blue);
            transform: translateY(-5px);
            box-shadow: var(--shadow-glow);
        }}
        
        .metric-icon {{
            font-size: 32px;
            margin-bottom: 15px;
        }}
        
        .metric-label {{
            font-size: 13px;
            text-transform: uppercase;
            letter-spacing: 2px;
            color: var(--text-secondary);
            margin-bottom: 10px;
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            background: var(--gradient-blue);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
            margin-bottom: 8px;
        }}
        
        .metric-trend {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        
        /* Visualization Containers */
        .viz-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 30px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }}
        
        .viz-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .viz-title span {{
            font-size: 28px;
        }}
        
        /* Table */
        .table-container {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 25px;
            margin-top: 30px;
            overflow-x: auto;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        
        .data-table th {{
            background: rgba(77,108,245,0.2);
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: white;
            border-radius: 10px 10px 0 0;
        }}
        
        .data-table td {{
            padding: 12px 15px;
            border-bottom: 1px solid var(--border);
            color: var(--text-secondary);
        }}
        
        .data-table tr:hover td {{
            background: rgba(77,108,245,0.1);
            color: white;
        }}
        
        .project-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .badge-APPL {{ background: linear-gradient(145deg, #4d6cf5, #3849b0); }}
        .badge-OLMM {{ background: linear-gradient(145deg, #20c9c9, #1a8c8c); }}
        
        .clear-filters {{
            background: transparent;
            border: 1px solid var(--border);
            color: var(--text-secondary);
            padding: 10px 25px;
            border-radius: 50px;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            margin-left: 15px;
        }}
        
        .clear-filters:hover {{
            background: rgba(255,255,255,0.1);
            color: white;
        }}
        
        .footer {{
            margin-top: 60px;
            text-align: center;
            color: var(--text-muted);
            font-size: 13px;
            padding: 30px;
            border-top: 1px solid var(--border);
        }}
        
        .active-filters {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 15px;
        }}
        
        .filter-tag {{
            background: var(--accent-blue);
            color: white;
            padding: 5px 15px;
            border-radius: 50px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .filter-tag button {{
            background: none;
            border: none;
            color: white;
            cursor: pointer;
            font-size: 16px;
        }}
        
        @media (max-width: 768px) {{
            body {{ padding: 15px; }}
            .title {{ font-size: 32px; }}
            .dashboard-header {{ padding: 25px; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <!-- Header -->
        <div class="dashboard-header">
            <div class="title">🧪 BEHub • Reliability Dashboard</div>
            <div style="font-size: 18px; color: var(--text-secondary); margin-bottom: 25px;">
                Interactive Test-Retest Analysis • {len(self.all_data)} Subjects • {len(self.all_data['project'].unique())} Projects
            </div>
            <div class="stats-bar">
                <div class="stat-pill">
                    <strong>{self.all_data['accuracy_pearson_r'].mean():.3f}</strong> Avg Accuracy Reliability
                </div>
                <div class="stat-pill">
                    <strong>{self.all_data['rt_pearson_r'].mean():.3f}</strong> Avg RT Reliability
                </div>
                <div class="stat-pill">
                    <strong>{self.all_data['n_common_stimuli'].mean():.0f}</strong> Avg Common Stimuli
                </div>
            </div>
        </div>
        
        <!-- Filter Section -->
        <div class="filter-section">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span style="font-size: 28px;">🔍</span>
                    <h2 style="font-size: 24px; font-weight: 600;">Dynamic Filtering</h2>
                </div>
                <button class="clear-filters" onclick="clearAllFilters()">Clear All Filters</button>
            </div>
            
            <div class="filter-grid">
                <!-- Project Filter -->
                <div class="filter-group">
                    <div class="filter-title">
                        <span>🎯</span> Project
                    </div>
                    <div class="filter-options" id="project-filters">
                        {''.join([f'<div class="filter-chip" onclick="toggleProject(\'{p}\')" id="chip-{p}">{p}</div>' for p in projects_list])}
                    </div>
                </div>
                
                <!-- Metric Range Filter -->
                <div class="filter-group">
                    <div class="filter-title">
                        <span>📊</span> Metric Range
                    </div>
                    <select id="metric-select" class="search-box" style="margin-bottom: 15px;" onchange="updateSliderRange()">
                        {''.join([f'<option value="{m}">{metrics_labels[m]}</option>' for m in all_metrics if m in self.all_data.columns])}
                    </select>
                    <div class="slider-container">
                        <div class="slider-label">
                            <span>Min: <span id="min-val">0.0</span></span>
                            <span>Max: <span id="max-val">1.0</span></span>
                        </div>
                        <input type="range" id="metric-slider" min="0" max="1" step="0.01" value="0" onchange="updateMetricFilter()">
                    </div>
                </div>
                
                <!-- Search -->
                <div class="filter-group">
                    <div class="filter-title">
                        <span>🔎</span> Subject Search
                    </div>
                    <input type="text" id="subject-search" class="search-box" 
                           placeholder="Search by subject ID..." onkeyup="filterTable()">
                </div>
            </div>
            
            <!-- Active Filters -->
            <div id="active-filters" class="active-filters">
                <!-- Will be populated by JavaScript -->
            </div>
        </div>
        
        <!-- Key Metrics Cards -->
        <div class="metrics-grid" id="metrics-cards">
            <!-- Will be populated by JavaScript -->
        </div>
        
        <!-- Visualizations -->
        <div class="viz-container">
            <div class="viz-title">
                <span>📊</span> Project Comparison: Key Reliability Metrics
            </div>
            {self.fig_to_html(comparison_bar)}
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px;">
            <div class="viz-container">
                <div class="viz-title">
                    <span>🫧</span> Project Performance Bubble Chart
                </div>
                {self.fig_to_html(bubble_chart)}
            </div>
            <div class="viz-container">
                <div class="viz-title">
                    <span>🎻</span> Distribution Comparison
                </div>
                {self.fig_to_html(violin_plots)}
            </div>
        </div>
        
        <div class="viz-container">
            <div class="viz-title">
                <span>🔬</span> Subject-Level Multi-Dimensional Analysis
            </div>
            {self.fig_to_html(scatter_matrix)}
        </div>
        
        <div class="viz-container">
            <div class="viz-title">
                <span>🔄</span> Parallel Coordinates: Multi-Metric Profile
            </div>
            {self.fig_to_html(parallel_coords)}
        </div>
        
        <!-- Data Table -->
        <div class="table-container">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div class="viz-title" style="margin-bottom: 0;">
                    <span>📋</span> Filtered Subject Data
                </div>
                <div style="color: var(--text-secondary);">
                    <span id="record-count">{len(self.all_data)}</span> subjects displayed
                </div>
            </div>
            <div style="overflow-x: auto; max-height: 600px; overflow-y: auto;">
                <table class="data-table" id="subject-table">
                    <thead>
                        <tr>
                            <th>Subject</th>
                            <th>Project</th>
                            <th>Acc r</th>
                            <th>Cohen's κ</th>
                            <th>% Agree</th>
                            <th>RT r</th>
                            <th>RT ICC</th>
                            <th>Learning Stage</th>
                            <th>Bias Stability</th>
                            <th>Common Stimuli</th>
                            <th>Acc S3</th>
                            <th>Acc S4</th>
                            <th>RT S3</th>
                            <th>RT S4</th>
                        </tr>
                    </thead>
                    <tbody id="table-body">
                        <!-- Will be populated by JavaScript -->
                    </tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>⚡ Behavioral Experiments Hub • Interactive Reliability Dashboard</p>
            <p>Generated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 15px;">Click on filter chips to filter by project • Use slider to filter by metric range • Search for specific subjects</p>
        </div>
    </div>
    
    <script>
        // Subject data from Python
        const subjectData = {subject_data_json};
        const projects = {projects_js};
        
        // Current filter state
        let activeProjects = [];
        let metricFilter = {{ metric: 'accuracy_pearson_r', min: 0, max: 1 }};
        let searchTerm = '';
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {{
            updateSliderRange();
            filterTable();
            updateMetricsCards();
        }});
        
        // Toggle project filter
        function toggleProject(project) {{
            const index = activeProjects.indexOf(project);
            const chip = document.getElementById(`chip-${{project}}`);
            
            if (index === -1) {{
                activeProjects.push(project);
                chip.classList.add('active');
            }} else {{
                activeProjects.splice(index, 1);
                chip.classList.remove('active');
            }}
            
            updateActiveFilters();
            filterTable();
            updateMetricsCards();
        }}
        
        // Update slider range based on selected metric
        function updateSliderRange() {{
            const metric = document.getElementById('metric-select').value;
            const values = subjectData.map(d => d[metric]).filter(v => v !== null && !isNaN(v));
            
            if (values.length > 0) {{
                const min = Math.min(...values);
                const max = Math.max(...values);
                const slider = document.getElementById('metric-slider');
                
                slider.min = min;
                slider.max = max;
                slider.step = (max - min) / 100;
                slider.value = min;
                
                document.getElementById('min-val').textContent = min.toFixed(2);
                document.getElementById('max-val').textContent = max.toFixed(2);
                
                metricFilter.metric = metric;
                metricFilter.min = min;
                metricFilter.max = max;
            }}
        }}
        
        // Update metric filter
        function updateMetricFilter() {{
            const slider = document.getElementById('metric-slider');
            metricFilter.min = parseFloat(slider.value);
            document.getElementById('min-val').textContent = metricFilter.min.toFixed(2);
            filterTable();
            updateMetricsCards();
        }}
        
        // Search filter
        function filterTable() {{
            searchTerm = document.getElementById('subject-search').value.toLowerCase();
            updateActiveFilters();
            renderTable();
            updateMetricsCards();
        }}
        
        // Clear all filters
        function clearAllFilters() {{
            activeProjects = [];
            projects.forEach(p => {{
                const chip = document.getElementById(`chip-${{p}}`);
                if (chip) chip.classList.remove('active');
            }});
            
            document.getElementById('subject-search').value = '';
            searchTerm = '';
            
            updateSliderRange();
            updateActiveFilters();
            filterTable();
            updateMetricsCards();
        }}
        
        // Update active filters display
        function updateActiveFilters() {{
            const container = document.getElementById('active-filters');
            container.innerHTML = '';
            
            if (activeProjects.length > 0) {{
                const tag = document.createElement('span');
                tag.className = 'filter-tag';
                tag.innerHTML = `Projects: ${{activeProjects.join(', ')}} <button onclick="clearAllFilters()">×</button>`;
                container.appendChild(tag);
            }}
            
            if (searchTerm) {{
                const tag = document.createElement('span');
                tag.className = 'filter-tag';
                tag.innerHTML = `Search: "${{searchTerm}}" <button onclick="document.getElementById('subject-search').value=''; filterTable();">×</button>`;
                container.appendChild(tag);
            }}
            
            if (metricFilter.min > 0) {{
                const tag = document.createElement('span');
                tag.className = 'filter-tag';
                tag.innerHTML = `${{metricFilter.metric}}: ≥${{metricFilter.min.toFixed(2)}} <button onclick="updateSliderRange(); filterTable();">×</button>`;
                container.appendChild(tag);
            }}
        }}
        
        // Filter data based on all active filters
        function getFilteredData() {{
            return subjectData.filter(row => {{
                // Project filter
                if (activeProjects.length > 0 && !activeProjects.includes(row.project)) {{
                    return false;
                }}
                
                // Metric range filter
                const metricValue = row[metricFilter.metric];
                if (metricValue === null || metricValue === undefined || isNaN(metricValue)) {{
                    return false;
                }}
                if (metricValue < metricFilter.min || metricValue > metricFilter.max) {{
                    return false;
                }}
                
                // Search filter
                if (searchTerm && !row.subject.toLowerCase().includes(searchTerm)) {{
                    return false;
                }}
                
                return true;
            }});
        }}
        
        // Render table with filtered data
        function renderTable() {{
            const filteredData = getFilteredData();
            const tbody = document.getElementById('table-body');
            const recordCount = document.getElementById('record-count');
            
            recordCount.textContent = filteredData.length;
            
            tbody.innerHTML = filteredData.map(row => `
                <tr>
                    <td><strong>${{row.subject}}</strong></td>
                    <td><span class="project-badge badge-${{row.project}}">${{row.project}}</span></td>
                    <td>${{row.accuracy_pearson_r?.toFixed(3) || 'N/A'}}</td>
                    <td>${{row.accuracy_cohen_kappa?.toFixed(3) || 'N/A'}}</td>
                    <td>${{row.accuracy_percent_agreement ? (row.accuracy_percent_agreement * 100).toFixed(1) + '%' : 'N/A'}}</td>
                    <td>${{row.rt_pearson_r?.toFixed(3) || 'N/A'}}</td>
                    <td>${{row.rt_icc?.toFixed(3) || 'N/A'}}</td>
                    <td>${{row.learning_stage_agreement ? (row.learning_stage_agreement * 100).toFixed(1) + '%' : 'N/A'}}</td>
                    <td>${{row.response_bias_stability ? (row.response_bias_stability * 100).toFixed(1) + '%' : 'N/A'}}</td>
                    <td>${{row.n_common_stimuli || 'N/A'}}</td>
                    <td>${{row.learning_accuracy_ses3 ? (row.learning_accuracy_ses3 * 100).toFixed(1) + '%' : 'N/A'}}</td>
                    <td>${{row.learning_accuracy_ses4 ? (row.learning_accuracy_ses4 * 100).toFixed(1) + '%' : 'N/A'}}</td>
                    <td>${{row.learning_rt_mean_ses3?.toFixed(0) || 'N/A'}}ms</td>
                    <td>${{row.learning_rt_mean_ses4?.toFixed(0) || 'N/A'}}ms</td>
                </tr>
            `).join('');
        }}
        
        // Update metrics cards based on filtered data
        function updateMetricsCards() {{
            const filteredData = getFilteredData();
            const container = document.getElementById('metrics-cards');
            
            if (filteredData.length === 0) {{
                container.innerHTML = `<div class="metric-card" style="grid-column: 1/-1;">
                    <div style="text-align: center; padding: 40px;">
                        <span style="font-size: 48px;">🔍</span>
                        <h3 style="margin-top: 20px;">No subjects match the current filters</h3>
                        <p style="color: var(--text-secondary);">Try adjusting your filter criteria</p>
                    </div>
                </div>`;
                return;
            }}
            
            const accRel = filteredData.reduce((sum, row) => sum + (row.accuracy_pearson_r || 0), 0) / filteredData.length;
            const rtRel = filteredData.reduce((sum, row) => sum + (row.rt_pearson_r || 0), 0) / filteredData.length;
            const learningStage = filteredData.reduce((sum, row) => sum + (row.learning_stage_agreement || 0), 0) / filteredData.length;
            const biasStability = filteredData.reduce((sum, row) => sum + (row.response_bias_stability || 0), 0) / filteredData.length;
            const commonStimuli = filteredData.reduce((sum, row) => sum + (row.n_common_stimuli || 0), 0) / filteredData.length;
            
            container.innerHTML = `
                <div class="metric-card">
                    <div class="metric-icon">🎯</div>
                    <div class="metric-label">Accuracy Reliability</div>
                    <div class="metric-value">${{accRel.toFixed(3)}}</div>
                    <div class="metric-trend">Pearson r • n=${{filteredData.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">⚡</div>
                    <div class="metric-label">RT Reliability</div>
                    <div class="metric-value">${{rtRel.toFixed(3)}}</div>
                    <div class="metric-trend">Pearson r • n=${{filteredData.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">📚</div>
                    <div class="metric-label">Learning Stage</div>
                    <div class="metric-value">${{(learningStage * 100).toFixed(1)}}%</div>
                    <div class="metric-trend">Consistency • n=${{filteredData.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🔄</div>
                    <div class="metric-label">Response Bias</div>
                    <div class="metric-value">${{(biasStability * 100).toFixed(1)}}%</div>
                    <div class="metric-trend">Stability • n=${{filteredData.length}}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">🖼️</div>
                    <div class="metric-label">Common Stimuli</div>
                    <div class="metric-value">${{commonStimuli.toFixed(0)}}</div>
                    <div class="metric-trend">Average per subject</div>
                </div>
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-label">Cohen's Kappa</div>
                    <div class="metric-value">${{(filteredData.reduce((sum, row) => sum + (row.accuracy_cohen_kappa || 0), 0) / filteredData.length).toFixed(3)}}</div>
                    <div class="metric-trend">Chance-corrected agreement</div>
                </div>
            `;
        }}
    </script>
</body>
</html>
'''
        
        # Save dashboard
        output_file = self.output_dir / "interactive_reliability_dashboard.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n{'='*70}")
        print(f"✅ INTERACTIVE DASHBOARD GENERATED")
        print(f"{'='*70}")
        print(f"\n📁 Dashboard saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")
        print(f"\n🌐 Open in browser to explore the interactive dashboard")
        print(f"\n✨ Features:")
        print(f"   • Filter by project (click chips)")
        print(f"   • Filter by metric range (slider)")
        print(f"   • Search by subject ID")
        print(f"   • Real-time table updates")
        print(f"   • Dynamic metrics cards")
        print(f"   • 6 interactive visualizations")
        print(f"   • Parallel coordinates plot")
        print(f"   • Bubble charts and violin plots")
        
        return output_file

def main():
    metrics_dir = Path("/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub/Projects/reliability_metrics")
    generator = InteractiveDashboardGenerator(metrics_dir)
    generator.generate_dashboard()

if __name__ == "__main__":
    main()