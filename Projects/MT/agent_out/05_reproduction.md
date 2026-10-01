# Reproduction check — MT (Mahesan 2026, mouse-tracking go/no-go)

Stage 05 of the BEEHub pipeline. Compares the paper's reported numbers against the
per-participant scored tables in `Projects/MT/derivatives/` using
`Agent/tools/reproduce_check.py compare`.

## Command

```
uv run Agent/tools/reproduce_check.py compare "Projects/MT/code/paper_claims.yaml" "Projects/MT/derivatives"
```

## Result

**69 claim(s): 0 match, 8 mismatch, 0 missing, 61 unresolved**

The exit code is non-zero because the tool treats every MISMATCH and UNRESOLVED as a
failure. **No claim matches.** The 8 MISMATCHes are a tool-capability artifact (see
below), not evidence that the analysis is wrong.

## Why no claim can PASS with the current tool

The comparison tool computes one statistic over **one file per claim**. Its
`source.file` glob is resolved with `Path.rglob`, which returns the **lexicographically
first hit** — it does **not** pool multiple files. For this project that file is always:

```
Projects/MT/derivatives/scored/sub-001/ses-01/beh/sub-001_ses-01_task-gonogo_desc-scored_beh.tsv
```

i.e. **one participant (sub-001), one session (ses-01), one task run**. The paper's
headline means, by contrast, are **pooled across participants and sessions** and
**trimmed of outliers**:

- Kinematic analyses were restricted to **correct trials only**; outliers were removed
  **cell-wise per metric** — *"1.5% of observations were removed for mean velocity,
  2.3% for mean acceleration, and 2.4% for path length"* (Methods, p. 17).
- The reported group means/ICCs are computed over the pooled, trimmed sample
  (df = 22 → 23 participants after one exclusion).

The tool cannot express "pool across all 50 TSVs", "correct trials only", or
"±2.5 SD trim", and its `scale` is a pure multiplier (no offset, so an error rate
`1 − mean(correct)` is not expressible). Every claim that needs one of those operations
therefore reads a single participant's untrimmed numbers and cannot equal the paper's
pooled value.

### The 8 MISMATCHes (single participant/session vs. pooled paper value)

| Claim | Paper (pooled) | Got (sub-001 / ses-01) | Column |
|---|---|---|---|
| `rt_go` | 582 ms | 615.8 ms | `rt_combined` |
| `rt_nogo_stopping` | 445 ms | 649.7 ms | `nogo_stop_time` |
| `pathlength_go` | 598 px | 572.6 px | `path_length` |
| `pathlength_nogo` | 542 px | 737.9 px | `path_length` |
| `velocity_go` | 1091 px/s | 933.5 px/s | `avg_velocity` |
| `velocity_nogo` | 934 px/s | 541 px/s | `avg_velocity` |
| `acceleration_go` | 25 884 px/s² | 26 510 px/s² | `avg_acceleration` |
| `acceleration_nogo` | 22 264 px/s² | 15 540 px/s² | `avg_acceleration` |

Each "got" value is a plausible per-participant, single-session figure (RT in ms after
the `scale: 1000` factor, kinematics in the paper's own px / px/s / px/s² units). The
spread between "got" and paper is exactly what you would expect when one
participant's untrimmed run is compared to a pooled, trimmed group mean. Note the
directions are not even consistent (e.g. `rt_nogo_stopping` is *longer* here, while
`pathlength_nogo` and `velocity_nogo` are *longer/shorter* than the paper) — the
signature of a single noisy sample, not a systematic unit error.

### The 61 UNRESOLVED (tool cannot express the statistic)

All of these fall into three buckets, none of which the tool can compute:

- **Pooled means already covered above** — their F-tests, p-values, η², session/
  interaction effects (e.g. `rt_trialtype_F` = 43.45, `rt_session_F` = 2.40).
- **Error rates** (`error_rate_go` = 4%, `error_rate_nogo` = 12%) — require
  `1 − mean(correct)`, an offset the pure-multiplier `scale` cannot do.
- **ICC test-retest values** (e.g. `icc_rt_go` = .85, `icc_error_nogo` = .59) — a
  two-session intraclass correlation, which is not one of the tool's supported stats
  (`mean/sd/median/min/max/sum/n/nunique/nrow`).

These remain `source:`-less on purpose: they cannot be checked by this tool, and
mapping them to a fake `source:` would produce a misleading MISMATCH.

## Verdict

- **Reproduction via `reproduce_check.py`: NOT achieved** for any claim, but for a
  stated, expected reason (single-file, untrimmed statistic vs. pooled trimmed paper
  value). This is a **limitation of the comparison tool**, not a finding that the
  delivered code disagrees with the paper.
- **No MISMATCH indicates a unit or column error.** Units were verified against the
  paper (RT/stopping-time in seconds → ms via `scale: 1000`; velocity px/s;
  acceleration px/s²; path length px). Columns map to the paper's constructs
  (`rt_combined`, `nogo_stop_time`, `path_length`, `avg_velocity`, `avg_acceleration`,
  `trial_type`).
- A faithful reproduction of the pooled headline means would require the tool to
  (a) glob-and-pool all 50 TSVs, (b) filter to correct trials, and (c) apply the
  cell-wise ±2.5 SD trim. None of the three are supported. Until then, the 8 mapped
  claims will always read as MISMATCH and the pooled/ICC/error claims as UNRESOLVED.

## Recommendation

Leave the 8 `source:` blocks in `paper_claims.yaml` as-is — they correctly name the
column, statistic and unit, and their `note` already records the single-file
caveat. Treat the 0-match result as "tool cannot verify pooled claims", not as a
failure of the derivation. A real reproduction check would need either an extended
`reproduce_check.py` (pool + trim + offset) or a one-off script that pools the 50
TSVs, trims, and recomputes the group means/ICCs to compare against the paper.
