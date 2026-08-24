#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mental Arithmetic Behavioral Paradigm — pygame implementation
Based on Ulrich et al. (2014, 2016b)

Dependencies: pip install pygame pandas numpy
Run:          python math_paradigm_pygame.py
"""

import sys
import os
import random
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pygame

# ============================================================================
# CONFIGURATION
# ============================================================================

#BLOCK_DURATION  = 170.0   # seconds per block
BLOCK_DURATION  = 30   # seconds per block
TASK_TIMEOUT    = 18.0    # seconds per trial
BREAK_DURATION  = 4.0     # seconds between trials
REST_DURATION   = 20.0    # seconds between blocks

CONDITIONS = {'B': 'Langeweile', 'F': 'Flow', 'O': 'Überlastung'}

SEQUENCES = [
    ['B','F','O','B','F','B','O','F','O','F','B','O'],
    ['B','O','F','B','O','B','F','O','F','O','B','F'],
]

WINDOW_SIZE = (1400, 1050)
FULLSCREEN  = False

BG_COLOR   = (255, 255, 255)   # white
TEXT_COLOR = (0,   0,   0)     # black
DIM_COLOR  = (160, 160, 160)   # grey for placeholders
BOX_COLOR  = (0,   0,   0)     # input box border
SEL_COLOR  = (50,  50, 200)    # selected Likert circle fill

LIKERT_QUESTIONS = [
    "Ich würde solche mathematischen Berechnungen nur zu gern noch einmal lösen",
    "Ich fühle mich optimal beansprucht",
    "Ich war begeistert",
]
LIKERT_LABELS = [
    "Stimme ich\nüberhaupt\nnicht zu", "2", "3", "4", "5", "6",
    "Stimme ich\nvoll zu",
]

# ============================================================================
# PYGAME HELPERS
# ============================================================================

class Screen:
    """Thin wrapper around pygame display + font cache."""

    def __init__(self):
        pygame.init()
        flags = pygame.FULLSCREEN if FULLSCREEN else 0
        self.surf = pygame.display.set_mode(WINDOW_SIZE, flags)
        pygame.display.set_caption("Mental Arithmetic Paradigm")
        self._fonts = {}

    def font(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = pygame.font.SysFont("DejaVu Sans", size, bold=bold)
        return self._fonts[key]

    def clear(self):
        self.surf.fill(BG_COLOR)

    def flip(self):
        pygame.display.flip()

    def W(self):
        return self.surf.get_width()

    def H(self):
        return self.surf.get_height()

    def cx(self):
        return self.W() // 2

    def cy(self):
        return self.H() // 2

    def draw_text(self, text, size, y, color=TEXT_COLOR, bold=False, center_x=None):
        """Draw a single line of text centred horizontally (or at center_x)."""
        f   = self.font(size, bold)
        sur = f.render(text, True, color)
        x   = (center_x if center_x is not None else self.cx()) - sur.get_width() // 2
        self.surf.blit(sur, (x, y))
        return sur.get_height()

    def draw_text_wrapped(self, text, size, y, color=TEXT_COLOR, bold=False,
                          max_width=None, line_spacing=8):
        """Draw multi-line text (split on '\n'), centred, return total height."""
        if max_width is None:
            max_width = int(self.W() * 0.85)
        f      = self.font(size, bold)
        lines  = text.split('\n')
        total  = 0
        for line in lines:
            # word-wrap within max_width
            words = line.split()
            row   = ''
            for w in words:
                test = (row + ' ' + w).strip()
                if f.size(test)[0] <= max_width:
                    row = test
                else:
                    if row:
                        sur = f.render(row, True, color)
                        self.surf.blit(sur, (self.cx() - sur.get_width() // 2, y + total))
                        total += sur.get_height() + line_spacing
                    row = w
            if row:
                sur = f.render(row, True, color)
                self.surf.blit(sur, (self.cx() - sur.get_width() // 2, y + total))
                total += sur.get_height() + line_spacing
        return total

    def draw_rect_border(self, rect, color=BOX_COLOR, width=3):
        pygame.draw.rect(self.surf, color, rect, width)

    def draw_circle(self, pos, radius, fill=None, border=TEXT_COLOR, border_width=2):
        if fill:
            pygame.draw.circle(self.surf, fill, pos, radius)
        pygame.draw.circle(self.surf, border, pos, radius, border_width)


def poll_events():
    """Return list of pygame events; quit immediately on QUIT."""
    evs = pygame.event.get()
    for e in evs:
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit(0)
    return evs


def wait_for_key(allowed=None):
    """Block until one of the allowed keys is pressed. Returns the key name."""
    while True:
        for e in poll_events():
            if e.type == pygame.KEYDOWN:
                name = pygame.key.name(e.key)
                if allowed is None or name in allowed:
                    return name
        time.sleep(0.01)


def wait_seconds(seconds):
    """Wait for `seconds` while still processing quit events."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        poll_events()
        time.sleep(0.01)


# ============================================================================
# MATH TASK GENERATORS
# ============================================================================

def create_boredom_task():
    """
    Boredom: one 3-digit number + one 1-digit number.
    Structure: xxx + x   (always has a 3-digit anchor)
    """
    base   = random.randint(100, 109)
    addend = random.randint(1, 9)
    numbers = [base, addend]
    random.shuffle(numbers)
    return {'text': ' + '.join(str(n) for n in numbers),
            'answer': sum(numbers), 'numbers': numbers}


