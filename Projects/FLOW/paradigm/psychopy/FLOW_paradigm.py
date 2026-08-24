#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mental Arithmetic Behavioral Paradigm — PsychoPy implementation
Based on Ulrich et al. (2014, 2016b)

Converted from: Projects/FLOW/paradigm/pygame/FLOW_paradigm_pygame.py
Dependencies: psychopy, pandas, numpy

Run:          python FLOW_paradigm_psychoPy.py
"""

import sys
import os
import random
import time
from datetime import datetime

import numpy as np
import pandas as pd
from psychopy import visual, core, event, gui

# ═══════════════════════════════════════════════════════════════════════════════
# ▼▼▼  PARADIGM CONFIG — THIS IS THE ONLY BLOCK YOU EDIT  ▼▼▼
# ═══════════════════════════════════════════════════════════════════════════════

# ── Identity ───────────────────────────────────────────────────────────────────
PARADIGM_ID   = "FLOW"
DATA_SUFFIX   = "FLOW_math"

# ── Timing (SECONDS) ──────────────────────────────────────────────────────────
BLOCK_DURATION = 170.0
TASK_TIMEOUT   = 18.0
BREAK_DURATION = 4.0
REST_DURATION  = 20.0

# ── Conditions ─────────────────────────────────────────────────────────────────
CONDITIONS = {'B': 'Langeweile', 'F': 'Flow', 'O': 'Überlastung'}

SEQUENCES = [
    ['B','F','O','B','F','B','O','F','O','F','B','O'],
    ['B','O','F','B','O','B','F','O','F','O','B','F'],
]

# ── Display geometry (PIXELS — house style requires explicit sizes) ───────────
WIN_SIZE      = (1400, 1050)
BG_COLOR      = (0, 0, 0)        # rgb255 black
WIN_BG_COLOR  = (1, 1, 1)        # rgb white (for dialog/instructions)

TEXT_COLOR    = (0, 0, 0)        # black
DIM_COLOR     = (0.63, 0.63, 0.63)  # grey (rgb)
BOX_BORDER    = (0, 0, 0)        # black
SEL_COLOR     = (0.2, 0.2, 0.78)     # blue (rgb)

# ── Likert ─────────────────────────────────────────────────────────────────────
LIKERT_QUESTIONS = [
    "Ich würde solche mathematischen Berechnungen nur zu gern noch einmal lösen",
    "Ich fühle mich optimal beansprucht",
    "Ich war begeistert",
]
LIKERT_LABELS = [
    "Stimme ich\nüberhaupt\nnicht zu", "2", "3", "4", "5", "6",
    "Stimme ich\nvoll zu",
]

# ═══════════════════════════════════════════════════════════════════════════════
# ▲▲▲  END PARADIGM CONFIG — do not edit below this line  ▲▲▲
# ═══════════════════════════════════════════════════════════════════════════════


# ── Paths ──────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts):
    return os.path.join(_HERE, *parts)

DATA_DIR = _p('data')


# ═══════════════════════════════════════════════════════════════════════════════
# WINDOW & CLOCK  — copied verbatim from paradigm_template.py
# ═══════════════════════════════════════════════════════════════════════════════

win = visual.Window(
    size=WIN_SIZE, fullscr=False,
    color=WIN_BG_COLOR, colorSpace="rgb",
    units="pix", allowGUI=True,
)
global_clock = core.Clock()

# ── Visual objects ─────────────────────────────────────────────────────────────
fix_stim = visual.TextStim(win, text="+", color="white", height=80, pos=(0, 0))
feedback_text = visual.TextStim(win, text="", color="white", height=50,
                                pos=(0, 350), wrapWidth=1100)


# ── Helpers ────────────────────────────────────────────────────────────────────
def check_quit():
    """Check for escape and quit cleanly."""
    if event.getKeys(keyList=["escape"]):
        save_data(pid, task_results, likert_responses)
        win.close()
        core.quit()


def show_fixation(duration=1.0):
    """Show a fixation cross for `duration` seconds."""
    fix_stim.draw(); win.flip(); core.wait(duration); check_quit()


# ═══════════════════════════════════════════════════════════════════════════════
# MATH TASK GENERATORS  — identical to pygame version
# ═══════════════════════════════════════════════════════════════════════════════

def create_boredom_task():
    base   = random.randint(100, 109)
    addend = random.randint(1, 9)
    numbers = [base, addend]
    random.shuffle(numbers)
    return {'text': ' + '.join(str(n) for n in numbers),
            'answer': sum(numbers), 'numbers': numbers}


def create_task_at_level(level):
    level = max(1, level)
    anchor = random.randint(100, 109)
    if level % 2 == 1:
        extra_two = (level - 1) // 2
        extra_one = 1
    else:
        extra_two = level // 2
        extra_one = 0
    numbers = ([anchor]
               + [random.randint(10, 99) for _ in range(extra_two)]
               + [random.randint(1, 9)  for _ in range(extra_one)])
    random.shuffle(numbers)
    return {'text': ' + '.join(str(n) for n in numbers),
            'answer': sum(numbers), 'numbers': numbers}


def create_flow_task(level):
    return create_task_at_level(level)


def create_overload_task(level):
    return create_task_at_level(level)


def make_placeholder(numbers):
    return ' + '.join('x' * len(str(n)) for n in numbers)


def update_difficulty(is_correct, level, cons_correct, cons_incorrect,
                      condition, starting_level):
    if is_correct:
        cons_correct += 1
        cons_incorrect = 0
        if cons_correct >= 2:
            level += 1
            cons_correct = 0
            print(f"  ✓✓ Zwei richtig! → Niveau {level}")
    else:
        cons_incorrect += 1
        cons_correct = 0
        if cons_incorrect >= 2:
            min_level = starting_level if condition == 'O' else 1
            new_level = max(min_level, level - 1)
            print(f"  ✗✗ Zwei falsch! → Niveau {new_level}")
            level = new_level
            cons_incorrect = 0
    return level, cons_correct, cons_incorrect


def expr_font_size(text):
    n = len(text)
    if n <= 9:  return 110
    if n <= 14: return 90
    if n <= 20: return 72
    if n <= 25: return 58
    if n <= 30: return 48
    return 40


# ═══════════════════════════════════════════════════════════════════════════════
# SCREEN HELPERS — replicating pygame visual elements with PsychoPy
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# COORDINATE CONVERSION  (pygame → PsychoPy)
# ═══════════════════════════════════════════════════════════════════════════════
# This paradigm was ported from pygame, where the origin (0,0) is the TOP-LEFT
# corner and y grows DOWNWARD. PsychoPy with units="pix" puts the origin at the
# SCREEN CENTRE and y grows UPWARD.
#
# All layout code below keeps the original pygame-style coordinates for
# readability; every position is converted at the point of use by _px().
# Do not pass raw pygame coords to a PsychoPy stim without calling _px().

def _px(x, y):
    """pygame-style (top-left origin, y down) -> PsychoPy pix (centre origin, y up)."""
    return (x - win.size[0] / 2.0, win.size[1] / 2.0 - y)


def _metallic_rect(x, y, w, h, radius=8):
    """
    Draw a metallic silver input box using gradient bands (replicating pygame
    draw_metallic_box).
    """
    # Gradient bands (top bright → mid dark → bottom bright)
    bands = []
    for i in range(h):
        t = i / max(h - 1, 1)
        if t < 0.18:
            v = int(235 + (255 - 235) * (t / 0.18))
        elif t < 0.45:
            v = int(255 - (255 - 175) * ((t - 0.18) / 0.27))
        elif t < 0.72:
            v = int(175 + (195 - 175) * ((t - 0.45) / 0.27))
        else:
            v = int(195 + (230 - 195) * ((t - 0.72) / 0.28))
        bands.append((max(0, min(255, v - 8)),
                      max(0, min(255, v - 4)),
                      max(0, min(255, v + 6))))

    for i, color_rgb in enumerate(bands):
        band = visual.Rect(
            win, width=w, height=1, pos=_px(x + w / 2, y + i),
            fillColor=color_rgb, colorSpace="rgb255",
            lineColor=color_rgb,
        )
        band.draw()

    # Outer dark rim
    rim = visual.Rect(
        win, width=w, height=h, pos=_px(x + w / 2, y + h / 2),
        fillColor=None,
        lineColor=(90, 95, 105), colorSpace="rgb255",
        lineWidth=2,
    )
    rim.draw()


def _draw_button(cx, y, label, width=90, height=70,
                 action_type='digit', pressed_action=None):
    """
    Draw a single numpad button, replicating pygame draw_numpad.
    """
    if action_type == pressed_action:
        bg = (0.7, 0.7, 0.86)
        border = (0.16, 0.16, 0.63)
    elif action_type == 'enter':
        bg = (0.235, 0.627, 0.235)
        border = (0.118, 0.392, 0.118)
    elif action_type == 'del':
        bg = (0.784, 0.314, 0.314)
        border = (0.545, 0.157, 0.157)
    else:
        bg = (0.902, 0.902, 0.941)
        border = (0.549, 0.549, 0.627)

    btn = visual.Rect(
        win, width=width, height=height, pos=_px(cx, y + height / 2),
        fillColor=bg, colorSpace="rgb",
        lineColor=border,
        lineWidth=2,
    )
    btn.draw()

    fsize = 22 if action_type in ('del', 'enter') else 28
    bold = action_type in ('enter', 'del')
    txt_color = (1, 1, 1) if action_type in ('enter', 'del') else TEXT_COLOR
    label_stim = visual.TextStim(
        win, text=label.upper(), color=txt_color, height=fsize,
        bold=bold, units="pix",
    )
    label_stim.pos = _px(cx, y + height / 2)
    label_stim.draw()


def _text_at(x, y, text, size=28, color=TEXT_COLOR, bold=False, wrapWidth=None):
    """Create, position and draw a TextStim at (x,y) — center-based coords."""
    ts = visual.TextStim(
        win, text=text, color=color, height=size,
        bold=bold, units="pix", wrapWidth=wrapWidth,
    )
    ts.pos = _px(x, y)
    ts.draw()
    return ts


def _text_centered(text, y, size=28, color=TEXT_COLOR, bold=False, wrapWidth=None):
    """Centred horizontally, draw at y."""
    return _text_at(win.size[0] / 2, y, text, size, color, bold, wrapWidth)


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENS
# ═══════════════════════════════════════════════════════════════════════════════

def show_instruction(text):
    """Show text and wait for SPACE or ESCAPE."""
    win.fullscr = False
    win.allowGUI = True

    _text_centered(text, win.size[1] / 4, size=32, bold=True, wrapWidth=1100)
    _text_centered("[ LEERTASTE zum Fortfahren ]",
                   win.size[1] - 80, size=24, color=DIM_COLOR)
    win.flip()
    while True:
        keys = event.getKeys()
        if 'space' in keys or 'escape' in keys:
            break
        time.sleep(0.01)


def show_rest():
    """20-second rest between blocks."""
    print("Pausenphase...")
    win.fullscr = False
    win.allowGUI = True
    end = time.monotonic() + REST_DURATION
    while time.monotonic() < end:
        remaining = int(end - time.monotonic()) + 1
        fix_stim.text = "+"
        fix_stim.height = 180
        fix_stim.pos = _px(win.size[0] / 2, 110)   # 110 px below the top edge
        fix_stim.draw()
        _text_centered("Pause", win.size[1] / 2 + 80, 32, color=DIM_COLOR)
        _text_centered(f"{remaining}s", win.size[1] / 2 + 130, 28, color=DIM_COLOR)
        win.flip()
        time.sleep(0.05)


def show_break(block_info_text, placeholder, next_numbers=None):
    """4-second break with placeholder expression."""
    win.fullscr = False
    win.allowGUI = True
    win.clearBuffer()
    end = time.monotonic() + BREAK_DURATION
    ph = make_placeholder(next_numbers) if next_numbers else placeholder
    fsize = expr_font_size(ph)
    while time.monotonic() < end:
        win.clearBuffer()
        _text_centered(block_info_text, 40, 26, color=DIM_COLOR)
        _text_centered("Kurze Pause", 90, 28, color=DIM_COLOR)
        _text_centered(ph, win.size[1] / 2 - fsize / 2, size=fsize,
                       color=DIM_COLOR, bold=True)
        win.flip()
        time.sleep(0.05)


# ═══════════════════════════════════════════════════════════════════════════════
# TRIAL
# ═══════════════════════════════════════════════════════════════════════════════

def run_trial(expression, block_info_text, block_start, condition,
              block_duration=BLOCK_DURATION):
    """
    Show expression + input box + numpad, collect answer via keyboard.
    Returns (user_answer, is_correct, timed_out, response_time_ms).
    """
    fsize = expr_font_size(expression['text'])
    box_h = 64
    box_w = 300
    BH, GAP = 70, 10
    numpad_rows = 4
    numpad_h = numpad_rows * BH + (numpad_rows - 1) * GAP
    total_h = fsize + 16 + box_h + 20 + numpad_h
    block_y = max(110, (win.size[1] - total_h) // 2)

    expr_y = block_y
    input_y = expr_y + fsize + 16
    numpad_y = input_y + box_h + 20
    cx = win.size[0] // 2

    BW, GAP_NP = 90, 10
    cols = 3
    grid = [
        ['7', '8', '9'],
        ['4', '5', '6'],
        ['1', '2', '3'],
        ['del', '0', 'enter'],
    ]
    total_w = cols * BW + (cols - 1) * GAP_NP
    start_x = cx - total_w // 2

    user_input = ''
    submitted = False
    timed_out = False
    trial_start = time.monotonic()
    cursor_tick = 0
    pressed_action = None

    while not submitted:
        elapsed = time.monotonic() - trial_start
        block_elapsed = time.monotonic() - block_start

        if elapsed >= TASK_TIMEOUT or block_elapsed >= block_duration:
            timed_out = True
            break

        remaining = int(TASK_TIMEOUT - elapsed) + 1

        # ── draw ──────────────────────────────────────────────────────────────
        win.clearBuffer()

        _text_centered(block_info_text, 14, 26)
        _text_centered(f"Zeit: {remaining}s", 48, 24, color=DIM_COLOR)
        _text_centered(expression['text'],
                       expr_y + fsize / 2, size=fsize, bold=True)

        # Input box — metallic silver
        box_left = cx - box_w // 2
        box_top = input_y
        _metallic_rect(box_left, box_top, box_w, box_h, radius=10)
        cursor = '|' if (cursor_tick // 30) % 2 == 0 else ' '
        input_text = user_input + cursor
        text_height = int(box_h * 0.60)
        # In PsychoPy 2026+, TextStim defaults to center-align.
        # We create a TextStim with wrapWidth and position it so its
        # left-edge (center - wrapWidth/2) sits 10px from box_left.
        text_stim = visual.TextStim(
            win, text=input_text, color=TEXT_COLOR,
            height=text_height, units="pix",
            wrapWidth=box_w - 20,
        )
        text_stim.pos = _px(box_left + 10 + (box_w - 20) / 2, box_top + box_h / 2)
        text_stim.draw()

        # Numpad
        for row_i, row in enumerate(grid):
            for col_i, label in enumerate(row):
                bx = start_x + col_i * (BW + GAP_NP)
                by = numpad_y + row_i * (BH + GAP_NP)
                btn_cx = bx + BW / 2
                action = label
                if action.isdigit():
                    action_type = 'digit'
                elif action == 'del':
                    action_type = 'del'
                else:
                    action_type = 'enter'
                _draw_button(btn_cx, by, label, width=BW, height=BH,
                             action_type=action_type,
                             pressed_action=pressed_action)

        win.flip()
        cursor_tick += 1
        pressed_action = None  # reset after one frame

        # ── events ────────────────────────────────────────────────────────────
        keys = event.getKeys()
        for key in keys:
            if key == 'escape':
                raise KeyboardInterrupt()
            elif key in ('return', 'kp_enter'):
                submitted = True
            elif key == 'backspace':
                user_input = user_input[:-1]
            elif key.isdigit():
                user_input += key

        time.sleep(0.016)

    rt_ms = (time.monotonic() - trial_start) * 1000

    if timed_out:
        return None, False, True, rt_ms
    if user_input == '':
        return None, False, False, rt_ms

    try:
        answer = int(user_input)
        is_correct = (answer == expression['answer'])
        return answer, is_correct, False, rt_ms
    except ValueError:
        return None, False, False, rt_ms


# ═══════════════════════════════════════════════════════════════════════════════
# LIKERT
# ═══════════════════════════════════════════════════════════════════════════════

def run_likert(condition, block_idx, participant_id, likert_responses):
    """Show each Likert question with 7 large tile buttons. Keyboard 1-7 + ENTER."""
    N = 7
    BTN_W = max(130, (WIN_SIZE[0] - 80) // N)
    BTN_H = 110
    GAP = 10
    total_w = N * BTN_W + (N - 1) * GAP
    start_x = WIN_SIZE[0] // 2 - total_w // 2
    btn_y = WIN_SIZE[1] // 2 - BTN_H // 2 + 30

    conf_w, conf_h = 220, 52
    conf_x = WIN_SIZE[0] // 2 - conf_w // 2
    conf_y = btn_y + BTN_H + 40

    CLR_IDLE    = (0.824, 0.835, 0.882)
    CLR_HOVER   = (0.725, 0.765, 0.843)
    CLR_SEL     = (0.235, 0.431, 0.863)
    CLR_SEL_HV  = (0.314, 0.510, 0.941)
    CLR_BORDER  = (0.471, 0.490, 0.549)
    CLR_SEL_BRD = (0.118, 0.235, 0.627)
    CLR_CONF    = (0.196, 0.627, 0.235)
    CLR_CONF_HV = (0.275, 0.745, 0.314)
    CLR_CONF_BD = (0.078, 0.353, 0.118)

    def _tile_rect(i):
        return (start_x + i * (BTN_W + GAP), btn_y, BTN_W, BTN_H)

    def _draw_tile(i, value, selected):
        is_sel = (selected == value)
        bg = (CLR_SEL_HV if is_sel else CLR_IDLE)
        brd = (CLR_SEL_BRD if is_sel else CLR_BORDER)
        r = _tile_rect(i)
        rect = visual.Rect(
            win, width=BTN_W - 2, height=BTN_H - 2,
            pos=_px(r[0] + BTN_W / 2, r[1] + BTN_H / 2),
            fillColor=bg, colorSpace="rgb",
            lineColor=brd, lineColorSpace="rgb",
            lineWidth=2,
        )
        rect.draw()

        # Number
        _text_at(r[0] + BTN_W / 2, r[1] + 32, str(value), 36,
                 color=TEXT_COLOR, bold=True)

        # Label (word-wrapped)
        label = LIKERT_LABELS[i].replace("\n", " ")
        words = label.split()
        lines = []
        row = ""
        for w in words:
            test = (row + " " + w).strip()
            if len(test) * 8 <= BTN_W - 10:
                row = test
            else:
                if row:
                    lines.append(row)
                row = w
        if row:
            lines.append(row)
        ly = r[1] + 58
        for line in lines:
            _text_at(r[0] + BTN_W / 2, ly, line, 13, color=TEXT_COLOR)
            ly += 16

    def _draw_confirm(enabled):
        if not enabled:
            bg, brd, tc = (0.706, 0.706, 0.706), (0.510, 0.510, 0.510), (0.863, 0.863, 0.863)
        else:
            bg, brd, tc = CLR_CONF, CLR_CONF_BD, TEXT_COLOR
        rect = visual.Rect(
            win, width=conf_w - 2, height=conf_h - 2,
            pos=_px(conf_x + conf_w / 2, conf_y + conf_h / 2),
            fillColor=bg, colorSpace="rgb",
            lineColor=brd, lineColorSpace="rgb",
            lineWidth=2,
        )
        rect.draw()
        _text_at(WIN_SIZE[0] / 2, conf_y + conf_h / 2,
                 "Bestätigen  ✓", 22, color=tc, bold=True)

    responses = []

    for q_idx, question in enumerate(LIKERT_QUESTIONS):
        selected = None
        goto_next = False

        while True:
            keys = event.getKeys()
            win.clearBuffer()

            _text_at(win.size[0] / 2, 28,
                     f"Frage {q_idx + 1} / {len(LIKERT_QUESTIONS)}",
                     22, color=DIM_COLOR)
            _text_centered(question, 70, 30, color=TEXT_COLOR,
                           bold=True, wrapWidth=1100)

            r0 = _tile_rect(0)
            rN = _tile_rect(N - 1)
            _text_at(r0[0] + BTN_W / 2, btn_y + BTN_H + 10,
                     "← stimme nicht zu", 18, color=DIM_COLOR)
            _text_at(rN[0] + BTN_W / 2, btn_y + BTN_H + 10,
                     "stimme zu →", 18, color=DIM_COLOR)

            for i in range(N):
                _draw_tile(i, i + 1, selected)
            _draw_confirm(selected is not None)

            if selected is None:
                hint = "Bitte eine Zahl anklicken, dann Bestätigen"
            else:
                hint = f"Ausgewählt: {selected}  —  Bestätigen klicken oder ENTER drücken"
            _text_centered(hint, WIN_SIZE[1] - 38, 20, color=DIM_COLOR)

            win.flip()

            for key in keys:
                if key == 'escape':
                    raise KeyboardInterrupt()
                if key.isdigit() and 1 <= int(key) <= 7:
                    selected = int(key)
                if key in ('return', 'kp_enter') and selected is not None:
                    goto_next = True

            if goto_next:
                break

        # Confirmation flash
        win.clearBuffer()
        _text_at(win.size[0] / 2, 28,
                 f"Frage {q_idx + 1} / {len(LIKERT_QUESTIONS)}",
                 22, color=DIM_COLOR)
        _text_centered(question, 70, 30, color=TEXT_COLOR,
                       bold=True, wrapWidth=1100)
        for i in range(N):
            _draw_tile(i, i + 1, selected)
        _draw_confirm(True)
        win.flip()
        time.sleep(0.4)

        responses.append(selected)

    likert_responses.append({
        'participant_id': participant_id,
        'block': block_idx + 1,
        'condition': condition,
        'q1_love_again': responses[0],
        'q2_well_matched': responses[1],
        'q3_thrilled': responses[2],
        'timestamp': datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# BLOCK
# ═══════════════════════════════════════════════════════════════════════════════

def run_block(condition, starting_level, block_idx,
              participant_id, task_results):
    if condition == 'B':
        level = block_starting_level = 1
    elif condition == 'F':
        level = block_starting_level = starting_level
    else:
        level = block_starting_level = starting_level + 3

    cons_correct = 0
    cons_incorrect = 0
    cname = CONDITIONS[condition]
    block_info = f"Block {block_idx + 1}/12 – {cname}"
    print(f"\nBlock {block_idx + 1} – {cname}  (start level {level})")

    block_start = time.monotonic()
    trial_count = 0
    prefetched = None

    while (time.monotonic() - block_start) < BLOCK_DURATION:
        trial_count += 1

        if prefetched is not None:
            expression = prefetched
            prefetched = None
        else:
            if condition == 'B':
                expression = create_boredom_task()
            elif condition == 'F':
                expression = create_flow_task(level)
            else:
                expression = create_overload_task(level)

        user_answer, is_correct, timed_out, rt_ms = run_trial(
            expression, block_info, block_start, condition)

        task_results.append({
            'participant_id': participant_id,
            'block': block_idx + 1,
            'condition': condition,
            'difficulty_level': level,
            'expression': expression['text'],
            'correct_answer': expression['answer'],
            'user_answer': user_answer,
            'is_correct': is_correct,
            'is_timeout': timed_out,
            'response_time_ms': round(rt_ms, 1),
            'timestamp': datetime.now().isoformat(),
        })

        if condition in ('F', 'O'):
            answered_correctly = is_correct and not timed_out
            level, cons_correct, cons_incorrect = update_difficulty(
                answered_correctly, level, cons_correct, cons_incorrect,
                condition, block_starting_level)

        if (time.monotonic() - block_start) < BLOCK_DURATION:
            if condition == 'B':
                next_task = create_boredom_task()
            elif condition == 'F':
                next_task = create_flow_task(level)
            else:
                next_task = create_overload_task(level)
            prefetched = next_task
            show_break(block_info,
                       make_placeholder(expression['numbers']),
                       next_numbers=next_task['numbers'])

    print(f"Block {block_idx + 1} abgeschlossen: {trial_count} Durchgänge, Endniveau: {level}")


# ═══════════════════════════════════════════════════════════════════════════════
# PRACTICE BLOCK
# ═══════════════════════════════════════════════════════════════════════════════

def run_practice_block(condition_type, duration_sec, start_level=1):
    """Returns list of levels (for calibration) or [] for boredom warm-up."""
    level = max(1, start_level)
    cons_correct = 0
    cons_incorrect = 0
    levels = []
    prefetched = None
    block_start = time.monotonic()

    while (time.monotonic() - block_start) < duration_sec:
        if prefetched is not None:
            expression = prefetched
            prefetched = None
        elif condition_type == 'boredom':
            expression = create_boredom_task()
        else:
            expression = create_flow_task(level)

        if (time.monotonic() - block_start) >= duration_sec:
            break

        _, is_correct, timed_out, _ = run_trial(
            expression, "Übung", block_start, condition_type,
            block_duration=duration_sec)

        if condition_type == 'flow':
            levels.append(level)
            answered_correctly = is_correct and not timed_out
            if answered_correctly:
                cons_correct += 1
                cons_incorrect = 0
                if cons_correct >= 2:
                    level += 1
                    cons_correct = 0
                    print(f"  Übung ✓✓ → Niveau {level}")
            else:
                cons_incorrect += 1
                cons_correct = 0
                if cons_incorrect >= 2:
                    level = max(1, level - 1)
                    cons_incorrect = 0
                    print(f"  Übung ✗✗ → Niveau {level}")

        if (time.monotonic() - block_start) < duration_sec:
            if condition_type == 'boredom':
                next_task = create_boredom_task()
            else:
                next_task = create_flow_task(level)
            prefetched = next_task
            show_break("Übung",
                       make_placeholder(expression['numbers']),
                       next_numbers=next_task['numbers'])

    return levels


# ═══════════════════════════════════════════════════════════════════════════════
# DATA SAVING
# ═══════════════════════════════════════════════════════════════════════════════

def save_data(participant_id, task_results, likert_responses):
    os.makedirs(DATA_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    if task_results:
        fn = os.path.join(DATA_DIR, f"{participant_id}_task_{ts}.csv")
        pd.DataFrame(task_results).to_csv(fn, index=False)
        print(f"✓ Aufgabendaten gespeichert: {fn}")

    if likert_responses:
        fn = os.path.join(DATA_DIR, f"{participant_id}_likert_{ts}.csv")
        pd.DataFrame(likert_responses).to_csv(fn, index=False)
        print(f"✓ Likert-Daten gespeichert: {fn}")


# ═══════════════════════════════════════════════════════════════════════════════
# SETUP DIALOG
# ═══════════════════════════════════════════════════════════════════════════════

def setup_dialog():
    """
    Show a PsychoPy dialog for participant info.
    Returns (pid, session, run_fam, run_eval, run_main, start_level).
    """
    exp_info = {
        'participant': '',
        'session': '001',
        'run_familiarization': True,
        'run_skill_eval': True,
        'run_main': True,
        'starting_level': '1',  # string so .isdigit() works
    }

    dlg = gui.DlgFromDict(
        exp_info,
        title="Mentales Rechnen – Paradigma",
        sortKeys=False,
    )
    if not dlg.OK:
        core.quit()

    pid = exp_info['participant'].strip() or 'test'
    session = exp_info['session'] or '001'
    run_fam = exp_info['run_familiarization']
    run_eval = exp_info['run_skill_eval']
    run_main = exp_info['run_main']
    sl = exp_info['starting_level']
    start_level = int(sl) if isinstance(sl, str) and sl.isdigit() else 1

    return pid, session, run_fam, run_eval, run_main, start_level


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    pid, session, run_fam, run_eval, run_main, starting_level = setup_dialog()

    task_results = []
    likert_responses = []

    try:
        # ── Familiarization ───────────────────────────────────────────────────
        if run_fam:
            print("\n=== Familiarisierung (3 min Aufwärmen) ===")
            show_instruction(
                "Familiarisierung\n\n"
                "Sie üben jetzt 3 Minuten lang einfache Additionsaufgaben.\n\n"
                "Geben Sie Ihr Ergebnis ein und bestätigen Sie mit ENTER.\n"
                "Drücken Sie die LEERTASTE zum Starten.")
            run_practice_block('boredom', 180)
            show_instruction(
                "Familiarisierung abgeschlossen!\n\n"
                "Drücken Sie die LEERTASTE zum Fortfahren.")

        # ── Skill Evaluation ─────────────────────────────────────────────────
        if run_eval:
            print("\n=== Kompetenzerfassung (5 min) ===")
            show_instruction(
                "Kompetenzerfassung\n\n"
                "Wir schätzen jetzt Ihren Startschwierigkeitsgrad ein.\n"
                "Die Aufgaben werden schwerer, wenn Sie richtig antworten.\n\n"
                "Drücken Sie die LEERTASTE zum Starten.")
            levels = run_practice_block('flow', 300, start_level=starting_level)
            if levels:
                last_quarter = levels[-max(1, len(levels) // 4):]
                starting_level = max(1, int(np.mean(last_quarter)))
            else:
                starting_level = 1
            print(f"Geschätzter Startschwierigkeitsgrad: {starting_level}")
            show_instruction(
                f"Kompetenzerfassung abgeschlossen!\n\n"
                f"Ihr geschätzter Startschwierigkeitsgrad: {starting_level}\n\n"
                f"Drücken Sie die LEERTASTE zum Fortfahren.")

        if not run_main:
            print("=== Abgeschlossen (kein Hauptexperiment gewählt) ===")
            core.quit()
            return

        # ── Main Experiment ───────────────────────────────────────────────────
        sequence = random.choice(SEQUENCES)
        print(f"\n=== Hauptexperiment ===")
        print(f"Versuchsperson: {pid}  |  Startschwierigkeitsgrad: {starting_level}")
        print(f"Sequenz: {'-'.join(sequence)}")

        show_instruction(
            "Hauptexperiment\n\n"
            "Sie bearbeiten 12 Blöcke mit Rechenaufgaben.\n"
            "Nach jedem Block beantworten Sie 3 kurze Fragen.\n\n"
            "Geben Sie Ihr Ergebnis ein und bestätigen Sie mit ENTER.\n"
            "ESC speichert und beendet das Experiment jederzeit.\n\n"
            "Drücken Sie die LEERTASTE zum Starten.")

        for block_idx, condition in enumerate(sequence):
            if block_idx > 0:
                show_rest()

            run_block(condition, starting_level, block_idx,
                      pid, task_results)
            run_likert(condition, block_idx, pid, likert_responses)

        show_instruction(
            "Experiment abgeschlossen!\n\n"
            "Vielen Dank für Ihre Teilnahme.\n\n"
            "Drücken Sie die LEERTASTE zum Speichern und Beenden.")

        save_data(pid, task_results, likert_responses)

    except KeyboardInterrupt:
        print("\nExperiment unterbrochen – Daten werden gespeichert...")
        save_data(pid, task_results, likert_responses)
    except Exception as e:
        import traceback
        print(f"\nError: {e}")
        traceback.print_exc()
        save_data(pid, task_results, likert_responses)
    finally:
        win.close()
        core.quit()


if __name__ == '__main__':
    main()
