"""
F1 Telemetria — frontend Streamlit.
Uruchom: streamlit run app.py
"""

from __future__ import annotations

import traceback
from dataclasses import replace
from typing import Optional

import streamlit as st

# ── Konfiguracja strony (MUSI być pierwsza) ─────────────────────────────────
st.set_page_config(
    page_title="F1 Telemetria",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**F1 Telemetria** — analiza stylu jazdy kierowców F1\nPowered by FastF1",
    },
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
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
/* Primary button — "URUCHOM ANALIZĘ" */
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
/* grid overlay */
.hero::before {
    content: "";
    position: absolute; inset: 0;
    background:
        repeating-linear-gradient(90deg, rgba(255,255,255,0.018) 0 1px, transparent 1px 44px),
        repeating-linear-gradient(0deg,  rgba(255,255,255,0.018) 0 1px, transparent 1px 44px);
    pointer-events: none;
}
/* tri-colour bottom line */
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
/* corner decoration */
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
""", unsafe_allow_html=True)


# ── Stałe ─────────────────────────────────────────────────────────────────────
SESSIONS = ["Q", "R", "FP1", "FP2", "FP3", "S", "SS"]
SESSION_LABELS = {
    "Q":   "Kwalifikacje",
    "R":   "Wyścig",
    "FP1": "Trening 1",
    "FP2": "Trening 2",
    "FP3": "Trening 3",
    "S":   "Sprint",
    "SS":  "Sprint Shootout",
}

KNOWN_DRIVERS = [
    "VER", "PER", "HAM", "RUS", "LEC", "SAI", "NOR", "PIA",
    "ALO", "STR", "OCO", "GAS", "ALB", "SAR", "BOT", "ZHO",
    "HUL", "MAG", "TSU", "LAW", "RIC", "BEA", "ANT", "DEV",
]


# ── Importy modułów projektu ───────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _import_modules():
    """Lazy import modułów projektu (FastF1 wolno się ładuje)."""
    from f1tele.data_loader import (
        load_session, load_drivers_data,
        get_available_sessions,
        get_session_drivers_list,
        get_race_pace_data,
    )
    from f1tele.corner_analysis import run_corner_analysis
    from f1tele.sector_analysis import compute_mini_sectors, compute_sector_stats
    from f1tele.driver_style import (
        compute_style_fingerprint, normalize_fingerprints,
        METRIC_LABELS, METRIC_FIELDS,
    )
    from f1tele.plots_interactive import (
        plot_telemetry_interactive,
        plot_corners_interactive,
        plot_mini_sector_dominance_interactive,
        plot_sector_heatmap_interactive,
        plot_radar_interactive,
        plot_style_bars_interactive,
        plot_driver_dominance_map_interactive,
        plot_speed_heatmap_track_interactive,
        plot_gear_map_interactive,
        plot_race_pace_interactive,
        plot_track_animation_interactive,
    )
    return {
        "load_session":                            load_session,
        "load_drivers_data":                       load_drivers_data,
        "get_available_sessions":                  get_available_sessions,
        "get_session_drivers_list":                get_session_drivers_list,
        "get_race_pace_data":                      get_race_pace_data,
        "run_corner_analysis":                     run_corner_analysis,
        "compute_mini_sectors":                    compute_mini_sectors,
        "compute_sector_stats":                    compute_sector_stats,
        "compute_style_fingerprint":               compute_style_fingerprint,
        "normalize_fingerprints":                  normalize_fingerprints,
        "METRIC_LABELS":                           METRIC_LABELS,
        "METRIC_FIELDS":                           METRIC_FIELDS,
        "plot_telemetry_interactive":              plot_telemetry_interactive,
        "plot_corners_interactive":                plot_corners_interactive,
        "plot_mini_sector_dominance_interactive":  plot_mini_sector_dominance_interactive,
        "plot_sector_heatmap_interactive":         plot_sector_heatmap_interactive,
        "plot_radar_interactive":                  plot_radar_interactive,
        "plot_style_bars_interactive":             plot_style_bars_interactive,
        "plot_driver_dominance_map_interactive":   plot_driver_dominance_map_interactive,
        "plot_speed_heatmap_track_interactive":    plot_speed_heatmap_track_interactive,
        "plot_gear_map_interactive":               plot_gear_map_interactive,
        "plot_race_pace_interactive":              plot_race_pace_interactive,
        "plot_track_animation_interactive":        plot_track_animation_interactive,
    }


# ── Nagłówek ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero fade-in">
    <div class="hero-stripe"></div>
    <div class="hero-icon">🏎</div>
    <div class="hero-text">
        <div class="hero-title">F1 Telemetria</div>
        <div class="hero-sub">Analiza stylu jazdy kierowców &nbsp;·&nbsp; FastF1</div>
    </div>
    <div class="hero-tag">Live analytics</div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-brand fade-in">
        <div class="sb-brand-icon">🏎</div>
        <div>
            <div class="sb-brand-title">F1 Telemetria</div>
            <div class="sb-brand-sub">Analiza danych</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── SESJA A ───────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-section">⚙️ &nbsp;Sesja A</div>', unsafe_allow_html=True)
    year = st.number_input("Rok sezonu", min_value=2018, max_value=2026, value=2024, step=1)
    round_input = st.text_input(
        "Runda",
        value="5",
        placeholder="nr lub nazwa GP",
        help="Wpisz numer rundy (np. 5) lub nazwę GP (np. Monaco, Bahrain)",
    )
    session_type = st.selectbox(
        "Typ sesji",
        SESSIONS,
        index=0,
        format_func=lambda s: SESSION_LABELS.get(s, s),
        help="Wybierz typ sesji do analizy",
    )

    # ── KIEROWCY — DYNAMICZNA LISTA ───────────────────────────────────────────
    st.markdown('<div class="sb-section" style="margin-top:16px">👤 &nbsp;Kierowcy</div>',
                unsafe_allow_html=True)

    load_drv_btn = st.button("🔄 Załaduj kierowców z sesji", use_container_width=True)
    if load_drv_btn:
        with st.spinner("Pobieranie listy kierowców..."):
            try:
                mods = _import_modules()
                try:
                    rv = int(round_input.strip())
                except ValueError:
                    rv = round_input.strip()
                drv_list = mods["get_session_drivers_list"](year, rv, session_type)
                st.session_state["available_drivers"] = [d["abbr"] for d in drv_list]
                st.session_state["driver_details"]    = {d["abbr"]: d for d in drv_list}
                st.success(f"Znaleziono {len(drv_list)} kierowców.")
            except Exception as e:
                st.error(f"Błąd ładowania kierowców: {e}")

    available_drivers = st.session_state.get("available_drivers", KNOWN_DRIVERS)

    # Wyświetl skrócone info o kierowcach, gdy lista pochodzi z sesji
    if "driver_details" in st.session_state:
        details = st.session_state["driver_details"]
        if details:
            sample = next(iter(details.values()))
            if sample.get("full_name"):
                with st.expander("ℹ️ Kierowcy w sesji", expanded=False):
                    for abbr, info in details.items():
                        st.caption(f"**{abbr}** — {info['full_name']}  ·  {info['team']}")

    drivers_multiselect = st.multiselect(
        "Wybierz kierowców",
        options=available_drivers,
        default=[d for d in ["VER", "NOR", "LEC"] if d in available_drivers],
        max_selections=6,
        help="Wybierz 2–6 kierowców do porównania",
    )
    custom_drivers = st.text_input(
        "Lub wpisz kody ręcznie",
        placeholder="VER,HAM,NOR — nadpisuje wybór",
        help="Oddziel przecinkami. Nadpisuje wybór powyżej.",
    )

    # ── OPCJE ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-section" style="margin-top:16px">🔧 &nbsp;Opcje</div>',
                unsafe_allow_html=True)
    mini_sects = st.slider("Mini-sektory", 10, 50, 25, step=5)
    with st.expander("Moduły analizy", expanded=False):
        mod_telemetry = st.checkbox("📈 Telemetria",  value=True)
        mod_corners   = st.checkbox("🔄 Zakręty",     value=True)
        mod_sectors   = st.checkbox("🏁 Sektory",     value=True)
        mod_style     = st.checkbox("🎯 Styl jazdy",  value=True)
        mod_track     = st.checkbox("🗺️ Mapa toru",  value=True)
        mod_race_pace = st.checkbox("🏎 Race pace",   value=True)

    st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
    run_btn = st.button("🚀 URUCHOM ANALIZĘ", use_container_width=True, type="primary")

    # ── HARMONOGRAM ───────────────────────────────────────────────────────────
    st.markdown('<div class="sb-section" style="margin-top:20px">📅 &nbsp;Harmonogram</div>',
                unsafe_allow_html=True)
    if st.button("Pokaż sezon", use_container_width=True):
        st.session_state["show_schedule"] = True
        st.session_state["schedule_year"] = year

    # ── SESJA B — CROSS-SESSION ───────────────────────────────────────────────
    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("🔀 Porównanie sesji (Cross-session)", expanded=False):
        st.caption("Załaduj drugą sesję, aby porównać telemetrię i styl jazdy między GP / latami.")
        year_b = st.number_input("Rok B", min_value=2018, max_value=2026,
                                 value=2023, step=1, key="year_b")
        round_b = st.text_input("Runda B", value="5",
                                 placeholder="nr lub nazwa GP", key="round_b")
        session_b_type = st.selectbox("Typ sesji B", SESSIONS, index=0, key="sess_b")

        # Dynamiczna lista dla sesji B
        load_drv_b_btn = st.button("🔄 Załaduj kierowców sesji B", use_container_width=True,
                                   key="load_b_drv")
        if load_drv_b_btn:
            with st.spinner("Pobieranie kierowców sesji B..."):
                try:
                    mods = _import_modules()
                    try:
                        rv_b = int(round_b.strip())
                    except ValueError:
                        rv_b = round_b.strip()
                    drv_list_b = mods["get_session_drivers_list"](year_b, rv_b, session_b_type)
                    st.session_state["available_drivers_b"] = [d["abbr"] for d in drv_list_b]
                    st.success(f"Znaleziono {len(drv_list_b)} kierowców.")
                except Exception as e:
                    st.error(f"Błąd: {e}")

        available_b = st.session_state.get("available_drivers_b", KNOWN_DRIVERS)
        drivers_b = st.multiselect(
            "Kierowcy sesji B",
            options=available_b,
            default=[d for d in ["VER", "NOR"] if d in available_b],
            max_selections=4,
            key="drv_b",
        )

        run_b_btn = st.button("➕ Załaduj sesję B", use_container_width=True, key="run_b")


# ── Ustal listę kierowców A ────────────────────────────────────────────────────
if custom_drivers.strip():
    final_drivers = [d.strip().upper() for d in custom_drivers.split(",") if d.strip()]
else:
    final_drivers = list(drivers_multiselect)


# ── Harmonogram (opcjonalny) ───────────────────────────────────────────────────
if st.session_state.get("show_schedule"):
    sch_year = st.session_state.get("schedule_year", year)
    with st.spinner(f"Pobieranie harmonogramu {sch_year}..."):
        try:
            mods = _import_modules()
            df = mods["get_available_sessions"](sch_year)
            if not df.empty:
                import pandas as pd
                st.subheader(f"📅 Sezon F1 {sch_year}")
                st.dataframe(
                    df.rename(columns={
                        "RoundNumber": "Runda",
                        "EventName":   "GP",
                        "Location":    "Miasto",
                        "Country":     "Kraj",
                        "EventDate":   "Data",
                    }),
                    use_container_width=True, hide_index=True,
                )
        except Exception as e:
            st.error(f"Błąd pobierania harmonogramu: {e}")
    st.session_state["show_schedule"] = False


# ═══════════════════════════════════════════════════════════
# ŁADOWANIE SESJI B (Cross-session)
# ═══════════════════════════════════════════════════════════
if st.session_state.get("run_b_btn_fired") or (
    "run_b" in st.session_state and st.session_state.get("run_b")
):
    st.session_state["run_b_btn_fired"] = False

if run_b_btn:
    if not drivers_b:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę dla sesji B!")
    else:
        try:
            rv_b = int(round_b.strip())
        except ValueError:
            rv_b = round_b.strip()

        progress_b = st.progress(0, text="Ładowanie sesji B...")
        status_b = st.empty()
        try:
            mods = _import_modules()
            status_b.info(f"📡 Ładowanie sesji B: **{year_b} GP#{rv_b} [{session_b_type}]**")
            session_b_data = mods["load_session"](year_b, rv_b, session_b_type, verbose=False)
            progress_b.progress(40, text="Sesja B załadowana...")

            status_b.info(f"🔄 Pobieranie telemetrii B: **{', '.join(drivers_b)}**")
            drivers_b_data = mods["load_drivers_data"](session_b_data, drivers_b)
            progress_b.progress(100, text="Sesja B gotowa!")

            if drivers_b_data:
                st.session_state["session_b"] = {
                    "session_data": session_b_data,
                    "drivers_data": drivers_b_data,
                }
                status_b.success(
                    f"✅ Sesja B załadowana: {session_b_data.event_name} {session_b_data.year}"
                )
            else:
                status_b.error("❌ Brak danych dla wybranych kierowców sesji B.")
        except Exception:
            progress_b.empty()
            status_b.empty()
            st.error("❌ Błąd ładowania sesji B:")
            st.code(traceback.format_exc(), language="python")


# ═══════════════════════════════════════════════════════════
# GŁÓWNA ANALIZA (Sesja A)
# ═══════════════════════════════════════════════════════════
if run_btn:
    if not final_drivers:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę!")
        st.stop()

    try:
        round_val: int | str = int(round_input.strip())
    except ValueError:
        round_val = round_input.strip()

    st.session_state["params"] = {
        "year": year, "round": round_val, "session": session_type,
        "drivers": final_drivers, "mini_sects": mini_sects,
        "mods": {
            "telemetry":  mod_telemetry,
            "corners":    mod_corners,
            "sectors":    mod_sectors,
            "style":      mod_style,
            "track":      mod_track,
            "race_pace":  mod_race_pace,
        },
    }
    st.session_state["results"] = None
    for key in list(st.session_state.keys()):
        if key.startswith("plot_"):
            del st.session_state[key]

    progress = st.progress(0, text="Ładowanie sesji...")
    status   = st.empty()

    try:
        mods = _import_modules()

        status.info(f"📡 Ładowanie sesji: **{year} GP#{round_val} [{session_type}]**")
        session_data = mods["load_session"](year, round_val, session_type, verbose=False)
        progress.progress(15, text="Sesja załadowana...")

        status.info(f"🔄 Pobieranie telemetrii dla: **{', '.join(final_drivers)}**")
        drivers_data = mods["load_drivers_data"](session_data, final_drivers)
        progress.progress(35, text="Telemetria pobrana...")

        if not drivers_data:
            status.empty(); progress.empty()
            st.error("❌ Nie udało się pobrać danych dla żadnego kierowcy.")
            st.stop()

        mods_cfg = st.session_state["params"]["mods"]
        figs: dict[str, object] = {}

        if mods_cfg["telemetry"]:
            status.info("📈 Generowanie wykresu telemetrii...")
            figs["telemetry"] = mods["plot_telemetry_interactive"](drivers_data, session_data)
            progress.progress(50, text="Telemetria gotowa...")

        corner_analysis = None
        if mods_cfg["corners"]:
            status.info("🔄 Analiza zakrętów...")
            corner_analysis = mods["run_corner_analysis"](drivers_data)
            figs["corners"] = mods["plot_corners_interactive"](
                drivers_data, corner_analysis, session_data
            )
            progress.progress(62, text="Zakręty gotowe...")

        mini_sector_data = None
        stats_df = None
        if mods_cfg["sectors"]:
            status.info("🏁 Analiza sektorów...")
            mini_sector_data = mods["compute_mini_sectors"](drivers_data, mini_sects)
            stats_df = mods["compute_sector_stats"](drivers_data)
            figs["mini_sectors"]    = mods["plot_mini_sector_dominance_interactive"](
                drivers_data, mini_sector_data, session_data
            )
            figs["sector_heatmap"] = mods["plot_sector_heatmap_interactive"](
                stats_df, drivers_data, session_data
            )
            progress.progress(74, text="Sektory gotowe...")

        fingerprints = []
        if mods_cfg["style"]:
            status.info("🎯 Obliczanie odcisku palca stylu jazdy...")
            raw_fps = [
                mods["compute_style_fingerprint"](d, corner_analysis)
                for d in drivers_data.values()
            ]
            fingerprints = mods["normalize_fingerprints"](raw_fps)
            figs["radar"]      = mods["plot_radar_interactive"](fingerprints, session_data)
            figs["style_bars"] = mods["plot_style_bars_interactive"](fingerprints, session_data)
            progress.progress(85, text="Styl jazdy gotowy...")

        if mods_cfg["track"]:
            status.info("🗺️ Generowanie map toru...")
            figs["track_dominance"] = mods["plot_driver_dominance_map_interactive"](
                drivers_data, session_data
            )
            for d in drivers_data.values():
                figs[f"speed_map_{d.driver}"] = mods["plot_speed_heatmap_track_interactive"](
                    d, session_data
                )
                figs[f"gear_map_{d.driver}"] = mods["plot_gear_map_interactive"](
                    d, session_data
                )
            progress.progress(92, text="Mapy toru gotowe...")

        race_pace_df = None
        if mods_cfg["race_pace"]:
            status.info("🏎 Pobieranie danych race pace...")
            try:
                import pandas as _pd
                race_pace_df = mods["get_race_pace_data"](session_data, list(drivers_data.keys()))
                if not race_pace_df.empty:
                    figs["race_pace"] = mods["plot_race_pace_interactive"](
                        race_pace_df, drivers_data, session_data
                    )
            except Exception as rpe:
                st.warning(f"Race pace: {rpe}")

        progress.progress(100, text="Analiza zakończona!")

        st.session_state["results"] = {
            "session_data":   session_data,
            "drivers_data":   drivers_data,
            "corner_analysis": corner_analysis,
            "stats_df":       stats_df,
            "fingerprints":   fingerprints,
            "race_pace_df":   race_pace_df,
            "figs":           figs,
            "METRIC_LABELS":  mods["METRIC_LABELS"],
            "METRIC_FIELDS":  mods["METRIC_FIELDS"],
        }

        n_figs = len([v for v in figs.values() if v is not None])
        status.success(f"✅ Analiza zakończona! Wygenerowano {n_figs} wykresów.")

    except Exception:
        progress.empty(); status.empty()
        st.error("❌ Błąd podczas analizy:")
        st.code(traceback.format_exc(), language="python")
        st.stop()


# ═══════════════════════════════════════════════════════════
# WYŚWIETLANIE WYNIKÓW
# ═══════════════════════════════════════════════════════════
results = st.session_state.get("results")

if results is None:
    # ── Strona powitalna ──────────────────────────────────────────────────────
    st.markdown("""
    <div class="welcome fade-in">
        <div class="welcome-title">Witaj w F1 Telemetria</div>
        <div class="welcome-sub">
            Wybierz sesję i kierowców w panelu po lewej, następnie kliknij
            <span class="accent">URUCHOM ANALIZĘ</span>.
        </div>
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("📈", "Telemetria",          "Prędkość · Delta · Gaz · Hamulec · Biegi · RPM",        "#e10600"),
        ("🔄", "Zakręty",             "Punkt hamowania · Prędkość apeksu · Wyjście z gazu",      "#ff7a00"),
        ("🏁", "Sektory",             "Mini-sektory · Dominacja · Mapa ciepła S1/S2/S3",         "#c8ff3d"),
        ("🎯", "Styl jazdy",          "Radar 10 metryk · Porównanie słupkowe",                   "#00d1ff"),
        ("🗺️", "Mapa toru",          "Dominacja · Gradient prędkości · Biegi · Animacja",        "#3bd971"),
        ("🏎", "Race Pace",           "Czas okrążenia · Trend · Składy opon · Sfinty",           "#f9c74f"),
        ("📊", "Podsumowanie",        "Tabela wyników · Profile kierowców · Czasy sektorów",      "#a78bfa"),
        ("🔀", "Cross-session",       "Porównanie sesji A vs B · Telemetria między GP / latami",  "#fb7185"),
    ]
    cols = st.columns(4)
    for i, (icon, title, desc, accent) in enumerate(features):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="feature-card" style="--accent:{accent}">
                <div class="feature-icon">{icon}</div>
                <div class="feature-title">{title}</div>
                <div class="feature-desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("""
    <div class="note-card fade-in delay-6">
        💡 Wszystkie wykresy są interaktywne — zoom, hover, pan.
        Dane pobierane przez FastF1 i cache'owane lokalnie.<br>
        Kliknij <b>🔄 Załaduj kierowców z sesji</b>, aby pobrać aktualną listę kierowców dla wybranego GP.
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Dane z wyników ─────────────────────────────────────────────────────────────
import pandas as pd

