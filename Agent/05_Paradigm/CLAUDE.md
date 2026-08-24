# BEEHub Paradigm Converter — Agent Instructions

You convert NBS Presentation paradigms into runnable **PsychoPy** and **Pygame** experiments
(and, later, PsychoJS/HTML) for the BEEHub project (https://github.com/memoslap/BEEHub).

Priority for now: **the generated experiment must run.** Preserve the timing values (durations,
onsets, order) from the source; frame-perfect precision is a later refinement.

> Placement: this file must be readable from the directory Claude Code is launched in. Launch from
> the **BEEHub repo root** (so both `Projects/` and the output folders are visible) and keep this
> file at the repo root (a symlink to `Agent/CLAUDE.md` is fine).

---

## Environment — read this first

- You run **inside the `psychopy` mamba/conda environment.** (The old `BEHub` env has a Python
  version that can't install PsychoPy — do not use it.) Use the `python`/`pip` already on `PATH`.
- **Do NOT** run `mamba activate` / `conda activate` inside a command — `activate` is a shell
  function not initialized in the non-interactive shells you spawn; it fails. The env is already
  active because it was activated before `claude` launched.
- If a command must target the env explicitly, use `mamba run -n psychopy <cmd>`.
- PsychoPy in this env is managed by conda (see `Agent/psychopy.yml`); prefer
  `mamba install -c conda-forge <pkg>` over `pip` for anything that pulls system libraries.
- All LLM work goes through the `claude` CLI you're already in. Do **not** write code that calls
  the `anthropic` / `langchain-anthropic` SDKs — the endpoint is OpenAI-compatible and such calls
  will fail.

---

## Repository layout you must respect

A Presentation paradigm is a **directory tree**, not a single file. Example:
`Projects/OLM/paradigm/presentation/OLM_paradigm/SET_A/`
- `*.exp` — the experiment file (references the scenarios below).
- `sce/*.sce` — **the actual PCL logic lives here** (`00_Instr_1.sce`, `03_learning.sce`,
  `04_AFC.sce`, ...). You MUST read the relevant `.sce` files, not just the `.exp`.
- `Stimuli/**` — assets in **nested** subfolders (`AFC/`, `bubbles/`, `control/block1/`,
  `learning/block1..4/`, loose files like `Map_65pos.png`).
- `results/` or `Ergebnisse/` — `.log` runtime files, used for timing validation only.

Outputs go under the project's psychopy/pygame folders, e.g.
`Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/`.

---

## ⚠️ DISPLAY CONVENTIONS ARE NOT NEGOTIABLE

Read `Agent/HOUSE_STYLE.md` before writing any PsychoPy code, and copy the window/stimulus setup
from `Agent/template/paradigm_template.py` **verbatim**. The short version:

```python
win = visual.Window(size=(1280, 720), fullscr=True,
                    color=(0, 0, 0), colorSpace="rgb255",
                    units="pix", allowGUI=False)

main_img = visual.ImageStim(win, pos=(0, -70), size=(1024, 787))   # ALWAYS pass size=
fix_stim = visual.TextStim(win, text="+", color="white", height=80, pos=(0, 0))
```

- `units="pix"` only. **Never** `norm` or `height`.
- **Every** `ImageStim` gets an explicit `size=` in pixels.
- Any `height`/`pos`/`wrapWidth` value between -1 and 1 is wrong — those are norm units.
- Missing stimuli **raise**, they don't print a warning and continue.

`Agent/check_runs.sh` lints these mechanically and will fail. Don't argue with it — copy the
reference.

**Preferred method: start from the reference, don't author from scratch.** Copy
`Agent/template/paradigm_template.py`'s setup block (window, clock, stimulus objects, helpers) into your new
file unchanged, then replace only the trial/block logic with the paradigm you're converting.

---

## Use the existing reference implementations

Several paradigms already have **human-made** PsychoPy/Pygame versions. Read the matching one
before generating, and follow its structure, naming, and English/German split:
- `Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english.py` (+ `_german.py`)
- `Projects/APPL/paradigm/psychopy/APPL_paradigm/Set_1/APPL_Set_1_english.py` (+ `_german.py`)
- `Projects/FLOW/paradigm/psychopy/FLOW_paradigm.psyexp`,
  `Projects/FLOW/paradigm/pygame/FLOW_paradigm_pygame.py`

Treat these as golden references for what "correct output" looks like here.

---

## Answer your own questions first — run the probe

Before reading any PCL or asking anything, run:

```bash
./Agent/probe.sh
```

It writes `Agent/probes/<TAG>_probe.md` with measured facts from the run logs and the
Stimuli tree: trial counts, block order, unique stimuli per block, response-code mapping,
realised durations, missing stimulus files, directory pollution, absolute paths to rewrite,
and where shared assets live.

That report is authoritative — prefer it over interpreting PCL. **Never escalate a question
the probe already answers.** Only genuine study-design decisions belong in `open_questions:`
(e.g. nominal vs empirical timing). Counts, orders, inventories, response codes and file
locations are measurable, not questions.

If the probe reports missing stimulus files, STOP and report it. Do not convert.

## Workflow rules

1. **Read the whole paradigm first**: the `.exp` AND the `.sce` scenarios it uses. Skim the
   matching existing psychopy `.py` reference if one exists.
2. **One paradigm (one SET) per session.** Don't batch.
3. **Resolve stimulus assets by searching the paradigm's directory tree** (`Stimuli/**`, and any
   images referenced from `sce/`). Match filenames **exactly** as written — case-sensitive on
   Linux. List the tree and confirm every referenced asset exists. If any is missing, **stop and
   report it** — never invent a path or a placeholder; these names are reused downstream.
4. **No trigger hardware.** There is no EEG/parallel port. Do NOT emit `psychopy.parallel`/LPT
   code. A `port_code` may be written to the data CSV as a value, but sent nowhere.
5. **Never invent API.** If unsure a PsychoPy/Pygame symbol exists in the installed version, check
   it (import it, or read the installed package) or leave `# TODO: verify <symbol>` and say so.
6. **Ambiguous PCL** (branching on unstated state) -> STOP and ask one question. Don't guess.
7. **Never overwrite** an output file with local edits without explicit confirmation.

---

## The "must run" gate — mandatory before a conversion is "done"

After writing an output file, verify it actually runs, not just compiles:

```bash
./Agent/check_runs.sh <path-to-generated-file.py>
```

`py_compile` (syntax) then a headless launch (imports resolve, window opens, no immediate crash).
On failure: read the real error, fix the real cause (usually a missing/renamed asset, a wrong API
symbol, or a missing import), and re-run until it passes. Do not report success while it fails.
If you can't make it pass after a reasonable number of tries, stop and report what's failing.

---

## Output expectations (v0)

- Runs in the `psychopy` env; window opens; runs headless without immediate crash.
- Stimuli pre-loaded; asset paths correct and existing.
- Durations/onsets/order preserved from the `.exp`/`.sce`.
- Responses (key + RT) written to a CSV in a `data/` subfolder next to the script.
- Clean exit on Escape.
- English and German variants where the reference implementation has them.
- Provenance header at the top of every generated file:
  ```python
  # AUTO-GENERATED by BEEHub converter -- DO NOT EDIT BY HAND
  # source: <relative path to .exp and .sce used>
  # model:  qwen3-coder:30b @ AppHubAI    generated: <UTC timestamp>
  ```

---

## Reference mappings (hints, not gospel)

The Presentation -> PsychoPy / Pygame mapping tables in `IMPLEMENTATION_GUIDE.md` are a starting
point. Treat every API symbol as a hint to verify against the installed version. The existing
reference implementations and the "must run" gate — not the table — decide correctness.
