"""
PsychoPy conversion of Presentation fMRI experiment
Original files: 00_Instr_1.sce, 01_Prac.sce, 02_Instr_2.sce, 
                03_learning.sce, 04_AFC.sce, 04_Instr_3.sce, 05_AFC.sce
"""

from psychopy import visual, core, event, gui, data
import numpy as np
import os
import sys
import random
from datetime import datetime

# =============================================================================
# PARAMETERS AND SETUP
# =============================================================================

# Experiment information
exp_name = 'fMRI_Learning_Experiment'
exp_info = {'participant': '', 'session': '001', 'date': datetime.now().strftime('%Y-%m-%d')}

# Display settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BG_COLOR = (-1, -1, -1)  # RGB from -1 to 1 (0,0,0 in 0-255 -> -1,-1,-1)
BG_COLOR_INSTR = (1, 1, 1)  # White background for instructions

# Timing parameters (in seconds)
FIXATION_DURATION = 4.5  # scan_period = 4500ms
STIM_DURATION = 2.5  # 2500ms
FEEDBACK_DURATION = 2.0  # 2000ms
ITI_DURATION = 4.5  # Inter-trial interval

# Response mapping (1=correct/left, 2=incorrect/right, 3=space)
RESPONSE_KEYS = ['1', '2', '3']  # Using number keys
CORRECT_KEY = '1'
INCORRECT_KEY = '2'
SPACE_KEY = 'space'

# Paths - UPDATE THESE TO YOUR PATHS
script_path = os.path.dirname(os.path.abspath(__file__))
STIM_PATH = os.path.join(script_path, "/Stimuli")
PRAC_PATH = os.path.join(STIM_PATH, "prac")
LEARNING_PATH = os.path.join(STIM_PATH, "learning")
CONTROL_PATH = os.path.join(STIM_PATH, "control")
AFC_PATH = os.path.join(STIM_PATH, "AFC")
BUBBLES_PATH = os.path.join(STIM_PATH, "bubbles")
INSTR_PATH = ""  # Path to instruction images

# fMRI simulation
FMRI_MODE = True
TRIGGER_KEY = '5'  # Key to simulate scanner trigger

# =============================================================================
# INITIALIZATION
# =============================================================================

# Create dialog for participant info
dlg = gui.DlgFromDict(exp_info, title=exp_name)
if not dlg.OK:
    core.quit()

# Setup window
win = visual.Window(
    size=[SCREEN_WIDTH, SCREEN_HEIGHT],
    fullscr=False,
    screen=0,
    color=BG_COLOR,
    colorSpace='rgb',
    units='pix'
)

# Create clock for timing
global_clock = core.Clock()
trial_clock = core.Clock()

# Setup event monitoring
event.globalKeys.add(key='escape', func=core.quit)

# Create data file
data_filename = f"{exp_info['participant']}_{exp_info['session']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
data_file = open(f"{data_filename}_data.csv", 'w')
data_file.write("trial_type,block,learning_stage,stimulus,word,correct_word,condition,response,rt,correct\n")

# =============================================================================
# STIMULUS CREATION
# =============================================================================

# Fixation cross
fixation = visual.TextStim(
    win=win,
    text='+',
    color='white',
    height=100,
    font='Arial'
)

# Text stimuli
pres_word = visual.TextStim(
    win=win,
    text='...',
    color='white',
    height=100,
    pos=(0, -400),
    font='Arial',
    wrapWidth=600
)

feedback_text = visual.TextStim(
    win=win,
    text='-',
    color='white',
    height=100,
    font='Arial',
    wrapWidth=800
)

# Image stimuli
pres_pic = visual.ImageStim(
    win=win,
    size=(600, 600),
    pos=(0, 0)
)

info_pic = visual.ImageStim(
    win=win,
    size=(600, 398),
    pos=(0, 0)
)

# =============================================================================
# STIMULUS LISTS (from 03_learning_final.sce)
# =============================================================================

# Hello/Learning/Control/Bye images
hlcb = [
    os.path.join(BUBBLES_PATH, "hello.jpg"),
    os.path.join(BUBBLES_PATH, "learning.jpg"),
    os.path.join(BUBBLES_PATH, "control.jpg"),
    os.path.join(BUBBLES_PATH, "bye.jpg")
]

