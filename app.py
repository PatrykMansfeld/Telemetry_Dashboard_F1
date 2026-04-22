"""
F1 Telemetria — frontend Streamlit.
Uruchom: streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="F1 Telemetria",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "**F1 Telemetria** — analiza stylu jazdy kierowców F1\nPowered by FastF1",
    },
)

# ── Motyw ─────────────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

theme = st.session_state["theme"]

from ui.styles import get_css
st.markdown(get_css(theme), unsafe_allow_html=True)

from ui.sidebar import render_sidebar
from ui.welcome import render_welcome
from ui.analysis import run_main_analysis, run_session_b_analysis
from ui.tabs import render_tabs


@st.cache_resource(show_spinner=False)
def _import_modules():
    """Lazy import modułów projektu (FastF1 wolno się ładuje)."""
    from f1tele.data_loader import (
        load_session, load_drivers_data,
        get_available_sessions,
        get_session_drivers_list,
        get_race_pace_data,
        get_weather_data,
        get_position_data,
    )
    from f1tele.corner_analysis import run_corner_analysis
    from f1tele.sector_analysis import compute_mini_sectors, compute_sector_stats
    from f1tele.driver_style import (
        compute_style_fingerprint, normalize_fingerprints,
        METRIC_LABELS, METRIC_FIELDS,
    )
    from f1tele.plots_interactive import (
        plot_telemetry_interactive,
        plot_corners_interactive,
        plot_mini_sector_dominance_interactive,
        plot_sector_heatmap_interactive,
        plot_radar_interactive,
        plot_style_bars_interactive,
        plot_driver_dominance_map_interactive,
        plot_speed_heatmap_track_interactive,
        plot_gear_map_interactive,
        plot_race_pace_interactive,
        plot_track_animation_interactive,
        plot_weather_interactive,
        plot_tire_degradation_interactive,
        plot_sector_colors_interactive,
        plot_drs_interactive,
        plot_delta_time_interactive,
        plot_braking_points_interactive,
        plot_position_interactive,
        plot_stint_overview_interactive,
    )
    return {
        "load_session":                            load_session,
        "load_drivers_data":                       load_drivers_data,
        "get_available_sessions":                  get_available_sessions,
        "get_session_drivers_list":                get_session_drivers_list,
        "get_race_pace_data":                      get_race_pace_data,
        "get_weather_data":                        get_weather_data,
        "get_position_data":                       get_position_data,
        "run_corner_analysis":                     run_corner_analysis,
        "compute_mini_sectors":                    compute_mini_sectors,
        "compute_sector_stats":                    compute_sector_stats,
        "compute_style_fingerprint":               compute_style_fingerprint,
        "normalize_fingerprints":                  normalize_fingerprints,
        "METRIC_LABELS":                           METRIC_LABELS,
        "METRIC_FIELDS":                           METRIC_FIELDS,
        "plot_telemetry_interactive":              plot_telemetry_interactive,
        "plot_corners_interactive":                plot_corners_interactive,
        "plot_mini_sector_dominance_interactive":  plot_mini_sector_dominance_interactive,
        "plot_sector_heatmap_interactive":         plot_sector_heatmap_interactive,
        "plot_radar_interactive":                  plot_radar_interactive,
        "plot_style_bars_interactive":             plot_style_bars_interactive,
        "plot_driver_dominance_map_interactive":   plot_driver_dominance_map_interactive,
        "plot_speed_heatmap_track_interactive":    plot_speed_heatmap_track_interactive,
        "plot_gear_map_interactive":               plot_gear_map_interactive,
        "plot_race_pace_interactive":              plot_race_pace_interactive,
        "plot_track_animation_interactive":        plot_track_animation_interactive,
        "plot_weather_interactive":                plot_weather_interactive,
        "plot_tire_degradation_interactive":       plot_tire_degradation_interactive,
        "plot_sector_colors_interactive":          plot_sector_colors_interactive,
        "plot_drs_interactive":                    plot_drs_interactive,
        "plot_delta_time_interactive":             plot_delta_time_interactive,
        "plot_braking_points_interactive":         plot_braking_points_interactive,
        "plot_position_interactive":               plot_position_interactive,
        "plot_stint_overview_interactive":         plot_stint_overview_interactive,
    }


# ── Hero + przełącznik motywu ─────────────────────────────────────────────────
hero_col, theme_col = st.columns([11, 1])
with hero_col:
    st.markdown("""
    <div class="hero fade-in">
        <div class="hero-stripe"></div>
        <div class="hero-icon">🏎</div>
        <div class="hero-text">
            <div class="hero-title">F1 Telemetria</div>
            <div class="hero-sub">Analiza stylu jazdy kierowców &nbsp;·&nbsp; FastF1</div>
        </div>
        <div class="hero-tag">Live analytics</div>
    </div>
    """, unsafe_allow_html=True)
with theme_col:
    st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
    _icon = "☀️ Jasny" if theme == "dark" else "🌙 Ciemny"
    if st.button(_icon, help="Zmień motyw (jasny / ciemny)", use_container_width=True):
        st.session_state["theme"] = "light" if theme == "dark" else "dark"
        st.rerun()

# ── Kontrolki ─────────────────────────────────────────────────────────────────
sidebar = render_sidebar(_import_modules)

if sidebar["custom_drivers"].strip():
    final_drivers = [d.strip().upper() for d in sidebar["custom_drivers"].split(",") if d.strip()]
else:
    final_drivers = list(sidebar["drivers_multiselect"])

# ── Harmonogram ───────────────────────────────────────────────────────────────
if st.session_state.get("show_schedule"):
    sch_year = st.session_state.get("schedule_year", sidebar["year"])
    with st.spinner(f"Pobieranie harmonogramu {sch_year}..."):
        try:
            mods = _import_modules()
            df = mods["get_available_sessions"](sch_year)
            if not df.empty:
                st.subheader(f"📅 Sezon F1 {sch_year}")
                st.dataframe(
                    df.rename(columns={
                        "RoundNumber": "Runda",
                        "EventName":   "GP",
                        "Location":    "Miasto",
                        "Country":     "Kraj",
                        "EventDate":   "Data",
                    }),
                    use_container_width=True, hide_index=True,
                )
        except Exception as e:
            st.error(f"Błąd pobierania harmonogramu: {e}")
    st.session_state["show_schedule"] = False

# ── Ładowanie sesji B ─────────────────────────────────────────────────────────
if sidebar["run_b_btn"]:
    run_session_b_analysis(
        sidebar["year_b"], sidebar["round_b"],
        sidebar["session_b_type"], sidebar["drivers_b"],
        _import_modules,
    )

# ── Główna analiza ────────────────────────────────────────────────────────────
if sidebar["run_btn"]:
    run_main_analysis(
        year=sidebar["year"],
        round_input=sidebar["round_input"],
        session_type=sidebar["session_type"],
        final_drivers=final_drivers,
        mini_sects=sidebar["mini_sects"],
        mods_cfg=sidebar["mods"],
        import_modules_fn=_import_modules,
    )

# ── Wyświetlanie wyników ──────────────────────────────────────────────────────
results = st.session_state.get("results")
if results is None:
    render_welcome()
    st.stop()

render_tabs(results, st.session_state.get("session_b"), _import_modules)
