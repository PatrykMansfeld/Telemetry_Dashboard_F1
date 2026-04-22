from __future__ import annotations

_DARK = dict(
    bg0="#03040b", bg1="#060810", bg2="#090d18",
    panel="#080b14", panel2="#0b0f1c",
    border="#1a2840", border_soft="#101828",
    text="#b8cde0", muted="#4e6070",
    accent="#e10600", accent2="#c8ff3d", accent3="#00d4ff", accent4="#ff6b00",
    glow="rgba(225,6,0,0.45)", glow_cyan="rgba(0,212,255,0.35)", glow_lime="rgba(200,255,61,0.3)",
    heading="#ffffff",
    grid="rgba(255,255,255,0.018)",
    input_bg="rgba(8,11,20,0.95)", input_text="#ffffff",
    panel_a="rgba(10,15,28,0.97)", panel_b="rgba(5,8,16,0.97)",
    expander_bg="rgba(6,9,16,0.95)",
    chip_bg="rgba(4,6,14,0.95)",
    note_a="rgba(8,12,22,0.98)", note_b="rgba(4,7,14,0.98)",
    hero_a="rgba(8,12,22,0.99)", hero_b="rgba(4,6,14,0.99)",
    feature_a="rgba(10,15,26,0.98)", feature_b="rgba(5,8,16,0.98)",
    results_a="rgba(10,15,26,0.99)", results_b="rgba(4,6,14,0.99)",
    driver_a="rgba(10,15,26,0.98)", driver_b="rgba(5,8,16,0.98)",
    tab_hover="rgba(225,6,0,0.06)", tab_active="rgba(225,6,0,0.07)",
    badge_bg="rgba(0,212,255,0.08)", badge_border="rgba(0,212,255,0.3)",
    ctrl_bg="rgba(6,9,18,0.97)", ctrl_border="#1a2840", ctrl_section="#00d4ff",
)

_LIGHT = dict(
    bg0="#f0f2f8", bg1="#f4f6fb", bg2="#e8ecf5",
    panel="#ffffff", panel2="#f8f9fd",
    border="#c8d4e8", border_soft="#dde4f0",
    text="#1a2540", muted="#6b7a9a",
    accent="#e10600", accent2="#6a5c00", accent3="#0055cc", accent4="#cc4400",
    glow="rgba(225,6,0,0.2)", glow_cyan="rgba(0,85,204,0.2)", glow_lime="rgba(100,80,0,0.1)",
    heading="#0a0f20",
    grid="rgba(0,0,0,0.02)",
    input_bg="rgba(255,255,255,0.98)", input_text="#0a0f20",
    panel_a="rgba(255,255,255,0.97)", panel_b="rgba(245,248,255,0.97)",
    expander_bg="rgba(248,250,255,0.97)",
    chip_bg="rgba(232,240,255,0.98)",
    note_a="rgba(245,248,255,0.99)", note_b="rgba(235,241,255,0.99)",
    hero_a="rgba(240,244,252,0.99)", hero_b="rgba(232,238,250,0.99)",
    feature_a="rgba(255,255,255,0.98)", feature_b="rgba(245,248,255,0.98)",
    results_a="rgba(250,252,255,0.99)", results_b="rgba(240,245,255,0.99)",
    driver_a="rgba(255,255,255,0.98)", driver_b="rgba(245,248,255,0.98)",
    tab_hover="rgba(225,6,0,0.04)", tab_active="rgba(225,6,0,0.05)",
    badge_bg="rgba(0,85,204,0.08)", badge_border="rgba(0,85,204,0.3)",
    ctrl_bg="rgba(255,255,255,0.97)", ctrl_border="#c8d4e8", ctrl_section="#0055cc",
)


