#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BEEHub PsychoPy paradigm template
=================================
Derived from the hand-written OLM Set B implementation, which is the house
reference. Everything below the CONFIG fence is paradigm-agnostic machinery and
has been preserved verbatim — it already works. Do not rewrite it.

TO CONVERT A NEW PARADIGM:
  1. Copy this file to the target psychopy folder.
  2. Edit ONLY the CONFIG block below.
  3. Run ./Agent/03_Paradigm/check_runs.sh <file>

The file as shipped is a working OLM Set B experiment, so it compiles and runs
before you touch it — you are editing values, not authoring an experiment.

Expected folder layout (relative to this script):
    Stimuli/instr/            instruction slide images (Folie*.JPG), optional
    Stimuli/learning/blockN/  1 _k_ + its same-house _i_ foils per house
    Stimuli/control/blockN/
    Stimuli/AFC/
    data/                     created automatically

COORDINATE SYSTEM — the #1 cause of "everything is in the corner":
  PsychoPy with units="pix" puts the origin (0,0) at the SCREEN CENTRE, with y
  growing UPWARD. pygame puts (0,0) at the TOP-LEFT with y growing DOWNWARD.
  If you are porting from pygame (or from any layout that assumes a top-left
  origin), convert EVERY position with _px() — see the helper below. Passing a
  raw pygame coordinate silently renders off-centre; nothing errors.

TEXT ALIGNMENT — do not use alignHoriz= / alignVert=:
  They are deprecated and raise at runtime in current PsychoPy
  ("`anchor_y` must be either top, bottom, center, or baseline").
  Use alignText= (justification inside the box) and anchorHoriz= / anchorVert=
  (which point of the box sits at pos). See _text_at() below.

STIMULUS FOLDER REQUIREMENT — read this before blaming the code:
  pair_stimuli() groups each _k_ file with _i_ files of the SAME house. A _k_
  with no same-house _i_ partner produces an empty foil list, so those images
  are NEVER SHOWN and the block silently runs short. This does not crash.
  Verify with ./Agent/03_Paradigm/probe.sh (section 5b) before converting.
