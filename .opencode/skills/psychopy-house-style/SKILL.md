---
name: psychopy-house-style
description: BEEHub's non-negotiable PsychoPy display conventions — pixel units, explicit image sizes, anchor usage, coordinate conversion. Use before writing or reviewing any generated PsychoPy code.
---

# PsychoPy house style — copy, do not invent

The canonical reference is `Agent/05_Paradigm/template/paradigm_template.py`.
Copy its window, clock, stimulus objects and helpers **verbatim**; replace only
the trial/block logic. `Agent/05_Paradigm/lint_style.sh` enforces these rules.

**These rules apply to code you generate.** Human-made reference files and a
project's original PsychoPy code are not rewritten to comply.

## Rules

1. **Pixel units only.**
   ```python
   win = visual.Window(size=(1280, 720), fullscr=True,
                       color=(0, 0, 0), colorSpace="rgb255",
                       units="pix", allowGUI=False)
   ```
   Never `norm`, `height`, `deg`.
2. **Every `ImageStim` gets an explicit `size=` in pixels.** No size is a bug.
3. **No `height`, `pos` or `wrapWidth` between -1 and 1** — those are norm
   values. Text heights are tens of pixels; positions hundreds.
4. **Load images through one helper that raises on a missing file**:
   ```python
   def _load_image(filename, size, pos=(0, 0)):
       full = STIM_DIR / filename
       if not full.exists():
           raise FileNotFoundError(f"stimulus not found: {full}")
       return visual.ImageStim(win, image=str(full), size=size, pos=pos)
   ```
5. **Origins differ.** PsychoPy `pix`: (0,0) at centre, y up. pygame/HTML: (0,0)
   top-left, y down. Port positions through:
   ```python
   def _px(x, y):
       return (x - win.size[0] / 2.0, win.size[1] / 2.0 - y)
   ```
   Forgetting this shifts everything right or flips it vertically, with no error.
6. **Never `alignHoriz=` / `alignVert=`** — they raise at runtime. Use
   `alignText=`, `anchorHoriz=`, `anchorVert=`.

## Sizes come from the source

Stimulus sizes and positions are taken from the source paradigm or from
`Agent/notes/<CODE>.md` — never chosen. If the source does not state them, ask.

## Self-check

- [ ] `units="pix"`; no `norm`/`height` anywhere
- [ ] every `ImageStim` has `size=`
- [ ] no `height`/`pos`/`wrapWidth` value in (-1, 1)
- [ ] missing stimuli raise
- [ ] no `alignHoriz`/`alignVert`
- [ ] ported top-left coordinates go through `_px()`
- [ ] `python3 Agent/tools/check_paradigm.py <file> --generated --launch` passes
