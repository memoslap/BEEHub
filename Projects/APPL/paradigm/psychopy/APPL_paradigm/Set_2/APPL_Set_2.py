#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PsychoPy implementation of APPL fMRI experiment
Based on Presentation .sce files - UPDATED VERSION
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

# Open window with correct size for instructions (1280x720)
win = visual.Window(
    size=[1280, 720],
    fullscr=False,
    screen=0,
    winType='pyglet',
    allowGUI=False,
    color='black',
    units='pix'
)

# =============================================================================
# STIMULUS DEFINITIONS
# =============================================================================

# Text stimuli
fixation = visual.TextStim(win, text='+', color='white', height=100)
response_text = visual.TextStim(win, text='-', color='white', height=100)
feedback_text = visual.TextStim(win, text='', color='white', height=100)

# Image stimuli
pres_pic = visual.ImageStim(win)
info_pic = visual.ImageStim(win)
pres_word = visual.TextStim(win, text='...', color='white', height=100, pos=(0, -400))

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
        
        # Learning stimuli (28 items with 6 words each) - UPDATED based on 03_learning_final.sce
        # Learning pics arrays - UPDATED from the .sce file
        learning_pics1 = ["learning/PICTURE_400.jpg", "learning/PICTURE_402.jpg", 
                          "learning/PICTURE_405.jpg", "learning/PICTURE_462.jpg",
                          "learning/PICTURE_53.jpg", "learning/PICTURE_216.jpg", 
                          "learning/PICTURE_21.jpg"]
        learning_pics2 = ["learning/PICTURE_480.jpg", "learning/PICTURE_488.jpg",
                          "learning/PICTURE_508.jpg", "learning/PICTURE_15.jpg",
                          "learning/PICTURE_695.jpg", "learning/PICTURE_703.jpg",
                          "learning/PICTURE_95.jpg"]
        learning_pics3 = ["learning/PICTURE_576.jpg", "learning/PICTURE_581.jpg",
                          "learning/PICTURE_52.jpg", "learning/PICTURE_594.jpg",
                          "learning/PICTURE_297.jpg", "learning/PICTURE_23.jpg",
                          "learning/PICTURE_605.jpg"]
        learning_pics4 = ["learning/PICTURE_247.jpg", "learning/PICTURE_43.jpg",
                          "learning/PICTURE_610.jpg", "learning/PICTURE_741.jpg",
                          "learning/PICTURE_235.jpg", "learning/PICTURE_720.jpg",
                          "learning/PICTURE_599.jpg"]
        
        # Learning words arrays - UPDATED from the .sce file
        learning_words1 = [
            ["Lopfer", "Loptem", "Lopdor", "Lopmig", "Lopter"],
            ["Resar", "Rerod", "Regan", "Reper", "Remert"],
            ["Nomtap", "Nomgan", "Nomtun", "Nomzerl", "Nomser"],
            ["Jamip", "Jamun", "Jakel", "Jaser", "Jasull"],
            ["Knele", "Knera", "Knefe", "Knetam", "Knesam"],
            ["Tignam", "Tigfe", "Tigdon", "Tigdam", "Tigmer"],
            ["Krükta", "Krükel", "Krüktem", "Krüklass", "Krükmig"]
        ]
        
        learning_words2 = [
            ["Zamet", "Zate", "Zabig", "Zabelt", "Zatir"],
            ["Jehler", "Jehrig", "Jehmel", "Jehtir", "Jehse"],
            ["Zerbe", "Zermel", "Zerse", "Zerpet", "Zertock"],
            ["Joten", "Joper", "Josant", "Jotolt", "Jota"],
            ["Munem", "Muschot", "Mufi", "Mugir", "Mupat"],
            ["Knusap", "Knufi", "Knufeg", "Knupat", "Knuler"],
            ["Klenter", "Klentant", "Klenban", "Klenta", "Klenfalt"]
        ]
        
        learning_words3 = [
            ["Schöle", "Schölte", "Schölse", "Schölme", "Schölter"],
            ["Zampe", "Zamse", "Zamram", "Zambel", "Zamler"],
            ["Geiten", "Geibel", "Geiner", "Geiper", "Geitel"],
            ["Gürbas", "Gürzer", "Gürter", "Gürbel", "Gürse"],
            ["Eume", "Eupis", "Euko", "Eudet", "Eutaf"],
            ["Koptan", "Koptel", "Koptur", "Kopster", "Kopsel"],
            ["Kegan", "Ketan", "Ketosch", "Keton", "Keteik"]
        ]
        
        learning_words4 = [
            ["Stise", "Stitons", "Stisin", "Stigit", "Stisum"],
            ["Finser", "Finsin", "Finlas", "Finsum", "Finges"],
            ["Seise", "Seimer", "Seitos", "Seiges", "Seitu"],
            ["Soktau", "Soklet", "Soktal", "Sokma", "Sokbat"],
            ["Efdi", "Efter", "Efto", "Efser", "Efnel"],
            ["Tulser", "Tulte", "Tulpos", "Tulber", "Tuldet"],
            ["Klotel", "Klosal", "Klotons", "Klobat", "Kloger"]
        ]
        
        # Combine into LEARNING array (28 items)
        self.LEARNING = []
        for i in range(7):
            self.LEARNING.append([learning_pics1[i]] + learning_words1[i])
        for i in range(7):
            self.LEARNING.append([learning_pics2[i]] + learning_words2[i])
        for i in range(7):
            self.LEARNING.append([learning_pics3[i]] + learning_words3[i])
        for i in range(7):
            self.LEARNING.append([learning_pics4[i]] + learning_words4[i])
        
        # Control stimuli (28 items with 3 words each) - UPDATED from 03_learning_final.sce
        self.CONTROL = [
            ["control/PICTURE_2.jpg", "Reifen", "Tiger", "Kompass"],
            ["control/PICTURE_98.jpg", "Tiger", "Kompass", "Gewehr"],
            ["control/PICTURE_292.jpg", "Kompass", "Gewehr", "Tunnel"],
            ["control/PICTURE_645.jpg", "Gewehr", "Tunnel", "Reifen"],
            ["control/PICTURE_286.jpg", "Tunnel", "Reifen", "Tiger"],
            ["control/PICTURE_733.jpg", "Brille", "Vogel", "Wolle"],
            ["control/PICTURE_430.jpg", "Vogel", "Wolle", "Hose"],
            ["control/PICTURE_134.jpg", "Wolle", "Hose", "Bagger"],
            ["control/PICTURE_718.jpg", "Hose", "Bagger", "Brille"],
            ["control/PICTURE_746.jpg", "Kegel", "Möwe", "Flagge"],
            ["control/PICTURE_220.jpg", "Möwe", "Flagge", "Blume"],
            ["control/PICTURE_295.jpg", "Flagge", "Blume", "Kegel"],
            ["control/PICTURE_312.jpg", "Blume", "Kegel", "Möwe"],
            ["control/PICTURE_731.jpg", "Bagger", "Brille", "Vogel"],
            ["control/PICTURE_549.jpg", "Schlange", "Parfüm", "Bibel"],
            ["control/PICTURE_314.jpg", "Parfüm", "Bibel", "Tasche"],
            ["control/PICTURE_350.jpg", "Bibel", "Tasche", "Vorhang"],
            ["control/PICTURE_388.jpg", "Tasche", "Vorhang", "Schlange"],
            ["control/PICTURE_418.jpg", "Vorhang", "Schlange", "Parfüm"],
            ["control/PICTURE_476.jpg", "Schürze", "Nagel", "Apfel"],
            ["control/PICTURE_485.jpg", "Nagel", "Apfel", "Tasse"],
            ["control/PICTURE_552.jpg", "Apfel", "Tasse", "Säule"],
            ["control/PICTURE_498.jpg", "Tasse", "Säule", "Schürze"],
            ["control/PICTURE_386.jpg", "Bombe", "Maske", "Spiegel"],
            ["control/PICTURE_84.jpg", "Maske", "Spiegel", "Schlitten"],
            ["control/PICTURE_340.jpg", "Spiegel", "Schlitten", "Bombe"],
            ["control/PICTURE_625.jpg", "Schlitten", "Bombe", "Maske"],
            ["control/PICTURE_663.jpg", "Säule", "Schürze", "Nagel"]
        ]
        
        # Build trial blocks
        self.build_blocks()
        
    def build_blocks(self):
        """Build trial blocks for learning and control phases"""
        
        # Initialize blocks (14 trials per block, 4 learning stages)
        self.blk1 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk2 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk3 = [[[] for _ in range(4)] for _ in range(14)]
        self.blk4 = [[[] for _ in range(4)] for _ in range(14)]
        self.ctrl1 = [[[] for _ in range(4)] for _ in range(14)]
        self.ctrl2 = [[[] for _ in range(4)] for _ in range(14)]
        
        # Fill learning blocks (based on the .sce file structure)
        a, b, c, d = 0, 0, 0, 0
        for i, item in enumerate(self.LEARNING):
            idx = i + 1
            if idx <= 7:  # Block 1
                # Create trials for each learning stage
                # Each picture appears with correct word and 4 incorrect words
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
            else:  # Block 4 (i > 21 and i <= 28)
                for ls in range(4):
                    self.blk4[d][ls] = f"{item[0]};{item[1]};{item[1]};c"
                    self.blk4[d+1][ls] = f"{item[0]};{item[ls+2]};{item[1]};i"
                d += 2
        
        # Fill control blocks (based on the .sce file structure)
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
        
        # Create task list (6 blocks total: 4 learning + 2 control)
        self.Task_List = {
            1: self.blk1,
            2: self.blk2,
            3: self.blk3,
            4: self.blk4,
            5: self.ctrl1,
            6: self.ctrl2
        }
        
        # Shuffle learning stages within each block (with constraints from .sce)
        for blk in range(1, 7):
            for ls in range(4):
                isOK = False
                while not isOK:
                    dummy = self.Task_List[blk][ls].copy()
                    random.shuffle(dummy)
                    
                    # Check constraints: no consecutive same picture or word
                    isOK = True
                    for k in range(13):
                        parts1 = dummy[k].split(';')
                        parts2 = dummy[k+1].split(';')
                        
                        if parts1[0] == parts2[0] or parts1[1] == parts2[1] or parts1[2] == parts2[1]:
                            isOK = False
                            break
                    
                    if isOK:
                        self.Task_List[blk][ls] = dummy
        
        # Set block order (with constraints from .sce)
        self.BlockOrder = [1, 2, 3, 4, 5, 6]
        
        # Shuffle with constraints: control blocks (5,6) not first or last, not consecutive
        isOrderOK = False
        while not isOrderOK:
            random.shuffle(self.BlockOrder)
            isOrderOK = True
            
            # Check constraints from .sce
            if self.BlockOrder[0] in [5, 6] or self.BlockOrder[5] in [5, 6]:
                isOrderOK = False
                continue
                
            for x in range(1, 6):
                if (self.BlockOrder[x-1] == 5 and self.BlockOrder[x] == 6) or \
                   (self.BlockOrder[x-1] == 6 and self.BlockOrder[x] == 5):
                    isOrderOK = False
                    break
        
        # Print block order for verification
        print(f"Block order: {self.BlockOrder}")
        
    # =========================================================================
    # INSTRUCTION PHASES (based on 00_Instr_1.sce and 02_Instr_2.sce)
    # =========================================================================
    
    def show_instructions_1(self):
        """Show first instruction set (00_Instr_1.sce)"""
        win.color = [1, 1, 1]  # White background
        win.flip()
        
        # Instructions 1-7
        for i in range(1, 8):
            full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"instr_1{i}.jpg")
            
            if os.path.exists(full_path):
                instr_img = visual.ImageStim(self.win, image=full_path, size=(1280, 720))
                instr_img.draw()
                self.win.flip()
                
                # Wait for response (button 1 for first 6, button 2 for last)
                if i < 7:
                    event.waitKeys(keyList=['1'])  # Left arrow in Presentation
                else:
                    event.waitKeys(keyList=['2'])  # Right arrow in Presentation
            else:
                # Fallback text instructions
                text = f"Instruktion {i}/7\n\nDrücke {'1' if i<7 else '2'} um fortzufahren"
                text_stim = visual.TextStim(self.win, text=text, color='black', height=50)
                text_stim.draw()
                self.win.flip()
                event.waitKeys(keyList=['1' if i<7 else '2'])
        
        win.color = 'black'
        win.flip()
    
    def show_instructions_2(self):
        """Show second instruction set (02_Instr_2.sce)"""
        win.color = [1, 1, 1]  # White background
        win.flip()
        
        full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "instr_21.jpg")
        if os.path.exists(full_path):
            instr_img = visual.ImageStim(self.win, image=full_path, size=(1280, 720))
            instr_img.draw()
            self.win.flip()
            event.waitKeys(keyList=['2'])
        else:
            text = "Instruktion\n\nDrücke 2 um fortzufahren"
            text_stim = visual.TextStim(self.win, text=text, color='black', height=50)
            text_stim.draw()
            self.win.flip()
            event.waitKeys(keyList=['2'])
        
        win.color = 'black'
        win.flip()
    
    # =========================================================================
    # PRACTICE PHASE (based on 01_Prac.sce)
    # =========================================================================
    
    def run_practice(self):
        """Run practice phase"""
        # Get practice images
        prac_images = glob.glob(os.path.join(self.prac_path, "*.jpg"))
        
        if not prac_images:
            print("No practice images found, skipping practice phase")
            return
        
        # Shuffle and run 2 repetitions (from .sce: loop int l = 1 until l > 2)
        for rep in range(2):
            random.shuffle(prac_images)
            
            for img_path in prac_images:
                # Determine if correct or incorrect based on filename (contains 'k')
                filename = os.path.basename(img_path).lower()
                is_correct = 'k' in filename
                
                # Present image for 2.5 seconds (from .sce: time = 0, then time = 2500)
                pres_pic.setImage(img_path)
                pres_pic.size = (1224, 987)  # From .sce
                pres_pic.draw()
                win.flip()
                
                # Wait for response (2.5 seconds)
                timer = core.Clock()
                response = None
                rt = None
                
                while timer.getTime() < 2.5:
                    keys = event.getKeys(keyList=['1', '2'], timeStamped=timer)
                    if keys and response is None:
                        response = keys[0][0]
                        rt = keys[0][1]
                    
                    if 'escape' in event.getKeys():
                        core.quit()
                    core.wait(0.01)
                
                # Show response text (from .sce: time = 2500)
                response_text.setText('-')
                response_text.draw()
                win.flip()
                core.wait(0.5)  # Short delay before next trial
                
                # Log response
                self.log_practice_trial(img_path, is_correct, response, rt)
            
            # Fixation between repetitions (from .sce: fixTrial with 4.5s)
            if rep < 1:  # After first repetition, before second
                fixation.draw()
                win.flip()
                core.wait(4.5)
    
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
    # LEARNING PHASE (based on 03_learning_final.sce)
    # =========================================================================
    
    def run_learning_phase(self):
        """Run main learning phase with feedback"""
        
        # Show intro (from .sce)
        intro_text = "Das Experiment\nbeginnt gleich.\n\nZu Erinnerung: \n   Ja = Zeigefinger\n Nein = Daumen"
        feedback_text.setText(intro_text)
        feedback_text.draw()
        win.flip()
        core.wait(2)
        
        # Wait for first pulse if in fMRI mode
        if self.exp_info['fmri_mode']:
            wait_for_pulse()
        
        first_trial = True
        
        # Run blocks
        for blk_idx, blk_num in enumerate(self.BlockOrder):
            currBlk = blk_num
            
            # Determine block type and show appropriate bubble
            if currBlk in [5, 6]:
                bubble = self.hlcb[2]  # Control
                bubble_code = "control"
            else:
                bubble = self.hlcb[1]  # Learning
                bubble_code = "learning"
            
            # Check if this is the last learning block (from .sce)
            is_last_learning = (blk_idx == 5 and currBlk in [1, 2, 3, 4])
            
            # Fixation before block (4 pulses from .sce)
            for f in range(4):
                if f < 3:
                    fixation.draw()
                    win.flip()
                    core.wait(4.5)
                    self.pulse_count += 1
                else:
                    # Show block info bubble (4th pulse)
                    if os.path.exists(bubble):
                        info_pic.setImage(bubble)
                        info_pic.size = (600, 398)  # From .sce
                        info_pic.draw()
                        win.flip()
                    else:
                        text_stim = visual.TextStim(self.win, text=bubble_code.upper(), 
                                                    color='white', height=100)
                        text_stim.draw()
                        win.flip()
                    core.wait(4.5)
                    self.pulse_count += 1
            
            # Run learning stages (1-4)
            for ls in range(4):
                for i in range(14):  # 14 trials per learning stage
                    
                    # Get trial data
                    trial_str = self.Task_List[currBlk][ls][i]
                    parts = trial_str.split(';')
                    
                    if len(parts) < 4:
                        continue
                    
                    pic_file, pres_word_str, correct_word, trial_type = parts
                    
                    # Get old response count (from .sce)
                    old_resp_count = len(self.response_history)
                    
                    # Load and present stimulus
                    full_pic_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                                "Stimuli", pic_file)
                    
                    if os.path.exists(full_pic_path):
                        pres_pic.setImage(full_pic_path)
                        pres_pic.size = (600, 600)  # From .sce
                    else:
                        # Try alternative path
                        alt_path = os.path.join(self.bubbles_path, "..", pic_file)
                        if os.path.exists(alt_path):
                            pres_pic.setImage(alt_path)
                            pres_pic.size = (600, 600)
                        else:
                            print(f"Image not found: {pic_file}")
                            continue
                    
                    # Present stimulus (2.5 seconds from .sce)
                    pres_pic.draw()
                    pres_word.setText(pres_word_str)
                    pres_word.draw()
                    win.flip()
                    
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
                    win.flip()
                    
                    # Determine feedback (from .sce logic)
                    curr_resp_count = len(self.response_history)
                    target_resp = old_resp_count + 1
                    
                    # Check response and timing
                    if response is not None:
                        # Response within time window
                        if (trial_type == 'c' and response == '1') or \
                           (trial_type == 'i' and response == '2'):
                            feedback = f"Korrekt, das ist {correct_word}"
                        else:
                            feedback = f"Falsch, das ist {correct_word}"
                    else:
                        # No response or too late
                        feedback = f"Zu spät, das ist {correct_word}"
                    
                    # Show feedback (2 seconds from .sce)
                    feedback_text.setText(feedback)
                    feedback_text.draw()
                    win.flip()
                    core.wait(2.0)
                    
                    # Log trial
                    self.log_learning_trial(blk_idx+1, currBlk, ls+1, i+1, 
                                           pic_file, pres_word_str, correct_word, 
                                           trial_type, response, rt)
                    
                    self.pulse_count += 1
                
                # Fixation between learning stages (from .sce)
                fixation.draw()
                win.flip()
                core.wait(4.5)
                self.pulse_count += 1
            
            # End of block - show bye bubble if last block (from .sce)
            if blk_idx == len(self.BlockOrder) - 1:
                for f in range(4):
                    if f < 3:
                        fixation.draw()
                        win.flip()
                        core.wait(4.5)
                        self.pulse_count += 1
                    else:
                        if os.path.exists(self.hlcb[3]):  # Bye image
                            info_pic.setImage(self.hlcb[3])
                            info_pic.size = (600, 398)
                            info_pic.draw()
                            win.flip()
                        core.wait(4.5)
                        self.pulse_count += 1
    
    def log_learning_trial(self, block_run, block_num, learning_stage, trial_num,
                          pic_file, word, correct_word, trial_type, response, rt):
        """Log learning trial data"""
        # Determine accuracy
        if response is not None:
            if (trial_type == 'c' and response == '1') or \
               (trial_type == 'i' and response == '2'):
                accuracy = 1
            else:
                accuracy = 0
        else:
            accuracy = -1  # No response
        
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
            'accuracy': accuracy,
            'pulse': self.pulse_count,
            'timestamp': core.getTime()
        }
        self.response_history.append(data_line)
        
        logging.data(f"LEARN: B{block_run}_{block_num}_LS{learning_stage}_T{trial_num}: "
                     f"{word}/{correct_word}/{trial_type}, resp:{response}, rt:{rt}, acc:{accuracy}")
    
    # =========================================================================
    # AFC PHASES (from original .py - keep as is)
    # =========================================================================
    
    def run_afc_phase(self, phase_num=1):
        """Run AFC (Alternative Forced Choice) phase"""
        
        # Get AFC images
        afc_images = glob.glob(os.path.join(self.afc_path, "*.jpg"))
        if not afc_images:
            print(f"No AFC images found for phase {phase_num}")
            return
        
        random.shuffle(afc_images)
        
        for img_path in afc_images:
            # Extract filename for event code
            fname = os.path.basename(img_path)
            
            # Set size based on phase (from original .py)
            if phase_num == 1:
                pres_pic.size = (1624, 1187)
            else:
                pres_pic.size = (1324, 1087)
            
            # Present image until response
            pres_pic.setImage(img_path)
            pres_pic.draw()
            win.flip()
            
            # Wait for response (1, 2, or 3)
            keys = event.waitKeys(keyList=['1', '2', '3', 'escape'])
            if 'escape' in keys:
                core.quit()
            
            response = keys[0]
            
            # Log response
            self.log_afc_trial(phase_num, img_path, response)
            
            # Brief pause
            core.wait(0.5)
    
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
        """Run complete experiment following the .sce sequence"""
        
        # 00_Instr_1.sce
        self.show_instructions_1()
        
        # 01_Prac.sce
        self.run_practice()
        
        # 02_Instr_2.sce
        self.show_instructions_2()
        
        # 04_AFC.sce (from original, not in provided .sce files)
        self.run_afc_phase(phase_num=1)
        
        # 03_learning_final.sce
        self.run_learning_phase()
        
        # 05_AFC.sce (from original)
        self.run_afc_phase(phase_num=2)
        
        # End of experiment
        thank_you = "Vielen Dank für Ihre Teilnahme!"
        thank_stim = visual.TextStim(self.win, text=thank_you, color='white', height=100)
        thank_stim.draw()
        win.flip()
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