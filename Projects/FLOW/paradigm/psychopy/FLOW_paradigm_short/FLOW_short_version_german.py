# ═══════════════════════════════════════════════════════════════════════════════
# FLOW — SHORT VERSION CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
# Drop-in replacement for the CONFIG block of FLOW_paradigm_psychoPy.py.
# Copy the full script to FLOW_short_version_psychoPy.py, then replace its CONFIG
# block with this one. Nothing below the CONFIG fence changes.
#
#   FULL : fam 180s + eval 300s + 12 blocks x 174s + rest  ≈ 43 min
#   SHORT: fam  60s + eval  skipped + 6 blocks x  64s + rest ≈  8 min
#
# ⚠️ WHAT MUST NOT CHANGE — these carry the experimental manipulation:
#    - all three CONDITIONS (B / F / O) must still appear, balanced
#    - the adaptive difficulty logic (update_difficulty) is untouched
#    - the Likert items are unchanged, so ratings stay comparable
# ⚠️ WHAT THIS COSTS: with 64 s blocks, participants complete far fewer trials per
#    block, so per-block difficulty adaptation has less time to converge. Treat
#    the short version as a demo/pilot instrument, NOT as a substitute for the
#    full protocol in data collection. Confirm with the study author before use.

# ── Identity ───────────────────────────────────────────────────────────────────
PARADIGM_ID   = "FLOW_short"
DATA_SUFFIX   = "FLOW_math_short"

# ── Timing (SECONDS) ──────────────────────────────────────────────────────────
BLOCK_DURATION = 60.0      # full: 170.0
TASK_TIMEOUT   = 18.0      # unchanged — a per-trial limit, not a length knob
BREAK_DURATION = 4.0       # unchanged
REST_DURATION  = 20.0      # unchanged

FAMILIARISATION_DURATION = 60.0    # full: 180.0
RUN_SKILL_EVALUATION     = False   # full: True (5 min). Short version starts at
                                   # STARTING_LEVEL instead of estimating it.
STARTING_LEVEL           = 3       # used when evaluation is skipped

# ── Conditions ─────────────────────────────────────────────────────────────────
CONDITIONS = {'B': 'Langeweile', 'F': 'Flow', 'O': 'Überlastung'}

# 6 blocks instead of 12 — each condition appears exactly twice, and no two
# adjacent blocks share a condition. Two sequences preserve counterbalancing.
SEQUENCES = [
    ['B', 'F', 'O', 'B', 'F', 'O'],
    ['B', 'O', 'F', 'B', 'O', 'F'],
]

# ── Display geometry (PIXELS — house style requires explicit sizes) ───────────
WIN_SIZE      = (1400, 1050)
BG_COLOR      = (0, 0, 0)
WIN_BG_COLOR  = (1, 1, 1)

TEXT_COLOR    = (0, 0, 0)
DIM_COLOR     = (0.63, 0.63, 0.63)
BOX_BORDER    = (0, 0, 0)
SEL_COLOR     = (0.2, 0.2, 0.78)

# ── Likert (unchanged — keeps ratings comparable to the full version) ─────────
LIKERT_QUESTIONS = [
    "Ich würde solche mathematischen Berechnungen nur zu gern noch einmal lösen",
    "Ich fühle mich optimal beansprucht",
    "Ich war begeistert",
]
LIKERT_LABELS = [
    "Stimme ich\nüberhaupt\nnicht zu", "2", "3", "4", "5", "6",
    "Stimme ich\nvoll zu",
]