# Learning stimuli - Pictures and associated words
LEARNING = [
    # Block 1 stimuli (5 items with 5 associated words each)
    {"pic": "learning/PICTURE_513.jpg", "words": ["Seltus", "Geward", "Gluktant", "Mekter", "Belschir"]},
    {"pic": "learning/PICTURE_24.jpg", "words": ["Basut", "Gluktant", "Goser", "Belschir", "Mekte"]},
    {"pic": "learning/PICTURE_40.jpg", "words": ["Priebem", "Goser", "Pafau", "Mekte", "Spiene"]},
    {"pic": "learning/PICTURE_245.jpg", "words": ["Enelt", "Pafau", "Aume", "Spiene", "Petonsk"]},
    {"pic": "learning/PICTURE_397.jpg", "words": ["Pofein", "Aume", "Geward", "Petonsk", "Mekter"]},
    
    # Block 2 stimuli
    {"pic": "learning/PICTURE_673.jpg", "words": ["Ingal", "Veschegt", "Sporkel", "Mummbant", "Vewerm"]},
    {"pic": "learning/PICTURE_354.jpg", "words": ["Aglud", "Sporkel", "Plumpent", "Vewerm", "Tompamm"]},
    {"pic": "learning/PICTURE_606.jpg", "words": ["Lokrast", "Plumpent", "Volkant", "Tompamm", "Nazehl"]},
    {"pic": "learning/PICTURE_308.jpg", "words": ["Ingam", "Volkant", "Straugel", "Nazehl", "Pakel"]},
    {"pic": "learning/PICTURE_321.jpg", "words": ["Mobe", "Straugel", "Veschegt", "Pakel", "Mummbant"]}
]

# Control stimuli (real objects)
CONTROL = [
    {"pic": "control/PICTURE_156.jpg", "words": ["Flöte", "Besen", "Mantel"]},
    {"pic": "control/PICTURE_590.jpg", "words": ["Besen", "Mantel", "Baby"]},
    {"pic": "control/PICTURE_644.jpg", "words": ["Mantel", "Baby", "Bogen"]},
    {"pic": "control/PICTURE_674.jpg", "words": ["Baby", "Bogen", "Flöte"]},
    {"pic": "control/PICTURE_680.jpg", "words": ["Bogen", "Flöte", "Besen"]},
    {"pic": "control/PICTURE_559.jpg", "words": ["Gurke", "Kabel", "Robbe"]},
    {"pic": "control/PICTURE_523.jpg", "words": ["Kabel", "Robbe", "Wespe"]},
    {"pic": "control/PICTURE_92.jpg", "words": ["Robbe", "Wespe", "Kiwi"]},
    {"pic": "control/PICTURE_62.jpg", "words": ["Wespe", "Kiwi", "Gurke"]},
    {"pic": "control/PICTURE_125.jpg", "words": ["Kiwi", "Gurke", "Kabel"]}
]

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def wait_for_trigger(trigger_key=TRIGGER_KEY):
    """Wait for scanner trigger (or keypress in simulation)"""
    if FMRI_MODE:
        # Wait for trigger key
        event.waitKeys(keyList=[trigger_key])
        global_clock.reset()
        return True
    else:
        # Just reset clock
        global_clock.reset()
        return True

def present_fixation(duration=FIXATION_DURATION, pulse_num=None):
    """Present fixation cross"""
    fixation.draw()
    win.flip()
    
    if pulse_num is not None:
        print(f"MRI Pulse: {pulse_num}")
    
    core.wait(duration)

def present_stimulus(pic_path, word, duration=STIM_DURATION):
    """Present picture with word below"""
    # Load and present stimulus
    pres_pic.image = pic_path
    pres_word.text = word
    
    pres_pic.draw()
    pres_word.draw()
    win.flip()
    
    # Wait for duration
    core.wait(duration)

def present_feedback(message, duration=FEEDBACK_DURATION):
    """Present feedback message"""
    feedback_text.text = message
    feedback_text.draw()
    win.flip()
    core.wait(duration)

def present_info_screen(image_path, duration=FIXATION_DURATION):
    """Present information screen"""
    info_pic.image = image_path
    info_pic.draw()
    win.flip()
    core.wait(duration)

