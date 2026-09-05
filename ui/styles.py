"""
Style dashboardu — jeden arkusz CSS budowany z tokenów motywu.

Zasada: kolor niesie informację. Interfejs jest neutralny (tło, ramki, tekst),
a nasycone barwy zostają dla danych — kolorów kierowców, składów opon i wykresów.
Jedynym akcentem UI jest czerwień F1, używana oszczędnie: akcja główna,
aktywna zakładka, wskaźnik sekcji.
"""

from __future__ import annotations

# ── Tokeny motywów ───────────────────────────────────────────────────────────
# Nazwy opisują rolę, nie kolor — dzięki temu oba motywy mają ten sam kontrakt.
_DARK = dict(
    bg="#0e1116",
    surface="#161a21",
    surface_2="#1b2028",
    surface_3="#222833",
    border="#262d38",
    border_strong="#38414f",
    text="#e6e9ee",
    text_secondary="#a9b2be",
    text_muted="#727c8a",
    heading="#ffffff",
    accent="#e10600",
    accent_hover="#ff2a1f",
    accent_soft="rgba(225,6,0,0.14)",
    accent_text="#ff5c52",
    success="#31c07a",
    success_bg="rgba(49,192,122,0.10)",
    warning="#e0a13a",
    warning_bg="rgba(224,161,58,0.10)",
    danger="#e5484d",
    danger_bg="rgba(229,72,77,0.10)",
    info_bg="rgba(120,150,200,0.08)",
    shadow="0 1px 2px rgba(0,0,0,0.4)",
    shadow_lg="0 4px 16px rgba(0,0,0,0.45)",
    overlay="rgba(14,17,22,0.92)",
)

_LIGHT = dict(
    bg="#f5f6f8",
    surface="#ffffff",
    surface_2="#f0f2f5",
    surface_3="#e7eaef",
    border="#dfe3e9",
    border_strong="#c3cad4",
    text="#161a20",
    text_secondary="#4d5765",
    text_muted="#79838f",
    heading="#0b0e13",
    accent="#d40500",
    accent_hover="#ab0400",
    accent_soft="rgba(212,5,0,0.09)",
    accent_text="#c00400",
    success="#177d4a",
    success_bg="rgba(23,125,74,0.09)",
    warning="#96631a",
    warning_bg="rgba(150,99,26,0.10)",
    danger="#c0272c",
    danger_bg="rgba(192,39,44,0.09)",
    info_bg="rgba(70,100,150,0.06)",
    shadow="0 1px 2px rgba(16,24,40,0.06)",
    shadow_lg="0 4px 16px rgba(16,24,40,0.10)",
    overlay="rgba(245,246,248,0.94)",
)

THEMES = {"dark": _DARK, "light": _LIGHT}

FONT_UI = "'Inter', -apple-system, 'Segoe UI', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Consolas', monospace"

def get_css(theme: str = "dark") -> str:
    """Zwraca kompletny arkusz stylów dla wybranego motywu."""
    c = THEMES.get(theme, _DARK)
    return f"<style>{_tokens(c)}{_BASE}{_LAYOUT}{_WIDGETS}{_COMPONENTS}</style>"


def _tokens(c: dict) -> str:
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {{
    --bg: {c['bg']};
    --surface: {c['surface']};
    --surface-2: {c['surface_2']};
    --surface-3: {c['surface_3']};
    --border: {c['border']};
    --border-strong: {c['border_strong']};
    --text: {c['text']};
    --text-2: {c['text_secondary']};
    --muted: {c['text_muted']};
    --heading: {c['heading']};
    --accent: {c['accent']};
    --accent-hover: {c['accent_hover']};
    --accent-soft: {c['accent_soft']};
    --accent-text: {c['accent_text']};
    --success: {c['success']};
    --success-bg: {c['success_bg']};
    --warning: {c['warning']};
    --warning-bg: {c['warning_bg']};
    --danger: {c['danger']};
    --danger-bg: {c['danger_bg']};
    --info-bg: {c['info_bg']};
    --shadow: {c['shadow']};
    --shadow-lg: {c['shadow_lg']};
    --overlay: {c['overlay']};
    --font-ui: {FONT_UI};
    --font-mono: {FONT_MONO};
    --radius: 8px;
    --radius-sm: 6px;
}}
"""


# ── Podstawy: tło, typografia, scrollbar ─────────────────────────────────────
_BASE = """
/* Tło malujemy na wszystkich warstwach Streamlita — gdy motyw dashboardu
   różni się od motywu Streamlita, sam `.stApp` by nie wystarczył. */
