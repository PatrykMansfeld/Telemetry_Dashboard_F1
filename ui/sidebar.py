from __future__ import annotations

import streamlit as st

from .constants import SESSIONS, SESSION_LABELS, KNOWN_DRIVERS

_MAX_ROUNDS: dict[int, int] = {
    2018: 21, 2019: 21, 2020: 17, 2021: 22,
    2022: 22, 2023: 22, 2024: 24, 2025: 24,
}


def _max_round_for_year(year: int) -> int:
    return _MAX_ROUNDS.get(year, 24)


def _mark_drv_stale() -> None:
    st.session_state["_drv_stale"] = True


def render_sidebar(import_modules_fn) -> dict:
    st.markdown('<div class="ctrl-panel fade-in">', unsafe_allow_html=True)

    # ── SESJA A ───────────────────────────────────────────────────────────────
    st.markdown('<div class="ctrl-section">⚙️ &nbsp;Sesja A</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        year = st.number_input(
            "Rok sezonu", min_value=2018, max_value=2026, value=2024, step=1,
            key="_year", on_change=_mark_drv_stale,
        )
    with col2:
        max_r = _max_round_for_year(int(year))
        current_round = st.session_state.get("_round_val", 5)
        clamped = min(int(current_round), max_r)
        round_num = st.number_input(
            f"Runda (1–{max_r})", min_value=1, max_value=max_r, value=clamped, step=1,
            key="_round_num", on_change=_mark_drv_stale,
        )
        st.session_state["_round_val"] = round_num
    with col3:
        session_type = st.selectbox(
            "Typ sesji", SESSIONS, index=0,
            format_func=lambda s: SESSION_LABELS.get(s, s),
            help="Wybierz typ sesji do analizy",
            key="_sess", on_change=_mark_drv_stale,
        )

    round_input = str(int(round_num))

    # Auto-odświeżenie kierowców przy zmianie parametrów sesji
    if st.session_state.pop("_drv_stale", False):
        with st.spinner("🔄 Aktualizacja listy kierowców..."):
            try:
                mods = import_modules_fn()
                drv_list = mods["get_session_drivers_list"](int(year), int(round_num), session_type)
                st.session_state["available_drivers"] = [d["abbr"] for d in drv_list]
                st.session_state["driver_details"]    = {d["abbr"]: d for d in drv_list}
            except Exception:
                pass

    # ── KIEROWCY ─────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="ctrl-section">👤 &nbsp;Kierowcy</div>',
        unsafe_allow_html=True,
    )

    load_drv_btn = st.button("🔄 Załaduj kierowców z sesji", use_container_width=True)
    if load_drv_btn:
        with st.spinner("Pobieranie listy kierowców..."):
            try:
                mods = import_modules_fn()
                drv_list = mods["get_session_drivers_list"](int(year), int(round_num), session_type)
                st.session_state["available_drivers"] = [d["abbr"] for d in drv_list]
                st.session_state["driver_details"]    = {d["abbr"]: d for d in drv_list}
                st.success(f"Znaleziono {len(drv_list)} kierowców.")
            except Exception as e:
                st.error(f"Błąd ładowania kierowców: {e}")

    available_drivers = st.session_state.get("available_drivers", KNOWN_DRIVERS)

    if "driver_details" in st.session_state:
        details = st.session_state["driver_details"]
        if details:
            sample = next(iter(details.values()))
            if sample.get("full_name"):
                with st.expander("ℹ️ Kierowcy w sesji", expanded=False):
                    cols_d = st.columns(3)
                    for i, (abbr, info) in enumerate(details.items()):
                        with cols_d[i % 3]:
                            st.caption(f"**{abbr}** — {info['full_name']}")

    col_ms, col_ci = st.columns([3, 2])
    with col_ms:
        drivers_multiselect = st.multiselect(
            "Wybierz kierowców",
            options=available_drivers,
            default=[d for d in ["VER", "NOR", "LEC"] if d in available_drivers],
            max_selections=6,
            help="Wybierz 2–6 kierowców do porównania",
        )
    with col_ci:
        custom_drivers = st.text_input(
            "Lub wpisz kody ręcznie",
            placeholder="VER,HAM,NOR",
            help="Oddziel przecinkami. Nadpisuje wybór.",
        )

    # ── OPCJE ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<div class="ctrl-section">🔧 &nbsp;Opcje</div>',
        unsafe_allow_html=True,
    )

    mini_sects = st.slider("Mini-sektory", 10, 50, 25, step=5)

    with st.expander("Moduły analizy", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            mod_telemetry = st.checkbox("📈 Telemetria",  value=True)
            mod_corners   = st.checkbox("🔄 Zakręty",     value=True)
        with c2:
            mod_sectors   = st.checkbox("🏁 Sektory",     value=True)
            mod_style     = st.checkbox("🎯 Styl jazdy",  value=True)
        with c3:
            mod_track     = st.checkbox("🗺️ Mapa toru",  value=True)
            mod_race_pace = st.checkbox("🏎 Race pace",   value=True)
        with c4:
            mod_weather   = st.checkbox("☁️ Pogoda",       value=True)

    st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
    run_btn = st.button("🚀 URUCHOM ANALIZĘ", use_container_width=True, type="primary")

    # ── HARMONOGRAM ───────────────────────────────────────────────────────────
    st.markdown(
        '<div class="ctrl-section">📅 &nbsp;Harmonogram</div>',
        unsafe_allow_html=True,
    )
    if st.button("Pokaż harmonogram sezonu", use_container_width=True):
        st.session_state["show_schedule"] = True
        st.session_state["schedule_year"] = int(year)

    # ── SESJA B — CROSS-SESSION ───────────────────────────────────────────────
    st.markdown("<div style='margin-top:4px'></div>", unsafe_allow_html=True)
    with st.expander("🔀 Porównanie sesji (Cross-session)", expanded=False):
        st.caption(
            "Załaduj drugą sesję, aby porównać telemetrię i styl jazdy między GP / latami."
        )
        cb1, cb2, cb3 = st.columns([2, 2, 3])
        with cb1:
            year_b = st.number_input(
                "Rok B", min_value=2018, max_value=2026, value=2023, step=1, key="year_b",
            )
        with cb2:
            max_rb = _max_round_for_year(int(year_b))
            round_b_num = st.number_input(
                f"Runda B (1–{max_rb})", min_value=1, max_value=max_rb, value=min(5, max_rb),
                step=1, key="round_b_num",
            )
        with cb3:
            session_b_type = st.selectbox(
                "Typ sesji B", SESSIONS, index=0, key="sess_b",
                format_func=lambda s: SESSION_LABELS.get(s, s),
            )

        round_b = str(int(round_b_num))

        load_drv_b_btn = st.button(
            "🔄 Załaduj kierowców sesji B", use_container_width=True, key="load_b_drv",
        )
        if load_drv_b_btn:
            with st.spinner("Pobieranie kierowców sesji B..."):
                try:
                    mods = import_modules_fn()
                    drv_list_b = mods["get_session_drivers_list"](int(year_b), int(round_b_num), session_b_type)
                    st.session_state["available_drivers_b"] = [d["abbr"] for d in drv_list_b]
                    st.success(f"Znaleziono {len(drv_list_b)} kierowców.")
                except Exception as e:
                    st.error(f"Błąd: {e}")

        available_b = st.session_state.get("available_drivers_b", KNOWN_DRIVERS)
        drivers_b = st.multiselect(
            "Kierowcy sesji B",
            options=available_b,
            default=[d for d in ["VER", "NOR"] if d in available_b],
            max_selections=4,
            key="drv_b",
        )
        run_b_btn = st.button("➕ Załaduj sesję B", use_container_width=True, key="run_b")

    st.markdown('</div>', unsafe_allow_html=True)

    return {
        "year":               int(year),
        "round_input":        round_input,
        "session_type":       session_type,
        "drivers_multiselect": drivers_multiselect,
        "custom_drivers":     custom_drivers,
        "mini_sects":         mini_sects,
        "mods": {
            "telemetry":  mod_telemetry,
            "corners":    mod_corners,
            "sectors":    mod_sectors,
            "style":      mod_style,
            "track":      mod_track,
            "race_pace":  mod_race_pace,
            "weather":    mod_weather,
        },
        "run_btn":        run_btn,
        "year_b":         int(year_b),
        "round_b":        round_b,
        "session_b_type": session_b_type,
        "drivers_b":      drivers_b,
        "run_b_btn":      run_b_btn,
    }
