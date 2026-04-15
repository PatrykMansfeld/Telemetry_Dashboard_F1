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
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg-0: #0b0c0f;
    --bg-1: #101318;
    --bg-2: #151a21;
    --panel: #0f1217;
    --panel-2: #121822;
    --border: #2a3038;
    --border-soft: #1d232b;
    --text: #d8dde6;
    --muted: #7b8494;
    --accent: #e10600;
    --accent-2: #c8ff3d;
    --accent-3: #00d1ff;
    --glow: rgba(225,6,0,0.35);
}

.stApp {
    background-color: var(--bg-0) !important;
    background-image:
        radial-gradient(900px 480px at 8% -10%, rgba(225,6,0,0.22), transparent 60%),
        radial-gradient(800px 520px at 100% 0%, rgba(0,209,255,0.16), transparent 60%),
        repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0 1px, transparent 1px 28px),
        repeating-linear-gradient(90deg, rgba(255,255,255,0.02) 0 1px, transparent 1px 28px);
    background-attachment: fixed;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1217 0%, #0b0c0f 100%) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: inset -1px 0 0 var(--border-soft) !important;
}

html, body, [class*="css"] {
    color: var(--text) !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
h1, h2, h3, h4, h5 {
    color: #ffffff !important;
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 0.12em !important;
}
[data-testid="stDataFrame"] *,
pre, code, .stCodeBlock * {
    font-family: 'JetBrains Mono', monospace !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-0); }
