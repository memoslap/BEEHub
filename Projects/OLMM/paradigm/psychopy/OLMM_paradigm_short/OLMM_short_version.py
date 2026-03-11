#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OLMM – Short Version (PsychoPy)
=================================
Object-Location Memory Mapping – short demo version.

Experiment structure
---------------------
00  Instructions Part 1     Folie1–8    (advance with SPACE)
01  Learning Phase           2 blocks × 2 repetitions
02  Instructions Part 2     Folie9–12   (advance with SPACE)
03  AFC Test                 3-AFC, unlimited response time

File naming
-----------
  hH_pP_TYPE_DIRECTION[_qN]_SIDE.jpg
    TYPE : k = correct position  |  i = foil position
    DIRECTION : up | down
    SIDE      : left | right

Button mapping
--------------
  Learning / Control : LEFT  = Ja  (korrekte Position / Haus rechts)
                       RIGHT = Nein (falsche Position / Haus nicht rechts)
  AFC                : 1 / 2 / 3

Trial timing
------------
  Phase 1  2.5 s  Stimulus shown; response accepted any time during this window.
                  Key labels shown below image (behavioural mode only).
  Phase 2  2.0 s  Feedback: "Richtig!" / "Falsch!" / "Zu spät!" above the
                  correct-position (_k_) image.
"""

import os, random, datetime, csv, glob
from psychopy import visual, core, event, gui

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts): return os.path.join(_HERE, *parts)

STIM_LEARN_DIR = _p("Stimuli", "learning")
STIM_AFC_DIR   = _p("Stimuli", "AFC")
STIM_INSTR_DIR = _p("Stimuli", "instr")
DATA_DIR       = _p("data")

# ── Timing (seconds) ───────────────────────────────────────────────────────────
TRIAL_DUR    = 2.500   # stimulus + response window
FEEDBACK_DUR = 2.000   # correct-position image
FIX_DUR      = 4.500   # inter-block fixation (fMRI)

# ── Experiment dialog ──────────────────────────────────────────────────────────
exp_info = {"Participant": "", "Session": "1", "fMRI mode": False}
dlg = gui.DlgFromDict(exp_info, title="OLMM Short", sortKeys=False)
if not dlg.OK: core.quit()

participant = exp_info["Participant"]
session     = exp_info["Session"]
fmri_mode   = exp_info["fMRI mode"]

os.makedirs(DATA_DIR, exist_ok=True)
date_str   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data_fname = _p("data", f"{participant}_ses{session}_{date_str}_OLMM_short.csv")

# ── Window & clock ─────────────────────────────────────────────────────────────
win = visual.Window(size=(1280, 720), fullscr=True,
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

key_label_left  = visual.TextStim(win, text="<- Ja",   color="white", height=40,
                                  pos=(-340,-490), wrapWidth=600)
key_label_right = visual.TextStim(win, text="Nein ->", color="white", height=40,
                                  pos=( 340,-490), wrapWidth=600)

# ── Data writer ────────────────────────────────────────────────────────────────
_csv_file   = open(data_fname, "w", newline="", encoding="utf-8")
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow(["participant","session",
                      "phase","block","rep","trial",
                      "stimulus","stim_type","direction","side",
                      "response_key","correct","rt","onset_time"])

def write_row(**kw):
    _csv_writer.writerow([participant, session,
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

# ── Trial runners ──────────────────────────────────────────────────────────────

def run_learning_trial(img_path, phase="learning", block=1, rep=1,
                       trial_idx=1, all_pairs=None):
    """
    Phase 1  (2.5 s):  Map image + key labels.  Response collected within window.
    Phase 2  (2.0 s):  "Richtig!" / "Falsch!" / "Zu spät!" above the _k_ image.
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

    # Wait out the rest of the stimulus window
    elapsed = resp_clock.getTime()
    if elapsed < TRIAL_DUR:
        core.wait(TRIAL_DUR - elapsed)

    # Correctness
    is_k = "_k_" in fname
    resp_code = 1 if response == "left" else (2 if response == "right" else 0)
    if resp_code == 0:
        correct_flag = "timeout";   fb_label = "Zu sp\u00e4t!"
    elif (is_k and resp_code == 1) or (not is_k and resp_code == 2):
        correct_flag = "correct";   fb_label = "Richtig!"
    else:
        correct_flag = "incorrect"; fb_label = "Falsch!"

    # Find _k_ image for feedback
    correct_fb = img_path
    if all_pairs:
        for pair in all_pairs:
            if pair["correct"] == img_path or img_path in pair["foils"]:
                correct_fb = pair["correct"]; break

    # Phase 2 ────────────────────────────────────────────────────────────────
    feed_text.text = f"{fb_label}   Die korrekte Position ist:"
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
    Phase 1  (2.5 s):  Image + question above + key labels.
    Phase 2  (2.0 s):  "Richtig!" / "Falsch!" / "Zu spät!" above same image
                       with correct-answer text.
    """
    meta  = parse_stim_name(img_path)
    fname = os.path.basename(img_path)

    # Phase 1 ────────────────────────────────────────────────────────────────
    feed_text.text = "Ist das Haus auf der rechten Seite?"
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
    fb_answer = ("Das Haus ist auf der rechten Seite."
                 if is_right else "Das Haus ist nicht auf der rechten Seite.")
    if resp_code == 0:
        correct_flag = "timeout";   fb_label = "Zu sp\u00e4t!"
    elif (is_right and resp_code == 1) or (not is_right and resp_code == 2):
        correct_flag = "correct";   fb_label = "Richtig!"
    else:
        correct_flag = "incorrect"; fb_label = "Falsch!"

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

def run_learning_block(block_dir, block_num, n_reps=2):
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

# ── Main experiment ────────────────────────────────────────────────────────────

# 00 Instructions
show_instructions([_p(STIM_INSTR_DIR, f"Folie{i}.JPG") for i in range(1,9)])

# 01 Learning (2 blocks, 2 reps each)
run_learning_block(STIM_LEARN_DIR, block_num=1, n_reps=2)
run_learning_block(STIM_LEARN_DIR, block_num=2, n_reps=2)

# 02 AFC instructions
show_instructions([_p(STIM_INSTR_DIR, f"Folie{i}.JPG") for i in range(9,13)])

# 03 AFC
afc_files = get_stimuli(STIM_AFC_DIR)
random.shuffle(afc_files)
for t_idx, img in enumerate(afc_files, 1):
    run_afc_trial(img, trial_idx=t_idx)

# End
visual.TextStim(win, text="Die Aufgabe ist beendet.\nVielen Dank!",
                color="white", height=60, wrapWidth=1100).draw()
win.flip()
event.waitKeys(keyList=["space","return","escape"])

_csv_file.close(); win.close(); core.quit()
