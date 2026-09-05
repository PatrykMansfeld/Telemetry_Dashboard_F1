"""
Stan sesji Streamlita w jednym miejscu.

Zamiast rozsypywać `st.session_state["..."]` po całym kodzie, wszystkie klucze
i dostęp do nich trzymamy tutaj — łatwiej wtedy prześledzić, co aplikacja
pamięta między przeładowaniami.
"""

from __future__ import annotations

import streamlit as st

from f1tele.config import DEFAULT_PLOT_THEME
from f1tele.pipeline import AnalysisResult

# ── Klucze session_state ─────────────────────────────────────────────────────
THEME             = "theme"
RESULT            = "result"
SESSION_B         = "session_b"
AVAILABLE_DRIVERS = "available_drivers"
DRIVER_DETAILS    = "driver_details"
AVAILABLE_B       = "available_drivers_b"
SHOW_SCHEDULE     = "show_schedule"
SCHEDULE_YEAR     = "schedule_year"
DRIVERS_STALE     = "_drivers_stale"
THEME_PROBED      = "_theme_probed"

_ANIMATION_PREFIX = "animation_"
_ANALYSIS_CACHE   = "_analysis_cache"

# Ile ostatnich analiz trzymamy w pamięci sesji.
CACHE_ENTRIES = 4

THEMES = ("dark", "light")


# ── Motyw ────────────────────────────────────────────────────────────────────
def streamlit_theme() -> str:
    """
    Motyw, w którym Streamlit rysuje własne widgety (tabele, pola formularzy).

    Wynika z ustawienia przeglądarki albo z menu ⋮ → Settings → Appearance;
    Python nie może go zmienić w trakcie sesji, więc to my się do niego dopasowujemy.
    """
    return _detected_theme() or DEFAULT_PLOT_THEME


def _detected_theme() -> str | None:
    """Motyw zgłoszony przez przeglądarkę; None, gdy jeszcze nieznany."""
    try:
        detected = st.context.theme.type
    except Exception:
        return None
    return detected if detected in THEMES else None


def ensure_theme_detected() -> None:
    """
    Przy pierwszym renderze Streamlit nie zna jeszcze motywu przeglądarki
    (`st.context.theme.type` jest puste). Odświeżamy stronę raz, żeby dashboard
    nie mignął w złym motywie; flaga chroni przed pętlą, gdy motyw pozostaje nieznany.
    """
    if st.session_state.get(THEME_PROBED):
        return
    st.session_state[THEME_PROBED] = True
    if _detected_theme() is None:
        st.rerun()


def current_theme() -> str:
    """
    Motyw dashboardu i wykresów.

    Domyślnie zgodny ze Streamlitem — dzięki temu tabele, kontrolki i wykresy
    wyglądają spójnie. Przycisk w nagłówku ustawia własną wartość na tę sesję.
    """
    return st.session_state.get(THEME) or streamlit_theme()


def toggle_theme() -> None:
    """Przełącza motyw jasny <-> ciemny (nadpisuje motyw Streamlita)."""
    st.session_state[THEME] = "light" if current_theme() == "dark" else "dark"


# ── Wyniki analizy ───────────────────────────────────────────────────────────
def get_result() -> AnalysisResult | None:
    return st.session_state.get(RESULT)


def set_result(result: AnalysisResult | None) -> None:
    st.session_state[RESULT] = result


def get_session_b() -> AnalysisResult | None:
    return st.session_state.get(SESSION_B)


def set_session_b(result: AnalysisResult | None) -> None:
    st.session_state[SESSION_B] = result


# ── Cache policzonych analiz ─────────────────────────────────────────────────
# Trzymamy je w stanie sesji, a nie w `st.cache_resource`: wynik zawiera żywą
# sesję FastF1 i figury Plotly, a liczeniu towarzyszy pasek postępu — cache
# Streamlita próbowałby odtwarzać te elementy i wywalał się na tym.
def cached_analysis(key: tuple):
    """Wcześniej policzona analiza dla tych parametrów albo None."""
    return st.session_state.get(_ANALYSIS_CACHE, {}).get(key)


def store_analysis(key: tuple, result) -> None:
    """Zapamiętuje wynik, wypychając najstarszy po przekroczeniu limitu."""
    cache = st.session_state.setdefault(_ANALYSIS_CACHE, {})
    cache[key] = result
    while len(cache) > CACHE_ENTRIES:
        cache.pop(next(iter(cache)))


# ── Animacja okrążenia (kosztowna, więc cachowana per zestaw kierowców) ──────
def animation_key(drivers) -> str:
    return _ANIMATION_PREFIX + "_".join(sorted(drivers))


def get_animation(drivers):
    return st.session_state.get(animation_key(drivers))


def set_animation(drivers, fig) -> None:
    st.session_state[animation_key(drivers)] = fig


def clear_animations() -> None:
    """Czyści zapamiętane animacje — po nowej analizie są nieaktualne."""
    for key in [k for k in st.session_state if k.startswith(_ANIMATION_PREFIX)]:
        del st.session_state[key]
