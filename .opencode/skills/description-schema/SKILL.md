---
name: description-schema
description: The key order, controlled vocabularies and outcome_measures field rules for Projects/<CODE>/<CODE>_description.json. Use when writing or auditing a project description.
---

# `<CODE>_description.json` schema

**`01_description_form.html` (repo root) is the authority.** It emits exactly this
JSON. Where this skill and the form disagree, the form wins — say so and continue.
Re-read its `<option>` lists for unusual projects; this copy may lag.

## Keys, in this order

```
full_name, short_description, long_description, background,
procedure, trial_structure, design,
modality, cognitive_domain, task_type, language, experimental_context,
software_original, language_original, implementations[], keywords[],
response_device, timing{}, outcome_measures[], n_sessions, software
```

then `derivations[]` (copied from `code/derivations.json` if present), then
`_provenance` and `_open_questions`.

- `project_code` is **not** a key — it only names the file.
- `timing` is an **object** of named numeric values (or `[min, max]`), using the
  names the paradigm uses: `block_duration_s`, `n_blocks_per_session`, …
- Omit any key you cannot evidence. Never `null`-fill, never `"TBD"`.

## Controlled vocabularies

```
modality:             visual | auditory | linguistic | tactile | multimodal |
                      virtual environment
experimental_context: behavioral | mri | eeg | pet | eye_tracking | fnirs | meg
language:             german | english | french | spanish | dutch | italian |
                      language-independent
cognitive_domain:     working memory | episodic memory | declarative memory |
                      spatial memory | semantic memory | spatial cognition |
                      cognitive control | emotion regulation | attention |
                      language | perception | learning
task_type:            continuous performance / n-back | associative learning |
                      recognition memory | object-location binding |
                      virtual navigation and pointing | color-word interference |
                      cognitive reappraisal | covert verb generation | go / no-go |
                      flanker | task switching | oddball / P300 | stop-signal
```

A new value is allowed, but prefer an existing term and flag any new one in
`_open_questions`.

## `outcome_measures[]` — up to six

Transcribe from `Agent/notes/<CODE>.md` "Derived outcomes". Do not choose them.

Required in every entry: `id` (UPPERCASE), `suffix`, `column`, `label`,
`axis_label`, `higher_is_better`, `is_binary`, `requires_correct_filter`,
`is_helper`, `display_priority`, **`role`**. Optional: `axis_range`,
`reference_line`, `plot_unit` (`trial`|`subject`), `is_global`, `paradigm_contrast`.

- `role`: `"primary"` on exactly one entry, `"secondary"` on at most one, and
  `"undecided"` where the PI has not chosen — always present, never inferred from
  `display_priority` or column order (skill `outcome-selection`). All entries
  `"undecided"` → also add an `_open_questions` entry, because the project is
  withheld from cross-project comparison until a primary is declared.
- `column` must name a real column: check with `head -1` on a real file.
- `suffix` must match a real filename ending exactly.
- **Outcomes in `derivatives/<name>/`**: `suffix` does not say which tree holds the
  file. Record the tree in the matching `derivations[]` entry's `output`, and add
  an `_open_questions` note naming the measure and its tree so a human can confirm
  the pipeline resolves it there. Do not invent a new key for this.
- `plot_unit: "subject"` when rows are not independent observations.
- `is_global: false` for paradigm-specific measures (flow index, d-prime).
- Do not add `main_metrics[]` — the pipeline does not read it.

## Review keys

```json
"_provenance":     { "<field>": "<file, page/line>" },
"_open_questions": [ { "field": "<key>", "why": "<what is missing>" } ]
```

Measured beats stated: if the paper says 40 trials and the data show 56, write 56
and record the discrepancy.