def get_css(theme: str = "dark") -> str:
    c = _DARK if theme == "dark" else _LIGHT

    root = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {{
    --bg-0: {c['bg0']};
    --bg-1: {c['bg1']};
    --bg-2: {c['bg2']};
    --panel: {c['panel']};
    --panel-2: {c['panel2']};
    --border: {c['border']};
    --border-soft: {c['border_soft']};
    --text: {c['text']};
    --muted: {c['muted']};
    --accent: {c['accent']};
    --accent-2: {c['accent2']};
    --accent-3: {c['accent3']};
    --accent-4: {c['accent4']};
    --glow: {c['glow']};
    --glow-cyan: {c['glow_cyan']};
    --glow-lime: {c['glow_lime']};
    --heading: {c['heading']};
    --grid: {c['grid']};
    --input-bg: {c['input_bg']};
    --input-text: {c['input_text']};
    --panel-a: {c['panel_a']};
    --panel-b: {c['panel_b']};
    --expander-bg: {c['expander_bg']};
    --chip-bg: {c['chip_bg']};
    --note-a: {c['note_a']};
    --note-b: {c['note_b']};
    --hero-a: {c['hero_a']};
    --hero-b: {c['hero_b']};
    --feature-a: {c['feature_a']};
    --feature-b: {c['feature_b']};
    --results-a: {c['results_a']};
    --results-b: {c['results_b']};
    --driver-a: {c['driver_a']};
    --driver-b: {c['driver_b']};
    --tab-hover: {c['tab_hover']};
    --tab-active: {c['tab_active']};
    --badge-bg: {c['badge_bg']};
    --badge-border: {c['badge_border']};
    --ctrl-bg: {c['ctrl_bg']};
    --ctrl-border: {c['ctrl_border']};
    --ctrl-section: {c['ctrl_section']};
}}
"""

    body = """
/* ─── HIDE SIDEBAR ─── */
section[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }

/* ─── BG ─── */
.stApp {
    background-color: var(--bg-0) !important;
    background-image:
        repeating-linear-gradient(45deg,  var(--grid) 0 1px, transparent 1px 16px),
        repeating-linear-gradient(-45deg, var(--grid) 0 1px, transparent 1px 16px),
        radial-gradient(ellipse 800px 500px at -5%  -8%,  var(--glow),      transparent 55%),
        radial-gradient(ellipse 700px 450px at 108%  4%,  var(--glow-cyan), transparent 55%),
        radial-gradient(ellipse 600px 400px at  50% 105%, var(--glow-lime),  transparent 60%);
    background-attachment: fixed;
}

/* ─── TYPOGRAPHY ─── */
html, body, [class*="css"] {
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
h1, h2, h3, h4, h5 {
    color: var(--heading) !important;
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stDataFrame"] *,
pre, code, .stCodeBlock * {
    font-family: 'JetBrains Mono', monospace !important;
}

/* ─── SCROLLBAR ─── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-0); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-3); }

/* ─── INPUTS ─── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    color: var(--input-text) !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent-3) !important;
    box-shadow: 0 0 0 2px var(--glow-cyan), 0 0 12px var(--glow-cyan) !important;
    outline: none !important;
}
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div > div {
    background-color: var(--input-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    color: var(--input-text) !important;
}

/* ─── SLIDER ─── */
[data-testid="stSlider"] [role="slider"] {
    background-color: var(--accent-3) !important;
    box-shadow: 0 0 14px var(--glow-cyan) !important;
}
[data-testid="stSlider"] > div > div > div > div:first-child {
    background: linear-gradient(90deg, var(--accent), var(--accent-3)) !important;
}

/* ─── CHECKBOX ─── */
[data-testid="stCheckbox"] label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--text) !important;
}