def create_task_at_level(level):
    """
    Level structure — every task contains exactly one 3-digit number
    as the anchor. Additional terms grow in count and digit-length:

    Level 1:  xxx + x
    Level 2:  xxx + xx
    Level 3:  xxx + xx + x
    Level 4:  xxx + xx + xx
    Level 5:  xxx + xx + xx + x
    Level 6:  xxx + xx + xx + xx
    Level 7:  xxx + xx + xx + xx + x
    Level 8:  xxx + xx + xx + xx + xx
    ...and so on (one extra 2-digit or 1-digit term added each level)

    The 3-digit anchor and all addends are randomised within their
    digit-count range; positions are shuffled so the anchor can appear
    anywhere in the expression.
    """
    level = max(1, level)

    # One 3-digit anchor always present (100–109 so sums stay manageable)
    anchor = random.randint(100, 109)

    # Extra terms beyond the anchor
    # Even levels end with a 2-digit term; odd levels end with a 1-digit term.
    # Level 1 → 0 two-digit, 1 one-digit
    # Level 2 → 1 two-digit, 0 one-digit
    # Level 3 → 1 two-digit, 1 one-digit
    # Level 4 → 2 two-digit, 0 one-digit
    # Level 5 → 2 two-digit, 1 one-digit
    # Level 6 → 3 two-digit, 0 one-digit
    # ...
    extra_two = (level - 1) // 2
    extra_one = (level - 1) % 2 + (1 if level % 2 == 1 else 0)
    # Simplify: odd level → ceil((level-1)/2) two-digit + 1 one-digit
    #           even level → level//2 two-digit + 0 one-digit
    if level % 2 == 1:          # odd: ends in 1-digit
        extra_two = (level - 1) // 2
        extra_one = 1
    else:                        # even: ends in 2-digit
        extra_two = level // 2
        extra_one = 0

    numbers = ([anchor]
               + [random.randint(10, 99) for _ in range(extra_two)]
               + [random.randint(1,  9)  for _ in range(extra_one)])
    random.shuffle(numbers)
    return {'text': ' + '.join(str(n) for n in numbers),
            'answer': sum(numbers), 'numbers': numbers}


def create_flow_task(level):
    return create_task_at_level(level)


def create_overload_task(level):
    return create_task_at_level(level)


def make_placeholder(numbers):
    return ' + '.join('x' * len(str(n)) for n in numbers)


# ============================================================================
# DIFFICULTY UPDATE
# ============================================================================

def update_difficulty(is_correct, level, cons_correct, cons_incorrect,
                      condition, starting_level):
    if is_correct:
        cons_correct    += 1
        cons_incorrect   = 0
        if cons_correct >= 2:
            level       += 1
            cons_correct = 0
            print(f"  ✓✓ Zwei richtig! → Niveau {level}")
    else:
        cons_incorrect  += 1
        cons_correct     = 0
        if cons_incorrect >= 2:
            min_level   = starting_level if condition == 'O' else 1
            new_level   = max(min_level, level - 1)
            print(f"  ✗✗ Zwei falsch! → Niveau {new_level}")
            level            = new_level
            cons_incorrect   = 0
    return level, cons_correct, cons_incorrect


# ============================================================================
# EXPRESSION FONT SIZE
# ============================================================================

def expr_font_size(text):
    """
    Font size tuned for new level structure (all levels have 3-digit anchor):
    Level 1-2:  7-8  chars  → 110px
    Level 3-4: 12-13 chars  →  90px
    Level 5-6: 17-18 chars  →  72px
    Level 7-8: 22-23 chars  →  58px
    Level 9-10:27-28 chars  →  48px
    Level 11+: 32+   chars  →  40px
    """
    n = len(text)
    if n <= 9:  return 110
    if n <= 14: return 90
    if n <= 20: return 72
    if n <= 25: return 58
    if n <= 30: return 48
    return 40


# ============================================================================
# SCREENS
# ============================================================================

