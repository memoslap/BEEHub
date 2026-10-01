# Project notes — <CODE>

Authoritative project-specific facts. These **override** the generic rules in
`AGENTS.md` and in any skill. Every agent reads this file before doing project
work.

Replace each `?` with an answer. A line still containing `?` is an **unanswered
question**: agents must put it to the human and stop rather than guess.

Delete nothing. A question that turns out not to apply gets `n/a` plus a reason,
so the next person can see it was considered.

---

## Identity

- project_code: `<CODE>`
- full_name: ?
- paper: ?                        <!-- filename in literature/ -->
- source_drop: ?                  <!-- folder name under Convert/ -->

## Structure

- session_mapping: ?              <!-- e.g. source suffix a -> ses-01, b -> ses-02 -->
- task_label: ?                   <!-- the <label> in task-<label>, alphanumeric -->
- n_participants: ?               <!-- from inventory_sessions.sh, never counted by eye -->
- n_sessions: ?
- incomplete_subjects: ?          <!-- who, which session missing, and what the paper says -->
- column_authority: ?             <!-- which file wins when two disagree -->

## Known quirks

<!-- Anything true of this project only: encoding, a renamed variable, a session
     recorded out of order, a file that looks like data but is not. One per line. -->

- ?

## Paradigm

- paradigm_source: ?              <!-- psychopy | presentation | other | none -->
- entry_script: ?
- reference_implementation: ?     <!-- an existing human-made version to match, or n/a -->
- convert_or_verify: ?            <!-- convert = generate new; verify = check it runs -->

## Derived outcomes

<!-- Written by 05_data-description AFTER the human chooses. Roles are explicit:
     exactly one primary, at most one secondary, "undecided" where the PI has not
     decided. Never inferred from display_priority or column order. -->

- PRIMARY   | column: ? | suffix: ? | higher_is_better: ? | binary: ? | label: ? | axis_label: ?
- SECONDARY | column: ? | suffix: ? | higher_is_better: ? | binary: ? | label: ? | axis_label: ?

## Derivation

<!-- Written by 05_data-description. Parameters exactly as run — an unrecorded
     threshold makes every number computed from it uninterpretable. -->

- name: ?
- script: ?
- input: ?
- output: ?
- output_glob: ?
- parameters: ?
- exclusions: ?                   <!-- what is dropped; what a failed parse scores -->
- description: ?

## Open decisions

<!-- Questions the human has seen and deliberately not answered yet. Each blocks
     something — say what. -->

- ?

## Log

<!-- One line per stage that ran: date, stage, what it changed. Append only. -->

- ?
