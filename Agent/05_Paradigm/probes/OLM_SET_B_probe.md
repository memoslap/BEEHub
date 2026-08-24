# Probe report — OLM_SET_B

Generated 2026-07-21 12:29 UTC by `Agent/03_Paradigm/probe.sh`.
**These are measured facts. Prefer them over interpreting PCL. Do not re-derive
anything answered here, and do not put it in `open_questions:`.**

## 1. Inventory

```
exp file(s) : Locato30_VersionB_fMRI.exp 
scenarios   : 8
run logs    : 46   [set 'B': 46 of 134]
stimuli dirs: control bubbles _quarantine AFC learning 
```

Reference log: `PlastMem-001_ses2_B-03_learning.log`

## 2. Trial structure (measured)

```
block/condition tag counts:
       14 ;block1;LS1
       14 ;block1;LS2
       14 ;block1;LS3
       14 ;block1;LS4
       14 ;block2;LS1
       14 ;block2;LS2
       14 ;block2;LS3
       14 ;block2;LS4
       14 ;block3;LS1
       14 ;block3;LS2
       14 ;block3;LS3
       14 ;block3;LS4
       14 ;block4;LS1
       14 ;block4;LS2
       14 ;block4;LS3
       14 ;block4;LS4

block order as actually run:
  block1 block2 block3 crt1 block4 crt2 
unique stimuli per block:
  block1: 28
  block2: 28
  block3: 28
  block4: 28

control trials:
       56 crt1-l
       56 crt2-r
```

## 3. Response mapping (measured)

Port input → response code, from the real run. Preserve these SEMANTICS in the
keyboard version; write the internal code to the CSV so scoring matches.

```
     1792 Port Input 115
      177 Response 1
      177 Port Input 98
      169 Response 2
      169 Port Input 97
        1 Type Response
```
ASCII: 97='a', 98='b', 115='s' (scanner pulse, NOT a response).

## 4. Realised timing (measured, log units = 0.1 ms)

```
stimulus events (most common durations):
       11 11998
       10 14831
        8 15665
        8 14998
feedback events:
      162 20831
      138 20997
       19 20164
        8 21164
```
⚠️ **1792 scanner pulses present — the original was fMRI pulse-locked.**
Realised durations are therefore variable, NOT the nominal `set_duration()` values.
Decide explicitly: nominal PCL values (recommended for standalone) or empirical
medians. Never mix. Record the choice in the provenance header.

## 5. Missing stimuli (log vs disk)

