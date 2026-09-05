"""Zakładka „Mapa toru” — dominacja, mapy per kierowca, DRS i animacja."""

from __future__ import annotations

import streamlit as st

from f1tele.pipeline import AnalysisResult, build_track_animation

from .. import state
from ..components import chart, empty_module, subheader


def render(result: AnalysisResult) -> None:
    figures = result.figures
    drawn = False

    if "track_dominance" in figures:
        subheader("Dominacja na torze")
        drawn = chart(figures["track_dominance"])
    elif result.drivers and not result.has_gps:
        st.warning("⚠️ Brak danych GPS — mapa dominacji niedostępna dla tej sesji.")

    drawn = _render_driver_maps(result) or drawn

    if "drs" in figures:
        subheader("Analiza DRS")
        drawn = chart(figures["drs"]) or drawn

    _render_animation(result)

    if not drawn and not result.has_gps:
        empty_module("Mapa toru")


def _render_driver_maps(result: AnalysisResult) -> bool:
    """Mapy prędkości i biegów, po jednej podzakładce na kierowcę."""
    drivers = [d for d in result.drivers
               if f"speed_map_{d}" in result.figures or f"gear_map_{d}" in result.figures]
    if not drivers:
        return False

    subheader("Mapy toru per kierowca")
    for tab, driver in zip(st.tabs([f"🗺️ {d}" for d in drivers]), drivers):
        with tab:
            col_speed, col_gear = st.columns(2)
            with col_speed:
                st.subheader("Prędkość")
                chart(result.figures.get(f"speed_map_{driver}"))
            with col_gear:
                st.subheader("Biegi")
                chart(result.figures.get(f"gear_map_{driver}"))
    return True


def _render_animation(result: AnalysisResult) -> None:
    """Animacja jest kosztowna, więc liczymy ją dopiero na żądanie."""
    subheader("Animacja okrążenia")

    if not result.has_gps:
        st.warning("⚠️ Brak danych GPS — animacja niedostępna dla tej sesji.")
        return

    drivers = list(result.drivers)
    if st.button("▶ Wygeneruj animację okrążenia", key="generate_animation"):
        with st.spinner("Generowanie animacji..."):
            try:
                figure = build_track_animation(result)
            except Exception as exc:
                st.error(f"Błąd generowania animacji: {exc}")
                figure = None
            if figure is None:
                st.warning("⚠️ Nie udało się wygenerować animacji.")
            else:
                state.set_animation(drivers, figure)

    if not chart(state.get_animation(drivers)):
        st.caption("Kliknij przycisk powyżej, aby wygenerować animację.")
