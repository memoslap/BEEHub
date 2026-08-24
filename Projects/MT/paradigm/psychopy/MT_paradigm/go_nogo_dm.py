#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2024.2.4),
    on November 03, 2025, at 15:09
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
prefs.hardware['audioLib'] = 'ptb'
prefs.hardware['audioLatencyMode'] = '3'
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER, priority)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

import psychopy.iohub as io
from psychopy.hardware import keyboard

# --- Setup global variables (available in all functions) ---
# create a device manager to handle hardware (keyboards, mice, mirophones, speakers, etc.)
deviceManager = hardware.DeviceManager()
# ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
# store info about the experiment session
psychopyVersion = '2024.2.4'
expName = 'go_nogo_dm'  # from the Builder filename that created this script
# information about this experiment
expInfo = {
    'participant': f"{randint(0, 999999):06.0f}",
    'session': '001',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Define some variables which will change depending on pilot mode ---
'''
To run in pilot mode, either use the run/pilot toggle in Builder, Coder and Runner, 
or run the experiment with `--pilot` as an argument. To change what pilot 
#mode does, check out the 'Pilot mode' tab in preferences.
'''
# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()
# start off with values from experiment settings
_fullScr = True
_winSize = [1280, 800]
# if in pilot mode, apply overrides according to preferences
if PILOTING:
    # force windowed mode
    if prefs.piloting['forceWindowed']:
        _fullScr = False
        # set window size
        _winSize = prefs.piloting['forcedWindowSize']

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    Parameters
    ==========
    expInfo : dict
        Information about this experiment.
    
    Returns
    ==========
    dict
        Information about this experiment.
    """
    # show participant info dialog
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    # return expInfo
    return expInfo


def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    dataDir : Path, str or None
        Folder to save the data to, leave as None to create a folder in the current directory.    
    Returns
    ==========
    psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    # remove dialog-specific syntax from expInfo
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)
    
    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)
    
    # an ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(
        name=expName, version='',
        extraInfo=expInfo, runtimeInfo=None,
        originPath='C:\\1_DevuMahesan_Data\\1. Ongoing_Work\\3. MouseTracking\\03 Data Collection\\Program_final_german\\go_nogo_dm.py',
        savePickle=True, saveWideText=True,
        dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    # return experiment handler
    return thisExp


def setupLogging(filename):
    """
    Setup a log file and tell it what level to log at.
    
    Parameters
    ==========
    filename : str or pathlib.Path
        Filename to save log file and data files as, doesn't need an extension.
    
    Returns
    ==========
    psychopy.logging.LogFile
        Text stream to receive inputs from the logging system.
    """
    # set how much information should be printed to the console / app
    if PILOTING:
        logging.console.setLevel(
            prefs.piloting['pilotConsoleLoggingLevel']
        )
    else:
        logging.console.setLevel('warning')
    # save a log file for detail verbose info
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(
            prefs.piloting['pilotLoggingLevel']
        )
    else:
        logFile.setLevel(
            logging.getLevel('info')
        )
    
    return logFile


def setupWindow(expInfo=None, win=None):
    """
    Setup the Window
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    win : psychopy.visual.Window
        Window to setup - leave as None to create a new window.
    
    Returns
    ==========
    psychopy.visual.Window
        Window in which to run this experiment.
    """
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')
    
    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=0,
            winType='pyglet', allowGUI=True, allowStencil=False,
            monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
            backgroundImage='', backgroundFit='none',
            blendMode='avg', useFBO=True,
            units='pix',
            checkTiming=False  # we're going to do this ourselves in a moment
        )
    else:
        # if we have a window, just set the attributes which are safe to set
        win.color = [0,0,0]
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'pix'
    if expInfo is not None:
        # get/measure frame rate if not already in expInfo
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='')
        expInfo['frameRate'] = win._monitorFrameRate
    win.hideMessage()
    # show a visual indicator if we're in piloting mode
    if PILOTING and prefs.piloting['showPilotingIndicator']:
        win.showPilotingIndicator()
    
    return win


def setupDevices(expInfo, thisExp, win):
    """
    Setup whatever devices are available (mouse, keyboard, speaker, eyetracker, etc.) and add them to 
    the device manager (deviceManager)
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window in which to run this experiment.
    Returns
    ==========
    bool
        True if completed successfully.
    """
    # --- Setup input devices ---
    ioConfig = {}
    
    # Setup iohub keyboard
    ioConfig['Keyboard'] = dict(use_keymap='psychopy')
    
    # Setup iohub experiment
    ioConfig['Experiment'] = dict(filename=thisExp.dataFileName)
    
    # Start ioHub server
    ioServer = io.launchHubServer(window=win, **ioConfig)
    
    # store ioServer object in the device manager
    deviceManager.ioServer = ioServer
    
    # create a default keyboard (e.g. to check for escape)
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='iohub'
        )
    if deviceManager.getDevice('welcome_resp') is None:
        # initialise welcome_resp
        welcome_resp = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='welcome_resp',
        )
    if deviceManager.getDevice('inst_resp') is None:
        # initialise inst_resp
        inst_resp = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='inst_resp',
        )
    if deviceManager.getDevice('inst_resp_2') is None:
        # initialise inst_resp_2
        inst_resp_2 = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='inst_resp_2',
        )
    if deviceManager.getDevice('resp_Exp_begin') is None:
        # initialise resp_Exp_begin
        resp_Exp_begin = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='resp_Exp_begin',
        )
    if deviceManager.getDevice('resp_Exp_begin_2') is None:
        # initialise resp_Exp_begin_2
        resp_Exp_begin_2 = deviceManager.addDevice(
            deviceClass='keyboard',
            deviceName='resp_Exp_begin_2',
        )
    # return True if completed successfully
    return True

def pauseExperiment(thisExp, win=None, timers=[], playbackComponents=[]):
    """
    Pause this experiment, preventing the flow from advancing to the next routine until resumed.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    timers : list, tuple
        List of timers to reset once pausing is finished.
    playbackComponents : list, tuple
        List of any components with a `pause` method which need to be paused.
    """
    # if we are not paused, do nothing
    if thisExp.status != PAUSED:
        return
    
    # start a timer to figure out how long we're paused for
    pauseTimer = core.Clock()
    # pause any playback components
    for comp in playbackComponents:
        comp.pause()
    # make sure we have a keyboard
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend='ioHub',
        )
    # run a while loop while we wait to unpause
    while thisExp.status == PAUSED:
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=['escape']):
            endExperiment(thisExp, win=win)
        # sleep 1ms so other threads can execute
        clock.time.sleep(0.001)
    # if stop was requested while paused, quit
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    # resume any playback components
    for comp in playbackComponents:
        comp.play()
    # reset any timers
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())


def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    """
    Run the experiment flow.
    
    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    psychopy.visual.Window
        Window in which to run this experiment.
    globalClock : psychopy.core.clock.Clock or None
        Clock to get global time from - supply None to make a new one.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    # mark experiment as started
    thisExp.status = STARTED
    # make sure window is set to foreground to prevent losing focus
    win.winHandle.activate()
    # make sure variables created by exec are available globally
    exec = environmenttools.setExecEnvironment(globals())
    # get device handles from dict of input devices
    ioServer = deviceManager.ioServer
    # get/create a default keyboard (e.g. to check for escape)
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='ioHub'
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    # make sure we're running in the directory for this experiment
    os.chdir(_thisDir)
    # get filename from ExperimentHandler for convenience
    filename = thisExp.dataFileName
    frameTolerance = 0.001  # how close to onset before 'same' frame
    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    # get frame duration from frame rate in expInfo
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess
    
    # Start Code - component code to be run after the window creation
    
    # --- Initialize components for Routine "welcome" ---
    welcome_text = visual.TextStim(win=win, name='welcome_text',
        text='Herzlich willkommen zum Experiment "Go-Path"\n\nBitte drücken Sie die Leertaste um fortzufahren',
        font='Arial',
        pos=(0, 0), draggable=False, height=40.0, wrapWidth=1500.0, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    welcome_resp = keyboard.Keyboard(deviceName='welcome_resp')
    
    # --- Initialize components for Routine "instruction" ---
    image = visual.ImageStim(
        win=win,
        name='image', 
        image='Slide7.PNG', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(1536, 864),
        color=[1,1,1], colorSpace='rgb', opacity=None,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)
    inst_resp = keyboard.Keyboard(deviceName='inst_resp')
    
    # --- Initialize components for Routine "instruction_2" ---
    image_2 = visual.ImageStim(
        win=win,
        name='image_2', 
        image='Slide8.PNG', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(1536, 864),
        color=[1,1,1], colorSpace='rgb', opacity=None,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)
    inst_resp_2 = keyboard.Keyboard(deviceName='inst_resp_2')
    
    # --- Initialize components for Routine "expStart" ---
    exp_start_inst = visual.TextStim(win=win, name='exp_start_inst',
        text='Es werden zwei Übungsdurchläufe durchgeführt:\n\nBlock 1: Sie sehen nur die Ziffern „go“ (2, 3, 4, 6, 7 oder 8). Bitte bewegen Sie die Maus auf das weiße Feld, um zu antworten.\n\nBlock 2: Hier sehen Sie neben den Go-Ziffern gelegentlich auch die No-Go-Ziffern (1 oder 9). \n\nBitte halten Sie die Bewegung sofort an, wenn Sie die No-Go-Ziffer sehen. \nReagieren Sie mit einem Klick in das weiße Feld, wenn Sie eine Go-Ziffer sehen. \n\n\nDrücken Sie die Leertaste, um mit Block 1 der Übungsversuche zu beginnen.',
        font='Arial',
        pos=(0, 0), draggable=False, height=40.0, wrapWidth=1500.0, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    resp_Exp_begin = keyboard.Keyboard(deviceName='resp_Exp_begin')
    
    # --- Initialize components for Routine "block_setup" ---
    
    # --- Initialize components for Routine "start_hold" ---
    fixation_cross_3 = visual.TextStim(win=win, name='fixation_cross_3',
        text='+',
        font='Arial',
        pos=(0, 0), draggable=False, height=30.0, wrapWidth=None, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=0.0);
    start_box = visual.Rect(
        win=win, name='start_box',
        width=(100, 100)[0], height=(100, 100)[1],
        ori=0.0, pos=(0, -400), draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='black', fillColor=[-1.0000, -1.0000, 1.0000],
        opacity=None, depth=-1.0, interpolate=True)
    mouse_start = event.Mouse(win=win)
    x, y = [None, None]
    mouse_start.mouseClock = core.Clock()
    # Run 'Begin Experiment' code from code
    # Add this to Begin Experiment section of your first routine
    import time
    mouse_sampling_rate = 0.01  # 100 Hz sampling
    
    
    
    # --- Initialize components for Routine "threshold" ---
    start_box_2 = visual.Rect(
        win=win, name='start_box_2',
        width=(100, 100)[0], height=(100, 100)[1],
        ori=0.0, pos=(0, -400), draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='black', fillColor='black',
        opacity=None, depth=0.0, interpolate=True)
    response_box = visual.Rect(
        win=win, name='response_box',
        width=(100, 100)[0], height=(100, 100)[1],
        ori=0.0, pos=(200, 300), draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='black', fillColor='white',
        opacity=None, depth=-1.0, interpolate=True)
    mouse_fix = event.Mouse(win=win)
    x, y = [None, None]
    mouse_fix.mouseClock = core.Clock()
    
    # --- Initialize components for Routine "stimulus" ---
    start_box_3 = visual.Rect(
        win=win, name='start_box_3',
        width=(100, 100)[0], height=(100, 100)[1],
        ori=0.0, pos=(0, -400), draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='black', fillColor='black',
        opacity=None, depth=-1.0, interpolate=True)
    response_box_2 = visual.Rect(
        win=win, name='response_box_2',
        width=(100, 100)[0], height=(100, 100)[1],
        ori=0.0, pos=(200, 300), draggable=False, anchor='center',
        lineWidth=1.0,
        colorSpace='rgb', lineColor='black', fillColor='white',
        opacity=None, depth=-2.0, interpolate=True)
    text_stimulus = visual.TextStim(win=win, name='text_stimulus',
        text='',
        font='Arial',
        pos=(200, 300), draggable=False, height=72.0, wrapWidth=None, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-3.0);
    mouse_resp = event.Mouse(win=win)
    x, y = [None, None]
    mouse_resp.mouseClock = core.Clock()
    # Run 'Begin Experiment' code from code_3
    import numpy as np
    
    # --- Initialize components for Routine "ITI" ---
    # Run 'Begin Experiment' code from code_4
    # Set up possible ITI durations
    possible_iti_durations = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]  # 500-1000ms in 100ms increments
    
    # Add a mouse component for the ITI period
    mouse_iti = event.Mouse(win=win)
    x, y = [None, None]
    mouse_iti.mouseClock = core.Clock()
    # Initialize trajectory arrays
    # Always re-initialize ITI trajectory arrays
    iti_trajectory_x = []
    iti_trajectory_y = []
    iti_trajectory_time = []
    iti_velocity_x = []
    iti_velocity_y = []
    iti_velocity_mag = []
    blank = visual.TextStim(win=win, name='blank',
        text='.',
        font='Arial',
        pos=(0, 0), draggable=False, height=1.0, wrapWidth=None, ori=0.0, 
        color='white', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    mouse_iti = event.Mouse(win=win)
    x, y = [None, None]
    mouse_iti.mouseClock = core.Clock()
    
    # --- Initialize components for Routine "block_end" ---
    block_end_text = visual.TextStim(win=win, name='block_end_text',
        text=None,
        font='Arial',
        pos=(0, 0), draggable=False, height=40.0, wrapWidth=1500.0, ori=0.0, 
        color='black', colorSpace='rgb', opacity=None, 
        languageStyle='LTR',
        depth=-1.0);
    resp_Exp_begin_2 = keyboard.Keyboard(deviceName='resp_Exp_begin_2')
    
    # create some handy timers
    
    # global clock to track the time since experiment started
    if globalClock is None:
        # create a clock if not given one
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        # if given a string, make a clock accoridng to it
        if globalClock == 'float':
            # get timestamps as a simple value
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            # get timestamps in ISO format
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            # get timestamps in a custom format
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    # routine timer to track time remaining of each (possibly non-slip) routine
    routineTimer = core.Clock()
    win.flip()  # flip window to reset last flip timer
    # store the exact time the global clock started
    expInfo['expStart'] = data.getDateStr(
        format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6
    )
    
    # --- Prepare to start Routine "welcome" ---
    # create an object to store info about Routine welcome
    welcome = data.Routine(
        name='welcome',
        components=[welcome_text, welcome_resp],
    )
    welcome.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for welcome_resp
    welcome_resp.keys = []
    welcome_resp.rt = []
    _welcome_resp_allKeys = []
    # store start times for welcome
    welcome.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    welcome.tStart = globalClock.getTime(format='float')
    welcome.status = STARTED
    thisExp.addData('welcome.started', welcome.tStart)
    welcome.maxDuration = None
    # keep track of which components have finished
    welcomeComponents = welcome.components
    for thisComponent in welcome.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "welcome" ---
    welcome.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *welcome_text* updates
        
        # if welcome_text is starting this frame...
        if welcome_text.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            welcome_text.frameNStart = frameN  # exact frame index
            welcome_text.tStart = t  # local t and not account for scr refresh
            welcome_text.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(welcome_text, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'welcome_text.started')
            # update status
            welcome_text.status = STARTED
            welcome_text.setAutoDraw(True)
        
        # if welcome_text is active this frame...
        if welcome_text.status == STARTED:
            # update params
            pass
        
        # *welcome_resp* updates
        waitOnFlip = False
        
        # if welcome_resp is starting this frame...
        if welcome_resp.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            welcome_resp.frameNStart = frameN  # exact frame index
            welcome_resp.tStart = t  # local t and not account for scr refresh
            welcome_resp.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(welcome_resp, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'welcome_resp.started')
            # update status
            welcome_resp.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(welcome_resp.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(welcome_resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if welcome_resp.status == STARTED and not waitOnFlip:
            theseKeys = welcome_resp.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
            _welcome_resp_allKeys.extend(theseKeys)
            if len(_welcome_resp_allKeys):
                welcome_resp.keys = _welcome_resp_allKeys[-1].name  # just the last key pressed
                welcome_resp.rt = _welcome_resp_allKeys[-1].rt
                welcome_resp.duration = _welcome_resp_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            welcome.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in welcome.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "welcome" ---
    for thisComponent in welcome.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for welcome
    welcome.tStop = globalClock.getTime(format='float')
    welcome.tStopRefresh = tThisFlipGlobal
    thisExp.addData('welcome.stopped', welcome.tStop)
    # check responses
    if welcome_resp.keys in ['', [], None]:  # No response was made
        welcome_resp.keys = None
    thisExp.addData('welcome_resp.keys',welcome_resp.keys)
    if welcome_resp.keys != None:  # we had a response
        thisExp.addData('welcome_resp.rt', welcome_resp.rt)
        thisExp.addData('welcome_resp.duration', welcome_resp.duration)
    thisExp.nextEntry()
    # the Routine "welcome" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "instruction" ---
    # create an object to store info about Routine instruction
    instruction = data.Routine(
        name='instruction',
        components=[image, inst_resp],
    )
    instruction.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for inst_resp
    inst_resp.keys = []
    inst_resp.rt = []
    _inst_resp_allKeys = []
    # store start times for instruction
    instruction.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    instruction.tStart = globalClock.getTime(format='float')
    instruction.status = STARTED
    thisExp.addData('instruction.started', instruction.tStart)
    instruction.maxDuration = None
    # keep track of which components have finished
    instructionComponents = instruction.components
    for thisComponent in instruction.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "instruction" ---
    instruction.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *image* updates
        
        # if image is starting this frame...
        if image.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            image.frameNStart = frameN  # exact frame index
            image.tStart = t  # local t and not account for scr refresh
            image.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(image, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'image.started')
            # update status
            image.status = STARTED
            image.setAutoDraw(True)
        
        # if image is active this frame...
        if image.status == STARTED:
            # update params
            pass
        
        # *inst_resp* updates
        waitOnFlip = False
        
        # if inst_resp is starting this frame...
        if inst_resp.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            inst_resp.frameNStart = frameN  # exact frame index
            inst_resp.tStart = t  # local t and not account for scr refresh
            inst_resp.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(inst_resp, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'inst_resp.started')
            # update status
            inst_resp.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(inst_resp.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(inst_resp.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if inst_resp.status == STARTED and not waitOnFlip:
            theseKeys = inst_resp.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
            _inst_resp_allKeys.extend(theseKeys)
            if len(_inst_resp_allKeys):
                inst_resp.keys = _inst_resp_allKeys[-1].name  # just the last key pressed
                inst_resp.rt = _inst_resp_allKeys[-1].rt
                inst_resp.duration = _inst_resp_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            instruction.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in instruction.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "instruction" ---
    for thisComponent in instruction.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for instruction
    instruction.tStop = globalClock.getTime(format='float')
    instruction.tStopRefresh = tThisFlipGlobal
    thisExp.addData('instruction.stopped', instruction.tStop)
    # check responses
    if inst_resp.keys in ['', [], None]:  # No response was made
        inst_resp.keys = None
    thisExp.addData('inst_resp.keys',inst_resp.keys)
    if inst_resp.keys != None:  # we had a response
        thisExp.addData('inst_resp.rt', inst_resp.rt)
        thisExp.addData('inst_resp.duration', inst_resp.duration)
    thisExp.nextEntry()
    # the Routine "instruction" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "instruction_2" ---
    # create an object to store info about Routine instruction_2
    instruction_2 = data.Routine(
        name='instruction_2',
        components=[image_2, inst_resp_2],
    )
    instruction_2.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for inst_resp_2
    inst_resp_2.keys = []
    inst_resp_2.rt = []
    _inst_resp_2_allKeys = []
    # store start times for instruction_2
    instruction_2.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    instruction_2.tStart = globalClock.getTime(format='float')
    instruction_2.status = STARTED
    thisExp.addData('instruction_2.started', instruction_2.tStart)
    instruction_2.maxDuration = None
    # keep track of which components have finished
    instruction_2Components = instruction_2.components
    for thisComponent in instruction_2.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "instruction_2" ---
    instruction_2.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *image_2* updates
        
        # if image_2 is starting this frame...
        if image_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            image_2.frameNStart = frameN  # exact frame index
            image_2.tStart = t  # local t and not account for scr refresh
            image_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(image_2, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'image_2.started')
            # update status
            image_2.status = STARTED
            image_2.setAutoDraw(True)
        
        # if image_2 is active this frame...
        if image_2.status == STARTED:
            # update params
            pass
        
        # *inst_resp_2* updates
        waitOnFlip = False
        
        # if inst_resp_2 is starting this frame...
        if inst_resp_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            inst_resp_2.frameNStart = frameN  # exact frame index
            inst_resp_2.tStart = t  # local t and not account for scr refresh
            inst_resp_2.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(inst_resp_2, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'inst_resp_2.started')
            # update status
            inst_resp_2.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(inst_resp_2.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(inst_resp_2.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if inst_resp_2.status == STARTED and not waitOnFlip:
            theseKeys = inst_resp_2.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
            _inst_resp_2_allKeys.extend(theseKeys)
            if len(_inst_resp_2_allKeys):
                inst_resp_2.keys = _inst_resp_2_allKeys[-1].name  # just the last key pressed
                inst_resp_2.rt = _inst_resp_2_allKeys[-1].rt
                inst_resp_2.duration = _inst_resp_2_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            instruction_2.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in instruction_2.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "instruction_2" ---
    for thisComponent in instruction_2.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for instruction_2
    instruction_2.tStop = globalClock.getTime(format='float')
    instruction_2.tStopRefresh = tThisFlipGlobal
    thisExp.addData('instruction_2.stopped', instruction_2.tStop)
    # check responses
    if inst_resp_2.keys in ['', [], None]:  # No response was made
        inst_resp_2.keys = None
    thisExp.addData('inst_resp_2.keys',inst_resp_2.keys)
    if inst_resp_2.keys != None:  # we had a response
        thisExp.addData('inst_resp_2.rt', inst_resp_2.rt)
        thisExp.addData('inst_resp_2.duration', inst_resp_2.duration)
    thisExp.nextEntry()
    # the Routine "instruction_2" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # --- Prepare to start Routine "expStart" ---
    # create an object to store info about Routine expStart
    expStart = data.Routine(
        name='expStart',
        components=[exp_start_inst, resp_Exp_begin],
    )
    expStart.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # create starting attributes for resp_Exp_begin
    resp_Exp_begin.keys = []
    resp_Exp_begin.rt = []
    _resp_Exp_begin_allKeys = []
    # store start times for expStart
    expStart.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    expStart.tStart = globalClock.getTime(format='float')
    expStart.status = STARTED
    thisExp.addData('expStart.started', expStart.tStart)
    expStart.maxDuration = None
    # keep track of which components have finished
    expStartComponents = expStart.components
    for thisComponent in expStart.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1
    
    # --- Run Routine "expStart" ---
    expStart.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *exp_start_inst* updates
        
        # if exp_start_inst is starting this frame...
        if exp_start_inst.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            exp_start_inst.frameNStart = frameN  # exact frame index
            exp_start_inst.tStart = t  # local t and not account for scr refresh
            exp_start_inst.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(exp_start_inst, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'exp_start_inst.started')
            # update status
            exp_start_inst.status = STARTED
            exp_start_inst.setAutoDraw(True)
        
        # if exp_start_inst is active this frame...
        if exp_start_inst.status == STARTED:
            # update params
            pass
        
        # *resp_Exp_begin* updates
        waitOnFlip = False
        
        # if resp_Exp_begin is starting this frame...
        if resp_Exp_begin.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            resp_Exp_begin.frameNStart = frameN  # exact frame index
            resp_Exp_begin.tStart = t  # local t and not account for scr refresh
            resp_Exp_begin.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(resp_Exp_begin, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'resp_Exp_begin.started')
            # update status
            resp_Exp_begin.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(resp_Exp_begin.clock.reset)  # t=0 on next screen flip
            win.callOnFlip(resp_Exp_begin.clearEvents, eventType='keyboard')  # clear events on next screen flip
        if resp_Exp_begin.status == STARTED and not waitOnFlip:
            theseKeys = resp_Exp_begin.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
            _resp_Exp_begin_allKeys.extend(theseKeys)
            if len(_resp_Exp_begin_allKeys):
                resp_Exp_begin.keys = _resp_Exp_begin_allKeys[-1].name  # just the last key pressed
                resp_Exp_begin.rt = _resp_Exp_begin_allKeys[-1].rt
                resp_Exp_begin.duration = _resp_Exp_begin_allKeys[-1].duration
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp, 
                win=win, 
                timers=[routineTimer], 
                playbackComponents=[]
            )
            # skip the frame we paused on
            continue
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            expStart.forceEnded = routineForceEnded = True
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in expStart.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # --- Ending Routine "expStart" ---
    for thisComponent in expStart.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for expStart
    expStart.tStop = globalClock.getTime(format='float')
    expStart.tStopRefresh = tThisFlipGlobal
    thisExp.addData('expStart.stopped', expStart.tStop)
    # check responses
    if resp_Exp_begin.keys in ['', [], None]:  # No response was made
        resp_Exp_begin.keys = None
    thisExp.addData('resp_Exp_begin.keys',resp_Exp_begin.keys)
    if resp_Exp_begin.keys != None:  # we had a response
        thisExp.addData('resp_Exp_begin.rt', resp_Exp_begin.rt)
        thisExp.addData('resp_Exp_begin.duration', resp_Exp_begin.duration)
    thisExp.nextEntry()
    # the Routine "expStart" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # set up handler to look after randomisation of conditions etc
    blocks_loop = data.TrialHandler2(
        name='blocks_loop',
        nReps=1.0, 
        method='sequential', 
        extraInfo=expInfo, 
        originPath=-1, 
        trialList=data.importConditions('block_sequence.xlsx'), 
        seed=None, 
    )
    thisExp.addLoop(blocks_loop)  # add the loop to the experiment
    thisBlocks_loop = blocks_loop.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisBlocks_loop.rgb)
    if thisBlocks_loop != None:
        for paramName in thisBlocks_loop:
            globals()[paramName] = thisBlocks_loop[paramName]
    
    for thisBlocks_loop in blocks_loop:
        currentLoop = blocks_loop
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        # abbreviate parameter names if possible (e.g. rgb = thisBlocks_loop.rgb)
        if thisBlocks_loop != None:
            for paramName in thisBlocks_loop:
                globals()[paramName] = thisBlocks_loop[paramName]
        
        # --- Prepare to start Routine "block_setup" ---
        # create an object to store info about Routine block_setup
        block_setup = data.Routine(
            name='block_setup',
            components=[],
        )
        block_setup.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from code_9
        import pandas as pd
        import random
        
        block_type = thisBlocks_loop['block_type']
        trials_file = thisBlocks_loop['trials_file']
        data_folder = os.path.dirname(filename)
        
        # Default path from Excel file
        original_file = trials_file
        
        # If it's go_nogo, apply the NoGo constraint
        if block_type == "go_nogo":
            df = pd.read_excel(original_file)
            
            for attempt in range(1000):
                df_shuffled = df.sample(frac=1).reset_index(drop=True)
                nogo_indices = df_shuffled.index[df_shuffled['trial_type'] == 'nogo'].tolist()
                if all(nogo_indices[i+1] - nogo_indices[i] >= 2 for i in range(len(nogo_indices) - 1)):
                    print(f"✅ Valid Go+NoGo sequence created on attempt {attempt+1}")
                    break
            else:
                print("⚠️ Could not create valid sequence — using unshuffled.")
                df_shuffled = df
        
            trials_file = os.path.join(data_folder, "temp_go_nogo_shuffled.xlsx")
            df_shuffled.to_excel(trials_file, index=False)
        
        elif block_type in ["go_only", "go_only_prac", "go_nogo_prac"]:
            df = pd.read_excel(original_file)
            df_shuffled = df.sample(frac=1).reset_index(drop=True)
            trials_file = os.path.join(data_folder, f"temp_{block_type}_shuffled.xlsx")
            df_shuffled.to_excel(trials_file, index=False)
            print(f"✅ Shuffled {block_type} saved to {trials_file}")
        
        else:
            print(f"⚠️ Unrecognized block_type: {block_type}")
        
        # store start times for block_setup
        block_setup.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        block_setup.tStart = globalClock.getTime(format='float')
        block_setup.status = STARTED
        thisExp.addData('block_setup.started', block_setup.tStart)
        block_setup.maxDuration = None
        # keep track of which components have finished
        block_setupComponents = block_setup.components
        for thisComponent in block_setup.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "block_setup" ---
        # if trial has changed, end Routine now
        if isinstance(blocks_loop, data.TrialHandler2) and thisBlocks_loop.thisN != blocks_loop.thisTrial.thisN:
            continueRoutine = False
        block_setup.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                block_setup.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in block_setup.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "block_setup" ---
        for thisComponent in block_setup.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for block_setup
        block_setup.tStop = globalClock.getTime(format='float')
        block_setup.tStopRefresh = tThisFlipGlobal
        thisExp.addData('block_setup.stopped', block_setup.tStop)
        # the Routine "block_setup" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        
        # set up handler to look after randomisation of conditions etc
        trials = data.TrialHandler2(
            name='trials',
            nReps=1.0, 
            method='sequential', 
            extraInfo=expInfo, 
            originPath=-1, 
            trialList=data.importConditions(trials_file), 
            seed=None, 
        )
        thisExp.addLoop(trials)  # add the loop to the experiment
        thisTrial = trials.trialList[0]  # so we can initialise stimuli with some values
        # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
        if thisTrial != None:
            for paramName in thisTrial:
                globals()[paramName] = thisTrial[paramName]
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        
        for thisTrial in trials:
            currentLoop = trials
            thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
            if thisSession is not None:
                # if running in a Session with a Liaison client, send data up to now
                thisSession.sendExperimentData()
            # abbreviate parameter names if possible (e.g. rgb = thisTrial.rgb)
            if thisTrial != None:
                for paramName in thisTrial:
                    globals()[paramName] = thisTrial[paramName]
            
            # --- Prepare to start Routine "start_hold" ---
            # create an object to store info about Routine start_hold
            start_hold = data.Routine(
                name='start_hold',
                components=[fixation_cross_3, start_box, mouse_start],
            )
            start_hold.status = NOT_STARTED
            continueRoutine = True
            # update component parameters for each repeat
            # setup some python lists for storing info about the mouse_start
            mouse_start.x = []
            mouse_start.y = []
            mouse_start.leftButton = []
            mouse_start.midButton = []
            mouse_start.rightButton = []
            mouse_start.time = []
            gotValidClick = False  # until a click is received
            # Run 'Begin Routine' code from code
            # Reset variables
            hold_timer = core.Clock()
            hold_complete = False
            hold_duration = 0.5  # 500ms required hold time
            in_start_box = False
            
            # Initialize trajectory arrays
            last_mouse_sample_time_start = time.time()
            start_trajectory_x = []
            start_trajectory_y = []
            start_trajectory_time = []
            current_pos = [0, 0]   
                
            if trials.thisN == 0:
                print("=== FINAL EXECUTION ORDER ===")
                for i, t in enumerate(trials.trialList):
                    print(f"{i+1:02}: digit={t['digit']}, type={t['trial_type']}")
            
            # store start times for start_hold
            start_hold.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            start_hold.tStart = globalClock.getTime(format='float')
            start_hold.status = STARTED
            thisExp.addData('start_hold.started', start_hold.tStart)
            start_hold.maxDuration = None
            # keep track of which components have finished
            start_holdComponents = start_hold.components
            for thisComponent in start_hold.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1
            
            # --- Run Routine "start_hold" ---
            # if trial has changed, end Routine now
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            start_hold.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                # get current time
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame
                
                # *fixation_cross_3* updates
                
                # if fixation_cross_3 is starting this frame...
                if fixation_cross_3.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    fixation_cross_3.frameNStart = frameN  # exact frame index
                    fixation_cross_3.tStart = t  # local t and not account for scr refresh
                    fixation_cross_3.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(fixation_cross_3, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'fixation_cross_3.started')
                    # update status
                    fixation_cross_3.status = STARTED
                    fixation_cross_3.setAutoDraw(True)
                
                # if fixation_cross_3 is active this frame...
                if fixation_cross_3.status == STARTED:
                    # update params
                    pass
                
                # if fixation_cross_3 is stopping this frame...
                if fixation_cross_3.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > fixation_cross_3.tStartRefresh + 0.5-frameTolerance:
                        # keep track of stop time/frame for later
                        fixation_cross_3.tStop = t  # not accounting for scr refresh
                        fixation_cross_3.tStopRefresh = tThisFlipGlobal  # on global time
                        fixation_cross_3.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.timestampOnFlip(win, 'fixation_cross_3.stopped')
                        # update status
                        fixation_cross_3.status = FINISHED
                        fixation_cross_3.setAutoDraw(False)
                
                # *start_box* updates
                
                # if start_box is starting this frame...
                if start_box.status == NOT_STARTED and tThisFlip >= 0-frameTolerance:
                    # keep track of start time/frame for later
                    start_box.frameNStart = frameN  # exact frame index
                    start_box.tStart = t  # local t and not account for scr refresh
                    start_box.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(start_box, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'start_box.started')
                    # update status
                    start_box.status = STARTED
                    start_box.setAutoDraw(True)
                
                # if start_box is active this frame...
                if start_box.status == STARTED:
                    # update params
                    pass
                # *mouse_start* updates
                
                # if mouse_start is starting this frame...
                if mouse_start.status == NOT_STARTED and t >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    mouse_start.frameNStart = frameN  # exact frame index
                    mouse_start.tStart = t  # local t and not account for scr refresh
                    mouse_start.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(mouse_start, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.addData('mouse_start.started', t)
                    # update status
                    mouse_start.status = STARTED
                    mouse_start.mouseClock.reset()
                    prevButtonState = mouse_start.getPressed()  # if button is down already this ISN'T a new click
                if mouse_start.status == STARTED:  # only update if started and not finished!
                    x, y = mouse_start.getPos()
                    mouse_start.x.append(x)
                    mouse_start.y.append(y)
                    buttons = mouse_start.getPressed()
                    mouse_start.leftButton.append(buttons[0])
                    mouse_start.midButton.append(buttons[1])
                    mouse_start.rightButton.append(buttons[2])
                    mouse_start.time.append(mouse_start.mouseClock.getTime())
                # Run 'Each Frame' code from code
                current_time = time.time()
                current_pos = mouse_start.getPos()
                # Only record data at specified sampling rate
                if current_time - last_mouse_sample_time_start >= mouse_sampling_rate:
                    # Get current mouse position with controlled sampling
                    current_pos = mouse_start.getPos()
                    current_frame_time = globalClock.getTime()
                    
                    # Add to trajectory with controlled sampling
                    start_trajectory_x.append(current_pos[0])
                    start_trajectory_y.append(current_pos[1])
                    start_trajectory_time.append(current_frame_time)
                    
                    # Update last sample time
                    last_mouse_sample_time_start = current_time
                
                # Check if mouse is in start box - by calculating if position is within box boundaries
                start_box_left = start_box.pos[0] - start_box.size[0]/2
                start_box_right = start_box.pos[0] + start_box.size[0]/2
                start_box_bottom = start_box.pos[1] - start_box.size[1]/2  
                start_box_top = start_box.pos[1] + start_box.size[1]/2
                
                # Check if mouse position is within box boundaries
                tolerance = 5  # pixels
                mouse_in_box = (current_pos[0] >= start_box_left - tolerance and 
                                current_pos[0] <= start_box_right + tolerance and 
                                current_pos[1] >= start_box_bottom - tolerance and 
                                current_pos[1] <= start_box_top + tolerance)
                
                # MODIFIED SECTION: Make sure we always start with blue box and reset timer at trial start
                if frameN <= 1:  # Only during the first frame of the routine
                    in_start_box = False
                    hold_timer.reset()
                    start_box.fillColor = [-1, -1, 1]  # Set to blue at the start of trial
                    
                if mouse_in_box:
                    if not in_start_box:  # Just entered the box
                        hold_timer.reset()
                        in_start_box = True
                    
                    # Check if hold time is complete (500ms)
                    if hold_timer.getTime() >= hold_duration:
                        hold_complete = True
                        start_box.fillColor = [-1, -1, -1]  # Change to black when hold complete
                        continueRoutine = False  # End routine, move to next
                else:
                    # Reset if mouse leaves box before hold is complete
                    in_start_box = False
                    hold_timer.reset()
                    start_box.fillColor = [-1, -1, 1]  # Back to blue
                    
                
                
                # check for quit (typically the Esc key)
                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return
                # pause experiment here if requested
                if thisExp.status == PAUSED:
                    pauseExperiment(
                        thisExp=thisExp, 
                        win=win, 
                        timers=[routineTimer], 
                        playbackComponents=[]
                    )
                    # skip the frame we paused on
                    continue
                
                # check if all components have finished
                if not continueRoutine:  # a component has requested a forced-end of Routine
                    start_hold.forceEnded = routineForceEnded = True
                    break
                continueRoutine = False  # will revert to True if at least one component still running
                for thisComponent in start_hold.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished
                
                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()
            
            # --- Ending Routine "start_hold" ---
            for thisComponent in start_hold.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            # store stop times for start_hold
            start_hold.tStop = globalClock.getTime(format='float')
            start_hold.tStopRefresh = tThisFlipGlobal
            thisExp.addData('start_hold.stopped', start_hold.tStop)
            # store data for trials (TrialHandler)
            trials.addData('mouse_start.x', mouse_start.x)
            trials.addData('mouse_start.y', mouse_start.y)
            trials.addData('mouse_start.leftButton', mouse_start.leftButton)
            trials.addData('mouse_start.midButton', mouse_start.midButton)
            trials.addData('mouse_start.rightButton', mouse_start.rightButton)
            trials.addData('mouse_start.time', mouse_start.time)
            # Run 'End Routine' code from code
            # Record if hold was successful
            thisExp.addData('hold_complete', hold_complete)
            # End Routine code for start_hold
            thisExp.addData('start_trajectory_x', start_trajectory_x)
            thisExp.addData('start_trajectory_y', start_trajectory_y)
            thisExp.addData('start_trajectory_time', start_trajectory_time)
            # the Routine "start_hold" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()
            
            # --- Prepare to start Routine "threshold" ---
            # create an object to store info about Routine threshold
            threshold = data.Routine(
                name='threshold',
                components=[start_box_2, response_box, mouse_fix],
            )
            threshold.status = NOT_STARTED
            continueRoutine = True
            # update component parameters for each repeat
            # setup some python lists for storing info about the mouse_fix
            mouse_fix.x = []
            mouse_fix.y = []
            mouse_fix.leftButton = []
            mouse_fix.midButton = []
            mouse_fix.rightButton = []
            mouse_fix.time = []
            gotValidClick = False  # until a click is received
            # Run 'Begin Routine' code from code_2
            # Initialize variables
            start_pos = [0, -400]  # Start box position
            threshold_y = start_pos[1] + 100  # 100px above start box
            corridor_width = 300  # Width of movement corridor
            
            last_mouse_sample_time_threshold = time.time()
            movement_initiated = False
            threshold_crossed = False
            fix_timer = core.Clock()
            max_wait_time = 5.0  # 5000ms max wait for movement
            timeout_occurred = False
            
            # Initialize trajectory arrays
            # Always re-initialize arrays for each trial
            threshold_trajectory_x = []
            threshold_trajectory_y = []
            threshold_trajectory_time = []
            threshold_velocity_x = []
            threshold_velocity_y = []
            threshold_velocity_mag = []
            # store start times for threshold
            threshold.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            threshold.tStart = globalClock.getTime(format='float')
            threshold.status = STARTED
            thisExp.addData('threshold.started', threshold.tStart)
            threshold.maxDuration = None
            # keep track of which components have finished
            thresholdComponents = threshold.components
            for thisComponent in threshold.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1
            
            # --- Run Routine "threshold" ---
            # if trial has changed, end Routine now
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            threshold.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                # get current time
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame
                
                # *start_box_2* updates
                
                # if start_box_2 is starting this frame...
                if start_box_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    start_box_2.frameNStart = frameN  # exact frame index
                    start_box_2.tStart = t  # local t and not account for scr refresh
                    start_box_2.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(start_box_2, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'start_box_2.started')
                    # update status
                    start_box_2.status = STARTED
                    start_box_2.setAutoDraw(True)
                
                # if start_box_2 is active this frame...
                if start_box_2.status == STARTED:
                    # update params
                    pass
                
                # *response_box* updates
                
                # if response_box is starting this frame...
                if response_box.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    response_box.frameNStart = frameN  # exact frame index
                    response_box.tStart = t  # local t and not account for scr refresh
                    response_box.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(response_box, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'response_box.started')
                    # update status
                    response_box.status = STARTED
                    response_box.setAutoDraw(True)
                
                # if response_box is active this frame...
                if response_box.status == STARTED:
                    # update params
                    pass
                # *mouse_fix* updates
                
                # if mouse_fix is starting this frame...
                if mouse_fix.status == NOT_STARTED and t >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    mouse_fix.frameNStart = frameN  # exact frame index
                    mouse_fix.tStart = t  # local t and not account for scr refresh
                    mouse_fix.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(mouse_fix, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.addData('mouse_fix.started', t)
                    # update status
                    mouse_fix.status = STARTED
                    mouse_fix.mouseClock.reset()
                    prevButtonState = mouse_fix.getPressed()  # if button is down already this ISN'T a new click
                if mouse_fix.status == STARTED:  # only update if started and not finished!
                    x, y = mouse_fix.getPos()
                    mouse_fix.x.append(x)
                    mouse_fix.y.append(y)
                    buttons = mouse_fix.getPressed()
                    mouse_fix.leftButton.append(buttons[0])
                    mouse_fix.midButton.append(buttons[1])
                    mouse_fix.rightButton.append(buttons[2])
                    mouse_fix.time.append(mouse_fix.mouseClock.getTime())
                # Run 'Each Frame' code from code_2
                # Run 'Each Frame' code from code_2
                current_time = time.time()
                # Get current mouse position for logic checks (needed every frame)
                current_pos = mouse_fix.getPos()
                
                # Movement checks needed every frame for responsive user experience
                if current_pos[1] > start_pos[1] and not movement_initiated:
                    movement_initiated = True
                
                in_corridor = abs(current_pos[0] - start_pos[0]) <= corridor_width/2
                
                if movement_initiated and in_corridor and current_pos[1] >= threshold_y and not threshold_crossed:
                    threshold_crossed = True
                    continueRoutine = False  # Move to stimulus routine
                
                if fix_timer.getTime() >= max_wait_time and not movement_initiated:
                    timeout_occurred = True
                    continueRoutine = False  # End routine
                    
                # Only record data at specified sampling rate
                if current_time - last_mouse_sample_time_threshold >= mouse_sampling_rate:
                    current_frame_time = globalClock.getTime()
                    
                    # Add to trajectory with controlled sampling
                    threshold_trajectory_x.append(current_pos[0])
                    threshold_trajectory_y.append(current_pos[1])
                    threshold_trajectory_time.append(current_frame_time)
                    
                    # Calculate velocity if we have at least 2 points
                    if len(threshold_trajectory_time) >= 2:
                        dt = threshold_trajectory_time[-1] - threshold_trajectory_time[-2]
                        if dt > 0:  # Avoid division by zero
                            vx = (threshold_trajectory_x[-1] - threshold_trajectory_x[-2]) / dt
                            vy = (threshold_trajectory_y[-1] - threshold_trajectory_y[-2]) / dt
                            threshold_velocity_x.append(vx)
                            threshold_velocity_y.append(vy)
                            threshold_velocity_mag.append(np.sqrt(vx**2 + vy**2))
                        else:
                            threshold_velocity_x.append(0)
                            threshold_velocity_y.append(0)
                            threshold_velocity_mag.append(0)
                    else:
                        threshold_velocity_x.append(0)
                        threshold_velocity_y.append(0)
                        threshold_velocity_mag.append(0)
                        
                    # Update last sample time
                    last_mouse_sample_time_threshold = current_time
                
                # check for quit (typically the Esc key)
                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return
                # pause experiment here if requested
                if thisExp.status == PAUSED:
                    pauseExperiment(
                        thisExp=thisExp, 
                        win=win, 
                        timers=[routineTimer], 
                        playbackComponents=[]
                    )
                    # skip the frame we paused on
                    continue
                
                # check if all components have finished
                if not continueRoutine:  # a component has requested a forced-end of Routine
                    threshold.forceEnded = routineForceEnded = True
                    break
                continueRoutine = False  # will revert to True if at least one component still running
                for thisComponent in threshold.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished
                
                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()
            
            # --- Ending Routine "threshold" ---
            for thisComponent in threshold.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            # store stop times for threshold
            threshold.tStop = globalClock.getTime(format='float')
            threshold.tStopRefresh = tThisFlipGlobal
            thisExp.addData('threshold.stopped', threshold.tStop)
            # store data for trials (TrialHandler)
            trials.addData('mouse_fix.x', mouse_fix.x)
            trials.addData('mouse_fix.y', mouse_fix.y)
            trials.addData('mouse_fix.leftButton', mouse_fix.leftButton)
            trials.addData('mouse_fix.midButton', mouse_fix.midButton)
            trials.addData('mouse_fix.rightButton', mouse_fix.rightButton)
            trials.addData('mouse_fix.time', mouse_fix.time)
            # Run 'End Routine' code from code_2
            # Record movement data
            thisExp.addData('movement_initiated', movement_initiated)
            thisExp.addData('threshold_crossed', threshold_crossed)
            thisExp.addData('movement_time', fix_timer.getTime())
            thisExp.addData('timeout_occurred', timeout_occurred)
            # End Routine code for threshold
            thisExp.addData('threshold_trajectory_x', threshold_trajectory_x)
            thisExp.addData('threshold_trajectory_y', threshold_trajectory_y)
            thisExp.addData('threshold_trajectory_time', threshold_trajectory_time)
            thisExp.addData('threshold_velocity_x', threshold_velocity_x)
            thisExp.addData('threshold_velocity_y', threshold_velocity_y)
            thisExp.addData('threshold_velocity_mag', threshold_velocity_mag)
            
            # Calculate additional threshold metrics
            if len(threshold_trajectory_x) > 2:
                # Initial acceleration (time from movement start to peak velocity)
                if len(threshold_velocity_mag) > 2:
                    peak_vel_idx = threshold_velocity_mag.index(max(threshold_velocity_mag))
                    if peak_vel_idx < len(threshold_trajectory_time) and peak_vel_idx > 0:
                        initial_accel_time = threshold_trajectory_time[peak_vel_idx] - threshold_trajectory_time[0]
                    else:
                        initial_accel_time = np.nan
                else:
                    initial_accel_time = np.nan
                
                # Movement path during threshold crossing
                threshold_path_length = 0
                for i in range(1, len(threshold_trajectory_x)):
                    segment = np.sqrt(
                        (threshold_trajectory_x[i] - threshold_trajectory_x[i-1])**2 + 
                        (threshold_trajectory_y[i] - threshold_trajectory_y[i-1])**2
                    )
                    threshold_path_length += segment
                
                thisExp.addData('threshold_initial_accel_time', initial_accel_time)
                thisExp.addData('threshold_path_length', threshold_path_length)
                thisExp.addData('threshold_max_velocity', max(threshold_velocity_mag) if threshold_velocity_mag else np.nan)
            else:
                thisExp.addData('threshold_initial_accel_time', np.nan)
                thisExp.addData('threshold_path_length', np.nan)
                thisExp.addData('threshold_max_velocity', np.nan)
            # the Routine "threshold" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()
            
            # --- Prepare to start Routine "stimulus" ---
            # create an object to store info about Routine stimulus
            stimulus = data.Routine(
                name='stimulus',
                components=[start_box_3, response_box_2, text_stimulus, mouse_resp],
            )
            stimulus.status = NOT_STARTED
            continueRoutine = True
            # update component parameters for each repeat
            # Run 'Begin Routine' code from code_6
            # Display the digit loaded from the .xlsx file
            text_stimulus.setText(str(digit))
            print(f"Running trial: digit={digit}, type={trial_type}, expected={correct_response}")
            
            
            text_stimulus.setText(digit)
            # setup some python lists for storing info about the mouse_resp
            mouse_resp.x = []
            mouse_resp.y = []
            mouse_resp.leftButton = []
            mouse_resp.midButton = []
            mouse_resp.rightButton = []
            mouse_resp.time = []
            mouse_resp.corr = []
            mouse_resp.clicked_name = []
            gotValidClick = False  # until a click is received
            # Run 'Begin Routine' code from code_3
            # Initialize variables for response tracking
            trial_clock = core.Clock()
            max_response_time = 1.5  # 1500ms max response time
            last_mouse_sample_time_stimulus = time.time()
            # Track mouse positions
            mouse_positions = []
            mouse_timestamps = []
            
            # Response tracking
            response_made = False
            movement_continued = False
            movement_stopped = False
            last_positions = []  # For tracking if movement has stopped
            still_duration = 0
            correct = False
            
            # Convert stimulus to correct type
            current_digit = int(digit)
            
            # Add to the beginning of stimulus routine
            import numpy as np
            
            
            # Always re-initialize trajectory arrays at the beginning of each trial
            trajectory_x = []
            trajectory_y = []
            trajectory_time = []
            velocity_x = []
            velocity_y = []
            velocity_magnitude = []
            acceleration_x = []
            acceleration_y = []
            acceleration_magnitude = []
            # store start times for stimulus
            stimulus.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            stimulus.tStart = globalClock.getTime(format='float')
            stimulus.status = STARTED
            thisExp.addData('stimulus.started', stimulus.tStart)
            stimulus.maxDuration = None
            # keep track of which components have finished
            stimulusComponents = stimulus.components
            for thisComponent in stimulus.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1
            
            # --- Run Routine "stimulus" ---
            # if trial has changed, end Routine now
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            stimulus.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                # get current time
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame
                
                # *start_box_3* updates
                
                # if start_box_3 is starting this frame...
                if start_box_3.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    start_box_3.frameNStart = frameN  # exact frame index
                    start_box_3.tStart = t  # local t and not account for scr refresh
                    start_box_3.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(start_box_3, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'start_box_3.started')
                    # update status
                    start_box_3.status = STARTED
                    start_box_3.setAutoDraw(True)
                
                # if start_box_3 is active this frame...
                if start_box_3.status == STARTED:
                    # update params
                    pass
                
                # *response_box_2* updates
                
                # if response_box_2 is starting this frame...
                if response_box_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    response_box_2.frameNStart = frameN  # exact frame index
                    response_box_2.tStart = t  # local t and not account for scr refresh
                    response_box_2.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(response_box_2, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'response_box_2.started')
                    # update status
                    response_box_2.status = STARTED
                    response_box_2.setAutoDraw(True)
                
                # if response_box_2 is active this frame...
                if response_box_2.status == STARTED:
                    # update params
                    pass
                
                # *text_stimulus* updates
                
                # if text_stimulus is starting this frame...
                if text_stimulus.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    text_stimulus.frameNStart = frameN  # exact frame index
                    text_stimulus.tStart = t  # local t and not account for scr refresh
                    text_stimulus.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(text_stimulus, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'text_stimulus.started')
                    # update status
                    text_stimulus.status = STARTED
                    text_stimulus.setAutoDraw(True)
                
                # if text_stimulus is active this frame...
                if text_stimulus.status == STARTED:
                    # update params
                    pass
                # *mouse_resp* updates
                
                # if mouse_resp is starting this frame...
                if mouse_resp.status == NOT_STARTED and t >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    mouse_resp.frameNStart = frameN  # exact frame index
                    mouse_resp.tStart = t  # local t and not account for scr refresh
                    mouse_resp.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(mouse_resp, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.addData('mouse_resp.started', t)
                    # update status
                    mouse_resp.status = STARTED
                    mouse_resp.mouseClock.reset()
                    prevButtonState = mouse_resp.getPressed()  # if button is down already this ISN'T a new click
                if mouse_resp.status == STARTED:  # only update if started and not finished!
                    x, y = mouse_resp.getPos()
                    mouse_resp.x.append(x)
                    mouse_resp.y.append(y)
                    buttons = mouse_resp.getPressed()
                    mouse_resp.leftButton.append(buttons[0])
                    mouse_resp.midButton.append(buttons[1])
                    mouse_resp.rightButton.append(buttons[2])
                    mouse_resp.time.append(mouse_resp.mouseClock.getTime())
                # Run 'Each Frame' code from code_3
                # Run 'Each Frame' code from code_3
                current_time = time.time()
                # Get current mouse position for logic checks (needed every frame)
                current_pos = mouse_resp.getPos()
                current_trial_time = trial_clock.getTime()  # For trial logic
                # Real-time checks needed every frame for responsive user experience
                if mouse_resp.isPressedIn(response_box_2) and not response_made:
                    response_made = True
                    rt = current_trial_time  # Use trial time for RT
                    buttons = mouse_resp.getPressed()
                    clicked_in_box = buttons[0] > 0
                    
                    if trial_type == "go":
                        correct = clicked_in_box
                    else:
                        correct = False
                    
                    click_pos = current_pos
                    thisExp.addData('response_box_clicked', clicked_in_box)
                    thisExp.addData('click_pos_x', click_pos[0])
                    thisExp.addData('click_pos_y', click_pos[1])
                    
                    continueRoutine = False
                
                # Add position to recent positions list (for checking if stopped)
                last_positions.append(current_pos)
                if len(last_positions) > 15:  # Keep last ~250ms of positions 
                    last_positions.pop(0)
                
                # Check if movement has stopped (for No-Go trials)
                if len(last_positions) >= 15:
                    pos_array = np.array(last_positions)
                    max_distance = np.max(np.sqrt(np.sum((pos_array - pos_array[0])**2, axis=1)))
                    
                    if max_distance < 5:  # Less than 5 pixels movement = stopped
                        movement_stopped = True
                        still_duration += 1/60  # Assuming 60Hz refresh rate
                        
                        if still_duration >= 0.5 and trial_type == "nogo":
                            correct = True
                            rt = current_trial_time  # Use trial time for RT
                            continueRoutine = False
                    else:
                        still_duration = 0
                        movement_stopped = False
                        movement_continued = True
                
                # Check if time has run out
                if current_trial_time >= max_response_time:
                    rt = max_response_time
                    
                    if trial_type == "nogo" and not movement_continued:
                        correct = True
                    elif trial_type == "go":
                        correct = False
                    
                    continueRoutine = False
                
                # Only record data at specified sampling rate
                if current_time - last_mouse_sample_time_stimulus >= mouse_sampling_rate:
                    current_global_time = globalClock.getTime()  # Get global time for trajectory data
                    
                    # Record position and time at controlled rate
                    mouse_positions.append(current_pos)
                    mouse_timestamps.append(current_global_time)  # Use global time for timestamps
                    
                    # Add to detailed trajectory data with controlled sampling
                    trajectory_x.append(current_pos[0])
                    trajectory_y.append(current_pos[1])
                    trajectory_time.append(current_global_time)  # Use global time for timestamps
                    
                    # Calculate velocity if we have at least 2 points
                    if len(trajectory_time) >= 2:
                        dt = trajectory_time[-1] - trajectory_time[-2]
                        if dt > 0:  # Avoid division by zero
                            vx = (trajectory_x[-1] - trajectory_x[-2]) / dt
                            vy = (trajectory_y[-1] - trajectory_y[-2]) / dt
                            velocity_x.append(vx)
                            velocity_y.append(vy)
                            velocity_magnitude.append(np.sqrt(vx**2 + vy**2))
                        else:
                            velocity_x.append(0)
                            velocity_y.append(0)
                            velocity_magnitude.append(0)
                    else:
                        velocity_x.append(0)
                        velocity_y.append(0)
                        velocity_magnitude.append(0)
                        
                    # Calculate acceleration if we have at least 2 velocity points
                    if len(velocity_x) >= 2:
                        dt = trajectory_time[-1] - trajectory_time[-2]
                        if dt > 0:  # Avoid division by zero
                            ax = (velocity_x[-1] - velocity_x[-2]) / dt
                            ay = (velocity_y[-1] - velocity_y[-2]) / dt
                            acceleration_x.append(ax)
                            acceleration_y.append(ay)
                            acceleration_magnitude.append(np.sqrt(ax**2 + ay**2))
                        else:
                            acceleration_x.append(0)
                            acceleration_y.append(0)
                            acceleration_magnitude.append(0)
                    else:
                        acceleration_x.append(0)
                        acceleration_y.append(0)
                        acceleration_magnitude.append(0)
                    
                    # Update last sample time
                    last_mouse_sample_time_stimulus = current_time
                
                # check for quit (typically the Esc key)
                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return
                # pause experiment here if requested
                if thisExp.status == PAUSED:
                    pauseExperiment(
                        thisExp=thisExp, 
                        win=win, 
                        timers=[routineTimer], 
                        playbackComponents=[]
                    )
                    # skip the frame we paused on
                    continue
                
                # check if all components have finished
                if not continueRoutine:  # a component has requested a forced-end of Routine
                    stimulus.forceEnded = routineForceEnded = True
                    break
                continueRoutine = False  # will revert to True if at least one component still running
                for thisComponent in stimulus.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished
                
                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()
            
            # --- Ending Routine "stimulus" ---
            for thisComponent in stimulus.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            # store stop times for stimulus
            stimulus.tStop = globalClock.getTime(format='float')
            stimulus.tStopRefresh = tThisFlipGlobal
            thisExp.addData('stimulus.stopped', stimulus.tStop)
            # store data for trials (TrialHandler)
            trials.addData('mouse_resp.x', mouse_resp.x)
            trials.addData('mouse_resp.y', mouse_resp.y)
            trials.addData('mouse_resp.leftButton', mouse_resp.leftButton)
            trials.addData('mouse_resp.midButton', mouse_resp.midButton)
            trials.addData('mouse_resp.rightButton', mouse_resp.rightButton)
            trials.addData('mouse_resp.time', mouse_resp.time)
            trials.addData('mouse_resp.corr', mouse_resp.corr)
            trials.addData('mouse_resp.clicked_name', mouse_resp.clicked_name)
            # Run 'End Routine' code from code_3
            # Save data
            thisExp.addData('mouse_positions_x', [pos[0] for pos in mouse_positions])
            thisExp.addData('mouse_positions_y', [pos[1] for pos in mouse_positions])
            thisExp.addData('mouse_timestamps', mouse_timestamps)
            thisExp.addData('response_made', response_made)
            thisExp.addData('movement_continued', movement_continued)
            thisExp.addData('movement_stopped', movement_stopped)
            thisExp.addData('correct', correct)
            thisExp.addData('rt', rt)
            
            # Add to End Routine section of stimulus routine
            # Save all trajectory metrics
            thisExp.addData('trajectory_x', trajectory_x)
            thisExp.addData('trajectory_y', trajectory_y)
            thisExp.addData('trajectory_time', trajectory_time)
            thisExp.addData('velocity_x', velocity_x)
            thisExp.addData('velocity_y', velocity_y)
            thisExp.addData('velocity_magnitude', velocity_magnitude)
            thisExp.addData('acceleration_x', acceleration_x)
            thisExp.addData('acceleration_y', acceleration_y)
            thisExp.addData('acceleration_magnitude', acceleration_magnitude)
            
            # Calculate additional metrics
            if len(trajectory_x) > 2:
                # Maximum velocity and acceleration
                max_velocity = max(velocity_magnitude) if velocity_magnitude else np.nan
                max_acceleration = max(acceleration_magnitude) if acceleration_magnitude else np.nan
                
                # Average velocity and acceleration
                avg_velocity = sum(velocity_magnitude) / len(velocity_magnitude) if velocity_magnitude else np.nan
                avg_acceleration = sum(acceleration_magnitude) / len(acceleration_magnitude) if acceleration_magnitude else np.nan
                
                # Initial movement direction (degrees)
                if len(trajectory_y) > 10:
                    initial_direction = np.degrees(np.arctan2(
                        trajectory_y[10] - trajectory_y[0], 
                        trajectory_x[10] - trajectory_x[0]
                    ))
                else:
                    # Not enough points, use the last available point instead
                    last_idx = len(trajectory_y) - 1
                    if last_idx > 0:  # Make sure we have at least 2 points
                        initial_direction = np.degrees(np.arctan2(
                            trajectory_y[last_idx] - trajectory_y[0], 
                            trajectory_x[last_idx] - trajectory_x[0]
                        ))
                    else:
                        initial_direction = np.nan  # Not enough points to calculate direction
                
                # Movement time
                movement_time = trajectory_time[-1] - trajectory_time[0]
                
                # Initiation time (time to start moving)
                initiation_threshold = 5  # pixels
                for i in range(1, len(trajectory_x)):
                    distance = np.sqrt((trajectory_x[i] - trajectory_x[0])**2 + 
                                    (trajectory_y[i] - trajectory_y[0])**2)
                    if distance > initiation_threshold:
                        initiation_time = trajectory_time[i] - trajectory_time[0]
                        break
                else:
                    initiation_time = np.nan
                
                # Calculate trajectory curvature
                # (comparing direct path to actual path)
                start_point = (trajectory_x[0], trajectory_y[0])
                end_point = (trajectory_x[-1], trajectory_y[-1])
                direct_distance = np.sqrt(
                    (end_point[0] - start_point[0])**2 + 
                    (end_point[1] - start_point[1])**2
                )
                
                # Calculate actual path length
                path_length = 0
                for i in range(1, len(trajectory_x)):
                    segment = np.sqrt(
                        (trajectory_x[i] - trajectory_x[i-1])**2 + 
                        (trajectory_y[i] - trajectory_y[i-1])**2
                    )
                    path_length += segment
                
                # Maximum deviation from direct path
                if direct_distance > 0:
                    # Get vector for direct path
                    direct_vector = np.array([
                        end_point[0] - start_point[0],
                        end_point[1] - start_point[1]
                    ])
                    unit_direct = direct_vector / np.linalg.norm(direct_vector)
                    
                    # Calculate perpendicular distance for each point
                    max_deviation = 0
                    for i in range(len(trajectory_x)):
                        point_vector = np.array([
                            trajectory_x[i] - start_point[0],
                            trajectory_y[i] - start_point[1]
                        ])
                        
                        # Project onto direct path
                        projection_length = np.dot(point_vector, unit_direct)
                        projection = unit_direct * projection_length
                        
                        # Calculate perpendicular distance
                        deviation = np.linalg.norm(point_vector - projection)
                        max_deviation = max(max_deviation, deviation)
                else:
                    max_deviation = 0
                
                # AUC (Area Under Curve) - simplified calculation
                auc = max_deviation * direct_distance / 2
                
                # Calculate path curvature
                path_curvature = path_length / direct_distance if direct_distance > 0 else np.nan
                
                # Movement smoothness (spectral arc length)
                # Simplified approximation using velocity profile
                if len(velocity_magnitude) > 3:
                # Calculate differences in velocity
                    velocity_changes = []
                    for i in range(1, len(velocity_magnitude)):
                        velocity_changes.append(abs(velocity_magnitude[i] - velocity_magnitude[i-1]))
                    smoothness = -sum(velocity_changes)
                else:
                    smoothness = np.nan
                
                # Save calculated metrics
                thisExp.addData('max_velocity', max_velocity)
                thisExp.addData('avg_velocity', avg_velocity)
                thisExp.addData('max_acceleration', max_acceleration)
                thisExp.addData('avg_acceleration', avg_acceleration)
                thisExp.addData('initial_direction', initial_direction)
                thisExp.addData('movement_time', movement_time)
                thisExp.addData('initiation_time', initiation_time)
                thisExp.addData('path_length', path_length)
                thisExp.addData('direct_distance', direct_distance)
                thisExp.addData('max_deviation', max_deviation)
                thisExp.addData('path_curvature', path_curvature)
                thisExp.addData('auc', auc)
                thisExp.addData('movement_smoothness', smoothness)
            else:
                # Handle cases with insufficient data points
                missing_value = np.nan
                thisExp.addData('max_velocity', missing_value)
                thisExp.addData('avg_velocity', missing_value)
                thisExp.addData('max_acceleration', missing_value)
                thisExp.addData('avg_acceleration', missing_value)
                thisExp.addData('initial_direction', missing_value)
                thisExp.addData('movement_time', missing_value)
                thisExp.addData('initiation_time', missing_value)
                thisExp.addData('path_length', missing_value)
                thisExp.addData('direct_distance', missing_value)
                thisExp.addData('max_deviation', missing_value)
                thisExp.addData('path_curvature', missing_value)
                thisExp.addData('auc', missing_value)
                thisExp.addData('movement_smoothness', missing_value)
                
            # Add to End Routine in stimulus
            # For NoGo trials
            if trial_type == "nogo":
                # Calculate distance moved after stimulus onset
                if len(trajectory_x) > 2:
                    post_stimulus_distance = 0
                    for i in range(1, len(trajectory_x)):
                        segment = np.sqrt(
                            (trajectory_x[i] - trajectory_x[i-1])**2 + 
                            (trajectory_y[i] - trajectory_y[i-1])**2
                        )
                        post_stimulus_distance += segment
                    
                    # Maximum velocity after stimulus in NoGo trials
                    max_post_stim_velocity = max(velocity_magnitude) if velocity_magnitude else np.nan
                    
                    # Time to stop after stimulus onset
                    stop_threshold = 5  # pixels per second
                    time_to_stop = np.nan
                    if len(velocity_magnitude) > 1 and len(trajectory_time) > 1:
                        for i in range(1, len(velocity_magnitude)):
                            if i < len(trajectory_time) and velocity_magnitude[i] < stop_threshold:
                                # Found a stop
                                time_to_stop = trajectory_time[i]
                                break
                    
                    thisExp.addData('post_stimulus_distance', post_stimulus_distance)
                    thisExp.addData('max_post_stim_velocity', max_post_stim_velocity)
                    thisExp.addData('time_to_stop', time_to_stop)
                else:
                    thisExp.addData('post_stimulus_distance', np.nan)
                    thisExp.addData('max_post_stim_velocity', np.nan)
                    thisExp.addData('time_to_stop', np.nan)
                    
            # Add to End Routine in code_3
            # Create a clear categorical accuracy label
            if trial_type == "go":
                if correct:
                    accuracy_type = "correct_go"  # Clicked in response box
                else:
                    accuracy_type = "failed_go"   # Didn't respond in time
            else:  # nogo trial
                if correct:
                    if movement_continued:
                        accuracy_type = "correct_nogo_stopped"  # Started moving but stopped
                    else:
                        accuracy_type = "correct_nogo_never_moved"  # Never moved
                else:
                    accuracy_type = "failed_nogo"  # Clicked or continued moving
            
            thisExp.addData('accuracy_type', accuracy_type)
            
            # Add to End Routine in code_3
            # For NoGo trials, calculate additional metrics
            if trial_type == "nogo":
                # Calculate total movement during nogo trial
                total_movement = 0
                if len(trajectory_x) > 1:
                    for i in range(1, len(trajectory_x)):
                        segment = np.sqrt(
                            (trajectory_x[i] - trajectory_x[i-1])**2 + 
                            (trajectory_y[i] - trajectory_y[i-1])**2
                        )
                        total_movement += segment
                    
                    # Calculate max distance from starting position
                    start_pos = np.array([trajectory_x[0], trajectory_y[0]])
                    max_distance_from_start = 0
                    for i in range(1, len(trajectory_x)):
                        current_pos = np.array([trajectory_x[i], trajectory_y[i]])
                        distance = np.linalg.norm(current_pos - start_pos)
                        max_distance_from_start = max(max_distance_from_start, distance)
                        
                    thisExp.addData('nogo_total_movement', total_movement)
                    thisExp.addData('nogo_max_distance', max_distance_from_start)
                else:
                    thisExp.addData('nogo_total_movement', 0)
                    thisExp.addData('nogo_max_distance', 0)
            # the Routine "stimulus" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()
            
            # --- Prepare to start Routine "ITI" ---
            # create an object to store info about Routine ITI
            ITI = data.Routine(
                name='ITI',
                components=[blank, mouse_iti],
            )
            ITI.status = NOT_STARTED
            continueRoutine = True
            # update component parameters for each repeat
            # Run 'Begin Routine' code from code_4
            # Hide the mouse cursor during ITI
            win.mouseVisible = False
            last_mouse_sample_time_iti = time.time()
            # Choose a random ITI duration for this trial
            import random
            this_iti_duration = random.choice(possible_iti_durations)
            thisExp.addData('iti_duration', this_iti_duration)  # Record the selected duration
            
            # Initialize variables for ITI tracking
            iti_trajectory_x = []
            iti_trajectory_y = []
            iti_trajectory_time = []
            iti_velocity_x = []
            iti_velocity_y = []
            iti_velocity_mag = []
            # setup some python lists for storing info about the mouse_iti
            mouse_iti.x = []
            mouse_iti.y = []
            mouse_iti.leftButton = []
            mouse_iti.midButton = []
            mouse_iti.rightButton = []
            mouse_iti.time = []
            gotValidClick = False  # until a click is received
            # store start times for ITI
            ITI.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
            ITI.tStart = globalClock.getTime(format='float')
            ITI.status = STARTED
            thisExp.addData('ITI.started', ITI.tStart)
            ITI.maxDuration = None
            # keep track of which components have finished
            ITIComponents = ITI.components
            for thisComponent in ITI.components:
                thisComponent.tStart = None
                thisComponent.tStop = None
                thisComponent.tStartRefresh = None
                thisComponent.tStopRefresh = None
                if hasattr(thisComponent, 'status'):
                    thisComponent.status = NOT_STARTED
            # reset timers
            t = 0
            _timeToFirstFrame = win.getFutureFlipTime(clock="now")
            frameN = -1
            
            # --- Run Routine "ITI" ---
            # if trial has changed, end Routine now
            if isinstance(trials, data.TrialHandler2) and thisTrial.thisN != trials.thisTrial.thisN:
                continueRoutine = False
            ITI.forceEnded = routineForceEnded = not continueRoutine
            while continueRoutine:
                # get current time
                t = routineTimer.getTime()
                tThisFlip = win.getFutureFlipTime(clock=routineTimer)
                tThisFlipGlobal = win.getFutureFlipTime(clock=None)
                frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
                # update/draw components on each frame
                # Run 'Each Frame' code from code_4
                # Run 'Each Frame' code from code_4
                current_time = time.time()
                # Get current mouse position
                current_pos = mouse_iti.getPos()
                current_frame_time = globalClock.getTime()
                
                # Only record data at specified sampling rate
                if current_time - last_mouse_sample_time_iti >= mouse_sampling_rate:
                    # Track mouse movement during ITI at controlled rate
                    iti_trajectory_x.append(current_pos[0])
                    iti_trajectory_y.append(current_pos[1])
                    iti_trajectory_time.append(current_frame_time)
                    
                    # Calculate velocity if we have at least 2 points
                    if len(iti_trajectory_time) >= 2:
                        dt = iti_trajectory_time[-1] - iti_trajectory_time[-2]
                        if dt > 0:  # Avoid division by zero
                            vx = (iti_trajectory_x[-1] - iti_trajectory_x[-2]) / dt
                            vy = (iti_trajectory_y[-1] - iti_trajectory_y[-2]) / dt
                            iti_velocity_x.append(vx)
                            iti_velocity_y.append(vy)
                            iti_velocity_mag.append(np.sqrt(vx**2 + vy**2))
                        else:
                            iti_velocity_x.append(0)
                            iti_velocity_y.append(0)
                            iti_velocity_mag.append(0)
                    else:
                        iti_velocity_x.append(0)
                        iti_velocity_y.append(0)
                        iti_velocity_mag.append(0)
                    
                    # Update last sample time
                    last_mouse_sample_time_iti = current_time
                
                # *blank* updates
                
                # if blank is starting this frame...
                if blank.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    blank.frameNStart = frameN  # exact frame index
                    blank.tStart = t  # local t and not account for scr refresh
                    blank.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(blank, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.timestampOnFlip(win, 'blank.started')
                    # update status
                    blank.status = STARTED
                    blank.setAutoDraw(True)
                
                # if blank is active this frame...
                if blank.status == STARTED:
                    # update params
                    pass
                
                # if blank is stopping this frame...
                if blank.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > blank.tStartRefresh + this_iti_duration-frameTolerance:
                        # keep track of stop time/frame for later
                        blank.tStop = t  # not accounting for scr refresh
                        blank.tStopRefresh = tThisFlipGlobal  # on global time
                        blank.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.timestampOnFlip(win, 'blank.stopped')
                        # update status
                        blank.status = FINISHED
                        blank.setAutoDraw(False)
                # *mouse_iti* updates
                
                # if mouse_iti is starting this frame...
                if mouse_iti.status == NOT_STARTED and t >= 0.0-frameTolerance:
                    # keep track of start time/frame for later
                    mouse_iti.frameNStart = frameN  # exact frame index
                    mouse_iti.tStart = t  # local t and not account for scr refresh
                    mouse_iti.tStartRefresh = tThisFlipGlobal  # on global time
                    win.timeOnFlip(mouse_iti, 'tStartRefresh')  # time at next scr refresh
                    # add timestamp to datafile
                    thisExp.addData('mouse_iti.started', t)
                    # update status
                    mouse_iti.status = STARTED
                    mouse_iti.mouseClock.reset()
                    prevButtonState = mouse_iti.getPressed()  # if button is down already this ISN'T a new click
                
                # if mouse_iti is stopping this frame...
                if mouse_iti.status == STARTED:
                    # is it time to stop? (based on global clock, using actual start)
                    if tThisFlipGlobal > mouse_iti.tStartRefresh + 1.0-frameTolerance:
                        # keep track of stop time/frame for later
                        mouse_iti.tStop = t  # not accounting for scr refresh
                        mouse_iti.tStopRefresh = tThisFlipGlobal  # on global time
                        mouse_iti.frameNStop = frameN  # exact frame index
                        # add timestamp to datafile
                        thisExp.addData('mouse_iti.stopped', t)
                        # update status
                        mouse_iti.status = FINISHED
                if mouse_iti.status == STARTED:  # only update if started and not finished!
                    x, y = mouse_iti.getPos()
                    mouse_iti.x.append(x)
                    mouse_iti.y.append(y)
                    buttons = mouse_iti.getPressed()
                    mouse_iti.leftButton.append(buttons[0])
                    mouse_iti.midButton.append(buttons[1])
                    mouse_iti.rightButton.append(buttons[2])
                    mouse_iti.time.append(mouse_iti.mouseClock.getTime())
                
                # check for quit (typically the Esc key)
                if defaultKeyboard.getKeys(keyList=["escape"]):
                    thisExp.status = FINISHED
                if thisExp.status == FINISHED or endExpNow:
                    endExperiment(thisExp, win=win)
                    return
                # pause experiment here if requested
                if thisExp.status == PAUSED:
                    pauseExperiment(
                        thisExp=thisExp, 
                        win=win, 
                        timers=[routineTimer], 
                        playbackComponents=[]
                    )
                    # skip the frame we paused on
                    continue
                
                # check if all components have finished
                if not continueRoutine:  # a component has requested a forced-end of Routine
                    ITI.forceEnded = routineForceEnded = True
                    break
                continueRoutine = False  # will revert to True if at least one component still running
                for thisComponent in ITI.components:
                    if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                        continueRoutine = True
                        break  # at least one component has not yet finished
                
                # refresh the screen
                if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                    win.flip()
            
            # --- Ending Routine "ITI" ---
            for thisComponent in ITI.components:
                if hasattr(thisComponent, "setAutoDraw"):
                    thisComponent.setAutoDraw(False)
            # store stop times for ITI
            ITI.tStop = globalClock.getTime(format='float')
            ITI.tStopRefresh = tThisFlipGlobal
            thisExp.addData('ITI.stopped', ITI.tStop)
            # Run 'End Routine' code from code_4
            # Make mouse visible again and reset position
            win.mouseVisible = True
            # Save ITI mouse tracking data
            thisExp.addData('iti_trajectory_x', iti_trajectory_x)
            thisExp.addData('iti_trajectory_y', iti_trajectory_y)
            thisExp.addData('iti_trajectory_time', iti_trajectory_time)
            thisExp.addData('iti_velocity_x', iti_velocity_x)
            thisExp.addData('iti_velocity_y', iti_velocity_y)
            thisExp.addData('iti_velocity_mag', iti_velocity_mag)
            
            # Calculate ITI movement metrics
            if len(iti_trajectory_x) > 2:
                # Calculate total distance moved during ITI
                iti_total_movement = 0
                for i in range(1, len(iti_trajectory_x)):
                    segment = np.sqrt(
                        (iti_trajectory_x[i] - iti_trajectory_x[i-1])**2 + 
                        (iti_trajectory_y[i] - iti_trajectory_y[i-1])**2
                    )
                    iti_total_movement += segment
                
                # Calculate average velocity during ITI
                iti_avg_velocity = sum(iti_velocity_mag) / len(iti_velocity_mag) if iti_velocity_mag else 0
                
                # Calculate max velocity during ITI
                iti_max_velocity = max(iti_velocity_mag) if iti_velocity_mag else 0
                
                # Save ITI movement summary metrics
                thisExp.addData('iti_total_movement', iti_total_movement)
                thisExp.addData('iti_avg_velocity', iti_avg_velocity)
                thisExp.addData('iti_max_velocity', iti_max_velocity)
                
                # Determine if significant movement occurred during ITI
                # (e.g., more than 50 pixels of movement is considered significant)
                iti_significant_movement = iti_total_movement > 50
                thisExp.addData('iti_significant_movement', iti_significant_movement)
            else:
                thisExp.addData('iti_total_movement', 0)
                thisExp.addData('iti_avg_velocity', 0)
                thisExp.addData('iti_max_velocity', 0)
                thisExp.addData('iti_significant_movement', False)
            
            # Make mouse visible again for next trial
            win.mouseVisible = True
            # store data for trials (TrialHandler)
            trials.addData('mouse_iti.x', mouse_iti.x)
            trials.addData('mouse_iti.y', mouse_iti.y)
            trials.addData('mouse_iti.leftButton', mouse_iti.leftButton)
            trials.addData('mouse_iti.midButton', mouse_iti.midButton)
            trials.addData('mouse_iti.rightButton', mouse_iti.rightButton)
            trials.addData('mouse_iti.time', mouse_iti.time)
            # the Routine "ITI" was not non-slip safe, so reset the non-slip timer
            routineTimer.reset()
            thisExp.nextEntry()
            
        # completed 1.0 repeats of 'trials'
        
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        
        # --- Prepare to start Routine "block_end" ---
        # create an object to store info about Routine block_end
        block_end = data.Routine(
            name='block_end',
            components=[block_end_text, resp_Exp_begin_2],
        )
        block_end.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from code_8
        # Get current block number and type
        block_number = blocks_loop.getCurrentTrial()['block_number']
        current_block_type = blocks_loop.getCurrentTrial()['block_type']
        
        # Look ahead to get next block type (if there is one)
        next_block_type = ""
        try:
            # Find the next trial in sequence
            if blocks_loop.thisTrialN + 1 < len(blocks_loop.trialList):
                next_block_type = blocks_loop.trialList[blocks_loop.thisTrialN + 1]['block_type']
            else:
                next_block_type = "none"  # Last block
        except:
            next_block_type = "none"
        
        # Based on the current block and the type of the next block
        if block_number == 1:  # After first practice block (go_only)
            block_end_text.text = "Übungsblock 1 ist abgeschlossen. Im nächsten Block werden Sie No-Go- zusammen mit Go-Versuchen üben. Zur Erinnerung: halten Sie die Bewegung an, sobald Sie eine 1 oder 9 sehen.\n\nDrücken Sie die Leertaste, um fortzufahren."
        elif block_number == 2:  # After second practice block (go_nogo_prac)
            block_end_text.text = "Die Übung ist abgeschlossen. Nun beginnen Sie mit dem Experiment. Im nächsten Block werden Sie nur Go-Versuche sehen. Reagieren Sie also, indem Sie in die weiße Box klicken.\n\nDrücken Sie die Leertaste, um fortzufahren."
        elif block_number == 15:  # Final block 
            block_end_text.text = "Das Experiment ist abgeschlossen. Vielen Dank für Ihre Teilnahme!"
        elif next_block_type == "go_only":  # Next block will be go_only
            block_end_text.text = "Machen Sie bei Bedarf eine Pause. Als nächstes werden Sie nur Go-Versuche sehen. Reagieren Sie, indem Sie in die weiße Box klicken.\n\nDrücken Sie die Leertaste, um fortzufahren."
        elif next_block_type == "go_nogo":  # Next block will be go_nogo
            block_end_text.text = "Machen Sie bei Bedarf eine Pause. Als nächstes werden Sie sowohl Go- als auch No-Go-Versuche sehen. Zur Erinnerung: halten Sie die Bewegung an, sobald Sie eine 1 oder 9 sehen. \n\nDrücken Sie die Leertaste, um fortzufahren."
        else:
            block_end_text.text = "Machen Sie bei Bedarf eine Pause.\n\nDrücken Sie die Leertaste, um fortzufahren"
        
        # Print for debugging
        print(f"Block transition: {block_number} ({current_block_type}) → Next: {next_block_type}")
        # create starting attributes for resp_Exp_begin_2
        resp_Exp_begin_2.keys = []
        resp_Exp_begin_2.rt = []
        _resp_Exp_begin_2_allKeys = []
        # store start times for block_end
        block_end.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        block_end.tStart = globalClock.getTime(format='float')
        block_end.status = STARTED
        thisExp.addData('block_end.started', block_end.tStart)
        block_end.maxDuration = None
        # keep track of which components have finished
        block_endComponents = block_end.components
        for thisComponent in block_end.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1
        
        # --- Run Routine "block_end" ---
        # if trial has changed, end Routine now
        if isinstance(blocks_loop, data.TrialHandler2) and thisBlocks_loop.thisN != blocks_loop.thisTrial.thisN:
            continueRoutine = False
        block_end.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *block_end_text* updates
            
            # if block_end_text is starting this frame...
            if block_end_text.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                block_end_text.frameNStart = frameN  # exact frame index
                block_end_text.tStart = t  # local t and not account for scr refresh
                block_end_text.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(block_end_text, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'block_end_text.started')
                # update status
                block_end_text.status = STARTED
                block_end_text.setAutoDraw(True)
            
            # if block_end_text is active this frame...
            if block_end_text.status == STARTED:
                # update params
                pass
            
            # *resp_Exp_begin_2* updates
            waitOnFlip = False
            
            # if resp_Exp_begin_2 is starting this frame...
            if resp_Exp_begin_2.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                resp_Exp_begin_2.frameNStart = frameN  # exact frame index
                resp_Exp_begin_2.tStart = t  # local t and not account for scr refresh
                resp_Exp_begin_2.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(resp_Exp_begin_2, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'resp_Exp_begin_2.started')
                # update status
                resp_Exp_begin_2.status = STARTED
                # keyboard checking is just starting
                waitOnFlip = True
                win.callOnFlip(resp_Exp_begin_2.clock.reset)  # t=0 on next screen flip
                win.callOnFlip(resp_Exp_begin_2.clearEvents, eventType='keyboard')  # clear events on next screen flip
            if resp_Exp_begin_2.status == STARTED and not waitOnFlip:
                theseKeys = resp_Exp_begin_2.getKeys(keyList=['space'], ignoreKeys=["escape"], waitRelease=False)
                _resp_Exp_begin_2_allKeys.extend(theseKeys)
                if len(_resp_Exp_begin_2_allKeys):
                    resp_Exp_begin_2.keys = _resp_Exp_begin_2_allKeys[-1].name  # just the last key pressed
                    resp_Exp_begin_2.rt = _resp_Exp_begin_2_allKeys[-1].rt
                    resp_Exp_begin_2.duration = _resp_Exp_begin_2_allKeys[-1].duration
                    # a response ends the routine
                    continueRoutine = False
            
            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp, 
                    win=win, 
                    timers=[routineTimer], 
                    playbackComponents=[]
                )
                # skip the frame we paused on
                continue
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                block_end.forceEnded = routineForceEnded = True
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in block_end.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # --- Ending Routine "block_end" ---
        for thisComponent in block_end.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for block_end
        block_end.tStop = globalClock.getTime(format='float')
        block_end.tStopRefresh = tThisFlipGlobal
        thisExp.addData('block_end.stopped', block_end.tStop)
        # check responses
        if resp_Exp_begin_2.keys in ['', [], None]:  # No response was made
            resp_Exp_begin_2.keys = None
        blocks_loop.addData('resp_Exp_begin_2.keys',resp_Exp_begin_2.keys)
        if resp_Exp_begin_2.keys != None:  # we had a response
            blocks_loop.addData('resp_Exp_begin_2.rt', resp_Exp_begin_2.rt)
            blocks_loop.addData('resp_Exp_begin_2.duration', resp_Exp_begin_2.duration)
        # the Routine "block_end" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
    # completed 1.0 repeats of 'blocks_loop'
    
    
    # mark experiment as finished
    endExperiment(thisExp, win=win)


def saveData(thisExp):
    """
    Save data from this experiment
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    """
    filename = thisExp.dataFileName
    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.
    
    This function does NOT close the window or end the Python process - use `quit` for this.
    
    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about 
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    """
    if win is not None:
        # remove autodraw from all current components
        win.clearAutoDraw()
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed
        win.flip()
    # return console logger level to WARNING
    logging.console.setLevel(logging.WARNING)
    # mark experiment handler as finished
    thisExp.status = FINISHED
    logging.flush()


def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.
    
    Parameters
    ==========
    win : psychopy.visual.Window
        Window to close.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    thisExp.abort()  # or data files will save again on exit
    # make sure everything is closed down
    if win is not None:
        # Flip one final time so any remaining win.callOnFlip() 
        # and win.timeOnFlip() tasks get executed before quitting
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    # terminate Python process
    core.quit()


# if running this experiment as a script...
if __name__ == '__main__':
    # call all functions in order
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo, 
        thisExp=thisExp, 
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)
