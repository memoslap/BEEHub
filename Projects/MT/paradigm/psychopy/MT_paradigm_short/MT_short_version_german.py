#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MT_short.py — compact re-implementation of the MT mouse-tracking go/no-go task.

Source of truth: Projects/MT/paradigm/psychopy/go_nogo_dm.py
Block manifest:  Projects/MT/paradigm/psychopy/block_sequence.xlsx

This is a SHORT version in the sense of "one readable file instead of 2958 lines
of Builder output". It is NOT a simplified paradigm: every timing, geometry and
scoring rule below is taken from go_nogo_dm.py and is annotated with the line it
came from. Where this file and go_nogo_dm.py disagree, go_nogo_dm.py wins.

Fixes relative to the previous MT_short.py, all of which changed the paradigm:

  1. THRESHOLD POSITION. Was: stimulus appeared when the cursor came within 60 px
     of the response box at (200,300) — i.e. after the movement was over. Now:
     threshold_y = start_y + 100 = -300, inside a 300 px corridor (go_nogo_dm.py
     1594-1595, 1718-1721). This is the dynamic start; without it the paradigm
     measures nothing it was designed to measure.
  2. START HOLD. Was: `while global_clock.getTime() - mouseClock.getTime() < 0.5`,
     which compares a session clock against one just reset, so the loop never ran
     after the first half second. Now: a real hold whose timer resets whenever the
     cursor leaves the box (1500-1512).
  3. STILLNESS. Was: distance between consecutive samples < 5 px, which accepts a
     240 px/s drift. Now: a 15-sample window (~250 ms) whose maximum displacement
     from the window start must stay under 5 px (2050-2064).
  4. HIT TEST. Was: a radius-60 circle. Now: the 100x100 rectangle the box
     actually is, matching the offline analysis box (471-478).
  5. TRAJECTORIES. Was: all three trajectory columns written as one scalar, so no
     mouse track was saved at all. Now: full JSON arrays under the same column
     names the analysis pipeline expects (mouse_resp.x/.y/.time).
  6. ITI. Was: random.uniform(0.5, 1.0). Now: random.choice over six discrete
     100 ms steps (513, 2437). Screen blanks and the cursor is hidden.

