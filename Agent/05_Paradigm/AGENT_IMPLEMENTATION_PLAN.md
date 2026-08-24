# BEEHub Paradigm Converter — Optimized Agent Implementation Plan

> How I would build the NBS Presentation → PsychoPy / Pygame / PsychoJS converter agent.
> This document keeps the good bones of the original `IMPLEMENTATION_GUIDE.md` and reworks
> the parts that would bite you in production: reliability, reproducibility, scientific-timing
> correctness, and internal consistency.

**Status of facts in this document.** Claude Code install/config details below were checked
against current Anthropic docs (July 2026) and are marked ✅ *verified*. PsychoPy / PsychoJS /
Pygame API details are from general knowledge and are marked ⚠️ *verify against your installed
version* — they change between releases and I did not run them here.

---

## Quick use

Day-to-day, the workflow is three steps:

```bash
mamba activate psychopy     # activate the env FIRST, then launch the agent
cd .../BEEHub               # repo ROOT (holds CLAUDE.md and Projects/); not code/

# point at the paradigm you want (edit Agent/target.env), then:
./Agent/make_prompts.sh     # verifies paths, prints the 4 prompts ready to paste

claude                      # agent inherits the env; reads ./CLAUDE.md automatically
```

Paste the prompts one at a time, stopping after prompt 1 to review the manifest yourself.

`CLAUDE.md` must sit where the agent is launched (or a parent). The canonical copy lives in
`Agent/CLAUDE.md`; symlink it to the repo root so it's auto-loaded:
`ln -sf Agent/CLAUDE.md CLAUDE.md`.

### What lives in `Agent/`

| File | Role |
|---|---|
| `CLAUDE.md` | Agent instructions. Symlinked to repo root so Claude Code auto-loads it. |
| **`template/paradigm_template.py`** | **The canonical PsychoPy reference.** Human-written, house-style compliant. Copy its window/stimulus setup verbatim; never author that block from scratch. |
| **`template/paradigm_demo.html`** | Interactive HTML demo template for Research_BEEHub. All CSS/screens/trial machinery generic; only the marked CONFIG block is edited. |
| `HOUSE_STYLE.md` | Display conventions as literal code (pixel units, explicit `ImageStim` sizes). |
| `lint_style.sh` | Mechanically enforces `HOUSE_STYLE.md`. Verified: rejects the bad generated file, passes the reference. |
| `check_runs.sh` | The gate: style lint → `py_compile` → headless launch. |
| **`target.env`** | **The one file you edit per paradigm** — project, set, language, exp file. Ships ready-made blocks for OLM full/short and APPL. |
| **`make_prompts.sh`** | `--list` discovers paradigms (incl. short, flags missing logs); emits the 4 prompts with paths substituted; verifies paths first. |
| `CONVERSION_WORKFLOW.md` | The 4-pass sequence and manifest schema. |
| **`probe.sh`** | Measures everything measurable and writes `probes/<TAG>_probe.md`. Run before Pass 1. |
| `probes/*.md` | Probe reports — measured facts the agent must not re-derive or escalate. |
| `manifests/*.yaml` | Per-SET manifests: the reviewed intermediate artifact codegen reads from. |
| `psychopy.yml` | conda/mamba env spec (source of truth for the environment). |
| `requirements.txt` | pip tooling only; defers to `psychopy.yml`. |
| `ir.py` | For the later deterministic-parser path; unused by the v0 flow. |

The reference implementation is the single highest-leverage asset here. A small model authoring
~80 lines of boilerplate correctly is unreliable; transplanting a known-good block and editing the
middle is well within reach. Every generation prompt should point at
`Agent/template/paradigm_template.py` explicitly.

# Prompts — generated, not hand-edited

**Do not copy paths into prompts by hand.** Paths live in one file, `Agent/target.env`, and
`Agent/make_prompts.sh` emits the four prompts fully substituted. Editing prompt text per
paradigm is how wrong paths creep in and waste a whole session.

## Switching paradigm: edit one file

```bash
# Agent/target.env — the ONLY file you change
PROJECT="OLM"                        # OLM | APPL | FLOW
PARADIGM="OLM_paradigm"              # e.g. OLM_paradigm_short, APPL_paradigm
LANG="english"                       # english | german
SET_PRESENTATION="SET_A"             # as it appears under paradigm/presentation/
SET_PSYCHOPY="Set_A"                 # as it appears under paradigm/psychopy/
EXP_FILE="Locato30_VersionA_fMRI.exp"
KEY_SCENARIOS="03_learning.sce and 05_AFC.sce"
REFERENCE="Agent/template/paradigm_template.py"
```

> **Why two SET variables rather than one derived name.** The repo naming is not regular:
> OLM uses `SET_A` → `Set_A`, but APPL uses `Set1_MRI` → `Set_1`. Any derivation rule breaks on
> APPL, so both are explicit. Everything else — source dir, `sce/`, `Stimuli/`, manifest name,
> output filename — *is* derived.

## Discovering what's available

Before setting anything, list what the repo actually contains:

```bash
./Agent/make_prompts.sh --list
```

For each paradigm/SET it reports the `.exp` file, scenario count, **whether run logs exist**, and
any existing PsychoPy references — and tags short versions `[SHORT]`.

### ⚠️ Short versions break the naming pattern

The `_short` paradigms are not just different values in the same shape:

| | Full (`SET_A`) | Short |
|---|---|---|
| Presentation dir | `OLM_paradigm/SET_A/` | `OLM_paradigm_short/SET_short/` |
| Exp file | `Locato30_VersionA_fMRI.exp` | `Locato10_fMRT.exp` |
| PsychoPy dir | `OLM_paradigm/Set_A/` | `OLM_paradigm_short/` — **no SET subfolder** |
| Output name | `OLM_Set_A_english.py` | `OLM_short_version_english.py` — **different pattern** |
| Run logs | 20+ in `results/` | **none** |

Two consequences, both handled by the tooling:

