# BEEHub Conversion Workflow — 4-Pass Sequence

A repeatable sequence for converting one Presentation SET to PsychoPy. The key idea: **produce a
small, checkable manifest before any code is written.** Errors caught in a 100-line manifest are
cheap; the same errors caught in a 600-line generated script are not.

Run all four passes in **one `claude` session per SET** (context carries between passes).
Launch as always:

```bash
mamba activate psychopy
cd /media/Data03/Studies/Research_BEEHub/Git_repository/BEEHub
claude
```

Paths below are for **OLM SET_A**. For another SET, swap the three path variables at the top of
Pass 1 and the reference file in Pass 3; everything else is unchanged.

---

## Pass 1 — Inventory (NO code)

> Read the OLM SET_A paradigm and produce an inventory manifest. **Do not write any Python yet.**
>
> Source tree: `Projects/OLM/paradigm/presentation/OLM_paradigm/SET_A/`
> - Read `Locato30_VersionA_fMRI.exp` in full.
> - Then read every scenario in `sce/` that the `.exp` references — the real PCL logic lives there
>   (`00_Instr_1.sce`, `01_Prac.sce`, `02_Instr_2.sce`, `03_learning.sce`, `04_Instr_3.sce`,
>   `04_AFC.sce`, `05_AFC.sce`).
> - List the `Stimuli/` tree so you know exactly which files exist.
>
> Write the result to `Agent/manifests/OLM_SET_A.yaml` following the schema in
> `Agent/CONVERSION_WORKFLOW.md` (section "Manifest schema"). Rules:
> - Every stimulus path must be **verified to exist on disk**. Mark each `exists: true|false`.
> - Never invent a filename or guess a path. If something referenced can't be found, record it
>   under `unresolved:` with the exact string as written in the source.
> - Record durations in **milliseconds, as written in the source**. Do not convert units yet.
> - Anything you are unsure about goes in `open_questions:` — do not silently pick an
>   interpretation.
>
> Then print a short summary: number of blocks, trials per block, total stimuli, and how many
> entries are unresolved or open.

---

## Pass 2 — Review (you, not the agent)

Open `Agent/manifests/OLM_SET_A.yaml` and check it against the `.sce` files yourself. Specifically:

- Is `unresolved:` empty? Any entry there is a real problem — a wrong path, a case mismatch, or a
  file that genuinely isn't in the repo.
- Do the trial counts and block order match what the paradigm should do?
- Are the durations right? Spot-check two or three against `03_learning.sce`.
- Do the response keys match the study's actual button mapping?

Correct anything wrong **in the YAML directly**, or tell the agent what to fix:

> In `Agent/manifests/OLM_SET_A.yaml`, <X> is wrong: it should be <Y>. Re-check that against
> `sce/03_learning.sce` and correct the manifest. Don't change anything else.

Do not proceed to Pass 3 until the manifest is clean. This is the whole point of the sequence.

---

## Pass 3 — Generate code from the manifest

> Now generate the PsychoPy script from the approved manifest
> `Agent/manifests/OLM_SET_A.yaml`. Follow CLAUDE.md.
>
> - **The manifest is the source of truth.** Do not re-derive structure from the `.exp`/`.sce`;
>   if the manifest and the source disagree, stop and tell me rather than picking one.
> - Read `Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english.py` first and match
>   its structure, naming, and conventions.
> - Write to
>   `Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english_generated.py`.
>   Do **not** overwrite the existing reference file.
> - Convert durations from ms to seconds at this stage, and say so in a comment where you do it.
> - Use `units='pix'` and set a named monitor explicitly, so PsychoPy doesn't fall back to a
>   temporary monitor spec.
> - No parallel-port / EEG trigger code.
> - Include the provenance header from CLAUDE.md, listing the manifest as the source.
>
> Don't run anything yet — just write the file and tell me what you did.

---

## Pass 4 — Gate and fix