body,
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stBottomBlockContainer"] { background: var(--bg) !important; }

html, body, [class*="css"], .stMarkdown, p, span, div, label, li {
    font-family: var(--font-ui);
    color: var(--text);
}
h1, h2, h3, h4, h5, h6 {
    color: var(--heading) !important;
    font-family: var(--font-ui) !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
}
[data-testid="stDataFrame"] *, pre, code, .stCodeBlock * {
    font-family: var(--font-mono) !important;
}
a { color: var(--accent-text) !important; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: var(--border-strong);
    border-radius: 6px;
    border: 3px solid var(--bg);
}
::-webkit-scrollbar-thumb:hover { background: var(--muted); }
"""


# ── Układ: pasek narzędzi, sidebar, szerokość treści ─────────────────────────
_LAYOUT = """
/* Nagłówek Streamlita to przezroczysty pasek wysokości 60 px, leżący NAD treścią
   i przechwytujący kliknięcia. Wyłączamy mu zdarzenia myszy (poza własnym
   paskiem narzędzi) i zaczynamy treść pod nim — inaczej górne przyciski
   i zakładki nie dają się kliknąć. */
[data-testid="stHeader"] {
    background: transparent !important;
    pointer-events: none;
}
[data-testid="stToolbar"], [data-testid="stHeader"] button {
    pointer-events: auto;
    right: 0.5rem;
}

.block-container {
    padding-top: 4rem !important;
    padding-bottom: 3rem !important;
    max-width: 1500px;
}

/* ── Sidebar: panel sterowania ── */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
    width: 360px !important;
}
section[data-testid="stSidebar"] > div { padding-top: 0.6rem; }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem !important; }
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarCollapsedControl"] button { color: var(--text-2) !important; }

/* Etykiety pól są nośnikiem informacji — muszą być czytelne, nie ozdobne. */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: var(--text-2) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {
    color: var(--muted) !important;
}

/* ── Przyklejona listwa zakładek: nawigacja zostaje pod ręką ──
   Streamlit zamyka listwę w kontenerze o dokładnie jej wysokości, więc sticky
   nie miałby po czym jechać. Rozpuszczamy ten kontener (display: contents),
   dzięki czemu listwa staje się dzieckiem całego bloku zakładek i może
   przesuwać się wzdłuż jego wysokości. */
[data-testid="stTabs"] > div > div:first-child { display: contents; }
[data-testid="stTabs"] > div > div:first-child > [data-baseweb="tab-list"] {
    position: sticky;
    top: 3.75rem;   /* tuż pod nagłówkiem Streamlita (60 px) */
    z-index: 60;
    background: var(--overlay);
    backdrop-filter: blur(8px);
    padding-top: 0.4rem;
}
"""


# ── Widgety Streamlita ───────────────────────────────────────────────────────
_WIDGETS = """
/* ── Pola tekstowe i liczbowe ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-mono) !important;
    font-size: 0.9rem !important;
}
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder { color: var(--muted) !important; }

[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-soft) !important;
}
[data-testid="stNumberInput"] button {
    background: var(--surface-3) !important;
    border-color: var(--border) !important;
    color: var(--text-2) !important;
}

/* ── Selectbox i multiselect ── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text) !important;
    min-height: 40px;
}
[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div:hover {
    border-color: var(--border-strong) !important;
}
div[data-baseweb="popover"] li { font-family: var(--font-mono) !important; }

/* Wybrani kierowcy jako żetony — czytelne, ale bez krzyku */
[data-testid="stMultiSelect"] span[data-baseweb="tag"] {
    background: var(--accent-soft) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent-text) !important;
    border-radius: 5px !important;
    font-family: var(--font-mono) !important;
    font-weight: 600 !important;
}
[data-testid="stMultiSelect"] span[data-baseweb="tag"] span { color: var(--accent-text) !important; }