1. **`SET_PSYCHOPY=""`** for short versions (outputs sit directly in `<PARADIGM>/`), and
   **`OUT_BASENAME`** must be set explicitly since the filename doesn't follow the usual pattern.
   `target.env` ships a ready-made block for each known configuration — copy it over the defaults.
2. **No logs means no empirical oracle.** The log-mining that settled the SET_A trial counts,
   block order, and response mapping simply isn't available. `make_prompts.sh` detects this and
   rewrites prompt 1 accordingly: it tells the agent that every count must come from the PCL, to
   state its reasoning, and to put anything uncertain in `open_questions:` rather than guessing.
   Expect **more open questions and a longer review** on short versions — that's correct behaviour,
   not a regression.

Short versions also get an explicit warning in the prompt not to assume the full-length paradigm's
counts carry over. A short version differs *by design*; inheriting SET_A's 336-trial structure
would be a silent, serious error.

## Generating and using the prompts

```bash
./Agent/make_prompts.sh --list    # what paradigms exist? (start here)
./Agent/make_prompts.sh --check   # verify the configured paths exist
./Agent/make_prompts.sh           # print all four prompts, substituted
./Agent/make_prompts.sh 2         # print just prompt 2, mid-session
```

`--check` runs before any prompt prints, and refuses to emit text if a directory or file is
missing — a typo'd SET name fails loudly here instead of silently producing a prompt full of
paths that don't exist. It also warns if the output file already exists and creates
`Agent/manifests/` as needed.

## Building the interactive HTML demo

Research_BEEHub embeds a browser demo per paradigm (see the existing `OLM_demo.html`). These are
generated from the **short version** of the paradigm — short enough to click through in a browser.

```bash
./Agent/make_prompts.sh demo
```

The script locates the short paradigm (`<PARADIGM>_short`), looks for a short-version `.py`, and
branches:

- **Short `.py` exists** → prints prompts **D1** (build the demo) and **D2** (verify it).
- **No short `.py`** → prints **D0** first, which converts the short paradigm from its own
  `.exp`/`sce/` — with an explicit warning not to inherit the full paradigm's trial counts —
  then D1 and D2.

### Why the template is structured the way it is

`Agent/template/paradigm_demo.html` is the working OLM demo with its paradigm-specific values
replaced by `{{PLACEHOLDER}}`s, confined to one clearly fenced block:

```
▼▼▼  PARADIGM CONFIG — THIS IS THE ONLY BLOCK YOU EDIT  ▼▼▼
    STIM_BASE, PAIRS, AFC_IMAGES, BUBBLES, timings, N_REPS
▲▲▲  END PARADIGM CONFIG — do not edit below this line  ▲▲▲
```

Everything else — all CSS, the six screens (`welcome`, `instructions`, `trial`, `afc`, `between`,
`results`) and all 24 JS functions — is paradigm-agnostic and stays byte-identical. This is the
same principle as `paradigm_template.py`: give a small model a fenced hole to fill rather than a
document to author. D2 enforces it by diffing the output against the template and requiring that
only the config block differs.

Demo-specific rules the prompts carry: every image path verified on disk (never invented),
`PAIRS.length === AFC_IMAGES.length` in the same house order, timings converted seconds → **ms**,
and no `{{` left anywhere. `N_REPS` is deliberately reduced for browsability, with the real
paradigm's count recorded alongside it so the difference is documented rather than hidden.

## Closing the loop: the probe

The first SET_A run produced eleven open questions. Answering them took a long analysis
session — but almost none of it required judgement. Trial counts, block order, stimulus
inventories, response mappings, realised durations and missing files are all *measurable*
from the run logs and the file tree. Only two of the eleven were genuine design decisions.

`Agent/probe.sh` does that measurement mechanically and writes
`Agent/probes/<TAG>_probe.md`. Prompt 1 now instructs the agent to run it **before reading any
PCL**, and forbids escalating anything the report answers.

| § | What it measures | Replaces the question |
|---|---|---|
| 2 | block/condition tag counts, block order, unique stimuli per block, control trials | "how many trials?", "what order?" |
| 3 | port-input → response-code mapping with counts | "which device, which buttons?" |
| 4 | realised durations + scanner-pulse count | "what timing?", "was it pulse-locked?" |
| 5 | stimuli used in the run vs present on disk, **naming each missing file** | "are files missing?" |
| 6 | Thumbs.db / desktop.ini pollution | "why does directory scanning break?" |
| 7 | absolute Windows paths per scenario | "which paths need rewriting?" |
| 8 | repo-wide search for `prac/`, `instr_NN.jpg`, shared assets | "where did this asset go?" |
| 9 | AFC variants compared on shuffle / `.jpg` filter / size | "which AFC scenario?" |
| 10 | what's left | the only things worth escalating |

Validated against the real SET_A log: the probe independently reproduced every finding from
the manual analysis, including naming the exact seven missing `_k_` files in `block4`.

### What the probe cannot do

It measures; it does not decide. These still need a human, and §10 says so explicitly:

- **fMRI timing convention** — nominal PCL durations vs empirical log medians. Both are
  defensible; it's a study-design call.
- **Confirming deliberate-looking oddities** — e.g. the control blocks' commented-out stimulus
  phase. The probe can show the code; only the author can confirm intent.
- **Instruction wording when the device changes** — grips ("Zeigefinger"/"Daumen") → keyboard.
  A literal translation would instruct participants to press something that doesn't exist.

Where logs are absent (the `_short` paradigms), §§2–5 are unavailable and the report says so,
telling the agent to reason explicitly from PCL and flag uncertainty. Fewer measured facts,
so expect more genuine open questions — correct behaviour, not a regression.

## The four passes (what the generated prompts do)

| Pass | Purpose | Key constraint |
|---|---|---|
| 1 | **Inventory → manifest.** Read `.exp` + `sce/`, check the run logs, write `Agent/manifests/<TAG>.yaml`. | No Python. Unresolved assets and ambiguities go in `unresolved:`/`open_questions:`, never guessed. |
| — | **YOU review the manifest.** | Both lists empty, counts sane, two durations spot-checked. This is the step that makes the rest work. |
| 2 | **Generate from the manifest**, copying the setup block verbatim from `$REFERENCE`. | Manifest is the source of truth; disagreement with `.sce` = stop and ask. |
| 3 | **Run the gate** (`check_runs.sh`: style lint → syntax → headless launch). | Don't report success while failing. |
| 4 | **Only if the lint keeps failing** — point at the reference file rather than re-explaining rules. | |

