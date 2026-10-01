---
name: outcome-selection
description: Find which BIDS columns can serve as reliability (ICC) outcomes and get the human to assign primary/secondary roles. Use in data-description before recording outcomes, and in project-description when transcribing them.
---

# Outcome selection

```bash
python3 Agent/tools/suggest_outcomes.py <CODE>
```

It scans `bids_data/` **and** every `derivatives/<name>/` tree beside it, and
labels each candidate with the location it came from. After a derivation run,
re-run it: the derived columns are usually the only viable outcomes.

Exit 0 → candidates exist (✅). Exit 1 → none; a derivation is needed
(skill `derivation-contract`). Show the tool's output **verbatim**.

## Ask — never answer these yourself

1. Which column is the **primary** outcome? (required)
2. Which is the **secondary**? (or none)
3. Up to four others for ICC and the overview? (or none)

For each chosen column: `higher_is_better`, `binary`, short label, axis label.

## Roles are always explicit — three states, never a default

Every project is in exactly one of these. Record which one, and say so in your report.

| State | How it looks | Effect |
|---|---|---|
| **Declared** | `"role": "primary"` on one entry, at most one `"secondary"` | enters the cross-project comparison |
| **Undecided** | `"role": "undecided"` on the candidates, plus an open decision in `Agent/notes/<CODE>.md` | reported at project level, withheld from cross-project comparison |
| **Missing** | no `role` key anywhere | a bug — the check agent flags it |

Undecided and Missing look the same in a dashboard but mean opposite things: one
is a research decision still pending, the other is a pipeline failure. Always
write `"undecided"` rather than leaving `role` out.

`display_priority` orders the dashboard. It carries **no** scientific meaning and
must never be read as "this is the headline outcome" — someone reordering a
dashboard for visual reasons would otherwise silently change what the project
claims to measure. Column order implies nothing either.

Why this matters here: reliability differs systematically between measure types
within one paradigm, so which column is primary moves the project's position in
the cross-project comparison. A defaulted primary would make that position an
artifact of file ordering rather than a research priority. Withholding a project
is the honest state, not a failure — report it plainly. Never supply a default.

⚠️ `is_primary` in the description form means "restrict to correct trials" (a
legacy name for `requires_correct_filter`). It does **not** mark the headline
outcome. Setting it for that purpose silently filters the wrong trials.

## Record in `Agent/notes/<CODE>.md`

```
## Derived outcomes
- PRIMARY   | column: <name> | suffix: <_desc-x_beh.tsv> | higher_is_better: yes/no
            | binary: yes/no | label: <text> | axis_label: <text>
- SECONDARY | ...
- (no role) | ...
```

A column not marked ✅ by the tool does not exist as an outcome. Never invent one.