/* ── Suwak ── */
[data-testid="stSlider"] [role="slider"] { background: var(--accent) !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[data-testid="stSliderTickBar"] { display: none; }
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: var(--accent-text) !important;
    font-family: var(--font-mono) !important;
}

/* ── Przyciski ── */
.stButton > button, .stDownloadButton > button {
    background: var(--surface-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border-strong) !important;
    border-radius: var(--radius-sm) !important;
    font-family: var(--font-ui) !important;
    font-weight: 500 !important;
    font-size: 0.86rem !important;
    padding: 0.45rem 0.9rem !important;
    transition: background 0.12s ease, border-color 0.12s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--surface-3) !important;
    border-color: var(--muted) !important;
    color: var(--text) !important;
}
.stButton > button:focus:not(:active) { box-shadow: 0 0 0 3px var(--accent-soft) !important; }

.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--accent-hover) !important;
    border-color: var(--accent-hover) !important;
}

/* ── Zakładki ── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 0.15rem;
    border-bottom: 1px solid var(--border);
}
[data-testid="stTabs"] button[role="tab"] {
    background: transparent !important;
    color: var(--text-2) !important;
    font-family: var(--font-ui) !important;
    font-size: 0.86rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 0.85rem !important;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0 !important;
    border-bottom: 2px solid transparent !important;
}
[data-testid="stTabs"] button[role="tab"]:hover {
    background: var(--surface-2) !important;
    color: var(--text) !important;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--text) !important;
    font-weight: 600 !important;
    border-bottom-color: var(--accent) !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Tabele ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    overflow: hidden;
}

/* ── Komunikaty ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    border-left-width: 3px !important;
}
/* Streamlit koloruje tekst komunikatów pod własny motyw — wymuszamy nasz,
   inaczej w ciemnym motywie zielone „gotowe” bywa nieczytelne. */
[data-testid="stAlert"] p,
[data-testid="stAlert"] div,
[data-testid="stAlert"] span,
[data-testid^="stAlertContent"] { color: var(--text) !important; }
[data-testid="stAlert"] svg { fill: currentColor !important; }
.stSuccess { background: var(--success-bg) !important; border-left-color: var(--success) !important; }
.stWarning { background: var(--warning-bg) !important; border-left-color: var(--warning) !important; }
.stError   { background: var(--danger-bg)  !important; border-left-color: var(--danger)  !important; }
.stInfo    { background: var(--info-bg)    !important; border-left-color: var(--border-strong) !important; }

/* ── Rozwijane sekcje ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
}
[data-testid="stExpander"] summary { color: var(--text) !important; font-size: 0.88rem !important; }
[data-testid="stExpander"] summary:hover { color: var(--accent-text) !important; }

/* ── Postęp i spinner ── */
[data-testid="stProgress"] > div > div > div { background: var(--accent) !important; }
[data-testid="stProgress"] > div > div { background: var(--surface-3) !important; }
[data-testid="stSpinner"] > div { border-top-color: var(--accent) !important; }

hr, [data-testid="stDivider"] hr { border-color: var(--border) !important; }
"""


# ── Komponenty własne ────────────────────────────────────────────────────────
_COMPONENTS = """
/* ── Pasek tytułowy ── */
.topbar {
    display: flex;
    align-items: baseline;
    gap: 0.75rem;
    padding-bottom: 0.7rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
.topbar-mark {
    width: 4px; height: 22px;
    background: var(--accent);
    border-radius: 2px;
    align-self: center;
}
.topbar-title {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    color: var(--heading);
}
.topbar-sub { font-size: 0.8rem; color: var(--muted); }

/* ── Pasek sesji: co właściwie oglądam ── */
.session-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.6rem;
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: var(--radius);
    padding: 0.7rem 0.95rem;
    margin-bottom: 0.85rem;
}
.session-name {
    font-size: 1rem;
    font-weight: 650;
    color: var(--heading);
}
.session-meta {
    font-size: 0.82rem;
    color: var(--text-2);
    margin-top: 0.15rem;
}
.session-tag {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--muted);
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.2rem 0.65rem;
    white-space: nowrap;
}

