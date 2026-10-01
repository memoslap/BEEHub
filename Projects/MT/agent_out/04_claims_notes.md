# 04 — Paper claims: Mahesan_2026_mousetracking_gonogo

Paper: `Projects/MT/literature/Mahesan_2026_mousetracking_gonogo.pdf`
Output: `Projects/MT/code/paper_claims.yaml`

## Claim summary

| Group | Count | Source pages | Description |
|-------|-------|--------------|-------------|
| error | 11 | 12–13 | Error rates (go 4%, no-go 12%), ANOVA stats (trial-type, session, interaction), ICCs |
| rt | 11 | 15 | RT (go 582 ms, no-go stopping 445 ms), ANOVA stats, ICCs |
| pathlength | 11 | 17–18 | Path length (go 598 px, no-go 542 px), ANOVA stats, ICCs |
| velocity | 11 | 20 | Mean velocity (go 1091 px/s, no-go 934 px/s), ANOVA stats, ICCs |
| acceleration | 11 | 22 | Mean acceleration (go 25 884 px/s², no-go 22 264 px/s²), ANOVA stats, ICCs |
| icc | 10 | 13, 15, 18, 20, 22 | Test-retest ICCs for all five measures (go and no-go) |
| outlier | 3 | 17 | Kinematic outlier removal percentages (velocity 1.5%, acceleration 2.3%, path length 2.4%) |
| n | 1 | 2 | Participant count (23) |
| **Total** | **69** | | |

## Page mapping

| Claim group | Paper page(s) | Markdown section | Notes |
|-------------|---------------|------------------|-------|
| n_participants | 2 | `## Page 2` (line 42) | Abstract: "Twenty-three healthy young adults" |
| error rates + ANOVA | 12 | `## Page 12` (line 416) | Error rate results, F(1,22) stats |
| error ICCs | 13 | `## Page 13` (line 445) | Go error ICC=.75, no-go error ICC=.59 |
| RT + ANOVA | 15 | `## Page 15` (line 494) | RT results, F(1,22) stats |
| RT ICCs | 15 | `## Page 15` (line 494) | Go RT ICC=.85, no-go RT ICC=.79 |
| kinematic outliers | 17 | `## Page 17` (line 548) | Outlier removal percentages |
| path length + ANOVA | 17 | `## Page 17` (line 548) | Path length results, F(1,22) stats |
| path length ICCs | 18 | `## Page 18` (line 577) | Go path ICC=.78, no-go path ICC=.83 |
| velocity + ANOVA | 20 | `## Page 20` (line 625) | Velocity results, F(1,22) stats |
| velocity ICCs | 20 | `## Page 20` (line 625) | Go velocity ICC=.83, no-go velocity ICC=.72 |
| acceleration + ANOVA | 22 | `## Page 22` (line 678) | Acceleration results, F(1,22) stats |
| acceleration ICCs | 22 | `## Page 22` (line 678) | Go acceleration ICC=.77, no-go acceleration ICC=.70 |

## Skipped items (not checkable)

- **Abstract ICC range restatement** (p. 2, line 59): "intraclass correlation coefficients ranging from .75 to .85 for go trials and from .59 to .83 for no-go trials" — restates the per-measure ICCs already captured individually; no new numeric claim.
- **RT outlier removal (2.1%)** (p. 11, line 398): "Error trials and outliers (2.1%) were removed prior to RT analyses." — methodological parameter in Data analyses section, not a reported result.
- **Prose-only qualitative statements**: e.g., "robust differences between go and no-go trials across all measures" (p. 2), "good reliability" / "moderate reliability" labels (pp. 13, 15, 18, 20, 22) — no standalone numeric value beyond the ICCs already captured.
- **Design parameters from Methods**: session spacing ("approximately one week"), ICC model specification (ICC(3,1)), benchmark thresholds (Koo & Li, 2016: <.50 poor, .50–.75 moderate, .75–.90 good, >.90 excellent) — design/interpretation context, not results.
- **Exclusion details** (p. 11, lines 394–397): "Two participants did not attend the second session… One additional participant was excluded due to low accuracy on go trials in the go/no-go block during session 1 (49%)." — the 49% is a per-participant criterion, not an aggregate result.

## Verification

- YAML parses with `yaml.safe_load`; 69 claims, 69 unique IDs.
- Every claim has `id`, `text`, `page`, `value`, `tolerance`, `unit`.
- `text` is verbatim from the converted markdown (line numbers in the paper markdown).
- Tolerances set from printed precision: integer counts → 0; 1-decimal %/ms/px → 0.1/0.5/0.5; F/η² → 0.01; p → 0.0005; ICC → 0.01; acceleration → 0.5.
- Page boundaries confirmed by grepping `## Page N` headers in the markdown.

## Pages that could not be read

None. All pages with numeric results had a text layer in the converted markdown.

## Next stage

`opencode --agent 05_data-description`
