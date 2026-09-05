"""
F1 Telemetria — dashboard Streamlit.

Uruchomienie:  streamlit run app.py

Podział ekranu: sidebar to panel sterowania („co analizujemy”), główna kolumna
to wyniki („co z tego wyszło”). Plik jest celowo krótki — składa ekran z gotowych
elementów (`ui/`), a całą analizę zleca pakietowi `f1tele`.
"""

from __future__ import annotations

import logging

import streamlit as st

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

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from ui import state  # noqa: E402
from ui.analysis import run_main_analysis, run_session_b_analysis  # noqa: E402
from ui.components import table  # noqa: E402
from ui.controls import render_controls  # noqa: E402
from ui.styles import get_css  # noqa: E402
from ui.tabs import render_tabs  # noqa: E402
from ui.welcome import render_welcome  # noqa: E402

SCHEDULE_COLUMNS = {
    "RoundNumber": "Runda",
    "EventName":   "GP",
    "Location":    "Miasto",
    "Country":     "Kraj",
    "EventDate":   "Data",
}


def render_topbar(theme: str) -> None:
    """Wąski pasek tytułowy — nazwa aplikacji i przełącznik motywu."""
    title, switch = st.columns([9, 1])
    with title:
        st.markdown("""
        <div class="topbar">
            <div class="topbar-mark"></div>
            <div class="topbar-title">F1 Telemetria</div>
            <div class="topbar-sub">Analiza stylu jazdy kierowców · FastF1</div>
        </div>
        """, unsafe_allow_html=True)
    with switch:
        label = "☀ Jasny" if theme == "dark" else "☾ Ciemny"
        if st.button(label, width="stretch",
                     help="Motyw dashboardu i wykresów. Domyślnie zgodny z motywem "
                          "Streamlita (menu ⋮ → Settings → Appearance)."):
            state.toggle_theme()
            st.rerun()


def render_schedule() -> None:
    """Kalendarz sezonu — pokazywany raz, po kliknięciu w sidebarze."""
    if not st.session_state.pop(state.SHOW_SCHEDULE, False):
        return

    from f1tele.data_loader import get_available_sessions

    year = st.session_state.get(state.SCHEDULE_YEAR)
    with st.spinner(f"Pobieranie harmonogramu {year}..."):
        schedule = get_available_sessions(year)

    if schedule.empty:
        st.error(f"Nie udało się pobrać harmonogramu sezonu {year}.")
        return

    with st.expander(f"Kalendarz sezonu {year}", expanded=True):
        table(schedule.rename(columns=SCHEDULE_COLUMNS), max_height=420)


def main() -> None:
    state.ensure_theme_detected()
    theme = state.current_theme()
    st.markdown(get_css(theme), unsafe_allow_html=True)

    render_topbar(theme)
    controls = render_controls()
    render_schedule()

    if controls.run_b:
        run_session_b_analysis(controls)
    if controls.run:
        run_main_analysis(controls)

    result = state.get_result()
    if result is None:
        render_welcome()
        return

    render_tabs(result, state.get_session_b())


main()
