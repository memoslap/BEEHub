#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PsychoPy implementation of APPL fMRI experiment
Based on Presentation .sce files
"""

from psychopy import visual, core, event, data, gui, logging
import numpy as np
import random
import os
import sys
import glob
from datetime import datetime

# =============================================================================
# EXPERIMENT SETUP
# =============================================================================

# Experiment info dialog
exp_info = {
    'subject': '001',
    'session': '1',
    'version': 'A',
    'fmri_mode': False,  # Set to True for fMRI with pulse triggering
}
dlg = gui.DlgFromDict(exp_info, title='APPL Experiment')
if not dlg.OK:
    core.quit()

# Create data filename
date_str = datetime.now().strftime("%Y-%m-%d_%H-%M")
filename = f"data/sub-{exp_info['subject']}_ses-{exp_info['session']}_ver-{exp_info['version']}_{date_str}"
os.makedirs('data', exist_ok=True)

# Set up logging
logging.console.setLevel(logging.INFO)
log_file = logging.LogFile(filename + '.log', level=logging.EXP)
logging.setDefaultClock(core.MonotonicClock())

# Open window
win = visual.Window(
    size=[1280, 720],
    fullscr=False,
    screen=0,
    winType='pyglet',
    allowGUI=False,
    color='black',
    units='pix'
)

# Set up response collection
if exp_info['fmri_mode']:
    # For fMRI, we'd configure button box here
    # This is a placeholder
    pass

# =============================================================================
# STIMULUS DEFINITIONS
# =============================================================================

# Text stimuli
fixation = visual.TextStim(win, text='+', color='white', height=100)
response_text = visual.TextStim(win, text='-', color='white', height=100)
feedback_text = visual.TextStim(win, text='', color='white', height=100)

# Image stimuli
pres_pic = visual.ImageStim(win, size=(600, 600))
info_pic = visual.ImageStim(win, size=(600, 398))
pres_word = visual.TextStim(win, text='...', color='white', height=100, pos=(0, -400))

# Combined stimulus for learning trials
stim_pic_word = visual.BufferImageStim(win, stim=[pres_pic, pres_word])

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def wait_for_pulse():
    """Wait for fMRI trigger (simulated or real)"""
    if exp_info['fmri_mode']:
        # In real fMRI mode, wait for trigger pulse
        # This is a placeholder - actual implementation depends on hardware
        pass
    else:
        # In emulation mode, wait for spacebar
        event.waitKeys(keyList=['space'])
        core.wait(0.5)  # Simulate scanner delay

def present_trial(stimulus, duration=None, response_buttons=None):
    """
    Present a trial with optional duration and response collection
    
    Parameters:
    - stimulus: visual stimulus to present
    - duration: trial duration in seconds (None = forever)
    - response_buttons: list of allowed buttons
    """
    timer = core.Clock()
    response = None
    rt = None
    
    while True:
        stimulus.draw()
        win.flip()
        
        # Check for responses
        if response_buttons:
            keys = event.getKeys(keyList=response_buttons, timeStamped=timer)
            if keys:
                response = keys[0][0]
                rt = keys[0][1]
                break
        
        # Check duration
        if duration and timer.getTime() >= duration:
            break
            
        # Check for quit
        if 'escape' in event.getKeys():
            core.quit()
    
    return response, rt

# =============================================================================
# EXPERIMENT PHASES
# =============================================================================

class APPLExperiment:
    def __init__(self, win, exp_info):
        self.win = win
        self.exp_info = exp_info
        self.pulse_count = 4  # Start pulse counter
        self.response_history = []
        
        # Initialize stimuli paths based on version

        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Stimuli")
        self.prac_path = os.path.join(base_path, "prac")
        self.learning_path = os.path.join(base_path, "learning")
        self.control_path = os.path.join(base_path, "control")
        self.afc_path = os.path.join(base_path, "AFC")
        self.bubbles_path = os.path.join(base_path, "bubbles")
        
        # Define stimuli for each phase
        self.init_stimuli()
        
    def init_stimuli(self):
        """Initialize all stimuli arrays"""
        
        # Hello/Learning/Control/Bye images
        self.hlcb = [
            os.path.join(self.bubbles_path, "hello.jpg"),
            os.path.join(self.bubbles_path, "learning.jpg"),
            os.path.join(self.bubbles_path, "control.jpg"),
            os.path.join(self.bubbles_path, "bye.jpg")
        ]
        
        # Learning stimuli (28 items with 6 words each)
        self.LEARNING = []
        
        # Learning pics arrays
        learning_pics1 = ["learning/PICTURE_692.jpg", "learning/PICTURE_640.jpg", 
                          "learning/PICTURE_379.jpg", "learning/PICTURE_465.jpg",
                          "learning/PICTURE_148.jpg", "learning/PICTURE_453.jpg", 
                          "learning/PICTURE_592.jpg"]
        learning_pics2 = ["learning/PICTURE_26.jpg", "learning/PICTURE_212.jpg",
                          "learning/PICTURE_38.jpg", "learning/PICTURE_654.jpg",
                          "learning/PICTURE_165.jpg", "learning/PICTURE_358.jpg",
                          "learning/PICTURE_659.jpg"]
        learning_pics3 = ["learning/PICTURE_67.jpg", "learning/PICTURE_68.jpg",
                          "learning/PICTURE_71.jpg", "learning/PICTURE_72.jpg",
                          "learning/PICTURE_202.jpg", "learning/PICTURE_203.jpg",
                          "learning/PICTURE_74.jpg"]
        learning_pics4 = ["learning/PICTURE_77.jpg", "learning/PICTURE_267.jpg",
                          "learning/PICTURE_97.jpg", "learning/PICTURE_100.jpg",
                          "learning/PICTURE_224.jpg", "learning/PICTURE_566.jpg",
                          "learning/PICTURE_32.jpg"]
        
        # Learning words arrays
        learning_words1 = [
            ["Halne", "Halpe", "Haler", "Halge", "Halser"],
            ["Letim", "Lemet", "Legas", "Letar", "Leniel"],
            ["Larbe", "Largas", "Lartan", "Larnel", "Lartum"],
            ["Flister", "Flistan", "Flistun", "Flisber", "Flistert"],
            ["Schiehel", "Schiegun", "Schiemer", "Schieton", "Schieter"],
            ["Neffit", "Neffsen", "Neffgasch", "Neffser", "Nefftoll"],
            ["Helte", "Heltaun", "Helsal", "Helger", "Helgu"]
        ]
        
        learning_words2 = [
            ["Logatt", "Lose", "Lonap", "Lomack", "Lomant"],
            ["Limtepp", "Limnap", "Limrest", "Limmant", "Limpad"],
            ["Derlas", "Derpest", "Dervat", "Derpod", "Derdum"],
            ["Dobul", "Dovat", "Dostal", "Dodem", "Dosir"],
            ["Nehal", "Negan", "Nerel", "Netoll", "Nereik"],
            ["Sprünte", "Spründent", "Sprünlas", "Sprüntinn", "Sprüntot"],
            ["Dertin", "Derstal", "Derse", "Dersir", "Dernark"]
        ]
        
        learning_words3 = [
            ["Maspe", "Mashun", "Masles", "Mastes", "Mastem"],
            ["Hiten", "Hine", "Hinsin", "Hiter", "Hitel"],
            ["Melant", "Mesin", "Metel", "Metes", "Medost"],
            ["Bleine", "Bleitem", "Bleites", "Bleidos", "Bleigo"],
            ["Flofe", "Flola", "Flogun", "Floto", "Flolei"],
            ["Wumze", "Wumges", "Wumes", "Wumtik", "Wumke"],
            ["Hamen", "Hante", "Haschin", "Hagem", "Hages"]
        ]
        
        learning_words4 = [
            ["Zase", "Zatei", "Zatol", "Zagon", "Zadit"],
            ["Zalbem", "Zaldot", "Zalkam", "Zaldit", "Zalme"],
            ["Zepa", "Zeka", "Zeche", "Zelan", "Zegat"],
            ["Tirsen", "Tirge", "Tirpa", "Tirgat", "Tirdan"],
            ["Herkun", "Hertes", "Hermo", "Hertuk", "Herlat"],
            ["Nerkanf", "Nermi", "Nertil", "Nerbat", "Nersal"],
            ["Dieges", "Diedap", "Diestei", "Diedam", "Diegons"]
        ]
        
        # Combine into LEARNING array
        for i in range(7):
            self.LEARNING.append([learning_pics1[i]] + learning_words1[i])
        for i in range(7):
            self.LEARNING.append([learning_pics2[i]] + learning_words2[i])
        for i in range(7):
            self.LEARNING.append([learning_pics3[i]] + learning_words3[i])
        for i in range(7):
            self.LEARNING.append([learning_pics4[i]] + learning_words4[i])
        
        # Control stimuli (28 items with 3 words each)
        self.CONTROL = [
            ["control/PICTURE_255.jpg", "Schaufel", "Fächer", "Kette"],
            ["control/PICTURE_551.jpg", "Kürbis", "Schaufel", "Affe"],
            ["control/PICTURE_368.jpg", "Fächer", "Kette", "Kürbis"],
            ["control/PICTURE_708.jpg", "Affe", "Kürbis", "Fächer"],
            ["control/PICTURE_391.jpg", "Kette", "Affe", "Schaufel"],
            ["control/PICTURE_185.jpg", "Fussball", "Lenkrad", "Truthahn"],
            ["control/PICTURE_398.jpg", "Lenkrad", "Truthahn", "Geschenk"],
            ["control/PICTURE_19.jpg", "Truthahn", "Geschenk", "Flasche"],
            ["control/PICTURE_338.jpg", "Geschenk", "Flasche", "Lenkrad"],
            ["control/PICTURE_414.jpg", "Lampe", "Brille", "Birne"],
            ["control/PICTURE_733.jpg", "Brille", "Birne", "Bluse"],
            ["control/PICTURE_42.jpg", "Birne", "Bluse", "Lampe"],
            ["control/PICTURE_59.jpg", "Bluse", "Lampe", "Brille"],
            ["control/PICTURE_343.jpg", "Flasche", "Fussball", "Truthahn"],
            ["control/PICTURE_491.jpg", "Teppich", "Drache", "Feuer"],
            ["control/PICTURE_111.jpg", "Drache", "Feuer", "Walnuss"],
            ["control/PICTURE_116.jpg", "Feuer", "Walnuss", "Anzug"],
            ["control/PICTURE_119.jpg", "Walnuss", "Anzug", "Teppich"],
            ["control/PICTURE_135.jpg", "Anzug", "Teppich", "Drache"],
            ["control/PICTURE_151.jpg", "Tablett", "Leuchtturm", "Teller"],
            ["control/PICTURE_540.jpg", "Leuchtturm", "Teller", "Hase"],
            ["control/PICTURE_234.jpg", "Teller", "Hase", "Panzer"],
            ["control/PICTURE_263.jpg", "Hase", "Panzer", "Tablett"],
            ["control/PICTURE_130.jpg", "Weste", "Absatz", "Zirkel"],
            ["control/PICTURE_266.jpg", "Absatz", "Zirkel", "Butter"],
            ["control/PICTURE_197.jpg", "Zirkel", "Butter", "Weste"],
            ["control/PICTURE_335.jpg", "Butter", "Weste", "Absatz"],
            ["control/PICTURE_621.jpg", "Panzer", "Tablett", "Leuchtturm"]
        ]
        
        # Build trial blocks
        self.build_blocks()
        
    def build_blocks(self):
        """Build trial blocks for learning and control phases"""
        
        # Initialize blocks
        self.blk1 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk2 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk3 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk4 = [[[] for _ in range(4)] for _ in range(14)]
        self.ctrl1 = [[[] for _ in range(4)] for _ in range(14)]
        self.ctrl2 = [[[] for _ in range(4)] for _ in range(14)]
        
        # Fill learning blocks
        a, b, c, d = 0, 0, 0, 0
        for i, item in enumerate(self.LEARNING):
            idx = i + 1
            if idx <= 7:  # Block 1
                # Create trials for each learning stage
                for ls in range(4):
                    self.blk1[a][ls] = f"{item[0]};{item[1]};{item[1]};c"
                    self.blk1[a+1][ls] = f"{item[0]};{item[ls+2]};{item[1]};i"
                a += 2
            elif idx <= 14:  # Block 2
                for ls in range(4):
                    self.blk2[b][ls] = f"{item[0]};{item[1]};{item[1]};c"
                    self.blk2[b+1][ls] = f"{item[0]};{item[ls+2]};{item[1]};i"
                b += 2
            elif idx <= 21:  # Block 3
                for ls in range(4):
                    self.blk3[c][ls] = f"{item[0]};{item[1]};{item[1]};c"
                    self.blk3[c+1][ls] = f"{item[0]};{item[ls+2]};{item[1]};i"
                c += 2
            else:  # Block 4
                for ls in range(4):
                    self.blk4[d][ls] = f"{item[0]};{item[1]};{item[1]};c"
                    self.blk4[d+1][ls] = f"{item[0]};{item[ls+2]};{item[1]};i"
                d += 2
        
        # Fill control blocks
        a, b = 0, 0
        for i in range(0, len(self.CONTROL), 2):
            if i < 14:
                for ls in range(4):
                    if ls < 2:
                        self.ctrl1[a][ls] = f"{self.CONTROL[i][0]};{self.CONTROL[i][1]};{self.CONTROL[i][1]};c"
                        self.ctrl1[a+1][ls] = f"{self.CONTROL[i][0]};{self.CONTROL[i][ls+2]};{self.CONTROL[i][1]};i"
                    else:
                        self.ctrl1[a][ls] = f"{self.CONTROL[i+1][0]};{self.CONTROL[i+1][1]};{self.CONTROL[i+1][1]};c"
                        self.ctrl1[a+1][ls] = f"{self.CONTROL[i+1][0]};{self.CONTROL[i+1][ls-1]};{self.CONTROL[i+1][1]};i"
                a += 2
            else:
                for ls in range(4):
                    if ls < 2:
                        self.ctrl2[b][ls] = f"{self.CONTROL[i][0]};{self.CONTROL[i][1]};{self.CONTROL[i][1]};c"
                        self.ctrl2[b+1][ls] = f"{self.CONTROL[i][0]};{self.CONTROL[i][ls+2]};{self.CONTROL[i][1]};i"
                    else:
                        self.ctrl2[b][ls] = f"{self.CONTROL[i+1][0]};{self.CONTROL[i+1][1]};{self.CONTROL[i+1][1]};c"
                        self.ctrl2[b+1][ls] = f"{self.CONTROL[i+1][0]};{self.CONTROL[i+1][ls-1]};{self.CONTROL[i+1][1]};i"
                b += 2
        
        # Create task list
        self.Task_List = {
            1: self.blk1,
            2: self.blk2,
            3: self.blk3,
            4: self.blk4,
            5: self.ctrl1,
            6: self.ctrl2
        }
        
        # Shuffle learning stages within each block
        for blk in range(1, 7):
            for ls in range(4):
                dummy = self.Task_List[blk][ls].copy()
                random.shuffle(dummy)
                self.Task_List[blk][ls] = dummy
        
        # Set block order
        self.BlockOrder = [1, 2, 3, 4, 5, 6]
        random.shuffle(self.BlockOrder)
        
    # =========================================================================
    # INSTRUCTION PHASES
    # =========================================================================
    
    def show_instructions_1(self):
        """Show first instruction set (00_Instr_1.sce)"""
        instr_files = [f"instr_1{i}.jpg" for i in range(1, 8)]
        
        for i, fname in enumerate(instr_files):
            full_path = os.path.join(self.bubbles_path, "..", fname)
            if os.path.exists(full_path):
                instr_img = visual.ImageStim(self.win, image=full_path, size=(1280, 720))
                instr_img.draw()
                self.win.flip()
                
                # Wait for response (button 1 for first 6, button 2 for last)
                if i < 6:
                    event.waitKeys(keyList=['1'])
                else:
                    event.waitKeys(keyList=['2'])
            else:
                # Fallback text instructions
                text = f"Instruction {i+1}\n\nPress {1 if i<6 else 2} to continue"
                text_stim = visual.TextStim(self.win, text=text, color='white', height=50)
                text_stim.draw()
                self.win.flip()
                event.waitKeys(keyList=['1' if i<6 else '2'])
    
    def show_instructions_2(self):
        """Show second instruction set (02_Instr_2.sce)"""
        full_path = os.path.join(self.bubbles_path, "..", "instr_21.jpg")
        if os.path.exists(full_path):
            instr_img = visual.ImageStim(self.win, image=full_path, size=(1280, 720))
            instr_img.draw()
            self.win.flip()
            event.waitKeys(keyList=['2'])
    
    def show_instructions_3(self):
        """Show third instruction set (04_Instr_3.sce)"""
        for i in range(1, 5):
            full_path = os.path.join(self.bubbles_path, "..", f"instr_3{i}.jpg")
            if os.path.exists(full_path):
                instr_img = visual.ImageStim(self.win, image=full_path, size=(1280, 720))
                instr_img.draw()
                self.win.flip()
                if i < 4:
                    event.waitKeys(keyList=['1'])
                else:
                    event.waitKeys(keyList=['2'])
    
    # =========================================================================
    # PRACTICE PHASE (01_Prac.sce)
    # =========================================================================
    
    def run_practice(self):
        """Run practice phase"""
        # Get practice images
        prac_images = glob.glob(os.path.join(self.prac_path, "*.jpg"))
        if not prac_images:
            # Fallback: create dummy practice
            self.run_practice_fallback()
            return
        
        # Shuffle and run 2 repetitions
        for rep in range(2):
            random.shuffle(prac_images)
            
            for img_path in prac_images:
                # Determine if correct or incorrect based on filename
                is_correct = 'k' in os.path.basename(img_path).lower()
                
                # Present image for 2.5 seconds
                pres_pic.setImage(img_path)
                pres_pic.size = (1224, 987)
                pres_pic.draw()
                self.win.flip()
                
                # Wait for response (2.5 seconds)
                timer = core.Clock()
                response = None
                rt = None
                
                while timer.getTime() < 2.5:
                    keys = event.getKeys(keyList=['1', '2'], timeStamped=timer)
                    if keys and response is None:
                        response = keys[0][0]
                        rt = keys[0][1]
                    
                    # Check for quit
                    if 'escape' in event.getKeys():
                        core.quit()
                    core.wait(0.01)
                
                # Show response text
                response_text.setText('-')
                response_text.draw()
                self.win.flip()
                core.wait(0.5)
                
                # Log response
                self.log_practice_trial(img_path, is_correct, response, rt)
            
            # Fixation between repetitions
            fixation.draw()
            self.win.flip()
            core.wait(4.5)  # Match scan_period
    
    def run_practice_fallback(self):
        """Fallback practice if images not found"""
        # Just show instructions
        text = "Übungsphase\n\nDrücke 1 für richtig, 2 für falsch"
        text_stim = visual.TextStim(self.win, text=text, color='white', height=50)
        text_stim.draw()
        self.win.flip()
        core.wait(3)
        
        for i in range(5):
            # Simulate trials
            is_correct = random.choice([True, False])
            text_stim.setText(f"Bild {i+1}\n\nDrücke {'1' if is_correct else '2'}")
            text_stim.draw()
            self.win.flip()
            
            timer = core.Clock()
            response = None
            while timer.getTime() < 2.5:
                keys = event.getKeys(keyList=['1', '2'], timeStamped=timer)
                if keys and response is None:
                    response = keys[0][0]
                core.wait(0.01)
            
            response_text.setText('-')
            response_text.draw()
            self.win.flip()
            core.wait(0.5)
    
    def log_practice_trial(self, img_path, is_correct, response, rt):
        """Log practice trial data"""
        data_line = {
            'phase': 'practice',
            'image': img_path,
            'is_correct': is_correct,
            'response': response,
            'rt': rt,
            'timestamp': core.getTime()
        }
        self.response_history.append(data_line)
        logging.data(f"PRAC: {img_path}, correct:{is_correct}, resp:{response}, rt:{rt}")
    
    # =========================================================================
    # LEARNING PHASE (03_learning.sce / 03_learning_final.sce)
    # =========================================================================
    
    def run_learning_phase(self):
        """Run main learning phase with feedback"""
        
        # Show intro
        intro_text = "Das Experiment beginnt gleich.\n\nZu Erinnerung: \n   Ja = Zeigefinger\n Nein = Daumen"
        feedback_text.setText(intro_text)
        feedback_text.draw()
        self.win.flip()
        core.wait(2)
        
        # Wait for first pulse
        if self.exp_info['fmri_mode']:
            wait_for_pulse()
        
        first_trial = True
        
        # Run blocks
        for blk_idx, blk_num in enumerate(self.BlockOrder):
            currBlk = blk_num
            
            # Determine block type and show appropriate bubble
            if currBlk in [5, 6]:
                bubble = self.hlcb[2]  # Control
            else:
                bubble = self.hlcb[1]  # Learning
            
            # Fixation before block
            for f in range(4):
                if f < 3:
                    fixation.draw()
                    self.win.flip()
                    core.wait(4.5)
                else:
                    # Show block info bubble
                    if os.path.exists(bubble):
                        info_pic.setImage(bubble)
                        info_pic.draw()
                        self.win.flip()
                    else:
                        # Fallback text
                        info_text = "Learning" if currBlk in [1,2,3,4] else "Control"
                        text_stim = visual.TextStim(self.win, text=info_text, color='white', height=100)
                        text_stim.draw()
                        self.win.flip()
                    core.wait(4.5)
            
            # Run learning stages (1-4)
            for ls in range(4):
                for i in range(14):  # 14 trials per learning stage
                    
                    # Get trial data
                    trial_str = self.Task_List[currBlk][ls][i]
                    parts = trial_str.split(';')
                    
                    if len(parts) < 4:
                        continue
                    
                    pic_file, pres_word_str, correct_word, trial_type = parts
                    
                    # Load and present stimulus
                    full_pic_path = os.path.join(self.bubbles_path, "..", pic_file)
                    if os.path.exists(full_pic_path):
                        pres_pic.setImage(full_pic_path)
                    else:
                        # Fallback: just show text
                        pres_word.setText(pres_word_str)
                        pres_word.draw()
                        self.win.flip()
                        core.wait(2.5)
                        continue
                    
                    # Record old response count
                    old_resp_count = len(self.response_history)
                    
                    # Present stimulus (2.5 seconds)
                    pres_pic.draw()
                    pres_word.setText(pres_word_str)
                    pres_word.draw()
                    self.win.flip()
                    
                    stim_onset = core.getTime()
                    response = None
                    rt = None
                    
                    # Wait for response during stimulus presentation
                    resp_timer = core.Clock()
                    while resp_timer.getTime() < 2.5:
                        keys = event.getKeys(keyList=['1', '2'], timeStamped=resp_timer)
                        if keys and response is None:
                            response = keys[0][0]
                            rt = keys[0][1]
                        core.wait(0.01)
                    
                    # Clear screen briefly
                    self.win.flip()
                    core.wait(0.1)
                    
                    # Determine feedback
                    if response is not None:
                        # Response within time window
                        if (trial_type == 'c' and response == '1') or (trial_type == 'i' and response == '2'):
                            feedback = f"Korrekt, das ist {correct_word}"
                        else:
                            feedback = f"Falsch, das ist {correct_word}"
                    else:
                        # Too late
                        feedback = f"Zu spät, das ist {correct_word}"
                    
                    # Show feedback (2 seconds)
                    feedback_text.setText(feedback)
                    feedback_text.draw()
                    self.win.flip()
                    core.wait(2.0)
                    
                    # Log trial
                    self.log_learning_trial(blk_idx+1, currBlk, ls+1, i+1, 
                                           pic_file, pres_word_str, correct_word, 
                                           trial_type, response, rt)
                    
                    self.pulse_count += 1
                
                # Fixation between learning stages
                fixation.draw()
                self.win.flip()
                core.wait(4.5)
                self.pulse_count += 1
            
            # End of block - show bye bubble if last block
            if blk_idx == len(self.BlockOrder) - 1:
                for f in range(4):
                    if f < 3:
                        fixation.draw()
                        self.win.flip()
                        core.wait(4.5)
                    else:
                        if os.path.exists(self.hlcb[3]):  # Bye image
                            info_pic.setImage(self.hlcb[3])
                            info_pic.draw()
                            self.win.flip()
                        core.wait(4.5)
    
    def log_learning_trial(self, block_run, block_num, learning_stage, trial_num,
                          pic_file, word, correct_word, trial_type, response, rt):
        """Log learning trial data"""
        data_line = {
            'phase': 'learning',
            'block_run': block_run,
            'block_num': block_num,
            'learning_stage': learning_stage,
            'trial_num': trial_num,
            'image': pic_file,
            'word': word,
            'correct_word': correct_word,
            'trial_type': trial_type,
            'response': response,
            'rt': rt,
            'pulse': self.pulse_count,
            'timestamp': core.getTime()
        }
        self.response_history.append(data_line)
        
        # Determine accuracy
        if response is not None:
            if (trial_type == 'c' and response == '1') or (trial_type == 'i' and response == '2'):
                accuracy = 1
            else:
                accuracy = 0
        else:
            accuracy = -1  # No response
        
        logging.data(f"LEARN: B{block_run}_{block_num}_LS{learning_stage}_T{trial_num}: "
                     f"{word}/{correct_word}/{trial_type}, resp:{response}, rt:{rt}, acc:{accuracy}")
    
    # =========================================================================
    # AFC PHASES (04_AFC.sce / 05_AFC.sce)
    # =========================================================================
    
    def run_afc_phase(self, phase_num=1):
        """Run AFC (Alternative Forced Choice) phase"""
        
        # Get AFC images
        afc_images = glob.glob(os.path.join(self.afc_path, "*.jpg"))
        if not afc_images:
            # Fallback
            self.run_afc_fallback()
            return
        
        random.shuffle(afc_images)
        
        for img_path in afc_images:
            # Extract filename for event code
            fname = os.path.basename(img_path)
            
            # Present image until response
            pres_pic.setImage(img_path)
            pres_pic.size = (1624, 1187) if phase_num == 1 else (1324, 1087)
            pres_pic.draw()
            self.win.flip()
            
            # Wait for response (1, 2, or 3)
            keys = event.waitKeys(keyList=['1', '2', '3', 'escape'])
            if 'escape' in keys:
                core.quit()
            
            response = keys[0]
            rt = None  # Not tracking RT precisely here
            
            # Log response
            self.log_afc_trial(phase_num, img_path, response)
            
            # Brief pause
            core.wait(0.5)
    
    def run_afc_fallback(self):
        """Fallback AFC if images not found"""
        text = "AFC Phase\n\nWähle 1, 2 oder 3"
        text_stim = visual.TextStim(self.win, text=text, color='white', height=50)
        
        for i in range(10):
            text_stim.setText(f"Bild {i+1}\n\nDrücke 1, 2 oder 3")
            text_stim.draw()
            self.win.flip()
            
            keys = event.waitKeys(keyList=['1', '2', '3'])
            self.log_afc_trial(1, f"fallback_{i}.jpg", keys[0])
    
    def log_afc_trial(self, phase_num, image, response):
        """Log AFC trial data"""
        data_line = {
            'phase': f'afc_{phase_num}',
            'image': image,
            'response': response,
            'timestamp': core.getTime()
        }
        self.response_history.append(data_line)
        logging.data(f"AFC{phase_num}: {image}, resp:{response}")
    
    # =========================================================================
    # MAIN EXPERIMENT FLOW
    # =========================================================================
    
    def run(self):
        """Run complete experiment"""
        
        # Show first instructions
        self.show_instructions_1()
        
        # Run practice
        self.run_practice()
        
        # Show second instructions
        self.show_instructions_2()
        
        # Run first AFC
        self.run_afc_phase(phase_num=1)
        
        # Show third instructions
        self.show_instructions_3()
        
        # Run main learning phase
        self.run_learning_phase()
        
        # Run final AFC
        self.run_afc_phase(phase_num=2)
        
        # End of experiment
        thank_you = "Vielen Dank für Ihre Teilnahme!"
        thank_stim = visual.TextStim(self.win, text=thank_you, color='white', height=100)
        thank_stim.draw()
        self.win.flip()
        core.wait(3)
        
        # Save data
        self.save_data()
    
    def save_data(self):
        """Save all response data to CSV"""
        import csv
        
        csv_file = filename + '.csv'
        
        if self.response_history:
            # Get all field names
            fieldnames = set()
            for entry in self.response_history:
                fieldnames.update(entry.keys())
            fieldnames = sorted(list(fieldnames))
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
                writer.writeheader()
                for entry in self.response_history:
                    writer.writerow(entry)
            
            print(f"Data saved to {csv_file}")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    try:
        # Create and run experiment
        exp = APPLExperiment(win, exp_info)
        exp.run()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        win.close()
        core.quit()