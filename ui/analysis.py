from __future__ import annotations

import traceback

import pandas as pd
import streamlit as st


def run_main_analysis(
    year: int,
    round_input: str,
    session_type: str,
    final_drivers: list[str],
    mini_sects: int,
    mods_cfg: dict,
    import_modules_fn,
) -> None:
    if not final_drivers:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę!")
        st.stop()

    try:
        round_val: int | str = int(round_input.strip())
    except ValueError:
        round_val = round_input.strip()

    st.session_state["params"] = {
        "year": year, "round": round_val, "session": session_type,
        "drivers": final_drivers, "mini_sects": mini_sects,
        "mods": mods_cfg,
    }
    st.session_state["results"] = None
    for key in list(st.session_state.keys()):
        if key.startswith("plot_"):
            del st.session_state[key]

    progress = st.progress(0, text="Ładowanie sesji...")
    status   = st.empty()

    try:
        mods = import_modules_fn()

        status.info(f"📡 Ładowanie sesji: **{year} GP#{round_val} [{session_type}]**")
        session_data = mods["load_session"](year, round_val, session_type, verbose=False)
        progress.progress(15, text="Sesja załadowana...")

        status.info(f"🔄 Pobieranie telemetrii dla: **{', '.join(final_drivers)}**")
        drivers_data = mods["load_drivers_data"](session_data, final_drivers)
        progress.progress(35, text="Telemetria pobrana...")

        if not drivers_data:
            status.empty(); progress.empty()
            st.error("❌ Nie udało się pobrać danych dla żadnego kierowcy.")
            st.stop()

        figs: dict[str, object] = {}

        if mods_cfg["telemetry"]:
            status.info("📈 Generowanie wykresu telemetrii...")
            figs["telemetry"] = mods["plot_telemetry_interactive"](drivers_data, session_data)
            progress.progress(50, text="Telemetria gotowa...")

        corner_analysis = None
        if mods_cfg["corners"]:
            status.info("🔄 Analiza zakrętów...")
            corner_analysis = mods["run_corner_analysis"](drivers_data)
            figs["corners"] = mods["plot_corners_interactive"](
                drivers_data, corner_analysis, session_data
            )
            try:
                figs["braking_points"] = mods["plot_braking_points_interactive"](
                    drivers_data, corner_analysis, session_data
                )
            except Exception:
                pass
            progress.progress(62, text="Zakręty gotowe...")

        if mods_cfg["telemetry"] and len(drivers_data) >= 2:
            try:
                figs["delta_time"] = mods["plot_delta_time_interactive"](
                    drivers_data, session_data, corner_analysis
                )
            except Exception:
                pass

        mini_sector_data = None
        stats_df = None
        if mods_cfg["sectors"]:
            status.info("🏁 Analiza sektorów...")
            mini_sector_data = mods["compute_mini_sectors"](drivers_data, mini_sects)
            stats_df = mods["compute_sector_stats"](drivers_data)
            figs["mini_sectors"]   = mods["plot_mini_sector_dominance_interactive"](
                drivers_data, mini_sector_data, session_data
            )
            figs["sector_heatmap"] = mods["plot_sector_heatmap_interactive"](
                stats_df, drivers_data, session_data
            )
            progress.progress(74, text="Sektory gotowe...")

        fingerprints = []
        if mods_cfg["style"]:
            status.info("🎯 Obliczanie odcisku palca stylu jazdy...")
            raw_fps = [
                mods["compute_style_fingerprint"](d, corner_analysis)
                for d in drivers_data.values()
            ]
            fingerprints = mods["normalize_fingerprints"](raw_fps)
            figs["radar"]      = mods["plot_radar_interactive"](fingerprints, session_data)
            figs["style_bars"] = mods["plot_style_bars_interactive"](fingerprints, session_data)
            progress.progress(85, text="Styl jazdy gotowy...")

        if mods_cfg["track"]:
            status.info("🗺️ Generowanie map toru...")
            figs["track_dominance"] = mods["plot_driver_dominance_map_interactive"](
                drivers_data, session_data
            )
            for d in drivers_data.values():
                figs[f"speed_map_{d.driver}"] = mods["plot_speed_heatmap_track_interactive"](
                    d, session_data
                )
                figs[f"gear_map_{d.driver}"] = mods["plot_gear_map_interactive"](
                    d, session_data
                )
            progress.progress(92, text="Mapy toru gotowe...")

        race_pace_df = None
        position_df  = pd.DataFrame()
        weather_df   = pd.DataFrame()

        if mods_cfg["race_pace"]:
            status.info("🏎 Pobieranie danych race pace...")
            try:
                race_pace_df = mods["get_race_pace_data"](session_data, list(drivers_data.keys()))
                if not race_pace_df.empty:
                    figs["race_pace"] = mods["plot_race_pace_interactive"](
                        race_pace_df, drivers_data, session_data
                    )
            except Exception as rpe:
                st.warning(f"Race pace: {rpe}")

            try:
                position_df = mods["get_position_data"](session_data, list(drivers_data.keys()))
                if not position_df.empty:
                    figs["positions"] = mods["plot_position_interactive"](
                        position_df, drivers_data, session_data
                    )
            except Exception:
                pass

            if race_pace_df is not None and not race_pace_df.empty:
                try:
                    figs["stint_overview"] = mods["plot_stint_overview_interactive"](
                        race_pace_df, drivers_data, session_data
                    )
                except Exception:
                    pass

        if mods_cfg.get("weather", True):
            status.info("☁️ Pobieranie danych pogodowych...")
            try:
                weather_df = mods["get_weather_data"](session_data)
                if not weather_df.empty:
                    figs["weather"] = mods["plot_weather_interactive"](weather_df, session_data)
            except Exception:
                pass

        if mods_cfg["sectors"]:
            try:
                figs["sector_colors"] = mods["plot_sector_colors_interactive"](
                    drivers_data, session_data
                )
            except Exception:
                pass

        if mods_cfg["track"]:
            try:
                figs["drs"] = mods["plot_drs_interactive"](drivers_data, session_data)
            except Exception:
                pass

        if mods_cfg["race_pace"] and race_pace_df is not None and not race_pace_df.empty:
            try:
                figs["tire_degradation"] = mods["plot_tire_degradation_interactive"](
                    race_pace_df, drivers_data, session_data
                )
            except Exception:
                pass

        progress.progress(100, text="Analiza zakończona!")

        st.session_state["results"] = {
            "session_data":    session_data,
            "drivers_data":    drivers_data,
            "corner_analysis": corner_analysis,
            "stats_df":        stats_df,
            "fingerprints":    fingerprints,
            "race_pace_df":    race_pace_df,
            "position_df":     position_df,
            "weather_df":      weather_df,
            "figs":            figs,
            "METRIC_LABELS":   mods["METRIC_LABELS"],
            "METRIC_FIELDS":   mods["METRIC_FIELDS"],
        }

        n_figs = len([v for v in figs.values() if v is not None])
        status.success(f"✅ Analiza zakończona! Wygenerowano {n_figs} wykresów.")

    except Exception:
        progress.empty(); status.empty()
        st.error("❌ Błąd podczas analizy:")
        st.code(traceback.format_exc(), language="python")
        st.stop()


