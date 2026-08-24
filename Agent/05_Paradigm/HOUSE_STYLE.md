# BEEHub PsychoPy House Style — COPY THIS, DO NOT INVENT

**The canonical reference is `Agent/03_Paradigm/template/paradigm_template.py`.** When generating any PsychoPy script,
copy its display conventions verbatim. Do not substitute your own.

## RULE 1 — Pixel units. Always.

Copy this window setup exactly, changing only the colour values if the paradigm differs:

```python
win = visual.Window(size=(1280, 720), fullscr=True,
                    color=(0, 0, 0), colorSpace="rgb255",
                    units="pix", allowGUI=False)
```

**FORBIDDEN:** `units='norm'`, `units='height'`, `units='deg'`. Only `units="pix"`.

## RULE 2 — Every ImageStim gets an explicit pixel size.

```python
# CORRECT — explicit size in pixels
main_img = visual.ImageStim(win, pos=(0, -70), size=(1024, 787))
afc_img  = visual.ImageStim(win, pos=(0,   0), size=(1224, 987))

# WRONG — no size: the image will not render at the intended scale
img = visual.ImageStim(win, image=str(path), pos=(0, -0.1))
```

An `ImageStim` without `size=` is a bug. Always pass one.

## RULE 3 — Positions and heights in pixels, never fractions.

```python
# CORRECT
fix_stim  = visual.TextStim(win, text="+", color="white", height=80, pos=(0, 0))
feed_text = visual.TextStim(win, text="",  color="white", height=50, pos=(0, 350),
                            wrapWidth=1100)

# WRONG — these are norm-unit values
text_stim = visual.TextStim(win, text='', height=0.06, wrapWidth=0.9)
fix_stim  = visual.TextStim(win, text='+', height=0.15)
```

Rule of thumb: if a `height`, `pos`, or `wrapWidth` value is between -1 and 1, it is wrong.
Text heights are tens of pixels (40–80). Positions are hundreds.

## RULE 4 — Load and size images through one helper.

Preloading is good; preloading *without a size* is not. If you cache images, pass the size:

```python
def _load_image(filename, size=(1024, 787), pos=(0, -70)):
    full = STIM_DIR / filename
    if not full.exists():
        raise FileNotFoundError(f"stimulus not found: {full}")
    return visual.ImageStim(win, image=str(full), size=size, pos=pos)
```

Missing stimuli must **raise**, not print a warning and continue with `None`.

## Standard sizes used in OLM

| Stimulus | size | pos |
|---|---|---|
| main house image | `(1024, 787)` | `(0, -70)` |
| feedback image | `(1024, 787)` | `(0, -70)` |
| AFC image | `(1224, 987)` | `(0, 0)` |
| full-screen instruction | `(1280, 720)` | `(0, 0)` |

## RULE 5 — Coordinate origin: PsychoPy centres, pygame corners.

`units="pix"` puts `(0,0)` at the **screen centre**, y growing **upward**.
pygame puts `(0,0)` at the **top-left**, y growing **downward**.

Native PsychoPy layout uses centre-based coords directly — that is fine:
```python
main_img = visual.ImageStim(win, pos=(0, -70), size=(1024, 787))   # 70 px below centre
```

But when PORTING a top-left layout (pygame, HTML, a screenshot), convert every position:
```python
def _px(x, y):
    """top-left origin (y down) -> PsychoPy pix (centre origin, y up)."""
    return (x - win.size[0] / 2.0, win.size[1] / 2.0 - y)

rect.pos = _px(box_left + box_w / 2, box_top + box_h / 2)
```

**Symptom of forgetting: everything drifts to the right and/or is vertically flipped —
with no error at all.** `pos=(win.size[0] / 2, y)` means "centre" in pygame and
"right edge" in PsychoPy.

## RULE 6 — Never use `alignHoriz=` / `alignVert=`.

They are deprecated and **raise at runtime**:
`` `anchor_y` must be either "top", "bottom", "center", or "baseline". ``

```python
# WRONG — raises
visual.TextStim(win, text=t, alignHoriz='left', alignVert='center')

# CORRECT
visual.TextStim(win, text=t,
                alignText='left',      # justification INSIDE the text box
                anchorHoriz='left',    # which point of the box sits at pos
                anchorVert='center')
```

## Self-check before you finish

- [ ] `units="pix"` in the Window call — and `norm`/`height` appear nowhere
- [ ] every `ImageStim` has `size=`
- [ ] no `height=`, `pos=`, or `wrapWidth=` value between -1 and 1
- [ ] missing stimuli raise, not warn
- [ ] no `alignHoriz=`/`alignVert=` anywhere (rule 6)\n- [ ] ported top-left coordinates go through `_px()` (rule 5)\n- [ ] `./Agent/03_Paradigm/check_runs.sh <file>` passes (it lints these rules)