Output columns are a superset of the 15 the analysis uses, so files produced here
can go straight through code/convert_MT.py.
"""

import csv
import datetime
import json
import os
import random
from math import sqrt

from psychopy import core, event, gui, visual

# ── Parameters — every one traceable to go_nogo_dm.py ────────────────────────
WIN_SIZE            = (1536, 864)   # 409
BOX_SIZE            = 100           # 448: width=(100,100)[0]
START_POS           = (0, -400)     # 449
RESP_POS            = (200, 300)    # 474
THRESHOLD_OFFSET    = 100           # 1594: threshold_y = start_y + 100
CORRIDOR_WIDTH      = 300           # 1595
HOLD_DUR            = 0.5           # 1339
FIXATION_DUR        = 0.5           # 1410
MAX_WAIT_MOVEMENT   = 5.0           # 1601
STIM_DEADLINE       = 1.5           # 1878
STILL_WINDOW_N      = 15            # 2052: ~250 ms at 60 Hz
STILL_MAX_PX        = 5             # 2056
STILL_REQUIRED_S    = 0.5           # 2064
ITI_CHOICES         = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]   # 513
SAMPLE_INTERVAL     = 0.01          # 458: mouse_sampling_rate, 100 Hz target
REFRESH_HZ          = 60.0          # 2063: still_duration += 1/60

START_BLUE  = [-1.0, -1.0, 1.0]     # 451
BLACK       = [-1.0, -1.0, -1.0]    # 469
BOX_HALF    = BOX_SIZE / 2.0

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))


def _p(*parts):
    return os.path.join(_THIS_DIR, *parts)


def find_paradigm_file(name):
    """Locate a condition table.

    The script may live beside the .xlsx files in paradigm/psychopy/, or one
    level down in paradigm/psychopy/MT_paradigm_short/. Search this directory
    first, then up to three parents, and fail with a message that says where we
    looked rather than a pandas traceback.
    """
    tried = []
    d = _THIS_DIR
    for _ in range(4):
        cand = os.path.join(d, name)
        tried.append(cand)
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    raise SystemExit(
        f"\nERROR: could not find {name!r}.\n"
        "Looked in:\n  " + "\n  ".join(tried) +
        "\n\nThe condition tables (block_sequence.xlsx, go_nogo.xlsx,\n"
        "go_nogo_prac.xlsx, go_only.xlsx) live in paradigm/psychopy/.\n"
        "Put this script there, or in a subfolder directly beneath it.\n")


# ── Geometry helpers ─────────────────────────────────────────────────────────
def in_rect(pos, centre, half=BOX_HALF):
    """Rectangular containment — the box IS a rectangle. The offline analysis
    uses x in [150,250], y in [250,350], which this reproduces exactly."""
    return (abs(pos[0] - centre[0]) <= half) and (abs(pos[1] - centre[1]) <= half)


def window_is_still(positions):
    """go_nogo_dm.py 2053-2056: maximum displacement from the FIRST sample of the
    window, across the whole window — not the distance between consecutive
    samples. A steady slow drift must not count as stopped."""
    if len(positions) < STILL_WINDOW_N:
        return False
    x0, y0 = positions[0]
    return max(sqrt((x - x0) ** 2 + (y - y0) ** 2) for x, y in positions) < STILL_MAX_PX


# ── Block / trial construction ───────────────────────────────────────────────
def load_block_sequence():
    import pandas as pd
    df = pd.read_excel(find_paradigm_file("block_sequence.xlsx"))
    return [{"block_type": r["block_type"], "block_number": int(r["block_number"]),
             "trials_count": int(r["trials_count"]),
             "is_practice": int(r["is_practice"]),
             "trials_file": find_paradigm_file(str(r["trials_file"]))}
            for _, r in df.iterrows()]


def load_trials(path):
    import pandas as pd
    return pd.read_excel(path).to_dict("records")


def shuffle_no_adjacent_nogo(trials, tries=1000):
    """The preprint restricts transitions to go->go, go->nogo and nogo->go, i.e.
    no two consecutive no-go trials."""
    for _ in range(tries):
        s = list(trials)
        random.shuffle(s)
        idx = [i for i, t in enumerate(s) if t["trial_type"] == "nogo"]
        if all(idx[j + 1] - idx[j] >= 2 for j in range(len(idx) - 1)):
            return s
    return trials


# ── Load and validate the paradigm files FIRST ───────────────────────────────
# Everything below this point can open a window. Nothing above it does, so a
# missing condition table exits cleanly instead of stranding a fullscreen window
# on the experimenter's screen.
blocks = load_block_sequence()
TRIALS_BY_BLOCK = {b["block_number"]: load_trials(b["trials_file"]) for b in blocks}
for b in blocks:
    got = len(TRIALS_BY_BLOCK[b["block_number"]])
    if got != b["trials_count"]:
        raise SystemExit(
            f"\nERROR: block {b['block_number']} ({b['block_type']}) declares "
            f"trials_count={b['trials_count']} in block_sequence.xlsx, but "
            f"{os.path.basename(b['trials_file'])} holds {got} rows.\n"
            "Fix the tables before running; a mismatch here silently changes the "
            "design.\n")
print(f"Loaded {len(blocks)} blocks, "
      f"{sum(len(v) for v in TRIALS_BY_BLOCK.values())} trials total.")


# ── Session setup ────────────────────────────────────────────────────────────
exp_info = {"participant": "", "session": "1"}
if not gui.DlgFromDict(exp_info, title="MT Mouse-Tracking Go/No-Go", sortKeys=False).OK:
    core.quit()

date_str = datetime.datetime.now().strftime("%Y-%m-%d_%Hh%M.%S")
os.makedirs(_p("data"), exist_ok=True)
out_path = _p("data", f"{exp_info['participant']}{exp_info['session']}"
                      f"_go_nogo_dm_{date_str}.csv")

COLUMNS = [
    "block_number", "block_type", "is_practice", "trials_count", "trial_number",
    "digit", "trial_type", "correct_response",
    "mouse_resp.x", "mouse_resp.y", "mouse_resp.leftButton",
    "mouse_resp.midButton", "mouse_resp.rightButton", "mouse_resp.time",
    "click_pos_x", "click_pos_y", "iti_duration",
    "hold_complete", "threshold_crossed", "timeout_occurred",
    "response_made", "movement_continued", "movement_stopped", "correct", "rt",
    "participant", "session", "date",
]

_fh = open(out_path, "w", newline="", encoding="utf-8-sig")
_writer = csv.DictWriter(_fh, fieldnames=COLUMNS, extrasaction="ignore")
_writer.writeheader()


def save_row(row):
    _writer.writerow(row)
    _fh.flush()


# ── Window and stimuli ───────────────────────────────────────────────────────
win = visual.Window(size=WIN_SIZE, units="pix", color=[0, 0, 0],
                    fullscr=False, allowGUI=False)
kb = event.Mouse(win=win)

fixation = visual.TextStim(win, text="+", height=40, color="white", pos=(0, 0))

start_box = visual.Rect(win, width=BOX_SIZE, height=BOX_SIZE, pos=START_POS,
                        lineColor="black", fillColor=START_BLUE, lineWidth=1.0)
# 471-478: the response box is WHITE with a black outline, in every phase and on
# every trial type. It must NEVER be recoloured by trial type — the colour would
# cue the participant before the digit is read.
response_box = visual.Rect(win, width=BOX_SIZE, height=BOX_SIZE, pos=RESP_POS,
                           lineColor="black", fillColor="white", lineWidth=1.0)
digit_stim = visual.TextStim(win, text="", height=72, color="black",
                             font="Arial", pos=RESP_POS)          # 497-503
block_text = visual.TextStim(win, text="", height=30, color="white",
                             wrapWidth=1200, pos=(0, 0))


def wait_space():
    event.clearEvents()
    while "space" not in event.getKeys(keyList=["space", "escape"]):
        if event.getKeys(keyList=["escape"]):
            _fh.close()
            win.close()
            core.quit()
        core.wait(0.01)


# ── Trial phases ─────────────────────────────────────────────────────────────
def phase_fixation():
    """0.5 s fixation cross (1410)."""
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DUR)


def phase_start_hold():
    """Cursor must rest inside the blue start box for 500 ms. The timer resets on
    entry and whenever the cursor leaves (1500-1512). Returns hold_complete."""
    start_box.fillColor = START_BLUE
    hold_timer = core.Clock()
    inside = False
    while True:
        pos = kb.getPos()
        now_inside = in_rect(pos, START_POS)
        if now_inside:
            if not inside:              # just entered — start counting
                hold_timer.reset()
                inside = True
            if hold_timer.getTime() >= HOLD_DUR:
                start_box.fillColor = BLACK      # 1508
                start_box.draw()
                win.flip()
                return True
        else:
            inside = False              # left the box — hold is void
        start_box.draw()
        fixation.draw()
        win.flip()
        if event.getKeys(keyList=["escape"]):
            _fh.close(); win.close(); core.quit()


def phase_threshold():
    """The dynamic start. The white response box is already on screen but EMPTY;
    the digit appears only once the cursor crosses threshold_y while inside the
    corridor (1594-1595, 1718-1721). Returns (crossed, timeout)."""
    threshold_y = START_POS[1] + THRESHOLD_OFFSET        # -300
    timer = core.Clock()
    movement_initiated = False
    while True:
        pos = kb.getPos()
        if pos[1] > START_POS[1]:
            movement_initiated = True
        in_corridor = abs(pos[0] - START_POS[0]) <= CORRIDOR_WIDTH / 2.0
        if movement_initiated and in_corridor and pos[1] >= threshold_y:
            return True, False
        if timer.getTime() >= MAX_WAIT_MOVEMENT and not movement_initiated:
            return False, True                            # 1601
        start_box.draw()
        response_box.draw()
        win.flip()
        if event.getKeys(keyList=["escape"]):
            _fh.close(); win.close(); core.quit()


def phase_stimulus(digit, trial_type):
    """Digit visible, 1.5 s deadline. Go: a left click inside the box.
    No-go: 500 ms of sustained stillness. Records the full trajectory."""
    digit_stim.setText(str(digit))
    trial_clock = core.Clock()
    tx, ty, tt, tl, tm, tr = [], [], [], [], [], []
    recent = []
    still_duration = 0.0
    response_made = movement_continued = movement_stopped = False
    correct = False
    rt = None
    click_x = click_y = None
    last_sample = -1.0

    while True:
        t = trial_clock.getTime()
        pos = kb.getPos()
        buttons = kb.getPressed()

        # Sample at the configured rate (458). The loop is frame-locked by
        # win.flip(), so in practice this yields one sample per refresh.
        if t - last_sample >= SAMPLE_INTERVAL:
            tx.append(pos[0]); ty.append(pos[1]); tt.append(t)
            tl.append(int(buttons[0])); tm.append(int(buttons[1]))
            tr.append(int(buttons[2]))
            last_sample = t

        # Response: ANY left click inside the box ends the trial. On a no-go
        # trial that is by definition an error (2038-2041).
        if not response_made and buttons[0] > 0 and in_rect(pos, RESP_POS):
            response_made = True
            rt = t
            click_x, click_y = pos[0], pos[1]
            correct = (trial_type == "go")
            break

        # Stillness over a 15-sample window (2050-2064).
        recent.append(pos)
        if len(recent) > STILL_WINDOW_N:
            recent.pop(0)
        if window_is_still(recent):
            movement_stopped = True
            still_duration += 1.0 / REFRESH_HZ
            if still_duration >= STILL_REQUIRED_S and trial_type == "nogo":
                correct = True
                rt = t
                break
        else:
            still_duration = 0.0
            movement_stopped = False
            movement_continued = True

        if t >= STIM_DEADLINE:
            rt = STIM_DEADLINE
            if trial_type == "nogo" and not movement_continued:
                correct = True                             # 2077-2079
            break

        start_box.draw()
        response_box.draw()
        digit_stim.draw()
        win.flip()
        if event.getKeys(keyList=["escape"]):
            _fh.close(); win.close(); core.quit()

    return {
        "x": tx, "y": ty, "t": tt, "lb": tl, "mb": tm, "rb": tr,
        "response_made": response_made, "movement_continued": movement_continued,
        "movement_stopped": movement_stopped, "correct": correct, "rt": rt,
        "click_x": click_x, "click_y": click_y,
    }


def phase_iti():
    """Blank screen, cursor hidden, duration drawn from six discrete steps."""
    dur = random.choice(ITI_CHOICES)                      # 513, 2437
    win.mouseVisible = False
    win.flip()                                            # clear the screen
    core.wait(dur)
    win.mouseVisible = True
    return dur


# ── Main loop ────────────────────────────────────────────────────────────────
block_text.setText(
    "Willkommen!\n\nBewegen Sie die Maus in das blaue Feld und halten Sie sie dort.\n"
    "Bewegen Sie den Cursor dann nach oben. Sobald eine Ziffer erscheint:\n\n"
    "Go-Ziffern (2,3,4,6,7,8): in die weiße Box klicken.\n"
    "No-Go-Ziffern (1,9): die Bewegung anhalten und nicht klicken.\n\n"
    "Leertaste zum Starten.")
block_text.draw()
win.flip()
wait_space()

for bi, blk in enumerate(blocks):
    trials = list(TRIALS_BY_BLOCK[blk["block_number"]])
    if blk["block_type"] in ("go_nogo", "go_nogo_prac"):
        trials = shuffle_no_adjacent_nogo(trials)
    else:
        random.shuffle(trials)

    block_text.setText(f"Block {blk['block_number']} von {len(blocks)}\n\n"
                       "Leertaste, um fortzufahren.")
    block_text.draw()
    win.flip()
    wait_space()

    for ti, tr in enumerate(trials, start=1):
        digit = int(tr["digit"])
        trial_type = str(tr["trial_type"])

        phase_fixation()
        hold_complete = phase_start_hold()
        crossed, timeout = phase_threshold()

        if timeout:
            # No movement within 5 s: no stimulus phase, row still recorded.
            save_row({"block_number": blk["block_number"], "block_type": blk["block_type"],
                      "is_practice": blk["is_practice"], "trials_count": blk["trials_count"],
                      "trial_number": ti, "digit": digit, "trial_type": trial_type,
                      "correct_response": tr.get("correct_response", ""),
                      "hold_complete": hold_complete, "threshold_crossed": False,
                      "timeout_occurred": True, "iti_duration": phase_iti(),
                      "participant": exp_info["participant"],
                      "session": exp_info["session"], "date": date_str})
            continue

        r = phase_stimulus(digit, trial_type)
        iti = phase_iti()

        save_row({
            "block_number": blk["block_number"], "block_type": blk["block_type"],
            "is_practice": blk["is_practice"], "trials_count": blk["trials_count"],
            "trial_number": ti, "digit": digit, "trial_type": trial_type,
            "correct_response": tr.get("correct_response", ""),
            # JSON arrays, exactly the encoding convert_MT.py expects.
            "mouse_resp.x": json.dumps(r["x"]), "mouse_resp.y": json.dumps(r["y"]),
            "mouse_resp.time": json.dumps(r["t"]),
            "mouse_resp.leftButton": json.dumps(r["lb"]),
            "mouse_resp.midButton": json.dumps(r["mb"]),
            "mouse_resp.rightButton": json.dumps(r["rb"]),
            "click_pos_x": "" if r["click_x"] is None else r["click_x"],
            "click_pos_y": "" if r["click_y"] is None else r["click_y"],
            "iti_duration": iti,
            "hold_complete": hold_complete, "threshold_crossed": True,
            "timeout_occurred": False,
            "response_made": r["response_made"],
            "movement_continued": r["movement_continued"],
            "movement_stopped": r["movement_stopped"],
            "correct": r["correct"], "rt": r["rt"],
            "participant": exp_info["participant"],
            "session": exp_info["session"], "date": date_str,
        })

block_text.setText("Das Experiment ist abgeschlossen.\nVielen Dank für Ihre Teilnahme!")
block_text.draw()
win.flip()
core.wait(3.0)
_fh.close()
win.close()
core.quit()
