"""Zakładka „Race Pace” — tempo wyścigu, opony, stinty i pozycje."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from f1tele.pipeline import AnalysisResult

from ..components import chart, empty_module, subheader, table

PACE_STATS = {
    "mean":   "Śr. [s]",
    "median": "Mediana [s]",
    "std":    "Odch. std [s]",
    "min":    "Najszybsze [s]",
    "count":  "Okrążeń",
}


def render(result: AnalysisResult) -> None:
    figures = result.figures
    drawn = chart(figures.get("race_pace"))

    if not result.race_pace.empty:
        subheader("Statystyki tempa")
        table(_pace_stats(result.race_pace), download="tempo_wyscigu")
        drawn = True

    if "tire_degradation" in figures:
        subheader("Degradacja opon per stint")
        chart(figures["tire_degradation"])

    if "stint_overview" in figures:
        subheader("Podział na stinty")
        chart(figures["stint_overview"])

    if "positions" in figures:
        subheader("Pozycje w wyścigu")
        chart(figures["positions"])
        drawn = True

    if not drawn:
        if result.session.session_type != "Wyścig":
            st.info(
                "ℹ️ Race Pace jest miarodajny głównie dla sesji wyścigowych. "
                f"Aktualna sesja: **{result.session.session_type}** — "
                "brak wystarczającej liczby porównywalnych okrążeń."
            )
        else:
            empty_module("Race Pace")


def _pace_stats(race_pace: pd.DataFrame) -> pd.DataFrame:
    """Rozrzut czasów okrążeń per kierowca."""
    return (race_pace.groupby("Driver")["LapTime_s"]
            .agg(list(PACE_STATS))
            .rename(columns=PACE_STATS)
            .round(3)
            .reset_index()
            .rename(columns={"Driver": "Kierowca"})
            .sort_values("Śr. [s]"))
