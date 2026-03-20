#!/usr/bin/env python3
"""
Interactive Dashboard Generator
Creates a filterable overview dashboard from all project JSON files
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict

# Import metric registry for the radar dropdown labels
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
    if _rm_mod is not None:
        from reliability_metrics import METRIC_REGISTRY, ALL_METRIC_IDS  # type: ignore  # noqa
    else:
        raise ImportError
except ImportError:
    # Minimal fallback so the dashboard still generates without the module
    METRIC_REGISTRY = [
        {"id": "icc",       "label": "ICC(3,1)"},
        {"id": "pearson_r", "label": "Pearson r"},
        {"id": "cohens_d",  "label": "Stability (Cohen\u2019s d)"},
        {"id": "cv",        "label": "Consistency (CV)"},
    ]
    ALL_METRIC_IDS = [m["id"] for m in METRIC_REGISTRY]


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
                "task_type": "unknown", "language": None, "recording_modality": None,
            })
            data.setdefault("demographics", {
                "n_participants": 0, "age_mean": None,
                "age_std": None, "sex_distribution": {},
            })
            data.setdefault("reliability_metrics", {})

            data["short_version_stem"] = self.check_short_version(project_dir)
            data["has_short_version"]  = data["short_version_stem"] is not None
            self.all_projects.append(data)

        print(f"\n  Total projects loaded: {len(self.all_projects)}")
        return self.all_projects
    
    def check_short_version(self, project_dir: Path) -> str | None:
        """Check if a short version paradigm file exists.

        Search order:
          1. {name}_short_version_{language}.py  — language from description JSON
          2. {name}_short_version.py             — legacy filename (no language suffix)

        Returns the matched filename stem (without .py) so the dashboard can
        build the correct href, or None if no file is found.
        """
        project_name = project_dir.name

        # Try to read language_original from the description JSON
        lang = None
        desc_path = project_dir / f"{project_name}_description.json"
        if desc_path.exists():
            try:
                import json as _json
                with open(desc_path, encoding="utf-8") as fh:
                    desc = _json.load(fh)
                lang = desc.get("language_original") or desc.get("language") or None
                if lang:
                    lang = lang.strip().lower()
            except Exception:
                pass

        short_dir = project_dir / "paradigm" / "psychopy" / f"{project_name}_paradigm_short"

        # Build candidate list — language-suffixed first, then legacy
        candidates = []
        if lang:
            stem = f"{project_name}_short_version_{lang}"
            candidates += [
                (short_dir / f"{stem}.py", stem),
                (project_dir / "paradigm" / "psychopy" / f"{stem}.py", stem),
                (project_dir / "paradigm" / f"{stem}.py", stem),
            ]
        # Legacy (no language suffix)
        legacy_stem = f"{project_name}_short_version"
        candidates += [
            (short_dir / f"{legacy_stem}.py", legacy_stem),
            (project_dir / "paradigm" / "psychopy" / f"{legacy_stem}.py", legacy_stem),
            (project_dir / "paradigm" / f"{legacy_stem}.py", legacy_stem),
        ]

        for path, stem in candidates:
            if path.exists():
                print(f"  Found short version: {path}")
                return stem          # e.g. "OLMM_short_version_german"

        return None
    
    def extract_unique_values(self) -> Dict:
        """Extract unique values for filter options"""
        modalities = set()
        domains = set()
        task_types = set()
        languages = set()
        recording_modalities = set()
        
        for project in self.all_projects:
            info = project.get('project_info', {})
            modalities.add(info.get('modality', 'unknown'))
            domains.add(info.get('cognitive_domain', 'unknown'))
            task_types.add(info.get('task_type', 'unknown'))
            lang = info.get('language', None)
            if lang:
                languages.add(lang)
            rec_mod = info.get('recording_modality', None)
            if rec_mod:
                recording_modalities.add(rec_mod)
        
        return {
            'modalities': sorted(modalities),
            'domains': sorted(domains),
            'task_types': sorted(task_types),
            'languages': sorted(languages),
            'recording_modalities': sorted(recording_modalities)
        }
    
    def get_data_ranges(self) -> Dict:
        """Get min/max ranges for slider filters.
        Reads only from reliability_metrics (task trial types).
        Control/rest conditions are stored in control_reliability and excluded.
        """
        ages = []
        n_subjects = []
        rt_iccs = []
        acc_iccs = []
        rt_cvs = []
        
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
                if metrics.get('rt_cv_mean') is not None:
                    rt_cvs.append(metrics['rt_cv_mean'])
        
        return {
            'age_min': int(min(ages)) if ages else 18,
            'age_max': int(max(ages)) + 1 if ages else 65,
            'subjects_min': int(min(n_subjects)) if n_subjects else 0,
            'subjects_max': int(max(n_subjects)) + 5 if n_subjects else 100,
            'rt_icc_min': round(min(rt_iccs), 2) if rt_iccs else -1,
            'rt_icc_max': round(max(rt_iccs), 2) if rt_iccs else 1,
            'acc_icc_min': round(min(acc_iccs), 2) if acc_iccs else -1,
            'acc_icc_max': round(max(acc_iccs), 2) if acc_iccs else 1,
            'cv_min': max(0, round(min(rt_cvs) - 0.5, 1)) if rt_cvs else 0,
            'cv_max': round(max(rt_cvs) + 0.5, 1) if rt_cvs else 100,
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
    <title>Research BEE Hub — BEhavioral Experiments</title>
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
                rgba(144, 195, 168, 0.9) 0%,
                rgba(168, 218, 195, 0.95) 25%,
                rgba(192, 232, 216, 0.98) 50%,
                rgba(168, 218, 195, 0.95) 75%,
                rgba(144, 195, 168, 0.9) 100%
            );
            padding: 36px 50px 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 
                0 10px 40px rgba(64, 158, 128, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.8),
                inset 0 -1px 0 rgba(64, 158, 128, 0.15);
            border: 1px solid rgba(64, 158, 128, 0.3);
            position: relative;
            overflow: hidden;
            text-align: center;
        }}

        .header-text {{
            text-align: center;
        }}

        .header-logo-left {{
            position: absolute;
            left: 40px;
            top: 50%;
            transform: translateY(-50%);
            height: 110px;
            width: auto;
            filter: drop-shadow(0 3px 10px rgba(45,134,89,0.18));
        }}

        .header-logo-right {{
            position: absolute;
            right: 40px;
            top: 50%;
            transform: translateY(-50%);
            height: 110px;
            width: auto;
            filter: drop-shadow(0 3px 10px rgba(45,134,89,0.18));
        }}

        .header::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, 
                #2d8659 0%,
                #409e80 15%,
                #40e0d0 30%,
                #48d1cc 50%,
                #40e0d0 70%,
                #409e80 85%,
                #2d8659 100%
            );
            opacity: 0.8;
        }}
        
        h1 {{
            background: linear-gradient(135deg, 
                #1e5f44 0%,
                #2d8659 15%,
                #409e80 30%,
                #40e0d0 50%,
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
            gap: 8px;
            margin-bottom: 18px;
        }}
        
        .tag {{
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            border: 1px solid;
            font-weight: 500;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
        .tag.language {{ 
            border-color: #409e80;
            color: #1a5238;
            background: linear-gradient(135deg, #ffeee6 0%, #ffdcc9 100%);
        }}
        .tag.recording {{
            border-color: #c07838;
            color: #6b3a10;
            background: linear-gradient(135deg, #fff3e0 0%, #ffe0b8 100%);
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 100%;
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
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(0, 1fr));
            gap: 12px;
            margin-top: 18px;
        }}
        
        .project-link {{
            display: block;
            padding: 12px 24px;
            text-align: center;
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

        /* ── Reliability Metrics Explained panel ── */
        .reliability-panel {{
            background: linear-gradient(135deg,
                rgba(235, 248, 243, 0.95) 0%,
                rgba(245, 252, 249, 0.98) 50%,
                rgba(235, 248, 243, 0.95) 100%
            );
            padding: 0;
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

        .reliability-panel-toggle {{
            width: 100%;
            background: none;
            border: none;
            cursor: pointer;
            padding: 22px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            text-align: left;
        }}

        .reliability-panel-toggle:hover .reliability-panel-title {{
            opacity: 0.8;
        }}

        .reliability-toggle-arrow {{
            font-size: 1.2em;
            color: #409e80;
            transition: transform 0.3s ease;
            flex-shrink: 0;
            margin-left: 16px;
        }}

        .reliability-panel.open .reliability-toggle-arrow {{
            transform: rotate(180deg);
        }}

        .reliability-panel-body {{
            display: none;
            padding: 0 40px 40px;
        }}

        .reliability-panel.open .reliability-panel-body {{
            display: block;
        }}

        .reliability-panel::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #2d8659 0%, #409e80 20%, #40e0d0 40%,
                #48d1cc 60%, #40e0d0 80%, #2d8659 100%
            );
            opacity: 0.7;
        }}

        .reliability-panel-header {{
            margin-bottom: 0;
            padding-bottom: 0;
            border-bottom: none;
            flex: 1;
        }}

        .reliability-panel-title {{
            background: linear-gradient(135deg,
                #1e5f44 0%, #2d8659 25%, #409e80 50%, #2d8659 75%, #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.6em;
            font-weight: 400;
            letter-spacing: -0.5px;
            margin-bottom: 6px;
        }}

        .reliability-panel-subtitle {{
            color: #5a8a72;
            font-size: 0.95em;
            font-weight: 300;
        }}

        .metric-cards-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }}

        .metric-card {{
            background: linear-gradient(135deg, #ffffff 0%, #f5fdf9 100%);
            border-radius: 12px;
            border: 1px solid rgba(64, 158, 128, 0.2);
            overflow: hidden;
            box-shadow:
                0 4px 16px rgba(64, 158, 128, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow:
                0 8px 24px rgba(64, 224, 208, 0.2),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
        }}

        .metric-card-header {{
            background: linear-gradient(135deg,
                rgba(64, 158, 128, 0.12) 0%,
                rgba(64, 224, 208, 0.10) 100%
            );
            padding: 16px 20px 14px;
            border-bottom: 1px solid rgba(64, 158, 128, 0.15);
        }}

        .metric-card-name {{
            background: linear-gradient(135deg,
                #1e5f44 0%, #2d8659 40%, #409e80 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.05em;
            font-weight: 600;
            margin-bottom: 4px;
        }}

        .metric-card-tagline {{
            color: #5a8a72;
            font-size: 0.85em;
            font-weight: 300;
        }}

        .metric-card-body {{
            padding: 18px 20px 20px;
        }}

        .metric-card-points {{
            list-style: none;
            padding: 0;
            margin: 0 0 14px 0;
        }}

        .metric-card-points li {{
            color: #444;
            font-size: 0.9em;
            line-height: 1.55;
            padding: 4px 0 4px 18px;
            position: relative;
        }}

        .metric-card-points li::before {{
            content: '›';
            position: absolute;
            left: 4px;
            color: #40e0d0;
            font-weight: 700;
        }}

        .formula-box {{
            background: linear-gradient(135deg,
                rgba(255,255,255,0.85) 0%,
                rgba(240,252,248,0.90) 100%
            );
            border: 1px solid rgba(64, 158, 128, 0.22);
            border-left: 3px solid rgba(64, 224, 208, 0.6);
            border-radius: 10px;
            padding: 16px 18px 12px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.9);
        }}

        /* ── Math expression rendering ── */
        .math-expr {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 5px;
            line-height: 1;
            padding: 4px 0;
        }}

        .math-lhs {{
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 1.05em;
            font-style: italic;
            color: #1e5f44;
            font-weight: 600;
            margin-right: 2px;
        }}

        .math-eq {{
            font-family: 'Georgia', serif;
            font-size: 1em;
            color: #409e80;
            font-weight: 400;
            margin: 0 4px;
        }}

        /* CSS fraction: numerator over denominator with a bar */
        .math-frac {{
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            vertical-align: middle;
            margin: 0 3px;
            font-family: 'Georgia', 'Times New Roman', serif;
        }}

        .math-num {{
            font-size: 0.82em;
            color: #1e5f44;
            padding: 0 4px 2px;
            font-style: italic;
            white-space: nowrap;
        }}

        .math-bar {{
            width: 100%;
            height: 1.5px;
            background: #2d8659;
            min-width: 20px;
        }}

        .math-den {{
            font-size: 0.82em;
            color: #1e5f44;
            padding: 2px 4px 0;
            font-style: italic;
            white-space: nowrap;
        }}

        .math-var {{
            font-family: 'Georgia', 'Times New Roman', serif;
            font-style: italic;
            font-size: 0.95em;
            color: #1e5f44;
        }}

        .math-op {{
            font-size: 0.95em;
            color: #2d8659;
            margin: 0 2px;
            font-weight: 500;
        }}

        .math-sub {{
            font-size: 0.65em;
            vertical-align: sub;
            color: #2d8659;
        }}

        .math-sup {{
            font-size: 0.65em;
            vertical-align: super;
            color: #2d8659;
        }}

        .math-paren {{
            font-size: 1.15em;
            color: #5a8a72;
            font-weight: 300;
            line-height: 1;
        }}

        .math-sqrt {{
            display: inline-flex;
            align-items: center;
            margin: 0 2px;
        }}

        .math-sqrt-sign {{
            font-size: 1.2em;
            color: #2d8659;
            margin-right: 1px;
            line-height: 1;
        }}

        .math-sqrt-content {{
            border-top: 1.5px solid #2d8659;
            padding: 1px 4px 0;
            font-family: 'Georgia', serif;
            font-style: italic;
            font-size: 0.85em;
            color: #1e5f44;
        }}

        /* Legend row below the formula */
        .formula-legend {{
            font-size: 0.78em;
            color: #5a8a72;
            border-top: 1px dashed rgba(64,158,128,0.25);
            padding-top: 8px;
            line-height: 1.6;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }}

        .formula-legend b {{
            font-family: 'Georgia', serif;
            font-style: italic;
            font-weight: 600;
            color: #2d8659;
        }}

        /* Range badge */
        .formula-range {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-size: 0.78em;
            color: #fff;
            background: linear-gradient(90deg, #2d8659 0%, #40e0d0 100%);
            border-radius: 20px;
            padding: 3px 12px;
            font-weight: 500;
            align-self: flex-start;
            letter-spacing: 0.2px;
        }}

        /* ── About / description box ── */
        .about-box {{
            background: linear-gradient(135deg,
                rgba(255, 255, 255, 0.97) 0%,
                rgba(245, 252, 249, 0.98) 50%,
                rgba(255, 255, 255, 0.97) 100%
            );
            border: 1px solid rgba(64, 158, 128, 0.2);
            border-radius: 16px;
            margin-bottom: 30px;
            box-shadow:
                0 6px 24px rgba(64, 158, 128, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.9);
            position: relative;
            overflow: hidden;
        }}

        .about-box::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg,
                #2d8659 0%, #409e80 20%, #40e0d0 40%,
                #48d1cc 60%, #40e0d0 80%, #2d8659 100%
            );
            opacity: 0.7;
        }}

        .about-box-inner {{
            padding: 28px 36px 30px;
        }}

        .about-title {{
            background: linear-gradient(135deg,
                #1e5f44 0%, #2d8659 30%, #409e80 60%, #1e5f44 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.15em;
            font-weight: 600;
            margin-bottom: 12px;
            letter-spacing: -0.2px;
        }}

        .about-text {{
            color: #444;
            font-size: 0.95em;
            line-height: 1.75;
            margin: 0;
        }}

        .about-text strong {{
            color: #1e5f44;
            font-weight: 600;
        }}

        .about-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 18px;
        }}

        .about-tag {{
            padding: 4px 13px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
            border: 1px solid rgba(64, 158, 128, 0.35);
            color: #2d8659;
            background: linear-gradient(135deg,
                rgba(64, 224, 208, 0.08) 0%,
                rgba(64, 158, 128, 0.08) 100%
            );
        }}

        .radio-pill {{
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 7px 16px;
            border-radius: 20px;
            border: 1px solid rgba(64, 158, 128, 0.4);
            background: rgba(255,255,255,0.85);
            color: #1e5f44;
            font-size: 0.92em;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .radio-pill:hover {{
            border-color: #40e0d0;
            background: rgba(64, 224, 208, 0.1);
        }}
        .radio-pill input[type="radio"] {{
            accent-color: #2d8659;
            width: 14px;
            height: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <img src="logo_memoslap.png" alt="MemoSlap Logo" class="header-logo-left"/>
        <div class="header-text">
            <h1>Research BEE Hub</h1>
            <p class="subtitle">BEhavioral Experiments &mdash; Discover, Compare &amp; Validate Paradigms</p>
        </div>
        <img src="beehub_logo.svg" alt="BEE Hub Logo" class="header-logo-right"/>
    </div>

    <div class="about-box">
        <div class="about-box-inner">
            <div class="about-title">What is Research BEE Hub?</div>
            <p class="about-text">
                <strong>Research BEE Hub</strong> (Research Behavioral Experiments Hub) is an open-source, Git-versioned platform for storing, analysing, and discovering behavioral paradigms alongside their critical validation metrics. The core problem it addresses is the <strong>paradigm selection bottleneck</strong>: when designing a new experiment, researchers currently have no efficient way to identify a paradigm with known reliability, demonstrated effects, and established statistical power. General sharing platforms such as OSF or Pavlovia facilitate data sharing but lack dedicated infrastructure for the metrics that matter most &mdash; test-retest reliability (ICC), effect sizes, sample characteristics, and cognitive domain classification.
            </p>
            <p class="about-text" style="margin-top: 12px;">
                Research BEE Hub fills this gap by hosting curated, piloted, or published experiments together with their datasets, analysis code, and a standardised <strong>reliability profile</strong> for each paradigm. Every project follows a consistent BIDS-inspired folder structure, is version-controlled, and adheres to <strong>FAIR principles</strong> (Findable, Accessible, Interoperable, Reusable). The interactive dashboard allows researchers to search, filter, and compare paradigms by modality, cognitive domain, sample size, ICC, and consistency &mdash; making reliability benchmarks directly visible and comparable across studies. The structured output is also designed to be <strong>meta-analysis ready</strong>, enabling large-scale synthesis of field-wide reproducibility patterns.
            </p>
            <div class="about-tags">
                <span class="about-tag">&#10003; Open-source &amp; Git-versioned</span>
                <span class="about-tag">&#10003; FAIR principles</span>
                <span class="about-tag">&#10003; BIDS-inspired structure</span>
                <span class="about-tag">&#10003; Test-retest reliability (ICC)</span>
                <span class="about-tag">&#10003; Meta-analysis ready</span>
                <span class="about-tag">&#10003; Standardised reliability profiles</span>
            </div>
        </div>
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

            <div class="filter-group">
                <label class="filter-label">Recording Modality</label>
                <select id="recordingModalityFilter" class="filter-select">
                    <option value="">All Recording Modalities</option>
                    <option value="behavioral">Behavioral</option>
                    <option value="mri">MRI</option>
                    <option value="eeg">EEG</option>
                    <option value="pet">PET</option>
                    <option value="eye_tracking">Eye-tracking</option>
                    <option value="fnirs">fNIRS</option>
"""

        for rec in unique_values['recording_modalities']:
            fixed = {'behavioral','mri','eeg','pet','eye_tracking','fnirs'}
            if rec.lower() not in fixed:
                html += f'                    <option value="{rec}">{rec.replace("_", " ").title()}</option>\n'

        html += """                </select>
            </div>

            <div class="filter-group">
                <label class="filter-label">Language of Paradigm</label>
                <select id="languageFilter" class="filter-select">
                    <option value="">All Languages</option>
"""
        
        for lang in unique_values['languages']:
            html += f'                    <option value="{lang}">{lang.replace("_", " ").title()}</option>\n'
        
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
            
            <div class="filter-group">
                <label class="filter-label">Consistency CV Mean (%)</label>
                <div class="slider-container">
                    <div class="slider-value" id="cvValue">{ranges['cv_min']:.2f} - {ranges['cv_max']:.2f}</div>
                    <input type="range" id="cvMin" min="{ranges['cv_min']}" max="{ranges['cv_max']}" value="{ranges['cv_min']}" step="0.5">
                    <input type="range" id="cvMax" min="{ranges['cv_min']}" max="{ranges['cv_max']}" value="{ranges['cv_max']}" step="0.5">
                </div>
            </div>
        </div>
        
        <div class="filters-grid" style="margin-top: 25px;">
            <div class="filter-group" style="grid-column: 1 / -1;">
                <label class="filter-label">&#x1F4CA; Radar Plot — Metrics &amp; Data Source</label>
                <div style="display:flex; gap:16px; flex-wrap:wrap; align-items:center; margin-top:6px;">
                    <select id="radarMetricFilter" class="filter-select" style="min-width:220px;"
                            onchange="updateCharts()">
                        <option value="all">All Metrics</option>
                    <option value="icc">ICC(3,1)</option>
                    <option value="pearson_r">Pearson r</option>
                    <option value="cohens_d">Stability (Cohen's d)</option>
                    <option value="cv">Consistency (CV)</option>
                    </select>
                    <div style="display:flex; gap:8px; align-items:center;">
                        <label style="font-size:0.9em; color:#1e5f44; font-weight:600;">Data source:</label>
                        <label class="radio-pill">
                            <input type="radio" name="radarSource" value="task" checked
                                   onchange="updateCharts()"> Task
                        </label>
                        <label class="radio-pill">
                            <input type="radio" name="radarSource" value="control"
                                   onchange="updateCharts()"> Control
                        </label>
                        <label class="radio-pill">
                            <input type="radio" name="radarSource" value="both"
                                   onchange="updateCharts()"> Both
                        </label>
                    </div>
                </div>
            </div>
        </div>

        <div class="action-buttons">
            <button class="btn btn-apply" onclick="applyFilters()">Apply Filters</button>
            <button class="btn btn-reset" onclick="resetFilters()">Reset All</button>
        </div>
    </div>

    <div class="reliability-panel" id="reliabilityPanel">
        <button class="reliability-panel-toggle" onclick="toggleReliabilityPanel()" aria-expanded="false">
            <div class="reliability-panel-header">
                <div class="reliability-panel-title">Reliability Metrics Explained</div>
            </div>
            <span class="reliability-toggle-arrow">▼</span>
        </button>
        <div class="reliability-panel-body">
            <div style="margin-bottom: 20px; padding-bottom: 20px; border-bottom: 2px solid; border-image: linear-gradient(90deg, transparent 0%, rgba(64, 158, 128, 0.3) 10%, rgba(64, 224, 208, 0.5) 50%, rgba(64, 158, 128, 0.3) 90%, transparent 100%) 1;">
                <div class="reliability-panel-subtitle">
                    All scores are normalised to [0, 1] — higher values indicate better reliability. ICC values are derived from task trials only; control, rest, and baseline conditions are excluded.
                </div>
            </div>
            <div class="metric-cards-grid">

                <div class="metric-card">
                    <div class="metric-card-header">
                        <div class="metric-card-name">ICC(3,1) — Intraclass Correlation</div>
                        <div class="metric-card-tagline">Test-retest consistency across sessions — task trials only, control/rest/baseline excluded</div>
                    </div>
                    <div class="metric-card-body">
                        <ul class="metric-card-points">
                            <li>Computed exclusively on task trial types — control, rest, fixation, baseline, and catch conditions are always excluded from the ICC calculation</li>
                            <li>Two-way mixed model, single measures — sessions are treated as fixed, subjects as random; session mean differences are partialled out of the error term (consistency estimate, not absolute agreement)</li>
                            <li>Reported separately for RT and Accuracy; each value represents the mean ICC across subjects who completed at least two sessions</li>
                        </ul>
                        <div class="formula-box">
                            <div class="math-expr">
                                <span class="math-lhs">ICC(3,1)</span>
                                <span class="math-eq">=</span>
                                <span class="math-frac">
                                    <span class="math-num"><span class="math-var">MS</span><span class="math-sub">r</span> &minus; <span class="math-var">MS</span><span class="math-sub">e</span></span>
                                    <span class="math-bar"></span>
                                    <span class="math-den"><span class="math-var">MS</span><span class="math-sub">r</span> + (<span class="math-var">k</span> &minus; 1) &middot; <span class="math-var">MS</span><span class="math-sub">e</span></span>
                                </span>
                            </div>
                            <div class="formula-legend">
                                <b>MS<span style="font-size:0.75em;vertical-align:sub">r</span></b> = between-subjects mean square &nbsp;&middot;&nbsp;
                                <b>MS<span style="font-size:0.75em;vertical-align:sub">e</span></b> = error mean square &nbsp;&middot;&nbsp;
                                <b>k</b> = number of sessions
                            </div>
                            <span class="formula-range">&minus;1 &rarr; 1 &nbsp;&middot;&nbsp; higher = more consistent &nbsp;&middot;&nbsp; task trials only</span>
                        </div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-card-header">
                        <div class="metric-card-name">Pearson r &mdash; Correlation</div>
                        <div class="metric-card-tagline">Linear association between Session 1 and Session 2</div>
                    </div>
                    <div class="metric-card-body">
                        <ul class="metric-card-points">
                            <li>Measures how strongly values co-vary across sessions</li>
                            <li>Sensitive to linear association, not absolute agreement</li>
                            <li>Complements ICC as a simple, intuitive reliability indicator</li>
                        </ul>
                        <div class="formula-box">
                            <div class="math-expr">
                                <span class="math-lhs">r</span>
                                <span class="math-eq">=</span>
                                <span class="math-frac">
                                    <span class="math-num">&Sigma; (<span class="math-var">X</span><span class="math-sub">1</span> &minus; <span class="math-var">X&#772;</span><span class="math-sub">1</span>) (<span class="math-var">X</span><span class="math-sub">2</span> &minus; <span class="math-var">X&#772;</span><span class="math-sub">2</span>)</span>
                                    <span class="math-bar"></span>
                                    <span class="math-den">
                                        <span class="math-sqrt">
                                            <span class="math-sqrt-sign">&radic;</span>
                                            <span class="math-sqrt-content">&Sigma;(<span class="math-var">X</span><span class="math-sub">1</span>&minus;<span class="math-var">X&#772;</span><span class="math-sub">1</span>)<span class="math-sup">2</span> &middot; &Sigma;(<span class="math-var">X</span><span class="math-sub">2</span>&minus;<span class="math-var">X&#772;</span><span class="math-sub">2</span>)<span class="math-sup">2</span></span>
                                        </span>
                                    </span>
                                </span>
                            </div>
                            <div class="formula-legend">
                                <b>X<span style="font-size:0.75em;vertical-align:sub">1</span>, X<span style="font-size:0.75em;vertical-align:sub">2</span></b> = session values &nbsp;&middot;&nbsp;
                                <b>X&#772;<span style="font-size:0.75em;vertical-align:sub">1</span>, X&#772;<span style="font-size:0.75em;vertical-align:sub">2</span></b> = session means
                            </div>
                            <span class="formula-range">0 &rarr; 1 &nbsp;&middot;&nbsp; higher = stronger correlation</span>
                        </div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-card-header">
                        <div class="metric-card-name">Stability &mdash; from Cohen&apos;s d</div>
                        <div class="metric-card-tagline">Magnitude of mean change between sessions</div>
                    </div>
                    <div class="metric-card-body">
                        <ul class="metric-card-points">
                            <li>Detects systematic shifts such as practice or fatigue effects</li>
                            <li>Derived from Cohen&apos;s d &mdash; inverted so that higher = more stable</li>
                            <li>A score of 1 means no detectable shift across sessions</li>
                        </ul>
                        <div class="formula-box">
                            <div class="math-expr">
                                <span class="math-lhs">d</span>
                                <span class="math-eq">=</span>
                                <span class="math-frac">
                                    <span class="math-num"><span class="math-var">M</span><span class="math-sub">1</span> &minus; <span class="math-var">M</span><span class="math-sub">2</span></span>
                                    <span class="math-bar"></span>
                                    <span class="math-den"><span class="math-var">SD</span><span class="math-sub">pooled</span></span>
                                </span>
                                <span class="math-op" style="margin-left:14px; color:#5a8a72; font-size:0.8em; font-style:normal">&there4;</span>
                                <span class="math-lhs" style="margin-left:4px">Stability</span>
                                <span class="math-eq">=</span>
                                <span class="math-var">1</span>
                                <span class="math-op">&minus;</span>
                                <span class="math-frac">
                                    <span class="math-num">|<span class="math-var">d</span>|</span>
                                    <span class="math-bar"></span>
                                    <span class="math-den">2</span>
                                </span>
                            </div>
                            <div class="formula-legend">
                                <b>M<span style="font-size:0.75em;vertical-align:sub">1</span>, M<span style="font-size:0.75em;vertical-align:sub">2</span></b> = session means &nbsp;&middot;&nbsp;
                                <b>SD<span style="font-size:0.75em;vertical-align:sub">pooled</span></b> = pooled standard deviation
                            </div>
                            <span class="formula-range">0 &rarr; 1 &nbsp;&middot;&nbsp; higher = more stable across sessions</span>
                        </div>
                    </div>
                </div>

                <div class="metric-card">
                    <div class="metric-card-header">
                        <div class="metric-card-name">Consistency &mdash; from CV</div>
                        <div class="metric-card-tagline">Within-session trial-to-trial variability</div>
                    </div>
                    <div class="metric-card-body">
                        <ul class="metric-card-points">
                            <li>Captures trial-level noise within each session</li>
                            <li>Coefficient of Variation is inverted &mdash; lower noise = higher score</li>
                            <li>Identifies tasks where participants respond erratically</li>
                        </ul>
                        <div class="formula-box">
                            <div class="math-expr">
                                <span class="math-lhs">CV</span>
                                <span class="math-eq">=</span>
                                <span class="math-frac">
                                    <span class="math-num"><span class="math-var">SD</span></span>
                                    <span class="math-bar"></span>
                                    <span class="math-den"><span class="math-var">Mean</span></span>
                                </span>
                                <span class="math-op">&times; 100</span>
                                <span class="math-op" style="margin-left:14px; color:#5a8a72; font-size:0.8em; font-style:normal">&there4;</span>
                                <span class="math-lhs" style="margin-left:4px">Consistency</span>
                                <span class="math-eq">=</span>
                                <span class="math-var">1</span>
                                <span class="math-op">&minus;</span>
                                <span class="math-frac">
                                    <span class="math-num"><span class="math-var">CV</span></span>
                                    <span class="math-bar"></span>
                                    <span class="math-den">50</span>
                                </span>
                            </div>
                            <div class="formula-legend">
                                <b>SD</b> = within-session standard deviation &nbsp;&middot;&nbsp;
                                <b>Mean</b> = within-session mean RT
                            </div>
                            <span class="formula-range">0 &rarr; 1 &nbsp;&middot;&nbsp; higher = more consistent responding</span>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <div class="results-container">
        <div class="results-header">
            Results: <span class="results-count" id="resultsCount">0</span> Projects
        </div>
        <div class="projects-grid" id="projectsGrid"></div>
    </div>

    <div class="charts-row">
        <div class="chart-container">
            <div class="chart-title">RT ICC Across Projects (task trials only)</div>
            <div id="rtIccRadar"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">Accuracy ICC Across Projects (task trials only)</div>
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
            
            const cvMin = parseFloat(document.getElementById('cvMin').value);
            const cvMax = parseFloat(document.getElementById('cvMax').value);
            document.getElementById('cvValue').textContent = `${{cvMin.toFixed(2)}} - ${{cvMax.toFixed(2)}}`;
        }}
        
        // Add event listeners to sliders
        ['ageMin', 'ageMax', 'subjectsMin', 'subjectsMax', 'iccMin', 'iccMax', 'cvMin', 'cvMax'].forEach(id => {{
            document.getElementById(id).addEventListener('input', updateSliderDisplays);
        }});
        
        function toggleReliabilityPanel() {{
            const panel = document.getElementById('reliabilityPanel');
            const btn = panel.querySelector('.reliability-panel-toggle');
            panel.classList.toggle('open');
            btn.setAttribute('aria-expanded', panel.classList.contains('open'));
        }}

        function applyFilters() {{
            const modality = document.getElementById('modalityFilter').value;
            const domain = document.getElementById('domainFilter').value;
            const taskType = document.getElementById('taskFilter').value;
            const language = document.getElementById('languageFilter').value;
            const recordingModality = document.getElementById('recordingModalityFilter').value;
            
            const ageMin = parseFloat(document.getElementById('ageMin').value);
            const ageMax = parseFloat(document.getElementById('ageMax').value);
            const subMin = parseInt(document.getElementById('subjectsMin').value);
            const subMax = parseInt(document.getElementById('subjectsMax').value);
            const iccMin = parseFloat(document.getElementById('iccMin').value);
            const iccMax = parseFloat(document.getElementById('iccMax').value);
            const cvMin = parseFloat(document.getElementById('cvMin').value);
            const cvMax = parseFloat(document.getElementById('cvMax').value);
            
            filteredProjects = allProjects.filter(project => {{
                const info = project.project_info || {{}};
                const demo = project.demographics || {{}};
                const reliability = project.reliability_metrics || {{}};
                
                // Check categorical filters
                if (modality && info.modality !== modality) return false;
                if (domain && info.cognitive_domain !== domain) return false;
                if (taskType && info.task_type !== taskType) return false;
                if (language && info.language !== language) return false;
                if (recordingModality && info.recording_modality !== recordingModality) return false;
                
                // Check demographic filters
                if (demo.age_mean) {{
                    if (demo.age_mean < ageMin || demo.age_mean > ageMax) return false;
                }}
                if (demo.n_participants) {{
                    if (demo.n_participants < subMin || demo.n_participants > subMax) return false;
                }}
                
                // Check reliability filters - reliability_metrics contains task trial types only
                // (control/rest conditions are stored separately in control_reliability and excluded here)
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
                
                // Check Consistency CV filter
                let allCvs = [];
                for (const metrics of Object.values(reliability)) {{
                    if (metrics.rt_cv_mean !== null && metrics.rt_cv_mean !== undefined) {{
                        allCvs.push(metrics.rt_cv_mean);
                    }}
                }}
                if (allCvs.length > 0) {{
                    const overallMeanCv = allCvs.reduce((a,b) => a+b) / allCvs.length;
                    if (overallMeanCv < cvMin || overallMeanCv > cvMax) return false;
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
            document.getElementById('languageFilter').value = '';
            document.getElementById('recordingModalityFilter').value = '';
            document.getElementById('radarMetricFilter').value = 'all';
            document.querySelector('input[name="radarSource"][value="task"]').checked = true;

            document.getElementById('ageMin').value = {ranges['age_min']};
            document.getElementById('ageMax').value = {ranges['age_max']};
            document.getElementById('subjectsMin').value = {ranges['subjects_min']};
            document.getElementById('subjectsMax').value = {ranges['subjects_max']};
            document.getElementById('iccMin').value = -1;
            document.getElementById('iccMax').value = 1;
            document.getElementById('cvMin').value = {ranges['cv_min']};
            document.getElementById('cvMax').value = {ranges['cv_max']};
            
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
                
                // Get overall average ICC from task trial types only (control/rest excluded)
                let allIccs = [];
                for (const metrics of Object.values(reliability)) {{
                    if (metrics.rt_icc_mean) allIccs.push(metrics.rt_icc_mean);
                    if (metrics.acc_icc_mean) allIccs.push(metrics.acc_icc_mean);
                }}
                const overallIcc = allIccs.length > 0 ? (allIccs.reduce((a,b) => a+b) / allIccs.length).toFixed(2) : 'N/A';
                
                // Get overall mean Consistency CV
                let allCvs = [];
                for (const metrics of Object.values(reliability)) {{
                    if (metrics.rt_cv_mean !== null && metrics.rt_cv_mean !== undefined) allCvs.push(metrics.rt_cv_mean);
                }}
                const overallCv = allCvs.length > 0 ? (allCvs.reduce((a,b) => a+b) / allCvs.length).toFixed(2) : 'N/A';
                
                return `
                    <div class="project-card">
                        <div class="project-name">${{project.project_name}}</div>
                        <div class="project-full-name">${{info.full_name || 'No description'}}</div>
                        <div class="project-tags">
                            <span class="tag modality">${{info.modality || 'unknown'}}</span>
                            <span class="tag domain">${{info.cognitive_domain || 'unknown'}}</span>
                            ${{info.recording_modality ? `<span class="tag recording">${{info.recording_modality.toLowerCase()}}</span>` : ''}}
                            ${{info.language ? `<span class="tag language">${{info.language}}</span>` : ''}}
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
                            <div class="stat-item">
                                <div class="stat-value">${{overallCv !== 'N/A' ? overallCv + '%' : 'N/A'}}</div>
                                <div class="stat-label">Consistency CV</div>
                            </div>
                        </div>
                        <div class="project-actions">
                            <a href="Projects/${{project.project_name}}/${{project.project_name}}_overview.html" class="project-link">View Details</a>
                            ${{project.has_short_version ? `<a href="Projects/${{project.project_name}}/${{project.project_name}}_paradigm.html" class="project-link test-paradigm" title="Short version: ${{project.short_version_stem}}.py">Paradigm</a>` : ''}}
                        </div>
                    </div>
                `;
            }}).join('');
        }}
        
        // ── Metric & source registry (mirrors reliability_metrics.py) ──────
        const METRIC_REGISTRY = [
            {{
                id: 'icc', label: 'ICC(3,1)',
                rt_key: 'rt_icc_mean', acc_key: 'acc_icc_mean',
                normalise: v => Math.max(0, Math.min(1, v))
            }},
            {{
                id: 'pearson_r', label: 'Pearson r',
                rt_key: 'rt_pearson_r_mean', acc_key: 'acc_pearson_r_mean',
                normalise: v => Math.max(0, Math.min(1, v))
            }},
            {{
                id: 'cohens_d', label: 'Stability (Cohen\u2019s d)',
                rt_key: 'rt_cohens_d_mean', acc_key: 'acc_cohens_d_mean',
                normalise: v => Math.max(0, Math.min(1, 1 - Math.min(Math.abs(v), 2) / 2))
            }},
            {{
                id: 'cv', label: 'Consistency (CV)',
                rt_key: 'rt_cv_mean', acc_key: 'acc_cv_mean',
                normalise: v => Math.max(0, Math.min(1, 1 - v / 50))
            }},
            // ── Add new metrics here — add entry and matching key names ──────
        ];
        const METRIC_BY_ID = Object.fromEntries(METRIC_REGISTRY.map(m => [m.id, m]));

        function getRadarScores(project, selectedMetricId, source) {{
            // source: 'task' | 'control' | 'both'
            const taskRel    = project.reliability_metrics    || {{}};
            const controlRel = project.control_reliability    || {{}};

            // Determine which reliability dict(s) to draw from
            let dicts = [];
            if (source === 'task')    dicts = [taskRel];
            else if (source === 'control') {{
                // Fall back to task data if no control metrics available
                const hasControl = Object.values(controlRel).some(m =>
                    METRIC_REGISTRY.some(r => m[r.rt_key] !== null && m[r.rt_key] !== undefined)
                );
                dicts = hasControl ? [controlRel] : [taskRel];
            }}
            else dicts = [taskRel, controlRel];  // both

            // Metrics to include
            const metricsToShow = selectedMetricId === 'all'
                ? METRIC_REGISTRY
                : METRIC_REGISTRY.filter(m => m.id === selectedMetricId);

            const categories = [];
            const values     = [];

            dicts.forEach(dict => {{
                Object.entries(dict).forEach(([tt, metrics]) => {{
                    metricsToShow.forEach(reg => {{
                        const rtVal  = metrics[reg.rt_key];
                        const accVal = metrics[reg.acc_key];
                        if (rtVal !== null && rtVal !== undefined) {{
                            categories.push(tt + ' RT ' + reg.label);
                            values.push(reg.normalise(rtVal));
                        }}
                        if (accVal !== null && accVal !== undefined) {{
                            categories.push(tt + ' Acc ' + reg.label);
                            values.push(reg.normalise(accVal));
                        }}
                    }});
                }});
            }});

            return {{ categories, values }};
        }}

        function _buildRadarTrace(r_values, theta, color, fillColor) {{
            const r = [...r_values, r_values[0]];
            const t = [...theta, theta[0]];
            return [{{
                type: 'scatterpolar',
                r: r, theta: t,
                fill: 'toself',
                fillcolor: fillColor,
                line: {{ color: color, width: 3 }},
                marker: {{ color: color, size: 10, line: {{ color: '#fff', width: 2 }} }}
            }}];
        }}

        function _plotRadar(divId, traces, color) {{
            const layout = {{
                polar: {{
                    bgcolor: 'rgba(255,255,255,0.95)',
                    radialaxis: {{
                        visible: true, range: [-0.2, 1],
                        gridcolor: 'rgba(64,158,128,0.2)',
                        tickfont: {{ color: '#1a5238', size: 12, weight: 500 }}
                    }},
                    angularaxis: {{
                        gridcolor: 'rgba(64,158,128,0.2)',
                        tickfont: {{ color: '#1a5238', size: 11, weight: 500 }}
                    }}
                }},
                paper_bgcolor: 'rgba(250,250,250,0.5)',
                font: {{ color: '#1a5238' }},
                showlegend: false,
                height: 450
            }};
            Plotly.newPlot(divId, traces, layout, {{responsive: true}});
        }}

        function updateCharts() {{
            const projectNames    = filteredProjects.map(p => p.project_name);
            const selectedMetric  = document.getElementById('radarMetricFilter').value;
            const selectedSource  = document.querySelector('input[name="radarSource"]:checked').value;

            // ── Determine which metrics to draw in each of the four radars ──
            // When a specific metric is selected show that metric split across
            // RT (top-left) and Acc (top-right).  When 'all' is chosen keep
            // the original four-panel layout: RT-ICC, Acc-ICC, Stability, Consistency.
            if (selectedMetric !== 'all') {{
                const reg = METRIC_BY_ID[selectedMetric];
                // Build per-project RT and Acc scores for the selected metric
                const rtVals  = [];
                const accVals = [];
                filteredProjects.forEach(p => {{
                    const taskRel    = p.reliability_metrics    || {{}};
                    const controlRel = p.control_reliability    || {{}};
                    let dicts = [];
                    if (selectedSource === 'task') dicts = [taskRel];
                    else if (selectedSource === 'control') {{
                        const hasControl = Object.values(controlRel).some(m =>
                            m[reg.rt_key] !== null && m[reg.rt_key] !== undefined
                        );
                        dicts = hasControl ? [controlRel] : [taskRel];
                    }}
                    else dicts = [taskRel, controlRel];

                    let rtList = [], accList = [];
                    dicts.forEach(d => {{
                        Object.values(d).forEach(m => {{
                            if (m[reg.rt_key]  !== null && m[reg.rt_key]  !== undefined) rtList.push(reg.normalise(m[reg.rt_key]));
                            if (m[reg.acc_key] !== null && m[reg.acc_key] !== undefined) accList.push(reg.normalise(m[reg.acc_key]));
                        }});
                    }});
                    rtVals.push(rtList.length  > 0 ? rtList.reduce((a,b)=>a+b)/rtList.length   : 0);
                    accVals.push(accList.length > 0 ? accList.reduce((a,b)=>a+b)/accList.length : 0);
                }});

                const rtTraces  = _buildRadarTrace(rtVals,  projectNames, '#409e80', 'rgba(64,158,128,0.25)');
                const accTraces = _buildRadarTrace(accVals, projectNames, '#3d9970', 'rgba(61,153,112,0.25)');

                _plotRadar('rtIccRadar',      rtTraces,  '#409e80');
                _plotRadar('accIccRadar',     accTraces, '#3d9970');

                // Hide the stability & consistency panels — not applicable for a single metric
                document.getElementById('stabilityRadar').closest('.chart-container').style.display = 'none';
                document.getElementById('consistencyRadar').closest('.chart-container').style.display = 'none';

                // Update chart titles
                document.querySelector('#rtIccRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    reg.label + ' — RT  (' + selectedSource + ' conditions)';
                document.querySelector('#accIccRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    reg.label + ' — Accuracy  (' + selectedSource + ' conditions)';
            }} else {{
                // 'all' — restore original four-panel layout
                document.getElementById('stabilityRadar').closest('.chart-container').style.display = '';
                document.getElementById('consistencyRadar').closest('.chart-container').style.display = '';

                document.querySelector('#rtIccRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    'RT ICC Across Projects (' + selectedSource + ' conditions)';
                document.querySelector('#accIccRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    'Accuracy ICC Across Projects (' + selectedSource + ' conditions)';
                document.querySelector('#stabilityRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    'RT Stability Across Projects (' + selectedSource + ' conditions)';
                document.querySelector('#consistencyRadar').closest('.chart-container')
                    .querySelector('.chart-title').textContent =
                    'RT Consistency Across Projects (' + selectedSource + ' conditions)';

                const iccReg  = METRIC_BY_ID['icc'];
                const stabReg = METRIC_BY_ID['cohens_d'];
                const consReg = METRIC_BY_ID['cv'];

                function _perProjectMean(key, reg) {{
                    return filteredProjects.map(p => {{
                        const taskRel    = p.reliability_metrics    || {{}};
                        const controlRel = p.control_reliability    || {{}};
                        let dicts = [];
                        if (selectedSource === 'task') dicts = [taskRel];
                        else if (selectedSource === 'control') {{
                            const hasControl = Object.values(controlRel).some(m =>
                                m[reg[key]] !== null && m[reg[key]] !== undefined
                            );
                            dicts = hasControl ? [controlRel] : [taskRel];
                        }}
                        else dicts = [taskRel, controlRel];
                        let vals = [];
                        dicts.forEach(d => {{
                            Object.values(d).forEach(m => {{
                                const v = m[reg[key]];
                                if (v !== null && v !== undefined) vals.push(reg.normalise(v));
                            }});
                        }});
                        return vals.length > 0 ? vals.reduce((a,b)=>a+b)/vals.length : 0;
                    }});
                }}

                const rtIccs     = _perProjectMean('rt_key',  iccReg);
                const accIccs    = _perProjectMean('acc_key', iccReg);
                const stability  = _perProjectMean('rt_key',  stabReg);
                const consistency = _perProjectMean('rt_key', consReg);

                _plotRadar('rtIccRadar',      _buildRadarTrace(rtIccs,      projectNames, '#409e80', 'rgba(64,158,128,0.25)'),  '#409e80');
                _plotRadar('accIccRadar',     _buildRadarTrace(accIccs,     projectNames, '#3d9970', 'rgba(183,110,121,0.25)'), '#3d9970');
                _plotRadar('stabilityRadar',  _buildRadarTrace(stability,   projectNames, '#5fbc9a', 'rgba(197,179,88,0.25)'),  '#5fbc9a');
                _plotRadar('consistencyRadar',_buildRadarTrace(consistency, projectNames, '#48d1cc', 'rgba(192,192,192,0.25)'), '#48d1cc');
            }}
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
    


def main():
    import sys
    # Derive BEHub root relative to this script's location.
    # Expected layout: BEHub/code/03_generate_dashboard.py → BEHub/ is one level up.
    base_path = sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
    d = InteractiveDashboard(base_path)
    d.load_all_projects()
    d.save_dashboard()
    print("Dashboard created with", len(d.all_projects), "projects!")


if __name__ == "__main__":
    main()