/* ─── BUTTONS ─── */
.stButton > button {
    background: transparent !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-weight: 600 !important;
    font-family: 'Orbitron', sans-serif !important;
    letter-spacing: 0.12em !important;
    font-size: 0.62rem !important;
    text-transform: uppercase !important;
    transition: all 0.2s ease !important;
    padding: 0.55rem 1rem !important;
}
.stButton > button:hover {
    color: var(--heading) !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 18px var(--glow), inset 0 0 12px var(--glow) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #9a0400 0%, #e10600 55%, #ff4422 100%) !important;
    color: #ffffff !important;
    border-color: #e10600 !important;
    box-shadow: 0 0 22px rgba(225,6,0,0.5), 0 6px 24px rgba(0,0,0,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 40px rgba(225,6,0,0.7), 0 8px 30px rgba(0,0,0,0.4) !important;
}

/* ─── TABS ─── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0 !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 0 !important;
    background: transparent !important;
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.06em !important;
    font-size: 0.74rem !important;
    padding: 10px 14px !important;
    transition: color 0.15s, border-color 0.15s, background 0.15s !important;
    text-transform: uppercase !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: var(--heading) !important;
    background: var(--tab-hover) !important;
    border-bottom-color: rgba(225,6,0,0.4) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: var(--tab-active) !important;
    text-shadow: 0 0 12px var(--glow) !important;
}

/* ─── METRIC CARDS ─── */
[data-testid="stMetric"] {
    background: linear-gradient(160deg, var(--panel-a), var(--panel-b)) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 4px !important;
    padding: 16px 20px !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stMetric"]::before {
    content: "" !important;
    position: absolute !important;
    top: 0; left: 0; right: 0 !important;
    height: 2px !important;
    background: linear-gradient(90deg, var(--accent), var(--accent-3)) !important;
    box-shadow: 0 0 10px var(--glow), 0 0 22px var(--glow-cyan) !important;
}
[data-testid="stMetric"]::after {
    content: "" !important;
    position: absolute !important;
    bottom: 0; right: 0 !important;
    width: 36px; height: 36px !important;
    border-right: 1px solid var(--badge-border) !important;
    border-bottom: 1px solid var(--badge-border) !important;
}
[data-testid="stMetricValue"] {
    color: var(--heading) !important;
    font-size: 1.45rem !important;
    font-family: 'Orbitron', monospace !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stMetricLabel"] {
    color: var(--accent-3) !important;
    font-size: 0.58rem !important;
    letter-spacing: 0.22em !important;
    text-transform: uppercase !important;
    font-family: 'Orbitron', sans-serif !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* ─── DATAFRAME ─── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    overflow: hidden !important;
}

/* ─── PROGRESS ─── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, var(--accent), var(--accent-4), var(--accent-3)) !important;
    border-radius: 2px !important;
    box-shadow: 0 0 10px var(--glow), 0 0 20px var(--glow-cyan) !important;
    transition: width 0.3s ease !important;
}

/* ─── ALERTS ─── */
[data-testid="stAlert"] { border-radius: 4px !important; border-left-width: 3px !important; }
.stSuccess { background-color: rgba(0,12,8,0.95) !important; border-color: #00ff9d !important; }
.stWarning { background-color: rgba(18,12,0,0.95) !important; border-color: var(--accent-2) !important; }
.stError   { background-color: rgba(18,2,2,0.95) !important; border-color: var(--accent) !important; }

/* ─── EXPANDER ─── */
[data-testid="stExpander"] {
    background-color: var(--expander-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    letter-spacing: 0.04em !important;
    color: var(--text) !important;
}

/* ─── MISC ─── */
[data-testid="stSpinner"] { color: var(--accent-3) !important; }
hr { border-color: var(--border) !important; margin: 16px 0 !important; }

/* ─── PLOTLY MODEBAR ─── */
.js-plotly-plot .plotly .modebar { background: transparent !important; }
.js-plotly-plot .plotly .modebar-btn path { fill: var(--muted) !important; }
.js-plotly-plot .plotly .modebar-btn:hover path { fill: var(--accent-3) !important; }


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   CONTROLS PANEL (replaces sidebar)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

.ctrl-panel {
    background: var(--ctrl-bg);
    border: 1px solid var(--ctrl-border);
    border-radius: 6px;
    padding: 20px 24px 16px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.ctrl-panel::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent), var(--accent-4), var(--accent-3), var(--accent-2));
    box-shadow: 0 0 14px var(--glow);
}

.ctrl-section {
    color: var(--ctrl-section);
    font-size: 0.56rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    padding: 7px 0 9px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 12px;
    margin-top: 16px;
    font-family: 'Orbitron', sans-serif;
    text-shadow: 0 0 10px var(--glow-cyan);
}
.ctrl-section:first-of-type { margin-top: 4px; }

/* ─── SECTION SUBHEADER ─── */
.f1-subheader {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: var(--heading);
    padding: 10px 0 10px 14px;
    border-left: 3px solid var(--accent-3);
    margin-bottom: 14px;
    text-transform: uppercase;
    position: relative;
    text-shadow: 0 0 12px var(--glow-cyan);
}
.f1-subheader::after {
    content: "";
    position: absolute;
    left: 14px; right: 0; bottom: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--glow-cyan), transparent);
}

