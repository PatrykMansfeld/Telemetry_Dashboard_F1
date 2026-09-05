"""Zakładka „Zakręty” — porównanie apeksów, hamowania i wyjść."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from f1tele.pipeline import AnalysisResult

from ..components import caption, chart, empty_module, subheader, table


def render(result: AnalysisResult) -> None:
    analysis = result.corners
    drawn = chart(result.figures.get("corners"))

    if analysis and analysis.corners and not analysis.is_official:
        st.warning(
            "Numeracja zakrętów pochodzi z wykrywania minimów prędkości, bo FastF1 "
            "nie udostępnił planu toru dla tej sesji. Łagodniejsze łuki mogły "
            "zostać pominięte, a numery nie muszą zgadzać się z transmisją."
        )

    if drawn and analysis and analysis.corners:
        subheader(f"Dane zakrętów ({len(analysis.corners)})")
        table(_corner_table(analysis, list(result.drivers)), max_height=420,
              download="zakrety")
        caption("„Apeks” to najniższa prędkość w zakręcie, „hamowanie” — dystans "
                "od naciśnięcia hamulca do apeksu (dłuższy = wcześniejsze hamowanie).")

    if "braking_points" in result.figures:
        subheader("Punkty hamowania per zakręt")
        drawn = chart(result.figures["braking_points"]) or drawn

    if not drawn:
        empty_module("Zakręty")


def _corner_table(analysis, drivers: list[str]) -> pd.DataFrame:
    """Apeks i długość hamowania każdego kierowcy w kolejnych zakrętach."""
    events_by_driver = {
        drv: {e.corner_id: e for e in analysis.driver_corners.get(drv, [])}
        for drv in drivers
    }
    rows = []
    for corner in analysis.corners:
        row = {
            "Zakręt":      corner.get("name", f"T{corner['id']}"),
            "Dystans [m]": f"{corner['distance']:.0f}",
        }
        for drv in drivers:
            event = events_by_driver[drv].get(corner["id"])
            row[f"{drv} apeks [km/h]"] = f"{event.apex_speed:.1f}" if event else "—"
            row[f"{drv} hamowanie [m]"] = f"{event.braking_distance:.1f}" if event else "—"
        rows.append(row)
    return pd.DataFrame(rows)