Prompt 1 also instructs the agent to **mine the run logs before interpreting any PCL** — that is
what settled the trial counts, block order, and response mapping for OLM SET_A (see "Verified
findings"), each in seconds and more reliably than reading scenario code.

## After the gate passes — verify yourself

The gate proves the script *launches*, not that trials or timing are right:

```bash
diff <psychopy_dir>/<PROJECT>_<SET>_<LANG>.py <psychopy_dir>/<PROJECT>_<SET>_<LANG>_generated.py
python <psychopy_dir>/<PROJECT>_<SET>_<LANG>_generated.py
```

`make_prompts.sh` prints both commands with real paths at the end of its output.

## Implementation plan without prompts



Then ask the agent to convert one paradigm (one SET), e.g.:

> *"Convert the OLM SET_A paradigm under Projects/OLM/paradigm/presentation/OLM_paradigm/SET_A/
> to PsychoPy following CLAUDE.md. Read the .exp AND its sce/ scenarios, resolve stimuli from the
> Stimuli/ tree, and use the existing OLM_Set_A_english.py as a reference. Then run the gate and
> fix anything that fails."*

After it writes a file, verify it actually runs before trusting it:

```bash
./Agent/check_runs.sh <path printed by ./Agent/make_prompts.sh>
```

Rules of thumb: **activate `psychopy` before starting `claude`, never after**; **launch from the
repo root**; **one SET per session**; **the code running is the acceptance test** (timing precision
comes later). The rest of this document is the reasoning and the longer-term hardening path.

---

## Decisions resolved (from project answers)

These were open questions in an earlier draft; they are now settled and the plan reflects them:

1. **Endpoint works.** The `claude` CLI runs against AppHubAI in the terminal, which is proof the
   transport is fine. AppHubAI is OpenAI-compatible, so something (a proxy/router, or an
   Anthropic-compatible endpoint the university exposes) is already translating to the Messages
   format the CLI needs. **Consequence:** the pipeline talks to the model *only* through the
   `claude` CLI, and the direct `anthropic` / `langchain-anthropic` SDKs are **removed** — a
   direct SDK call would hit the OpenAI side and break.
2. **No trigger hardware.** EEG/parallel-port code is **dropped**. `port_code` survives at most as
   an optional data-log column, sent nowhere.
3. **Timing source of truth = the `.exp`/`.sce`/`.log`.** The generated script reproduces the
   presentation's timing; PsychoPy/Pygame handle the rest. `.log` files (usually available, in
   `results/` or `Ergebnisse/`) are an after-the-fact timing check, not a generation input.
4. **A paradigm is a directory tree, not one file.** The `.exp` references scenario files in
   `sce/*.sce` where the **actual PCL logic lives** — both must be read. Stimuli live in a nested
   `Stimuli/**` tree (not beside the `.exp`); the converter searches that tree and matches
   filenames **exactly** (case-sensitive on Linux), failing loudly if one is missing.
5. **Existing human-made references exist and must be used.** Several paradigms already ship
   PsychoPy/Pygame versions (e.g. `OLM_Set_A_english.py`, `APPL_Set_1_english.py`,
   `FLOW_paradigm.psyexp`); the agent reads the matching one as a golden reference, including the
   English/German split.
6. **"It runs" is the priority.** v0 is LLM-first generation behind a hard compile-and-launch
   gate; frame-accurate timing and the full deterministic parser are later refinements.
7. **The agent runs inside the `psychopy` mamba env** (the old `BEHub` env's Python couldn't
   install PsychoPy) and installs packages there (see §4.5).

---

## Verified findings from the source files and run logs

Established by reading `01_Prac.sce` / `03_learning.sce` / `04_AFC.sce` / `05_AFC.sce` and by
analysing two real run logs (`PlastMem-005_ses1_A-03_learning.log`,
`sub-001_ses-4_task-OLMM_acq-2_beh.log`). These are facts about the paradigm, not assumptions.

> **The logs turned out to be the single best oracle in this project.** They record what actually
> ran, so counting questions ("how many trials?", "which stimuli?", "which buttons?") are settled
> in seconds — no PCL interpretation required. Check the logs FIRST for any empirical question.

### 🚨 BLOCKER — 7 stimulus files are missing from `learning/block4`

The real run used **28 unique stimuli in block4**, identical to blocks 1–3 (verified unique counts:
28/28/28/28), splitting as 7 `_k_` + 21 `_i_`. The repo has 21 — exactly the `_i_` count, so the
missing 7 are the `_k_` (correct-position/feedback) images:

```
h24_p40_k_up_q4_left.jpg    h26_p20_k_up_q2_right.jpg   h27_p8_k_up_q1_left.jpg
h30_p14_k_up_q2_right.jpg   h34_p41_k_up_q4_left.jpg    h38_p37_k_up_q3_right.jpg
h44_p18_k_up_q1_right.jpg
```

Confirm with `ls .../Stimuli/learning/block4/*_k_*.jpg | wc -l` (expect 0). **Do not convert SET_A
until these are recovered** — converting now bakes the deficit in permanently.

### Paradigm structure (from the log)

| Fact | Value |
|---|---|
| Learning blocks | 4, each 14 trials × 4 repetitions (LS1–LS4) = 56 |
| Control blocks | 2 (`crt1`, `crt2`), 56 trials each |
| Total learning phase | 6 blocks × 56 = **336 trials** |
| Unique stimuli per learning block | 28 (7 `_k_` + 21 `_i_`) |
| Realised block order (PlastMem-005) | block1 → block2 → block3 → control-1 → block4 → control-2 |
| Practice | **40 trials** = 20 unique images × 2 passes, reshuffled between passes |