session_data    = results["session_data"]
drivers_data    = results["drivers_data"]
corner_analysis = results["corner_analysis"]
stats_df        = results["stats_df"]
fingerprints    = results["fingerprints"]
race_pace_df    = results["race_pace_df"]
figs            = results["figs"]
METRIC_LABELS   = results["METRIC_LABELS"]
METRIC_FIELDS   = results["METRIC_FIELDS"]

sorted_drivers  = sorted(drivers_data.values(), key=lambda d: d.lap_time)


# ── Nagłówek wyników ───────────────────────────────────────────────────────────
st.markdown(f"""
<div class="results-header fade-in">
    <div class="results-icon">🏁</div>
    <div>
        <div class="results-title">{session_data.event_name} {session_data.year}</div>
        <div class="results-meta">
            {session_data.session_type} &nbsp;·&nbsp;
            {session_data.circuit_name} &nbsp;·&nbsp;
            {session_data.country}
        </div>
    </div>
    <div class="results-badge">Session</div>
</div>
""", unsafe_allow_html=True)

# ── Szybkie metryki ────────────────────────────────────────────────────────────
ref_time = sorted_drivers[0].lap_time
cols = st.columns(min(len(sorted_drivers), 4))
for col, d in zip(cols, sorted_drivers[:4]):
    delta = d.lap_time - ref_time
    delta_str = "POLE 🥇" if delta == 0 else f"+{delta:.3f}s"
    col.metric(
        label=d.driver,
        value=d.lap_time_str,
        delta=delta_str,
        delta_color="off" if delta == 0 else "inverse",
    )

