# The Intake agent (00_Intake) — watch Convert/, plan, confirm, dispatch

## What you asked for, and the one adjustment
You want an overall BEEHub agent that (1) notices when something lands in `Convert/`,
(2) works out what needs doing, (3) **writes a plan and asks you for dataset-specific
instructions before anything runs.** All three are right. One adjustment: don't make
the *agent* the thing that watches. An LLM session that idles waiting for files burns
context and money and can't be trusted to still be alive next week. Split it:

- **A tiny deterministic watcher** (cron job or a filesystem hook) does the "is there
  anything in `Convert/`?" check. No model. It just detects a new drop and launches
  the Intake agent once.
- **The Intake agent** does the part that needs judgement: survey the drop, produce a
  plan, ask you for special instructions, and — only after you confirm — dispatch the
  existing pipeline (restructure → describe → paradigm → check → dashboard).

This keeps the model out of the idle-waiting loop and matches your "propose → review →
apply" discipline: Intake never migrates anything itself, exactly like Describe never
holds the rename hammer.

## Where it sits
It's agent `00_` because it runs before the others and hands off to them. It is
**read-only** over `Convert/` and writes exactly one artifact: a plan file the human
signs off on. It does not rename, move, or convert — it routes.

```
watcher (cron/hook, no model)
   └─ sees new Convert/<drop>/ → launches:
00_Intake  (read-only; SURVEY → PLAN → ASK → on approval, DISPATCH)
   └─ 01_Renaming_Restructure → 02_Create_Description → 03_Paradigm → 04_Check_structure → 05_Dashboard
```
(Resolve the describe/restructure ordering contradiction in your docs before wiring
this — the dispatch order is baked in here as restructure-first per the role files.)

## The confirmation gate is the whole point
The agent must **stop after the plan and wait**. It may not dispatch on the same turn
it produced the plan. Approval is an explicit human message. This is what lets you
inject "for this dataset, session b = ses-2" or "the compiled CSV is the column
authority" before any agent acts on a wrong assumption — the cheapest possible place
to correct course.

---

## Paste into Agent/00_Intake/CLAUDE.md

```
# BEEHub Intake Agent — detect, plan, confirm, dispatch

You are the front door. Something has landed in `Convert/`. You SURVEY it, write a
PLAN, ask the human for dataset-specific instructions, and — only after explicit
approval — DISPATCH the pipeline. You are READ-ONLY: you never rename, move, convert,
or write anything except your plan file. You route work; you do not do it.

## Stage 1 — SURVEY (no changes, no guesses)
For each unhandled folder in `Convert/`:
- Inventory: file types, counts, sizes, top-level structure (depth-limited; do not
  recurse into huge trees blindly, and never `cat` a log/.sce/large csv — `head -1`
  and globs only).
- Detect the likely paradigm(s) and whether a project code is stated. If the code is
  not obvious, you will ASK — never invent it.
- Note obvious anomalies: spaces in names, missing sessions, mixed session padding,
  files you cannot classify. Do not normalise anything; just record it.

## Stage 2 — PLAN (write one file, then STOP)
Write `Convert/<drop>/INTAKE_PLAN.md` containing:
- what you think this is (paradigm, project code, rough subject/session count);
- which pipeline agents will run and in what order, and what each will do;
- every assumption you are making, each marked so it is easy to override;
- every anomaly and open question, phrased as a concrete yes/no where possible;
- an explicit list titled "Tell me before I start:" — the dataset-specific decisions
  you need (e.g. session-letter → number mapping, which file is the column authority,
  task label, whether a measure is primary/secondary).
Then STOP and show the human the plan. Do NOT dispatch anything this turn.

## Stage 3 — DISPATCH (only after explicit approval)
When (and only when) the human approves — and after folding in any instructions they
gave — hand off to the pipeline. For each agent, the handoff is a PATH to the plan and
the drop, not the raw data: the pipeline reads files itself.
- Record the approved instructions into the target project's `# PROJECT NOTES` (via
  the relevant agent), so they are captured as authoritative, not lost in chat.
- Dispatch order: 01_Renaming_Restructure → 02_Create_Description → [human reviews JSON]
  → 03_Paradigm → 04_Check_structure → 05_Dashboard. Respect the review points; do not
  collapse them.

## Hard rules
- Read-only over Convert/. One writable artifact: INTAKE_PLAN.md.
- Never dispatch on the same turn you wrote the plan. Approval is a separate message.
- Never invent a project code, a session mapping, or a paradigm identity. Ask.
- If Convert/ has several drops, handle ONE per session; list the rest and stop.
- If nothing in Convert/ is new (all drops already have a completed marker), say so
  and stop — do not re-process.
```

---

## The watcher (deterministic, no model)
Keep it boring. A cron entry or a hook that checks for an unhandled drop and launches
Intake once, headless. Sketch — verify flags against your CLI:

```bash
# intake_watch.sh — run from repo root, e.g. via cron every 10 min
set -uo pipefail
cd "$(dirname "$0")"
for d in Convert/*/; do
  [[ -f "${d}.beehub_done" ]] && continue          # already handled
  [[ -f "${d}INTAKE_PLAN.md" ]] && continue         # plan exists, awaiting human
  ./beehub-agent 00 -p "A new drop is in ${d}. Run Stage 1 SURVEY and Stage 2 PLAN
      for it, then stop."                            # headless launch, plan only
  break                                              # one drop per run
done
```

Notes:
- The watcher only ever triggers **plan** generation. Dispatch stays human-gated — the
  watcher never approves anything.
- Markers (`.beehub_done`, presence of `INTAKE_PLAN.md`) make it idempotent: it won't
  re-plan a drop that's already waiting on you or already finished.
- If your CLI build can't run headless (`-p`), the watcher can instead just notify you
  (write a line to a log / send a mail) and you launch Intake interactively. Verify
  headless support before relying on it — same caveat as the rest of the modern-tooling
  stack.

## Honest caveats
- A small local model as a *dispatcher* is the weak spot (planning a route is harder
  than doing one scoped task). Keep Intake's job narrow and deterministic: fixed
  pipeline order, fixed plan template, ask-don't-guess. The routing is fixed, so it
  barely has to "decide" anything — which is what you want on a 30–35B model.
- Don't let Intake also *do* the work — the moment it both plans and executes, you lose
  the confirmation gate that makes it safe.
- This is the same shape as the orchestrator in `AGENT_ARCHITECTURE_DEEPDIVE.md`; if
  you adopt native subagents later, Intake becomes the thin lead agent and the pipeline
  agents become its subagents, with the plan-and-confirm gate unchanged.
```
