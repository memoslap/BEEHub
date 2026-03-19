#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OLMM – Set A (PsychoPy) [English]
=========================
Object-Location Memory Mapping – full experiment, counterbalanced Set A.

Folder layout (relative to this script)
-----------------------------------------
Stimuli/
  instr/              Folie1.JPG … Folie12.JPG
  learning/
    block1/ … block4/ hH_pP_TYPE_DIRECTION[_qN]_SIDE.jpg
  control/
    block1/ block2/   hH_pP_TYPE_DIRECTION[_qN]_SIDE.jpg
  AFC/                hHpP_N.jpg

Experiment order
-----------------
  00  Instructions Part 1   Folie1–8
  01  Learning  Block 1     4 reps
  02  Control   Block 1     4 reps
  03  Learning  Block 2     4 reps
  04  Learning  Block 3     4 reps
  05  Control   Block 2     4 reps
  06  Learning  Block 4     4 reps
  07  Instructions Part 2   Folie9–12
  08  AFC Test

Button mapping
--------------
  Learning  : LEFT  = Ja  (korrekte Position)   RIGHT = Nein (falsche Position)
  Control   : LEFT  = Ja  (Haus rechts)          RIGHT = Nein (Haus nicht rechts)
  AFC       : 1 / 2 / 3

Trial timing
------------
  Phase 1  2.5 s  Stimulus shown; response accepted any time in this window.
                  In behavioural mode: key labels shown below image.
  Phase 2  2.0 s  "Correct!" / "Wrong!" / "Too late!" above the correct-
                  position (_k_) image.  Window runs to completion; no early exit.
