from __future__ import annotations

import streamlit as st

from .constants import SESSIONS, SESSION_LABELS, KNOWN_DRIVERS


def _mark_drv_stale() -> None:
    st.session_state["_drv_stale"] = True


def render_sidebar(import_modules_fn) -> dict:
    with st.sidebar:
        st.markdown("""
        <div class="sb-brand fade-in">
            <div class="sb-brand-icon">🏎</div>
            <div>
                <div class="sb-brand-title">F1 Telemetria</div>
                <div class="sb-brand-sub">Analiza danych</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── SESJA A ───────────────────────────────────────────────────────────
        st.markdown('<div class="sb-section">⚙️ &nbsp;Sesja A</div>', unsafe_allow_html=True)
        year = st.number_input(
            "Rok sezonu", min_value=2018, max_value=2026, value=2024, step=1,
            key="_year", on_change=_mark_drv_stale,
        )
        round_input = st.text_input(
            "Runda", value="5", placeholder="nr lub nazwa GP",
            help="Wpisz numer rundy (np. 5) lub nazwę GP (np. Monaco, Bahrain)",
            key="_round", on_change=_mark_drv_stale,
        )
        session_type = st.selectbox(
            "Typ sesji", SESSIONS, index=0,
            format_func=lambda s: SESSION_LABELS.get(s, s),
            help="Wybierz typ sesji do analizy",
            key="_sess", on_change=_mark_drv_stale,
        )

        # Auto-odświeżenie kierowców przy zmianie parametrów sesji
        if st.session_state.pop("_drv_stale", False) and round_input.strip():
            with st.spinner("🔄 Aktualizacja listy kierowców..."):
                try:
                    mods = import_modules_fn()
                    try:
                        rv_auto = int(round_input.strip())
                    except ValueError:
                        rv_auto = round_input.strip()
                    drv_list = mods["get_session_drivers_list"](year, rv_auto, session_type)
                    st.session_state["available_drivers"] = [d["abbr"] for d in drv_list]
                    st.session_state["driver_details"]    = {d["abbr"]: d for d in drv_list}
                except Exception:
                    pass

        # ── KIEROWCY ─────────────────────────────────────────────────────────
        st.markdown(
            '<div class="sb-section" style="margin-top:16px">👤 &nbsp;Kierowcy</div>',
            unsafe_allow_html=True,
        )

        load_drv_btn = st.button("🔄 Załaduj kierowców z sesji", use_container_width=True)
        if load_drv_btn:
            with st.spinner("Pobieranie listy kierowców..."):
                try:
                    mods = import_modules_fn()
                    try:
                        rv = int(round_input.strip())
                    except ValueError:
                        rv = round_input.strip()
                    drv_list = mods["get_session_drivers_list"](year, rv, session_type)
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
                        for abbr, info in details.items():
                            st.caption(f"**{abbr}** — {info['full_name']}  ·  {info['team']}")

        drivers_multiselect = st.multiselect(
            "Wybierz kierowców",
            options=available_drivers,
            default=[d for d in ["VER", "NOR", "LEC"] if d in available_drivers],
            max_selections=6,
            help="Wybierz 2–6 kierowców do porównania",
        )
        custom_drivers = st.text_input(
            "Lub wpisz kody ręcznie",
            placeholder="VER,HAM,NOR — nadpisuje wybór",
            help="Oddziel przecinkami. Nadpisuje wybór powyżej.",
        )

        # ── OPCJE ─────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="sb-section" style="margin-top:16px">🔧 &nbsp;Opcje</div>',
            unsafe_allow_html=True,
        )
        mini_sects = st.slider("Mini-sektory", 10, 50, 25, step=5)
        with st.expander("Moduły analizy", expanded=False):
            mod_telemetry = st.checkbox("📈 Telemetria",  value=True)
            mod_corners   = st.checkbox("🔄 Zakręty",     value=True)
            mod_sectors   = st.checkbox("🏁 Sektory",     value=True)
            mod_style     = st.checkbox("🎯 Styl jazdy",  value=True)
            mod_track     = st.checkbox("🗺️ Mapa toru",  value=True)
            mod_race_pace = st.checkbox("🏎 Race pace",   value=True)
            mod_weather   = st.checkbox("☁️ Pogoda",       value=True)

        st.markdown("<div style='margin-top:18px'></div>", unsafe_allow_html=True)
        run_btn = st.button("🚀 URUCHOM ANALIZĘ", use_container_width=True, type="primary")

        # ── HARMONOGRAM ───────────────────────────────────────────────────────
        st.markdown(
            '<div class="sb-section" style="margin-top:20px">📅 &nbsp;Harmonogram</div>',
            unsafe_allow_html=True,
        )
        if st.button("Pokaż sezon", use_container_width=True):
            st.session_state["show_schedule"] = True
            st.session_state["schedule_year"] = year

        # ── SESJA B — CROSS-SESSION ───────────────────────────────────────────
        st.markdown("<hr>", unsafe_allow_html=True)
        with st.expander("🔀 Porównanie sesji (Cross-session)", expanded=False):
            st.caption(
                "Załaduj drugą sesję, aby porównać telemetrię i styl jazdy między GP / latami."
            )
            year_b = st.number_input(
                "Rok B", min_value=2018, max_value=2026, value=2023, step=1, key="year_b",
            )
            round_b = st.text_input(
                "Runda B", value="5", placeholder="nr lub nazwa GP", key="round_b",
            )
            session_b_type = st.selectbox(
                "Typ sesji B", SESSIONS, index=0, key="sess_b",
                format_func=lambda s: SESSION_LABELS.get(s, s),
            )

            load_drv_b_btn = st.button(
                "🔄 Załaduj kierowców sesji B", use_container_width=True, key="load_b_drv",
            )
            if load_drv_b_btn:
                with st.spinner("Pobieranie kierowców sesji B..."):
                    try:
                        mods = import_modules_fn()
                        try:
                            rv_b = int(round_b.strip())
                        except ValueError:
                            rv_b = round_b.strip()
                        drv_list_b = mods["get_session_drivers_list"](year_b, rv_b, session_b_type)
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

    return {
        "year":               year,
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
        "year_b":         year_b,
        "round_b":        round_b,
        "session_b_type": session_b_type,
        "drivers_b":      drivers_b,
        "run_b_btn":      run_b_btn,
    }