def get_response(timeout=STIM_DURATION):
    """Get response with timeout"""
    response = None
    rt = None
    
    # Clear events
    event.clearEvents()
    
    # Wait for response or timeout
    timer = core.Clock()
    while timer.getTime() < timeout:
        keys = event.getKeys(keyList=RESPONSE_KEYS)
        if keys:
            response = keys[0]
            rt = timer.getTime()
            break
        core.wait(0.01)
    
    return response, rt

def create_learning_trials():
    """Create learning trials structure (similar to Task_List in original)"""
    # Initialize block structures
    blk1 = [[None]*4 for _ in range(10)]
    blk2 = [[None]*4 for _ in range(10)]
    
    # Fill block 1 (first 5 stimuli)
    for i in range(5):
        idx = i * 2
        pic = LEARNING[i]["pic"]
        corr_word = LEARNING[i]["words"][0]
        
        for ls in range(4):  # 4 learning stages
            blk1[idx][ls] = f"{pic};{corr_word};{corr_word};c"
            blk1[idx+1][ls] = f"{pic};{LEARNING[i]['words'][ls+1]};{corr_word};i"
    
    # Fill block 2 (next 5 stimuli)
    for i in range(5, 10):
        idx = (i-5) * 2
        pic = LEARNING[i]["pic"]
        corr_word = LEARNING[i]["words"][0]
        
        for ls in range(4):
            blk2[idx][ls] = f"{pic};{corr_word};{corr_word};c"
            blk2[idx+1][ls] = f"{pic};{LEARNING[i]['words'][ls+1]};{corr_word};i"
    
    # Create control block
    ctrl = [[None]*4 for _ in range(10)]
    for i in range(0, 10, 2):
        if i < len(CONTROL):
            pic1 = CONTROL[i]["pic"]
            pic2 = CONTROL[i+1]["pic"] if i+1 < len(CONTROL) else CONTROL[i]["pic"]
            
            for ls in range(4):
                if ls < 2:  # Use first control item
                    ctrl[i][ls] = f"{pic1};{CONTROL[i]['words'][0]};{CONTROL[i]['words'][0]};c"
                    ctrl[i+1][ls] = f"{pic1};{CONTROL[i]['words'][1]};{CONTROL[i]['words'][0]};i"
                else:  # Use second control item
                    ctrl[i][ls] = f"{pic2};{CONTROL[i+1]['words'][0]};{CONTROL[i+1]['words'][0]};c"
                    ctrl[i+1][ls] = f"{pic2};{CONTROL[i+1]['words'][2]};{CONTROL[i+1]['words'][0]};i"
    
    # Organize into task list
    task_list = [[[None]*10 for _ in range(4)] for _ in range(3)]
    
    for ls in range(4):
        for item in range(10):
            task_list[0][ls][item] = blk1[item][ls]  # Block 1 (learning)
            task_list[1][ls][item] = blk2[item][ls]  # Block 2 (learning)
            task_list[2][ls][item] = ctrl[item][ls]  # Block 3 (control)
    
    return task_list

def shuffle_learning_stage(trials):
    """Shuffle trials within learning stage with constraints"""
    shuffled = trials.copy()
    valid = False
    
    while not valid:
        random.shuffle(shuffled)
        valid = True
        
        # Check consecutive trials constraints
        for k in range(len(shuffled)-1):
            parts1 = shuffled[k].split(';')
            parts2 = shuffled[k+1].split(';')
            
            # Check if same picture, same word, or word matches next picture's word
            if (parts1[0] == parts2[0] or 
                parts1[1] == parts2[1] or 
                parts1[2] == parts2[1]):
                valid = False
                break
    
    return shuffled

# =============================================================================
# INSTRUCTION FUNCTIONS (from 00_Instr_1.sce, 02_Instr_2.sce, 04_Instr_3.sce)
# =============================================================================

