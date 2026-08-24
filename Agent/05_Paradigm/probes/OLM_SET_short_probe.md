# Probe report — OLM_SET_short

Generated 2026-07-21 14:38 UTC by `Agent/03_Paradigm/probe.sh`.
**These are measured facts. Prefer them over interpreting PCL. Do not re-derive
anything answered here, and do not put it in `open_questions:`.**

## 1. Inventory

```
exp file(s) : Locato10_fMRT.exp 
scenarios   : 7
run logs    : 0
0   [set 'SHORT': 0
0 of 0
0]
stimuli dirs: bubbles allPicsA10_short AFC 
```

Reference log: ``

## 2. Trial structure (measured)

```
block/condition tag counts:

block order as actually run:

unique stimuli per block:

control trials:
```

## 3. Response mapping (measured)

Port input → response code, from the real run. Preserve these SEMANTICS in the
keyboard version; write the internal code to the CSV so scoring matches.

```
```
ASCII: 97='a', 98='b', 115='s' (scanner pulse, NOT a response).

## 4. Realised timing (measured, log units = 0.1 ms)

```
stimulus events (most common durations):
feedback events:
```

## 5. Missing stimuli (log vs disk)

```
```
✅ Every stimulus used in the reference run is present on disk.

## 5b. Pairing integrity (LEARNING blocks only)

The generated PsychoPy pairs each _k_ (correct-position) file with _i_ files of the
SAME house. A _k_ with no same-house _i_ yields an empty foil list, so those trials
silently vanish and the other images are never shown. This does NOT crash.

```
```
✅ Every _k_ file has same-house _i_ partners; all files would be presented.

## 5c. Learning vs control overlap

```
```
Any overlap means participants see learning stimuli again during control blocks —
extra encoding exposure that can confound the learning measure. Check whether the
ORIGINAL presentation folders overlap too; if they do not, the folders were
mis-assembled. Escalate rather than deciding this yourself.

## 6. Non-stimulus files in Stimuli/

```
Thumbs.db / desktop.ini / lock files: 2
```
⚠️ **Directory listings are polluted.** Any directory-scanning logic in the generated
PsychoPy MUST filter to `*.jpg` explicitly, or these will be loaded as stimuli.
Add them to .gitignore. Do not count them in stimulus totals.

## 7. Absolute Windows paths in scenarios

These resolved only on the acquisition machine and MUST be replaced with paths
relative to the paradigm folder. Note which SET each points at — cross-set
references mean the asset is SHARED, not misplaced.

```
  01_Prac.sce:186:"C:/Users/malinowskir/Desktop/Agnes/Locato40_AB_ver2/Version_A/Stimuli/prac"
  01_Prac.sce:212:"C:/Users/malinowskir/Desktop/Locato40_2ver/Version_A/Stimuli/prac"
  03_learning.sce:177:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_short/Stimuli/allPicsA10_short"
  04_AFC.sce:54:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_short/Stimuli/AFC"
  05_AFC.sce:54:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_short/Stimuli/AFC"
```

## 8. Referenced assets — do they exist anywhere?

```
  prac/ : ❌ NOT FOUND anywhere under Projects/
  AFC/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Stimuli/AFC
  bubbles/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Stimuli/bubbles
  control/ : ⚠️ not in this SET, but found elsewhere → Projects/APPL/paradigm/presentation/APPL_paradigm/Set1_MRI/Stimuli/control Projects/APPL/paradigm/presentation/APPL_paradigm/Set2_MRI/Stimuli/control 
  learning/ : ⚠️ not in this SET, but found elsewhere → Projects/APPL/paradigm/presentation/APPL_paradigm/Set1_MRI/Stimuli/learning Projects/APPL/paradigm/presentation/APPL_paradigm/Set2_MRI/Stimuli/learning 
  instr/ : ⚠️ not in this SET, but found elsewhere → Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instr Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instr/instr 
  instr_NN.jpg referenced by 00_Instr_1.sce : 0 found repo-wide
    → but Instructions.pptx present: Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instructions.pptx Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instr/instr.pptx 
    → and 36 Folie*.JPG slide exports exist elsewhere in the repo
```
**Instruction images are missing but REGENERABLE** — export the slides from
`Instructions.pptx` (the short paradigm stores them as `Instr/instr/Folie*.JPG`).
They are full-screen 1280x720, unlike the 1024x787 house stimuli.

## 9. AFC scenario variants

```
  04_AFC.sce: shuffle=0
0  jpg_filter=0
0  width = 1224; height = 987
  05_AFC.sce: shuffle=1  jpg_filter=1  width = 1324; height = 1087
```
The `.jpg` filter is a **bug fix**, not a style choice: without it, Thumbs.db and
desktop.ini (see §6) are loaded as stimuli. Prefer the filtered variant, and filter
in the generated PsychoPy regardless of which scenario you follow.

## 10. Genuinely open — escalate only these

Everything above is measured. Put a question in `open_questions:` ONLY if it is
a study-design decision that no file can answer, e.g.:

- fMRI timing convention: nominal PCL durations vs empirical log medians
- whether a deliberate-looking oddity in the PCL is intended (confirm with the author)
- how to word instructions when the response device changes (grips → keyboard)

Do NOT escalate: trial counts, block order, stimulus inventories, response codes,
durations, missing files, which AFC variant, or where a shared asset lives.
