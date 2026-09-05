"""
Zakładki dashboardu.

`render_tabs` składa stałą część widoku — pasek sesji i listwę kierowców, które
zostają na ekranie niezależnie od zakładki — a treść deleguje do modułów:
jedna zakładka = jeden plik.
"""

from __future__ import annotations

import streamlit as st

from f1tele.pipeline import AnalysisResult

from . import (
    corners,
    cross_session,
    info,
    race_pace,
    sectors,
    style,
    summary,
    telemetry,
    track,
)

TAB_NAMES = [
    "Podsumowanie", "Telemetria", "Zakręty", "Sektory", "Styl jazdy",
    "Mapa toru", "Race pace", "Porównanie", "Info",
]


def render_tabs(result: AnalysisResult, session_b: AnalysisResult | None) -> None:
    """Renderuje kontekst sesji, listwę kierowców i wszystkie zakładki."""
    _render_session_bar(result, session_b)
    _render_driver_strip(result)

    tabs = st.tabs(TAB_NAMES)
    renderers = [
        summary.render, telemetry.render, corners.render, sectors.render,
        style.render, track.render, race_pace.render,
    ]
    for tab, render in zip(tabs, renderers):
        with tab:
            render(result)

    with tabs[7]:
        cross_session.render(result, session_b)
    with tabs[8]:
        info.render(result, session_b)


def _render_session_bar(result: AnalysisResult, session_b: AnalysisResult | None) -> None:
    """Stała informacja o tym, czyje dane są na ekranie."""
    session = result.session
    tag = f"{len(result.drivers)} kierowców · {len(result.figures)} wykresów"
    if session_b is not None:
        tag += f" · sesja B: {session_b.session.event_name} {session_b.session.year}"

    st.markdown(f"""
    <div class="session-bar">
        <div>
            <div class="session-name">{session.event_name} {session.year}</div>
            <div class="session-meta">
                {session.session_type} · {session.circuit_name}, {session.country}
                · runda {session.round_number}
            </div>
        </div>
        <div class="session-tag">{tag}</div>
    </div>
    """, unsafe_allow_html=True)


def _render_driver_strip(result: AnalysisResult) -> None:
    """Czasy okrążeń wszystkich porównywanych kierowców, w kolorach zespołów."""
    drivers = result.sorted_drivers
    if not drivers:
        return

    reference = drivers[0].lap_time
    pills = []
    for position, driver in enumerate(drivers, start=1):
        delta = driver.lap_time - reference
        delta_html = ('<span class="dp-delta lead">najszybsze</span>' if delta == 0
                      else f'<span class="dp-delta">+{delta:.3f} s</span>')
        pills.append(f"""
        <div class="driver-pill" style="--c:{driver.color}">
            <div class="dp-head">
                <span class="dp-code">{driver.driver}</span>
                <span class="dp-pos">P{position}</span>
            </div>
            <div class="dp-time">{driver.lap_time_str}</div>
            {delta_html}
            <div class="dp-meta">okr. {driver.lap_number} · {driver.compound.title()}</div>
        </div>""")

    st.markdown(f'<div class="driver-strip">{"".join(pills)}</div>',
                unsafe_allow_html=True)


__all__ = ["render_tabs", "TAB_NAMES"]