def show_instructions_part1():
    """Show first set of instructions (00_Instr_1.sce)"""
    # Change to white background
    win.color = BG_COLOR_INSTR
    win.flip()
    
    instr_images = [
        "instr_11.jpg", "instr_12.jpg", "instr_13.jpg", 
        "instr_14.jpg", "instr_15.jpg", "instr_16.jpg", "instr_17.jpg"
    ]
    
    for i, img in enumerate(instr_images):
        img_path = os.path.join(INSTR_PATH, img)
        if os.path.exists(img_path):
            info_pic.image = img_path
            info_pic.draw()
            win.flip()
            
            # Wait for key press (button 1 for most, button 2 for last)
            if i == len(instr_images) - 1:
                event.waitKeys(keyList=['2'])
            else:
                event.waitKeys(keyList=['1'])
    
    # Restore black background
    win.color = BG_COLOR
    win.flip()

def show_instructions_part2():
    """Show second set of instructions (02_Instr_2.sce)"""
    win.color = BG_COLOR_INSTR
    win.flip()
    
    img_path = os.path.join(INSTR_PATH, "instr_21.jpg")
    if os.path.exists(img_path):
        info_pic.image = img_path
        info_pic.draw()
        win.flip()
        event.waitKeys(keyList=['2'])
    
    win.color = BG_COLOR
    win.flip()

def show_instructions_part3():
    """Show third set of instructions (04_Instr_3.sce)"""
    win.color = BG_COLOR_INSTR
    win.flip()
    
    instr_images = ["instr_31.jpg", "instr_32.jpg", "instr_33.jpg", "instr_34.jpg"]
    
    for i, img in enumerate(instr_images):
        img_path = os.path.join(INSTR_PATH, img)
        if os.path.exists(img_path):
            info_pic.image = img_path
            info_pic.draw()
            win.flip()
            
            if i == len(instr_images) - 1:
                event.waitKeys(keyList=['2'])
            else:
                event.waitKeys(keyList=['1'])
    
    win.color = BG_COLOR
    win.flip()

# =============================================================================
# PRACTICE FUNCTION (from 01_Prac.sce)
# =============================================================================

def run_practice():
    """Run practice block"""
    print("Starting practice...")
    
    # Get practice images
    prac_images = []
    if os.path.exists(PRAC_PATH):
        for f in os.listdir(PRAC_PATH):
            if f.endswith('.jpg') or f.endswith('.png'):
                prac_images.append(os.path.join(PRAC_PATH, f))
    
    random.shuffle(prac_images)
    
    # Run 2 repetitions of practice
    for rep in range(2):
        for img_path in prac_images:
            # Determine if correct or incorrect based on filename
            filename = os.path.basename(img_path)
            is_correct = 'k' in filename.lower()
            
            # Present stimulus
            pres_pic.image = img_path
            pres_word.text = "Richtige Position" if is_correct else "Falsche Position"
            
            pres_pic.draw()
            pres_word.draw()
            win.flip()
            core.wait(2.5)  # 2500ms
            
            # Present dash
            feedback_text.text = "-"
            feedback_text.draw()
            win.flip()
            core.wait(2.0)  # 2000ms
        
        # Fixation between reps
        present_fixation()

# =============================================================================
# LEARNING FUNCTION (from 03_learning_final.sce)
# =============================================================================