::-webkit-scrollbar-thumb { background: #2d333c; border-radius: 6px; }
::-webkit-scrollbar-thumb:hover { background: #3a414c; }

[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
textarea {
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.95rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--glow) !important;
    outline: none !important;
}
[data-testid="stMultiSelect"] > div,
[data-testid="stSelectbox"] > div > div {
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

[data-testid="stSlider"] [role="slider"] {
    background-color: var(--accent) !important;
    box-shadow: 0 0 8px var(--glow) !important;
}
[data-testid="stSlider"] > div > div > div > div:first-child {
    background: var(--accent) !important;
}

[data-testid="stCheckbox"] label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

.stButton > button {
    background: linear-gradient(135deg, #e10600 0%, #ff3b2a 60%, #ff7a00 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.12em !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    transition: transform 0.15s ease, box-shadow 0.2s ease !important;
    box-shadow: 0 10px 30px rgba(225,6,0,0.25) !important;
    padding: 0.55rem 1.1rem !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 16px 38px rgba(225,6,0,0.35) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

[data-testid="stTabs"] [role="tablist"] {
    gap: 8px !important;
    border-bottom: 1px solid var(--border) !important;
    padding-bottom: 6px !important;
}
[data-testid="stTabs"] button[role="tab"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 999px !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: 0.08em !important;
    font-size: 0.78rem !important;
    padding: 6px 14px !important;
    transition: color 0.15s, border-color 0.15s, background 0.15s !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    color: #ffffff !important;
    border-color: var(--accent) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: #ffffff !important;
    border-color: var(--accent) !important;
    background: rgba(225,6,0,0.15) !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(160deg, #131820, #0f1217) !important;
    border: 1px solid var(--border) !important;
    border-top: 2px solid var(--accent) !important;
    border-radius: 12px !important;
    padding: 14px 18px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stMetric"]:hover { border-color: #3a414c !important; }
[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 1.5rem !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 500 !important;
}
[data-testid="stMetricLabel"] {
    color: var(--muted) !important;
    font-size: 0.68rem !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, var(--accent), #ff7a00) !important;
    border-radius: 6px !important;
    transition: width 0.3s ease !important;
}

[data-testid="stAlert"] { border-radius: 10px !important; }
.stSuccess { background-color: #0b1a12 !important; border-color: #2adf9d !important; }
.stWarning { background-color: #201800 !important; }
.stError   { background-color: #1a0b0b !important; }

[data-testid="stExpander"] {
    background-color: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    transition: border-color 0.2s !important;
}
[data-testid="stExpander"]:hover { border-color: #3a414c !important; }
[data-testid="stExpander"] summary {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

[data-testid="stSpinner"] { color: var(--accent) !important; }
hr { border-color: var(--border) !important; margin: 14px 0 !important; }

[data-testid="stSidebar"] label {
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.86rem !important;
    letter-spacing: 0.04em !important;
}

.sb-section {
    color: var(--muted);
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    padding: 6px 0 8px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 10px;
    font-family: 'Space Grotesk', sans-serif;
}

.js-plotly-plot .plotly .modebar {
    background: transparent !important;
}
.js-plotly-plot .plotly .modebar-btn path {
    fill: var(--muted) !important;
}
.js-plotly-plot .plotly .modebar-btn:hover path {
    fill: var(--accent) !important;
}

.f1-subheader {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.92rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: #ffffff;
    padding: 8px 0 8px 12px;
    border-left: 3px solid var(--accent);
    margin-bottom: 12px;
    text-transform: uppercase;
}

.hero {
    position: relative;
    display: flex;
    align-items: center;
    gap: 18px;
    padding: 20px 26px;
    margin: -1rem -1rem 1.6rem;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 14px;
    background: linear-gradient(135deg, #0e1116 0%, #141a22 45%, #0b0c0f 100%);
    box-shadow: 0 18px 40px rgba(0,0,0,0.35), 0 0 28px var(--glow);
    overflow: hidden;
    flex-wrap: wrap;
}
.hero > * { position: relative; z-index: 1; }
.hero::after {
    content: "";
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0 2px, transparent 2px 12px);
    opacity: 0.25;
    pointer-events: none;
}
.results-icon { font-size: 1.4rem; opacity: 0.85; }
.hero-stripe {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 6px;
    background: linear-gradient(180deg, #ff3b2a, #e10600, #7a0000);
    box-shadow: 0 0 18px var(--glow);
}
.hero-icon { font-size: 2.2rem; line-height: 1; filter: drop-shadow(0 0 10px var(--glow)); }
.hero-title { font-family: 'Bebas Neue', sans-serif; font-size: 2rem; letter-spacing: 0.18em; color: #ffffff; }
.hero-sub { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.28em; text-transform: uppercase; margin-top: 4px; }
.hero-tag { margin-left: auto; font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: var(--accent-2); border: 1px solid rgba(200,255,61,0.5); padding: 6px 10px; border-radius: 999px; background: rgba(200,255,61,0.1); }

.sb-brand { display: flex; align-items: center; gap: 10px; padding: 14px 6px 12px; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.sb-brand-icon { font-size: 1.5rem; filter: drop-shadow(0 0 10px var(--glow)); }
.sb-brand-title { font-family: 'Bebas Neue', sans-serif; font-size: 1.25rem; letter-spacing: 0.22em; color: #ffffff; }
.sb-brand-sub { font-size: 0.6rem; color: var(--muted); letter-spacing: 0.2em; text-transform: uppercase; }

.welcome { margin-top: 8px; margin-bottom: 26px; }
.welcome-title { font-family: 'Bebas Neue', sans-serif; font-size: 2.1rem; letter-spacing: 0.16em; color: #ffffff; }
.welcome-sub { font-size: 0.95rem; color: var(--muted); margin-top: 8px; letter-spacing: 0.06em; }
.accent { color: var(--accent); font-weight: 700; letter-spacing: 0.12em; }

.feature-card {
    background: linear-gradient(160deg, rgba(20,25,34,0.95), rgba(12,14,18,0.95));
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent, #e10600);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    animation: fadeUp 0.6s ease both;
}
.feature-card:hover {
    transform: translateY(-2px);
    border-color: var(--accent, #e10600);
    box-shadow: 0 12px 26px rgba(0,0,0,0.35), 0 0 18px var(--accent, #e10600);
}
.feature-icon { font-size: 1.6rem; margin-bottom: 8px; }
.feature-title { font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 700; color: #ffffff; letter-spacing: 0.08em; margin-bottom: 6px; }
.feature-desc { font-size: 0.8rem; color: var(--muted); line-height: 1.4; }

.note-card {
    background: linear-gradient(135deg, rgba(18,20,26,0.95), rgba(10,12,16,0.95));
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px 18px;
    font-size: 0.82rem;
    color: var(--muted);
    letter-spacing: 0.04em;
}

.results-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 14px 20px;
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 12px;
    background: linear-gradient(135deg, #121722 0%, #0b0c0f 70%);
    box-shadow: 0 12px 26px rgba(0,0,0,0.35);
    margin-bottom: 18px;
    flex-wrap: wrap;
}
.results-title { font-family: 'Bebas Neue', sans-serif; font-size: 1.4rem; letter-spacing: 0.16em; color: #ffffff; }
.results-meta { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.18em; text-transform: uppercase; }
.results-badge { margin-left: auto; font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase; color: #ffffff; background: rgba(0,209,255,0.15); border: 1px solid rgba(0,209,255,0.45); padding: 6px 10px; border-radius: 999px; }

.driver-card {
    background: linear-gradient(160deg, #141a22, #0f1217);
    border: 1px solid var(--border);
    border-top: 2px solid var(--accent, #e10600);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
    box-shadow: 0 10px 22px rgba(0,0,0,0.25);
}
.driver-card-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 8px; }
.driver-title { font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; letter-spacing: 0.14em; color: var(--accent, #e10600); }
.driver-badge { font-size: 0.65rem; color: var(--muted); letter-spacing: 0.2em; text-transform: uppercase; }
.driver-time { font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: #ffffff; margin-bottom: 10px; }
.driver-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 8px; }
.driver-chip { background: var(--panel-2); border: 1px solid var(--border-soft); border-radius: 8px; padding: 6px 8px; text-align: center; }
.driver-chip-label { font-size: 0.62rem; color: var(--muted); letter-spacing: 0.14em; }
.driver-chip-value { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; color: #ffffff; }
.driver-meta { font-size: 0.7rem; color: var(--muted); letter-spacing: 0.1em; }

.fade-in { animation: fadeUp 0.7s ease both; }
.delay-1 { animation-delay: 0.05s; }
.delay-2 { animation-delay: 0.1s; }
.delay-3 { animation-delay: 0.15s; }
.delay-4 { animation-delay: 0.2s; }
.delay-5 { animation-delay: 0.25s; }
.delay-6 { animation-delay: 0.3s; }

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
    .hero { margin: -1rem -1rem 1.2rem; }
    .hero-tag, .results-badge { margin-left: 0; }
    .driver-grid { grid-template-columns: 1fr 1fr; }
}
</style>
""", unsafe_allow_html=True)


# ── Stałe ─────────────────────────────────────────────────────────────────────
SESSIONS = ["Q", "R", "FP1", "FP2", "FP3", "S", "SS"]

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
        help="Q=Kwalifikacje, R=Wyścig, FP1/FP2/FP3=Treningi, S=Sprint, SS=Sprint Shootout",
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
    elif session_data.session_type != "R":
        st.info(
            "ℹ️ Race Pace jest najbardziej miarodajny dla sesji wyścigowych (R). "
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
