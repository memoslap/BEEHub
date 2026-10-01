"""Generate beehub_diagram.svg in the dashboard's black-gold style."""
from xml.sax.saxutils import escape as esc

W, H = 1040, 900
GOLD, GOLD_HI, GOLD_TXT, GOLD_DIM, BRONZE = "#c9a227", "#f0d060", "#d4b44a", "#a08840", "#cd7f32"
SERIF = "Georgia, 'Times New Roman', serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', monospace"
out = []
add = out.append


def text(x, y, s, size=10.5, fill=GOLD_TXT, weight="normal", anchor="middle",
         family=SANS, style="normal", spacing=None, opacity=None):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    extra += f' opacity="{opacity}"' if opacity else ""
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" font-style="{style}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def card(x, y, w, h, title=None, lines=(), files=(), highlight=False, title_size=12.5,
         line_gap=14, top_accent=True):
    stroke = GOLD_HI if highlight else "rgba(201,162,39,0.35)"
    sw = 1.8 if highlight else 1
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="url(#cardGrad)" '
        f'stroke="{stroke}" stroke-width="{sw}"/>')
    if top_accent:
        add(f'<rect x="{x+10}" y="{y}" width="{w-20}" height="3" rx="1.5" fill="url(#goldBar)"/>')
    cy = y + 22
    if title:
        text(x + w / 2, cy, title, size=title_size, fill=GOLD_HI, weight="bold")
        add(f'<line x1="{x+18}" y1="{cy+7}" x2="{x+w-18}" y2="{cy+7}" stroke="rgba(201,162,39,0.25)"/>')
        cy += 24
    for ln in lines:
        text(x + w / 2, cy, ln)
        cy += line_gap
    if files:
        cy += 2
        for f in files:
            text(x + w / 2, cy, f, size=9.5, fill=GOLD_DIM, style="italic", family=MONO)
            cy += 13
    return cy


def pill(x, y, w, label, filled=False, color=GOLD, size=9.5, h=20):
    if filled:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="{color}"/>')
        text(x + w / 2, y + h / 2 + 3.4, label, size=size, fill="#1a1a1a", weight="bold")
    else:
        add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h/2}" fill="rgba(201,162,39,0.08)" '
            f'stroke="{color}" stroke-width="1"/>')
        text(x + w / 2, y + h / 2 + 3.4, label, size=size, fill=color, weight="bold")


def band(y, h, label):
    add(f'<rect x="14" y="{y}" width="{W-28}" height="{h}" rx="12" fill="rgba(201,162,39,0.04)" '
        f'stroke="rgba(201,162,39,0.22)"/>')
    add(f'<rect x="22" y="{y+8}" width="30" height="{h-16}" rx="7" fill="#1c1a10" '
        f'stroke="rgba(201,162,39,0.35)"/>')
    cx, cy = 37, y + h / 2
    add(f'<text x="{cx}" y="{cy}" transform="rotate(-90 {cx} {cy})" font-family="{SERIF}" '
        f'font-size="12" fill="{GOLD}" font-weight="bold" letter-spacing="3" text-anchor="middle" '
        f'dominant-baseline="middle">{label}</text>')


def arrow(x1, y1, x2, y2):
    add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{GOLD}" stroke-width="1.6" '
        f'opacity="0.75" marker-end="url(#arr)"/>')


