---
name: read-paper
description: Extract a project's paper (PDF) into text and page images and pull out the facts BEEHub needs — task, domain, participants, sessions, measures, analysis. Use before planning, describing, or checking a project.
---

# Reading the paper

The paper is the single best evidence source for what a project *is*. Read it
before forming any view from filenames.

## 1. Convert

OpenCode does not pass PDFs to the model. Convert first:

```bash
uv run Agent/tools/pdf_for_agent.py "<path to pdf>" -o "<output dir>"
```

- Text layer → one `<name>.md`. Read this with the read tool.
- Pages with no text layer (scans, figure-only pages) → `page-NNN.png`.
- `--render 4,7` forces specific pages to PNG too (results tables are often
  images); `--dpi 300` for small print.

Output dirs: during intake `Convert/<drop>/_intake/paper/`; after restructure
`Projects/<CODE>/agent_out/paper/`.

**If you need a PNG page and cannot see it**, list which pages and ask the human
to re-run the session attaching them (`opencode run -f "<png>" ...`). Never
guess what an image contains.

## 2. Extract — quote the sentence for each

| Field | Where it usually is |
|---|---|
| task type, cognitive domain, modality | Abstract, Methods intro |
| language of materials, experimental context | Methods |
| original software | Methods / Apparatus |
| participants: n recruited, n analysed, exclusions | Methods / Participants |
| sessions, blocks, trials per block | Procedure / Design |
| outcome measures | Methods / Analysis, Results |
| analysis steps | Statistical analysis |

For each field write the value **and the supporting sentence with page number**.
If the paper does not state it, write `not stated`. Do not infer.

## 3. Treat paper numbers as claims, not facts

The paper states what the authors intended or found; the data show what is on
disk. Where they disagree, that is a finding to report — the measured value wins
for structure, and the disagreement is recorded, never silently resolved.