def run_learning_blocks():
    """Run main learning blocks"""
    print("Starting learning blocks...")
    
    # Create task list
    task_list = create_learning_trials()
    
    # Shuffle learning stages within each block
    for blk in range(3):
        for ls in range(4):
            task_list[blk][ls] = shuffle_learning_stage(task_list[blk][ls])
    
    # Create block order (ensure control not first or last)
    block_order = [0, 1, 2]  # 0=Block1, 1=Block2, 2=Control
    valid_order = False
    while not valid_order:
        random.shuffle(block_order)
        if block_order[0] != 2 and block_order[2] != 2:
            valid_order = True
    
    print(f"Block order: {block_order}")
    
    # Show intro
    feedback_text.text = "Das Experiment\nbeginnt gleich.\nSind Sie bereit?"
    feedback_text.draw()
    win.flip()
    core.wait(1.0)  # 1000ms
    
    # Wait for first trigger
    wait_for_trigger()
    
    pulse = 2  # Start pulse counter
    
    # Run blocks
    for blk_idx, blk_num in enumerate(block_order):
        curr_blk = blk_num
        
        # Determine block type
        if curr_blk == 2:
            info_bubble = hlcb[2]  # Control
            block_type = "control"
        elif blk_idx == len(block_order) - 1:
            info_bubble = hlcb[3]  # Bye (but this will be shown after)
            block_type = "learning"
        else:
            info_bubble = hlcb[1]  # Learning
            block_type = "learning"
        
        # Pre-block fixation (4 pulses)
        for f in range(4):
            if f < 3:
                present_fixation(duration=FIXATION_DURATION)
            else:
                present_info_screen(info_bubble, duration=FIXATION_DURATION)
        
        # Run learning stages
        for ls in range(4):  # 4 learning stages per block
            for trial_idx in range(10):  # 10 trials per stage
                
                # Parse trial info
                trial_str = task_list[curr_blk][ls][trial_idx]
                parts = trial_str.split(';')
                pic_path = os.path.join(STIM_PATH, parts[0])
                pres_word_text = parts[1]
                correct_word = parts[2]
                condition = parts[3]  # 'c' or 'i'
                
                # Store response count before trial
                old_resp_count = len(event.getKeys())
                
                # Present stimulus
                pres_pic.image = pic_path
                pres_word.text = pres_word_text
                
                pres_pic.draw()
                pres_word.draw()
                win.flip()
                
                # Get response
                response, rt = get_response(timeout=STIM_DURATION)
                
                # Present feedback
                if response is None:
                    # No response
                    feedback = f"Zu spät, das ist {correct_word}"
                    correct = 0
                else:
                    # Check if correct
                    if (condition == 'c' and response == CORRECT_KEY) or \
                       (condition == 'i' and response == INCORRECT_KEY):
                        feedback = f"Korrekt, das ist {correct_word}"
                        correct = 1
                    else:
                        feedback = f"Falsch, das ist {correct_word}"
                        correct = 0
                
                # Save data
                data_file.write(f"learning,{blk_idx+1},{ls+1},{pic_path},{pres_word_text},{correct_word},{condition},{response},{rt},{correct}\n")
                data_file.flush()
                
                # Show feedback
                present_feedback(feedback, duration=FEEDBACK_DURATION)
                
                pulse += 1
            
            # Inter-stage fixation
            present_fixation(duration=FIXATION_DURATION)
            pulse += 1
        
        # Post-block fixation if not last
        if blk_idx < len(block_order) - 1:
            present_fixation(duration=FIXATION_DURATION * 4)
        else:
            # Show bye screen
            for f in range(4):
                if f < 3:
                    present_fixation(duration=FIXATION_DURATION)
                else:
                    present_info_screen(hlcb[3], duration=FIXATION_DURATION)

# =============================================================================
# AFC FUNCTIONS (from 04_AFC.sce and 05_AFC.sce)
# =============================================================================

def run_afc():
    """Run AFC (Alternative Forced Choice) task"""
    print("Starting AFC...")
    
    # Show AFC instructions
    show_instructions_part3()
    
    # Get AFC images
    afc_images = []
    if os.path.exists(AFC_PATH):
        for f in os.listdir(AFC_PATH):
            if f.endswith('.jpg') or f.endswith('.png'):
                afc_images.append(os.path.join(AFC_PATH, f))
    
    random.shuffle(afc_images)
    
    # Present each AFC trial
    for img_path in afc_images:
        filename = os.path.basename(img_path)
        
        # Present image
        pres_pic.image = img_path
        pres_pic.draw()
        win.flip()
        
        # Wait for response (keys 1,2,3)
        keys = event.waitKeys(keyList=['1', '2', '3'])
        response = keys[0] if keys else None
        
        # Save data
        data_file.write(f"afc,0,0,{img_path},,,,{response},,0\n")
        data_file.flush()

# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def main():
    """Main experiment function"""
    try:
        # Show initial instructions
        show_instructions_part1()
        
        # Show second set of instructions
        show_instructions_part2()
        
        # Run practice
        run_practice()
        
        # Wait for trigger before main experiment
        print("Waiting for trigger...")
        wait_for_trigger()
        
        # Run main learning blocks
        run_learning_blocks()
        
        # Run AFC task
        run_afc()
        
        # Thank you screen
        feedback_text.text = "Vielen Dank für Ihre Teilnahme!"
        feedback_text.draw()
        win.flip()
        core.wait(3.0)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        data_file.close()
        win.close()
        core.quit()

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()