"""

import os, random, datetime, csv, glob
from psychopy import visual, core, event, gui

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts): return os.path.join(_HERE, *parts)

STIM_LEARN_DIRS = [_p("Stimuli","learning",f"block{i}") for i in range(1,5)]
STIM_CTRL_DIRS  = [_p("Stimuli","control", f"block{i}") for i in range(1,3)]
STIM_AFC_DIR    = _p("Stimuli","AFC")
STIM_INSTR_DIR  = _p("Stimuli","instr")
DATA_DIR        = _p("data")

# ── Timing (seconds) ───────────────────────────────────────────────────────────
TRIAL_DUR    = 2.500   # stimulus + response window
FEEDBACK_DUR = 2.000   # correct-position feedback
FIX_DUR      = 4.500   # inter-block fixation (fMRI baseline)

# ── Experiment dialog ──────────────────────────────────────────────────────────
exp_info = {"Participant": "", "Session": "1", "fMRI mode": False}
dlg = gui.DlgFromDict(exp_info, title="OLMM Set A", sortKeys=False)
if not dlg.OK: core.quit()

participant = exp_info["Participant"]
session     = exp_info["Session"]
fmri_mode   = exp_info["fMRI mode"]

os.makedirs(DATA_DIR, exist_ok=True)
date_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data_fname = _p("data", f"{participant}_ses{session}_{date_str}_OLMM_A.csv")

# ── Window & clock ─────────────────────────────────────────────────────────────
win = visual.Window(size=(1280,720), fullscr=True,
                    color=(0,0,0), colorSpace="rgb255",
                    units="pix", allowGUI=False)
global_clock = core.Clock()

# ── Visual objects ─────────────────────────────────────────────────────────────
fix_stim  = visual.TextStim(win, text="+", color="white", height=80, pos=(0,0))
feed_text = visual.TextStim(win, text="",  color="white", height=50, pos=(0,350),
                            wrapWidth=1100)
main_img  = visual.ImageStim(win, pos=(0,-70), size=(1024,787))
feed_img  = visual.ImageStim(win, pos=(0,-70), size=(1024,787))
afc_img   = visual.ImageStim(win, pos=(0,  0), size=(1224,987))

key_label_left  = visual.TextStim(win, text="<- Yes",   color="white", height=40,
                                  pos=(-340,-490), wrapWidth=600)
key_label_right = visual.TextStim(win, text="No ->", color="white", height=40,
                                  pos=( 340,-490), wrapWidth=600)

# ── Data writer ────────────────────────────────────────────────────────────────
_csv_file   = open(data_fname, "w", newline="", encoding="utf-8")
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow(["participant","session","set",
                      "phase","block","rep","trial",
                      "stimulus","stim_type","direction","side",
                      "response_key","correct","rt","onset_time"])

def write_row(**kw):
    _csv_writer.writerow([participant, session, "A",
        kw.get("phase",""), kw.get("block",""), kw.get("rep",""), kw.get("trial",""),
        kw.get("stimulus",""), kw.get("stim_type",""),
        kw.get("direction",""), kw.get("side",""),
        kw.get("response_key",""), kw.get("correct",""),
        kw.get("rt",""), kw.get("onset_time","")])
    _csv_file.flush()

# ── Helpers ────────────────────────────────────────────────────────────────────
def check_quit():
    if event.getKeys(keyList=["escape"]):
        _csv_file.close(); win.close(); core.quit()

def show_fixation(duration=FIX_DUR):
    fix_stim.draw(); win.flip(); core.wait(duration); check_quit()

def get_stimuli(directory):
    files = sorted(glob.glob(os.path.join(directory,"*.jpg")) +
                   glob.glob(os.path.join(directory,"*.JPG")))
    return [f for f in files
            if not os.path.basename(f).lower().startswith("thumbs")]

def parse_stim_name(filename):
    base  = os.path.splitext(os.path.basename(filename))[0]
    parts = base.split("_")
    try:
        return {"house": parts[0], "pos": parts[1], "stim_type": parts[2],
                "direction": parts[3], "side": parts[-1]}
    except IndexError:
        return {"house": base, "pos":"", "stim_type":"", "direction":"", "side":""}

def pair_stimuli(all_files):
    k_files = [f for f in all_files if "_k_" in os.path.basename(f)]
    i_files = [f for f in all_files if "_i_" in os.path.basename(f)]
    pairs = []
    for kf in k_files:
        hid   = parse_stim_name(kf)["house"]
        foils = [f for f in i_files if parse_stim_name(f)["house"] == hid]
        pairs.append({"correct": kf, "foils": foils,
                      "meta": parse_stim_name(kf)})
    return pairs

def shuffle_no_repeat(items, key_fn):
    items = items[:]
    random.shuffle(items)
    for _ in range(200):
        ok = True
        for i in range(1, len(items)):
            if key_fn(items[i]) == key_fn(items[i-1]):
                ok = False
                j = random.randint(i, len(items)-1)
                items[i], items[j] = items[j], items[i]
        if ok: break
    return items

def show_instructions(img_paths):
    img_stim = visual.ImageStim(win, size=(1280,720), pos=(0,0))
    for p in img_paths:
        if os.path.isfile(p):
            img_stim.setImage(p); img_stim.draw()
        else:
            visual.TextStim(win, text=f"[{os.path.basename(p)}]",
                            color="white", height=60).draw()
        win.flip()
        event.waitKeys(keyList=["space","escape"]); check_quit()


def show_text_slide(title, body, footer="[SPACE to continue]", advance_key="space"):
    """Render a text instruction slide on a black background."""
    visual.TextStim(win, text=title, color="white", height=36,
                    bold=True, pos=(0, 280), wrapWidth=1100).draw()
    visual.Line(win, start=(-540, 240), end=(540, 240),
                lineColor="white", lineWidth=1).draw()
    visual.TextStim(win, text=body, color="white", height=28,
                    pos=(0, 20), wrapWidth=1050, alignText="left").draw()
    visual.TextStim(win, text=footer, color="white", height=22,
                    pos=(0, -295), wrapWidth=1100).draw()
    win.flip()
    event.waitKeys(keyList=[advance_key, "escape"]); check_quit()


def show_instructions_part1():
    """8 text slides for the learning phase (English)."""
    show_text_slide(
        title="Welcome – OLMM Study",
        body=(
            "Thank you for participating!\n\n"
            "In this task you will learn where houses are located on a map.\n\n"
            "Your task is to remember the exact position\n"
            "of each house."
        ),
        footer="Slide 1 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="What you will see",
        body=(
            "You will see an image showing a house on a map.\n\n"
            "The house is either in the CORRECT position\n"
            "or in a WRONG position.\n\n"
            "Your task: decide whether the house\n"
            "is in the correct location."
        ),
        footer="Slide 2 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Keys",
        body=(
            "Press:\n\n"
            "  ARROW LEFT   <-  YES, that is the correct position\n\n"
            "  ARROW RIGHT  ->  NO,  that is not the correct position\n\n"
            "You have 2.5 seconds per image.\n"
            "Respond as quickly and accurately as possible."
        ),
        footer="Slide 3 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Feedback",
        body=(
            "After each response you will see feedback:\n\n"
            "  'Correct!'   – your answer was right\n\n"
            "  'Wrong!'     – your answer was not right\n\n"
            "  'Too late!'  – you did not respond in time\n\n"
            "You will also be shown the correct position of the house."
        ),
        footer="Slide 4 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Learning repetitions",
        body=(
            "Each house will be shown multiple times.\n\n"
            "The first time you will not yet know the correct position –\n"
            "this is normal. Use the feedback to learn.\n\n"
            "With each repetition it should become easier\n"
            "to recognise the correct position."
        ),
        footer="Slide 5 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Control task",
        body=(
            "There is also a control task in between.\n\n"
            "You will see the same type of image and answer the question:\n\n"
            "  'Is the house on the right side of the image?'\n\n"
            "Again: ARROW LEFT = YES, ARROW RIGHT = NO.\n\n"
            "Just look at the image – no spatial memory required."
        ),
        footer="Slide 6 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Important notes",
        body=(
            "Try to remember the POSITION of each house on the map,\n"
            "not just what the house looks like.\n\n"
            "This task measures spatial memory –\n"
            "where exactly on the map is the house located?\n\n"
            "Respond as quickly and accurately as possible."
        ),
        footer="Slide 7 / 8   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Ready?",
        body=(
            "You are now ready to begin the task.\n\n"
            "As a reminder:\n"
            "  ARROW LEFT  <-  YES  (correct position)\n"
            "  ARROW RIGHT ->  NO   (wrong position)\n\n"
            "You have 2.5 seconds per image.\n\n"
            "Good luck!"
        ),
        footer="Slide 8 / 8   [SPACEBAR -> Start]",
        advance_key="space"
    )


def show_instructions_part2():
    """4 text slides for the AFC recognition test (English)."""
    show_text_slide(
        title="Memory test",
        body=(
            "You have completed all the learning blocks.\n\n"
            "A memory test follows now.\n\n"
            "You will see images with three different positions for the same house.\n"
            "Only one position was correct – which one was it?"
        ),
        footer="Slide 1 / 4   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Memory test – Your task",
        body=(
            "Select from the three shown positions\n"
            "the position you learned during the learning phase.\n\n"
            "Press:\n\n"
            "       1  →  left position\n"
            "       2  →  middle position\n"
            "       3  →  right position"
        ),
        footer="Slide 2 / 4   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Memory test – Notes",
        body=(
            "There is no time limit.\n\n"
            "Respond as accurately as possible.\n\n"
            "If you are unsure, guess –\n"
            "do not leave any image unanswered."
        ),
        footer="Slide 3 / 4   [SPACEBAR -> continue]"
    )
    show_text_slide(
        title="Memory test – Ready?",
        body=(
            "The memory test is about to begin.\n\n"
            "As a reminder:\n\n"
            "       1  →  left position\n"
            "       2  →  middle position\n"
            "       3  →  right position\n\n"
            "Good luck!"
        ),
        footer="Slide 4 / 4   [SPACEBAR -> Start]",
        advance_key="space"
    )


# ── Trial runners ──────────────────────────────────────────────────────────────

def run_learning_trial(img_path, phase="learning", block=1, rep=1,
                       trial_idx=1, all_pairs=None):
    """
    Phase 1  (TRIAL_DUR = 2.5 s):
        Map image shown; key labels visible in behavioural mode.
        Response collected any time during the window; window always runs to end.
    Phase 2  (FEEDBACK_DUR = 2.0 s):
        "Correct!" / "Wrong!" / "Too late!" above the _k_ image.
    """
    meta  = parse_stim_name(img_path)
    fname = os.path.basename(img_path)

    # Phase 1 ────────────────────────────────────────────────────────────────
    main_img.setImage(img_path)
    main_img.draw()
    if not fmri_mode:
        key_label_left.draw()
        key_label_right.draw()
    win.flip()
    onset = global_clock.getTime()

    event.clearEvents()
    resp_clock = core.Clock()
    response = rt = None
    while resp_clock.getTime() < TRIAL_DUR:
        keys = event.getKeys(keyList=["left","right","escape"],
                             timeStamped=resp_clock)
        if keys:
            key, t = keys[0]
            if key == "escape":
                _csv_file.close(); win.close(); core.quit()
            response, rt = key, t
            break
        check_quit()

    # Wait out remainder of stimulus window
    elapsed = resp_clock.getTime()
    if elapsed < TRIAL_DUR:
        core.wait(TRIAL_DUR - elapsed)

    # Correctness
    is_k = "_k_" in fname
    resp_code = 1 if response == "left" else (2 if response == "right" else 0)
    if resp_code == 0:
        correct_flag = "timeout";   fb_label = "Too late!"
    elif (is_k and resp_code == 1) or (not is_k and resp_code == 2):
        correct_flag = "correct";   fb_label = "Correct!"
    else:
        correct_flag = "incorrect"; fb_label = "Wrong!"

    # Find _k_ feedback image
    correct_fb = img_path
    if all_pairs:
        for pair in all_pairs:
            if pair["correct"] == img_path or img_path in pair["foils"]:
                correct_fb = pair["correct"]; break

    # Phase 2 ────────────────────────────────────────────────────────────────
    feed_text.text = f"{fb_label}   The correct position is:"
    feed_img.setImage(correct_fb)
    feed_text.draw(); feed_img.draw()
    win.flip()
    core.wait(FEEDBACK_DUR)
    check_quit()

    write_row(phase=phase, block=block, rep=rep, trial=trial_idx,
              stimulus=fname, stim_type=meta["stim_type"],
              direction=meta["direction"], side=meta["side"],
              response_key=response, correct=correct_flag,
              rt=round(rt,4) if rt else "", onset_time=round(onset,4))


def run_control_trial(img_path, phase="control", block=1, rep=1, trial_idx=1):
    """
    Phase 1  (TRIAL_DUR = 2.5 s):
        Image + "Is the house on the right side?" above + key labels.
        Response collected any time; window always runs to end.
    Phase 2  (FEEDBACK_DUR = 2.0 s):
        "Correct!" / "Wrong!" / "Too late!" above same image with answer text.
    """
    meta  = parse_stim_name(img_path)
    fname = os.path.basename(img_path)

    # Phase 1 ────────────────────────────────────────────────────────────────
    feed_text.text = "Is the house on the right side?"
    feed_img.setImage(img_path)
    feed_text.draw(); feed_img.draw()
    if not fmri_mode:
        key_label_left.draw()
        key_label_right.draw()
    win.flip()
    onset = global_clock.getTime()

    event.clearEvents()
    resp_clock = core.Clock()
    response = rt = None
    while resp_clock.getTime() < TRIAL_DUR:
        keys = event.getKeys(keyList=["left","right","escape"],
                             timeStamped=resp_clock)
        if keys:
            key, t = keys[0]
            if key == "escape":
                _csv_file.close(); win.close(); core.quit()
            response, rt = key, t
            break
        check_quit()

    elapsed = resp_clock.getTime()
    if elapsed < TRIAL_DUR:
        core.wait(TRIAL_DUR - elapsed)

    is_right  = meta["side"] == "right"
    resp_code = 1 if response == "left" else (2 if response == "right" else 0)
    fb_answer = ("The house is on the right side."
                 if is_right else "The house is not on the right side.")
    if resp_code == 0:
        correct_flag = "timeout";   fb_label = "Too late!"
    elif (is_right and resp_code == 1) or (not is_right and resp_code == 2):
        correct_flag = "correct";   fb_label = "Correct!"
    else:
        correct_flag = "incorrect"; fb_label = "Wrong!"

    # Phase 2 ────────────────────────────────────────────────────────────────
    feed_text.text = f"{fb_label}   {fb_answer}"
    feed_text.draw(); feed_img.draw()
    win.flip()
    core.wait(FEEDBACK_DUR)
    check_quit()

    write_row(phase=phase, block=block, rep=rep, trial=trial_idx,
              stimulus=fname, stim_type=meta["stim_type"],
              direction=meta["direction"], side=meta["side"],
              response_key=response, correct=correct_flag,
              rt=round(rt,4) if rt else "", onset_time=round(onset,4))


def run_afc_trial(img_path, trial_idx=1):
    """3-AFC: composite image, keys 1/2/3, no time limit."""
    fname = os.path.basename(img_path)
    event.clearEvents()
    afc_img.setImage(img_path); afc_img.draw(); win.flip()
    onset = global_clock.getTime()
    keys  = event.waitKeys(keyList=["1","2","3","escape"])
    rt    = global_clock.getTime() - onset
    if "escape" in keys:
        _csv_file.close(); win.close(); core.quit()
    write_row(phase="AFC", trial=trial_idx, stimulus=fname,
              response_key=keys[0], rt=round(rt,4), onset_time=round(onset,4))

# ── Block runners ──────────────────────────────────────────────────────────────

def run_learning_block(block_dir, block_num, n_reps=4):
    files = get_stimuli(block_dir)
    pairs = pair_stimuli(files)

    random.shuffle(pairs)
    ups   = [p for p in pairs if p["meta"]["direction"] == "up"]
    downs = [p for p in pairs if p["meta"]["direction"] == "down"]
    interleaved = []
    for u, d in zip(ups, downs):
        interleaved += [u, d]
    interleaved += ups[len(downs):] + downs[len(ups):]
    pairs = interleaved

    stim_list = []
    for pair in pairs:
        stim_list.append(pair["correct"])
        stim_list.extend(pair["foils"])

    for rep in range(1, n_reps + 1):
        shuffled = shuffle_no_repeat(stim_list,
                                     key_fn=lambda f: parse_stim_name(f)["house"])
        for t_idx, img in enumerate(shuffled, 1):
            run_learning_trial(img, phase=f"learning-{block_num}",
                               block=block_num, rep=rep,
                               trial_idx=t_idx, all_pairs=pairs)
        show_fixation(FIX_DUR)


def run_control_block(block_dir, block_num, n_reps=4):
    stim_list = get_stimuli(block_dir)
    for rep in range(1, n_reps + 1):
        shuffled = shuffle_no_repeat(stim_list,
                                     key_fn=lambda f: parse_stim_name(f)["house"])
        for t_idx, img in enumerate(shuffled, 1):
            run_control_trial(img, phase=f"control-{block_num}",
                              block=block_num, rep=rep, trial_idx=t_idx)
        show_fixation(FIX_DUR)

# ── Main experiment ────────────────────────────────────────────────────────────

# 00  Instructions Part 1
show_instructions_part1()

# 01  Learning Block 1
run_learning_block(STIM_LEARN_DIRS[0], block_num=1)

# 02  Control Block 1
run_control_block(STIM_CTRL_DIRS[0], block_num=1)

# 03  Learning Block 2
run_learning_block(STIM_LEARN_DIRS[1], block_num=2)

# 04  Learning Block 3
run_learning_block(STIM_LEARN_DIRS[2], block_num=3)

# 05  Control Block 2
run_control_block(STIM_CTRL_DIRS[1], block_num=2)

# 06  Learning Block 4
run_learning_block(STIM_LEARN_DIRS[3], block_num=4)

# 07  Instructions Part 2 (AFC)
show_instructions_part2()

# 08  AFC Test
afc_files = get_stimuli(STIM_AFC_DIR)
random.shuffle(afc_files)
for t_idx, img in enumerate(afc_files, 1):
    run_afc_trial(img, trial_idx=t_idx)

# End screen
visual.TextStim(win, text="The task is complete.\nThank you!",
                color="white", height=60, wrapWidth=1100).draw()
win.flip()
event.waitKeys(keyList=["space","return","escape"])

_csv_file.close(); win.close(); core.quit()