/* ─── HERO BANNER ─── */
.hero {
    position: relative;
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 26px 32px;
    margin: -1rem -1rem 2rem;
    background: linear-gradient(135deg, var(--hero-a) 0%, var(--hero-b) 100%);
    overflow: hidden;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
}
.hero::before {
    content: "";
    position: absolute; inset: 0;
    background:
        repeating-linear-gradient(90deg, var(--grid) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(0deg,  var(--grid) 0 1px, transparent 1px 44px);
    pointer-events: none;
}
.hero::after {
    content: "";
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent) 0%, var(--accent-4) 30%, var(--accent-3) 60%, var(--accent-2) 85%, transparent 100%);
    box-shadow: 0 0 18px var(--glow), 0 0 36px var(--glow-cyan);
}
.hero > * { position: relative; z-index: 1; }
.hero-stripe {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
    background: linear-gradient(180deg, var(--accent-2), var(--accent), var(--accent-3));
    box-shadow: 2px 0 24px var(--glow), 2px 0 40px var(--glow-cyan);
}
.hero-icon {
    font-size: 2.6rem;
    line-height: 1;
    filter: drop-shadow(0 0 18px var(--glow)) drop-shadow(0 0 36px var(--glow));
}
.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.9rem;
    letter-spacing: 0.12em;
    color: var(--heading);
    font-weight: 900;
    text-shadow: 0 0 30px var(--glow), 0 2px 0 rgba(0,0,0,0.5);
}
.hero-sub {
    font-size: 0.6rem;
    color: var(--accent-3);
    letter-spacing: 0.32em;
    text-transform: uppercase;
    margin-top: 5px;
    font-family: 'Orbitron', sans-serif;
    text-shadow: 0 0 10px var(--glow-cyan);
}
.hero-tag {
    margin-left: auto;
    font-size: 0.55rem;
    letter-spacing: 0.24em;
    text-transform: uppercase;
    color: var(--accent-2);
    border: 1px solid var(--glow-lime);
    padding: 7px 12px;
    border-radius: 2px;
    background: var(--glow-lime);
    font-family: 'Orbitron', sans-serif;
    box-shadow: 0 0 14px var(--glow-lime);
}
.hero-tag::before {
    content: "● ";
    animation: blink 1.4s ease-in-out infinite;
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.15; }
}

/* ─── WELCOME SCREEN ─── */
.welcome { margin-top: 10px; margin-bottom: 30px; }
.welcome-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.4rem;
    letter-spacing: 0.1em;
    color: var(--heading);
    font-weight: 900;
    text-shadow: 0 0 50px var(--glow);
}
.welcome-sub {
    font-size: 0.92rem;
    color: var(--muted);
    margin-top: 10px;
    letter-spacing: 0.04em;
    line-height: 1.7;
}
.accent { color: var(--accent); font-weight: 700; letter-spacing: 0.1em; }

/* ─── FEATURE CARDS ─── */
.feature-card {
    background: linear-gradient(160deg, var(--feature-a), var(--feature-b));
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 3px;
    padding: 18px 16px;
    margin-bottom: 12px;
    position: relative;
    overflow: hidden;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
    animation: fadeUp 0.55s ease both;
}
.feature-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent, #e10600);
    box-shadow: 0 0 14px var(--accent, #e10600);
}
.feature-card::after {
    content: "";
    position: absolute;
    bottom: 7px; right: 9px;
    width: 16px; height: 16px;
    border-right: 1px solid var(--border-soft);
    border-bottom: 1px solid var(--border-soft);
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 36px rgba(0,0,0,0.3), 0 0 28px var(--glow);
}
.feature-icon { font-size: 1.5rem; margin-bottom: 10px; }
.feature-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.74rem;
    font-weight: 700;
    color: var(--heading);
    letter-spacing: 0.12em;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.feature-desc { font-size: 0.76rem; color: var(--muted); line-height: 1.55; }

/* ─── NOTE CARD ─── */
.note-card {
    background: linear-gradient(135deg, var(--note-a), var(--note-b));
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-3);
    border-radius: 4px;
    padding: 14px 18px;
    font-size: 0.8rem;
    color: var(--muted);
    letter-spacing: 0.03em;
    box-shadow: -3px 0 14px var(--glow-cyan);
}

