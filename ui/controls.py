"""
Panel sterowania w sidebarze.

Sidebar odpowiada za „co analizujemy”, główna kolumna za „co z tego wyszło”.
Dzięki temu po uruchomieniu analizy wyniki są od razu na wierzchu, a panel
można zwinąć jednym kliknięciem.

`render_controls()` zwraca `ControlState` z gotowymi wartościami — lista
kierowców jest już rozwiązana (ręczny wpis nadpisuje wybór z listy), więc
`app.py` nie musi niczego dopowiadać.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st

from f1tele.config import (
    DEFAULT_DRIVERS,
    DEFAULT_MINI_SECTS,
    DEFAULT_ROUND,
    DEFAULT_SESSION,
    DEFAULT_YEAR,
    MAX_DRIVERS,
    MAX_YEAR,
    MIN_YEAR,
)
from f1tele.data_loader import get_session_drivers_list
from f1tele.pipeline import Modules

from . import state
from .constants import KNOWN_DRIVERS, SESSION_LABELS, SESSIONS, max_round_for_year

_MODULES_KEY = "_selected_modules"

MODULE_LABELS = {
    "telemetry": "Telemetria",
    "corners":   "Zakręty",
    "sectors":   "Sektory",
    "style":     "Styl jazdy",
    "track":     "Mapa toru",
    "race_pace": "Race pace",
    "weather":   "Pogoda",
}


@dataclass
class ControlState:
    """Odczyt panelu po jednym przebiegu renderowania."""
    year: int
    round_number: int
    session_type: str
    drivers: list[str]
    mini_sectors: int
    modules: Modules
    run: bool

    year_b: int
    round_b: int
    session_b_type: str
    drivers_b: list[str] = field(default_factory=list)
    run_b: bool = False

    # None = najszybsze okrążenie każdego kierowcy
    lap_number: int | None = None


def _section(label: str) -> None:
    st.markdown(f'<div class="side-section">{label}</div>', unsafe_allow_html=True)


def _mark_drivers_stale() -> None:
    """Zmiana parametrów sesji unieważnia listę kierowców."""
    st.session_state[state.DRIVERS_STALE] = True


def _fetch_drivers(year: int, round_number: int, session_type: str,
                   into: str, details_key: str | None = None) -> int:
    """Pobiera skład sesji do `session_state`; zwraca liczbę kierowców."""
    drivers = get_session_drivers_list(year, round_number, session_type)
    st.session_state[into] = [d["abbr"] for d in drivers]
    if details_key:
        st.session_state[details_key] = {d["abbr"]: d for d in drivers}
    return len(drivers)


def _session_picker(key_prefix: str, *, default_year: int, default_round: int,
                    on_change=None) -> tuple[int, int, str]:
    """Rok i runda obok siebie, typ sesji pod spodem — mieści się w sidebarze."""
    col_year, col_round = st.columns(2)
    with col_year:
        year = st.number_input(
            "Rok", min_value=MIN_YEAR, max_value=MAX_YEAR, value=default_year,
            step=1, key=f"{key_prefix}_year", on_change=on_change,
        )
    with col_round:
        max_r = max_round_for_year(year)
        # Sezony różnią się liczbą rund — po zmianie roku przycinamy zapamiętaną
        # wartość, inaczej widget dostałby liczbę spoza swojego zakresu.
        round_key = f"{key_prefix}_round"
        if st.session_state.get(round_key, 0) > max_r:
            st.session_state[round_key] = max_r
        round_number = st.number_input(
            f"Runda (1–{max_r})", min_value=1, max_value=max_r,
            value=min(default_round, max_r), step=1,
            key=round_key, on_change=on_change,
        )
    session_type = st.selectbox(
        "Typ sesji", SESSIONS, index=SESSIONS.index(DEFAULT_SESSION),
        format_func=lambda s: SESSION_LABELS.get(s, s),
        key=f"{key_prefix}_type", on_change=on_change,
    )
    return int(year), int(round_number), session_type


def _driver_picker(available: list[str]) -> list[str]:
    """Wybór kierowców z listy albo ręcznie wpisanymi kodami."""
    picked = st.multiselect(
        "Kierowcy", options=available,
        default=[d for d in DEFAULT_DRIVERS if d in available],
        max_selections=MAX_DRIVERS,
        label_visibility="collapsed",
        placeholder=f"Wybierz do {MAX_DRIVERS} kierowców",
    )
    manual = st.text_input(
        "Albo wpisz kody ręcznie", placeholder="VER, HAM, NOR",
        help="Oddziel przecinkami. Nadpisuje wybór powyżej.",
    )
    if manual.strip():
        return [d.strip().upper() for d in manual.split(",") if d.strip()]
    return list(picked)


def _lap_picker() -> int | None:
    """
    Które okrążenie analizować.

    Domyślnie najszybsze każdego kierowcy. Konkretny numer pozwala porównać
    np. przejazd na świeżej i zużytej oponie w tym samym wyścigu.
    """
    mode = st.radio(
        "Okrążenie", ["Najszybsze", "Wybrany numer"],
        horizontal=True, label_visibility="collapsed",
        help="„Najszybsze” bierze najlepsze okrążenie każdego kierowcy osobno.",
    )
    if mode == "Najszybsze":
        return None
    return int(st.number_input("Numer okrążenia", min_value=1, max_value=80,
                               value=1, step=1))


def _driver_details() -> None:
    """Pełne nazwiska pobranego składu — pomaga, gdy kody nic nie mówią."""
    details = st.session_state.get(state.DRIVER_DETAILS) or {}
    if not details or not next(iter(details.values())).get("full_name"):
        return
    with st.expander(f"Skład sesji ({len(details)})", expanded=False):
        for abbr, info in details.items():
            st.caption(f"**{abbr}** · {info['full_name']}")


def _modules_picker() -> Modules:
    """Domyślnie liczymy wszystko; wyłączanie modułów skraca czas analizy."""
    stored = st.session_state.get(_MODULES_KEY, list(MODULE_LABELS))
    with st.expander(f"Moduły analizy ({len(stored)}/{len(MODULE_LABELS)})", expanded=False):
        st.caption("Odznacz to, czego nie potrzebujesz — analiza policzy się szybciej.")
        selected = [
            key for key in MODULE_LABELS
            if st.checkbox(MODULE_LABELS[key], value=key in stored, key=f"mod_{key}")
        ]
    st.session_state[_MODULES_KEY] = selected
    return Modules(**{key: key in selected for key in MODULE_LABELS})


def render_controls() -> ControlState:
    """Renderuje sidebar i zwraca odczytane ustawienia."""
    with st.sidebar:
        _section("Sesja")
        year, round_number, session_type = _session_picker(
            "a", default_year=DEFAULT_YEAR, default_round=int(DEFAULT_ROUND),
            on_change=_mark_drivers_stale,
        )

        # Zmiana parametrów sesji automatycznie odświeża skład kierowców.
        if st.session_state.pop(state.DRIVERS_STALE, False):
            with st.spinner("Aktualizacja składu..."):
                try:
                    _fetch_drivers(year, round_number, session_type,
                                   state.AVAILABLE_DRIVERS, state.DRIVER_DETAILS)
                except Exception:
                    pass  # brak sieci lub sesji — zostaje poprzednia lista

        _section("Kierowcy")
        available = st.session_state.get(state.AVAILABLE_DRIVERS, KNOWN_DRIVERS)
        drivers = _driver_picker(available)
        lap_number = _lap_picker()

        if st.button("Pobierz skład z sesji", width="stretch"):
            with st.spinner("Pobieranie składu..."):
                try:
                    found = _fetch_drivers(year, round_number, session_type,
                                           state.AVAILABLE_DRIVERS, state.DRIVER_DETAILS)
                    st.success(f"Znaleziono {found} kierowców.")
                except Exception as exc:
                    st.error(f"Nie udało się pobrać składu: {exc}")
        _driver_details()

        _section("Opcje")
        mini_sectors = st.slider("Liczba mini-sektorów", 10, 50, DEFAULT_MINI_SECTS, step=5)
        modules = _modules_picker()

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        run = st.button("▶  Uruchom analizę", width="stretch", type="primary")

        _section("Więcej")
        with st.expander("Porównanie z drugą sesją", expanded=False):
            st.caption("Wczytaj sesję B, aby zestawić telemetrię i styl jazdy "
                       "między wyścigami lub sezonami.")
            year_b, round_b, session_b_type = _session_picker(
                "b", default_year=max(MIN_YEAR, DEFAULT_YEAR - 1),
                default_round=int(DEFAULT_ROUND),
            )

            if st.button("Pobierz skład sesji B", width="stretch", key="load_drivers_b"):
                with st.spinner("Pobieranie składu..."):
                    try:
                        found = _fetch_drivers(year_b, round_b, session_b_type,
                                               state.AVAILABLE_B)
                        st.success(f"Znaleziono {found} kierowców.")
                    except Exception as exc:
                        st.error(f"Nie udało się pobrać składu: {exc}")

            available_b = st.session_state.get(state.AVAILABLE_B, KNOWN_DRIVERS)
            drivers_b = st.multiselect(
                "Kierowcy sesji B", options=available_b,
                default=[d for d in DEFAULT_DRIVERS[:2] if d in available_b],
                max_selections=4, key="drivers_b",
            )
            run_b = st.button("Wczytaj sesję B", width="stretch", key="run_b")

        with st.expander("Harmonogram sezonu", expanded=False):
            st.caption("Podgląd kalendarza — przyda się, gdy nie pamiętasz numeru rundy.")
            if st.button(f"Pokaż kalendarz {year}", width="stretch"):
                st.session_state[state.SHOW_SCHEDULE] = True
                st.session_state[state.SCHEDULE_YEAR] = year

    return ControlState(
        year=year,
        round_number=round_number,
        session_type=session_type,
        drivers=drivers,
        mini_sectors=mini_sectors,
        modules=modules,
        run=run,
        lap_number=lap_number,
        year_b=year_b,
        round_b=round_b,
        session_b_type=session_b_type,
        drivers_b=list(drivers_b),
        run_b=run_b,
    )
