#!/usr/bin/env python3
"""
02_generate_paradigm.py
Generates a per-project paradigm HTML page from *_description.json.
Rich sections (Procedure, Trial Structure, Design, Timing, Software,
Response Device, Keywords) live here; the overview HTML only shows
short description + background.
"""

import json
import importlib.util
from pathlib import Path
from typing import List, Dict


# ─────────────────────────────────────────────────────────────────────────────
# Small HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_description(project_dir: Path, project_name: str) -> Dict:
    """Load *_description.json; return minimal defaults if absent."""
    desc_path = project_dir / f"{project_name}_description.json"
    defaults = {
        "full_name":         project_name,
        "short_description": "Behavioral task.",
        "modality":          "unknown",
        "cognitive_domain":  "unknown",
        "task_type":         "unknown",
        "difficulty":        "unknown",
    }
    if not desc_path.exists():
        return defaults
    try:
        with open(desc_path, encoding="utf-8") as fh:
            data = json.load(fh)
        for k, v in defaults.items():
            data.setdefault(k, v)
        # Legacy compat
        if "description" in data and "short_description" not in data:
            data["short_description"] = data["description"]
        return data
    except Exception as e:
        print(f"  Warning: could not load {desc_path.name}: {e}")
        return defaults


def _info_card(label: str, value: str) -> str:
    if not value or value == "unknown":
        return ""
    return f"""        <div class="info-card">
            <div class="info-card-label">{label}</div>
            <div class="info-card-value">{value}</div>
        </div>"""


def _section(title: str, body_html: str) -> str:
    return f"""        <div class="section">
            <h2>{title}</h2>
            {body_html}
        </div>"""


def _text_box(text: str) -> str:
    return f'        <div class="text-box">{text}</div>'


def _timing_chips(timing_dict: Dict) -> str:
    chips = "".join(
        f'<span class="timing-chip"><span class="chip-label">'
        f'{k.replace("_", " ").title()}</span> {v}</span>'
        for k, v in timing_dict.items()
    )
    return f'<div class="timing-row">{chips}</div>'


def _keyword_chips(kws: List[str]) -> str:
    chips = "".join(f'<span class="kw-chip">{k}</span>' for k in kws)
    return f'<div class="kw-row">{chips}</div>'


_GITHUB_SVG = (
    '<svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor">'
    '<path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59'
    ".4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49"
    "-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53"
    ".63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87"
    ".51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15"
    "-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27"
    " 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1"
    ".16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65"
    " 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15"
    '.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>'
)


def _github_link(href: str, label: str = "View on GitHub") -> str:
    return (f'<a href="{href}" class="github-link" target="_blank">'
            f'{_GITHUB_SVG} {label}</a>')