**Practice count — correcting a plausible misreading.** The `one_Ten[i][l]` indexing looks like it
selects a different image per pass, but columns 1 and 2 are filled *identically*
(`one_Ten[one][1]` and `one_Ten[one][2]` are both `picPairs[i][1]`). `l` does not change which
image appears; only the reshuffle differs. 2 passes × 20 rows = 40.

### Response mapping (exact, from the log)

The original ran in the scanner with Presentation ResponseGrips:

```
Port Input 98  -> Response 1   (192x)    ASCII 'b'  -> "richtig" (correct/yes)
Port Input 97  -> Response 2   (142x)    ASCII 'a'  -> "falsch"  (incorrect/no)
Port Input 115 -> Pulse 30     (1792x)   scanner trigger, NOT a response
```

The PsychoPy version uses the keyboard, but must preserve the **semantics**: `left` → internal
code 1, `right` → internal code 2. Write both the key name and the internal code to the CSV so
accuracy scoring matches the original analysis pipeline.

### Control blocks have no separate stimulus phase — deliberately

In the control branch of `03_learning.sce` the stimulus presentation is explicitly commented out
(`#mainTrial.set_duration(2500); #mainTrial.present();`). What runs is only the feedback trial,
carrying image **and** question together:

```
FeedTrial.set_duration(2500);
FeedText.set_caption("Ist das Haus auf der rechten Seite?", true);
```

So a control trial is **one screen for 2500 ms**. The systematic commenting indicates intent, not
an accident. Worth one line of confirmation from the study author; the code is unambiguous.

### ⚠️ fMRI pulse-locking is the main timing risk

The original was genuinely pulse-locked: the log holds **1792 real scanner pulses**, and trials
call `set_mri_pulse()` — they *waited* for a pulse rather than free-running. Realised durations are
therefore variable, not the nominal `set_duration()` values (log units appear to be 0.1 ms):

| Event | Nominal | Realised in log |
|---|---|---|
| learning stimulus | — | ~1000–1300 ms |
| "extra Pic Time" | — | ~1330–1630 ms |
| feedback | 2000 ms | ~2100 ms |

**A decision is required before generation:** (a) use the nominal PCL values — recommended for a
standalone behavioural version — or (b) use empirical medians from the logs, closer to what
participants experienced. Pick one, never mix, and state the choice in the provenance header along
with the fact that fMRI synchronisation was intentionally removed.

### Settled minor points

