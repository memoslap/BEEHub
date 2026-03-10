#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fMRI Learning Task - PsychoPy Version
Converted from Presentation software script

This experiment presents pictures paired with words and participants indicate
if the pairing is correct or incorrect. Designed for fMRI studies.

Requirements:
- PsychoPy 2023.x or later
- Images folder structure:
  - bubbles/ (instruction images)
  - learning/ (stimulus images)
"""

from psychopy import visual, core, event, data, gui, logging
from psychopy.hardware import keyboard
import random
import os
from datetime import datetime
import pandas as pd

# ============================================================================
# EXPERIMENT PARAMETERS
# ============================================================================

# Display settings
BACKGROUND_COLOR = [0, 0, 0]  # Black background
TEXT_COLOR = [1, 1, 1]  # White text
FIXATION_SYMBOL = '+'
FONT_SIZE = 100

# Timing (in seconds)
STIMULUS_DURATION = 2.5  # Stimulus presentation
FEEDBACK_DURATION = 2.0  # Feedback presentation
FIXATION_DURATION = 4.5  # Between trials/blocks
INTRO_DURATION = 100  # Intro screen (or until response)

# fMRI settings
SCAN_PERIOD = 1.0  # TR in seconds
PULSES_PER_SCAN = 1
PULSE_KEY = '5'  # Common fMRI trigger key (can be changed)

# Response keys
LEFT_KEY = 'left'  # Correct (button 1 / index finger)
RIGHT_KEY = 'right'  # Incorrect (button 2 / thumb)
QUIT_KEY = 'q'

# Image dimensions
PIC_SIZE = (600, 600)
INFO_PIC_SIZE = (600, 398)

# ============================================================================
# STIMULUS DEFINITIONS
# ============================================================================

# Instruction images
INSTRUCTION_IMAGES = [
    "bubbles/hello.jpg",
    "bubbles/learning.jpg",
    "bubbles/control.jpg",
    "bubbles/bye.jpg"
]

# Learning stimuli - Block 1
LEARNING_PICS_1 = [
    "learning/PICTURE_24.jpg",
    "learning/PICTURE_40.jpg",
    "learning/PICTURE_62.jpg",
    "learning/PICTURE_92.jpg",
    "learning/PICTURE_125.jpg",
    "learning/PICTURE_156.jpg",
    "learning/PICTURE_245.jpg"
]

LEARNING_WORDS_1 = [
    ["Halne", "Halpe", "Haler", "Halge", "Halser"],
    ["Letim", "Lemet", "Legas", "Letar", "Leniel"],
    ["Larbe", "Largas", "Lartan", "Larnel", "Lartum"],
    ["Flister", "Flistan", "Flistun", "Flisber", "Flistert"],
    ["Schiehel", "Schiegun", "Schiemer", "Schieton", "Schieter"],
    ["Neffit", "Neffsen", "Neffgasch", "Neffser", "Nefftoll"],
    ["Helte", "Heltaun", "Helsal", "Helger", "Helgu"]
]

# Learning stimuli - Block 2
LEARNING_PICS_2 = [
    "learning/PICTURE_308.jpg",
    "learning/PICTURE_321.jpg",
    "learning/PICTURE_354.jpg",
    "learning/PICTURE_397.jpg",
    "learning/PICTURE_165.jpg",
    "learning/PICTURE_358.jpg",
    "learning/PICTURE_659.jpg"
]

LEARNING_WORDS_2 = [
    ["Logatt", "Lose", "Lonap", "Lomack", "Lomant"],
    ["Limtepp", "Limnap", "Limrest", "Limmant", "Limpad"],
    ["Derlas", "Derpest", "Dervat", "Derpod", "Derdum"],
    ["Dobul", "Dovat", "Dostal", "Dodem", "Dosir"],
    ["Nehal", "Negan", "Nerel", "Netoll", "Nereik"],
    ["Sprünte", "Spründent", "Sprünlas", "Sprüntinn", "Sprüntot"],
    ["Dertin", "Derstal", "Derse", "Dersir", "Dernark"]
]

# Learning stimuli - Block 3
LEARNING_PICS_3 = [
    "learning/PICTURE_67.jpg",
    "learning/PICTURE_68.jpg",
    "learning/PICTURE_71.jpg",
    "learning/PICTURE_72.jpg",
    "learning/PICTURE_202.jpg",
    "learning/PICTURE_203.jpg",
    "learning/PICTURE_74.jpg"
]

LEARNING_WORDS_3 = [
    ["Maspe", "Mashun", "Masles", "Mastes", "Mastem"],
    ["Hiten", "Hine", "Hinsin", "Hiter", "Hitel"],
    ["Melant", "Mesin", "Metel", "Metes", "Medost"],
    ["Bleine", "Bleitem", "Bleites", "Bleidos", "Bleigo"],
    ["Flofe", "Flola", "Flogun", "Floto", "Flolei"],
    ["Wumze", "Wumges", "Wumes", "Wumtik", "Wumke"],
    ["Hamen", "Hante", "Haschin", "Hagem", "Hages"]
]

# Learning stimuli - Block 4
LEARNING_PICS_4 = [
    "learning/PICTURE_77.jpg",
    "learning/PICTURE_267.jpg",
    "learning/PICTURE_97.jpg",
    "learning/PICTURE_100.jpg",
    "learning/PICTURE_224.jpg",
    "learning/PICTURE_566.jpg",
    "learning/PICTURE_32.jpg"
]

LEARNING_WORDS_4 = [
    ["Zase", "Zatei", "Zatol", "Zagon", "Zadit"],
    ["Zalbem", "Zaldot", "Zalkam", "Zaldit", "Zalme"],
    ["Zepa", "Zeka", "Zeche", "Zelan", "Zegat"],
    ["Tirsen", "Tirge", "Tirpa", "Tirgat", "Tirdan"],
    ["Herkun", "Hertes", "Hermo", "Hertuk", "Herlat"],
    ["Nerkanf", "Nermi", "Nertil", "Nerbat", "Nersal"],
    ["Dieges", "Diedap", "Diestei", "Diedam", "Diegons"]
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_trial_list(pics, words):
    """
    Create a list of trials from pictures and words.
    
    Args:
        pics: List of picture filenames
        words: List of word lists (each containing 5 words)
    
    Returns:
        List of trials where each trial is [pic, correct_word, word2, word3, word4, word5]
    """
    trials = []
    for i in range(len(pics)):
        trial = [pics[i]] + words[i]
        trials.append(trial)
    return trials


def create_learning_blocks():
    """
    Create all learning blocks with shuffled stimuli.
    
    Returns:
        List of 4 blocks, each containing shuffled trial lists
    """
    blocks = []
    
    # Block 1
    block1_trials = create_trial_list(LEARNING_PICS_1.copy(), LEARNING_WORDS_1.copy())
    random.shuffle(block1_trials)
    blocks.append(block1_trials)
    
    # Block 2
    block2_trials = create_trial_list(LEARNING_PICS_2.copy(), LEARNING_WORDS_2.copy())
    random.shuffle(block2_trials)
    blocks.append(block2_trials)
    
    # Block 3
    block3_trials = create_trial_list(LEARNING_PICS_3.copy(), LEARNING_WORDS_3.copy())
    random.shuffle(block3_trials)
    blocks.append(block3_trials)
    
    # Block 4
    block4_trials = create_trial_list(LEARNING_PICS_4.copy(), LEARNING_WORDS_4.copy())
    random.shuffle(block4_trials)
    blocks.append(block4_trials)
    
    return blocks


def create_task_trials(block_trials):
    """
    Create task trials for a block across 4 learning stages.
    Each stage has 14 trials (7 pictures x 2 presentations with different words).
    
    Args:
        block_trials: List of [pic, word1, word2, word3, word4, word5] trials
    
    Returns:
        4 learning stages, each with 14 trials
    """
    stages = [[], [], [], []]
    
    for trial in block_trials:
        pic = trial[0]
        correct_word = trial[1]  # First word is correct
        incorrect_words = trial[2:]  # Remaining 4 words are incorrect
        
        # Create 2 trials per picture (1 correct, 1 incorrect)
        # Shuffle to randomize correct/incorrect order
        trial_types = ['c', 'i']
        random.shuffle(trial_types)
        
        for trial_type in trial_types:
            if trial_type == 'c':
                # Correct trial
                trial_data = {
                    'picture': pic,
                    'word': correct_word,
                    'correct_word': correct_word,
                    'type': 'c'
                }
            else:
                # Incorrect trial - randomly select one of the incorrect words
                incorrect_word = random.choice(incorrect_words)
                trial_data = {
                    'picture': pic,
                    'word': incorrect_word,
                    'correct_word': correct_word,
                    'type': 'i'
                }
            
            # Distribute trials across 4 stages
            for stage in stages:
                if len(stage) < 14:
                    stage.append(trial_data)
                    break
    
    # Shuffle trials within each stage
    for stage in stages:
        random.shuffle(stage)
    
    return stages


def create_block_order():
    """
    Create a randomized block order (1-4) with constraints.
    Constraints:
    - First block cannot be 5 or 6 (control blocks - not used in short version)
    - Last block cannot be 5 or 6
    - Blocks 5 and 6 cannot be consecutive
    
    Returns:
        List of block indices in randomized order
    """
    # For this short version, we only have blocks 1-4
    # Create random order
    valid_order = False
    while not valid_order:
        order = [1, 2, 3, 4]
        random.shuffle(order)
        
        # For short version with only 4 blocks, any order is valid
        # But we keep the structure for consistency with original
        valid_order = True
    
    return order


def wait_for_scanner_pulse(win, text_stim, kb):
    """
    Wait for scanner pulse before starting experiment.
    
    Args:
        win: PsychoPy window
        text_stim: Text stimulus to display waiting message
        kb: Keyboard object
    
    Returns:
        Timestamp of pulse receipt
    """
    text_stim.text = 'Warte auf Scanner...\n\nWaiting for scanner pulse...'
    text_stim.draw()
    win.flip()
    
    # Wait for pulse
    keys = kb.waitKeys(keyList=[PULSE_KEY, QUIT_KEY])
    
    if QUIT_KEY in [k.name for k in keys]:
        core.quit()
    
    return core.getTime()


def show_fixation(win, fix_stim, duration):
    """
    Show fixation cross for specified duration.
    
    Args:
        win: PsychoPy window
        fix_stim: Fixation stimulus
        duration: Duration in seconds
    """
    fix_stim.draw()
    win.flip()
    core.wait(duration)


def show_instruction(win, img_stim, image_path, duration):
    """
    Show instruction image.
    
    Args:
        win: PsychoPy window
        img_stim: Image stimulus object
        image_path: Path to instruction image
        duration: Duration in seconds
    """
    if os.path.exists(image_path):
        img_stim.image = image_path
        img_stim.draw()
        win.flip()
        core.wait(duration)
    else:
        print(f"Warning: Instruction image not found: {image_path}")
        core.wait(duration)


def present_trial(win, pic_stim, word_stim, trial_data, kb):
    """
    Present a single trial (picture + word) and collect response.
    
    Args:
        win: PsychoPy window
        pic_stim: Picture stimulus object
        word_stim: Word stimulus object
        trial_data: Dictionary with trial information
        kb: Keyboard object
    
    Returns:
        Dictionary with response data
    """
    # Set stimuli
    pic_path = trial_data['picture']
    if os.path.exists(pic_path):
        pic_stim.image = pic_path
    else:
        print(f"Warning: Image not found: {pic_path}")
    
    word_stim.text = trial_data['word']
    
    # Draw stimuli
    pic_stim.draw()
    word_stim.draw()
    win.flip()
    
    # Record onset time
    onset_time = core.getTime()
    
    # Wait for response (or timeout)
    kb.clock.reset()
    keys = kb.waitKeys(maxWait=STIMULUS_DURATION, keyList=[LEFT_KEY, RIGHT_KEY, QUIT_KEY])
    
    # Process response
    if keys:
        key = keys[0]
        if key.name == QUIT_KEY:
            core.quit()
        
        response = key.name
        rt = key.rt
        
        # Determine accuracy
        if trial_data['type'] == 'c':  # Correct pairing
            correct = (response == LEFT_KEY)
        else:  # Incorrect pairing
            correct = (response == RIGHT_KEY)
    else:
        # No response (timeout)
        response = None
        rt = None
        correct = False
    
    return {
        'onset_time': onset_time,
        'response': response,
        'rt': rt,
        'correct': correct,
        'too_late': keys is None
    }


def show_feedback(win, text_stim, trial_data, response_data):
    """
    Show feedback based on response.
    
    Args:
        win: PsychoPy window
        text_stim: Text stimulus for feedback
        trial_data: Trial information
        response_data: Response information
    """
    correct_word = trial_data['correct_word']
    
    if response_data['too_late']:
        feedback_text = f"Zu spät, das ist {correct_word}"
    elif response_data['correct']:
        feedback_text = f"Korrekt, das ist {correct_word}"
    else:
        feedback_text = f"Falsch, das ist {correct_word}"
    
    text_stim.text = feedback_text
    text_stim.draw()
    win.flip()
    core.wait(FEEDBACK_DURATION)


def save_trial_data(trial_list, filename):
    """
    Save trial data to CSV file.
    
    Args:
        trial_list: List of trial dictionaries
        filename: Output filename
    """
    df = pd.DataFrame(trial_list)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")


# ============================================================================
# MAIN EXPERIMENT
# ============================================================================

def run_experiment():
    """
    Main experiment function.
    """
    # ========================================================================
    # Setup
    # ========================================================================
    
    # Get participant info
    exp_info = {
        'Participant ID': '',
        'Session': '001',
        'Wait for scanner': True,
        'Fullscreen': True
    }
    
    dlg = gui.DlgFromDict(exp_info, title='fMRI Learning Task', 
                          order=['Participant ID', 'Session', 'Wait for scanner', 'Fullscreen'])
    if not dlg.OK:
        core.quit()
    
    # Setup data logging
    exp_info['date'] = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    exp_info['psychopyVersion'] = '2023.2.0'
    
    # Create data filename
    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    data_filename = os.path.join(
        data_dir,
        f"sub-{exp_info['Participant ID']}_ses-{exp_info['Session']}_{exp_info['date']}"
    )
    
    # Setup logging
    log_file = logging.LogFile(data_filename + '.log', level=logging.INFO)
    logging.console.setLevel(logging.WARNING)
    
    # Create window
    win = visual.Window(
        size=[1680, 1050],
        fullscr=exp_info['Fullscreen'],
        color=BACKGROUND_COLOR,
        units='pix'
    )
    
    # Create stimuli
    pic_stim = visual.ImageStim(
        win,
        size=PIC_SIZE,
        pos=(0, 0)
    )
    
    word_stim = visual.TextStim(
        win,
        text='',
        color=TEXT_COLOR,
        height=FONT_SIZE,
        pos=(0, -400)
    )
    
    text_stim = visual.TextStim(
        win,
        text='',
        color=TEXT_COLOR,
        height=FONT_SIZE,
        pos=(0, 0),
        wrapWidth=1200
    )
    
    fix_stim = visual.TextStim(
        win,
        text=FIXATION_SYMBOL,
        color=TEXT_COLOR,
        height=FONT_SIZE,
        pos=(0, 0)
    )
    
    info_stim = visual.ImageStim(
        win,
        size=INFO_PIC_SIZE,
        pos=(0, 0)
    )
    
    # Setup keyboard
    kb = keyboard.Keyboard()
    
    # ========================================================================
    # Prepare experiment
    # ========================================================================
    
    # Create learning blocks
    all_blocks = create_learning_blocks()
    
    # Create block order (using only 4 blocks in short version)
    block_order = create_block_order()
    
    # We'll use only the first 4 blocks (indices 0-3)
    # In the original, this would go up to 6 blocks
    num_blocks = 4
    
    # Container for all trial data
    all_trial_data = []
    
    # ========================================================================
    # Show introduction
    # ========================================================================
    
    intro_text = ("Das Experiment\nbeginnt gleich.\n\n"
                  "Zu Erinnerung:\n   Ja = Zeigefinger\n Nein = Daumen")
    text_stim.text = intro_text
    text_stim.draw()
    win.flip()
    
    # Wait for response or timeout
    kb.waitKeys(maxWait=INTRO_DURATION, keyList=[LEFT_KEY, RIGHT_KEY, PULSE_KEY])
    
    # ========================================================================
    # Wait for scanner (if requested)
    # ========================================================================
    
    if exp_info['Wait for scanner']:
        pulse_time = wait_for_scanner_pulse(win, text_stim, kb)
        exp_start_time = pulse_time
    else:
        exp_start_time = core.getTime()
    
    # ========================================================================
    # Run blocks
    # ========================================================================
    
    for block_idx in range(num_blocks):
        current_block = block_order[block_idx]
        block_trials = all_blocks[current_block - 1]  # -1 because list is 0-indexed
        
        print(f"\n=== Block {block_idx + 1}/{num_blocks} (Block type: {current_block}) ===")
        
        # Determine instruction image
        is_last_block = (block_idx == num_blocks - 1)
        
        # Show fixation (3 repetitions) + instruction (1 repetition)
        for f in range(4):
            if f < 3:
                # Show fixation
                show_fixation(win, fix_stim, FIXATION_DURATION)
            else:
                # Show instruction
                if is_last_block:
                    instr_img = INSTRUCTION_IMAGES[1]  # Learning instruction
                else:
                    instr_img = INSTRUCTION_IMAGES[1]  # Learning instruction
                
                if os.path.exists(instr_img):
                    show_instruction(win, info_stim, instr_img, FIXATION_DURATION)
                else:
                    show_fixation(win, fix_stim, FIXATION_DURATION)
        
        # Create task trials for this block (4 learning stages)
        task_stages = create_task_trials(block_trials)
        
        # Run through 4 learning stages
        for stage_idx, stage_trials in enumerate(task_stages):
            print(f"  Stage {stage_idx + 1}/4: {len(stage_trials)} trials")
            
            # Run trials in this stage
            for trial_idx, trial_data in enumerate(stage_trials):
                # Present trial and collect response
                response_data = present_trial(win, pic_stim, word_stim, trial_data, kb)
                
                # Show feedback
                show_feedback(win, text_stim, trial_data, response_data)
                
                # Store data
                trial_record = {
                    'participant': exp_info['Participant ID'],
                    'session': exp_info['Session'],
                    'block': block_idx + 1,
                    'block_type': current_block,
                    'stage': stage_idx + 1,
                    'trial': trial_idx + 1,
                    'picture': trial_data['picture'],
                    'word': trial_data['word'],
                    'correct_word': trial_data['correct_word'],
                    'trial_type': trial_data['type'],
                    'onset_time': response_data['onset_time'] - exp_start_time,
                    'response': response_data['response'],
                    'rt': response_data['rt'],
                    'correct': response_data['correct'],
                    'too_late': response_data['too_late']
                }
                all_trial_data.append(trial_record)
            
            # Show fixation between stages
            show_fixation(win, fix_stim, FIXATION_DURATION)
        
        # Show goodbye image if last block
        if is_last_block:
            # Show fixation (3 times) + goodbye (1 time)
            for f in range(4):
                if f < 3:
                    show_fixation(win, fix_stim, FIXATION_DURATION)
                else:
                    bye_img = INSTRUCTION_IMAGES[3]  # Bye image
                    if os.path.exists(bye_img):
                        show_instruction(win, info_stim, bye_img, FIXATION_DURATION)
                    else:
                        show_fixation(win, fix_stim, FIXATION_DURATION)
    
    # ========================================================================
    # Save data and cleanup
    # ========================================================================
    
    # Save trial data
    save_trial_data(all_trial_data, data_filename + '.csv')
    
    # Show end message
    text_stim.text = 'Experiment beendet.\n\nVielen Dank!'
    text_stim.draw()
    win.flip()
    core.wait(3)
    
    # Cleanup
    win.close()
    core.quit()


# ============================================================================
# Run
# ============================================================================

if __name__ == '__main__':
    run_experiment()
