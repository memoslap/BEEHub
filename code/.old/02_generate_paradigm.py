#!/usr/bin/env python3
"""
Interactive Dashboard Generator
Creates a filterable overview dashboard from all project JSON files
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict


class InteractiveDashboard:
    """Generates interactive HTML dashboard with advanced filtering"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.all_projects = []
    
    def load_all_projects(self) -> List[Dict]:
        """Load all project data. Three strategies per project folder, in order:

          1. {project}_data.json  — pre-computed by multi_project_overview_GREEN.py
          2. Any *_data.json in the folder  — alternative naming conventions
          3. Live analysis via ProjectOverviewGenerator  — when only TSV/bids_data exist

        learning_stage_data is always stripped: the dashboard never shows stage charts.
        """
        projects_path = self.base_path / "Projects"
        if not projects_path.exists():
            print(f"Projects path not found: {projects_path}")
            return []

        # -- Try to import the overview generator for live fallback --
        _generator = None
        try:
            import importlib.util
            candidates = [
                Path(__file__).parent / "multi_project_overview_GREEN.py",
                self.base_path / "multi_project_overview_GREEN.py",
                self.base_path.parent / "multi_project_overview_GREEN.py",
            ]
            for candidate in candidates:
                if candidate.exists():
                    spec = importlib.util.spec_from_file_location("_overview", candidate)
                    mod  = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    _generator = mod.ProjectOverviewGenerator(str(self.base_path))
                    print(f"  Live-analysis fallback available ({candidate.name})")
                    break
        except Exception as e:
            print(f"  Live-analysis not available: {e}")

        for project_dir in sorted(projects_path.iterdir()):
            if not project_dir.is_dir():
                continue
            project_name = project_dir.name
            data = None

            # 1. Canonical JSON
            canonical = project_dir / f"{project_name}_data.json"
            if canonical.exists():
                try:
                    with open(canonical) as f:
                        data = json.load(f)
                    print(f"  Loaded (JSON):       {project_name}")
                except Exception as e:
                    print(f"  Error reading {canonical.name}: {e}")

            # 2. Any *_data.json (different naming / subfolder conventions)
            if data is None:
                for jf in sorted(project_dir.glob("*_data.json")):
                    try:
                        with open(jf) as f:
                            data = json.load(f)
                        print(f"  Loaded (JSON alt):   {project_name}  <-  {jf.name}")
                        break
                    except Exception as e:
                        print(f"  Error reading {jf.name}: {e}")

            # 3. Live analysis when TSV / bids_data exist but no JSON yet
            if data is None and _generator is not None:
                has_bids = (project_dir / "bids_data").exists()
                has_tsv  = any(project_dir.rglob("*_RT_beh.tsv"))
                if has_bids or has_tsv:
                    try:
                        data = _generator.analyze_project(project_name)
                        if data:
                            print(f"  Loaded (live):       {project_name}")
                        else:
                            data = None
                    except Exception as e:
                        print(f"  Live analysis failed for {project_name}: {e}")

            if data is None:
                print(f"  Skipped (no data):   {project_name}")
                continue

            # Strip learning_stage_data — never displayed in the dashboard
            data.pop("learning_stage_data", None)

            # Safe defaults for any missing keys
            data.setdefault("project_name", project_name)
            data.setdefault("project_info", {
                "full_name": project_name, "description": "",
                "modality": "unknown", "cognitive_domain": "unknown",
                "task_type": "unknown", "difficulty": "unknown",
            })
            data.setdefault("demographics", {
                "n_participants": 0, "age_mean": None,
                "age_std": None, "sex_distribution": {},
            })
            data.setdefault("reliability_metrics", {})

            data["has_short_version"] = self.check_short_version(project_dir)
            self.all_projects.append(data)

        print(f"\n  Total projects loaded: {len(self.all_projects)}")
        return self.all_projects
    
    def check_short_version(self, project_dir: Path) -> bool:
        """Check if a short version paradigm file exists"""
        project_name = project_dir.name
        # Check for pattern: BEHub/Projects/APPL/paradigm/psychopy/APPL_paradigm_short/APPL_short_version.py
        short_version_patterns = [
            project_dir / "paradigm" / "psychopy" / f"{project_name}_paradigm_short" / f"{project_name}_short_version.py",
            project_dir / "paradigm" / "psychopy" / f"{project_name}_short_version.py",
            project_dir / "paradigm" / f"{project_name}_short_version.py",
        ]
        
        for pattern in short_version_patterns:
            if pattern.exists():
                print(f"  Found short version: {pattern}")
                return True
        return False
    
    def generate_test_paradigm_launcher(self, project_data: Dict) -> str:
        """Generate HTML paradigm page with description and links"""
        project_name = project_data.get('project_name', 'Unknown')
        project_info = project_data.get('project_info', {})
        
        # Get project description
        description = project_info.get('description', 'No description available.')
        modality = project_info.get('modality', 'N/A')
        cognitive_domain = project_info.get('cognitive_domain', 'N/A')
        task_type = project_info.get('task_type', 'N/A')
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{project_name} - Paradigm</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #e8e4e0 0%, #f0ece8 50%, #ffffff 100%);
            background-attachment: fixed;
            color: #2a1a0a;
            padding: 40px 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: linear-gradient(135deg,
                rgba(210, 195, 175, 0.90) 0%,
                rgba(235, 225, 210, 0.95) 25%,
                rgba(252, 248, 242, 0.98) 50%,
                rgba(235, 225, 210, 0.95) 75%,
                rgba(210, 195, 175, 0.90) 100%
            );
            border-radius: 20px;
            padding: 50px;
            box-shadow:
                0 10px 40px rgba(160, 120, 60, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.85),
                inset 0 -1px 0 rgba(160, 110, 50, 0.15);
            border: 1px solid rgba(190, 150, 80, 0.30);
            position: relative;
            overflow: hidden;
        }}

        .container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg,
                #6b3a10 0%,
                #9e5c1e 12%,
                #c07838 25%,
                #d4a020 40%,
                #e8c048 50%,
                #d4a020 60%,
                #b8b0be 75%,
                #c4a0b4 88%,
                #6b3a10 100%
            );
            opacity: 0.85;
        }}

        h1 {{
            background: linear-gradient(135deg,
                #6b3a10 0%,
                #9e5c1e 15%,
                #c07838 30%,
                #d4a020 50%,
                #b8b0be 70%,
                #c4a0b4 85%,
                #9e5c1e 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-size: 3em;
            font-weight: 300;
            letter-spacing: -1px;
            padding-bottom: 15px;
            border-bottom: 4px solid;
            border-image: linear-gradient(90deg,
                transparent 0%,
                rgba(160, 120, 60, 0.3) 10%,
                rgba(212, 160, 32, 0.6) 50%,
                rgba(160, 120, 60, 0.3) 90%,
                transparent 100%
            ) 1;
        }}

        .subtitle {{
            color: #7a5030;
            margin-bottom: 40px;
            font-size: 1.3em;
            font-weight: 300;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .info-card {{
            background: linear-gradient(135deg,
                rgba(220, 200, 170, 0.85) 0%,
                rgba(240, 228, 208, 0.90) 50%,
                rgba(220, 200, 170, 0.85) 100%
            );
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #c07838;
            box-shadow:
                0 4px 16px rgba(160, 110, 50, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.6);
        }}

        .info-card h3 {{
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }}

        .info-card p {{
            color: #3a2010;
            font-size: 1.2em;
            font-weight: 600;
        }}

        .description-box {{
            background: linear-gradient(135deg,
                rgba(245, 236, 220, 0.90) 0%,
                rgba(255, 250, 240, 0.95) 50%,
                rgba(245, 236, 220, 0.90) 100%
            );
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 40px;
            line-height: 1.8;
            font-size: 1.1em;
            color: #3a2010;
            border: 1px solid rgba(190, 150, 80, 0.25);
            box-shadow: 0 4px 16px rgba(160, 110, 50, 0.12);
            position: relative;
            overflow: hidden;
        }}

        .description-box::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #9e5c1e 0%, #d4a020 30%, #e8c048 50%, #d4a020 70%, #c4a0b4 100%
            );
            opacity: 0.7;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 50%, #b8b0be 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
            border-left: 6px solid #d4a020;
            padding-left: 15px;
        }}

        .links-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .link-card {{
            background: linear-gradient(135deg,
                rgba(225, 210, 185, 0.85) 0%,
                rgba(245, 235, 215, 0.92) 50%,
                rgba(225, 210, 185, 0.85) 100%
            );
            border: 1px solid rgba(190, 150, 80, 0.30);
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s ease;
            cursor: pointer;
            box-shadow:
                0 4px 16px rgba(160, 110, 50, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.65);
            position: relative;
            overflow: hidden;
        }}

        .link-card::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #9e5c1e 0%, #d4a020 50%, #c4a0b4 100%
            );
            opacity: 0.6;
            transition: opacity 0.3s;
        }}

        .link-card:hover {{
            border-color: rgba(212, 160, 32, 0.55);
            box-shadow:
                0 8px 28px rgba(160, 110, 50, 0.28),
                inset 0 1px 0 rgba(255, 255, 255, 0.75);
            transform: translateY(-3px);
        }}

        .link-card:hover::before {{
            opacity: 1;
        }}

        .link-card h3 {{
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}

        .link-card p {{
            color: #6a4820;
            margin-bottom: 15px;
            line-height: 1.6;
        }}

        .link-card code {{
            display: block;
            background: rgba(160, 110, 50, 0.10);
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #9e5c1e;
            word-break: break-all;
            margin-top: 10px;
            border: 1px solid rgba(190, 150, 80, 0.25);
        }}

        .btn-container {{
            display: flex;
            gap: 15px;
            margin-top: 40px;
            flex-wrap: wrap;
        }}

        .btn {{
            padding: 18px 35px;
            border: none;
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}

        .btn-demo {{
            background: linear-gradient(135deg,
                #e8c048 0%, #d4a020 35%, #c07838 100%
            );
            color: #2a1a0a;
            flex: 1;
            min-width: 250px;
            font-size: 1.2em;
            box-shadow:
                0 4px 20px rgba(212, 160, 32, 0.40),
                inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }}

        .btn-demo:hover {{
            background: linear-gradient(135deg,
                #c07838 0%, #d4a020 50%, #e8c048 100%
            );
            transform: translateY(-2px);
            box-shadow:
                0 8px 28px rgba(212, 160, 32, 0.55),
                inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }}

        .btn-secondary {{
            background: linear-gradient(135deg,
                #b8b0be 0%, #c8c0c8 40%, #c4a0b4 100%
            );
            color: #2a1a0a;
            flex: 0 0 auto;
            min-width: 200px;
            box-shadow:
                0 4px 16px rgba(180, 150, 180, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.40);
        }}

        .btn-secondary:hover {{
            background: linear-gradient(135deg,
                #c4a0b4 0%, #c8c0c8 50%, #b8b0be 100%
            );
            transform: translateY(-2px);
            box-shadow:
                0 8px 24px rgba(180, 150, 180, 0.50),
                inset 0 1px 0 rgba(255, 255, 255, 0.40);
        }}

        .github-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #8a4a10;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
            padding: 10px 20px;
            border: 2px solid rgba(190, 150, 80, 0.45);
            border-radius: 8px;
            transition: all 0.3s;
            background: rgba(255, 248, 235, 0.60);
        }}

        .github-link:hover {{
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            color: #fff8ee;
            border-color: #d4a020;
            box-shadow: 0 4px 14px rgba(180, 130, 40, 0.35);
        }}

        .warning-box {{
            background: linear-gradient(135deg, #fdf5e0 0%, #f5e8c0 100%);
            border-left: 4px solid #d4a020;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            color: #7a4a10;
            font-size: 1.05em;
            box-shadow: 0 2px 10px rgba(180, 130, 40, 0.12);
        }}

        .highlight-box {{
            background: linear-gradient(135deg,
                rgba(215, 195, 210, 0.80) 0%,
                rgba(235, 220, 230, 0.88) 50%,
                rgba(215, 195, 210, 0.80) 100%
            );
            border: 1px solid rgba(196, 160, 180, 0.45);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow:
                0 6px 24px rgba(180, 140, 170, 0.20),
                inset 0 1px 0 rgba(255, 255, 255, 0.65);
            position: relative;
            overflow: hidden;
        }}

        .highlight-box::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #c4a0b4 0%, #b8b0be 35%, #d4a020 65%, #c07838 100%
            );
            opacity: 0.75;
        }}

        .highlight-box h3 {{
            background: linear-gradient(135deg, #8a4060 0%, #b8b0be 50%, #9e5c1e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 15px;
            font-size: 1.3em;
        }}

        .highlight-box ul {{
            list-style: none;
            padding: 0;
        }}

        .highlight-box li {{
            color: #3a2010;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{project_name}</h1>
        <div class="subtitle">Paradigm Overview & Resources</div>
        
        <div class="info-grid">
            <div class="info-card">
                <h3>Modality</h3>
                <p>{modality}</p>
            </div>
            <div class="info-card">
                <h3>Cognitive Domain</h3>
                <p>{cognitive_domain}</p>
            </div>
            <div class="info-card">
                <h3>Task Type</h3>
                <p>{task_type}</p>
            </div>
        </div>
        
        <div class="section">
            <h2> Description</h2>
            <div class="description-box">
                {description}
            </div>
        </div>
        
        <div class="section">
            <h2> Interactive Demo</h2>
            <div class="warning-box">
                 <strong>Try it now:</strong> Experience a browser-based demo version of this paradigm with reduced trials and timing.
            </div>
            <div class="btn-container">
                <a href="paradigm/psychopy/{project_name}_paradigm_short/{project_name}_demo.html" class="btn btn-demo" target="_blank">
                     Launch Interactive Demo
                </a>
            </div>
        </div>
        
        <div class="section">
            <h2> Paradigm Files</h2>
            <div class="links-container">
                <div class="link-card">
                    <h3> PsychoPy Version</h3>
                    <p>Full implementation with all features for running the experiment in PsychoPy.</p>
                    <code>BEHub/Projects/{project_name}/paradigm/psychopy/</code>
                    <a href="https://github.com/memoslap/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy" 
                       class="github-link" 
                       target="_blank" 
                       style="display: inline-flex; margin-top: 15px;">
                        <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        View on GitHub
                    </a>
                </div>
                
                <div class="link-card">
                    <h3> Short Test Version</h3>
                    <p>Reduced version for quick testing and debugging with fewer trials.</p>
                    <code>BEHub/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short/</code>
                    <a href="https://github.com/memoslap/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short" 
                       class="github-link" 
                       target="_blank" 
                       style="display: inline-flex; margin-top: 15px;">
                        <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        View on GitHub
                    </a>
                </div>
                
                <div class="link-card">
                    <h3> Presentation Files</h3>
                    <p>Original Presentation software files with stimuli and materials.</p>
                    <code>BEHub/Projects/{project_name}/paradigm/presentation/</code>
                    <a href="https://github.com/memoslap/BEHub/tree/main/Projects/{project_name}/paradigm/presentation" 
                       class="github-link" 
                       target="_blank" 
                       style="display: inline-flex; margin-top: 15px;">
                        <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        View on GitHub
                    </a>
                </div>
                
                <div class="link-card">
                    <h3> Stimuli</h3>
                    <p>All stimulus materials including images and experimental materials.</p>
                    <code>BEHub/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short/Stimuli/</code>
                    <a href="https://github.com/memoslap/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short/Stimuli" 
                       class="github-link" 
                       target="_blank" 
                       style="display: inline-flex; margin-top: 15px;">
                        <svg width="20" height="20" viewBox="0 0 16 16" fill="currentColor">
                            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
                        </svg>
                        View on GitHub
                    </a>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2> Running the Paradigm</h2>
            <div class="highlight-box">
                <h3>PsychoPy Instructions</h3>
                <ul>
                    <li>Install PsychoPy (recommended version 2021.2 or later)</li>
                    <li>Clone or download the repository from GitHub</li>
                    <li>Navigate to the PsychoPy directory</li>
                    <li>Run: <code>python {project_name}_short_version.py</code> (for test version)</li>
                    <li>Follow on-screen instructions</li>
                </ul>
            </div>
        </div>
        
        <div class="btn-container">
            <a href="../../dashboard.html" class="btn btn-secondary">← Back to Dashboard</a>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def save_test_paradigm_launchers(self):
        """Save paradigm launcher HTML pages for projects that have short versions"""
        count = 0
        for project in self.all_projects:
            if project.get('has_short_version', False):
                project_name = project.get('project_name')
                project_dir = self.base_path / "Projects" / project_name
                
                launcher_html = self.generate_test_paradigm_launcher(project)
                launcher_path = project_dir / f"{project_name}_paradigm.html"
                
                with open(launcher_path, 'w', encoding='utf-8') as f:
                    f.write(launcher_html)
                
                print(f"  Created paradigm page: {launcher_path}")
                count += 1
        
        return count
    


def main():
    import sys
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub"
    d = InteractiveDashboard(base_path)
    d.load_all_projects()
    count = d.save_test_paradigm_launchers()
    print("Paradigm pages created:", count)


if __name__ == "__main__":
    main()