/* ── Listwa kierowców: kolor = kierowca ── */
.driver-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.driver-pill {
    flex: 1 1 150px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-top: 3px solid var(--c);
    border-radius: var(--radius);
    padding: 0.6rem 0.8rem;
}
.dp-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.4rem;
}
.dp-code {
    font-family: var(--font-mono);
    font-size: 0.95rem;
    font-weight: 700;
    color: var(--c);
    letter-spacing: 0.04em;
}
.dp-pos {
    font-family: var(--font-mono);
    font-size: 0.7rem;
    color: var(--muted);
}
.dp-time {
    font-family: var(--font-mono);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text);
    margin: 0.25rem 0 0.1rem;
    letter-spacing: -0.02em;
}
.dp-delta {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-2);
}
.dp-delta.lead { color: var(--accent-text); font-weight: 600; }
.dp-meta {
    font-size: 0.72rem;
    color: var(--muted);
    margin-top: 0.35rem;
    padding-top: 0.35rem;
    border-top: 1px solid var(--border);
}

/* ── Tabele danych ──
   Rysujemy je sami (patrz components.table), więc trzymają się motywu
   aplikacji, a nie motywu Streamlita. */
.table-wrap {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: auto;
    margin-bottom: 0.3rem;
}
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--font-mono);
    font-size: 0.82rem;
}
.data-table thead th {
    position: sticky;
    top: 0;
    background: var(--surface-2);
    color: var(--muted);
    font-weight: 600;
    font-size: 0.72rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    text-align: left;
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
.data-table td {
    padding: 0.5rem 0.75rem;
    color: var(--text);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
.data-table tbody tr:last-child td { border-bottom: none; }
.data-table tbody tr:nth-child(even) { background: var(--surface); }
.data-table tbody tr:hover { background: var(--surface-2); }
.data-table .num { text-align: right; font-variant-numeric: tabular-nums; }

/* Objaśnienie pod tabelą lub wykresem */
.hint {
    font-size: 0.76rem;
    color: var(--muted);
    line-height: 1.5;
    margin: 0.15rem 0 0.4rem;
}

/* ── Nagłówek sekcji wewnątrz zakładki ── */
.section-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.5rem 0 0.6rem;
}
.section-title::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}
.section-title:first-child { margin-top: 0.3rem; }

/* ── Kafelek z podpowiedzią ── */
.note-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.1rem;
    font-size: 0.88rem;
    color: var(--text-2);
    line-height: 1.6;
}
.note-card b, .note-card strong { color: var(--text); }
.note-card ol, .note-card ul { margin: 0.5rem 0 0 1.1rem; padding: 0; }
.note-card li { margin-bottom: 0.3rem; color: var(--text-2); }

/* ── Ekran powitalny ── */
.welcome {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.6rem 1.5rem;
    margin-bottom: 1.1rem;
}
.welcome-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--heading);
    margin-bottom: 0.4rem;
}
.welcome-sub { font-size: 0.92rem; color: var(--text-2); line-height: 1.65; }
.welcome-sub .accent { color: var(--accent-text); font-weight: 600; }

.feature-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent-c, var(--border-strong));
    border-radius: var(--radius-sm);
    padding: 0.8rem 0.9rem;
    margin-bottom: 0.6rem;
    height: 100%;
}
.feature-title {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 0.2rem;
}
.feature-desc { font-size: 0.76rem; color: var(--muted); line-height: 1.5; }

/* ── Porównanie sesji ── */
.compare-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--c, var(--accent));
    border-radius: var(--radius);
    padding: 0.7rem 0.9rem;
}
.compare-label {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    color: var(--muted);
}
.compare-name { font-size: 0.98rem; font-weight: 650; color: var(--heading); margin-top: 0.15rem; }
.compare-meta { font-size: 0.78rem; color: var(--text-2); }
.compare-vs {
    text-align: center;
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--muted);
    padding-top: 1.5rem;
}

/* ── Sekcja w sidebarze ── */
.side-section {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin: 1.1rem 0 0.5rem;
}
.side-section::after {
    content: "";
    flex: 1;
    height: 1px;
    background: var(--border);
}
.side-section:first-child { margin-top: 0.2rem; }
"""
