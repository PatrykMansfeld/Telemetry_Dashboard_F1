"""Zakładka „Cross-session” — porównanie dwóch sesji (np. Monaco 2023 vs 2024)."""

from __future__ import annotations

from dataclasses import replace

import pandas as pd
import streamlit as st

from f1tele.config import DEFAULT_MINI_SECTS
from f1tele.corner_analysis import run_corner_analysis
from f1tele.driver_style import compute_style_fingerprint, normalize_fingerprints
from f1tele.pipeline import AnalysisResult
from f1tele.plots import (
    plot_corners_interactive,
    plot_mini_sector_dominance_interactive,
    plot_radar_interactive,
    plot_style_bars_interactive,
    plot_telemetry_interactive,
)
from f1tele.sector_analysis import compute_mini_sectors

from .. import state
from ..components import chart, dim_color, note, subheader, table

# Prefiks odróżniający kierowców z sesji B w połączonych wykresach.
TAG_B = "B:"


def render(result: AnalysisResult, session_b: AnalysisResult | None) -> None:
    if session_b is None:
        note("""
            <b>Porównanie dwóch sesji</b><br><br>
            Aby porównać kierowców między dwiema sesjami (np. Monaco 2023 vs 2024):
            <ol>
                <li>W sidebarze rozwiń <b>Porównanie z drugą sesją</b></li>
                <li>Wybierz rok, rundę i typ sesji B</li>
                <li>Wybierz kierowców sesji B</li>
                <li>Kliknij <b>Wczytaj sesję B</b></li>
            </ol>
        """)
        return

    _render_headers(result, session_b)

    subheader("Porównanie najszybszych okrążeń")
    table(_comparison_table(result, session_b), download="porownanie_sesji")

    theme = state.current_theme()
    same_circuit = result.same_circuit_as(session_b)
    combined = dict(result.drivers)
    for driver, data in session_b.drivers.items():
        combined[TAG_B + driver] = replace(
            data, driver=TAG_B + driver, color=dim_color(data.color))

    if len(combined) >= 2:
        subheader("Telemetria — sesja A vs B")
        if same_circuit:
            chart(plot_telemetry_interactive(combined, result.session, theme=theme))
        else:
            st.warning(
                f"Sesje odbyły się na różnych torach "
                f"({result.session.circuit_name} vs {session_b.session.circuit_name}), "
                "więc nakładanie telemetrii po dystansie nic nie mówi — ten sam "
                "kilometr okrążenia to zupełnie inne miejsce. Wykres pomijamy; "
                "porównanie stylu jazdy poniżej pozostaje sensowne."
            )

        if same_circuit:
            _render_track_comparison(combined, result, theme)

        subheader("Styl jazdy — sesja A vs B")
        fingerprints = normalize_fingerprints(
            [compute_style_fingerprint(d, result.corners) for d in result.drivers.values()]
            + [compute_style_fingerprint(combined[TAG_B + drv])
               for drv in session_b.drivers]
        )
        col_radar, col_bars = st.columns([1, 1])
        with col_radar:
            chart(plot_radar_interactive(fingerprints, result.session, theme=theme))
        with col_bars:
            chart(plot_style_bars_interactive(fingerprints, result.session, theme=theme))


def _render_track_comparison(combined: dict, result: AnalysisResult, theme: str) -> None:
    """
    Sektory i zakręty dla obu sesji naraz.

    Ma sens tylko na tym samym torze — stąd wywołanie zza sprawdzenia toru.
    Zakręty liczymy od nowa, bo analiza sesji A nie zna kierowców z sesji B.
    """
    subheader("Dominacja w mini-sektorach — sesja A vs B")
    mini_sectors = compute_mini_sectors(combined, DEFAULT_MINI_SECTS)
    chart(plot_mini_sector_dominance_interactive(
        combined, mini_sectors, result.session, theme=theme))

    subheader("Zakręty — sesja A vs B")
    corners = run_corner_analysis(combined, result.session.corners)
    chart(plot_corners_interactive(combined, corners, result.session, theme=theme))


def _render_headers(result: AnalysisResult, session_b: AnalysisResult) -> None:
    col_a, col_vs, col_b = st.columns([5, 1, 5])
    with col_a:
        _session_card(result, "SESJA A", accent="var(--accent)")
    with col_vs:
        st.markdown('<div class="compare-vs">vs</div>', unsafe_allow_html=True)
    with col_b:
        _session_card(session_b, "SESJA B", accent="#4c8dff")


def _session_card(result: AnalysisResult, label: str, accent: str) -> None:
    session = result.session
    drivers = ", ".join(sorted(result.drivers))
    st.markdown(f"""
    <div class="compare-card" style="--c:{accent}">
        <div class="compare-label">{label}</div>
        <div class="compare-name">{session.event_name} {session.year}</div>
        <div class="compare-meta">{session.session_type} · {session.circuit_name}</div>
        <div class="compare-meta">{drivers}</div>
    </div>""", unsafe_allow_html=True)


def _comparison_table(result: AnalysisResult, session_b: AnalysisResult) -> pd.DataFrame:
    rows = []
    for label, source in (("A", result), ("B", session_b)):
        for driver in source.sorted_drivers:
            rows.append({
                "Sesja":    label,
                "Kierowca": driver.driver,
                "Czas":     driver.lap_time_str,
                "S1 [s]":   round(driver.sector1, 3),
                "S2 [s]":   round(driver.sector2, 3),
                "S3 [s]":   round(driver.sector3, 3),
                "Okr. #":   driver.lap_number,
                "Opona":    driver.compound,
            })
    return pd.DataFrame(rows)