- `# Change 30 -> 28` (line 112) is **historical**; arrays are already `[7][4]` = 28. No action.
- `01_Prac_old.sce` is **unreferenced** by any scenario — exclude from conversion, don't delete.
- **`05_AFC.sce` is probably the live one** (adds `shuffle()`, adds a `.jpg` filter bug-fix, and its
  stimulus path matches `01_Prac.sce`'s generation while `04_AFC` points at an older machine).
  ⚠️ Not confirmed — both logs cover only `03_learning`, so no AFC phase is recorded.
- The **cross-scenario chain** remains unverified for the same reason. Sorting `Ergebnisse/` logs by
  timestamp would settle it.

---

## 0. TL;DR — what I changed and why

The original guide is a solid scaffold, but it has three structural problems and several
correctness risks. Here is the short version of the redesign:

| # | Original approach | Problem | Optimized approach |
|---|---|---|---|
| 1 | Pipeline throws the raw `.exp` at the LLM and asks for 3 files. The repo *defines* `parsers/`, `generators/`, `validators/` but `pipeline.py` never calls them. | Non-deterministic, hard to test, expensive, and internally inconsistent. | **Hybrid architecture:** deterministic parser → normalized **Intermediate Representation (IR)** → template-based generation, with the LLM used *only* for genuinely ambiguous PCL logic. |
| 2 | "Pass 2" uses `gemma3:27b` to review timing/trigger logic. | LLM review is a weak gate; it silently misses real timing bugs. | **Deterministic-first validation:** AST compile → headless import → structural checks against the IR → *then* optional LLM review as a last, advisory layer. |
| 3 | CI auto-commits generated code straight to `main`/`develop`. | For experiment code, a timing bug invalidates *data*. Auto-committing non-deterministic output to a protected branch is risky, and the commit can re-trigger the workflow. | **PR-based, human-in-the-loop by default:** generate → validate → open a PR with a review checklist. Auto-merge is opt-in per paradigm and loop-guarded. |
| 4 | `.log` files listed as a generation input. | Presentation `.log` files are *runtime output*, not paradigm definitions — they only capture the path that actually executed. | Reframe `.log` as a **validation oracle** (does the generated timeline match a real run?), never a source of truth for generation. |
| 5 | Timing mapped as `duration = N ms → core.wait(N/1000)`; onset via `while clock.getTime() < t: pass`. | `core.wait()` and busy-waits are not frame-accurate; this quietly degrades visual-onset precision, which matters for EEG. | **Frame-based timing** and `win.callOnFlip()` for triggers (see §7). Marked ⚠️ verify. |
| 6 | No determinism controls, no caching, no provenance. | Re-runs churn the repo and burn tokens; you can't reproduce a given output. | Pin model + Claude Code version, request temperature 0 where the endpoint allows, hash inputs to skip unchanged files, and stamp provenance into every generated file header. |

Everything else (project layout, the `CLAUDE.md` idea, GitHub Actions, the mapping tables as a
*starting reference*) is retained and refined.

---

## 1. Core architecture: parse → IR → generate (not "prompt → files")

The single most important change. Instead of asking the model to translate an `.exp` straight
into three target languages, split the job:

```
.exp / .log ──▶ [deterministic parser] ──▶ IR (validated JSON) ──▶ [generators] ──▶ .py / .py / .html
                        │                        ▲                        │
                        │              [LLM: ambiguous PCL only]          │
                        └──────────────────────────────────────▶ [validators] ◀┘
```

Why this is better:

- **Testable.** The parser and the IR can be unit-tested against fixtures with exact expected
  output. You cannot meaningfully unit-test "did the LLM produce good code today?"
- **Reproducible.** The same `.exp` produces byte-identical IR every time. Generation from IR via
  templates is deterministic too. The LLM is confined to the small, genuinely ambiguous surface.
- **Cheaper and faster.** Most of an `.exp` (scenario header, stimulus declarations, simple
  loops, fixed durations, port codes) is mechanical. Don't pay a 30B model to re-derive it.
- **Auditable.** When a paradigm is wrong, you can point at *which* stage failed.

**Where the LLM still earns its place:** arbitrary PCL control flow (nested conditionals,
computed durations, jitter logic, custom response scoring, subroutines). The parser flags spans
it can't map deterministically; the agent is invoked to translate *only those spans* into the
target language, given the surrounding IR as context. This is also the only place the
`CLAUDE.md` "ask for clarification on ambiguous conditionals" rule actually applies.

> If a full deterministic parser is too much up front, invert the ratio over time: ship an
> LLM-heavy v0, but capture every conversion as a golden test (§9), and migrate the recurring,
> well-understood constructs into the deterministic parser as they prove stable. The IR boundary
> lets you do this incrementally without rewriting the generators.

> **Repo reality (important for both the parser and the LLM path).** In this repository a paradigm
> is a *directory tree*, not a single `.exp`. The `.exp` largely *references* scenario files in a
> `sce/` subfolder — `00_Instr_1.sce`, `03_learning.sce`, `04_AFC.sce`, etc. — and **the real PCL
> logic lives in those `.sce` files**. So "the input" is the `.exp` plus its `.sce` scenarios.
> Stimuli sit in a nested `Stimuli/**` tree (`AFC/`, `bubbles/`, `control/block1/`,
> `learning/block1..4/`, loose files), and `.log` runtime files live in `results/` or `Ergebnisse/`.
> Several paradigms also already ship *human-made* PsychoPy/Pygame implementations (e.g.
> `Projects/OLM/paradigm/psychopy/OLM_paradigm/Set_A/OLM_Set_A_english.py`,
> `Projects/APPL/.../APPL_Set_1_english.py`, `Projects/FLOW/.../FLOW_paradigm.psyexp`) — these are
> the best golden references and encode the English/German split. Whichever path you take, parse
> the `.sce` scenarios (not only the `.exp`) and resolve assets by searching the paradigm subtree.

---

## 2. The Intermediate Representation (IR)

A normalized, serializable model of a paradigm. Rough shape (Python dataclasses / Pydantic;
serialize to JSON so it's diffable and cacheable):

```python
# converter/ir.py  (illustrative — adapt field names to your actual .exp constructs)
from dataclasses import dataclass, field
from enum import Enum

class StimKind(str, Enum):
    BITMAP = "bitmap"; SOUND = "sound"; VIDEO = "video"; TEXT = "text"; BLANK = "blank"

@dataclass
class Stimulus:
    id: str
    kind: StimKind
    asset: str | None = None        # filename for bitmap/sound/video
    text: str | None = None
    pos: tuple[float, float] = (0.0, 0.0)

@dataclass
class Event:
    stimulus_id: str
    duration_ms: int | None          # None = until response
    onset_ms: int | None = None      # absolute onset, if specified
    port_code: int | None = None     # EEG trigger
    collect_response: bool = False
    response_keys: list[str] = field(default_factory=list)
    response_timeout_ms: int | None = None
    # spans the parser could NOT map deterministically go here:
    raw_pcl: str | None = None       # verbatim PCL for LLM translation

@dataclass
class Paradigm:
    name: str
    background_rgb: tuple[int, int, int]     # 0–255, Presentation convention
    font_size_px: int
    refresh_hz: float | None                 # if known; needed for frame-based timing
    trials: list[list[Event]]                # trial = ordered list of events
    randomize: bool = False
    metadata: dict = field(default_factory=dict)  # provenance, source hash, etc.
```

The IR is the contract between parsing and generation. Get this right and everything downstream
gets simpler. Note the explicit `raw_pcl` escape hatch — that's the LLM's job jar.

---

## 3. The agent (`CLAUDE.md`) — scoped, not omniscient

Keep a `CLAUDE.md`, but narrow the agent's remit so it isn't the whole pipeline. The agent is
good at *translation of ambiguous logic* and *review*, not at being a deterministic compiler.

Recommended `CLAUDE.md` structure (condensed):

```markdown
# BEEHub Converter — Agent Instructions

## Role
Translate specific, flagged PCL logic spans into target-language equivalents, and review
generated experiment code for correctness. You are NOT the parser and NOT the whole pipeline.

## Hard rules
1. Read the IR context provided before translating a span. Do not re-derive structure the IR
   already encodes.
2. Work on ONE paradigm per session (context hygiene).
3. Never invent PsychoPy/PsychoJS/Pygame API. If unsure a symbol exists, say so and leave a
   `# TODO: verify <symbol> in <version>` marker rather than guessing.
4. If a PCL span is ambiguous (branching that depends on unstated state), STOP and ask — do not
   pick an interpretation silently.
5. Timing is scientific data. Prefer frame-based timing; never convert a visual duration to a
   bare sleep without flagging the precision trade-off.
6. Never overwrite an output file that has local modifications without explicit confirmation.

## Reference mappings
(Keep the original mapping tables here as a STARTING POINT — but treat them as hints, and
verify every API symbol against the installed version. See known-risk notes in the plan.)
```

Keeping the mapping tables is fine; the key change is the framing — they're hints for the agent,
not a spec it's trusted to have applied correctly. Deterministic checks (§6) verify the result.

---

## 4. Environment configuration (✅ verified where marked)

### 4.1 Install Claude Code

✅ *Verified (July 2026):* the current official install is the native installer; npm is legacy
but still works.

```bash
# Native installer (recommended, no Node.js needed)
curl -fsSL https://claude.ai/install.sh | bash

# Pin a specific version (recommended for CI reproducibility)
curl -fsSL https://claude.ai/install.sh | bash -s <version>

claude --version
claude doctor          # diagnoses PATH / install-type issues
```

The original `mise use claude` recipe is unverified — I'd drop it in favor of the two official
paths above unless you've confirmed a working `mise` plugin.

### 4.2 Point Claude Code at AppHubAI

✅ *Verified:* `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, and the alias overrides
`ANTHROPIC_DEFAULT_OPUS_MODEL` / `ANTHROPIC_DEFAULT_SONNET_MODEL` / `ANTHROPIC_DEFAULT_HAIKU_MODEL`
are all real, current settings. The original `~/.claude/settings.json` is valid:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://apphubai.wolke.uni-greifswald.de",
    "ANTHROPIC_AUTH_TOKEN": "<TOKEN — never commit>",
    "ANTHROPIC_DEFAULT_OPUS_MODEL":   "unsloth/qwen3-coder:30b",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "unsloth/qwen3-coder:30b",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL":  "bartowski/deepreinforce-ai_Ornith-1.0-35B-GGUF:Q4_K_M"
  }
}
```

> ### ✅ Resolved — route through the CLI only
> `ANTHROPIC_BASE_URL` changes *where* requests go, not *what protocol* the server speaks. Claude
> Code sends **Anthropic Messages API** format; AppHubAI is **OpenAI-compatible**. The fact that
> `claude` already works in the terminal means something (a proxy/router, or an
> Anthropic-compatible endpoint the university exposes) is already translating between the two.
>
> **Consequence for the build:** do all model calls through the **`claude` CLI**. Do **not** add
> direct `anthropic`/`langchain-anthropic` SDK calls to the pipeline — those would hit AppHubAI's
> OpenAI-format side and fail. Shelling out to `claude` rides on the translation that already
> works for you.
>
> Note also that the credential may be a bearer token (`ANTHROPIC_AUTH_TOKEN` → sent as
> `Authorization: Bearer …`) rather than an API key (`ANTHROPIC_API_KEY` → sent as `x-api-key`).
> `claude doctor` tells you which. This only matters when you reproduce the setup in CI (§10) —
> the local session already has it right.

### 4.3 Python dependencies

Two adjustments to the original list: **pin versions in a lockfile** (`pip-compile` / `uv lock`)
so CI is reproducible, and **drop `anthropic` and `langchain-anthropic`** — with all model calls
going through the `claude` CLI (§4.2), the SDKs aren't used and would break against the
OpenAI-format endpoint anyway. See the rewritten `requirements.txt` shipped alongside this plan.

### 4.4 Model-selection reference

The table in the original is a reasonable planning aid, but the context-window and
active-parameter figures are model-specific and I can't verify them here. **Treat those numbers
as approximate and confirm them against AppHubAI's own model card** before relying on them for
chunking decisions (§8).

### 4.5 The `psychopy` mamba environment

The agent runs and installs PsychoPy/Pygame inside the `psychopy` mamba env. (The earlier `BEHub`
env had a Python version PsychoPy couldn't install into, so a dedicated `psychopy` env was created;
its spec is checked in as `Agent/psychopy.yml`.) The reliable pattern is to **activate first, then
launch `claude`** — the agent inherits `PATH`/`CONDA_PREFIX` and every command it runs uses that
env's Python automatically:

```bash
mamba activate psychopy
cd .../BEEHub          # repo root
claude
```

The gotcha: the agent should **not** run `mamba activate` itself inside a command — `activate` is
a shell function that isn't initialized in the fresh non-interactive subshells the bash tool
spawns, so it fails. Two safe patterns:

- **Preferred:** activate before launching `claude` (above); the agent never activates anything.
- **If a command must target the env explicitly:** use `mamba run -n psychopy <cmd>` (works
  non-interactively). ⚠️ If `mamba run` ever misbehaves, fall back to
  `source "$(conda info --base)/etc/profile.d/conda.sh" && conda activate psychopy && …`.

Two install caveats:

- **PsychoPy on Linux is managed by conda here**, not pip (that's why `psychopy.yml` exists). Add
  further packages with `mamba install -c conda-forge <pkg>`; reserve `pip` for pure-Python deps.
  To rebuild the env from scratch: `mamba env create -f Agent/psychopy.yml` (or `env update`).
- **Headless launch needs a virtual display.** On a box with no monitor, wrap window creation in
  `xvfb-run` (handled by `Agent/check_runs.sh`). On your workstation with a real display it just
  works.

`Agent/CLAUDE.md` encodes these rules so the agent doesn't fight the env. Note `requirements.txt`
is now secondary — `psychopy.yml` is the source of truth for the environment.

---

## 5. Determinism & reproducibility controls

LLM output is non-deterministic; experiment code must be reproducible. Add:

- **Temperature 0** (or the lowest the endpoint honors) for generation and review passes, if
  AppHubAI exposes it. ⚠️ Whether/how a custom endpoint respects sampling params varies — verify.
- **Pin everything:** model version string, Claude Code version, prompt templates (checked into
  the repo), and the dependency lockfile.
- **Input hashing / caching.** Compute a hash of `(source .exp bytes + CLAUDE.md + prompt
  template + model id)`. Skip regeneration when the hash is unchanged. This stops the repo from
  churning on every unrelated push and cuts token spend.
- **Provenance header** in every generated file:

  ```python
  # AUTO-GENERATED by BEEHub converter — DO NOT EDIT BY HAND
  # source:   paradigms/raw/OLM_paradigm.exp  (sha256: 1a2b3c…)
  # ir_hash:  9f8e7d…
  # model:    qwen3-coder:30b @ AppHubAI
  # cc_ver:   2.1.x   generated: 2026-07-15T… UTC
  ```

  This makes "which input/model produced this file?" answerable, which you *will* need when a
  paradigm misbehaves in the lab.

---

## 6. Validation — deterministic first, LLM last

Replace "let gemma3 check it" with a layered gate. Each layer is cheap and catches a distinct
failure class; the LLM layer is advisory only.

1. **Syntax (AST).** `python -m py_compile` on every `.py`. Non-negotiable, already in the guide.
2. **Import / headless smoke.** Import the module (and, for PsychoPy, attempt window creation in
   an offscreen/`libGL`-software context in CI) to catch missing symbols and typo'd APIs that
   compile fine but fail at import. This is where hallucinated methods surface.
3. **Structural equivalence to the IR.** The strongest gate and the one the original lacks:
   assert the generated code contains the right *number* of trials/events, the right stimulus
   asset references, the right port codes, and durations that match the IR. Do this by parsing
   the generated AST or by running the experiment in a **headless/simulated mode** that logs its
   own timeline, then diffing that timeline against the IR. If a trial silently vanished, this
   catches it; an LLM reviewer often won't.
4. **Golden-file diff** (§9): compare against a known-good reference for that paradigm.
5. **LLM review (advisory).** *Now* optionally ask a model to review for smells. Treat its output
   as suggestions surfaced in the PR, never as a merge gate. Using a *different* model
   (e.g. `gemma3:27b`) for a second opinion is fine at this layer — just don't trust it to be
   correct about timing.

CI fails the build on layers 1–4. Layer 5 posts comments.

---

## 7. Timing correctness (⚠️ verify all APIs against your PsychoPy version)

> **Scope note.** There is no EEG/parallel-port hardware in this setup, so trigger code is dropped
> entirely; `port_code` at most becomes a CSV column. The timing concern that *does* apply is
> fMRI pulse-locking — see "Verified findings" above, which supersedes the generic guidance here
> with measured numbers from the real runs.

This section is about scientific validity, and it's where naive translation does quiet damage.
I'm confident about the *principles*; I'm flagging the exact API symbols because they move
between PsychoPy releases and I did not execute them here.

**Visual duration → frames, not sleeps.** `core.wait(N/1000)` does not align stimulus offset to
the monitor's refresh, so onset/offset timing jitters by up to a frame or more and interacts
badly with dropped frames. Prefer frame-based presentation:

```python
# duration_ms known, refresh_hz known → present for a fixed number of frames
n_frames = round(duration_ms / 1000 * refresh_hz)
for _ in range(n_frames):
    stim.draw()
    win.flip()
