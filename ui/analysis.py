"""
Uruchamianie analizy z poziomu interfejsu.

Cała logika siedzi w `f1tele.pipeline` — tutaj zostaje to, co należy do
Streamlita: pasek postępu, komunikaty i zapis wyniku w stanie sesji.

Wyniki cache'ujemy po parametrach analizy (patrz `state.cached_analysis`), więc
powrót do policzonej wcześniej sesji jest natychmiastowy.
"""

from __future__ import annotations

import traceback

import streamlit as st

from f1tele.pipeline import (
    AnalysisRequest,
    Modules,
    load_comparison_session,
    run_analysis,
)

from . import state
from .controls import ControlState


def run_main_analysis(controls: ControlState) -> None:
    """Uruchamia analizę sesji A i zapisuje wynik w stanie sesji."""
    if not controls.drivers:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę!")
        return

    request = AnalysisRequest(
        year=controls.year,
        round_number=controls.round_number,
        session_type=controls.session_type,
        drivers=controls.drivers,
        mini_sectors=controls.mini_sectors,
        modules=controls.modules,
        theme=state.current_theme(),
        lap_number=controls.lap_number,
    )

    state.set_result(None)
    state.clear_animations()

    key = request.cache_key()
    cached = state.cached_analysis(key)
    if cached is not None:
        cached.theme = request.theme
        state.set_result(cached)
        st.toast(f"Wczytano z pamięci — {len(cached.figures)} wykresów", icon="⚡")
        return

    progress = st.progress(0, text="Ładowanie sesji...")
    status = st.empty()

    def on_progress(pct: int, text: str) -> None:
        progress.progress(pct, text=text)
        status.info(text)

    try:
        result = run_analysis(request, on_progress=on_progress)
    except ValueError as exc:
        progress.empty()
        status.empty()
        st.error(f"❌ {exc}")
        return
    except Exception:
        progress.empty()
        status.empty()
        st.error("❌ Błąd podczas analizy:")
        st.code(traceback.format_exc(), language="python")
        return

    progress.empty()
    status.empty()

    result.theme = request.theme
    state.store_analysis(key, result)
    state.set_result(result)

    # Wynik widać na ekranie — wystarczy krótkie potwierdzenie, bez paska,
    # który zajmowałby miejsce nad wykresami.
    message = f"Gotowe — {len(result.figures)} wykresów"
    if result.warnings:
        message += f", {len(result.warnings)} pominięto (szczegóły w zakładce Info)"
    st.toast(message, icon="✅")


def run_session_b_analysis(controls: ControlState) -> None:
    """Ładuje drugą sesję do porównania cross-session."""
    if not controls.drivers_b:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę dla sesji B!")
        return

    progress = st.progress(0, text="Ładowanie sesji B...")
    status = st.empty()
    try:
        status.info(f"📡 Sesja B: {controls.year_b} GP#{controls.round_b} "
                    f"[{controls.session_b_type}]")
        session_b = load_comparison_session(
            controls.year_b, controls.round_b,
            controls.session_b_type, controls.drivers_b,
        )
    except ValueError as exc:
        progress.empty()
        status.empty()
        st.error(f"❌ {exc}")
        return
    except Exception:
        progress.empty()
        status.empty()
        st.error("❌ Błąd ładowania sesji B:")
        st.code(traceback.format_exc(), language="python")
        return

    progress.empty()
    status.empty()
    state.set_session_b(session_b)
    st.toast(f"Sesja B: {session_b.session.label}", icon="✅")


__all__ = ["run_main_analysis", "run_session_b_analysis", "Modules"]