# ─────────────────────────────────────────────────────────────────────────────
# CSS (metallic green — matches dashboard aesthetic)
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #e8e4e0 0%, #f0ece8 50%, #ffffff 100%);
            background-attachment: fixed;
            color: #2a1a0a;
            padding: 40px 20px;
            min-height: 100vh;
        }

        .container {
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
        }

        .container::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 4px;
            background: linear-gradient(90deg,
                #6b3a10 0%, #9e5c1e 12%, #c07838 25%, #d4a020 40%,
                #e8c048 50%, #d4a020 60%, #b8b0be 75%, #c4a0b4 88%, #6b3a10 100%
            );
            opacity: 0.85;
        }

        /* ── Header ─────────────────────────────────────────────────── */
        .project-code {
            background: linear-gradient(135deg,
                #6b3a10 0%, #9e5c1e 15%, #c07838 30%,
                #d4a020 50%, #b8b0be 70%, #c4a0b4 85%, #9e5c1e 100%
            );
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 3em;
            font-weight: 300;
            letter-spacing: -1px;
            margin-bottom: 8px;
            padding-bottom: 15px;
            border-bottom: 4px solid;
            border-image: linear-gradient(90deg,
                transparent 0%, rgba(160, 120, 60, 0.3) 10%,
                rgba(212, 160, 32, 0.6) 50%,
                rgba(160, 120, 60, 0.3) 90%, transparent 100%
            ) 1;
        }

        .project-full-name {
            color: #7a5030;
            font-size: 1.3em;
            font-style: italic;
            font-weight: 300;
            margin-bottom: 4px;
        }

        .page-subtitle {
            color: #9a6a40;
            font-size: 1.1em;
            font-weight: 300;
            margin-bottom: 36px;
        }

        /* ── Info cards ─────────────────────────────────────────────── */
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 18px;
            margin-bottom: 36px;
        }

        .info-card {
            background: linear-gradient(135deg,
                rgba(220, 200, 170, 0.85) 0%,
                rgba(240, 228, 208, 0.90) 50%,
                rgba(220, 200, 170, 0.85) 100%
            );
            padding: 18px 20px;
            border-radius: 12px;
            border-left: 4px solid #c07838;
            box-shadow: 0 4px 16px rgba(160, 110, 50, 0.15),
                        inset 0 1px 0 rgba(255, 255, 255, 0.7);
            border-top: 1px solid rgba(255, 255, 255, 0.6);
        }

        .info-card-label {
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 0.78em;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 700;
            margin-bottom: 6px;
        }

        .info-card-value {
            color: #3a2010;
            font-size: 1.1em;
            font-weight: 600;
        }

        /* ── Sections ───────────────────────────────────────────────── */
        .section {
            margin-bottom: 40px;
        }

        .section h2 {
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 50%, #b8b0be 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            font-size: 1.8em;
            font-weight: 400;
            border-left: 6px solid #d4a020;
            padding-left: 15px;
        }

        /* ── Text boxes (Description, Background) ───────────────────── */
        .text-box {
            background: linear-gradient(135deg,
                rgba(245, 236, 220, 0.90) 0%,
                rgba(255, 250, 240, 0.95) 50%,
                rgba(245, 236, 220, 0.90) 100%
            );
            padding: 28px 30px;
            border-radius: 12px;
            line-height: 1.8;
            font-size: 1.05em;
            color: #3a2010;
            border: 1px solid rgba(190, 150, 80, 0.25);
            box-shadow: 0 4px 16px rgba(160, 110, 50, 0.12);
            position: relative;
            overflow: hidden;
        }

        .text-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg,
                #9e5c1e 0%, #d4a020 30%, #e8c048 50%, #d4a020 70%, #c4a0b4 100%
            );
            opacity: 0.7;
        }

        /* ── Paradigm detail grid ────────────────────────────────────── */
        .detail-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 18px 24px;
        }

        @media (max-width: 720px) {
            .detail-grid { grid-template-columns: 1fr; }
            .container { padding: 28px 20px; }
        }

        .detail-cell {
            background: linear-gradient(135deg,
                rgba(225, 210, 185, 0.80) 0%,
                rgba(242, 232, 214, 0.88) 50%,
                rgba(225, 210, 185, 0.80) 100%
            );
            border: 1px solid rgba(190, 150, 80, 0.28);
            border-radius: 12px;
            padding: 20px 22px;
            box-shadow: 0 3px 12px rgba(160, 110, 50, 0.10),
                        inset 0 1px 0 rgba(255, 255, 255, 0.65);
            position: relative;
            overflow: hidden;
        }

        .detail-cell::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg,
                #9e5c1e 0%, #d4a020 50%, #c4a0b4 100%
            );
            opacity: 0.55;
        }

        .detail-cell-full { grid-column: 1 / -1; }

        .detail-label {
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 0.75em;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 1px solid rgba(190, 150, 80, 0.25);
        }

        .detail-text {
            color: #3a2010;
            font-size: 0.97em;
            line-height: 1.7;
        }

        /* ── Timing chips ───────────────────────────────────────────── */
        .timing-row { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 4px; }

        .timing-chip {
            background: rgba(212, 160, 32, 0.12);
            border: 1px solid rgba(190, 150, 80, 0.40);
            border-radius: 8px;
            padding: 5px 12px;
            font-size: 0.88em;
            color: #5a3010;
        }

        .chip-label {
            font-weight: 700;
            color: #9e5c1e;
            margin-right: 4px;
        }

        /* ── Keyword chips ──────────────────────────────────────────── */
        .kw-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; }

        .kw-chip {
            background: rgba(196, 160, 180, 0.18);
            border: 1px solid rgba(196, 160, 180, 0.40);
            border-radius: 14px;
            padding: 4px 13px;
            font-size: 0.85em;
            color: #7a3a50;
        }

        /* ── File / resource cards ──────────────────────────────────── */
        .links-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }

        .link-card {
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
            box-shadow: 0 4px 16px rgba(160, 110, 50, 0.15),
                        inset 0 1px 0 rgba(255, 255, 255, 0.65);
            position: relative;
            overflow: hidden;
        }

        .link-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #9e5c1e 0%, #d4a020 50%, #c4a0b4 100%);
            opacity: 0.6;
            transition: opacity 0.3s;
        }

        .link-card:hover {
            border-color: rgba(212, 160, 32, 0.55);
            box-shadow: 0 8px 28px rgba(160, 110, 50, 0.28),
                        inset 0 1px 0 rgba(255, 255, 255, 0.75);
            transform: translateY(-3px);
        }

        .link-card:hover::before { opacity: 1; }

        .link-card h3 {
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            font-size: 1.3em;
        }

        .link-card p {
            color: #6a4820;
            margin-bottom: 15px;
            line-height: 1.6;
        }

        .link-card code {
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
            margin-bottom: 14px;
        }

        /* ── GitHub link ────────────────────────────────────────────── */
        .github-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #8a4a10;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.0em;
            padding: 10px 20px;
            border: 2px solid rgba(190, 150, 80, 0.45);
            border-radius: 8px;
            transition: all 0.3s;
            background: rgba(255, 248, 235, 0.60);
        }

        .github-link:hover {
            background: linear-gradient(135deg, #9e5c1e 0%, #d4a020 100%);
            color: #fff8ee;
            border-color: #d4a020;
            box-shadow: 0 4px 14px rgba(180, 130, 40, 0.35);
        }

        /* ── Demo box ───────────────────────────────────────────────── */
        .demo-box {
            background: linear-gradient(135deg, #fdf5e0 0%, #f5e8c0 100%);
            border-left: 4px solid #d4a020;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 24px;
            color: #7a4a10;
            font-size: 1.05em;
            box-shadow: 0 2px 10px rgba(180, 130, 40, 0.12);
        }

        /* ── Buttons ────────────────────────────────────────────────── */
        .btn-container {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 16px 32px;
            border: none;
            border-radius: 12px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }

        .btn-demo {
            background: linear-gradient(135deg, #e8c048 0%, #d4a020 35%, #c07838 100%);
            color: #2a1a0a;
            flex: 1;
            min-width: 250px;
            font-size: 1.15em;
            box-shadow: 0 4px 20px rgba(212, 160, 32, 0.40),
                        inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }

        .btn-demo:hover {
            background: linear-gradient(135deg, #c07838 0%, #d4a020 50%, #e8c048 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 28px rgba(212, 160, 32, 0.55),
                        inset 0 1px 0 rgba(255, 255, 255, 0.35);
        }

        .btn-back {
            background: linear-gradient(135deg, #b8b0be 0%, #c8c0c8 40%, #c4a0b4 100%);
            color: #2a1a0a;
            flex: 0 0 auto;
            min-width: 200px;
            box-shadow: 0 4px 16px rgba(180, 150, 180, 0.35),
                        inset 0 1px 0 rgba(255, 255, 255, 0.40);
        }

        .btn-back:hover {
            background: linear-gradient(135deg, #c4a0b4 0%, #c8c0c8 50%, #b8b0be 100%);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(180, 150, 180, 0.50),
                        inset 0 1px 0 rgba(255, 255, 255, 0.40);
        }

        /* ── Instructions box ───────────────────────────────────────── */
        .instructions-box {
            background: linear-gradient(135deg,
                rgba(215, 195, 210, 0.80) 0%,
                rgba(235, 220, 230, 0.88) 50%,
                rgba(215, 195, 210, 0.80) 100%
            );
            border: 1px solid rgba(196, 160, 180, 0.45);
            border-radius: 12px;
            padding: 28px 30px;
            box-shadow: 0 6px 24px rgba(180, 140, 170, 0.20),
                        inset 0 1px 0 rgba(255, 255, 255, 0.65);
            position: relative;
            overflow: hidden;
        }

        .instructions-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg,
                #c4a0b4 0%, #b8b0be 35%, #d4a020 65%, #c07838 100%
            );
            opacity: 0.75;
        }

        .instructions-box h3 {
            background: linear-gradient(135deg, #8a4060 0%, #b8b0be 50%, #9e5c1e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 1.2em;
            margin-bottom: 16px;
        }

        .instructions-box ul { list-style: none; padding: 0; }

        .instructions-box li {
            color: #3a2010;
            margin-bottom: 10px;
            padding-left: 18px;
            position: relative;
            line-height: 1.6;
        }

        .instructions-box li::before {
            content: '›';
            position: absolute;
            left: 0;
            color: #c07838;
            font-weight: 700;
        }

        .instructions-box code {
            background: rgba(160, 110, 50, 0.12);
            border: 1px solid rgba(190, 150, 80, 0.30);
            border-radius: 4px;
            padding: 1px 7px;
            font-family: 'Courier New', monospace;
            font-size: 0.90em;
            color: #9e5c1e;
        }

        /* ── Footer ─────────────────────────────────────────────────── */
        .footer-row {
            margin-top: 44px;
            padding-top: 22px;
            border-top: 1px solid rgba(190, 150, 80, 0.25);
        }
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main class
# ─────────────────────────────────────────────────────────────────────────────

class InteractiveDashboard:
    """Generates paradigm HTML pages for each project."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.all_projects: List[Dict] = []

    # ── project loading ───────────────────────────────────────────────────

    def load_all_projects(self) -> List[Dict]:
        projects_path = self.base_path / "Projects"
        if not projects_path.exists():
            print(f"Projects path not found: {projects_path}")
            return []

        _generator = None
        try:
            candidates = [
                Path(__file__).parent / "01_multi_project_overview.py",
                self.base_path / "01_multi_project_overview.py",
                self.base_path.parent / "01_multi_project_overview.py",
                Path(__file__).parent / "multi_project_overview_GREEN.py",
                self.base_path / "multi_project_overview_GREEN.py",
            ]
            for c in candidates:
                if c.exists():
                    spec = importlib.util.spec_from_file_location("_overview", c)
                    mod  = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    _generator = mod.ProjectOverviewGenerator(str(self.base_path))
                    print(f"  Live-analysis fallback: {c.name}")
                    break
        except Exception as e:
            print(f"  Live-analysis not available: {e}")

        for project_dir in sorted(projects_path.iterdir()):
            if not project_dir.is_dir():
                continue
            project_name = project_dir.name
            data = None

            for jf in ([project_dir / f"{project_name}_data.json"]
                       + sorted(project_dir.glob("*_data.json"))):
                if jf.exists():
                    try:
                        with open(jf) as f:
                            data = json.load(f)
                        print(f"  Loaded (JSON): {project_name}")
                        break
                    except Exception as e:
                        print(f"  Error reading {jf.name}: {e}")

            if data is None and _generator is not None:
                if ((project_dir / "bids_data").exists()
                        or any(project_dir.rglob("*_RT_beh.tsv"))):
                    try:
                        data = _generator.analyze_project(project_name)
                        if data:
                            print(f"  Loaded (live): {project_name}")
                    except Exception as e:
                        print(f"  Live analysis failed for {project_name}: {e}")

            if data is None:
                # No behavioral data but description JSON may exist → still generate page
                desc_path = project_dir / f"{project_name}_description.json"
                if desc_path.exists():
                    data = {"project_name": project_name}
                    print(f"  Loaded (desc only): {project_name}")
                else:
                    print(f"  Skipped (no data): {project_name}")
                    continue

            data.pop("learning_stage_data", None)
            data.setdefault("project_name", project_name)
            data.setdefault("project_info", {})
            data.setdefault("demographics", {})
            data.setdefault("reliability_metrics", {})
            data["has_short_version"] = self.check_short_version(project_dir)
            self.all_projects.append(data)

        print(f"\n  Total projects loaded: {len(self.all_projects)}")
        return self.all_projects

    def check_short_version(self, project_dir: Path) -> bool:
        n = project_dir.name
        patterns = [
            project_dir / "paradigm" / "psychopy" / f"{n}_paradigm_short" / f"{n}_short_version.py",
            project_dir / "paradigm" / "psychopy" / f"{n}_short_version.py",
            project_dir / "paradigm" / f"{n}_short_version.py",
        ]
        return any(p.exists() for p in patterns)

    # ── HTML generator ────────────────────────────────────────────────────

    def generate_test_paradigm_launcher(self, project_data: Dict) -> str:
        pn       = project_data.get("project_name", "Unknown")
        proj_dir = self.base_path / "Projects" / pn

        # Load rich description JSON; fall back to project_info from data.json
        desc = _load_description(proj_dir, pn)
        pi   = project_data.get("project_info", {})
        for k, v in pi.items():
            desc.setdefault(k, v)

        full_name   = desc.get("full_name", pn)
        short_desc  = desc.get("short_description") or desc.get("description", "")
        long_desc   = desc.get("long_description", "")
        background  = desc.get("background", "")
        procedure   = desc.get("procedure", "")
        trial_str   = desc.get("trial_structure", "")
        design      = desc.get("design", "")
        software    = desc.get("software", "")
        resp_device = desc.get("response_device", "")
        timing      = desc.get("timing", {})
        keywords    = desc.get("keywords", [])
        modality    = desc.get("modality", "")
        domain      = desc.get("cognitive_domain", "")
        task_type   = desc.get("task_type", "")
        difficulty  = desc.get("difficulty", "")
        n_sessions  = desc.get("n_sessions", "")

        # ── Info cards ───────────────────────────────────────────────────
        card_defs = [
            ("Modality",         modality),
            ("Cognitive Domain", domain),
            ("Task Type",        task_type),
        ]
        info_cards = "\n".join(_info_card(lbl, val) for lbl, val in card_defs)

        # ── Description ──────────────────────────────────────────────────
        desc_content = short_desc
        if long_desc:
            desc_content += f"<br><br>{long_desc}"
        desc_section = (
            _section("Description", _text_box(desc_content))
            if desc_content else ""
        )

        # ── Background ───────────────────────────────────────────────────
        bg_section = (
            _section("Background", _text_box(background))
            if background else ""
        )

        # ── Paradigm Details grid ────────────────────────────────────────
        detail_cells = []
        if procedure:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Procedure</div>'
                f'<div class="detail-text">{procedure}</div></div>')
        if trial_str:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Trial Structure</div>'
                f'<div class="detail-text">{trial_str}</div></div>')
        if design:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Design</div>'
                f'<div class="detail-text">{design}</div></div>')
        if software:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Software</div>'
                f'<div class="detail-text">{software}</div></div>')
        if resp_device:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Response Device</div>'
                f'<div class="detail-text">{resp_device}</div></div>')
        if timing:
            detail_cells.append(
                f'<div class="detail-cell">'
                f'<div class="detail-label">Timing</div>'
                f'{_timing_chips(timing)}</div>')
        if keywords:
            detail_cells.append(
                f'<div class="detail-cell detail-cell-full">'
                f'<div class="detail-label">Keywords</div>'
                f'{_keyword_chips(keywords)}</div>')

        detail_section = ""
        if detail_cells:
            detail_section = _section(
                "Paradigm Details",
                f'<div class="detail-grid">{"".join(detail_cells)}</div>')

        # ── Interactive Demo ─────────────────────────────────────────────
        demo_section = _section("Interactive Demo", f"""
            <div class="demo-box">
                <strong>Try it now:</strong> Experience a browser-based demo version
                of this paradigm with reduced trials and timing.
            </div>
            <div class="btn-container">
                <a href="paradigm/psychopy/{pn}_paradigm_short/{pn}_demo.html"
                   class="btn btn-demo" target="_blank">
                    Launch Interactive Demo
                </a>
            </div>""")

        # ── Paradigm Files ───────────────────────────────────────────────
        gh = f"https://github.com/memoslap/BEEHub/tree/main/Projects/{pn}"
        files_section = _section("Paradigm Files", f"""
            <div class="links-grid">
                <div class="link-card">
                    <h3>PsychoPy Version</h3>
                    <p>Full implementation with all features for running the experiment.</p>
                    <code>BEEHub/Projects/{pn}/paradigm/psychopy/</code>
                    {_github_link(f"{gh}/paradigm/psychopy")}
                </div>
                <div class="link-card">
                    <h3>Short Test Version</h3>
                    <p>Reduced version for quick testing and debugging.</p>
                    <code>BEEHub/Projects/{pn}/paradigm/psychopy/{pn}_paradigm_short/</code>
                    {_github_link(f"{gh}/paradigm/psychopy/{pn}_paradigm_short")}
                </div>
                <div class="link-card">
                    <h3>Presentation Files</h3>
                    <p>Original Neurobehavioral Systems files with stimuli.</p>
                    <code>BEEHub/Projects/{pn}/paradigm/presentation/</code>
                    {_github_link(f"{gh}/paradigm/presentation")}
                </div>
                <div class="link-card">
                    <h3>Stimuli</h3>
                    <p>All stimulus materials and experimental resources.</p>
                    <code>BEEHub/Projects/{pn}/paradigm/psychopy/{pn}_paradigm_short/Stimuli/</code>
                    {_github_link(f"{gh}/paradigm/psychopy/{pn}_paradigm_short/Stimuli")}
                </div>
            </div>""")

        # ── Running instructions ─────────────────────────────────────────
        run_section = _section("Running the Paradigm", f"""
            <div class="instructions-box">
                <h3>PsychoPy Instructions</h3>
                <ul>
                    <li>Install PsychoPy (recommended version 2021.2 or later)</li>
                    <li>Clone or download the repository from GitHub</li>
                    <li>Navigate to the PsychoPy directory for this project</li>
                    <li>Run: <code>python {pn}_short_version.py</code> (test version)</li>
                    <li>Follow the on-screen instructions</li>
                </ul>
            </div>""")

        # ── Assemble ─────────────────────────────────────────────────────
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{pn} — Paradigm</title>
    <style>
{_CSS}
    </style>
</head>
<body>
    <div class="container">
        <div class="project-code">{pn}</div>
        <div class="project-full-name">{full_name}</div>
        <div class="page-subtitle">Paradigm Overview &amp; Resources</div>
        <div class="info-grid">
{info_cards}
        </div>
{demo_section}
{desc_section}
{bg_section}
{detail_section}
{files_section}
{run_section}
        <div class="footer-row">
            <a href="../../dashboard.html" class="btn btn-back">&#8592; Back to Dashboard</a>
        </div>
    </div>
</body>
</html>"""

    # ── Save paradigm pages ───────────────────────────────────────────────

    def save_test_paradigm_launchers(self) -> int:
        count = 0
        for project in self.all_projects:
            pn = project.get("project_name")
            project_dir = self.base_path / "Projects" / pn
            html = self.generate_test_paradigm_launcher(project)
            out  = project_dir / f"{pn}_paradigm.html"
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"  Created: {out}")
            count += 1
        return count


# ─────────────────────────────────────────────────────────────────────────────

def main():
    import sys
    base_path = (sys.argv[1] if len(sys.argv) > 1
                 else Path(__file__).resolve().parent.parent)
    d = InteractiveDashboard(base_path)
    d.load_all_projects()
    count = d.save_test_paradigm_launchers()
    print(f"Paradigm pages created: {count}")


if __name__ == "__main__":
    main()
