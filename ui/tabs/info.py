"""Zakładka „Info” — co się wygenerowało, a co nie."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from f1tele.pipeline import AnalysisResult

from ..components import subheader, table


def render(result: AnalysisResult, session_b: AnalysisResult | None) -> None:
    subheader("Wygenerowane wykresy")
    if result.figures:
        st.success(f"✅ {len(result.figures)} interaktywnych wykresów.")
        table(pd.DataFrame({"Wykres": sorted(result.figures)}), max_height=320)
    else:
        st.info("Brak wygenerowanych wykresów.")

    if result.warnings:
        subheader("Pominięte moduły")
        st.warning("Poniższe wykresy nie powstały — reszta analizy jest kompletna.")
        table(pd.DataFrame({"Szczegóły": result.warnings}))

    subheader("Sesja")
    session = result.session
    st.info(f"**{session.label}** | {session.circuit_name}, {session.country} "
            f"— runda {session.round_number}, kierowców: {len(result.drivers)}")

    if session_b is not None:
        subheader("Sesja B")
        b = session_b.session
        st.info(f"**{b.label}** | {b.circuit_name}, {b.country} "
                f"— kierowców: {len(session_b.drivers)}")
