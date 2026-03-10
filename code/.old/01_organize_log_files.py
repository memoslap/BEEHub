#!/usr/bin/env python3
"""
Script 1: Organize Behavioral Log Files by Project

This script scans a source directory for behavioral log files and organizes them
by project name (extracted from the task field in the filename).

Author: Behavioral_Exp_Hub
Date: 2024
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_project_from_filename(filename: str) -> str:
    """
    Extract project name from BIDS-style filename.
    
    Expected format: sub-XXX_ses-X_task-PROJECTNAME_acq-X_beh.log
    
    Args:
        filename: Name of the log file
        
    Returns:
        Project name (e.g., 'OLMM') or 'Unknown' if pattern not found
    """
    # Pattern to extract task name (only alphanumeric, no underscores)
    pattern = r'task-([A-Za-z0-9]+)(?:_|$)'
    match = re.search(pattern, filename)
    
    if match:
        project_name = match.group(1)
        logger.debug(f"Extracted project '{project_name}' from '{filename}'")
        return project_name
    else:
        logger.warning(f"Could not extract project name from '{filename}'")
        return "Unknown"


def find_log_files(source_dir: str, pattern: str = "*.log") -> List[Tuple[str, str]]:
    """
    Recursively find all log files in source directory.
    
    Args:
        source_dir: Root directory to search
        pattern: File pattern to match (default: *.log)
        
    Returns:
        List of tuples (file_path, project_name)
    """
    log_files = []
    source_path = Path(source_dir)
    
    if not source_path.exists():
        logger.error(f"Source directory does not exist: {source_dir}")
        return log_files
    
    logger.info(f"Scanning directory: {source_dir}")
    
    # Find all log files recursively
    for log_file in source_path.rglob(pattern):
        if log_file.is_file():
            filename = log_file.name
            project_name = extract_project_from_filename(filename)
            log_files.append((str(log_file), project_name))
            logger.debug(f"Found: {filename} -> Project: {project_name}")
    
    logger.info(f"Found {len(log_files)} log files")
    return log_files


def extract_bids_structure(filename: str) -> Tuple[str, str]:
    """
    Extract BIDS directory structure from filename.
    
    Expected format: sub-XXX_ses-Y_task-PROJECTNAME_acq-Z_beh.log
    
    Args:
        filename: Name of the log file
        
    Returns:
        Tuple of (subject_dir, session_dir) e.g., ('sub-001', 'ses-3')
    """
    # Pattern to extract subject and session
    sub_pattern = r'(sub-[A-Za-z0-9]+)'
    ses_pattern = r'(ses-[A-Za-z0-9]+)'
    
    sub_match = re.search(sub_pattern, filename)
    ses_match = re.search(ses_pattern, filename)
    
    subject_dir = sub_match.group(1) if sub_match else 'sub-unknown'
    session_dir = ses_match.group(1) if ses_match else 'ses-unknown'
    
    return subject_dir, session_dir


def organize_by_project(
    log_files: List[Tuple[str, str]], 
    output_dir: str,
    copy: bool = True
) -> Dict[str, int]:
    """
    Organize log files into project-specific BIDS directories.
    
    Args:
        log_files: List of tuples (file_path, project_name)
        output_dir: Base output directory for projects
        copy: If True, copy files; if False, move files
        
    Returns:
        Dictionary mapping project names to number of files
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    project_counts = {}
    
    for file_path, project_name in log_files:
        filename = Path(file_path).name
        
        # Extract BIDS structure from filename
        subject_dir, session_dir = extract_bids_structure(filename)
        
        # Create BIDS directory structure: Projects/PROJECTNAME/raw_logs/sub-XXX/ses-Y/
        bids_dir = output_path / project_name / "raw_logs" / subject_dir / session_dir
        bids_dir.mkdir(parents=True, exist_ok=True)
        
        # Destination file path
        dest_path = bids_dir / filename
        
        # Copy or move file
        try:
            if copy:
                shutil.copy2(file_path, dest_path)
                logger.info(f"Copied: {filename} -> {project_name}/raw_logs/{subject_dir}/{session_dir}/")
            else:
                shutil.move(file_path, dest_path)
                logger.info(f"Moved: {filename} -> {project_name}/raw_logs/{subject_dir}/{session_dir}/")
            
            # Update counts
            project_counts[project_name] = project_counts.get(project_name, 0) + 1
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
    
    return project_counts