"""

import os, random, datetime, csv, glob
from psychopy import visual, core, event, gui

# ═══════════════════════════════════════════════════════════════════════════════
# ▼▼▼  PARADIGM CONFIG — THIS IS THE ONLY BLOCK YOU EDIT  ▼▼▼
# ═══════════════════════════════════════════════════════════════════════════════

# ── Identity ───────────────────────────────────────────────────────────────────
PARADIGM_ID   = "OLMM"           # short name shown in the dialog title
SET_LABEL     = "B"              # written to every CSV row
LANGUAGE      = "english"        # english | german
DATA_SUFFIX   = "OLMM_B"         # goes into the data filename

# ── Structure ──────────────────────────────────────────────────────────────────
N_LEARNING_BLOCKS = 4
N_CONTROL_BLOCKS  = 2
N_REPS            = 4            # repetitions per block (LS1..LS4 in the logs)

# Block order. Each entry: ("learning"|"control", block_number).
# Taken from the paradigm's own .sce / probe report — do NOT assume it matches
# another SET. Set BLOCK_ORDER_RANDOMISE=True to shuffle at runtime instead.
BLOCK_SEQUENCE = [
    ("learning", 1),
    ("control",  1),
    ("learning", 2),
    ("learning", 3),
    ("control",  2),
    ("learning", 4),
]
BLOCK_ORDER_RANDOMISE = False    # True => shuffle, keeping controls non-adjacent

# ── Timing (SECONDS — convert from the .sce milliseconds) ─────────────────────
TRIAL_DUR    = 2.500   # stimulus + response window
FEEDBACK_DUR = 2.000   # correct-position feedback
FIX_DUR      = 4.500   # inter-block fixation

# ── Response keys ──────────────────────────────────────────────────────────────
# Preserve the SEMANTICS of the original device mapping (see probe report §3),
# not the hardware codes. Internal code 1 = "yes/correct", 2 = "no/wrong".
KEY_YES      = "left"
KEY_NO       = "right"
KEY_AFC      = ["1", "2", "3"]
KEY_QUIT     = "escape"
LABEL_YES    = "<- Yes"
LABEL_NO     = "No ->"

# ── Display geometry (PIXELS — house style requires explicit sizes) ───────────
WIN_SIZE      = (1280, 720)
BG_COLOR      = (0, 0, 0)        # rgb255
MAIN_IMG_SIZE = (1024, 787);  MAIN_IMG_POS = (0, -70)
AFC_IMG_SIZE  = (1224, 987);  AFC_IMG_POS  = (0, 0)
INSTR_IMG_SIZE = (1280, 720)

# ── Instruction slides ─────────────────────────────────────────────────────────
# Shown before the learning phase and before the AFC test. Edit the text; the
# rendering is handled by show_text_slide() below.
INSTRUCTIONS_PART1 = [
        {"title": 'Welcome – OLMM Study',
         "body": 'Thank you for participating!\n\nIn this task you will learn where houses are located on a map.\n\nYour task is to remember the exact position\nof each house.',
         "footer": 'Slide 1 / 8   [SPACEBAR -> continue]'},
        {"title": 'What you will see',
         "body": 'You will see an image showing a house on a map.\n\nThe house is either in the CORRECT position\nor in a WRONG position.\n\nYour task: decide whether the house\nis in the correct location.',
         "footer": 'Slide 2 / 8   [SPACEBAR -> continue]'},
        {"title": 'Keys',
         "body": 'Press:\n\n  ARROW LEFT   <-  YES, that is the correct position\n\n  ARROW RIGHT  ->  NO,  that is not the correct position\n\nYou have 2.5 seconds per image.\nRespond as quickly and accurately as possible.',
         "footer": 'Slide 3 / 8   [SPACEBAR -> continue]'},
        {"title": 'Feedback',
         "body": "After each response you will see feedback:\n\n  'Correct!'   – your answer was right\n\n  'Wrong!'     – your answer was not right\n\n  'Too late!'  – you did not respond in time\n\nYou will also be shown the correct position of the house.",
         "footer": 'Slide 4 / 8   [SPACEBAR -> continue]'},
        {"title": 'Learning repetitions',
         "body": 'Each house will be shown multiple times.\n\nThe first time you will not yet know the correct position –\nthis is normal. Use the feedback to learn.\n\nWith each repetition it should become easier\nto recognise the correct position.',
         "footer": 'Slide 5 / 8   [SPACEBAR -> continue]'},
        {"title": 'Control task',
         "body": "There is also a control task in between.\n\nYou will see the same type of image and answer the question:\n\n  'Is the house on the right side of the image?'\n\nAgain: ARROW LEFT = YES, ARROW RIGHT = NO.\n\nJust look at the image – no spatial memory required.",
         "footer": 'Slide 6 / 8   [SPACEBAR -> continue]'},
        {"title": 'Important notes',
         "body": 'Try to remember the POSITION of each house on the map,\nnot just what the house looks like.\n\nThis task measures spatial memory –\nwhere exactly on the map is the house located?\n\nRespond as quickly and accurately as possible.',
         "footer": 'Slide 7 / 8   [SPACEBAR -> continue]'},
        {"title": 'Ready?',
         "body": 'You are now ready to begin the task.\n\nAs a reminder:\n  ARROW LEFT  <-  YES  (correct position)\n  ARROW RIGHT ->  NO   (wrong position)\n\nYou have 2.5 seconds per image.\n\nGood luck!',
         "footer": 'Slide 8 / 8   [SPACEBAR -> Start]'},
]

INSTRUCTIONS_PART2 = [
        {"title": 'Memory test',
         "body": 'You have completed all the learning blocks.\n\nA memory test follows now.\n\nYou will see images with three different positions for the same house.\nOnly one position was correct – which one was it?',
         "footer": 'Slide 1 / 4   [SPACEBAR -> continue]'},
        {"title": 'Memory test – Your task',
         "body": 'Select from the three shown positions\nthe position you learned during the learning phase.\n\nPress:\n\n       1  →  left position\n       2  →  middle position\n       3  →  right position',
         "footer": 'Slide 2 / 4   [SPACEBAR -> continue]'},
        {"title": 'Memory test – Notes',
         "body": 'There is no time limit.\n\nRespond as accurately as possible.\n\nIf you are unsure, guess –\ndo not leave any image unanswered.',
         "footer": 'Slide 3 / 4   [SPACEBAR -> continue]'},
        {"title": 'Memory test – Ready?',
         "body": 'The memory test is about to begin.\n\nAs a reminder:\n\n       1  →  left position\n       2  →  middle position\n       3  →  right position\n\nGood luck!',
         "footer": 'Slide 4 / 4   [SPACEBAR -> Start]'},
]

# Optional: image-based instructions instead of text slides. Point at files in
# Stimuli/instr/ (e.g. PowerPoint exports Folie1.JPG..). Empty list = text only.
INSTRUCTION_IMAGES_PART1 = []
INSTRUCTION_IMAGES_PART2 = []

# ═══════════════════════════════════════════════════════════════════════════════
# ▲▲▲  END PARADIGM CONFIG — do not edit below this line  ▲▲▲
# ═══════════════════════════════════════════════════════════════════════════════


# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts): return os.path.join(_HERE, *parts)

STIM_LEARN_DIRS = [_p("Stimuli","learning",f"block{i}") for i in range(1, N_LEARNING_BLOCKS+1)]
STIM_CTRL_DIRS  = [_p("Stimuli","control", f"block{i}") for i in range(1, N_CONTROL_BLOCKS+1)]
STIM_AFC_DIR    = _p("Stimuli","AFC")
STIM_INSTR_DIR  = _p("Stimuli","instr")
DATA_DIR        = _p("data")

# ── Experiment dialog ──────────────────────────────────────────────────────────
exp_info = {"Participant": "", "Session": "1", "fMRI mode": False}
dlg = gui.DlgFromDict(exp_info, title=f"{PARADIGM_ID} Set {SET_LABEL}", sortKeys=False)
if not dlg.OK: core.quit()

participant = exp_info["Participant"]
session     = exp_info["Session"]
fmri_mode   = exp_info["fMRI mode"]

os.makedirs(DATA_DIR, exist_ok=True)
date_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data_fname = _p("data", f"{participant}_ses{session}_{date_str}_{DATA_SUFFIX}.csv")

# ── Window & clock ─────────────────────────────────────────────────────────────
win = visual.Window(size=WIN_SIZE, fullscr=True,
                    color=BG_COLOR, colorSpace="rgb255",
                    units="pix", allowGUI=False)
global_clock = core.Clock()

# ═══════════════════════════════════════════════════════════════════════════════
# COORDINATE + TEXT HELPERS — use these, do not hand-roll positions
# ═══════════════════════════════════════════════════════════════════════════════
# PsychoPy units="pix": origin at SCREEN CENTRE, y grows UPWARD.
# pygame:               origin at TOP-LEFT,      y grows DOWNWARD.
#
# Native PsychoPy layout (like this template's own stimuli) uses centre-based
# coords directly — pos=(0, -70) means 70 px below centre. That is fine.
#
# But if you are PORTING a layout that assumes a top-left origin, convert every
# position with _px(). Symptom of forgetting: everything drifts to the right
# and/or vertically flipped, with no error message.

def _px(x, y):
    """Top-left-origin (y down) -> PsychoPy pix (centre origin, y up).

    Use for ported pygame/HTML layouts:
        rect.pos = _px(box_left + box_w / 2, box_top + box_h / 2)
    Do NOT use for coordinates that are already centre-based.
    """
    return (x - win.size[0] / 2.0, win.size[1] / 2.0 - y)


def _text_at(x, y, text, size=28, color="white", bold=False,
             wrap=None, align="center", top_left=False):
    """Draw text. Set top_left=True if (x, y) are pygame-style coordinates.

    NOTE the alignment API: alignText controls justification WITHIN the text
    box; anchorHoriz/anchorVert control which point of the box sits at pos.
    Never use the deprecated alignHoriz= / alignVert= — they raise at runtime.
    """
    ts = visual.TextStim(win, text=text, color=color, height=size, bold=bold,
                         units="pix", wrapWidth=wrap,
                         alignText=align, anchorHoriz=align, anchorVert="center")
    ts.pos = _px(x, y) if top_left else (x, y)
    ts.draw()
    return ts


# ── Visual objects ─────────────────────────────────────────────────────────────
fix_stim  = visual.TextStim(win, text="+", color="white", height=80, pos=(0,0))
feed_text = visual.TextStim(win, text="",  color="white", height=50, pos=(0,350),
                            wrapWidth=1100)
main_img  = visual.ImageStim(win, pos=MAIN_IMG_POS, size=MAIN_IMG_SIZE)
feed_img  = visual.ImageStim(win, pos=MAIN_IMG_POS, size=MAIN_IMG_SIZE)
afc_img   = visual.ImageStim(win, pos=AFC_IMG_POS,  size=AFC_IMG_SIZE)

key_label_left  = visual.TextStim(win, text=LABEL_YES, color="white", height=40,
                                  pos=(-340,-490), wrapWidth=600)
key_label_right = visual.TextStim(win, text=LABEL_NO,  color="white", height=40,
                                  pos=( 340,-490), wrapWidth=600)

# ── Data writer ────────────────────────────────────────────────────────────────
_csv_file   = open(data_fname, "w", newline="", encoding="utf-8")
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow(["participant","session","set",
                      "phase","block","rep","trial",
                      "stimulus","stim_type","direction","side",
                      "response_key","correct","rt","onset_time"])

def write_row(**kw):
    _csv_writer.writerow([participant, session, SET_LABEL,
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


def show_instructions_part1():
    """Config-driven: edit INSTRUCTIONS_PART1, not this function."""
    if INSTRUCTION_IMAGES_PART1:
        show_instructions([_p("Stimuli","instr",f) for f in INSTRUCTION_IMAGES_PART1])
    for s in INSTRUCTIONS_PART1:
        show_text_slide(title=s["title"], body=s["body"], footer=s["footer"])


def show_instructions_part2():
    """Config-driven: edit INSTRUCTIONS_PART2, not this function."""
    if INSTRUCTION_IMAGES_PART2:
        show_instructions([_p("Stimuli","instr",f) for f in INSTRUCTION_IMAGES_PART2])
    for s in INSTRUCTIONS_PART2:
        show_text_slide(title=s["title"], body=s["body"], footer=s["footer"])



# ── Main experiment ────────────────────────────────────────────────────────────
# Driven entirely by BLOCK_SEQUENCE in the CONFIG block above.

def _resolve_sequence():
    seq = list(BLOCK_SEQUENCE)
    if not BLOCK_ORDER_RANDOMISE:
        return seq
    for _ in range(500):                     # shuffle, keep controls non-adjacent
        random.shuffle(seq)
        if seq[0][0] == "control":
            continue
        if any(seq[i][0] == "control" and seq[i-1][0] == "control"
               for i in range(1, len(seq))):
            continue
        return seq
    return seq                                # fall back to the shuffled order

show_instructions_part1()

_sequence = _resolve_sequence()
print("Block order:", [f"{k}-{n}" for k, n in _sequence])

for _kind, _num in _sequence:
    if _kind == "learning":
        run_learning_block(STIM_LEARN_DIRS[_num-1], block_num=_num, n_reps=N_REPS)
    elif _kind == "control":
        run_control_block(STIM_CTRL_DIRS[_num-1], block_num=_num, n_reps=N_REPS)
    else:
        raise ValueError(f"unknown block kind in BLOCK_SEQUENCE: {_kind!r}")

show_instructions_part2()

# ── AFC test ───────────────────────────────────────────────────────────────────
afc_files = get_stimuli(STIM_AFC_DIR)
random.shuffle(afc_files)
for t_idx, img in enumerate(afc_files, 1):
    run_afc_trial(img, trial_idx=t_idx)

# ── End screen ─────────────────────────────────────────────────────────────────
visual.TextStim(win, text="The task is complete.\nThank you!",
                color="white", height=60, wrapWidth=1100).draw()
win.flip()
event.waitKeys(keyList=["space","return",KEY_QUIT])

_csv_file.close(); win.close(); core.quit()