```
  block1: run used 28 unique, disk has 28 .jpg
  block2: run used 28 unique, disk has 28 .jpg
    ❌ MISSING: h107_p41_i_up_left.jpg
    ❌ MISSING: h107_p42_k_up_right.jpg
    ❌ MISSING: h107_p43_i_up_right.jpg
    ❌ MISSING: h107_p63_i_up_right.jpg
    ❌ MISSING: h108_p27_k_up_right.jpg
    ❌ MISSING: h108_p34_i_up_right.jpg
    ❌ MISSING: h108_p51_i_up_left.jpg
    ❌ MISSING: h108_p52_i_up_right.jpg
    ❌ MISSING: h109_p23_i_up_left.jpg
    ❌ MISSING: h109_p27_i_up_right.jpg
    ❌ MISSING: h109_p51_k_up_left.jpg
    ❌ MISSING: h109_p64_i_up_left.jpg
    ❌ MISSING: h12_p13_i_down_left.jpg
    ❌ MISSING: h12_p3_i_down_left.jpg
    ❌ MISSING: h12_p48_i_down_left.jpg
    ❌ MISSING: h12_p4_k_down_left.jpg
    ❌ MISSING: h18_p16_i_down_right.jpg
    ❌ MISSING: h18_p6_i_down_right.jpg
    ❌ MISSING: h18_p7_k_down_right.jpg
    ❌ MISSING: h18_p8_i_down_right.jpg
    ❌ MISSING: h22_p15_i_down_left.jpg
    ❌ MISSING: h22_p20_i_down_left.jpg
    ❌ MISSING: h22_p21_k_down_left.jpg
    ❌ MISSING: h22_p24_i_down_left.jpg
    ❌ MISSING: h25_p13_i_down_left.jpg
    ❌ MISSING: h25_p14_k_down_left.jpg
    ❌ MISSING: h25_p48_i_down_left.jpg
    ❌ MISSING: h25_p56_i_down_left.jpg
  block3: run used 28 unique, disk has 28 .jpg
    ❌ MISSING: h46_p12_i_down_left.jpg
    ❌ MISSING: h46_p18_k_down_left.jpg
    ❌ MISSING: h46_p19_i_down_left.jpg
    ❌ MISSING: h46_p23_i_down_left.jpg
    ❌ MISSING: h48_p40_i_down_right.jpg
    ❌ MISSING: h48_p41_k_down_right.jpg
    ❌ MISSING: h48_p42_i_down_left.jpg
    ❌ MISSING: h48_p49_i_down_right.jpg
    ❌ MISSING: h53_p32_i_down_right.jpg
    ❌ MISSING: h53_p33_k_down_right.jpg
    ❌ MISSING: h53_p34_i_down_left.jpg
    ❌ MISSING: h53_p64_i_down_right.jpg
    ❌ MISSING: h87_p10_i_up_left.jpg
    ❌ MISSING: h87_p6_i_up_left.jpg
    ❌ MISSING: h87_p8_i_up_left.jpg
    ❌ MISSING: h87_p9_k_up_left.jpg
    ❌ MISSING: h89_p31_i_up_left.jpg
    ❌ MISSING: h89_p38_i_up_left.jpg
    ❌ MISSING: h89_p39_k_up_left.jpg
    ❌ MISSING: h89_p50_i_up_left.jpg
    ❌ MISSING: h94_p1_i_up_left.jpg
    ❌ MISSING: h94_p2_k_up_left.jpg
    ❌ MISSING: h94_p3_i_up_left.jpg
    ❌ MISSING: h94_p46_i_up_left.jpg
    ❌ MISSING: h98_p13_i_up_right.jpg
    ❌ MISSING: h98_p18_i_up_right.jpg
    ❌ MISSING: h98_p19_k_up_right.jpg
    ❌ MISSING: h98_p62_i_up_right.jpg
  block4: run used 28 unique, disk has 28 .jpg
    ❌ MISSING: h33_p10_i_down_right.jpg
    ❌ MISSING: h33_p11_k_down_right.jpg
    ❌ MISSING: h33_p12_i_down_right.jpg
    ❌ MISSING: h33_p17_i_down_right.jpg
    ❌ MISSING: h35_p31_i_down_right.jpg
    ❌ MISSING: h35_p38_i_down_right.jpg
    ❌ MISSING: h35_p50_k_down_right.jpg
    ❌ MISSING: h35_p61_i_down_right.jpg
    ❌ MISSING: h36_p11_i_down_left.jpg
    ❌ MISSING: h36_p12_k_down_left.jpg
    ❌ MISSING: h36_p13_i_down_left.jpg
    ❌ MISSING: h36_p18_i_down_left.jpg
    ❌ MISSING: h42_p48_i_down_left.jpg
    ❌ MISSING: h42_p55_i_down_left.jpg
    ❌ MISSING: h42_p56_i_down_left.jpg
    ❌ MISSING: h42_p5_k_down_left.jpg
    ❌ MISSING: h82_p15_i_up_right.jpg
    ❌ MISSING: h82_p20_i_up_right.jpg
    ❌ MISSING: h82_p21_k_up_right.jpg
    ❌ MISSING: h82_p24_i_up_right.jpg
    ❌ MISSING: h83_p24_i_up_right.jpg
    ❌ MISSING: h83_p29_k_up_right.jpg
    ❌ MISSING: h83_p37_i_up_right.jpg
    ❌ MISSING: h83_p57_i_up_right.jpg
    ❌ MISSING: h85_p10_i_up_left.jpg
    ❌ MISSING: h85_p11_k_up_left.jpg
    ❌ MISSING: h85_p12_i_up_left.jpg
    ❌ MISSING: h85_p17_i_up_left.jpg
```
🚨 **84 stimulus file(s) used in the real run are absent from disk.**
Do NOT convert this SET until they are recovered — the deficit would be baked in.
Record them under `unresolved:` and stop.

