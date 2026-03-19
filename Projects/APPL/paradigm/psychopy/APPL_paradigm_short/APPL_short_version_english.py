#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APPL – Short Version (PsychoPy) [English]
=================================
Associative Picture-Pseudoword Learning – short/demo version.

Folder layout (relative to this script)
-----------------------------------------
Stimuli/
  bubbles/   hello.jpg  learning.jpg  control.jpg  bye.jpg
  learning/  PICTURE_*.jpg   (10 items)
  control/   PICTURE_*.jpg   (10 items)
  AFC/       PICTURE_*.jpg   (if present)

Experiment structure
---------------------
00  Instructions Part 1     instr_11–17.jpg  (key 1 to advance, key 2 on last)
01  Instructions Part 2     instr_21.jpg     (key 2 to advance)
02  Learning / control phase
      3 blocks  (2 learning + 1 control), control not first or last
      Each block: 4 learning stages × 10 trials
      Bubble screen before each block; fixation between stages
03  Instructions Part 3     instr_31–34.jpg  (key 1 / key 2 on last)
04  AFC Test                 keys 1/2/3, no time limit

Trial timing
------------
  Phase 1  2.5 s  Image (600×600) shown centre + pseudoword below (pos 0,−400).
                  Keys 1 (Ja) and 2 (Nein) accepted any time during the window.
                  Window always runs to full 2.5 s regardless of response time.
  Phase 2  2.0 s  Feedback text only (no image):
                      "Korrekt, das ist {correct_word}"
                      "Falsch, das ist {correct_word}"
                      "Zu spät, das ist {correct_word}"

Response mapping
----------------
  1 = Ja   (correct association / correct word shown)
  2 = Nein (incorrect association / foil shown)
  AFC: 1 / 2 / 3
