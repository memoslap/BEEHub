#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
APPL – Set 2 (PsychoPy)
=========================
Associative Picture-Pseudoword Learning – full experiment, Set 2.

Identical structure to Set 1. Only LEARNING/CONTROL stimulus lists differ,
and folder layout differs: bubbles/, learning/, and control/ live directly
under Set_2/ (not inside a Stimuli/ subfolder).

Folder layout (relative to this script)
-----------------------------------------
bubbles/    hello.jpg  learning.jpg  control.jpg  bye.jpg
learning/   PICTURE_*.jpg   (28 items)
control/    PICTURE_*.jpg   (28 items)
data/        output CSV + log
instr_1*.jpg / instr_21.jpg / instr_3*.jpg  (instruction slides at script root)

Trial timing  ← same as Set 1
------------
  Phase 1  2.5 s  Image (600×600) centre + pseudoword below (pos 0,−400).
                  Keys 1 (Ja) and 2 (Nein) accepted any time; window completes.
  Phase 2  2.0 s  Feedback text only:
                      "Korrekt/Falsch/Zu spät, das ist {correct_word}"
"""

import os, random, datetime, csv, glob
from psychopy import visual, core, event, gui, logging

# ── Paths ──────────────────────────────────────────────────────────────────────
# NOTE: Set 2 has no Stimuli/ subfolder – bubbles, learning, control are at root.
_HERE = os.path.dirname(os.path.abspath(__file__))
def _p(*parts): return os.path.join(_HERE, *parts)

STIM_DIR    = _HERE          # images referenced as 'learning/PICTURE_x.jpg' etc.
BUBBLES_DIR = _p('bubbles')
LEARN_DIR   = _p('learning')
CTRL_DIR    = _p('control')
AFC_DIR     = _p('AFC')
DATA_DIR    = _p('data')

# ── Timing ─────────────────────────────────────────────────────────────────────
STIM_DUR     = 2.500
FEEDBACK_DUR = 2.000
FIX_DUR      = 4.500

KEY_YES = '1'
KEY_NO  = '2'

# ── Dialog ─────────────────────────────────────────────────────────────────────
exp_info = {'subject': '001', 'session': '1', 'fmri_mode': False}
dlg = gui.DlgFromDict(exp_info, title='APPL Experiment – Set 2', sortKeys=False)
if not dlg.OK:
    core.quit()

participant = exp_info['subject']
session     = exp_info['session']
fmri_mode   = exp_info['fmri_mode']

os.makedirs(DATA_DIR, exist_ok=True)
date_str  = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
csv_fname = _p('data', f"sub-{participant}_ses-{session}_{date_str}_APPL_Set2.csv")
log_fname = _p('data', f"sub-{participant}_ses-{session}_{date_str}_APPL_Set2.log")

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
key_label_1   = visual.TextStim(win, text='1 = Ja',   color='white', height=40,
                                pos=(-340, -490))
key_label_2   = visual.TextStim(win, text='2 = Nein', color='white', height=40,
                                pos=( 340, -490))

# ── CSV writer ─────────────────────────────────────────────────────────────────
_csv_file   = open(csv_fname, 'w', newline='', encoding='utf-8')
_csv_writer = csv.writer(_csv_file)
_csv_writer.writerow(['participant', 'session', 'set',
                      'phase', 'block_run', 'block_num', 'learning_stage', 'trial',
                      'image', 'word', 'correct_word', 'condition',
                      'response', 'correct', 'rt', 'onset_time'])

def write_row(**kw):
    _csv_writer.writerow([participant, session, '2',
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
    key_label = 'LEERTASTE' if advance_key == 'space' else f'Taste {advance_key}'
    visual.TextStim(win, text=f"{footer}    [{key_label} -> weiter]",
                    color='white', height=22,
                    pos=(0, -295), wrapWidth=1100).draw()
    win.flip()
    event.waitKeys(keyList=[advance_key, 'escape']); check_quit()


def show_instructions_part1():
    """7 slides explaining the learning task."""
    show_text_slide(
        title="Willkommen – APPL-Studie",
        body=(
            "Vielen Dank für Ihre Teilnahme!\n\n"
            "In dieser Studie werden Sie Bilder kennenlernen,\n"
            "die jeweils mit einem erfundenen Wort verbunden sind.\n\n"
            "Ihre Aufgabe ist es, sich zu merken,\n"
            "welches Wort zu welchem Bild gehört."
        ),
        footer="Folie 1 / 7"
    )
    show_text_slide(
        title="Ablauf der Aufgabe",
        body=(
            "Sie sehen nacheinander Bilder auf dem Bildschirm.\n\n"
            "Unter jedem Bild erscheint ein Wort.\n\n"
            "Ihre Aufgabe:\n"
            "  Entscheiden Sie, ob das angezeigte Wort\n"
            "  das RICHTIGE Wort für dieses Bild ist."
        ),
        footer="Folie 2 / 7"
    )
    show_text_slide(
        title="Tasten",
        body=(
            "Drücken Sie:\n\n"
            "       1  ->  JA,  das ist das richtige Wort\n\n"
            "       2  ->  NEIN,  das ist nicht das richtige Wort\n\n"
            "Sie haben 2,5 Sekunden Zeit für Ihre Antwort.\n"
            "Antworten Sie so schnell und genau wie möglich."
        ),
        footer="Folie 3 / 7"
    )
    show_text_slide(
        title="Rückmeldung",
        body=(
            "Nach jeder Antwort erhalten Sie eine Rückmeldung:\n\n"
            "  'Korrekt, das ist [Wort]'  – Ihre Antwort war richtig\n\n"
            "  'Falsch, das ist [Wort]'   – Ihre Antwort war falsch\n\n"
            "  'Zu spät, das ist [Wort]'  – keine Antwort in der Zeit\n\n"
            "Nutzen Sie die Rückmeldung, um das Wort zu lernen."
        ),
        footer="Folie 4 / 7"
    )
    show_text_slide(
        title="Lernphasen",
        body=(
            "Jedes Bild wird mehrmals gezeigt.\n\n"
            "Beim ersten Mal kennen Sie das richtige Wort noch nicht –\n"
            "das ist normal. Lernen Sie durch die Rückmeldungen.\n\n"
            "Mit jeder Wiederholung sollte es Ihnen leichter fallen,\n"
            "das richtige Wort zu erkennen."
        ),
        footer="Folie 5 / 7"
    )
    show_text_slide(
        title="Kontrollaufgabe",
        body=(
            "Zwischendurch gibt es eine Kontrollaufgabe.\n\n"
            "Dort sehen Sie bekannte Objekte mit echten deutschen Wörtern.\n\n"
            "Auch hier entscheiden Sie mit  1  (Ja) und  2  (Nein),\n"
            "ob das angezeigte Wort zum Bild passt.\n\n"
            "Die Aufgabe funktioniert genauso wie die Lernaufgabe."
        ),
        footer="Folie 6 / 7"
    )
    show_text_slide(
        title="Bereit?",
        body=(
            "Sie sind nun bereit, mit der Aufgabe zu beginnen.\n\n"
            "Denken Sie daran:\n"
            "  1 = JA   (richtiges Wort)\n"
            "  2 = NEIN (falsches Wort)\n\n"
            "Antworten Sie innerhalb von 2,5 Sekunden.\n\n"
            "Viel Erfolg!"
        ),
        footer="Folie 7 / 7",
        advance_key='space'
    )


def show_instructions_part2():
    """Single slide shown before the main learning phase begins."""
    show_text_slide(
        title="Die Aufgabe beginnt jetzt",
        body=(
            "Die Lernaufgabe beginnt gleich.\n\n"
            "Zur Erinnerung:\n\n"
            "       1  ->  JA,  das ist das richtige Wort\n\n"
            "       2  ->  NEIN,  das ist nicht das richtige Wort\n\n"
            "Sie haben 2,5 Sekunden pro Bild."
        ),
        footer="Drücken Sie die LEERTASTE, wenn Sie bereit sind.",
        advance_key='space'
    )


def show_instructions_part3():
    """4 slides for the AFC (recognition) test."""
    show_text_slide(
        title="Gedächtnistest",
        body=(
            "Sie haben nun alle Lernblöcke abgeschlossen.\n\n"
            "Jetzt folgt ein Gedächtnistest.\n\n"
            "Ihnen werden Bilder gezeigt, die Sie zuvor gesehen haben.\n"
            "Zu jedem Bild werden drei Wörter angezeigt."
        ),
        footer="Folie 1 / 4"
    )
    show_text_slide(
        title="Gedächtnistest – Ihre Aufgabe",
        body=(
            "Wählen Sie das Wort, das während der Lernphase\n"
            "zu diesem Bild gehörte.\n\n"
            "Drücken Sie:\n\n"
            "       1  ->  linkes Wort\n"
            "       2  ->  mittleres Wort\n"
            "       3  ->  rechtes Wort"
        ),
        footer="Folie 2 / 4"
    )
    show_text_slide(
        title="Gedächtnistest – Hinweise",
        body=(
            "Es gibt keine Zeitbeschränkung.\n\n"
            "Antworten Sie so genau wie möglich.\n\n"
            "Wenn Sie unsicher sind, raten Sie –\n"
            "lassen Sie kein Bild unbeantwortet."
        ),
        footer="Folie 3 / 4"
    )
    show_text_slide(
        title="Gedächtnistest – Bereit?",
        body=(
            "Der Gedächtnistest beginnt gleich.\n\n"
            "Zur Erinnerung:\n\n"
            "       1  ->  linkes Wort\n"
            "       2  ->  mittleres Wort\n"
            "       3  ->  rechtes Wort\n\n"
            "Viel Erfolg!"
        ),
        footer="Drücken Sie die LEERTASTE, um zu beginnen.",
        advance_key='space'
    )

def get_stimuli(directory):
    files = sorted(glob.glob(os.path.join(directory, '*.jpg')) +
                   glob.glob(os.path.join(directory, '*.JPG')))
    return [f for f in files
            if not os.path.basename(f).lower().startswith('thumbs')]

# ── Stimulus lists – Set 2 ─────────────────────────────────────────────────────
LEARNING = [
    # Block 1 (7 items)
    {'pic': 'learning/PICTURE_400.jpg', 'words': ['Lopfer',  'Loptem',    'Lopdor',   'Lopmig',   'Lopter']},
    {'pic': 'learning/PICTURE_402.jpg', 'words': ['Resar',   'Rerod',     'Regan',    'Reper',    'Remert']},
    {'pic': 'learning/PICTURE_405.jpg', 'words': ['Nomtap',  'Nomgan',    'Nomtun',   'Nomzerl',  'Nomser']},
    {'pic': 'learning/PICTURE_462.jpg', 'words': ['Jamip',   'Jamun',     'Jakel',    'Jaser',    'Jasull']},
    {'pic': 'learning/PICTURE_53.jpg',  'words': ['Knele',   'Knera',     'Knefe',    'Knetam',   'Knesam']},
    {'pic': 'learning/PICTURE_216.jpg', 'words': ['Tignam',  'Tigfe',     'Tigdon',   'Tigdam',   'Tigmer']},
    {'pic': 'learning/PICTURE_21.jpg',  'words': ['Kr\u00fckta', 'Kr\u00fckel', 'Kr\u00fcktem', 'Kr\u00fcklass', 'Kr\u00fckmig']},
    # Block 2 (7 items)
    {'pic': 'learning/PICTURE_480.jpg', 'words': ['Zamet',   'Zate',      'Zabig',    'Zabelt',   'Zatir']},
    {'pic': 'learning/PICTURE_488.jpg', 'words': ['Jehler',  'Jehrig',    'Jehmel',   'Jehtir',   'Jehse']},
    {'pic': 'learning/PICTURE_508.jpg', 'words': ['Zerbe',   'Zermel',    'Zerse',    'Zerpet',   'Zertock']},
    {'pic': 'learning/PICTURE_15.jpg',  'words': ['Joten',   'Joper',     'Josant',   'Jotolt',   'Jota']},
    {'pic': 'learning/PICTURE_695.jpg', 'words': ['Munem',   'Muschot',   'Mufi',     'Mugir',    'Mupat']},
    {'pic': 'learning/PICTURE_703.jpg', 'words': ['Knusap',  'Knufi',     'Knufeg',   'Knupat',   'Knuler']},
    {'pic': 'learning/PICTURE_95.jpg',  'words': ['Klenter', 'Klentant',  'Klenban',  'Klenta',   'Klenfalt']},
    # Block 3 (7 items)
    {'pic': 'learning/PICTURE_576.jpg', 'words': ['Sch\u00f6le',  'Sch\u00f6lte',  'Sch\u00f6lse',  'Sch\u00f6lme',  'Sch\u00f6lter']},
    {'pic': 'learning/PICTURE_581.jpg', 'words': ['Zampe',   'Zamse',     'Zamram',   'Zambel',   'Zamler']},
    {'pic': 'learning/PICTURE_52.jpg',  'words': ['Geiten',  'Geibel',    'Geiner',   'Geiper',   'Geitel']},
    {'pic': 'learning/PICTURE_594.jpg', 'words': ['G\u00fcrbas', 'G\u00fcrzer', 'G\u00fcrter', 'G\u00fcrbel', 'G\u00fcrse']},
    {'pic': 'learning/PICTURE_297.jpg', 'words': ['Eume',    'Eupis',     'Euko',     'Eudet',    'Eutaf']},
    {'pic': 'learning/PICTURE_23.jpg',  'words': ['Koptan',  'Koptel',    'Koptur',   'Kopster',  'Kopsel']},
    {'pic': 'learning/PICTURE_605.jpg', 'words': ['Kegan',   'Ketan',     'Ketosch',  'Keton',    'Keteik']},
    # Block 4 (7 items)
    {'pic': 'learning/PICTURE_247.jpg', 'words': ['Stise',   'Stitons',   'Stisin',   'Stigit',   'Stisum']},
    {'pic': 'learning/PICTURE_43.jpg',  'words': ['Finser',  'Finsin',    'Finlas',   'Finsum',   'Finges']},
    {'pic': 'learning/PICTURE_610.jpg', 'words': ['Seise',   'Seimer',    'Seitos',   'Seiges',   'Seitu']},
    {'pic': 'learning/PICTURE_741.jpg', 'words': ['Soktau',  'Soklet',    'Soktal',   'Sokma',    'Sokbat']},
    {'pic': 'learning/PICTURE_235.jpg', 'words': ['Efdi',    'Efter',     'Efto',     'Efser',    'Efnel']},
    {'pic': 'learning/PICTURE_720.jpg', 'words': ['Tulser',  'Tulte',     'Tulpos',   'Tulber',   'Tuldet']},
    {'pic': 'learning/PICTURE_599.jpg', 'words': ['Klotel',  'Klosal',    'Klotons',  'Klobat',   'Kloger']},
]

CONTROL = [
    # ctrl1 (14 items)
    {'pic': 'control/PICTURE_2.jpg',   'words': ['Reifen',    'Tiger',      'Kompass']},
    {'pic': 'control/PICTURE_98.jpg',  'words': ['Tiger',     'Kompass',    'Gewehr']},
    {'pic': 'control/PICTURE_292.jpg', 'words': ['Kompass',   'Gewehr',     'Tunnel']},
    {'pic': 'control/PICTURE_645.jpg', 'words': ['Gewehr',    'Tunnel',     'Reifen']},
    {'pic': 'control/PICTURE_286.jpg', 'words': ['Tunnel',    'Reifen',     'Tiger']},
    {'pic': 'control/PICTURE_733.jpg', 'words': ['Brille',    'Vogel',      'Wolle']},
    {'pic': 'control/PICTURE_430.jpg', 'words': ['Vogel',     'Wolle',      'Hose']},
    {'pic': 'control/PICTURE_134.jpg', 'words': ['Wolle',     'Hose',       'Bagger']},
    {'pic': 'control/PICTURE_718.jpg', 'words': ['Hose',      'Bagger',     'Brille']},
    {'pic': 'control/PICTURE_746.jpg', 'words': ['Kegel',     'M\u00f6we',  'Flagge']},
    {'pic': 'control/PICTURE_220.jpg', 'words': ['M\u00f6we', 'Flagge',     'Blume']},
    {'pic': 'control/PICTURE_295.jpg', 'words': ['Flagge',    'Blume',      'Kegel']},
    {'pic': 'control/PICTURE_312.jpg', 'words': ['Blume',     'Kegel',      'M\u00f6we']},
    {'pic': 'control/PICTURE_731.jpg', 'words': ['Bagger',    'Brille',     'Vogel']},
    # ctrl2 (14 items)
    {'pic': 'control/PICTURE_549.jpg', 'words': ['Schlange',  'Parf\u00fcm','Bibel']},
    {'pic': 'control/PICTURE_314.jpg', 'words': ['Parf\u00fcm','Bibel',     'Tasche']},
    {'pic': 'control/PICTURE_350.jpg', 'words': ['Bibel',     'Tasche',     'Vorhang']},
    {'pic': 'control/PICTURE_388.jpg', 'words': ['Tasche',    'Vorhang',    'Schlange']},
    {'pic': 'control/PICTURE_418.jpg', 'words': ['Vorhang',   'Schlange',   'Parf\u00fcm']},
    {'pic': 'control/PICTURE_476.jpg', 'words': ['Sch\u00fcrze','Nagel',    'Apfel']},
    {'pic': 'control/PICTURE_485.jpg', 'words': ['Nagel',     'Apfel',      'Tasse']},
    {'pic': 'control/PICTURE_552.jpg', 'words': ['Apfel',     'Tasse',      'S\u00e4ule']},
    {'pic': 'control/PICTURE_498.jpg', 'words': ['Tasse',     'S\u00e4ule', 'Sch\u00fcrze']},
    {'pic': 'control/PICTURE_386.jpg', 'words': ['Bombe',     'Maske',      'Spiegel']},
    {'pic': 'control/PICTURE_84.jpg',  'words': ['Maske',     'Spiegel',    'Schlitten']},
    {'pic': 'control/PICTURE_340.jpg', 'words': ['Spiegel',   'Schlitten',  'Bombe']},
    {'pic': 'control/PICTURE_625.jpg', 'words': ['Schlitten', 'Bombe',      'Maske']},
    {'pic': 'control/PICTURE_663.jpg', 'words': ['S\u00e4ule','Sch\u00fcrze','Nagel']},
]

# ── Trial builder ──────────────────────────────────────────────────────────────

def build_block_trials(items, n_ls=4):
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
    Phase 1  (2.5 s):  Image + word; response accepted any time; window completes.
    Phase 2  (2.0 s):  Feedback text only.
    """
    pic_path     = os.path.join(STIM_DIR, trial['pic'])
    word         = trial['word']
    correct_word = trial['correct_word']
    condition    = trial['condition']

    # Phase 1 ─────────────────────────────────────────────────────────────
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

    elapsed = resp_clock.getTime()
    if elapsed < STIM_DUR:
        core.wait(STIM_DUR - elapsed)

    # Correctness ──────────────────────────────────────────────────────────
    if response is None:
        correct_flag = 'timeout'
        fb_msg = f'Zu sp\u00e4t, das ist {correct_word}'
    elif (condition == 'c' and response == KEY_YES) or \
         (condition == 'i' and response == KEY_NO):
        correct_flag = 'correct'
        fb_msg = f'Korrekt, das ist {correct_word}'
    else:
        correct_flag = 'incorrect'
        fb_msg = f'Falsch, das ist {correct_word}'

    # Phase 2 ─────────────────────────────────────────────────────────────
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

