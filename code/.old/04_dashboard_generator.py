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
    
    def extract_unique_values(self) -> Dict:
        """Extract unique values for filter options"""
        modalities = set()
        domains = set()
        task_types = set()
        
        for project in self.all_projects:
            info = project.get('project_info', {})
            modalities.add(info.get('modality', 'unknown'))
            domains.add(info.get('cognitive_domain', 'unknown'))
            task_types.add(info.get('task_type', 'unknown'))
        
        return {
            'modalities': sorted(modalities),
            'domains': sorted(domains),
            'task_types': sorted(task_types)
        }
    
    def get_data_ranges(self) -> Dict:
        """Get min/max ranges for slider filters"""
        ages = []
        n_subjects = []
        rt_iccs = []
        acc_iccs = []
        
        for project in self.all_projects:
            demo = project.get('demographics', {})
            if demo.get('age_mean'):
                ages.append(demo['age_mean'])
            if demo.get('n_participants'):
                n_subjects.append(demo['n_participants'])
            
            for metrics in project.get('reliability_metrics', {}).values():
                if metrics.get('rt_icc_mean') is not None:
                    rt_iccs.append(metrics['rt_icc_mean'])
                if metrics.get('acc_icc_mean') is not None:
                    acc_iccs.append(metrics['acc_icc_mean'])
        
        return {
            'age_min': int(min(ages)) if ages else 18,
            'age_max': int(max(ages)) + 1 if ages else 65,
            'subjects_min': int(min(n_subjects)) if n_subjects else 0,
            'subjects_max': int(max(n_subjects)) + 5 if n_subjects else 100,
            'rt_icc_min': round(min(rt_iccs), 2) if rt_iccs else -1,
            'rt_icc_max': round(max(rt_iccs), 2) if rt_iccs else 1,
            'acc_icc_min': round(min(acc_iccs), 2) if acc_iccs else -1,
            'acc_icc_max': round(max(acc_iccs), 2) if acc_iccs else 1
        }
    
    def generate_dashboard_html(self) -> str:
        """Generate interactive dashboard HTML"""
        
        unique_values = self.extract_unique_values()
        ranges = self.get_data_ranges()
        projects_json = json.dumps(self.all_projects, indent=2)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BEHub</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #e8e8e8 0%, #f5f5f5 50%, #ffffff 100%);
            color: #333;
            padding: 20px;
            background-attachment: fixed;
        }}
        
        .header {{
            background: linear-gradient(135deg, 
                rgba(144, 195, 168, 0.9) 0%,    /* Sage green */
                rgba(168, 218, 195, 0.95) 25%,  /* Mint green */
                rgba(192, 232, 216, 0.98) 50%,  /* Light mint */
                rgba(168, 218, 195, 0.95) 75%,
                rgba(144, 195, 168, 0.9) 100%
            );
            padding: 50px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 
                0 10px 40px rgba(64, 158, 128, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.8),
                inset 0 -1px 0 rgba(64, 158, 128, 0.15);
            text-align: center;
            border: 1px solid rgba(64, 158, 128, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                #2d8659 0%,      /* Forest green */
                #409e80 15%,     /* Emerald */
                #40e0d0 30%,     /* Turquoise */
                #48d1cc 50%,     /* Medium turquoise */
                #40e0d0 70%,
                #409e80 85%,
                #2d8659 100%
            );
            opacity: 0.8;
        }}
        
        h1 {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,      /* Deep forest */
                #2d8659 15%,     /* Forest green */
                #409e80 30%,     /* Emerald */
                #40e0d0 50%,     /* Turquoise */
                #409e80 70%,
                #2d8659 85%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3.5em;
            margin-bottom: 10px;
            font-weight: 300;
            letter-spacing: -1px;
        }}
        
        .subtitle {{
            color: #1e5f44;
            font-size: 1.2em;
            font-weight: 300;
        }}
        
        .filters-container {{
            background: linear-gradient(135deg, 
                rgba(235, 248, 243, 0.95) 0%, 
                rgba(245, 252, 249, 0.98) 50%, 
                rgba(235, 248, 243, 0.95) 100%
            );
            padding: 35px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 
                0 8px 32px rgba(64, 158, 128, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(64, 158, 128, 0.1);
            border: 1px solid rgba(64, 158, 128, 0.25);
            position: relative;
            overflow: hidden;
        }}
        
        .filters-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                #2d8659 0%,
                #409e80 20%,
                #40e0d0 40%,
                #48d1cc 60%,
                #40e0d0 80%,
                #2d8659 100%
            );
            opacity: 0.7;
        }}
        
        .filters-title {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #2d8659 25%,
                #409e80 50%,
                #2d8659 75%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.6em;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, 
                transparent 0%,
                rgba(64, 158, 128, 0.3) 10%,
                rgba(64, 224, 208, 0.5) 50%,
                rgba(64, 158, 128, 0.3) 90%,
                transparent 100%
            ) 1;
            font-weight: 400;
            letter-spacing: -0.5px;
        }}
        
        .filters-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
        }}
        
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .filter-label {{
            background: linear-gradient(90deg, #1e5f44 0%, #2d8659 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 0.9em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .filter-select {{
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.95) 0%, 
                rgba(250, 254, 252, 0.98) 100%
            );
            border: 1px solid rgba(64, 158, 128, 0.3);
            color: #1e5f44;
            padding: 14px;
            border-radius: 10px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 
                0 2px 8px rgba(64, 158, 128, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(64, 158, 128, 0.05);
        }}
        
        .filter-select:hover {{
            border-color: rgba(64, 224, 208, 0.5);
            box-shadow: 
                0 4px 12px rgba(64, 224, 208, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(64, 158, 128, 0.1);
        }}
        
        .filter-select:focus {{
            outline: none;
            border-color: #40e0d0;
            box-shadow: 
                0 0 0 3px rgba(64, 224, 208, 0.2),
                0 4px 12px rgba(64, 224, 208, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }}
        
        .slider-container {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        
        .slider-value {{
            background: linear-gradient(135deg, 
                #2d8659 0%,
                #40e0d0 50%,
                #2d8659 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 1.1em;
            text-align: center;
        }}
        
        input[type="range"] {{
            width: 100%;
            height: 5px;
            border-radius: 3px;
            background: linear-gradient(180deg, 
                rgba(200, 230, 220, 0.8) 0%, 
                rgba(220, 240, 235, 0.9) 100%
            );
            outline: none;
            -webkit-appearance: none;
            box-shadow: 
                inset 0 1px 3px rgba(64, 158, 128, 0.2),
                0 1px 0 rgba(255, 255, 255, 0.7);
            border: 1px solid rgba(64, 158, 128, 0.15);
        }}
        
        input[type="range"]::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, 
                #40e0d0 0%,
                #7fffd4 50%,
                #40e0d0 100%
            );
            cursor: pointer;
            border: 2px solid #fff;
            box-shadow: 
                0 2px 8px rgba(64, 224, 208, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.5),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        }}
        
        input[type="range"]::-moz-range-thumb {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, 
                #40e0d0 0%,
                #7fffd4 50%,
                #40e0d0 100%
            );
            cursor: pointer;
            border: 2px solid #fff;
            box-shadow: 
                0 2px 8px rgba(64, 224, 208, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.5),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        }}
        
        .action-buttons {{
            display: flex;
            gap: 15px;
            margin-top: 30px;
            justify-content: center;
        }}
        
        .btn {{
            padding: 14px 36px;
            border: none;
            border-radius: 12px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            letter-spacing: 0.3px;
            position: relative;
            overflow: hidden;
        }}
        
        .btn::before {{
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }}
        
        .btn:hover::before {{
            width: 300px;
            height: 300px;
        }}
        
        .btn-apply {{
            background: linear-gradient(135deg, 
                #2d8659 0%,
                #40e0d0 50%,
                #2d8659 100%
            );
            color: #fff;
            box-shadow: 
                0 4px 16px rgba(64, 224, 208, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }}
        
        .btn-apply:hover {{
            transform: translateY(-2px);
            box-shadow: 
                0 6px 20px rgba(64, 224, 208, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        }}
        
        .btn-apply:active {{
            transform: translateY(0);
        }}
        
        .btn-reset {{
            background: linear-gradient(135deg, 
                #a8dac3 0%,
                #c5e8d8 50%,
                #a8dac3 100%
            );
            color: #1e5f44;
            box-shadow: 
                0 2px 8px rgba(168, 218, 195, 0.3),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(0, 0, 0, 0.05);
        }}
        
        .btn-reset:hover {{
            transform: translateY(-2px);
            box-shadow: 
                0 4px 12px rgba(168, 218, 195, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(0, 0, 0, 0.05);
        }}
        
        .results-container {{
            background: linear-gradient(135deg, 
                rgba(250, 250, 250, 0.95) 0%, 
                rgba(255, 255, 255, 0.98) 50%, 
                rgba(248, 248, 248, 0.95) 100%
            );
            padding: 35px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 
                0 8px 32px rgba(64, 158, 128, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(64, 158, 128, 0.1);
            border: 1px solid rgba(64, 224, 208, 0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .results-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                #2d8659 0%,
                #40e0d0 20%,
                #409e80 40%,
                #48d1cc 60%,
                #409e80 80%,
                #2d8659 100%
            );
            opacity: 0.6;
        }}
        
        .results-header {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #409e80 25%,
                #2d8659 50%,
                #409e80 75%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.6em;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, 
                transparent 0%,
                rgba(64, 158, 128, 0.3) 10%,
                rgba(64, 224, 208, 0.5) 50%,
                rgba(64, 158, 128, 0.3) 90%,
                transparent 100%
            ) 1;
            font-weight: 400;
        }}
        
        .results-count {{
            background: linear-gradient(135deg, 
                #2d8659 0%,
                #40e0d0 50%,
                #2d8659 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 700;
            font-size: 1.4em;
        }}
        
        .projects-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }}
        
        .project-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f8f8f8 100%);
            padding: 28px;
            border-radius: 14px;
            box-shadow: 
                0 4px 20px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .project-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                #2d8659 0%,    /* Bronze */
                #40e0d0 25%,   /* Gold */
                #409e80 50%,   /* Copper */
                #48d1cc 75%,   /* Silver */
                #2d8659 100%   /* Bronze */
            );
            opacity: 0.7;
        }}
        
        .project-card:hover {{
            transform: translateY(-5px);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }}
        
        .project-card:hover::before {{
            opacity: 1;
            height: 5px;
        }}
        
        .project-name {{
            background: linear-gradient(135deg, 
                #409e80 0%,    /* Copper */
                #2d8659 25%,   /* Bronze */
                #40e0d0 50%,   /* Gold */
                #2d8659 75%,   /* Bronze */
                #409e80 100%   /* Copper */
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.6em;
            font-weight: 600;
            margin-bottom: 8px;
            letter-spacing: -0.3px;
        }}
        
        .project-full-name {{
            color: #666;
            font-size: 0.95em;
            margin-bottom: 15px;
            font-weight: 300;
        }}
        
        .project-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }}
        
        .tag {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            border: 1px solid;
            font-weight: 500;
            box-shadow: 
                0 1px 3px rgba(0, 0, 0, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.7);
        }}
        
        .tag.modality {{ 
            border-color: #40e0d0;
            color: #2f6f50;
            background: linear-gradient(135deg, #fff9e6 0%, #ffedb3 100%);
        }}
        .tag.domain {{ 
            border-color: #2d8659;
            color: #1e5f44;
            background: linear-gradient(135deg, #ffe9d9 0%, #ffd4b3 100%);
        }}
        .tag.difficulty {{ 
            border-color: #409e80;
            color: #1a5238;
            background: linear-gradient(135deg, #ffeee6 0%, #ffdcc9 100%);
        }}
        
        .project-stats {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin-top: 18px;
        }}
        
        .stat-item {{
            background: linear-gradient(135deg, 
                rgba(64, 224, 208, 0.08) 0%,   /* Gold tint */
                rgba(64, 158, 128, 0.08) 50%,  /* Bronze tint */
                rgba(64, 158, 128, 0.08) 100%  /* Copper tint */
            );
            padding: 14px;
            border-radius: 10px;
            text-align: center;
            border: 1px solid rgba(64, 158, 128, 0.15);
            box-shadow: 
                0 2px 6px rgba(64, 158, 128, 0.1),
                inset 0 1px 0 rgba(255, 255, 255, 0.7);
            position: relative;
            overflow: hidden;
        }}
        
        .stat-item::after {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(64, 224, 208, 0.2) 50%,
                transparent 100%
            );
            transition: left 0.5s ease;
        }}
        
        .stat-item:hover::after {{
            left: 100%;
        }}
        
        .stat-value {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #409e80 50%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.5em;
            font-weight: 700;
            position: relative;
            z-index: 1;
        }}
        
        .stat-label {{
            color: #888;
            font-size: 0.85em;
            margin-top: 4px;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }}
        
        .project-actions {{
            display: flex;
            gap: 12px;
            margin-top: 18px;
            flex-wrap: wrap;
        }}
        
        .project-link {{
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, 
                #2d8659 0%,
                #40e0d0 50%,
                #2d8659 100%
            );
            color: #fff;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 
                0 3px 10px rgba(64, 158, 128, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }}
        
        .project-link.test-paradigm {{
            background: linear-gradient(135deg, 
                #e5c158 0%,
                #cd7f32 50%,
                #e5c158 100%
            );
            box-shadow: 
                0 3px 10px rgba(229, 193, 88, 0.35),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        }}
        
        .project-link:hover {{
            transform: translateY(-2px);
            box-shadow: 
                0 5px 15px rgba(64, 158, 128, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
            background: linear-gradient(135deg, 
                #40e0d0 0%,
                #e5c158 50%,
                #40e0d0 100%
            );
        }}
        
        .project-link.test-paradigm:hover {{
            background: linear-gradient(135deg, 
                #cd7f32 0%,
                #40e0d0 50%,
                #cd7f32 100%
            );
            box-shadow: 
                0 5px 15px rgba(229, 193, 88, 0.45),
                inset 0 1px 0 rgba(255, 255, 255, 0.3),
                inset 0 -1px 0 rgba(0, 0, 0, 0.1);
        }}
        
        .no-results {{
            text-align: center;
            padding: 60px;
            color: #999;
            font-size: 1.3em;
            font-weight: 300;
        }}
        
        .chart-container {{
            background: linear-gradient(135deg, 
                rgba(250, 250, 250, 0.95) 0%, 
                rgba(255, 255, 255, 0.98) 50%, 
                rgba(248, 248, 248, 0.95) 100%
            );
            padding: 35px;
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow: 
                0 8px 32px rgba(64, 158, 128, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.9),
                inset 0 -1px 0 rgba(64, 158, 128, 0.1);
            border: 1px solid rgba(64, 224, 208, 0.2);
            position: relative;
            overflow: hidden;
        }}
        
        .chart-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, 
                #2d8659 0%,
                #40e0d0 20%,
                #409e80 40%,
                #48d1cc 60%,
                #409e80 80%,
                #2d8659 100%
            );
            opacity: 0.6;
        }}
        
        .chart-container:hover::before {{
            opacity: 1;
        }}
        
        .chart-title {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #409e80 25%,
                #2d8659 50%,
                #409e80 75%,
                #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.6em;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid;
            border-image: linear-gradient(90deg, 
                transparent 0%,
                rgba(64, 158, 128, 0.3) 10%,
                rgba(64, 224, 208, 0.5) 50%,
                rgba(64, 158, 128, 0.3) 90%,
                transparent 100%
            ) 1;
            font-weight: 400;
            letter-spacing: -0.3px;
        }}
        
        .charts-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BEHub - Dashboard</h1>
        <p class="subtitle">Explore Your Behavioral Studies</p>
    </div>
    
    <div class="filters-container">
        <div class="filters-title">
            Filter Options
        </div>
        
        <div class="filters-grid">
            <div class="filter-group">
                <label class="filter-label">Modality</label>
                <select id="modalityFilter" class="filter-select">
                    <option value="">All Modalities</option>
