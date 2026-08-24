# Project notes — <CODE>

Facts the agents cannot work out for themselves. **Authoritative**: these override the
generic rules in any agent's CLAUDE.md.

A double question-mark marks an unanswered question. An agent that finds one must **ask
the human and stop** — it may not answer on its own. Delete a question only by answering
it; write `n/a` if it genuinely does not apply.

---

## Identity
- Project code: `<CODE>`
- Full study name: ??
- Task label (BIDS `task-`, alphanumeric, no separators, e.g. `gonogo`): ??

## Sessions
- How many sessions per participant? ??
- How does the source encode the session? (filename suffix `a`/`b`, a folder, a column) ??
- Mapping to BIDS session numbers (e.g. `a` → `ses-01`, `b` → `ses-02`): ??
- Are any participants known to be incomplete? ?? *(don't guess — the agent must confirm
  with `inventory_sessions.sh`; this line records what YOU already know)*

## Data columns
- Which file is the **column authority** — the one whose header defines the analysed
  column set? ??
- Any columns that must be kept or dropped regardless? ??

## Outcome measures
- Which measures does the analysis actually produce, and where are they defined
  (script, paper section)? ??
- Which is **primary** and which **secondary**? ?? *(a human decision — the agent must
  never pick this)*

## Paradigm
- Software the paradigm was built in: ??
- Language(s) of the presented material: ??
- Anything the agent must NOT touch or rename: ??

## Known quirks
Free text. Anything irregular a human already knows: duplicated files, renamed
participants, an aborted session, a folder that looks wrong but is correct.

- ??

---

## Provenance
Record who said what, so a stale note can be spotted later.

| Fact | Source | Date |
|---|---|---|
| ?? | ?? | ?? |
