# Mental Arithmetic Paradigm — pygame Implementation

Complete pygame implementation of the mental arithmetic behavioral paradigm based on Ulrich et al. (2014, 2016b).

## Files Included

- **math_paradigm_pygame.py** — Complete standalone Python script (no PsychoPy required)
- **environment.yml** — Mamba/conda environment file to recreate the exact environment
- **README_pygame.md** — This file

---

## Requirements

### Python Packages
```bash
pip install pygame pandas numpy
```

### Minimum Versions
- Python 3.10+
- pygame 2.0+
- pandas 1.3+
- numpy 1.20+

---

## Installation

### Recommended: Recreate the environment with mamba

```bash
mamba env create -f environment.yml
mamba activate pygame
```

### Manual setup

```bash
mamba create -n pygame python=3.10
mamba activate pygame
pip install pygame pandas numpy
```

---

## Running the Experiment

```bash
mamba activate pygame
python math_paradigm_pygame.py
```

This will:
1. Open a **pygame setup dialog** to collect participant information
2. Optionally run familiarization (3 min warm-up)
3. Optionally run skill evaluation (5 min adaptive calibration)
4. Run the main experiment (12 blocks)
5. Save data to CSV files in a `data/` directory

---

## Experiment Flow

### 1. Setup Dialog (pygame window)

A small GUI window appears before the experiment asking for:

- **Participant ID** — unique identifier (e.g. `sub-001`)
- **Session** — session number (e.g. `001`)
- **Run Familiarization** — checkbox (recommended: on)
- **Run Skill Evaluation** — checkbox (recommended: on)
- **Run Main Experiment** — checkbox
- **Starting Level** — only shown when Skill Evaluation is off

Click **Start Experiment** or press **ENTER** to proceed.  
Use **TAB** to move between text fields. **ESC** cancels and exits.

### 2. Familiarization (3 minutes, optional)

- Simple addition problems (Boredom condition)
- Participants learn to use the keyboard interface
- No data recorded

### 3. Skill Evaluation (5 minutes, optional)

- Adaptive difficulty (Flow condition)
- Starts at level 1 (or the manually set starting level)
- Difficulty adjusts based on performance
- **Starting level** = average difficulty of last 25% of trials

### 4. Main Experiment (~30 minutes)

#### Block Structure
- **12 task blocks** (170 seconds each)
- **11 rest periods** (20 seconds each) between blocks
- One of two counterbalanced sequences (randomly selected):
  - Sequence 1: B–F–O–B–F–B–O–F–O–F–B–O
  - Sequence 2: B–O–F–B–O–B–F–O–F–O–B–F
- After each block: 3 Likert scale questions (1–7, keyboard)

---

## Conditions Explained

### Boredom (B)
- Add a single digit (1–9) to a number between 100–109
- Sum always ≤ 110
- Example: `105 + 3`
- Fixed difficulty — does not adapt

### Flow (F)
- Starts at participant's estimated level
- Adapts: 2 consecutive correct → level +1; 2 consecutive incorrect → level −1
- Example progression: `5 + 7` → `45 + 8` → `32 + 7 + 4`

### Overload (O)
- Starts 3 levels above participant's estimated level
- Difficulty does not decrease below the starting level
- Example: if estimated level = 3, Overload starts at level 6

---

## Difficulty Levels

| Level | Description | Example |
|-------|-------------|---------|
| 1 | Two 1-digit numbers | 5 + 7 |
| 2 | One 2-digit + one 1-digit | 45 + 8 |
| 3 | One 2-digit + two 1-digit | 32 + 7 + 4 |
| 4 | Two 2-digit + one 1-digit | 56 + 78 + 3 |
| 5 | Two 2-digit + two 1-digit | 46 + 82 + 5 + 3 |
| 6 | Three 2-digit + one 1-digit | 34 + 67 + 91 + 5 |
| 7+ | Increasing complexity | … |

---

## Keyboard Controls

### During Math Tasks
| Key | Action |
|-----|--------|
| `0`–`9` / numpad | Enter digits |
| `ENTER` | Submit answer |
| `BACKSPACE` | Delete last digit |
| `ESC` | Save and quit |

### During Instructions / Likert
| Key | Action |
|-----|--------|
| `SPACE` | Continue |
| `1`–`7` / numpad `1`–`7` | Select Likert response |
| `ESC` | Save and quit |

---

## Data Files

Saved automatically in a `data/` directory (created if missing).

### Filename Format
```
data/{participant_id}_task_{YYYYMMDD_HHMMSS}.csv
data/{participant_id}_likert_{YYYYMMDD_HHMMSS}.csv
```