def run_session_b_analysis(
    year_b: int,
    round_b: str,
    session_b_type: str,
    drivers_b: list[str],
    import_modules_fn,
) -> None:
    if not drivers_b:
        st.error("⚠️ Wybierz co najmniej jednego kierowcę dla sesji B!")
        return

    try:
        rv_b: int | str = int(round_b.strip())
    except ValueError:
        rv_b = round_b.strip()

    progress_b = st.progress(0, text="Ładowanie sesji B...")
    status_b   = st.empty()
    try:
        mods = import_modules_fn()
        status_b.info(f"📡 Ładowanie sesji B: **{year_b} GP#{rv_b} [{session_b_type}]**")
        session_b_data = mods["load_session"](year_b, rv_b, session_b_type, verbose=False)
        progress_b.progress(40, text="Sesja B załadowana...")

        status_b.info(f"🔄 Pobieranie telemetrii B: **{', '.join(drivers_b)}**")
        drivers_b_data = mods["load_drivers_data"](session_b_data, drivers_b)
        progress_b.progress(100, text="Sesja B gotowa!")

        if drivers_b_data:
            st.session_state["session_b"] = {
                "session_data": session_b_data,
                "drivers_data": drivers_b_data,
            }
            status_b.success(
                f"✅ Sesja B załadowana: {session_b_data.event_name} {session_b_data.year}"
            )
        else:
            status_b.error("❌ Brak danych dla wybranych kierowców sesji B.")
    except Exception:
        progress_b.empty()
        status_b.empty()
        st.error("❌ Błąd ładowania sesji B:")
        st.code(traceback.format_exc(), language="python")