def create_project_readme(output_dir: str, project_name: str, file_count: int):
    """
    Create a README.md file in each project directory.
    
    Args:
        output_dir: Base output directory
        project_name: Name of the project
        file_count: Number of log files in the project
    """
    project_path = Path(output_dir) / project_name
    readme_path = project_path / "README.md"
    
    readme_content = f"""# {project_name} Behavioral Data

## Overview
This directory contains behavioral data for the {project_name} project.

## Data Summary
- **Number of log files**: {file_count}
- **Data organized**: {Path.cwd()}

## Directory Structure
```
{project_name}/
├── raw_logs/              # Original log files in BIDS structure
│   ├── sub-001/
│   │   ├── ses-1/
│   │   │   └── sub-001_ses-1_task-{project_name}_acq-1_beh.log
│   │   └── ses-2/
│   │       └── sub-001_ses-2_task-{project_name}_acq-1_beh.log
│   └── sub-002/
│       └── ses-1/
│           └── sub-002_ses-1_task-{project_name}_acq-1_beh.log
├── bids_data/             # BIDS-formatted TSV files (generated by script 02)
│   ├── sub-001/
│   │   ├── ses-1/
│   │   │   ├── sub-001_ses-1_task-{project_name}_acq-1_events.tsv
│   │   │   └── sub-001_ses-1_task-{project_name}_acq-1_events.json
│   │   └── ses-2/
│   │       ├── sub-001_ses-2_task-{project_name}_acq-1_events.tsv
│   │       └── sub-001_ses-2_task-{project_name}_acq-1_events.json
│   └── sub-002/
│       └── ses-1/
│           ├── sub-002_ses-1_task-{project_name}_acq-1_events.tsv
│           └── sub-002_ses-1_task-{project_name}_acq-1_events.json
└── reliability_metrics.json  # Reliability metrics (generated by script 03)
```

## Processing Steps

1. **Organize log files** (✓ Complete)
   ```bash
   python scripts/01_organize_log_files.py
   ```

2. **Convert to BIDS format**
   ```bash
   python scripts/02_convert_to_bids.py --project-name {project_name}
   ```

3. **Compute reliability metrics**
   ```bash
   python scripts/03_compute_reliability.py --project-name {project_name}
   ```

## File Naming Convention

Log files follow BIDS naming convention:
```
sub-<label>_ses-<label>_task-{project_name}_acq-<label>_beh.log
```

Directory structure follows BIDS hierarchy:
```
raw_logs/sub-<label>/ses-<label>/<filename>
```

## Notes
- Raw log files are preserved in BIDS structure in `raw_logs/`
- BIDS conversion creates standardized TSV files with matching structure
- Reliability metrics enable cross-project comparisons

## Contact
For questions about this dataset, please contact the project PI.
"""
    
    with open(readme_path, 'w') as f:
        f.write(readme_content)
    
    logger.info(f"Created README for project: {project_name}")


def print_summary(project_counts: Dict[str, int], output_dir: str):
    """
    Print summary statistics of the organization process.
    
    Args:
        project_counts: Dictionary of project names to file counts
        output_dir: Base output directory
    """
    print("\n" + "=" * 70)
    print("LOG FILE ORGANIZATION SUMMARY")
    print("=" * 70)
    print(f"\nOutput Directory: {output_dir}\n")
    print(f"{'Project Name':<30} {'Number of Files':<15}")
    print("-" * 70)
    
    total_files = 0
    for project, count in sorted(project_counts.items()):
        print(f"{project:<30} {count:<15}")
        total_files += count
    
    print("-" * 70)
    print(f"{'TOTAL':<30} {total_files:<15}")
    print("\n" + "=" * 70)
    
    # Print directory structure
    print("\nCreated BIDS Directory Structure:")
    for project in sorted(project_counts.keys()):
        print(f"  {output_dir}/")
        print(f"    └── {project}/")
        print(f"        ├── README.md")
        print(f"        └── raw_logs/")
        print(f"            └── sub-<label>/")
        print(f"                └── ses-<label>/")
        print(f"                    └── [{project_counts[project]} log files total]")
        print()


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description='Organize behavioral log files by project name',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Organize log files from MeMoSLAP study (using default BEHub/Projects structure)
  python 01_organize_log_files.py --source-dir /media/Data04/Studies/MeMoSLAP
  
  # Move files instead of copying
  python 01_organize_log_files.py \\
      --source-dir /path/to/data \\
      --move
  
  # Use custom output directory
  python 01_organize_log_files.py \\
      --source-dir /path/to/data \\
      --output-dir /custom/path/Projects
  
  # Use custom file pattern
  python 01_organize_log_files.py \\
      --source-dir /path/to/data \\
      --file-pattern "*.txt"
        """
    )
    
    # Determine default output directory relative to script location
    script_dir = Path(__file__).parent
    default_output_dir = script_dir.parent / "Projects"
    
    parser.add_argument(
        '--source-dir',
        type=str,
        required=True,
        help='Source directory containing subject folders with log files'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=str(default_output_dir),
        help=f'Output directory for organized projects (default: {default_output_dir})'
    )
    
    parser.add_argument(
        '--file-pattern',
        type=str,
        default='*.log',
        help='File pattern to match (default: *.log)'
    )
    
    parser.add_argument(
        '--move',
        action='store_true',
        help='Move files instead of copying (default: copy)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Print header
    print("\n" + "=" * 70)
    print("BEHAVIORAL LOG FILE ORGANIZER")
    print("=" * 70)
    print(f"\nSource Directory: {args.source_dir}")
    print(f"Output Directory: {args.output_dir}")
    print(f"File Pattern: {args.file_pattern}")
    print(f"Operation: {'MOVE' if args.move else 'COPY'}")
    print(f"\nExpected structure: BEHub/code/ (scripts) and BEHub/Projects/ (data)")
    print()
    
    # Find log files
    log_files = find_log_files(args.source_dir, args.file_pattern)
    
    if not log_files:
        logger.error("No log files found. Exiting.")
        return
    
    # Organize files
    logger.info("Organizing files by project...")
    project_counts = organize_by_project(
        log_files, 
        args.output_dir, 
        copy=not args.move
    )
    
    # Create README files for each project
    logger.info("Creating project README files...")
    for project_name, count in project_counts.items():
        create_project_readme(args.output_dir, project_name, count)
    
    # Print summary
    print_summary(project_counts, args.output_dir)
    
    print("\n✓ Organization complete!")
    print(f"\nNext step: Convert to BIDS format")
    print(f"  python 02_convert_to_bids.py")


if __name__ == "__main__":
    main()