def show_instruction(scr, text):
    """Show text and wait for SPACE or ESCAPE."""
    scr.clear()
    scr.draw_text_wrapped(text, 32, scr.H() // 4)
    scr.draw_text("[ LEERTASTE zum Fortfahren ]", 24, scr.H() - 80, color=DIM_COLOR)
    scr.flip()
    wait_for_key(['space', 'escape'])


def show_rest(scr):
    print("Pausenphase...")
    end = time.monotonic() + REST_DURATION
    while time.monotonic() < end:
        poll_events()
        remaining = int(end - time.monotonic()) + 1
        scr.clear()
        scr.draw_text("+", 180, scr.cy() - 110, bold=True)
        scr.draw_text("Pause", 32, scr.cy() + 80, color=DIM_COLOR)
        scr.draw_text(f"{remaining}s", 28, scr.cy() + 130, color=DIM_COLOR)
        scr.flip()
        time.sleep(0.05)


def show_break(scr, block_info_text, placeholder, next_numbers=None):
    end = time.monotonic() + BREAK_DURATION
    ph  = make_placeholder(next_numbers) if next_numbers else placeholder
    fsize = expr_font_size(ph)
    while time.monotonic() < end:
        poll_events()
        scr.clear()
        scr.draw_text(block_info_text, 26, 40, color=DIM_COLOR)
        scr.draw_text("Kurze Pause", 28, 90, color=DIM_COLOR)
        scr.draw_text(ph, fsize, scr.cy() - fsize // 2, color=DIM_COLOR, bold=True)
        scr.flip()
        time.sleep(0.05)


# ============================================================================
# TRIAL
# ============================================================================

# ============================================================================
# NUMPAD WIDGET
# ============================================================================

def make_numpad(cx, top_y):
    """
    Build numpad button layout centred on cx, starting at top_y.
    Returns list of dicts: {rect, label, action}
    action: '0'-'9' = digit, 'del' = backspace, 'enter' = submit
    Layout:
        7  8  9
        4  5  6
        1  2  3
       DEL  0  ENTER
    """
    BW, BH, GAP = 90, 70, 10
    cols = 3
    grid = [
        ['7', '8', '9'],
        ['4', '5', '6'],
        ['1', '2', '3'],
        ['del', '0', 'enter'],
    ]
    total_w = cols * BW + (cols - 1) * GAP
    start_x = cx - total_w // 2
    buttons = []
    for row_i, row in enumerate(grid):
        for col_i, label in enumerate(row):
            x = start_x + col_i * (BW + GAP)
            y = top_y   + row_i * (BH + GAP)
            buttons.append({'rect': pygame.Rect(x, y, BW, BH),
                            'label': label, 'action': label})
    return buttons


def draw_numpad(scr, buttons, pressed_action=None):
    """Draw all numpad buttons, highlight the pressed one."""
    for btn in buttons:
        action = btn['action']
        rect   = btn['rect']
        label  = btn['label'].upper()

        if action == pressed_action:
            bg, border = (180, 180, 220), (40,  40, 160)
        elif action == 'enter':
            bg, border = (60, 160,  60), (30, 100,  30)
        elif action == 'del':
            bg, border = (200, 80,  80), (140, 40,  40)
        else:
            bg, border = (230, 230, 240), (140, 140, 160)

        pygame.draw.rect(scr.surf, bg,     rect, border_radius=8)
        pygame.draw.rect(scr.surf, border, rect, 2, border_radius=8)

        fsize = 22 if action in ('del', 'enter') else 28
        bold  = action in ('enter', 'del')
        f     = scr.font(fsize, bold=bold)
        txt_c = (255, 255, 255) if action in ('enter', 'del') else TEXT_COLOR
        sur   = f.render(label, True, txt_c)
        scr.surf.blit(sur, (rect.centerx - sur.get_width()  // 2,
                            rect.centery - sur.get_height() // 2))



def draw_metallic_box(surf, rect, radius=8):
    """
    Draw a metallic silver input box using horizontal gradient bands
    and a polished highlight/shadow rim.
    """
    x, y, w, h = rect.x, rect.y, rect.width, rect.height

    # ── gradient bands (top bright → mid dark → bottom bright) ───────────────
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
        # cool blue-grey metal tint
        bands.append((max(0, min(255, v - 8)),
                      max(0, min(255, v - 4)),
                      max(0, min(255, v + 6))))

    # Render gradient, clip to rounded rect via SRCALPHA mask
    grad_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for i, color in enumerate(bands):
        pygame.draw.line(grad_surf, color, (0, i), (w, i))

    mask_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    mask_surf.fill((0, 0, 0, 0))
    pygame.draw.rect(mask_surf, (255, 255, 255, 255),
                     (0, 0, w, h), border_radius=radius)
    grad_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(grad_surf, (x, y))

    # ── outer dark rim ────────────────────────────────────────────────────────
    pygame.draw.rect(surf, (90, 95, 105), rect, 2, border_radius=radius)

    # ── inner glint lines (top-left bright, bottom shadow) ───────────────────
    inner = pygame.Rect(x + 2, y + 2, w - 4, h - 4)
    pygame.draw.line(surf, (255, 255, 255),
                     (inner.x + radius, inner.y),
                     (inner.right - radius, inner.y), 1)
    pygame.draw.line(surf, (255, 255, 255),
                     (inner.x, inner.y + radius),
                     (inner.x, inner.bottom - radius), 1)
    pygame.draw.line(surf, (110, 115, 125),
                     (inner.x + radius, inner.bottom),
                     (inner.right - radius, inner.bottom), 1)

def run_trial(scr, expression, block_info_text, block_start, condition,
              block_duration=BLOCK_DURATION):
    """
    Show expression + clickable numpad, collect answer via click or keyboard.
    Returns (user_answer, is_correct, timed_out, response_time_ms).
    block_duration: total seconds of the enclosing block/phase.
    """
    fsize = expr_font_size(expression['text'])
    box_h = 64
    box_w = 300

    # ── vertical stack layout: expr → input box → numpad ─────────────────────
    BH, GAP      = 70, 10
    numpad_rows  = 4
    numpad_h     = numpad_rows * BH + (numpad_rows - 1) * GAP
    total_h      = fsize + 16 + box_h + 20 + numpad_h
    block_y      = max(110, (scr.H() - total_h) // 2)

    expr_y   = block_y
    input_y  = expr_y  + fsize + 16
    numpad_y = input_y + box_h  + 20

    box_rect = pygame.Rect(scr.cx() - box_w // 2, input_y, box_w, box_h)
    buttons  = make_numpad(scr.cx(), numpad_y)

    user_input     = ''
    submitted      = False
    timed_out      = False
    trial_start    = time.monotonic()
    cursor_tick    = 0
    pressed_action = None

    while not submitted:
        elapsed       = time.monotonic() - trial_start
        block_elapsed = time.monotonic() - block_start

        if elapsed >= TASK_TIMEOUT or block_elapsed >= block_duration:
            timed_out = True
            break

        remaining = int(TASK_TIMEOUT - elapsed) + 1

        # ── draw ──────────────────────────────────────────────────────────────
        scr.clear()
        scr.draw_text(block_info_text, 26, 14)
        scr.draw_text(f"Zeit: {remaining}s", 24, 48, color=DIM_COLOR)
        scr.draw_text(expression['text'], fsize, expr_y, bold=True)

        # Input display box — metallic silver
        draw_metallic_box(scr.surf, box_rect, radius=10)
        cursor = '|' if (cursor_tick // 30) % 2 == 0 else ' '
        scr.draw_text(user_input + cursor,
                      int(box_h * 0.60),
                      input_y + (box_h - int(box_h * 0.60)) // 2)

        # Numpad
        draw_numpad(scr, buttons, pressed_action)

        scr.flip()
        cursor_tick   += 1
        pressed_action = None   # reset highlight after one frame

        # ── events ────────────────────────────────────────────────────────────
        for e in poll_events():
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                for btn in buttons:
                    if btn['rect'].collidepoint(e.pos):
                        pressed_action = btn['action']
                        if btn['action'].isdigit():
                            user_input += btn['action']
                        elif btn['action'] == 'del':
                            user_input = user_input[:-1]
                        elif btn['action'] == 'enter':
                            submitted = True

            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    raise KeyboardInterrupt
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    pressed_action = 'enter'
                    submitted = True
                elif e.key == pygame.K_BACKSPACE:
                    pressed_action = 'del'
                    user_input = user_input[:-1]
                elif e.unicode.isdigit():
                    pressed_action = e.unicode
                    user_input += e.unicode

        time.sleep(0.016)

    rt_ms = (time.monotonic() - trial_start) * 1000

    if timed_out:
        return None, False, True, rt_ms
    if user_input == '':
        return None, False, False, rt_ms

    try:
        answer     = int(user_input)
        is_correct = answer == expression['answer']
        return answer, is_correct, False, rt_ms
    except ValueError:
        return None, False, False, rt_ms

# ============================================================================
# LIKERT
# ============================================================================

def run_likert(scr, condition, block_idx, participant_id, likert_responses):
    """
    Show each Likert question with 7 large clickable tile buttons.
    Mouse click OR keyboard 1-7 selects an answer.
    A "Confirm" button (or ENTER) submits the selection.
    """
    N         = 7
    BTN_W     = max(130, (scr.W() - 80) // N)   # tile width
    BTN_H     = 110                               # tile height
    GAP       = 10
    total_w   = N * BTN_W + (N - 1) * GAP
    start_x   = scr.cx() - total_w // 2
    btn_y     = scr.cy() - BTN_H // 2 + 30       # vertical centre of screen

    # Confirm button
    conf_w, conf_h = 220, 52
    conf_rect = pygame.Rect(scr.cx() - conf_w // 2,
                            btn_y + BTN_H + 40, conf_w, conf_h)

    # Colours
    CLR_IDLE    = (210, 215, 225)
    CLR_HOVER   = (185, 195, 215)
    CLR_SEL     = (60,  110, 220)
    CLR_SEL_HV  = (80,  130, 240)
    CLR_BORDER  = (120, 125, 140)
    CLR_SEL_BRD = (30,   60, 160)
    CLR_CONF    = (50,  160,  60)
    CLR_CONF_HV = (70,  190,  80)
    CLR_CONF_BD = (20,   90,  30)

    def make_tile_rects():
        rects = []
        for i in range(N):
            x = start_x + i * (BTN_W + GAP)
            rects.append(pygame.Rect(x, btn_y, BTN_W, BTN_H))
        return rects

    def draw_tile(surf, rect, label, value, selected, hovered):
        is_sel = (selected == value)
        is_hov = hovered
        if is_sel:
            bg  = CLR_SEL_HV if is_hov else CLR_SEL
            brd = CLR_SEL_BRD
            tc  = (255, 255, 255)
        else:
            bg  = CLR_HOVER if is_hov else CLR_IDLE
            brd = CLR_BORDER
            tc  = TEXT_COLOR

        pygame.draw.rect(surf, bg,  rect, border_radius=10)
        pygame.draw.rect(surf, brd, rect, 2, border_radius=10)

        # Number (big, top half)
        num_f  = pygame.font.SysFont("DejaVu Sans", 36, bold=True)
        num_s  = num_f.render(str(value), True, tc)
        surf.blit(num_s, (rect.centerx - num_s.get_width()  // 2,
                          rect.y + 14))

        # Label text (small, bottom half, word-wrapped inside tile)
        lbl_f   = pygame.font.SysFont("DejaVu Sans", 13)
        words   = label.replace("\n", " ").split()
        lines   = []
        row     = ""
        for w in words:
            test = (row + " " + w).strip()
            if lbl_f.size(test)[0] <= BTN_W - 10:
                row = test
            else:
                if row:
                    lines.append(row)
                row = w
        if row:
            lines.append(row)

        ly = rect.y + 58
        for line in lines:
            ls = lbl_f.render(line, True, tc)
            surf.blit(ls, (rect.centerx - ls.get_width() // 2, ly))
            ly += 16

    def draw_confirm(surf, rect, hovered, enabled):
        if not enabled:
            bg, brd, tc = (180, 180, 180), (130, 130, 130), (220, 220, 220)
        elif hovered:
            bg, brd, tc = CLR_CONF_HV, CLR_CONF_BD, (255, 255, 255)
        else:
            bg, brd, tc = CLR_CONF, CLR_CONF_BD, (255, 255, 255)
        pygame.draw.rect(surf, bg,  rect, border_radius=10)
        pygame.draw.rect(surf, brd, rect, 2, border_radius=10)
        f = pygame.font.SysFont("DejaVu Sans", 22, bold=True)
        s = f.render("Bestätigen  ✓", True, tc)
        surf.blit(s, (rect.centerx - s.get_width()  // 2,
                      rect.centery - s.get_height() // 2))

    responses = []

    for q_idx, question in enumerate(LIKERT_QUESTIONS):
        selected  = None
        tile_rects = make_tile_rects()
        clock     = pygame.time.Clock()

        while True:
            mx, my   = pygame.mouse.get_pos()
            hov_tile = next((i for i, r in enumerate(tile_rects)
                             if r.collidepoint(mx, my)), None)
            hov_conf = conf_rect.collidepoint(mx, my)

            scr.clear()

            # Question number + text
            scr.draw_text(f"Frage {q_idx + 1} / {len(LIKERT_QUESTIONS)}",
                          22, 28, color=DIM_COLOR)
            scr.draw_text_wrapped(question, 30, 70, bold=True)

            # Scale anchors
            scr.draw_text("← stimme nicht zu", 18, btn_y + BTN_H + 10,
                          color=DIM_COLOR,
                          center_x=tile_rects[0].centerx)
            scr.draw_text("stimme zu →", 18, btn_y + BTN_H + 10,
                          color=DIM_COLOR,
                          center_x=tile_rects[-1].centerx)

            # Tiles
            for i, rect in enumerate(tile_rects):
                draw_tile(scr.surf, rect, LIKERT_LABELS[i],
                          i + 1, selected, hov_tile == i)

            # Confirm button
            draw_confirm(scr.surf, conf_rect,
                         hov_conf, selected is not None)

            # Hint
            hint = "Bitte eine Zahl anklicken, dann Bestätigen" if selected is None else                    f"Ausgewählt: {selected}  —  Bestätigen klicken oder ENTER drücken"
            scr.draw_text(hint, 20, scr.H() - 38, color=DIM_COLOR)

            scr.flip()
            clock.tick(60)

            for e in poll_events():
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    # tile click
                    for i, rect in enumerate(tile_rects):
                        if rect.collidepoint(e.pos):
                            selected = i + 1
                    # confirm click
                    if conf_rect.collidepoint(e.pos) and selected is not None:
                        goto_next = True

                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        raise KeyboardInterrupt
                    # number keys 1-7
                    name = pygame.key.name(e.key)
                    digit = None
                    if name in [str(i) for i in range(1, 8)]:
                        digit = int(name)
                    elif e.key in range(pygame.K_KP1, pygame.K_KP8):
                        digit = e.key - pygame.K_KP0
                    if digit and 1 <= digit <= 7:
                        selected = digit
                    # ENTER confirms if something selected
                    if e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        if selected is not None:
                            goto_next = True

            # Check if we should advance (use a flag to break cleanly)
            try:
                if goto_next:
                    break
            except UnboundLocalError:
                pass
            goto_next = False

        # Brief confirmation flash
        scr.clear()
        scr.draw_text(f"Frage {q_idx + 1} / {len(LIKERT_QUESTIONS)}",
                      22, 28, color=DIM_COLOR)
        scr.draw_text_wrapped(question, 30, 70, bold=True)
        for i, rect in enumerate(tile_rects):
            draw_tile(scr.surf, rect, LIKERT_LABELS[i],
                      i + 1, selected, False)
        draw_confirm(scr.surf, conf_rect, False, True)
        scr.flip()
        time.sleep(0.4)

        responses.append(selected)
        goto_next = False   # reset for next question

    likert_responses.append({
        'participant_id': participant_id,
        'block':          block_idx + 1,
        'condition':      condition,
        'q1_love_again':  responses[0],
        'q2_well_matched':responses[1],
        'q3_thrilled':    responses[2],
        'timestamp':      datetime.now().isoformat(),
    })


# ============================================================================
# BLOCK
# ============================================================================

def run_block(scr, condition, starting_level, block_idx,
              participant_id, task_results):
    if condition == 'B':
        level = block_starting_level = 1
    elif condition == 'F':
        level = block_starting_level = starting_level
    else:   # 'O'
        level = block_starting_level = starting_level + 3

    cons_correct   = 0
    cons_incorrect = 0
    cname          = CONDITIONS[condition]
    block_info     = f"Block {block_idx + 1}/12 – {cname}"
    print(f"\nBlock {block_idx + 1} – {cname}  (start level {level})")

    block_start   = time.monotonic()
    trial_count   = 0
    prefetched    = None

    while (time.monotonic() - block_start) < BLOCK_DURATION:
        trial_count += 1

        # use prefetched task if available
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
            scr, expression, block_info, block_start, condition)

        task_results.append({
            'participant_id':    participant_id,
            'block':             block_idx + 1,
            'condition':         condition,
            'difficulty_level':  level,
            'expression':        expression['text'],
            'correct_answer':    expression['answer'],
            'user_answer':       user_answer,
            'is_correct':        is_correct,
            'is_timeout':        timed_out,
            'response_time_ms':  round(rt_ms, 1),
            'timestamp':         datetime.now().isoformat(),
        })

        if condition in ('F', 'O'):
            # Timeouts count as incorrect (no answer = wrong answer).
            # For Flow the minimum level is always 1 (fully flexible up and down).
            # For Overload the minimum is block_starting_level (stays challenging).
            answered_correctly = is_correct and not timed_out
            level, cons_correct, cons_incorrect = update_difficulty(
                answered_correctly, level, cons_correct, cons_incorrect,
                condition, block_starting_level)

        # pre-generate next task for placeholder
        if (time.monotonic() - block_start) < BLOCK_DURATION:
            if condition == 'B':
                next_task = create_boredom_task()
            elif condition == 'F':
                next_task = create_flow_task(level)
            else:
                next_task = create_overload_task(level)
            prefetched = next_task
            show_break(scr, block_info,
                       make_placeholder(expression['numbers']),
                       next_numbers=next_task['numbers'])

    print(f"Block {block_idx + 1} abgeschlossen: {trial_count} Durchgänge, Endniveau: {level}")


# ============================================================================
# PRACTICE BLOCK
# ============================================================================

def run_practice_block(scr, condition_type, duration_sec, start_level=1):
    """Returns list of levels (for calibration) or [] for boredom warm-up."""
    level          = max(1, start_level)
    cons_correct   = 0
    cons_incorrect = 0
    levels         = []
    prefetched     = None
    block_start    = time.monotonic()

    while (time.monotonic() - block_start) < duration_sec:
        if prefetched is not None:
            expression = prefetched
            prefetched = None
        elif condition_type == 'boredom':
            expression = create_boredom_task()
        else:
            expression = create_flow_task(level)

        # Stop immediately if time already expired before this trial starts
        if (time.monotonic() - block_start) >= duration_sec:
            break

        _, is_correct, timed_out, _ = run_trial(
            scr, expression, "Übung", block_start, condition_type,
            block_duration=duration_sec)

        if condition_type == 'flow':
            levels.append(level)
            # Timeouts count as incorrect (no answer = wrong),
            # matching the same 2-consecutive rule as the main experiment.
            answered_correctly = is_correct and not timed_out
            if answered_correctly:
                cons_correct   += 1
                cons_incorrect  = 0
                if cons_correct >= 2:
                    level        = level + 1
                    cons_correct = 0
                    print(f"  Übung ✓✓ → Niveau {level}")
            else:
                cons_incorrect += 1
                cons_correct    = 0
                if cons_incorrect >= 2:
                    level          = max(1, level - 1)
                    cons_incorrect = 0
                    print(f"  Übung ✗✗ → Niveau {level}")

        # break with placeholder
        if (time.monotonic() - block_start) < duration_sec:
            if condition_type == 'boredom':
                next_task = create_boredom_task()
            else:
                next_task = create_flow_task(level)
            prefetched = next_task
            show_break(scr, "Übung",
                       make_placeholder(expression['numbers']),
                       next_numbers=next_task['numbers'])

    return levels


# ============================================================================
# DATA SAVING
# ============================================================================

def save_data(participant_id, task_results, likert_responses):
    os.makedirs('data', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    if task_results:
        fn = f"data/{participant_id}_task_{ts}.csv"
        pd.DataFrame(task_results).to_csv(fn, index=False)
        print(f"✓ Aufgabendaten gespeichert: {fn}")

    if likert_responses:
        fn = f"data/{participant_id}_likert_{ts}.csv"
        pd.DataFrame(likert_responses).to_csv(fn, index=False)
        print(f"✓ Likert-Daten gespeichert: {fn}")


# ============================================================================
# SETUP DIALOG  (pure pygame — no wx/Qt needed)
# ============================================================================

FIELD_BG        = (245, 245, 245)
FIELD_ACTIVE_BG = (255, 255, 220)
FIELD_BORDER    = (180, 180, 180)
ACTIVE_BORDER   = (80,  80, 200)
CHECK_ON        = (60, 160,  60)
CHECK_OFF       = (200, 200, 200)
BTN_COLOR       = (60, 120, 220)
BTN_TEXT        = (255, 255, 255)
DIALOG_BG       = (240, 240, 240)
HEADER_COLOR    = (40,  40, 120)


def setup_dialog():
    """
    Show a self-contained pygame setup dialog.
    Returns (pid, session, run_fam, run_eval, run_main, start_level).
    """
    pygame.init()
    DW, DH   = 580, 580
    surf     = pygame.display.set_mode((DW, DH))
    pygame.display.set_caption("Mentales Rechnen – Einstellungen")

    def fnt(size, bold=False):
        return pygame.font.SysFont("DejaVu Sans", size, bold=bold)

    def draw_text(text, size, x, y, color=TEXT_COLOR, bold=False, surf=surf):
        s = fnt(size, bold).render(text, True, color)
        surf.blit(s, (x, y))
        return s.get_width(), s.get_height()

    def draw_centered(text, size, y, color=TEXT_COLOR, bold=False):
        s = fnt(size, bold).render(text, True, color)
        surf.blit(s, (DW // 2 - s.get_width() // 2, y))

    def _draw_dialog_metallic(target_surf, rect, active=False, radius=6):
        """Metallic silver input field for the setup dialog."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        bands = []
        for i in range(h):
            t = i / max(h - 1, 1)
            if t < 0.18:
                v = int(230 + (252 - 230) * (t / 0.18))
            elif t < 0.45:
                v = int(252 - (252 - 170) * ((t - 0.18) / 0.27))
            elif t < 0.72:
                v = int(170 + (190 - 170) * ((t - 0.45) / 0.27))
            else:
                v = int(190 + (225 - 190) * ((t - 0.72) / 0.28))
            bands.append((max(0, min(255, v - 8)),
                          max(0, min(255, v - 4)),
                          max(0, min(255, v + 8))))
        gs = pygame.Surface((w, h), pygame.SRCALPHA)
        for i, c in enumerate(bands):
            pygame.draw.line(gs, c, (0, i), (w, i))
        ms = pygame.Surface((w, h), pygame.SRCALPHA)
        ms.fill((0, 0, 0, 0))
        pygame.draw.rect(ms, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
        gs.blit(ms, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        target_surf.blit(gs, (x, y))
        # rim: active = blue glow, inactive = dark grey
        rim = (60, 100, 220) if active else (90, 95, 108)
        rim_w = 2 if not active else 2
        pygame.draw.rect(target_surf, rim, rect, rim_w, border_radius=radius)
        # top-left glint
        inner = pygame.Rect(x + 2, y + 2, w - 4, h - 4)
        pygame.draw.line(target_surf, (255, 255, 255),
                         (inner.x + radius, inner.y), (inner.right - radius, inner.y), 1)
        pygame.draw.line(target_surf, (255, 255, 255),
                         (inner.x, inner.y + radius), (inner.x, inner.bottom - radius), 1)
        pygame.draw.line(target_surf, (105, 110, 120),
                         (inner.x + radius, inner.bottom),
                         (inner.right - radius, inner.bottom), 1)
        if active:
            # subtle blue inner highlight
            pygame.draw.rect(target_surf, (180, 200, 255, 60), rect, 1, border_radius=radius)

    def _draw_dialog_button(target_surf, rect, label, font_fn):
        """Metallic blue-steel button with glint."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height
        # gradient: bright top → mid deep blue → slightly lighter bottom
        for i in range(h):
            t = i / max(h - 1, 1)
            if t < 0.3:
                r = int(55  + (80  - 55)  * (t / 0.3))
                g = int(110 + (130 - 110) * (t / 0.3))
                b = int(210 + (230 - 210) * (t / 0.3))
            elif t < 0.6:
                r = int(80  - (80  - 40)  * ((t - 0.3) / 0.3))
                g = int(130 - (130 - 90)  * ((t - 0.3) / 0.3))
                b = int(230 - (230 - 180) * ((t - 0.3) / 0.3))
            else:
                r = int(40  + (70  - 40)  * ((t - 0.6) / 0.4))
                g = int(90  + (120 - 90)  * ((t - 0.6) / 0.4))
                b = int(180 + (210 - 180) * ((t - 0.6) / 0.4))
            pygame.draw.line(target_surf, (r, g, b), (x, y + i), (x + w, y + i))
        # clip corners by drawing rounded border mask
        pygame.draw.rect(target_surf, (30, 70, 170), rect, 2, border_radius=10)
        # top glint
        pygame.draw.line(target_surf, (160, 195, 255),
                         (x + 12, y + 3), (x + w - 12, y + 3), 1)
        # label
        f  = font_fn(22, bold=True)
        s  = f.render(label, True, (240, 248, 255))
        # subtle drop shadow
        sh = f.render(label, True, (20, 50, 130))
        target_surf.blit(sh, (rect.centerx - s.get_width() // 2 + 1,
                              rect.centery - s.get_height() // 2 + 1))
        target_surf.blit(s,  (rect.centerx - s.get_width() // 2,
                              rect.centery - s.get_height() // 2))

    # ── layout ────────────────────────────────────────────────────────────────
    PAD   = 36
    LH    = 58       # row height
    IH    = 46       # input box height (taller for readability)
    IW    = 260      # input box width
    LX    = PAD      # label x
    IX    = 240      # input / control x
    y0    = 110      # first row y

    fields = [
        {'label': 'Versuchsperson-ID', 'value': '',    'type': 'text',  'default': 'test'},
        {'label': 'Sitzung',         'value': '001', 'type': 'text',  'default': '001'},
    ]
    checks = [
        {'label': 'Familiarisierung',     'value': True},
        {'label': 'Kompetenzerfassung',   'value': True},
        {'label': 'Hauptexperiment',      'value': True},
    ]
    level_field = {'label': 'Startschwierigkeitsgrad', 'value': '1', 'type': 'text', 'default': '1'}

    active_field = 0   # index into fields (or None)
    clock        = pygame.time.Clock()
    cursor_tick  = 0

    # rects for hit-testing
    field_rects = []
    check_rects = []
    level_rect  = None
    btn_rect    = pygame.Rect(DW // 2 - 110, DH - 70, 220, 52)

    running = True
    while running:
        surf.fill(DIALOG_BG)

        # ── header ────────────────────────────────────────────────────────────
        pygame.draw.rect(surf, HEADER_COLOR, (0, 0, DW, 72))
        draw_centered("Mentales Rechnen – Paradigma", 22, 14,
                      color=(255, 255, 255), bold=True)
        draw_centered("Versuchseinstellungen", 16, 44, color=(200, 210, 255))

        # ── text fields ───────────────────────────────────────────────────────
        field_rects.clear()
        for i, f in enumerate(fields):
            y = y0 + i * LH
            draw_text(f['label'], 18, LX, y + 9)
            rect = pygame.Rect(IX, y, IW, IH)
            field_rects.append(rect)
            is_active = (active_field == i)
            # Metallic silver field
            _draw_dialog_metallic(surf, rect, active=is_active, radius=6)
            # cursor blink
            txt = f['value']
            if is_active and (cursor_tick // 30) % 2 == 0:
                txt += '|'
            txt_color = TEXT_COLOR if f['value'] else (160, 160, 160)
            draw_text(txt, 19, rect.x + 10, rect.y + (IH - 22) // 2, color=txt_color)

        # ── checkboxes ────────────────────────────────────────────────────────
        check_rects.clear()
        cy_start = y0 + len(fields) * LH + 16
        for i, c in enumerate(checks):
            y    = cy_start + i * LH
            crect = pygame.Rect(IX, y + 6, 26, 26)
            check_rects.append(crect)
            draw_text(c['label'], 18, LX, y + 9)
            pygame.draw.rect(surf, CHECK_ON if c['value'] else CHECK_OFF, crect)
            pygame.draw.rect(surf, (100, 100, 100), crect, 2)
            if c['value']:
                # draw tick
                pygame.draw.line(surf, (255,255,255),
                                 (crect.x+4,  crect.y+13),
                                 (crect.x+10, crect.y+19), 3)
                pygame.draw.line(surf, (255,255,255),
                                 (crect.x+10, crect.y+19),
                                 (crect.x+22, crect.y+6),  3)

        # ── starting level (only when skill eval is off) ───────────────────
        if not checks[1]['value']:
            y     = cy_start + len(checks) * LH + 6
            draw_text(level_field['label'], 18, LX, y + 9)
            lrect = pygame.Rect(IX, y, 80, IH)
            level_rect = lrect
            is_active  = (active_field == len(fields))   # field index after text fields
            _draw_dialog_metallic(surf, lrect, active=is_active, radius=6)
            txt = level_field['value']
            if is_active and (cursor_tick // 30) % 2 == 0:
                txt += '|'
            draw_text(txt, 19, lrect.x + 10, lrect.y + (IH - 22) // 2)
        else:
            level_rect = None
            if active_field == len(fields):
                active_field = 0

        # ── OK button — metallic blue ─────────────────────────────────────────
        _draw_dialog_button(surf, btn_rect, "Experiment starten", fnt)

        pygame.display.flip()
        cursor_tick += 1
        clock.tick(60)

        # ── events ────────────────────────────────────────────────────────────
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                clicked = False
                for i, r in enumerate(field_rects):
                    if r.collidepoint(e.pos):
                        active_field = i
                        clicked = True
                for i, r in enumerate(check_rects):
                    if r.collidepoint(e.pos):
                        checks[i]['value'] = not checks[i]['value']
                        clicked = True
                if level_rect and level_rect.collidepoint(e.pos):
                    active_field = len(fields)
                    clicked = True
                if btn_rect.collidepoint(e.pos):
                    running = False
                if not clicked:
                    active_field = None

            elif e.type == pygame.KEYDOWN:
                # TAB cycles fields
                if e.key == pygame.K_TAB:
                    n_fields = len(fields) + (1 if not checks[1]['value'] else 0)
                    active_field = ((active_field or 0) + 1) % n_fields
                elif e.key == pygame.K_RETURN or e.key == pygame.K_KP_ENTER:
                    running = False
                elif e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit(0)
                elif active_field is not None:
                    # which field is active?
                    if active_field < len(fields):
                        f = fields[active_field]
                        if e.key == pygame.K_BACKSPACE:
                            f['value'] = f['value'][:-1]
                        elif e.unicode.isprintable() and len(f['value']) < 32:
                            f['value'] += e.unicode
                    elif active_field == len(fields):
                        # level field — digits only
                        if e.key == pygame.K_BACKSPACE:
                            level_field['value'] = level_field['value'][:-1]
                        elif e.unicode.isdigit() and len(level_field['value']) < 3:
                            level_field['value'] += e.unicode

    # ── collect results ───────────────────────────────────────────────────────
    pid         = fields[0]['value'].strip() or fields[0]['default']
    session     = fields[1]['value'].strip() or fields[1]['default']
    run_fam     = checks[0]['value']
    run_eval    = checks[1]['value']
    run_main    = checks[2]['value']
    start_level = int(level_field['value']) if level_field['value'].isdigit() else 1

    # close dialog window — main() will open the experiment window
    pygame.display.quit()
    pygame.quit()

    return pid, session, run_fam, run_eval, run_main, start_level


# ============================================================================
# MAIN
# ============================================================================

def main():
    pid, session, run_fam, run_eval, run_main, starting_level = setup_dialog()

    scr            = Screen()
    task_results   = []
    likert_responses = []

    try:
        # ── Familiarization ───────────────────────────────────────────────────
        if run_fam:
            print("\n=== Familiarisierung (3 min Aufwärmen) ===")
            show_instruction(scr,
                "Familiarisierung\n\n"
                "Sie üben jetzt 3 Minuten lang einfache Additionsaufgaben.\n\n"
                "Geben Sie Ihr Ergebnis ein und bestätigen Sie mit ENTER.\n"
                "Drücken Sie die LEERTASTE zum Starten.")
            run_practice_block(scr, 'boredom', 180)
            show_instruction(scr,
                "Familiarisierung abgeschlossen!\n\n"
                "Drücken Sie die LEERTASTE zum Fortfahren.")

        # ── Skill Evaluation ─────────────────────────────────────────────────
        if run_eval:
            print("\n=== Kompetenzerfassung (5 min) ===")
            show_instruction(scr,
                "Kompetenzerfassung\n\n"
                "Wir schätzen jetzt Ihren Startschwierigkeitsgrad ein.\n"
                "Die Aufgaben werden schwerer, wenn Sie richtig antworten.\n\n"
                "Drücken Sie die LEERTASTE zum Starten.")
            levels = run_practice_block(scr, 'flow', 300, start_level=starting_level)
            if levels:
                last_quarter   = levels[-max(1, len(levels) // 4):]
                starting_level = max(1, int(np.mean(last_quarter)))
            else:
                starting_level = 1
            print(f"Geschätzter Startschwierigkeitsgrad: {starting_level}")
            show_instruction(scr,
                f"Kompetenzerfassung abgeschlossen!\n\n"
                f"Ihr geschätzter Startschwierigkeitsgrad: {starting_level}\n\n"
                f"Drücken Sie die LEERTASTE zum Fortfahren.")

        if not run_main:
            print("=== Abgeschlossen (kein Hauptexperiment gewählt) ===")
            pygame.quit()
            return

        # ── Main Experiment ───────────────────────────────────────────────────
        sequence = random.choice(SEQUENCES)
        print(f"\n=== Hauptexperiment ===")
        print(f"Versuchsperson: {pid}  |  Startschwierigkeitsgrad: {starting_level}")
        print(f"Sequenz: {'-'.join(sequence)}")

        show_instruction(scr,
            "Hauptexperiment\n\n"
            "Sie bearbeiten 12 Blöcke mit Rechenaufgaben.\n"
            "Nach jedem Block beantworten Sie 3 kurze Fragen.\n\n"
            "Geben Sie Ihr Ergebnis ein und bestätigen Sie mit ENTER.\n"
            "ESC speichert und beendet das Experiment jederzeit.\n\n"
            "Drücken Sie die LEERTASTE zum Starten.")

        for block_idx, condition in enumerate(sequence):
            if block_idx > 0:
                show_rest(scr)

            run_block(scr, condition, starting_level, block_idx,
                      pid, task_results)
            run_likert(scr, condition, block_idx, pid, likert_responses)

        show_instruction(scr,
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
        pygame.quit()


if __name__ == '__main__':
    main()