/* ─── RESULTS HEADER ─── */
.results-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 18px 24px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 4px;
    background: linear-gradient(135deg, var(--results-a) 0%, var(--results-b) 100%);
    box-shadow: -4px 0 24px var(--glow), 0 12px 36px rgba(0,0,0,0.3);
    margin-bottom: 18px;
    flex-wrap: wrap;
    position: relative;
    overflow: hidden;
}
.results-header::before {
    content: "";
    position: absolute; inset: 0;
    background: repeating-linear-gradient(90deg, transparent 0 43px, var(--grid) 43px 44px);
    pointer-events: none;
}
.results-icon { font-size: 1.5rem; position: relative; z-index: 1; }
.results-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.25rem;
    letter-spacing: 0.1em;
    color: var(--heading);
    font-weight: 800;
    position: relative; z-index: 1;
}
.results-meta {
    font-size: 0.6rem;
    color: var(--muted);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
    position: relative; z-index: 1;
}
.results-badge {
    margin-left: auto;
    font-size: 0.54rem;
    letter-spacing: 0.26em;
    text-transform: uppercase;
    color: var(--accent-3);
    background: var(--badge-bg);
    border: 1px solid var(--badge-border);
    padding: 6px 12px;
    border-radius: 2px;
    font-family: 'Orbitron', sans-serif;
    box-shadow: 0 0 14px var(--glow-cyan);
    position: relative; z-index: 1;
}

/* ─── DRIVER CARD ─── */
.driver-card {
    background: linear-gradient(160deg, var(--driver-a), var(--driver-b));
    border: 1px solid var(--border);
    border-top: none;
    border-radius: 4px;
    padding: 18px;
    margin-bottom: 10px;
    position: relative;
    overflow: hidden;
}
.driver-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--accent, #e10600);
    box-shadow: 0 0 20px var(--accent, #e10600), 0 0 44px var(--glow);
}
.driver-card-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px; }
.driver-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.6rem;
    letter-spacing: 0.08em;
    color: var(--accent, #e10600);
    font-weight: 900;
    text-shadow: 0 0 22px var(--glow);
}
.driver-badge {
    font-size: 0.58rem;
    color: var(--accent-2);
    letter-spacing: 0.24em;
    text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
}
.driver-time {
    font-family: 'Orbitron', monospace;
    font-size: 1.1rem;
    color: var(--heading);
    margin-bottom: 14px;
    letter-spacing: 0.07em;
}
.driver-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 10px; }
.driver-chip {
    background: var(--chip-bg);
    border: 1px solid var(--border-soft);
    border-radius: 3px;
    padding: 8px 6px;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.driver-chip::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: var(--badge-border);
}
.driver-chip-label {
    font-size: 0.55rem;
    color: var(--accent-3);
    letter-spacing: 0.22em;
    text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
}
.driver-chip-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.84rem;
    color: var(--heading);
    font-weight: 500;
}
.driver-meta {
    font-size: 0.6rem;
    color: var(--muted);
    letter-spacing: 0.16em;
    font-family: 'Orbitron', sans-serif;
    text-transform: uppercase;
}

/* ─── ANIMATIONS ─── */
.fade-in  { animation: fadeUp 0.6s ease both; }
.delay-1  { animation-delay: 0.06s; }
.delay-2  { animation-delay: 0.12s; }
.delay-3  { animation-delay: 0.18s; }
.delay-4  { animation-delay: 0.24s; }
.delay-5  { animation-delay: 0.30s; }
.delay-6  { animation-delay: 0.36s; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 8px  var(--glow-cyan); }
    50%       { box-shadow: 0 0 22px var(--glow-cyan), 0 0 44px var(--glow-cyan); }
}

/* ─── RESPONSIVE ─── */
@media (max-width: 900px) {
    .hero { margin: -1rem -1rem 1.4rem; padding: 18px 22px; }
    .hero-title { font-size: 1.4rem; }
    .hero-tag, .results-badge { margin-left: 0; }
    .driver-grid { grid-template-columns: 1fr 1fr; }
    .ctrl-panel { padding: 14px 16px 12px; }
}
</style>
"""
    return root + body