Example:
```
data/sub-001_task_20260301_143022.csv
data/sub-001_likert_20260301_143022.csv
```

### Task CSV Columns
```
participant_id, block, condition, difficulty_level, expression,
correct_answer, user_answer, is_correct, is_timeout, response_time_ms, timestamp
```

### Likert CSV Columns
```
participant_id, block, condition, q1_love_again, q2_well_matched, q3_thrilled, timestamp
```

---

## Customization

All timing and display settings are at the top of `math_paradigm_pygame.py`:

```python
BLOCK_DURATION  = 170.0   # seconds per block
TASK_TIMEOUT    = 18.0    # seconds per trial
BREAK_DURATION  = 4.0     # seconds between trials
REST_DURATION   = 20.0    # seconds between blocks

WINDOW_SIZE = (1400, 1050)
FULLSCREEN  = False
```

### Likert Questions
```python
LIKERT_QUESTIONS = [
    "Ich würde solche mathematischen Berechnungen nur zu gern noch einmal lösen",
    "Ich fühle mich optimal beansprucht",
    "Ich war begeistert",
]
```

### Block Sequences
```python
SEQUENCES = [
    ['B','F','O','B','F','B','O','F','O','F','B','O'],
    ['B','O','F','B','O','B','F','O','F','O','B','F'],
]
```

---

## Data Analysis

### Python
```python
import pandas as pd

task   = pd.read_csv('data/sub-001_task_20260301_143022.csv')
likert = pd.read_csv('data/sub-001_likert_20260301_143022.csv')

# Accuracy by condition
print(task.groupby('condition')['is_correct'].mean())

# Mean RT by condition (excluding timeouts)
print(task[~task['is_timeout']].groupby('condition')['response_time_ms'].mean())

# Likert means for Flow blocks
print(likert[likert['condition']=='F'][['q1_love_again','q2_well_matched','q3_thrilled']].mean())
```

### R
```r
task   <- read.csv("data/sub-001_task_20260301_143022.csv")
likert <- read.csv("data/sub-001_likert_20260301_143022.csv")

# Accuracy by condition
aggregate(is_correct ~ condition, data = task, FUN = mean)

# Mean RT by condition (excluding timeouts)
aggregate(response_time_ms ~ condition,
          data = task[!task$is_timeout, ], FUN = mean)

# Likert means for Flow blocks
flow <- likert[likert$condition == "F", ]
colMeans(flow[, c("q1_love_again", "q2_well_matched", "q3_thrilled")])
```

---

## Troubleshooting

### `No module named 'pygame'`
```bash
mamba activate pygame
pip install pygame
```

### Window does not open / black screen
Try toggling fullscreen in the config:
```python
FULLSCREEN = True
```

### Font rendering issues (special characters)
The script uses `DejaVu Sans` which is included with most Linux systems. If German umlauts appear wrong:
```bash
# Manjaro / Arch
sudo pacman -S ttf-dejavu
```

### Data not saving
- Check write permissions in the script directory
- Data saves automatically on ESC or on completion
- Check terminal output for error messages

---

## Why pygame instead of PsychoPy

PsychoPy has known compatibility issues on Arch/Manjaro Linux under Wayland due to its wxPython GUI dependency segfaulting at the C level. This pygame implementation is a complete drop-in replacement that:

- Has zero display-server dependencies (works on Wayland, X11, and XWayland)
- Uses only `pygame`, `pandas`, and `numpy`
- Preserves all experimental logic, timing, and data output identically
- Includes a native pygame setup dialog (no wx or Qt required)

---

## Integration with Neuroimaging (EEG / fMRI)

To send event markers, add trigger calls at key points in `math_paradigm_pygame.py`:

```python
import serial  # or your trigger library

# Example: at trial onset inside run_trial()
port.write(bytes([condition_code]))

# Example: at response submission
port.write(bytes([response_code]))
```

All timestamps are recorded in milliseconds using `time.monotonic()` for sub-millisecond precision.

---

## References

- Ulrich, M., et al. (2014). Neural correlates of experimentally induced flow experiences. *NeuroImage*.
- Ulrich, M., et al. (2016). Neural signatures of experimentally induced flow experiences identified in a typical fMRI block design with BOLD imaging. *NeuroImage*.

---

## Version History

- **v2.0** (2026) — pygame rewrite; removes PsychoPy/wxPython dependency; adds native pygame setup dialog; identical experimental logic and data output
- **v1.0** (2026) — original PsychoPy implementation