## 5b. Pairing integrity (LEARNING blocks only)

The generated PsychoPy pairs each _k_ (correct-position) file with _i_ files of the
SAME house. A _k_ with no same-house _i_ yields an empty foil list, so those trials
silently vanish and the other images are never shown. This does NOT crash.

```
  learning/block1: 7 _k_ + 21 _i_ = 28
  learning/block2: 7 _k_ + 21 _i_ = 28
  learning/block3: 7 _k_ + 21 _i_ = 28
  learning/block4: 7 _k_ + 21 _i_ = 28
```
✅ Every _k_ file has same-house _i_ partners; all files would be presented.

## 5c. Learning vs control overlap

```
  block1: 5 of 28 learning images also appear in control
  block2: 3 of 28 learning images also appear in control
```
Any overlap means participants see learning stimuli again during control blocks —
extra encoding exposure that can confound the learning measure. Check whether the
ORIGINAL presentation folders overlap too; if they do not, the folders were
mis-assembled. Escalate rather than deciding this yourself.

## 6. Non-stimulus files in Stimuli/

```
Thumbs.db / desktop.ini / lock files: 4
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
  01_Prac_old.sce:69:"C:/Users/malinowskir/Desktop/Agnes/Locato40_AB_ver2/Version_A/Stimuli/prac"
  03_learning.sce:188:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/SET_B/Stimuli/learning/block1"
  03_learning.sce:189:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/Set_B/Stimuli/learning/block2"
  03_learning.sce:190:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/Set_B/Stimuli/learning/block3"
  03_learning.sce:191:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/Set_B/Stimuli/learning/block4"
  03_learning.sce:193:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/Set_B/Stimuli/control/block1"
  03_learning.sce:194:"C:/Users/fMRI/Desktop/Presentation_Paradigmen/AG_Floeel_P1/Locato_fMRT_last/Set_B/Stimuli/control/block2"
  04_AFC.sce:54:"D:/DATA/LOCATO Versionen/FoGru_fMRI_Version_HGW/Locato40_2ver/Version_A/Stimuli/AFC"
  05_AFC.sce:54:"C:/Users/malinowskir/Desktop/Agnes/Locato40_AB_ver2/Version_A/Stimuli/AFC"
```

## 8. Referenced assets — do they exist anywhere?

```
  prac/ : ❌ NOT FOUND anywhere under Projects/
  AFC/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/Stimuli/AFC
  bubbles/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/Stimuli/bubbles
  control/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/Stimuli/control
  learning/ : ✅ Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/Stimuli/_quarantine/learning
  instr/ : ⚠️ not in this SET, but found elsewhere → Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instr Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/Instr/instr 
  instr_NN.jpg referenced by 00_Instr_1.sce : 0 found repo-wide
    → but Instructions.pptx present: Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/Instructions.pptx 
    → and 36 Folie*.JPG slide exports exist elsewhere in the repo
```
**Instruction images are missing but REGENERABLE** — export the slides from
`Instructions.pptx` (the short paradigm stores them as `Instr/instr/Folie*.JPG`).
They are full-screen 1280x720, unlike the 1024x787 house stimuli.

## 9. AFC scenario variants

```
  04_AFC.sce: shuffle=0
0  jpg_filter=0
0  width = 1624; height = 1187
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
