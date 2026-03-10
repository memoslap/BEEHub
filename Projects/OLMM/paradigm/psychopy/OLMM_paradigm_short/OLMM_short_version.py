#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LOCATO - Short Version (PsychoPy)
===================================
Spatial learning & memory task (fMRI-compatible).

Experiment structure
---------------------
00  Instructions Part 1      (7 slides, advance with LEFT arrow)
01  Practice Block           (map+house stimuli, 2 learning repetitions,
                              2500 ms/trial, 2000 ms feedback)
03  Learning Phase           (2 blocks × 4 repetitions, up/down interleaved;
                              learning + control conditions,
                              2500 ms/trial, 2000 ms feedback)
04  Instructions Part 3      (4 slides, advance with LEFT/RIGHT arrow)
05  AFC Test                 (alternative forced-choice, 3 options,
                              unlimited response time, shuffled order)

File naming convention (stimuli)
---------------------------------
  hH_pP_TYPE_DIRECTION_SIDE.jpg
    H    = house ID
    P    = position ID
    TYPE = "i"  (incorrect/foil map position)  |  "k" (correct map position)
    DIRECTION = "up" | "down"
    SIDE = "left" | "right"

Buttons
--------
  Learning / Practice : LEFT arrow = "correct position"  (code 1)
                        RIGHT arrow = "incorrect position" (code 2)
  Control             : LEFT arrow = yes, house is on RIGHT side (code 1)
                        RIGHT arrow = no, house is NOT on right side (code 2)
  AFC test            : keys 1, 2, 3 on number row

Data saved to:  data/<participant>_<date>_locato.csv

Requirements
-------------
  PsychoPy >= 2023.1
  Stimuli folders (set paths below):
    STIM_PRAC_DIR   - practice stimuli
    STIM_LEARN_DIR  - main learning stimuli  (allPicsA10_short)
    STIM_AFC_DIR    - AFC composite images