"""

import os, random, datetime, csv, glob
from psychopy import visual, core, event, gui, logging

# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts): return os.path.join(_HERE, *parts)

STIM_DIR    = _p("Stimuli")
BUBBLES_DIR = _p("Stimuli", "bubbles")
LEARN_DIR   = _p("Stimuli", "learning")
CTRL_DIR    = _p("Stimuli", "control")
AFC_DIR     = _p("Stimuli", "AFC")
DATA_DIR    = _p("data")

# ── Timing ─────────────────────────────────────────────────────────────────────
STIM_DUR     = 2.500   # stimulus on-screen + response window
FEEDBACK_DUR = 2.000   # feedback text duration
FIX_DUR      = 4.500   # fixation / inter-block / bubble duration

# ── Response keys ──────────────────────────────────────────────────────────────
KEY_YES = '1'   # Ja  – correct word shown
KEY_NO  = '2'   # Nein – foil shown

# ── Experiment dialog ──────────────────────────────────────────────────────────
exp_info = {'participant': '', 'session': '001', 'fmri_mode': False}
dlg = gui.DlgFromDict(exp_info, title='APPL Short Version', sortKeys=False)
if not dlg.OK:
    core.quit()

participant = exp_info['participant']
session     = exp_info['session']
fmri_mode   = exp_info['fmri_mode']

os.makedirs(DATA_DIR, exist_ok=True)
date_str  = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
csv_fname = _p("data", f"{participant}_{session}_{date_str}_APPL_short.csv")
log_fname = _p("data", f"{participant}_{session}_{date_str}_APPL_short.log")

logging.console.setLevel(logging.WARNING)
logging.LogFile(log_fname, level=logging.EXP)

# ── Window & clock ─────────────────────────────────────────────────────────────
win = visual.Window(size=(1280, 720), fullscr=True,
                    color='black', units='pix', allowGUI=False)
global_clock = core.Clock()

# ── Visual objects ─────────────────────────────────────────────────────────────
fixation      = visual.TextStim(win, text='+', color='white', height=100)
feedback_text = visual.TextStim(win, text='',  color='white', height=60,
                                wrapWidth=1100)
pres_word     = visual.TextStim(win, text='',  color='white', height=100,
                                pos=(0, -400), wrapWidth=600)
pres_pic      = visual.ImageStim(win, size=(600, 600), pos=(0, 0))
info_pic      = visual.ImageStim(win, size=(600, 398), pos=(0, 0))
afc_pic       = visual.ImageStim(win, size=(1224, 987), pos=(0, 0))

# Key labels – shown in behavioural mode only
key_label_1 = visual.TextStim(win, text='1 = Yes',   color='white', height=40,
                               pos=(-340, -490))
key_label_2 = visual.TextStim(win, text='2 = No', color='white', height=40,
                               pos=( 340, -490))

# ── CSV writer ─────────────────────────────────────────────────────────────────
_csv_file   = open(csv_fname, 'w', newline='', encoding='utf-8')
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow(['participant', 'session',
                      'phase', 'block_run', 'block_num', 'learning_stage', 'trial',
                      'image', 'word', 'correct_word', 'condition',
                      'response', 'correct', 'rt', 'onset_time'])

def write_row(**kw):
    _csv_writer.writerow([participant, session,
        kw.get('phase',''),        kw.get('block_run',''),
        kw.get('block_num',''),    kw.get('learning_stage',''),
        kw.get('trial',''),        kw.get('image',''),
        kw.get('word',''),         kw.get('correct_word',''),
        kw.get('condition',''),    kw.get('response',''),
        kw.get('correct',''),      kw.get('rt',''),
        kw.get('onset_time','')])
    _csv_file.flush()

# ── Helpers ────────────────────────────────────────────────────────────────────
def check_quit():
    if event.getKeys(keyList=['escape']):
        _csv_file.close(); win.close(); core.quit()

def show_fixation(duration=FIX_DUR):
    fixation.draw(); win.flip()
    core.wait(duration); check_quit()

def show_bubble(img_path, duration=FIX_DUR):
    if os.path.isfile(img_path):
        info_pic.setImage(img_path); info_pic.draw()
    else:
        visual.TextStim(win, text=os.path.basename(img_path),
                        color='white', height=60).draw()
    win.flip(); core.wait(duration); check_quit()

def show_text_slide(title, body, footer, advance_key='space'):
    """Render a single instruction slide – black background, white text only."""
    # Title
    visual.TextStim(win, text=title, color='white', height=36,
                    bold=True, pos=(0, 280), wrapWidth=1100).draw()
    # Divider line
    visual.Line(win, start=(-540, 240), end=(540, 240),
                lineColor='white', lineWidth=1).draw()
    # Body
    visual.TextStim(win, text=body, color='white', height=28,
                    pos=(0, 20), wrapWidth=1050, alignText='left').draw()
    # Footer
    key_label = 'SPACEBAR' if advance_key == 'space' else f'Key {advance_key}'
    visual.TextStim(win, text=f"{footer}    [{key_label} -> continue]",
                    color='white', height=22,
                    pos=(0, -295), wrapWidth=1100).draw()
    win.flip()
    event.waitKeys(keyList=[advance_key, 'escape']); check_quit()


def show_instructions_part1():
    """7 slides explaining the learning task."""
    show_text_slide(
        title="Welcome – APPL Study",
        body=(
            "Thank you for participating!\n\n"
            "In this study you will learn pictures,\n"
            "each paired with an invented word.\n\n"
            "Your task is to remember\n"
            "which word belongs to which picture."
        ),
        footer="Slide 1 / 7"
    )
    show_text_slide(
        title="How the task works",
        body=(
            "You will see pictures on the screen one by one.\n\n"
            "Below each picture a word is shown.\n\n"
            "Your task:\n"
            "  Decide whether the displayed word is the\n"
            "  CORRECT word for that picture."
        ),
        footer="Slide 2 / 7"
    )
    show_text_slide(
        title="Keys",
        body=(
            "Press:\n\n"
            "       1  ->  YES, that is the correct word\n\n"
            "       2  ->  NO,  that is not the correct word\n\n"
            "You have 2.5 seconds to respond.\n"
            "Answer as quickly and accurately as possible."
        ),
        footer="Slide 3 / 7"
    )
    show_text_slide(
        title="Feedback",
        body=(
            "After each response you will receive feedback:\n\n"
            "  'Correct, it is [word]'   – your answer was right\n\n"
            "  'Wrong, it is [word]'     – your answer was wrong\n\n"
            "  'Too late, it is [word]'  – no response in time\n\n"
            "Use the feedback to learn the word."
        ),
        footer="Slide 4 / 7"
    )
    show_text_slide(
        title="Learning phases",
        body=(
            "Each picture will be shown multiple times.\n\n"
            "The first time you will not yet know the correct word –\n"
            "this is normal. Learn from the feedback.\n\n"
            "With each repetition it should become easier\n"
            "to recognise the correct word."
        ),
        footer="Slide 5 / 7"
    )
    show_text_slide(
        title="Control task",
        body=(
            "There is also a control task in between.\n\n"
            "You will see familiar objects with real English words.\n\n"
            "Again, use  1  (Yes) and  2  (No) to decide\n"
            "whether the displayed word matches the picture.\n\n"
            "The task works exactly like the learning task."
        ),
        footer="Slide 6 / 7"
    )
    show_text_slide(
        title="Ready?",
        body=(
            "You are now ready to begin the task.\n\n"
            "Remember:\n"
            "  1 = YES  (correct word)\n"
            "  2 = NO   (wrong word)\n\n"
            "Respond within 2.5 seconds.\n\n"
            "Good luck!"
        ),
        footer="Slide 7 / 7",
        advance_key='space'
    )


def show_instructions_part2():
    """Single slide shown before the main learning phase begins."""
    show_text_slide(
        title="The task starts now",
        body=(
            "The learning task is about to begin.\n\n"
            "As a reminder:\n\n"
            "       1  ->  YES, that is the correct word\n\n"
            "       2  ->  NO,  that is not the correct word\n\n"
            "You have 2.5 seconds per picture."
        ),
        footer="Press the SPACEBAR when you are ready.",
        advance_key='space'
    )


def show_instructions_part3():
    """4 slides for the AFC (recognition) test."""
    show_text_slide(
        title="Memory test",
        body=(
            "You have now completed all learning blocks.\n\n"
            "A memory test follows now.\n\n"
            "You will see pictures that you have seen before.\n"
            "Three words will be shown for each picture."
        ),
        footer="Slide 1 / 4"
    )
    show_text_slide(
        title="Memory test – Your task",
        body=(
            "Select the word that belonged to this picture\n"
            "during the learning phase.\n\n"
            "Press:\n\n"
            "       1  ->  left word\n"
            "       2  ->  middle word\n"
            "       3  ->  right word"
        ),
        footer="Slide 2 / 4"
    )
    show_text_slide(
        title="Memory test – Notes",
        body=(
            "There is no time limit.\n\n"
            "Respond as accurately as possible.\n\n"
            "If you are unsure, guess –\n"
            "do not leave any picture unanswered."
        ),
        footer="Slide 3 / 4"
    )
    show_text_slide(
        title="Memory test – Ready?",
        body=(
            "The memory test is about to begin.\n\n"
            "As a reminder:\n\n"
            "       1  ->  left word\n"
            "       2  ->  middle word\n"
            "       3  ->  right word\n\n"
            "Good luck!"
        ),
        footer="Press the SPACEBAR to begin.",
        advance_key='space'
    )

def get_stimuli(directory):
    files = sorted(glob.glob(os.path.join(directory, '*.jpg')) +
                   glob.glob(os.path.join(directory, '*.JPG')))
    return [f for f in files
            if not os.path.basename(f).lower().startswith('thumbs')]

# ── Stimulus lists ─────────────────────────────────────────────────────────────
# LEARNING: each entry = {pic, words}
#   words[0] = correct word; words[1..4] = foils (one per learning stage)
LEARNING = [
    # Block 1
    {'pic': 'learning/PICTURE_513.jpg', 'words': ['Seltus',  'Geward',   'Gluktant', 'Mekter',  'Belschir']},
    {'pic': 'learning/PICTURE_24.jpg',  'words': ['Basut',   'Gluktant', 'Goser',    'Belschir','Mekte']},
    {'pic': 'learning/PICTURE_40.jpg',  'words': ['Priebem', 'Goser',    'Pafau',    'Mekte',   'Spiene']},
    {'pic': 'learning/PICTURE_245.jpg', 'words': ['Enelt',   'Pafau',    'Aume',     'Spiene',  'Petonsk']},
    {'pic': 'learning/PICTURE_397.jpg', 'words': ['Pofein',  'Aume',     'Geward',   'Petonsk', 'Mekter']},
    # Block 2
    {'pic': 'learning/PICTURE_673.jpg', 'words': ['Ingal',   'Veschegt', 'Sporkel',  'Mummbant','Vewerm']},
    {'pic': 'learning/PICTURE_354.jpg', 'words': ['Aglud',   'Sporkel',  'Plumpent', 'Vewerm',  'Tompamm']},
    {'pic': 'learning/PICTURE_606.jpg', 'words': ['Lokrast', 'Plumpent', 'Volkant',  'Tompamm', 'Nazehl']},
    {'pic': 'learning/PICTURE_308.jpg', 'words': ['Ingam',   'Volkant',  'Straugel', 'Nazehl',  'Pakel']},
    {'pic': 'learning/PICTURE_321.jpg', 'words': ['Mobe',    'Straugel', 'Veschegt', 'Pakel',   'Mummbant']},
]

# CONTROL: each entry = {pic, words}
#   words[0] = correct (real) word; words[1..2] = foils
CONTROL = [
    {'pic': 'control/PICTURE_156.jpg', 'words': ['Fl\u00f6te',  'Besen',  'Mantel']},
    {'pic': 'control/PICTURE_590.jpg', 'words': ['Besen',  'Mantel', 'Baby']},
    {'pic': 'control/PICTURE_644.jpg', 'words': ['Mantel', 'Baby',   'Bogen']},
    {'pic': 'control/PICTURE_674.jpg', 'words': ['Baby',   'Bogen',  'Fl\u00f6te']},
    {'pic': 'control/PICTURE_680.jpg', 'words': ['Bogen',  'Fl\u00f6te', 'Besen']},
    {'pic': 'control/PICTURE_559.jpg', 'words': ['Gurke',  'Kabel',  'Robbe']},
    {'pic': 'control/PICTURE_523.jpg', 'words': ['Kabel',  'Robbe',  'Wespe']},
    {'pic': 'control/PICTURE_92.jpg',  'words': ['Robbe',  'Wespe',  'Kiwi']},
    {'pic': 'control/PICTURE_62.jpg',  'words': ['Wespe',  'Kiwi',   'Gurke']},
    {'pic': 'control/PICTURE_125.jpg', 'words': ['Kiwi',   'Gurke',  'Kabel']},
]

# ── Trial builder ──────────────────────────────────────────────────────────────

def build_block_trials(items, n_ls=4):
    """
    For each item and each learning stage, produce:
      - one 'c' trial  (correct word, key 1 = Ja)
      - one 'i' trial  (foil word rotating per ls, key 2 = Nein)
    Returns task_list[ls] = list of trial dicts for that learning stage.
    """
    task_list = [[] for _ in range(n_ls)]
    for item in items:
        pic   = item['pic']
        corr  = item['words'][0]
        foils = item['words'][1:]
        for ls in range(n_ls):
            foil = foils[ls % len(foils)]
            task_list[ls].append({'pic': pic, 'word': corr,
                                  'correct_word': corr, 'condition': 'c'})
            task_list[ls].append({'pic': pic, 'word': foil,
                                  'correct_word': corr, 'condition': 'i'})
    return task_list

def shuffle_trials(trials):
    """Shuffle with constraint: no consecutive same pic, same word, or
    correct_word of trial k matching word of trial k+1."""
    t = trials[:]
    for _ in range(500):
        random.shuffle(t)
        ok = all(
            t[k]['pic']          != t[k+1]['pic']  and
            t[k]['word']         != t[k+1]['word'] and
            t[k]['correct_word'] != t[k+1]['word']
            for k in range(len(t) - 1)
        )
        if ok:
            break
    return t

# ── Trial runner ───────────────────────────────────────────────────────────────

def run_trial(trial, phase, block_run, block_num, ls_num, trial_idx):
    """
    Phase 1  (STIM_DUR = 2.5 s):
        Image + word shown for the full window.
        Key 1 or 2 accepted at any point; window always completes.
    Phase 2  (FEEDBACK_DUR = 2.0 s):
        Feedback text only – "Korrekt/Falsch/Zu spät, das ist {correct_word}".
    """
    pic_path     = os.path.join(STIM_DIR, trial['pic'])
    word         = trial['word']
    correct_word = trial['correct_word']
    condition    = trial['condition']

    # ── Phase 1 ───────────────────────────────────────────────────────────
    if os.path.isfile(pic_path):
        pres_pic.setImage(pic_path)
        pres_pic.draw()
    else:
        visual.TextStim(win, text=f"[{trial['pic']}]",
                        color='white', height=50).draw()
    pres_word.setText(word)
    pres_word.draw()
    if not fmri_mode:
        key_label_1.draw()
        key_label_2.draw()
    win.flip()
    onset = global_clock.getTime()

    event.clearEvents()
    resp_clock = core.Clock()
    response = rt = None
    while resp_clock.getTime() < STIM_DUR:
        keys = event.getKeys(keyList=[KEY_YES, KEY_NO, 'escape'],
                             timeStamped=resp_clock)
        if keys:
            key, t = keys[0]
            if key == 'escape':
                _csv_file.close(); win.close(); core.quit()
            response, rt = key, t
            break
        check_quit()

    # Always wait out the full stimulus window
    elapsed = resp_clock.getTime()
    if elapsed < STIM_DUR:
        core.wait(STIM_DUR - elapsed)

    # ── Determine correctness ─────────────────────────────────────────────
    if response is None:
        correct_flag = 'timeout'
        fb_msg = f'Too late, it is {correct_word}'
    elif (condition == 'c' and response == KEY_YES) or \
         (condition == 'i' and response == KEY_NO):
        correct_flag = 'correct'
        fb_msg = f'Correct, it is {correct_word}'
    else:
        correct_flag = 'incorrect'
        fb_msg = f'Wrong, it is {correct_word}'

    # ── Phase 2 ───────────────────────────────────────────────────────────
    feedback_text.setText(fb_msg)
    feedback_text.draw()
    win.flip()
    core.wait(FEEDBACK_DUR)
    check_quit()

    write_row(phase=phase, block_run=block_run, block_num=block_num,
              learning_stage=ls_num, trial=trial_idx,
              image=trial['pic'], word=word,
              correct_word=correct_word, condition=condition,
              response=response, correct=correct_flag,
              rt=round(rt, 4) if rt else '',
              onset_time=round(onset, 4))

    logging.data(f"{phase} run{block_run}_blk{block_num}_LS{ls_num}_T{trial_idx}: "
                 f"word={word} corr={correct_word} cond={condition} "
                 f"resp={response} rt={rt} acc={correct_flag}")

# ── Block runner ───────────────────────────────────────────────────────────────

def run_block(items, block_run, block_num, phase, n_ls=4):
    task_list = build_block_trials(items, n_ls)
    for ls in range(n_ls):
        shuffled = shuffle_trials(task_list[ls])
        for t_idx, trial in enumerate(shuffled, 1):
            run_trial(trial, phase=phase, block_run=block_run,
                      block_num=block_num, ls_num=ls + 1, trial_idx=t_idx)
        show_fixation(FIX_DUR)

def run_afc():
    afc_files = get_stimuli(AFC_DIR)
    if not afc_files:
        return
    random.shuffle(afc_files)
    for t_idx, img_path in enumerate(afc_files, 1):
        event.clearEvents()
        afc_pic.setImage(img_path); afc_pic.draw(); win.flip()
        onset = global_clock.getTime()
        keys  = event.waitKeys(keyList=['1', '2', '3', 'escape'])
        rt    = global_clock.getTime() - onset
        if 'escape' in keys:
            _csv_file.close(); win.close(); core.quit()
        write_row(phase='AFC', trial=t_idx,
                  image=os.path.basename(img_path),
                  response=keys[0], rt=round(rt, 4),
                  onset_time=round(onset, 4))

# ── Block order: control (idx 2) must not be first or last ────────────────────
def make_block_order(n_blocks=3, ctrl_indices=None):
    if ctrl_indices is None:
        ctrl_indices = {2}
    order = list(range(n_blocks))
    for _ in range(500):
        random.shuffle(order)
        if order[0] not in ctrl_indices and order[-1] not in ctrl_indices:
            return order
    return [0, 2, 1]  # fallback

# ── Bubble paths ───────────────────────────────────────────────────────────────
BUBBLES = {
    'hello':    _p('Stimuli', 'bubbles', 'hello.jpg'),
    'learning': _p('Stimuli', 'bubbles', 'learning.jpg'),
    'control':  _p('Stimuli', 'bubbles', 'control.jpg'),
    'bye':      _p('Stimuli', 'bubbles', 'bye.jpg'),
}

ALL_BLOCKS = [
    # (items_slice,    phase,        bubble_key, block_num_csv)
    (LEARNING[:5],    'learning-1', 'learning', 1),
    (LEARNING[5:],    'learning-2', 'learning', 2),
    (CONTROL,         'control-1',  'control',  3),
]

# ── Main experiment ────────────────────────────────────────────────────────────

# 00  Instructions Part 1  (7 slides, SPACE to advance)
show_instructions_part1()

# 01  Instructions Part 2  (1 slide, SPACE to start)
show_instructions_part2()

# 02  Hello bubble, then blocks
show_bubble(BUBBLES['hello'], duration=FIX_DUR)

order = make_block_order()
for run_idx, blk_idx in enumerate(order):
    items, phase, bubble_key, block_num = ALL_BLOCKS[blk_idx]
    show_bubble(BUBBLES[bubble_key], duration=FIX_DUR)
    run_block(items, block_run=run_idx + 1, block_num=block_num,
              phase=phase, n_ls=4)

show_bubble(BUBBLES['bye'], duration=FIX_DUR)

# 03  Instructions Part 3 – AFC  (4 slides, SPACE on last)
show_instructions_part3()

# 04  AFC
run_afc()

# End screen
feedback_text.setText('Thank you for your participation!')
feedback_text.draw(); win.flip()
core.wait(3.0)

_csv_file.close(); win.close(); core.quit()