# ── Block order ────────────────────────────────────────────────────────────────
def make_block_order():
    order = list(range(6))
    ctrl  = {4, 5}
    for _ in range(2000):
        random.shuffle(order)
        if order[0] in ctrl or order[-1] in ctrl:
            continue
        if any(order[k] in ctrl and order[k+1] in ctrl
               for k in range(5)):
            continue
        return order
    return [0, 4, 1, 2, 5, 3]

# ── Bubble paths ───────────────────────────────────────────────────────────────
# Set 2: bubbles/ is at the script root (no Stimuli/ subfolder)
BUBBLES = {
    'hello':    _p('bubbles', 'hello.jpg'),
    'learning': _p('bubbles', 'learning.jpg'),
    'control':  _p('bubbles', 'control.jpg'),
    'bye':      _p('bubbles', 'bye.jpg'),
}

ALL_BLOCKS = [
    (LEARNING[0:7],   'learning-1', 'learning', 1),
    (LEARNING[7:14],  'learning-2', 'learning', 2),
    (LEARNING[14:21], 'learning-3', 'learning', 3),
    (LEARNING[21:28], 'learning-4', 'learning', 4),
    (CONTROL[0:14],   'control-1',  'control',  5),
    (CONTROL[14:28],  'control-2',  'control',  6),
]

# ── Main experiment ────────────────────────────────────────────────────────────

# 00  Instructions Part 1  (7 slides, SPACE to advance)
show_instructions_part1()

# 01  Instructions Part 2  (1 slide, SPACE to start)
show_instructions_part2()

# 02  Hello
show_bubble(BUBBLES['hello'], duration=FIX_DUR)

# 03  Main blocks
order = make_block_order()
for run_idx, blk_idx in enumerate(order):
    items, phase, bubble_key, block_num = ALL_BLOCKS[blk_idx]
    show_bubble(BUBBLES[bubble_key], duration=FIX_DUR)
    run_block(items, block_run=run_idx + 1, block_num=block_num,
              phase=phase, n_ls=4)

# 04  Bye
show_bubble(BUBBLES['bye'], duration=FIX_DUR)

# 05  Instructions Part 3 – AFC  (4 slides, SPACE on last)
show_instructions_part3()

# 06  AFC
run_afc()

# End
feedback_text.setText('Vielen Dank f\u00fcr Ihre Teilnahme!')
feedback_text.draw(); win.flip()
core.wait(3.0)

_csv_file.close(); win.close(); core.quit()