"""

# ============================================================
# Imports
# ============================================================
import os, sys, random, datetime, csv, glob
from psychopy import visual, core, event, data, gui, logging

# ============================================================
# Paths  – edit these to match your directory layout
# ============================================================
STIM_PRAC_DIR  = os.path.join("Stimuli", "prac")
STIM_LEARN_DIR = os.path.join("Stimuli", "allPicsA10_short")
STIM_AFC_DIR   = os.path.join("Stimuli", "AFC")
DATA_DIR       = "data"

# ============================================================
# Timing (seconds)
# ============================================================
TRIAL_DUR    = 2.500   # stimulus on-screen time
FEEDBACK_DUR = 2.000   # feedback display time
FIX_DUR      = 4.500   # inter-block fixation duration (fMRI)
INFO_DUR     = 4.500   # end-of-block info image duration

# fMRI scan period (used for dummy-pulse emulation if needed)
SCAN_PERIOD  = 4.500

# ============================================================
# Experiment info dialog
# ============================================================
exp_info = {
    "Participant": "",
    "Session":     "1",
    "Version":     ["A", "B"],
    "fMRI mode":   False,
}
dlg = gui.DlgFromDict(exp_info, title="LOCATO Short", sortKeys=False)
if not dlg.OK:
    core.quit()

participant = exp_info["Participant"]
session     = exp_info["Session"]
version     = exp_info["Version"]
fmri_mode   = exp_info["fMRI mode"]

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
date_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data_fname = os.path.join(DATA_DIR, f"{participant}_ses{session}_{date_str}_locato.csv")

# ============================================================
# Window & global clock
# ============================================================
win = visual.Window(
    size=(1280, 720),
    fullscr=True,
    color=(0, 0, 0),
    colorSpace="rgb255",
    units="pix",
    allowGUI=False,
)
global_clock = core.Clock()

# ============================================================
# Stimuli objects (reused throughout)
# ============================================================
fix_stim = visual.TextStim(
    win, text="+", color="white", height=80, pos=(0, 0)
)
feed_text = visual.TextStim(
    win, text="", color="white", height=50, pos=(0, 350),
    wrapWidth=1100,
)
main_img  = visual.ImageStim(win, pos=(0, -70), size=(1024, 787))
feed_img  = visual.ImageStim(win, pos=(0, -70), size=(1024, 787))
afc_img   = visual.ImageStim(win, pos=(0, 0),   size=(1224, 987))

# ============================================================
# Data writer
# ============================================================
_csv_file   = open(data_fname, "w", newline="", encoding="utf-8")
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow([
    "participant", "session", "version",
    "phase", "block", "rep", "trial",
    "stimulus", "stim_type", "direction", "side",
    "response_key", "correct", "rt", "onset_time"
])

def write_row(**kwargs):
    _csv_writer.writerow([
        participant, session, version,
        kwargs.get("phase", ""),
        kwargs.get("block", ""),
        kwargs.get("rep", ""),
        kwargs.get("trial", ""),
        kwargs.get("stimulus", ""),
        kwargs.get("stim_type", ""),
        kwargs.get("direction", ""),
        kwargs.get("side", ""),
        kwargs.get("response_key", ""),
        kwargs.get("correct", ""),
        kwargs.get("rt", ""),
        kwargs.get("onset_time", ""),
    ])
    _csv_file.flush()

# ============================================================
# Helper utilities
# ============================================================
def check_quit():
    """Allow Escape to abort at any time."""
    keys = event.getKeys(keyList=["escape"])
    if keys:
        _csv_file.close()
        win.close()
        core.quit()

def show_fixation(duration=FIX_DUR):
    """Show a white fixation cross for a given duration."""
    fix_stim.draw()
    win.flip()
    core.wait(duration)
    check_quit()

def parse_stim_name(filename):
    """
    Parse metadata encoded in filename.
    Pattern: hH_pP_TYPE_DIRECTION_SIDE.jpg
    Returns dict with keys: house, pos, stim_type, direction, side
    """
    base = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split("_")
    try:
        return {
            "house":      parts[0],          # e.g. "h1"
            "pos":        parts[1],          # e.g. "p37"
            "stim_type":  parts[2],          # "i" or "k"
            "direction":  parts[3],          # "up" or "down"
            "side":       parts[4],          # "left" or "right"
        }
    except IndexError:
        return {
            "house": base, "pos": "", "stim_type": "",
            "direction": "", "side": ""
        }

def get_stimuli(directory, extension=".jpg"):
    """Return sorted list of all image files in directory."""
    pattern = os.path.join(directory, f"*{extension}")
    files = sorted(glob.glob(pattern))
    return files

def pair_stimuli(all_files):
    """
    Build pairs: each 'k' file is paired with the matching 'i' file.
    Returns list of dicts: {correct: path, incorrect: path, meta: dict}
    The match is determined by the same house-ID (hH) portion.
    """
    k_files = [f for f in all_files if "_k_" in os.path.basename(f)]
    i_files = [f for f in all_files if "_i_" in os.path.basename(f)]

    pairs = []
    for kf in k_files:
        meta_k = parse_stim_name(kf)
        house_id = meta_k["house"]
        # find matching incorrect (same house)
        matching_i = [f for f in i_files if parse_stim_name(f)["house"] == house_id]
        if matching_i:
            pairs.append({
                "correct":   kf,
                "incorrect": matching_i[0],
                "meta":      meta_k,
            })
    return pairs

# ============================================================
# Trial runners
# ============================================================

def run_learning_trial(img_path, phase="learning", block=1, rep=1, trial_idx=1,
                       all_pairs=None):
    """
    Show stimulus for TRIAL_DUR, collect response, show feedback.
    Learning logic:
      'k' file → correct response is LEFT (key 1 / left arrow)
      'i' file → correct response is RIGHT (key 2 / right arrow)
    Feedback shows the CORRECT position image.
    """
    meta  = parse_stim_name(img_path)
    fname = os.path.basename(img_path)

    # Load image
    main_img.setImage(img_path)
    main_img.draw()
    win.flip()
    onset = global_clock.getTime()

    # Collect response within TRIAL_DUR window
    resp_clock = core.Clock()
    response   = None
    rt         = None
    while resp_clock.getTime() < TRIAL_DUR:
        keys = event.getKeys(keyList=["left", "right", "escape"],
                             timeStamped=resp_clock)
        if keys:
            key, t = keys[0]
            if key == "escape":
                _csv_file.close(); win.close(); core.quit()
            response = key
            rt       = t
            break
        check_quit()

    # Determine correctness
    is_correct_img = ("_k_" in fname)   # True if this is the correct map position
    if response == "left":
        resp_code = 1
    elif response == "right":
        resp_code = 2
    else:
        resp_code = 0   # no response / timeout

    if resp_code == 0:
        correct_flag = "timeout"
    elif (is_correct_img and resp_code == 1) or (not is_correct_img and resp_code == 2):
        correct_flag = "correct"
    else:
        correct_flag = "incorrect"

    # Find the correct feedback image (the 'k' file for this house)
    correct_fb_path = img_path  # fallback
    if all_pairs:
        for pair in all_pairs:
            if pair["correct"] == img_path or pair["incorrect"] == img_path:
                correct_fb_path = pair["correct"]
                break

    # Fill remaining stimulus time if response was early
    if rt is not None:
        remaining = TRIAL_DUR - rt
        if remaining > 0.05:
            main_img.draw()
            win.flip()
            core.wait(remaining)

    # Feedback screen
    if correct_flag == "timeout":
        feed_text.text = "Zu spät, die korrekte Position ist:"
    elif correct_flag == "correct":
        feed_text.text = "Richtig, die korrekte Position ist:"
    else:
        feed_text.text = "Falsch, die korrekte Position ist:"

    feed_img.setImage(correct_fb_path)
    feed_text.draw()
    feed_img.draw()
    win.flip()
    core.wait(FEEDBACK_DUR)
    check_quit()

    # Log
    write_row(
        phase=phase, block=block, rep=rep, trial=trial_idx,
        stimulus=fname,
        stim_type=meta["stim_type"],
        direction=meta["direction"],
        side=meta["side"],
        response_key=response,
        correct=correct_flag,
        rt=round(rt, 4) if rt else "",
        onset_time=round(onset, 4),
    )


def run_control_trial(img_path, phase="control", block=1, rep=1, trial_idx=1):
    """
    Control condition:
      Show a house-on-map image.
      Question: 'Is the house on the RIGHT side?'
      LEFT = yes / RIGHT = no
      Correct: 'right' in filename → yes (LEFT key)
                'left' in filename → no  (RIGHT key)
    """
    meta  = parse_stim_name(img_path)
    fname = os.path.basename(img_path)

    feed_text.text = "Ist das Haus auf der rechten Seite?"
    feed_img.setImage(img_path)
    feed_text.draw()
    feed_img.draw()
    win.flip()
    onset = global_clock.getTime()

    resp_clock = core.Clock()
    response   = None
    rt         = None
    while resp_clock.getTime() < TRIAL_DUR:
        keys = event.getKeys(keyList=["left", "right", "escape"],
                             timeStamped=resp_clock)
        if keys:
            key, t = keys[0]
            if key == "escape":
                _csv_file.close(); win.close(); core.quit()
            response = key
            rt       = t
            break
        check_quit()

    is_right  = ("right" in fname)
    resp_code = 1 if response == "left" else (2 if response == "right" else 0)

    if resp_code == 0:
        correct_flag = "timeout"
        fb_prefix = ("Zu spät, das Haus ist auf der rechten Seite:"
                     if is_right else
                     "Zu spät, das Haus ist nicht auf der rechten Seite:")
    elif (is_right and resp_code == 1) or (not is_right and resp_code == 2):
        correct_flag = "correct"
        fb_prefix = ("Richtig, das Haus ist auf der rechten Seite:"
                     if is_right else
                     "Richtig, das Haus ist nicht auf der rechten Seite:")
    else:
        correct_flag = "incorrect"
        fb_prefix = ("Falsch, das Haus ist auf der rechten Seite:"
                     if is_right else
                     "Falsch, das Haus ist nicht auf der rechten Seite:")

    feed_text.text = fb_prefix
    feed_text.draw()
    feed_img.draw()
    win.flip()
    core.wait(FEEDBACK_DUR)
    check_quit()

    write_row(
        phase=phase, block=block, rep=rep, trial=trial_idx,
        stimulus=fname,
        stim_type=meta["stim_type"],
        direction=meta["direction"],
        side=meta["side"],
        response_key=response,
        correct=correct_flag,
        rt=round(rt, 4) if rt else "",
        onset_time=round(onset, 4),
    )


def run_afc_trial(img_path, trial_idx=1):
    """
    Alternative Forced Choice test.
    Show composite AFC image; wait for keys 1, 2, or 3 (unlimited time).
    """
    fname = os.path.basename(img_path)
    afc_img.setImage(img_path)
    afc_img.draw()
    win.flip()
    onset = global_clock.getTime()

    keys = event.waitKeys(keyList=["1", "2", "3", "escape"])
    rt   = global_clock.getTime() - onset
    if "escape" in keys:
        _csv_file.close(); win.close(); core.quit()

    response = keys[0]
    write_row(
        phase="AFC", block="", rep="", trial=trial_idx,
        stimulus=fname, stim_type="", direction="", side="",
        response_key=response, correct="",
        rt=round(rt, 4), onset_time=round(onset, 4),
    )


# ============================================================
# Instruction displayer
# ============================================================
def show_instructions(img_paths, last_key="left"):
    """
    Show a sequence of instruction images.
    Advance with LEFT arrow; last slide advances with `last_key`.
    """
    instr_img = visual.ImageStim(win, size=(1280, 720), pos=(0, 0))
    for idx, p in enumerate(img_paths):
        if not os.path.isfile(p):
            # If file missing, show placeholder text
            visual.TextStim(win, text=f"[Instruction {idx+1}]",
                            color="white", height=60).draw()
        else:
            instr_img.setImage(p)
            instr_img.draw()
        win.flip()
        advance_key = last_key if idx == len(img_paths) - 1 else "left"
        event.waitKeys(keyList=[advance_key, "escape"])
        check_quit()


# ============================================================
# ============  MAIN EXPERIMENT  =============================
# ============================================================

# ----------------------------------------------------------
# 00 - Instructions Part 1
# ----------------------------------------------------------
instr1_imgs = [
    os.path.join("Stimuli", "instructions", f"instr_1{i}.jpg")
    for i in range(1, 8)
]
show_instructions(instr1_imgs, last_key="right")


# ----------------------------------------------------------
# 01 - Practice Block
# ----------------------------------------------------------
prac_files = get_stimuli(STIM_PRAC_DIR)
prac_pairs = pair_stimuli(prac_files)

# Build trial list: each pair contributes both the correct and incorrect image
prac_trials = []
for pair in prac_pairs:
    prac_trials.append(pair["correct"])
    prac_trials.append(pair["incorrect"])

# 2 learning repetitions
for rep in range(1, 3):
    random.shuffle(prac_trials)
    for t_idx, img in enumerate(prac_trials, 1):
        run_learning_trial(
            img, phase="practice", block=1, rep=rep,
            trial_idx=t_idx, all_pairs=prac_pairs
        )
    show_fixation(FIX_DUR)


# ----------------------------------------------------------
# 03 - Learning Phase
# ----------------------------------------------------------
learn_files = get_stimuli(STIM_LEARN_DIR)
learn_pairs = pair_stimuli(learn_files)

# Separate ups and downs and interleave
random.shuffle(learn_pairs)
ups   = [p for p in learn_pairs if p["meta"]["direction"] == "up"]
downs = [p for p in learn_pairs if p["meta"]["direction"] == "down"]

# Interleave: up, down, up, down ...
interleaved = []
for u, d in zip(ups, downs):
    interleaved.append(u)
    interleaved.append(d)
# Any remainder
for p in ups[len(downs):] + downs[len(ups):]:
    interleaved.append(p)
learn_pairs = interleaved

# Choose 5 random pairs for the control condition
ctrl_indices = random.sample(range(len(learn_pairs)), min(5, len(learn_pairs)))
ctrl_pairs   = [learn_pairs[i] for i in ctrl_indices]

# Build per-block stimulus lists
#   blk1/blk2: learning condition (each pair: correct + incorrect)
blk1 = []
blk2 = []
for pair in learn_pairs:
    blk1.append(pair["correct"])
    blk1.append(pair["incorrect"])
    blk2.append(pair["correct"])
    blk2.append(pair["incorrect"])

#   ctrl1: control condition (show same images with direction question)
ctrl1 = []
for pair in ctrl_pairs:
    ctrl1.append(pair["correct"])
    ctrl1.append(pair["incorrect"])

# Block order:  learning-1 → control-1 → learning-2
block_order = ["learning-1", "control-1", "learning-2"]

block_idx = 0
ctrl_idx  = 0

for phase_label in block_order:

    if phase_label.startswith("learning"):
        block_idx += 1
        stim_list = blk1 if phase_label == "learning-1" else blk2
        # 4 repetitions
        for rep in range(1, 5):
            random.shuffle(stim_list)
            for t_idx, img in enumerate(stim_list, 1):
                run_learning_trial(
                    img, phase=phase_label, block=block_idx,
                    rep=rep, trial_idx=t_idx,
                    all_pairs=learn_pairs
                )
            show_fixation(FIX_DUR)

    elif phase_label == "control-1":
        ctrl_idx += 1
        stim_list = ctrl1 * 1   # 1 run through all control stimuli (× 4 reps in original)
        for rep in range(1, 5):
            random.shuffle(stim_list)
            for t_idx, img in enumerate(stim_list, 1):
                run_control_trial(
                    img, phase="control", block=ctrl_idx,
                    rep=rep, trial_idx=t_idx
                )
            show_fixation(FIX_DUR)


# ----------------------------------------------------------
# 04 - Instructions Part 3 (AFC instructions)
# ----------------------------------------------------------
instr3_imgs = [
    os.path.join("Stimuli", "instructions", f"instr_3{i}.jpg")
    for i in range(1, 5)
]
show_instructions(instr3_imgs, last_key="right")


# ----------------------------------------------------------
# 05 - AFC Test
# ----------------------------------------------------------
afc_files = get_stimuli(STIM_AFC_DIR)
random.shuffle(afc_files)
for t_idx, img in enumerate(afc_files, 1):
    run_afc_trial(img, trial_idx=t_idx)


# ----------------------------------------------------------
# End screen
# ----------------------------------------------------------
visual.TextStim(
    win, text="Die Aufgabe ist beendet.\nVielen Dank!",
    color="white", height=60, wrapWidth=1100
).draw()
win.flip()
event.waitKeys(keyList=["space", "return", "escape"])

# ============================================================
# Clean up
# ============================================================
_csv_file.close()
win.close()
core.quit()
