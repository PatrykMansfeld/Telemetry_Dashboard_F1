"""Zakładka „Styl jazdy” — radar, słupki i tabela metryk."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from f1tele.driver_style import (
    METRIC_FIELDS,
    METRIC_LABELS,
    METRIC_UNITS,
    MIN_DRIVERS_FOR_SCALE,
)
from f1tele.pipeline import AnalysisResult

from ..components import caption, chart, empty_module, subheader, table


def render(result: AnalysisResult) -> None:
    radar = result.figures.get("radar")
    bars = result.figures.get("style_bars")

    if radar is not None or bars is not None:
        col_radar, col_bars = st.columns([1, 1])
        with col_radar:
            if radar is not None:
                subheader("Radar stylu jazdy")
                chart(radar)
        with col_bars:
            if bars is not None:
                subheader("Porównanie metryk")
                chart(bars)

    if not result.fingerprints:
        if radar is None and bars is None:
            empty_module("Styl jazdy")
        return

    if len(result.fingerprints) < MIN_DRIVERS_FOR_SCALE:
        st.warning(
            "Przy dwóch kierowcach skala 0–100 zawsze rozciąga się na całą oś: "
            "lepszy dostaje 100, drugi 0, nawet gdy różnica jest śladowa. "
            "Czytaj ją jako kolejność, a rzeczywistą różnicę bierz z kolumn "
            "z wartościami surowymi poniżej."
        )

    subheader("Metryki stylu jazdy")
    table(_metric_table(result.fingerprints), download="styl_jazdy")
    caption("Kolumna „skala” to wartość względna w tym zestawieniu (100 = najwyższa "
            "w grupie), obok niej wartość surowa w jednostkach fizycznych. "
            "★ oznacza najwyższy wynik danej metryki.")


def _metric_table(fingerprints) -> pd.DataFrame:
    """Metryka w wierszu, kierowca w kolumnie: skala 0–100 plus wartość surowa."""
    rows = []
    for label, field, unit in zip(METRIC_LABELS, METRIC_FIELDS, METRIC_UNITS):
        scaled = [getattr(fp, field) for fp in fingerprints]
        best = max(scaled)
        row = {"Metryka": label.replace("\n", " "), "Jednostka": unit}
        for fp, value in zip(fingerprints, scaled):
            raw = fp.raw_metrics.get(field, 0.0)
            mark = "★ " if value == best else ""
            row[f"{fp.driver} skala"] = f"{mark}{value:.0f}"
            row[f"{fp.driver} wartość"] = f"{raw:.1f}"
        rows.append(row)
    return pd.DataFrame(rows)