```

If `refresh_hz` isn't known, measure it at runtime (PsychoPy has a refresh-rate measurement
helper — ⚠️ confirm the exact call, e.g. `win.getActualFrameRate()`), and record it in the data
file so timing is interpretable after the fact.

**The onset busy-wait must go.** `while clock.getTime() < t: pass` pins a CPU core and blocks the
window; it's both imprecise and harmful. Use frame counting or a flip-locked schedule instead.

**EEG/parallel-port guidance removed.** This setup has no trigger hardware, so the generated
scripts emit no `psychopy.parallel` code at all; `Agent/lint_style.sh` rejects it if it
reappears. The relevant timing issue here is fMRI pulse-locking (see "Verified findings").

**PsychoJS (HTML) is the highest-risk output — consider generating it, not hand-writing it.**
Hand-authored PsychoJS drifts from the API fast, and the original snippet mixes constructs I
would not assume are correct as written. The most robust path is usually to author the paradigm
once as a PsychoPy **Builder** experiment and use Builder's HTML/JS export, which produces
version-matched PsychoJS and Pavlovia-ready structure. If you must emit PsychoJS directly, pin
the exact PsychoJS version, validate every symbol against that version's API, and test in a
browser — don't ship it on a `py_compile`-style check alone (there isn't one for JS here).

---

## 8. The pipeline (revised)

Keep `pipeline.py` as the orchestrator, but make it drive the *stages*, not a single mega-prompt.

```
for each changed .exp:
  1. parse   → IR (deterministic)            # converter/parsers
  2. resolve → for each Event.raw_pcl span, call the agent to translate it,
               given IR context; splice results back into the IR   # LLM, scoped
  3. generate→ render IR via templates to psychopy/pygame/(psychojs)  # converter/generators
  4. validate→ layers 1–4 from §6 (fail hard on error)               # converter/validators
  5. review  → optional advisory LLM pass, output as notes           # LLM, advisory
  6. record  → write provenance header + update cache hash
