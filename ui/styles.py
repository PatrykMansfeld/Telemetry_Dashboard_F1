CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@300;400;500&display=swap');

:root {
    --bg-0: #03040b;
    --bg-1: #060810;
    --bg-2: #090d18;
    --panel: #080b14;
    --panel-2: #0b0f1c;
    --border: #1a2840;
    --border-soft: #101828;
    --text: #b8cde0;
    --muted: #4e6070;
    --accent: #e10600;
    --accent-2: #c8ff3d;
    --accent-3: #00d4ff;
    --accent-4: #ff6b00;
    --glow: rgba(225,6,0,0.45);
    --glow-cyan: rgba(0,212,255,0.35);
    --glow-lime: rgba(200,255,61,0.3);
}

/* ─── BG: carbon fibre weave + aurora glows ─── */
.stApp {
    background-color: var(--bg-0) !important;
    background-image:
        repeating-linear-gradient(45deg,  rgba(255,255,255,0.016) 0 1px, transparent 1px 16px),
        repeating-linear-gradient(-45deg, rgba(255,255,255,0.016) 0 1px, transparent 1px 16px),
        radial-gradient(ellipse 800px 500px at -5%  -8%,  rgba(225,6,0,0.22),    transparent 55%),
        radial-gradient(ellipse 700px 450px at 108%  4%,  rgba(0,212,255,0.16),  transparent 55%),
        radial-gradient(ellipse 600px 400px at  50% 105%, rgba(200,255,61,0.06), transparent 60%);
    background-attachment: fixed;
}

/* ─── SIDEBAR ─── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #06080f 0%, #03040b 100%) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 6px 0 40px rgba(0,0,0,0.6) !important;
}

/* ─── TYPOGRAPHY ─── */
html, body, [class*="css"] {
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
h1, h2, h3, h4, h5 {
    color: #ffffff !important;
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
::-webkit-scrollbar-thumb { background: #1a2840; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-3); }

/* ─── INPUTS ─── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea {
    background-color: rgba(8,11,20,0.95) !important;
    border: 1px solid var(--border) !important;
    color: #ffffff !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent-3) !important;
    box-shadow: 0 0 0 2px rgba(0,212,255,0.2), 0 0 12px rgba(0,212,255,0.15) !important;
    outline: none !important;
}
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div > div {
    background-color: rgba(8,11,20,0.95) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
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
    color: #ffffff !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 18px var(--glow), inset 0 0 12px rgba(225,6,0,0.08) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #9a0400 0%, #e10600 55%, #ff4422 100%) !important;
    color: #ffffff !important;
    border-color: #e10600 !important;
    box-shadow: 0 0 22px rgba(225,6,0,0.5), 0 6px 24px rgba(0,0,0,0.5) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 40px rgba(225,6,0,0.7), 0 8px 30px rgba(0,0,0,0.6) !important;
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
    color: #ffffff !important;
    background: rgba(225,6,0,0.06) !important;
    border-bottom-color: rgba(225,6,0,0.4) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: rgba(225,6,0,0.07) !important;
    text-shadow: 0 0 12px var(--glow) !important;
}

/* ─── METRIC CARDS ─── */
[data-testid="stMetric"] {
    background: linear-gradient(160deg, rgba(10,15,28,0.97), rgba(5,8,16,0.97)) !important;
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
    border-right: 1px solid rgba(0,212,255,0.18) !important;
    border-bottom: 1px solid rgba(0,212,255,0.18) !important;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
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
    background-color: rgba(6,9,16,0.95) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
}
[data-testid="stExpander"] summary {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    letter-spacing: 0.04em !important;
}

/* ─── MISC ─── */
[data-testid="stSpinner"] { color: var(--accent-3) !important; }
hr { border-color: var(--border) !important; margin: 16px 0 !important; }
[data-testid="stSidebar"] label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
}

/* ─── PLOTLY MODEBAR ─── */
.js-plotly-plot .plotly .modebar { background: transparent !important; }
.js-plotly-plot .plotly .modebar-btn path { fill: var(--muted) !important; }
.js-plotly-plot .plotly .modebar-btn:hover path { fill: var(--accent-3) !important; }


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   CUSTOM COMPONENTS
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */

/* ─── SIDEBAR SECTION ─── */
.sb-section {
    color: var(--accent-3);
    font-size: 0.56rem;
    font-weight: 700;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    padding: 7px 0 9px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 10px;
    font-family: 'Orbitron', sans-serif;
    text-shadow: 0 0 10px var(--glow-cyan);
}

/* ─── SIDEBAR BRAND ─── */
.sb-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 4px 14px;
    margin-bottom: 14px;
    position: relative;
}
.sb-brand::after {
    content: "";
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, var(--accent), var(--accent-3), transparent 80%);
}
.sb-brand-icon { font-size: 1.4rem; filter: drop-shadow(0 0 10px var(--glow)); }
.sb-brand-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1rem;
    letter-spacing: 0.16em;
    color: #ffffff;
    font-weight: 800;
    text-shadow: 0 0 16px var(--glow);
}
.sb-brand-sub {
    font-size: 0.54rem;
    color: var(--muted);
    letter-spacing: 0.24em;
    text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
}