> Now run the gate on the file you just wrote:
>
> ```
> ./Agent/check_runs.sh Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english_generated.py
> ```
>
> If it fails: read the actual error, identify the real cause (missing/renamed asset, wrong
> PsychoPy API symbol for the installed version, missing import), fix it, and re-run. Repeat until
> it passes.
>
> Do not report success while the gate is failing. If you can't get it passing after a few
> attempts, stop and tell me exactly what's failing and what you tried.
>
> When it passes, summarize: what you changed to make it pass, and anything in the script you're
> less than confident about.

### After Pass 4 — your own check

The gate only proves the script **launches** without crashing. It does not prove the trials or
timing are correct. So also:

```bash
diff Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english.py \
     Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english_generated.py
```

and run it for real, clicking through a few trials. Once you trust it, keep the manifest — it is
your regression fixture for this SET.

---

## Manifest schema

Designed to be scanned by eye in a couple of minutes. YAML, one file per SET, under
`Agent/manifests/`.

```yaml
paradigm: OLM_SET_A
source:
  exp: Projects/OLM/paradigm/presentation/OLM_paradigm/SET_A/Locato30_VersionA_fMRI.exp
  scenarios:
    - sce/00_Instr_1.sce
    - sce/03_learning.sce
    - sce/04_AFC.sce
  stimuli_root: Projects/OLM/paradigm/presentation/OLM_paradigm/SET_A/Stimuli
  generated: 2026-07-20T10:00:00Z

display:
  background_rgb: [0, 0, 0]      # as written in the source (Presentation convention)
  font_size_px: 36
  units: pix

response:
  keys: ['1', '2', '3']          # exact keys the paradigm accepts
  quit_key: escape
  timeout_ms: 2000               # null if it waits indefinitely

blocks:                          # order as the paradigm defines it
  - name: learning-1
    type: learning
    n_trials: 28
    randomize: true
  - name: control-1
    type: control
    n_trials: 14
    randomize: true

events:                          # the per-trial event sequence, in order
  - id: fixation
    kind: blank
    duration_ms: 500
  - id: house
    kind: bitmap
    asset: learning/block1/h24_p33_i_up_left.jpg
    duration_ms: 3000
    port_code: 10                # recorded to CSV only; sent nowhere (no trigger hardware)
  - id: response
    kind: response
    duration_ms: null            # null = until response
    collect: true

stimuli:                         # EVERY asset referenced, with existence verified
  - ref: learning/block1/h24_p33_i_up_left.jpg
    path: Projects/OLM/.../Stimuli/learning/block1/h24_p33_i_up_left.jpg
    exists: true
  - ref: bubbles/learning.png
    path: Projects/OLM/.../Stimuli/bubbles/learning.png
    exists: true

unresolved: []                   # referenced but NOT found on disk — must be empty before Pass 3

open_questions: []               # ambiguities the agent refused to guess at
```

### How to eyeball it fast

1. `unresolved:` and `open_questions:` — both empty? If not, stop here.
2. `grep -c "exists: true"` vs `grep -c "exists: false"` — no falses.
3. Block names and `n_trials` — do they match the paradigm you know?
4. Spot-check two `duration_ms` values against the `.sce`.
5. `response.keys` — correct button mapping?

That's the whole review. Under five minutes once you've done it twice.

---

## Scaling to other paradigms

Same four passes, swapping paths:

| SET | Source tree | Reference implementation |
|---|---|---|
| OLM SET_B | `Projects/OLM/paradigm/presentation/OLM_paradigm/SET_B/` | `.../psychopy/OLM_paradigm/Set_B/OLM_Set_B_english.py` |
| OLM short | `Projects/OLM/paradigm/presentation/OLM_paradigm_short/SET_short/` | `.../psychopy/OLM_paradigm_short/OLM_short_version_english.py` |
| APPL Set1 | `Projects/APPL/paradigm/presentation/APPL_paradigm/Set1_MRI/` | `.../psychopy/APPL_paradigm/Set_1/APPL_Set_1_english.py` |
| APPL short | `Projects/APPL/paradigm/presentation/APPL_paradigm_short/` | `.../psychopy/APPL_paradigm_short/APPL_short_version_english.py` |

German variants: after the English one passes, ask for the German version matching the existing
`*_german.py`, reusing the **same manifest** — only the displayed text changes.

One SET per session. Always.