# ------------------------------------------------------------------ defs + bg
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
add(f'''<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0f0f0f"/><stop offset="0.5" stop-color="#1a1a1a"/><stop offset="1" stop-color="#111111"/>
  </linearGradient>
  <linearGradient id="header" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#2c2c2c"/><stop offset="0.5" stop-color="#414141"/><stop offset="1" stop-color="#2c2c2c"/>
  </linearGradient>
  <linearGradient id="cardGrad" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#1c1a10"/><stop offset="0.5" stop-color="#201e12"/><stop offset="1" stop-color="#1a1810"/>
  </linearGradient>
  <linearGradient id="goldBar" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{GOLD}" stop-opacity="0.2"/><stop offset="0.5" stop-color="{GOLD_HI}"/>
    <stop offset="1" stop-color="{GOLD}" stop-opacity="0.2"/>
  </linearGradient>
  <linearGradient id="titleGold" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{GOLD}"/><stop offset="0.5" stop-color="{GOLD_HI}"/><stop offset="1" stop-color="{GOLD}"/>
  </linearGradient>
  <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="{GOLD}"/>
  </marker>
</defs>''')
add(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')

# ------------------------------------------------------------------ header
add(f'<rect x="0" y="0" width="{W}" height="54" fill="url(#header)"/>')
add(f'<rect x="0" y="53" width="{W}" height="1.5" fill="url(#goldBar)"/>')
text(W / 2, 35, "BEE Hub — Platform Architecture", size=23, fill="url(#titleGold)",
     family=SERIF, spacing=2)

# ------------------------------------------------------------------ TOOL band
band(66, 132, "TOOL")
text(W / 2 + 20, 86, "Pre-step — metadata authoring tool (runs offline in the browser, before any script)",
     size=12, fill=GOLD_HI, weight="bold", family=SERIF)

# classification box (left)
add('<rect x="64" y="98" width="150" height="88" rx="8" fill="#1c1a10" stroke="rgba(201,162,39,0.35)" stroke-dasharray="4 3"/>')
text(139, 116, "Classification step", size=10.5, fill=GOLD_HI, weight="bold")
for i, s in enumerate(["Modality · Task type", "Cognitive domain", "Language",
                       "Experimental context"]):
    text(139, 133 + i * 13, s, size=9.8)

# main form box
add('<rect x="228" y="96" width="600" height="92" rx="10" fill="url(#cardGrad)" stroke="#f0d060" stroke-width="1.6"/>')
# drawn document icon (replaces emoji, which does not render everywhere)
add('<rect x="244" y="114" width="40" height="52" rx="5" fill="#2c2a18" stroke="#c9a227"/>')
for k in range(4):
    add(f'<line x1="252" y1="{126+k*9}" x2="{276 - (8 if k == 3 else 0)}" y2="{126+k*9}" stroke="#d4b44a" stroke-width="1.6"/>')
text(296, 134, "01_description_form.html", size=13, fill=GOLD_HI, weight="bold", anchor="start", family=MONO)
text(296, 152, "7-step browser wizard", size=10.5, anchor="start")
text(296, 167, "live JSON preview · validation", size=9.5, fill=GOLD_DIM, anchor="start", style="italic")
add('<line x1="474" y1="106" x2="474" y2="178" stroke="rgba(201,162,39,0.3)"/>')
steps = [("1 Identity", 66), ("2 Description", 82), ("3 Classification", 98), ("4 Procedure", 74),
         ("5 Software", 70), ("6 Outcomes", 74), ("7 Review & Download", 128)]
x0, y0 = 486, 112
row = [steps[:4], steps[4:]]
for r, items in enumerate(row):
    x = x0
    for lab, w in items:
        hi = lab.startswith(("3", "6"))
        pill(x, y0 + r * 32, w, lab, filled=hi, size=9.2, h=22)
        x += w + 6

# produces box (right)
add('<rect x="842" y="98" width="178" height="88" rx="8" fill="#1c1a10" stroke="rgba(201,162,39,0.35)"/>')
text(931, 116, "Produces", size=10.5, fill=GOLD_HI, weight="bold")
text(931, 133, "MYPROJECT_description.json", size=9.2, fill=GOLD_DIM, style="italic", family=MONO)
text(931, 150, "→ move to", size=9.8)
text(931, 164, "Projects/MYPROJECT/", size=9.2, fill=GOLD_DIM, family=MONO)
text(931, 178, "before running scripts", size=9.8)

arrow(465, 188, 465, 226)

# ------------------------------------------------------------------ INPUT band
band(216, 168, "INPUT")
cw, gap, cx0 = 154, 8, 64
inputs = [
    ("Raw Trial Data", ["RT · Accuracy", "Trial-level TSV files", "BIDS-compatible"],
     ["*_RT_beh.tsv", "*_ACC_beh.tsv", "*_ACCBIN_beh.tsv"], "REQUIRED for analysis", False),
    ("Participant Data", ["Age · Sex", "Sample size", "Clinical / healthy"],
     ["participants.tsv"], "REQUIRED for analysis", False),
    ("Description JSON", ["Modality · Domain · Task", "Language · Exp. context", "Implementations",
                          "outcome_measures [ ]"],
     ["*_description.json"], "via 01_description_form", True),
    ("Paradigm Code", ["PsychoPy / E-Prime", "Original + compatible ports", "Multi-language versions"],
     ["paradigm/psychopy/", "paradigm/eprime/ etc."], None, False),
    ("Publications", ["DOI · Authors · Year", "Open-access flag", "ICC from paper"],
     ["bibliography.json", "(v2 schema preferred)"], None, False),
    ("Filter Tags", ["Cognitive domain · Modality", "Experimental context", "Language · Task type"],
     ["project_info dict"], None, False),
]
for i, (t, ls, fs, badge, hi) in enumerate(inputs):
    x = cx0 + i * (cw + gap)
    card(x, 228, cw, 146, t, ls, fs, highlight=hi, line_gap=13.5)
    if badge:
        bronze = badge.startswith("REQ")
        c = BRONZE if bronze else GOLD
        add(f'<rect x="{x+14}" y="350" width="{cw-28}" height="17" rx="8.5" fill="rgba(201,162,39,0.08)" stroke="{c}"/>')
        text(x + cw / 2, 362, badge, size=8.8, fill=c, weight="bold")
for i in range(6):
    x = cx0 + i * (cw + gap) + cw / 2
    arrow(x, 384, x, 400)

# ------------------------------------------------------------------ PROCESSING band
band(402, 176, "PROCESSING")
scripts = [
    ("01_multi_project_overview.py", ["Load TSVs per outcome_measures", "Parse BIDS · task vs. control",
                                      "Reliability via module ▸", "Demographics · learning stages"],
     "→ _data.json + _overview.html"),
    ("02_generate_paradigm.py", ["Read description + _data.json", "Software & language block",
                                 "Implementations (original first)", "Paradigm files + demo link"],
     "→ _paradigm.html"),
    ("03_generate_dashboard.py", ["Aggregate all _data.json", "Combo-select + metric filters",
                                  "Reliability radars", "Project cards"],
     "→ dashboard.html"),
]
sw_, sx0 = 186, 64
for i, (t, ls, o) in enumerate(scripts):
    x = sx0 + i * (sw_ + 14)
    add(f'<rect x="{x}" y="414" width="{sw_}" height="118" rx="9" fill="url(#cardGrad)" stroke="rgba(201,162,39,0.35)"/>')
    add(f'<rect x="{x+10}" y="414" width="{sw_-20}" height="3" rx="1.5" fill="url(#goldBar)"/>')
    text(x + sw_ / 2, 434, t, size=10.3, fill=GOLD_HI, weight="bold", family=MONO)
    for k, ln in enumerate(ls):
        text(x + sw_ / 2, 454 + k * 14, ln, size=10)
    text(x + sw_ / 2, 522, o, size=9.5, fill=GOLD_DIM, style="italic", family=MONO)
    if i < 2:
        arrow(x + sw_ + 1, 473, x + sw_ + 13, 473)

# shared module strip
add('<rect x="64" y="540" width="586" height="28" rx="8" fill="rgba(201,162,39,0.10)" stroke="rgba(201,162,39,0.45)" stroke-dasharray="4 3"/>')
text(76, 558, "reliability_metrics.py", size=10.5, fill=GOLD_HI, weight="bold", anchor="start", family=MONO)
text(240, 558, "shared module · imported by 01 (not run directly) · ICC via pingouin 0.6.1",
     size=9.8, anchor="start")

# metrics box
mx, mw = 664, 356
add(f'<rect x="{mx}" y="414" width="{mw}" height="154" rx="9" fill="url(#cardGrad)" stroke="#f0d060" stroke-width="1.4"/>')
text(mx + mw / 2, 434, "Reliability metrics (task trials only)", size=12, fill=GOLD_HI, weight="bold")
add(f'<line x1="{mx+18}" y1="441" x2="{mx+mw-18}" y2="441" stroke="rgba(201,162,39,0.25)"/>')
metrics = [("ICC(C,1)", "consistency, 95 % CI"), ("ICC(A,1)", "absolute agreement, 95 % CI"),
           ("Pearson r", "session 1 vs. session 2"), ("Session-shift d", "→ stability score"),
           ("Hedges' g", "paradigm effect size"), ("Cronbach's α / KR-20", "internal consistency"),
           ("Within-session CV", "continuous outcomes only")]
for k, (a, b) in enumerate(metrics):
    yy = 458 + k * 14
    text(mx + 22, yy, a, size=10, fill=GOLD_HI, weight="bold", anchor="start")
    text(mx + 160, yy, b, size=10, anchor="start")
text(mx + mw / 2, 559, "control / rest / baseline stored separately, excluded from ICC",
     size=9, fill=GOLD_DIM, style="italic")

for x in (157, 357, 557):
    arrow(x, 578, x, 594)

# ------------------------------------------------------------------ DISCOVERY band
band(596, 212, "DISCOVERY")
# FAIR
add('<rect x="64" y="608" width="118" height="188" rx="9" fill="url(#cardGrad)" stroke="rgba(201,162,39,0.35)"/>')
text(123, 630, "FAIR", size=13, fill=GOLD_HI, weight="bold", family=SERIF, spacing=2)
for k, (L, rest) in enumerate([("F", "indable"), ("A", "ccessible"), ("I", "nteroperable"), ("R", "eusable")]):
    add(f'<text x="80" y="{654+k*17}" font-family="{SANS}" font-size="11"><tspan fill="{GOLD_HI}" font-weight="bold">{L}</tspan><tspan fill="{GOLD_TXT}">{rest}</tspan></text>')
add('<line x1="78" y1="720" x2="168" y2="720" stroke="rgba(201,162,39,0.25)"/>')
for k, s in enumerate(["Git-versioned", "Open source (GPL-2.0)", "BIDS-inspired", "Meta-analysis ready"]):
    text(123, 738 + k * 14, s, size=9.3, fill=GOLD_DIM, style="italic")

# dashboard container
dx, dw = 194, 646
add(f'<rect x="{dx}" y="608" width="{dw}" height="188" rx="10" fill="#161510" stroke="#f0d060" stroke-width="1.4"/>')
add(f'<rect x="{dx+12}" y="608" width="{dw-24}" height="3" rx="1.5" fill="url(#goldBar)"/>')
text(dx + dw / 2, 630, "Interactive Dashboard — BEE Hub", size=13.5, fill="url(#titleGold)",
     weight="bold", family=SERIF, spacing=1)
panels = [
    ("Filter Panel", ["Cognitive domain · Task type", "Modality · Language",
                      "Experimental context", "Metric range · Age · N"], "task / control · primary / secondary"),
    ("Project Cards", ["Name · domain tags", "Subjects · Mean age",
                       "Primary-outcome ICC", "CV (continuous only)"], "View Details · Paradigm"),
    ("Radar Charts", ["ICC(C) · ICC(A) · r · α", "Stability · Effect size",
                      "Trial CV (continuous)", "Cross-project Plotly radars"], "Reliability Metrics Explained ▾"),
]
pw = 202
for i, (t, ls, foot) in enumerate(panels):
    x = dx + 12 + i * (pw + 9)
    add(f'<rect x="{x}" y="640" width="{pw}" height="92" rx="7" fill="#1c1a10" stroke="rgba(201,162,39,0.3)"/>')
    text(x + pw / 2, 656, t, size=11, fill=GOLD_HI, weight="bold")
    for k, ln in enumerate(ls):
        text(x + pw / 2, 671 + k * 12.5, ln, size=9.4)
    text(x + pw / 2, 726, foot, size=8.6, fill=GOLD_DIM, style="italic")
pages = [("Project Overview  (_overview.html)", ["Violin · Scatter · Reliability radar · Learning stages · Publications"],
          "linked from card → View Details"),
         ("Paradigm Page  (_paradigm.html)", ["Software & language · Implementations · Procedure · Demo link"],
          "linked from card → Paradigm")]
ppw = 305
for i, (t, ls, foot) in enumerate(pages):
    x = dx + 12 + i * (ppw + 12)
    add(f'<rect x="{x}" y="740" width="{ppw}" height="48" rx="7" fill="#1c1a10" stroke="rgba(201,162,39,0.3)"/>')
    text(x + ppw / 2, 755, t, size=10.3, fill=GOLD_HI, weight="bold")
    text(x + ppw / 2, 769, ls[0], size=8.9)
    text(x + ppw / 2, 782, foot, size=8.4, fill=GOLD_DIM, style="italic")

# use cases
ux = 852
add(f'<rect x="{ux}" y="608" width="168" height="188" rx="9" fill="url(#cardGrad)" stroke="rgba(201,162,39,0.35)"/>')
text(ux + 84, 630, "Use Cases", size=13, fill=GOLD_HI, weight="bold", family=SERIF, spacing=1)
for k, s in enumerate(["Select a paradigm", "Compare reliability", "Power estimation", "Meta-analysis",
                       "Replicate studies", "Test pilot data", "Discover by language", "Filter by exp. context"]):
    add(f'<circle cx="{ux+16}" cy="{649+k*18}" r="2.4" fill="{GOLD}"/>')
    text(ux + 26, 653 + k * 18, s, size=10, anchor="start")

# ------------------------------------------------------------------ bottom legend / tags
text(W / 2, 830, "Filterable metadata fields & computed reliability metrics available per paradigm",
     size=10, fill=GOLD_DIM, style="italic")
mets = [("ICC(C,1)", 64), ("ICC(A,1)", 64), ("Pearson r", 68), ("α / KR-20", 70), ("Stability", 64),
        ("Effect size g", 86), ("Trial CV", 60)]
metas = [("Sample size", 78), ("Age", 44), ("Modality", 64), ("Exp. context", 84), ("Cog. domain", 82),
         ("Task type", 66), ("Language", 66)]
x = 64
add(f'<rect x="{x}" y="844" width="12" height="12" rx="3" fill="{GOLD}"/>')
text(x + 18, 854, "computed metric", size=9.5, anchor="start", fill=GOLD_TXT)
x = 170
for lab, w in mets:
    pill(x, 841, w, lab, filled=True, size=9.2)
    x += w + 6
add(f'<rect x="64" y="872" width="12" height="12" rx="3" fill="rgba(201,162,39,0.08)" stroke="{GOLD}"/>')
text(82, 882, "metadata filter", size=9.5, anchor="start", fill=GOLD_TXT)
x = 170
for lab, w in metas:
    pill(x, 869, w, lab, filled=False, size=9.2)
    x += w + 6

add('</svg>')
open('/home/claude/svg/beehub_diagram.svg', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