```

Notes on the original `run_claude_pass` helper: building the subprocess env by hand is fine, but
(a) prefer `claude -p "<prompt>" --output-format json` in scripts and read the structured result
rather than scraping stdout, and (b) ✅ per current docs, set `DISABLE_AUTOUPDATER=1` in CI so a
mid-run auto-update can't change behavior. Also `capture_output=False` means you can't inspect
failures — capture and log it.

---

## 9. Testing — golden files are the real gate

For a converter, the highest-value tests compare output to vetted references.

- **Fixtures:** a small library of `.exp` inputs covering each construct (bitmap, sound, video,
  text, blank; fixed vs response-terminated duration; randomization; port codes; one genuinely
  ambiguous PCL span).
- **Golden outputs:** for each fixture, a human-reviewed, known-good `.py` (and `.html`) committed
  to `tests/golden/`. The deterministic parts should diff *exactly*; wrap the LLM-translated
  spans so their region is checked structurally (does it still produce the right timeline?)
  rather than character-for-character, since the model may phrase equivalent code differently.
- **Parser unit tests:** `.exp` → expected IR, exact.
- **Timeline tests:** run each generated experiment in headless/simulated mode and assert the
  emitted event timeline matches the IR (trial count, order, durations, trigger codes). This is
  the test that actually protects your data.
- **Regression capture:** every real conversion that a human approves becomes a new golden case.

CI runs parser + timeline + golden diffs on every PR and blocks merge on failure.

---

## 10. CI/CD (revised: PR-based, pinned, loop-safe)

Keep GitHub Actions, change the posture from "auto-commit to main" to "open a reviewed PR."

Key changes to the original workflow:

- **Trigger** stays on `.exp` pushes, but **write results to a branch and open a PR**, not a
  direct commit to `main`/`develop`. Generated experiment code should get a human's eyes before
  it can collect real subject data.
- **Loop guard.** If you *do* keep any auto-commit path, prefix commit messages with `[skip ci]`
  and scope path filters so generated `.py`/`.html` never re-trigger the converter. The original
  triggers on `raw/*.exp` and commits `psychopy|pygame|html`, which mostly avoids a loop — but
  the PR approach removes the risk entirely.
- **Pin the toolchain.** Install a fixed Claude Code version (`bash -s <version>`), a locked
  Python env, and set `DISABLE_AUTOUPDATER=1`. ✅ verified these are the right knobs.
- **Secrets.** Keep the token in `secrets.APPHUBAI_TOKEN` and pass it as a **step-scoped env
  var**; avoid writing it into `~/.claude/settings.json` on the runner where later steps (or an
  uploaded artifact) could expose it. Add `.claude/` and any temp config to `.gitignore`.
- **Don't fail the whole batch on one file.** Convert per-file, collect failures, and report them
  in the PR body; a single bad `.exp` shouldn't block the others.
- **`continue-on-error` on tests is wrong here.** The original lets tests fail without blocking
  the commit. For experiment code, a failing timeline test *should* block the merge.
- **Runner reality:** PsychoPy in headless CI needs system libs (e.g. software GL, `libgl1`,
  audio stubs) and a virtual display (`xvfb`). Budget for that in the job setup, or the
  import/headless smoke test in §6 won't run.

---

## 11. Suggested milestones

Reordered to match the "it runs first" priority, with the data blocker first:

1. 🚨 **Recover the 7 missing `learning/block4` `_k_` files.** Converting before this bakes a
   corrupted stimulus set into the output. Nothing else matters until this is done.
2. **Decide the fMRI timing convention** (nominal vs empirical) and record it.
3. **v0, one paradigm end to end** via the 4-pass sequence in `Agent/CONVERSION_WORKFLOW.md`:
   inventory → your review → generate from manifest (copying setup from
   `Agent/template/paradigm_template.py`) → `Agent/check_runs.sh`.
4. **Capture it as a golden test** (§9) so later changes can't silently regress it. The reviewed
   manifest is itself the fixture.
5. **Widen coverage** to the other SETs, the **short versions** (`--list` shows them; expect more open questions since they have no logs), and the German variants — edit `Agent/target.env`, rerun
   `./Agent/make_prompts.sh`, one session each, every one behind the gate and captured as a
   golden case. Reuse the same manifest for a language variant — only displayed text changes.
6. **Pygame** targets next, using the existing pygame/`.psyexp` references where present.
7. **Then harden toward the IR path** (§1–§2): move the recurring, well-understood constructs into
   a deterministic parser and confine the LLM to flagged ambiguous spans plus advisory review.
8. **PsychoJS**: prefer the PsychoPy Builder export route; if authoring directly, add browser
   validation.
9. **CI as a PR bot** (§10) once outputs are stable enough to review in bulk.

> **Reusable technique: mine the logs first.** For every new SET, run the empirical questions past
> the `.log` files in `Ergebnisse/`/`results/` before interpreting any PCL. Trial counts, stimulus
> inventories, block order, response codes, and realised durations all fall out of a few `awk`
> passes over a real run. This is how the block4 shortfall, the 40-trial practice count, and the
> exact response mapping were settled here — each in seconds, and each more reliable than reading
> the scenario code.

---

## 12. Open questions to confirm (don't guess these)

Most paradigm questions are now settled empirically — see "Verified findings" above. What remains:

### Blocking the SET_A conversion

- 🚨 **Recover the 7 missing `learning/block4` `_k_` files.** Filenames listed above. Nothing
  should be converted for SET_A until these are back.
- **fMRI timing convention** — nominal PCL durations (recommended) or empirical log medians?
  A study-owner decision; record it in the provenance header.
- **Confirm the control-block design** with the study author — one image+question screen at
  2500 ms, no separate stimulus phase. The code is unambiguous; the confirmation is a formality.

### Not blocking, but unverified

- **Which AFC scenario runs** — `05_AFC.sce` is the likely one on code evidence, but no AFC-phase
  log was available. Find one in `Ergebnisse/` and check whether trial order varies across
  participants.
- **The cross-scenario chain** — assumed `00_Instr_1 → 01_Prac → 02_Instr_2 → 03_learning → AFC →
  04_Instr_3`. Sort `Ergebnisse/` logs by timestamp to confirm.
- **Log time units** — findings above assume Presentation logs in 0.1 ms (a 2000 ms setting logs
  as ~20997, consistently). Confirm against your Presentation configuration before relying on
  derived durations.

### Infrastructure

- **Credential mechanism** — bearer token vs API key. Only matters for CI (§10); `claude doctor`.
- **`psychopy.yml` builds cleanly** on your machine — verify once.
- **Target PsychoPy version** — pins the API surface; every ⚠️ symbol in §7 should be checked
  against it. Lower priority while "it runs" is the v0 bar.
- **Does AppHubAI honor sampling params / what is its `num_ctx`?** The context length is the more
  important of the two: if the server truncates below ~32k, no prompting change will fix output
  quality on multi-file reads.

**Resolved:** endpoint transport · no trigger hardware · paradigm is a directory tree with logic in
`sce/` · assets in nested `Stimuli/**` · practice = 40 trials · 336 learning trials · response
mapping (98→1 "richtig", 97→2 "falsch") · block order is a constrained runtime shuffle ·
`30 → 28` historical · `01_Prac_old.sce` obsolete · "it runs" is the acceptance bar.

---

## Sources

Claude Code facts marked ✅ were verified July 15, 2026 against Anthropic's official docs:
- Setup / native installer: https://code.claude.com/docs/en/setup
- Model configuration & alias-override env vars: https://code.claude.com/docs/en/model-config

PsychoPy, PsychoJS, and Pygame API specifics were **not** executed here and should be confirmed
against your installed versions:
- PsychoPy API: https://psychopy.org/api/
- PsychoJS API: https://psychopy.github.io/psychojs/
- Pygame docs: https://www.pygame.org/docs/

I do not have a verified source for the AppHubAI endpoint's supported API format or the model
spec figures in the original guide's model table — both need confirmation from the University of
Greifswald AppHubAI documentation directly.
