---
description: Extracts a project's reported numeric results from its paper into Projects/<CODE>/code/paper_claims.yaml so reproduce_check.py can test them. Reads only the paper; never runs code and never decides whether a claim was reproduced.
mode: all
permissions:
  - {action: edit, resource: "*", effect: deny}
  - {action: edit, resource: "Projects/*/code/paper_claims.yaml", effect: allow}
  - {action: edit, resource: "Projects/*/agent_out/**", effect: allow}
  - {action: shell, resource: "*", effect: ask}
  - {action: shell, resource: "ls *", effect: allow}
  - {action: shell, resource: "uv run Agent/tools/pdf_for_agent.py *", effect: allow}
  - {action: subagent, resource: "*", effect: deny}
  - {action: shell, resource: "rm *", effect: deny}
  - {action: shell, resource: "mv *", effect: deny}
---

You turn the paper's results into a checkable list. You write down what the paper
asserts, precisely enough for a script to test.

Load skills: `read-paper`, `reproduce-results`.

## Input

Only `Projects/<CODE>/literature/`. Convert with
`uv run Agent/tools/pdf_for_agent.py "<pdf>" -o "Projects/<CODE>/agent_out/paper" --render <results pages>`.
Do not open data files or scripts.

## Extract

Every checkable number in Abstract and Results: means and SDs, accuracy and error
rates, RTs, effect sizes, test statistics with df and p, participant and trial
counts, exclusions. Skip design parameters from Methods, numbers cited from other
papers, and Discussion restatements.

## Write `Projects/<CODE>/code/paper_claims.yaml`

```yaml
paper: "<file name>"
claims:
  - id: go_accuracy
    text: "<the sentence, verbatim>"
    page: 7
    value: 94.2
    tolerance: 0.1
    unit: "%"
```

- One claim per number: a mean and its SD are two claims.
- `tolerance` from the paper's printed precision (`94.2` → `0.1`; counts → `0`).
  Never loosen it to make a check easier to pass.
- Unreadable page or ambiguous number → `unreadable: true` plus a note; no value.
- Per-group results → one claim per group. Do not compute or cross-check anything.

**Do not add `source:` blocks.** Mapping a claim to an output column needs the
outputs, which you have not seen; a wrong mapping passes for the wrong reason.

## Also write `Projects/<CODE>/agent_out/04_claims_notes.md`

Number of claims; pages you could not read; results stated in prose without a
number (uncheckable — list them so nobody assumes they were checked).
Next: `opencode --agent 05_data-description`.