/* ─── SECTION SUBHEADER ─── */
.f1-subheader {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    color: #ffffff;
    padding: 10px 0 10px 14px;
    border-left: 3px solid var(--accent-3);
    margin-bottom: 14px;
    text-transform: uppercase;
    position: relative;
    text-shadow: 0 0 12px rgba(0,212,255,0.3);
}
.f1-subheader::after {
    content: "";
    position: absolute;
    left: 14px; right: 0; bottom: 0;
    height: 1px;
    background: linear-gradient(90deg, rgba(0,212,255,0.25), transparent);
}

/* ─── HERO BANNER ─── */
.hero {
    position: relative;
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 26px 32px;
    margin: -1rem -1rem 2rem;
    background: linear-gradient(135deg, rgba(8,12,22,0.99) 0%, rgba(4,6,14,0.99) 100%);
    overflow: hidden;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
}
.hero::before {
    content: "";
    position: absolute; inset: 0;
    background:
        repeating-linear-gradient(90deg, rgba(255,255,255,0.018) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(0deg,  rgba(255,255,255,0.018) 0 1px, transparent 1px 44px);
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
    box-shadow: 2px 0 24px var(--glow), 2px 0 40px rgba(0,212,255,0.25);
}
.hero-icon {
    font-size: 2.6rem;
    line-height: 1;
    filter: drop-shadow(0 0 18px var(--glow)) drop-shadow(0 0 36px rgba(225,6,0,0.25));
}
.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.9rem;
    letter-spacing: 0.12em;
    color: #ffffff;
    font-weight: 900;
    text-shadow: 0 0 30px rgba(225,6,0,0.35), 0 2px 0 rgba(0,0,0,0.9);
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
    border: 1px solid rgba(200,255,61,0.4);
    padding: 7px 12px;
    border-radius: 2px;
    background: rgba(200,255,61,0.07);
    font-family: 'Orbitron', sans-serif;
    box-shadow: 0 0 14px rgba(200,255,61,0.12);
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
    color: #ffffff;
    font-weight: 900;
    text-shadow: 0 0 50px rgba(225,6,0,0.25);
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
    background: linear-gradient(160deg, rgba(10,15,26,0.98), rgba(5,8,16,0.98));
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
    border-right: 1px solid rgba(255,255,255,0.07);
    border-bottom: 1px solid rgba(255,255,255,0.07);
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 14px 36px rgba(0,0,0,0.55), 0 0 28px rgba(225,6,0,0.18);
}
.feature-icon { font-size: 1.5rem; margin-bottom: 10px; }
.feature-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.74rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.12em;
    margin-bottom: 8px;
    text-transform: uppercase;
}
.feature-desc { font-size: 0.76rem; color: var(--muted); line-height: 1.55; }

/* ─── NOTE CARD ─── */
.note-card {
    background: linear-gradient(135deg, rgba(8,12,22,0.98), rgba(4,7,14,0.98));
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-3);
    border-radius: 4px;
    padding: 14px 18px;
    font-size: 0.8rem;
    color: var(--muted);
    letter-spacing: 0.03em;
    box-shadow: -3px 0 14px rgba(0,212,255,0.1);
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
    background: linear-gradient(135deg, rgba(10,15,26,0.99) 0%, rgba(4,6,14,0.99) 100%);
    box-shadow: -4px 0 24px rgba(225,6,0,0.2), 0 12px 36px rgba(0,0,0,0.5);
    margin-bottom: 18px;
    flex-wrap: wrap;
    position: relative;
    overflow: hidden;
}
.results-header::before {
    content: "";
    position: absolute; inset: 0;
    background: repeating-linear-gradient(90deg, transparent 0 43px, rgba(255,255,255,0.012) 43px 44px);
    pointer-events: none;
}
.results-icon { font-size: 1.5rem; position: relative; z-index: 1; }
.results-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.25rem;
    letter-spacing: 0.1em;
    color: #ffffff;
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
    background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.3);
    padding: 6px 12px;
    border-radius: 2px;
    font-family: 'Orbitron', sans-serif;
    box-shadow: 0 0 14px rgba(0,212,255,0.12);
    position: relative; z-index: 1;
}

/* ─── DRIVER CARD ─── */
.driver-card {
    background: linear-gradient(160deg, rgba(10,15,26,0.98), rgba(5,8,16,0.98));
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
    box-shadow: 0 0 20px var(--accent, #e10600), 0 0 44px rgba(225,6,0,0.25);
}
.driver-card-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 8px; }
.driver-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 1.6rem;
    letter-spacing: 0.08em;
    color: var(--accent, #e10600);
    font-weight: 900;
    text-shadow: 0 0 22px var(--accent, rgba(225,6,0,0.5));
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
    color: #ffffff;
    margin-bottom: 14px;
    letter-spacing: 0.07em;
    text-shadow: 0 0 12px rgba(255,255,255,0.15);
}
.driver-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 10px; }
.driver-chip {
    background: rgba(4,6,14,0.95);
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
    background: rgba(0,212,255,0.22);
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
    color: #ffffff;
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
    50%       { box-shadow: 0 0 22px var(--glow-cyan), 0 0 44px rgba(0,212,255,0.18); }
}

/* ─── RESPONSIVE ─── */
@media (max-width: 900px) {
    .hero { margin: -1rem -1rem 1.4rem; padding: 18px 22px; }
    .hero-title { font-size: 1.4rem; }
    .hero-tag, .results-badge { margin-left: 0; }
    .driver-grid { grid-template-columns: 1fr 1fr; }
}
</style>
"""