st.divider()


# ── TABS ───────────────────────────────────────────────────────────────────────
session_b_loaded = "session_b" in st.session_state and st.session_state["session_b"]

tab_names = [
    "📊 Podsumowanie",
    "📈 Telemetria",
    "🔄 Zakręty",
    "🏁 Sektory",
    "🎯 Styl jazdy",
    "🗺️ Mapa toru",
    "🏎 Race Pace",
    "🔀 Cross-session",
    "📋 Info",
]
tabs = st.tabs(tab_names)


# ═══════════════════════════════════════════════════════════
# TAB 1 — PODSUMOWANIE
# ═══════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<div class="f1-subheader">Wyniki okrążeń</div>', unsafe_allow_html=True)

    lap_rows = []
    for i, d in enumerate(sorted_drivers):
        delta = d.lap_time - ref_time
        lap_rows.append({
            "#":         ["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1),
            "Kierowca":  d.driver,
            "Czas":      d.lap_time_str,
            "Delta":     "POLE" if delta == 0 else f"+{delta:.3f}s",
            "S1 [s]":    round(d.sector1, 3),
            "S2 [s]":    round(d.sector2, 3),
            "S3 [s]":    round(d.sector3, 3),
            "Okrążenie": d.lap_number,
            "Opona":     d.compound,
        })

    lap_df = pd.DataFrame(lap_rows)
    st.dataframe(lap_df, use_container_width=True, hide_index=True)

    st.markdown('<div class="f1-subheader">Profile kierowców</div>', unsafe_allow_html=True)
    driver_cols = st.columns(min(len(drivers_data), 3))
    for col, d in zip(driver_cols, sorted_drivers):
        with col:
            is_pole = d.lap_time == ref_time
            badge = "🥇 POLE" if is_pole else ""
            st.markdown(f"""
            <div class="driver-card" style="--accent:{d.color}">
                <div class="driver-card-header">
                    <div class="driver-title">{d.driver}</div>
                    <div class="driver-badge">{badge}</div>
                </div>
                <div class="driver-time">{d.lap_time_str}</div>
                <div class="driver-grid">
                    <div class="driver-chip">
                        <div class="driver-chip-label">S1</div>
                        <div class="driver-chip-value">{d.sector1:.3f}</div>
                    </div>
                    <div class="driver-chip">
                        <div class="driver-chip-label">S2</div>
                        <div class="driver-chip-value">{d.sector2:.3f}</div>
                    </div>
                    <div class="driver-chip">
                        <div class="driver-chip-label">S3</div>
                        <div class="driver-chip-value">{d.sector3:.3f}</div>
                    </div>
                </div>
                <div class="driver-meta">Okr. #{d.lap_number} &nbsp;·&nbsp; {d.compound}</div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# TAB 2 — TELEMETRIA
# ═══════════════════════════════════════════════════════════
with tabs[1]:
    fig = figs.get("telemetry")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Moduł Telemetria nie był uruchomiony lub brak danych.")


# ═══════════════════════════════════════════════════════════
# TAB 3 — ZAKRĘTY
# ═══════════════════════════════════════════════════════════
with tabs[2]:
    fig = figs.get("corners")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

        if corner_analysis and corner_analysis.corners:
            st.markdown(
                f'<div class="f1-subheader">Dane zakrętów ({len(corner_analysis.corners)} wykryto)</div>',
                unsafe_allow_html=True,
            )
            rows = []
            for corner in corner_analysis.corners:
                row = {"Zakręt": f"T{corner['id']}", "Dystans [m]": f"{corner['distance']:.0f}"}
                for drv in drivers_data:
                    ev_map = {e.corner_id: e for e in corner_analysis.driver_corners.get(drv, [])}
                    ev = ev_map.get(corner["id"])
                    row[f"{drv} – Apeks [km/h]"] = f"{ev.apex_speed:.1f}" if ev else "—"
                    row[f"{drv} – Ham. [m]"]     = f"{ev.braking_distance:.1f}" if ev else "—"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Moduł Zakręty nie był uruchomiony lub brak danych.")


# ═══════════════════════════════════════════════════════════
# TAB 4 — SEKTORY
# ═══════════════════════════════════════════════════════════
with tabs[3]:
    fig1 = figs.get("mini_sectors")
    fig2 = figs.get("sector_heatmap")

    if fig1 is not None:
        st.plotly_chart(fig1, use_container_width=True)
    if fig2 is not None:
        st.plotly_chart(fig2, use_container_width=True)

    if stats_df is not None and not stats_df.empty:
        st.markdown('<div class="f1-subheader">Statystyki sektorowe</div>', unsafe_allow_html=True)
        display_cols = {
            "Driver": "Kierowca",   "Sector": "Sektor",
            "Time_s": "Czas [s]",   "MaxSpeed": "Max V [km/h]",
            "AvgSpeed": "Śr. V [km/h]", "FullThrottle_pct": "Pełny gaz %",
            "Braking_pct": "Hamowanie %",
        }
        st.dataframe(
            stats_df[list(display_cols.keys())].rename(columns=display_cols)
                .sort_values(["Sektor", "Czas [s]"]).reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

    if fig1 is None and fig2 is None:
        st.info("Moduł Sektory nie był uruchomiony lub brak danych.")


# ═══════════════════════════════════════════════════════════
# TAB 5 — STYL JAZDY
# ═══════════════════════════════════════════════════════════
with tabs[4]:
    fig_radar = figs.get("radar")
    fig_bars  = figs.get("style_bars")

    if fig_radar is not None or fig_bars is not None:
        col_r, col_b = st.columns([1, 1])
        with col_r:
            if fig_radar is not None:
                st.markdown('<div class="f1-subheader">Radar stylu jazdy</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(fig_radar, use_container_width=True)
        with col_b:
            if fig_bars is not None:
                st.markdown('<div class="f1-subheader">Porównanie metryk</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(fig_bars, use_container_width=True)

    if fingerprints:
        st.markdown('<div class="f1-subheader">Metryki stylu jazdy (0 – 100)</div>',
                    unsafe_allow_html=True)
        metric_rows = []
        for label, field in zip(METRIC_LABELS, METRIC_FIELDS):
            row = {"Metryka": label.replace("\n", " ")}
            vals = [getattr(fp, field) for fp in fingerprints]
            best = max(vals)
            for fp, val in zip(fingerprints, vals):
                row[fp.driver] = f"{'★ ' if val == best else ''}{val:.1f}"
            metric_rows.append(row)
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)

    if fig_radar is None and not fingerprints:
        st.info("Moduł Styl jazdy nie był uruchomiony lub brak danych.")


# ═══════════════════════════════════════════════════════════
# TAB 6 — MAPA TORU + ANIMACJA
# ═══════════════════════════════════════════════════════════
with tabs[5]:
    fig_dom = figs.get("track_dominance")

    if fig_dom is not None:
        st.markdown('<div class="f1-subheader">Dominacja na torze</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_dom, use_container_width=True)
    elif st.session_state.get("params", {}).get("mods", {}).get("track"):
        st.warning("⚠️ Brak danych GPS — mapa dominacji niedostępna dla tej sesji.")

    for drv in drivers_data:
        fig_spd  = figs.get(f"speed_map_{drv}")
        fig_gear = figs.get(f"gear_map_{drv}")

        if fig_spd is not None or fig_gear is not None:
            with st.expander(f"🗺️ Mapy toru — {drv}", expanded=False):
                c1, c2 = st.columns(2)
                if fig_spd is not None:
                    c1.subheader(f"Prędkość — {drv}")
                    c1.plotly_chart(fig_spd, use_container_width=True)
                if fig_gear is not None:
                    c2.subheader(f"Biegi — {drv}")
                    c2.plotly_chart(fig_gear, use_container_width=True)

    # ── ANIMACJA TORU ─────────────────────────────────────────────────────────
    st.markdown('<div class="f1-subheader" style="margin-top:20px">Animacja okrążenia</div>',
                unsafe_allow_html=True)

    has_gps = any("X" in d.telemetry.columns for d in drivers_data.values())
    if not has_gps:
        st.warning("⚠️ Brak danych GPS — animacja niedostępna dla tej sesji.")
    else:
        anim_key = "anim_" + "_".join(sorted(drivers_data.keys()))
        if st.button("▶ Wygeneruj animację okrążenia", key="gen_anim"):
            with st.spinner("Generowanie animacji..."):
                try:
                    mods = _import_modules()
                    fig_generated = mods["plot_track_animation_interactive"](
                        drivers_data, session_data, n_frames=80
                    )
                    if fig_generated is not None:
                        st.session_state[anim_key] = fig_generated
                    else:
                        st.warning("⚠️ Nie można wygenerować animacji — brak danych GPS.")
                except Exception as _anim_err:
                    st.error(f"Błąd generowania animacji: {_anim_err}")

        fig_anim = st.session_state.get(anim_key)
        if fig_anim is not None:
            st.plotly_chart(fig_anim, use_container_width=True)
        else:
            st.caption("Kliknij przycisk powyżej, aby wygenerować animację.")

    if not any(
        k.startswith(("track_", "speed_map_", "gear_map_"))
        for k, v in figs.items() if v is not None
    ) and not has_gps:
        st.info("Moduł Mapa toru nie był uruchomiony lub brak danych GPS.")


# ═══════════════════════════════════════════════════════════
# TAB 7 — RACE PACE
# ═══════════════════════════════════════════════════════════
with tabs[6]:
    fig_rp = figs.get("race_pace")

    if fig_rp is not None:
        st.plotly_chart(fig_rp, use_container_width=True)

        if race_pace_df is not None and not race_pace_df.empty:
            st.markdown('<div class="f1-subheader">Statystyki tempa</div>',
                        unsafe_allow_html=True)
            pace_stats = (
                race_pace_df.groupby("Driver")["LapTime_s"]
                .agg(["mean", "median", "std", "min", "count"])
                .rename(columns={
                    "mean":   "Śr. [s]",
                    "median": "Mediana [s]",
                    "std":    "Odch. std [s]",
                    "min":    "Najszybsze [s]",
                    "count":  "Okrążeń",
                })
                .round(3)
                .reset_index()
                .rename(columns={"Driver": "Kierowca"})
                .sort_values("Śr. [s]")
            )
            st.dataframe(pace_stats, use_container_width=True, hide_index=True)
    elif session_data.session_type != SESSION_LABELS["R"]:
        st.info(
            "ℹ️ Race Pace jest najbardziej miarodajny dla sesji wyścigowych. "
            f"Aktualna sesja: **{session_data.session_type}**. "
            "Dane są dostępne, ale mogą być ograniczone."
        )
        if race_pace_df is not None and not race_pace_df.empty:
            mods = _import_modules()
            fig_rp2 = mods["plot_race_pace_interactive"](race_pace_df, drivers_data, session_data)
            if fig_rp2 is not None:
                st.plotly_chart(fig_rp2, use_container_width=True)
        else:
            st.warning("Brak danych race pace dla tej sesji lub moduł nie był uruchomiony.")
    else:
        st.info("Moduł Race Pace nie był uruchomiony lub brak danych.")


# ═══════════════════════════════════════════════════════════
# TAB 8 — CROSS-SESSION
# ═══════════════════════════════════════════════════════════
with tabs[7]:
    session_b = st.session_state.get("session_b")

    if not session_b:
        st.markdown("""
        <div class="note-card">
            🔀 <b>Cross-session comparison</b><br><br>
            Aby porównać kierowców między dwiema sesjami (np. Monaco 2023 vs 2024):
            <ol style="margin-top:10px; color: var(--muted);">
                <li>Rozwiń panel <b>🔀 Porównanie sesji</b> w sidebarze po lewej</li>
                <li>Wybierz rok, rundę i typ sesji B</li>
                <li>Wybierz kierowców sesji B</li>
                <li>Kliknij <b>➕ Załaduj sesję B</b></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    else:
        session_b_data   = session_b["session_data"]
        drivers_b_data   = session_b["drivers_data"]

        # Nagłówek porównania
        col_a, col_sep, col_b_head = st.columns([5, 1, 5])
        with col_a:
            st.markdown(f"""
            <div class="results-header" style="margin-bottom:8px">
                <div>
                    <div class="results-title">{session_data.event_name} {session_data.year}</div>
                    <div class="results-meta">SESJA A · {session_data.session_type} · {session_data.circuit_name}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        with col_sep:
            st.markdown("<div style='text-align:center;font-size:2rem;padding-top:20px'>⚔️</div>",
                        unsafe_allow_html=True)
        with col_b_head:
            st.markdown(f"""
            <div class="results-header" style="margin-bottom:8px;border-left-color:#00d1ff">
                <div>
                    <div class="results-title">{session_b_data.event_name} {session_b_data.year}</div>
                    <div class="results-meta">SESJA B · {session_b_data.session_type} · {session_b_data.circuit_name}</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.divider()

        # ── Tabela porównawcza najszybszych okrążeń ───────────────────────────
        st.markdown('<div class="f1-subheader">Porównanie najszybszych okrążeń</div>',
                    unsafe_allow_html=True)

        all_d = {
            **{f"A:{k}": v for k, v in drivers_data.items()},
            **{f"B:{k}": v for k, v in drivers_b_data.items()},
        }
        cmp_rows = []
        for tag, d in all_d.items():
            cmp_rows.append({
                "Sesja":     "A" if tag.startswith("A:") else "B",
                "Kierowca":  d.driver,
                "Czas":      d.lap_time_str,
                "S1 [s]":    round(d.sector1, 3),
                "S2 [s]":    round(d.sector2, 3),
                "S3 [s]":    round(d.sector3, 3),
                "Okr. #":    d.lap_number,
                "Opona":     d.compound,
            })
        st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)

        # ── Telemetria porównawcza ─────────────────────────────────────────────
        st.markdown('<div class="f1-subheader">Telemetria — sesja A vs B</div>',
                    unsafe_allow_html=True)

        # Przyciemnij kolory sesji B, żeby odróżnić wizualnie
        def _dim_color(hex_col: str) -> str:
            h = hex_col.lstrip("#")
            try:
                r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            except ValueError:
                return hex_col
            r2 = min(255, int(r * 0.55 + 200 * 0.45))
            g2 = min(255, int(g * 0.55 + 200 * 0.45))
            b2 = min(255, int(b * 0.55 + 200 * 0.45))
            return f"#{r2:02x}{g2:02x}{b2:02x}"

        combined_data: dict = {}
        for drv, d in drivers_data.items():
            combined_data[drv] = d
        for drv, d in drivers_b_data.items():
            tag = f"B:{drv}"
            combined_data[tag] = replace(d, driver=tag, color=_dim_color(d.color))

        if len(combined_data) >= 2:
            mods = _import_modules()
            fig_cross_telem = mods["plot_telemetry_interactive"](
                combined_data, session_data
            )
            if fig_cross_telem is not None:
                st.plotly_chart(fig_cross_telem, use_container_width=True)

        # ── Styl jazdy — porównanie ────────────────────────────────────────────
        st.markdown('<div class="f1-subheader">Styl jazdy — sesja A vs B</div>',
                    unsafe_allow_html=True)
        mods = _import_modules()
        all_fps_raw = []
        for drv, d in drivers_data.items():
            all_fps_raw.append(mods["compute_style_fingerprint"](d, corner_analysis))
        for drv, d in drivers_b_data.items():
            tagged = replace(d, driver=f"B:{drv}", color=_dim_color(d.color))
            all_fps_raw.append(mods["compute_style_fingerprint"](tagged))

        if len(all_fps_raw) >= 2:
            all_fps = mods["normalize_fingerprints"](all_fps_raw)
            # Zastąp kolorami tagowanymi
            for fp, (tag, d_tagged) in zip(
                all_fps,
                list({k: v for k, v in {**{k: v for k, v in drivers_data.items()},
                                          **{f"B:{k}": replace(v, driver=f"B:{k}",
                                             color=_dim_color(v.color))
                                             for k, v in drivers_b_data.items()}}.items()}.items())
            ):
                pass  # kolory już ustawione przez compute_style_fingerprint

            crc, crb = st.columns([1, 1])
            with crc:
                fig_crs_radar = mods["plot_radar_interactive"](all_fps, session_data)
                st.plotly_chart(fig_crs_radar, use_container_width=True)
            with crb:
                fig_crs_bars = mods["plot_style_bars_interactive"](all_fps, session_data)
                st.plotly_chart(fig_crs_bars, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# TAB 9 — INFO
# ═══════════════════════════════════════════════════════════
with tabs[8]:
    st.markdown('<div class="f1-subheader">Wygenerowane wykresy</div>', unsafe_allow_html=True)
    generated = {k: v for k, v in figs.items() if v is not None}
    if generated:
        st.success(f"✅ {len(generated)} interaktywnych wykresów wygenerowanych.")
        st.dataframe(
            pd.DataFrame([{"Wykres": k} for k in generated]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Brak wygenerowanych wykresów.")

    if session_b:
        st.markdown('<div class="f1-subheader">Sesja B</div>', unsafe_allow_html=True)
        sb_d = session_b["session_data"]
        st.info(
            f"Załadowana sesja B: **{sb_d.event_name} {sb_d.year}** "
            f"— {sb_d.session_type} | {sb_d.circuit_name}, {sb_d.country}"
        )