"""
        
        for mod in unique_values['modalities']:
            html += f'                    <option value="{mod}">{mod.replace("_", " ").title()}</option>\n'
        
        html += """                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Cognitive Domain</label>
                <select id="domainFilter" class="filter-select">
                    <option value="">All Domains</option>
"""
        
        for domain in unique_values['domains']:
            html += f'                    <option value="{domain}">{domain.replace("_", " ").title()}</option>\n'
        
        html += """                </select>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Task Type</label>
                <select id="taskFilter" class="filter-select">
                    <option value="">All Task Types</option>
"""
        
        for task in unique_values['task_types']:
            html += f'                    <option value="{task}">{task.replace("_", " ").title()}</option>\n'
        
        html += f"""                </select>
            </div>
        </div>
        
        <div class="filters-grid" style="margin-top: 25px;">
            <div class="filter-group">
                <label class="filter-label">Mean Age (years)</label>
                <div class="slider-container">
                    <div class="slider-value" id="ageValue">{ranges['age_min']} - {ranges['age_max']}</div>
                    <input type="range" id="ageMin" min="{ranges['age_min']}" max="{ranges['age_max']}" value="{ranges['age_min']}" step="1">
                    <input type="range" id="ageMax" min="{ranges['age_min']}" max="{ranges['age_max']}" value="{ranges['age_max']}" step="1">
                </div>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Number of Subjects</label>
                <div class="slider-container">
                    <div class="slider-value" id="subjectsValue">{ranges['subjects_min']} - {ranges['subjects_max']}</div>
                    <input type="range" id="subjectsMin" min="{ranges['subjects_min']}" max="{ranges['subjects_max']}" value="{ranges['subjects_min']}" step="5">
                    <input type="range" id="subjectsMax" min="{ranges['subjects_min']}" max="{ranges['subjects_max']}" value="{ranges['subjects_max']}" step="5">
                </div>
            </div>
            
            <div class="filter-group">
                <label class="filter-label">Overall ICC (Mean)</label>
                <div class="slider-container">
                    <div class="slider-value" id="iccValue">-1.00 - 1.00</div>
                    <input type="range" id="iccMin" min="-1" max="1" value="-1" step="0.05">
                    <input type="range" id="iccMax" min="-1" max="1" value="1" step="0.05">
                </div>
            </div>
        </div>
        
        <div class="action-buttons">
            <button class="btn btn-apply" onclick="applyFilters()">Apply Filters</button>
            <button class="btn btn-reset" onclick="resetFilters()">Reset All</button>
        </div>
    </div>
    
    <div class="results-container">
        <div class="results-header">
            Results: <span class="results-count" id="resultsCount">0</span> Projects
        </div>
        <div class="projects-grid" id="projectsGrid"></div>
    </div>
    
    <div class="chart-container">
        <div class="chart-title">Sample Sizes Across Projects</div>
        <div id="sampleSizeRadar"></div>
    </div>
    
    <div class="chart-container">
        <div class="chart-title">Mean Ages Across Projects</div>
        <div id="ageRadar"></div>
    </div>
    
    <div class="charts-row">
        <div class="chart-container">
            <div class="chart-title">RT ICC Across Projects</div>
            <div id="rtIccRadar"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Accuracy ICC Across Projects</div>
            <div id="accIccRadar"></div>
        </div>
    </div>
    
    <div class="charts-row">
        <div class="chart-container">
            <div class="chart-title">RT Stability Across Projects</div>
            <div id="stabilityRadar"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">RT Consistency Across Projects</div>
            <div id="consistencyRadar"></div>
        </div>
    </div>
    
    <script>
        const allProjects = {projects_json};
        let filteredProjects = [...allProjects];
        
        // Update slider displays
        function updateSliderDisplays() {{
            const ageMin = document.getElementById('ageMin').value;
            const ageMax = document.getElementById('ageMax').value;
            document.getElementById('ageValue').textContent = `${{ageMin}} - ${{ageMax}}`;
            
            const subMin = document.getElementById('subjectsMin').value;
            const subMax = document.getElementById('subjectsMax').value;
            document.getElementById('subjectsValue').textContent = `${{subMin}} - ${{subMax}}`;
            
            const iccMin = parseFloat(document.getElementById('iccMin').value);
            const iccMax = parseFloat(document.getElementById('iccMax').value);
            document.getElementById('iccValue').textContent = `${{iccMin.toFixed(2)}} - ${{iccMax.toFixed(2)}}`;
        }}
        
        // Add event listeners to sliders
        ['ageMin', 'ageMax', 'subjectsMin', 'subjectsMax', 'iccMin', 'iccMax'].forEach(id => {{
            document.getElementById(id).addEventListener('input', updateSliderDisplays);
        }});
        
        function applyFilters() {{
            const modality = document.getElementById('modalityFilter').value;
            const domain = document.getElementById('domainFilter').value;
            const taskType = document.getElementById('taskFilter').value;
            
            const ageMin = parseFloat(document.getElementById('ageMin').value);
            const ageMax = parseFloat(document.getElementById('ageMax').value);
            const subMin = parseInt(document.getElementById('subjectsMin').value);
            const subMax = parseInt(document.getElementById('subjectsMax').value);
            const iccMin = parseFloat(document.getElementById('iccMin').value);
            const iccMax = parseFloat(document.getElementById('iccMax').value);
            
            filteredProjects = allProjects.filter(project => {{
                const info = project.project_info || {{}};
                const demo = project.demographics || {{}};
                const reliability = project.reliability_metrics || {{}};
                
                // Check categorical filters
                if (modality && info.modality !== modality) return false;
                if (domain && info.cognitive_domain !== domain) return false;
                if (taskType && info.task_type !== taskType) return false;
                
                // Check demographic filters
                if (demo.age_mean) {{
                    if (demo.age_mean < ageMin || demo.age_mean > ageMax) return false;
                }}
                if (demo.n_participants) {{
                    if (demo.n_participants < subMin || demo.n_participants > subMax) return false;
                }}
                
                // Check reliability filters using overall mean ICC (combining RT and Accuracy)
                let allIccs = [];
                
                for (const metrics of Object.values(reliability)) {{
                    if (metrics.rt_icc_mean !== null && metrics.rt_icc_mean !== undefined) {{
                        allIccs.push(metrics.rt_icc_mean);
                    }}
                    if (metrics.acc_icc_mean !== null && metrics.acc_icc_mean !== undefined) {{
                        allIccs.push(metrics.acc_icc_mean);
                    }}
                }}
                
                // Calculate overall mean ICC (combining all RT and Accuracy ICC values)
                if (allIccs.length > 0) {{
                    const overallMeanIcc = allIccs.reduce((a,b) => a+b) / allIccs.length;
                    if (overallMeanIcc < iccMin || overallMeanIcc > iccMax) return false;
                }}
                
                return true;
            }});
            
            displayProjects();
            updateCharts();
        }}
        
        function resetFilters() {{
            document.getElementById('modalityFilter').value = '';
            document.getElementById('domainFilter').value = '';
            document.getElementById('taskFilter').value = '';
            
            document.getElementById('ageMin').value = {ranges['age_min']};
            document.getElementById('ageMax').value = {ranges['age_max']};
            document.getElementById('subjectsMin').value = {ranges['subjects_min']};
            document.getElementById('subjectsMax').value = {ranges['subjects_max']};
            document.getElementById('iccMin').value = -1;
            document.getElementById('iccMax').value = 1;
            
            updateSliderDisplays();
            filteredProjects = [...allProjects];
            displayProjects();
            updateCharts();
        }}
        
        function displayProjects() {{
            const grid = document.getElementById('projectsGrid');
            const count = document.getElementById('resultsCount');
            
            count.textContent = filteredProjects.length;
            
            if (filteredProjects.length === 0) {{
                grid.innerHTML = '<div class="no-results">No projects match the selected filters</div>';
                return;
            }}
            
            grid.innerHTML = filteredProjects.map(project => {{
                const info = project.project_info || {{}};
                const demo = project.demographics || {{}};
                const reliability = project.reliability_metrics || {{}};
                
                // Get overall average ICC (combining RT and Accuracy)
                let allIccs = [];
                for (const metrics of Object.values(reliability)) {{
                    if (metrics.rt_icc_mean) allIccs.push(metrics.rt_icc_mean);
                    if (metrics.acc_icc_mean) allIccs.push(metrics.acc_icc_mean);
                }}
                const overallIcc = allIccs.length > 0 ? (allIccs.reduce((a,b) => a+b) / allIccs.length).toFixed(2) : 'N/A';
                
                return `
                    <div class="project-card">
                        <div class="project-name">${{project.project_name}}</div>
                        <div class="project-full-name">${{info.full_name || 'No description'}}</div>
                        <div class="project-tags">
                            <span class="tag modality">${{info.modality || 'unknown'}}</span>
                            <span class="tag domain">${{info.cognitive_domain || 'unknown'}}</span>
                        </div>
                        <div class="project-stats">
                            <div class="stat-item">
                                <div class="stat-value">${{demo.n_participants || 'N/A'}}</div>
                                <div class="stat-label">Subjects</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${{demo.age_mean ? demo.age_mean.toFixed(1) : 'N/A'}}</div>
                                <div class="stat-label">Mean Age</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${{overallIcc}}</div>
                                <div class="stat-label">Overall ICC</div>
                            </div>
                        </div>
                        <div class="project-actions">
                            <a href="Projects/${{project.project_name}}/${{project.project_name}}_overview.html" class="project-link">View Details</a>
                            ${{project.has_short_version ? `<a href="Projects/${{project.project_name}}/${{project.project_name}}_paradigm.html" class="project-link test-paradigm">Paradigm</a>` : ''}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        function updateCharts() {{
            const projectNames = filteredProjects.map(p => p.project_name);
            
            // Sample Size Radar - Bronze
            const sampleSizes = filteredProjects.map(p => p.demographics.n_participants || 0);
            const sampleSizeRadarData = [{{
                type: 'scatterpolar',
                r: sampleSizes,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(64, 158, 128, 0.25)',
                line: {{
                    color: '#2d8659',
                    width: 3
                }},
                marker: {{
                    color: '#2d8659',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const sampleSizeLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        gridcolor: 'rgba(64, 158, 128, 0.2)',
                        tickfont: {{color: '#1e5f44', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(64, 158, 128, 0.2)',
                        tickfont: {{color: '#1e5f44', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#1e5f44'}},
                showlegend: false,
                height: 500
            }};
            
            Plotly.newPlot('sampleSizeRadar', sampleSizeRadarData, sampleSizeLayout, {{responsive: true}});
            
            // Age Radar - Gold
            const ages = filteredProjects.map(p => p.demographics.age_mean || 0);
            const ageRadarData = [{{
                type: 'scatterpolar',
                r: ages,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(64, 224, 208, 0.25)',
                line: {{
                    color: '#40e0d0',
                    width: 3
                }},
                marker: {{
                    color: '#40e0d0',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const ageLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        gridcolor: 'rgba(64, 224, 208, 0.2)',
                        tickfont: {{color: '#2f6f50', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(64, 224, 208, 0.2)',
                        tickfont: {{color: '#2f6f50', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#2f6f50'}},
                showlegend: false,
                height: 500
            }};
            
            Plotly.newPlot('ageRadar', ageRadarData, ageLayout, {{responsive: true}});
            
            // RT ICC Radar - Copper
            const rtIccs = [];
            filteredProjects.forEach(p => {{
                let iccs = [];
                Object.values(p.reliability_metrics || {{}}).forEach(m => {{
                    if (m.rt_icc_mean !== null && m.rt_icc_mean !== undefined) {{
                        iccs.push(m.rt_icc_mean);
                    }}
                }});
                rtIccs.push(iccs.length > 0 ? iccs.reduce((a,b) => a+b) / iccs.length : 0);
            }});
            
            const rtIccRadarData = [{{
                type: 'scatterpolar',
                r: rtIccs,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(64, 158, 128, 0.25)',
                line: {{
                    color: '#409e80',
                    width: 3
                }},
                marker: {{
                    color: '#409e80',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const rtIccLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        range: [-0.2, 1],
                        gridcolor: 'rgba(64, 158, 128, 0.2)',
                        tickfont: {{color: '#1a5238', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(64, 158, 128, 0.2)',
                        tickfont: {{color: '#1a5238', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#1a5238'}},
                showlegend: false,
                height: 450
            }};
            
            Plotly.newPlot('rtIccRadar', rtIccRadarData, rtIccLayout, {{responsive: true}});
            
            // Accuracy ICC Radar - Rose Gold
            const accIccs = [];
            filteredProjects.forEach(p => {{
                let iccs = [];
                Object.values(p.reliability_metrics || {{}}).forEach(m => {{
                    if (m.acc_icc_mean !== null && m.acc_icc_mean !== undefined) {{
                        iccs.push(m.acc_icc_mean);
                    }}
                }});
                accIccs.push(iccs.length > 0 ? iccs.reduce((a,b) => a+b) / iccs.length : 0);
            }});
            
            const accIccRadarData = [{{
                type: 'scatterpolar',
                r: accIccs,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(183, 110, 121, 0.25)',
                line: {{
                    color: '#3d9970',
                    width: 3
                }},
                marker: {{
                    color: '#3d9970',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const accIccLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        range: [-0.2, 1],
                        gridcolor: 'rgba(183, 110, 121, 0.2)',
                        tickfont: {{color: '#8b5a65', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(183, 110, 121, 0.2)',
                        tickfont: {{color: '#8b5a65', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#8b5a65'}},
                showlegend: false,
                height: 450
            }};
            
            Plotly.newPlot('accIccRadar', accIccRadarData, accIccLayout, {{responsive: true}});
            
            // Stability Radar - Antique Gold
            const stability = [];
            filteredProjects.forEach(p => {{
                let stabs = [];
                Object.values(p.reliability_metrics || {{}}).forEach(m => {{
                    if (m.rt_cohens_d_mean !== null && m.rt_cohens_d_mean !== undefined) {{
                        const d_abs = Math.abs(m.rt_cohens_d_mean);
                        const stab_score = Math.max(0, Math.min(1, 1 - (d_abs / 2)));
                        stabs.push(stab_score);
                    }}
                }});
                stability.push(stabs.length > 0 ? stabs.reduce((a,b) => a+b) / stabs.length : 0);
            }});
            
            const stabilityRadarData = [{{
                type: 'scatterpolar',
                r: stability,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(197, 179, 88, 0.25)',
                line: {{
                    color: '#5fbc9a',
                    width: 3
                }},
                marker: {{
                    color: '#5fbc9a',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const stabilityLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        range: [0, 1],
                        gridcolor: 'rgba(197, 179, 88, 0.2)',
                        tickfont: {{color: '#9d8c4a', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(197, 179, 88, 0.2)',
                        tickfont: {{color: '#9d8c4a', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#9d8c4a'}},
                showlegend: false,
                height: 450
            }};
            
            Plotly.newPlot('stabilityRadar', stabilityRadarData, stabilityLayout, {{responsive: true}});
            
            // Consistency Radar - Silver
            const consistency = [];
            filteredProjects.forEach(p => {{
                let cons = [];
                Object.values(p.reliability_metrics || {{}}).forEach(m => {{
                    if (m.rt_cv_mean !== null && m.rt_cv_mean !== undefined) {{
                        const cons_score = Math.max(0, Math.min(1, 1 - (m.rt_cv_mean / 50)));
                        cons.push(cons_score);
                    }}
                }});
                consistency.push(cons.length > 0 ? cons.reduce((a,b) => a+b) / cons.length : 0);
            }});
            
            const consistencyRadarData = [{{
                type: 'scatterpolar',
                r: consistency,
                theta: projectNames,
                fill: 'toself',
                fillcolor: 'rgba(192, 192, 192, 0.25)',
                line: {{
                    color: '#48d1cc',
                    width: 3
                }},
                marker: {{
                    color: '#48d1cc',
                    size: 10,
                    line: {{
                        color: '#ffffff',
                        width: 2
                    }}
                }}
            }}];
            
            const consistencyLayout = {{
                polar: {{
                    bgcolor: 'rgba(255, 255, 255, 0.95)',
                    radialaxis: {{
                        visible: true,
                        range: [0, 1],
                        gridcolor: 'rgba(192, 192, 192, 0.2)',
                        tickfont: {{color: '#808080', size: 12, weight: 500}}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(192, 192, 192, 0.2)',
                        tickfont: {{color: '#808080', size: 11, weight: 500}}
                    }}
                }},
                paper_bgcolor: 'rgba(250, 250, 250, 0.5)',
                font: {{color: '#808080'}},
                showlegend: false,
                height: 450
            }};
            
            Plotly.newPlot('consistencyRadar', consistencyRadarData, consistencyLayout, {{responsive: true}});
        }}
        
        // Initialize
        applyFilters();
    </script>
</body>
</html>"""
        
        return html
    
    def save_dashboard(self, output_path: str = None):
        """Save dashboard HTML"""
        if output_path is None:
            output_path = self.base_path / "dashboard.html"
        else:
            output_path = Path(output_path)
        
        html = self.generate_dashboard_html()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\nDashboard saved: {output_path}")
        return output_path
    
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
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c2f 0%, #2d8659 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 50px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }}
        
        h1 {{
            color: #2d8659;
            margin-bottom: 10px;
            font-size: 3em;
            border-bottom: 4px solid #40e0d0;
            padding-bottom: 15px;
        }}
        
        .subtitle {{
            color: #666;
            margin-bottom: 40px;
            font-size: 1.3em;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .info-card {{
            background: linear-gradient(135deg, #e8f5f1 0%, #d4ebe3 100%);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #2d8659;
        }}
        
        .info-card h3 {{
            color: #2d8659;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }}
        
        .info-card p {{
            color: #333;
            font-size: 1.2em;
            font-weight: 600;
        }}
        
        .description-box {{
            background: #f8f9fa;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 40px;
            line-height: 1.8;
            font-size: 1.1em;
            color: #333;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            color: #2d8659;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-left: 6px solid #40e0d0;
            padding-left: 15px;
        }}
        
        .links-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .link-card {{
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 25px;
            transition: all 0.3s ease;
            cursor: pointer;
        }}
        
        .link-card:hover {{
            border-color: #40e0d0;
            box-shadow: 0 5px 20px rgba(64, 224, 208, 0.3);
            transform: translateY(-3px);
        }}
        
        .link-card h3 {{
            color: #2d8659;
            margin-bottom: 10px;
            font-size: 1.3em;
        }}
        
        .link-card p {{
            color: #666;
            margin-bottom: 15px;
            line-height: 1.6;
        }}
        
        .link-card code {{
            display: block;
            background: #e9ecef;
            padding: 10px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            color: #d63384;
            word-break: break-all;
            margin-top: 10px;
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
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .btn-demo {{
            background: linear-gradient(135deg, #e5c158 0%, #cd7f32 100%);
            color: white;
            flex: 1;
            min-width: 250px;
            font-size: 1.2em;
        }}
        
        .btn-demo:hover {{
            background: linear-gradient(135deg, #cd7f32 0%, #e5c158 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(229, 193, 88, 0.4);
        }}
        
        .btn-secondary {{
            background: linear-gradient(135deg, #2d8659 0%, #40e0d0 100%);
            color: white;
            flex: 0 0 auto;
            min-width: 200px;
        }}
        
        .btn-secondary:hover {{
            background: linear-gradient(135deg, #40e0d0 0%, #2d8659 100%);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(64, 224, 208, 0.4);
        }}
        
        .github-link {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #2d8659;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1em;
            padding: 10px 20px;
            border: 2px solid #2d8659;
            border-radius: 8px;
            transition: all 0.3s;
        }}
        
        .github-link:hover {{
            background: #2d8659;
            color: white;
        }}
        
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #e5c158;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            color: #856404;
            font-size: 1.05em;
        }}
        
        .highlight-box {{
            background: linear-gradient(135deg, #e8f5f1 0%, #d4ebe3 100%);
            border: 2px solid #40e0d0;
            padding: 25px;
            border-radius: 12px;
            margin-bottom: 30px;
        }}
        
        .highlight-box h3 {{
            color: #2d8659;
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        
        .highlight-box ul {{
            list-style-position: inside;
            color: #333;
            line-height: 2;
            font-size: 1.05em;
        }}
        
        .highlight-box li {{
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
                    <a href="https://github.com/YOUR_USERNAME/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy" 
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
                    <a href="https://github.com/YOUR_USERNAME/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short" 
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
                    <a href="https://github.com/YOUR_USERNAME/BEHub/tree/main/Projects/{project_name}/paradigm/presentation" 
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
                    <a href="https://github.com/YOUR_USERNAME/BEHub/tree/main/Projects/{project_name}/paradigm/psychopy/{project_name}_paradigm_short/Stimuli" 
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
    
    def run(self):
        """Generate dashboard"""
        print("=" * 70)
        print("Generating Interactive Dashboard")
        print("=" * 70)
        
        self.load_all_projects()
        
        if not self.all_projects:
            print("\nNo projects found!")
            return
        
        self.save_dashboard()
        
        # Generate paradigm pages
        print("\nGenerating paradigm pages...")
        launcher_count = self.save_test_paradigm_launchers()
        
        print(f"\n✅ Dashboard created with {len(self.all_projects)} projects!")
        print(f"✅ Created {launcher_count} paradigm page(s)!")
        print("=" * 70)


def main():
    import sys
    
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        base_path = "/home/niemannf/Documents/Konzepte/Behavioral_Exp_Hub/BEHub"
    
    dashboard = InteractiveDashboard(base_path)
    dashboard.run()


if __name__ == "__main__":
    main()
