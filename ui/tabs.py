from __future__ import annotations

from dataclasses import replace

import pandas as pd
import streamlit as st


def _dim_color(hex_col: str) -> str:
    h = hex_col.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return hex_col
    r2 = min(255, int(r * 0.55 + 200 * 0.45))
    g2 = min(255, int(g * 0.55 + 200 * 0.45))
    b2 = min(255, int(b * 0.55 + 200 * 0.45))
    return f"#{r2:02x}{g2:02x}{b2:02x}"


def render_tabs(results: dict, session_b: dict | None, import_modules_fn) -> None:
    session_data    = results["session_data"]
    drivers_data    = results["drivers_data"]
    corner_analysis = results["corner_analysis"]
    stats_df        = results["stats_df"]
    fingerprints    = results["fingerprints"]
    race_pace_df    = results["race_pace_df"]
    position_df     = results.get("position_df", pd.DataFrame())
    figs            = results["figs"]
    METRIC_LABELS   = results["METRIC_LABELS"]
    METRIC_FIELDS   = results["METRIC_FIELDS"]

    sorted_drivers = sorted(drivers_data.values(), key=lambda d: d.lap_time)
    ref_time       = sorted_drivers[0].lap_time

    # ── Nagłówek wyników ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="results-header fade-in">
        <div class="results-icon">🏁</div>
        <div>
            <div class="results-title">{session_data.event_name} {session_data.year}</div>
            <div class="results-meta">
                {session_data.session_type} &nbsp;·&nbsp;
                {session_data.circuit_name} &nbsp;·&nbsp;
                {session_data.country}
            </div>
        </div>
        <div class="results-badge">Session</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Szybkie metryki ────────────────────────────────────────────────────────
    cols = st.columns(min(len(sorted_drivers), 4))
    for col, d in zip(cols, sorted_drivers[:4]):
        delta     = d.lap_time - ref_time
        delta_str = "POLE 🥇" if delta == 0 else f"+{delta:.3f}s"
        col.metric(
            label=d.driver,
            value=d.lap_time_str,
            delta=delta_str,
            delta_color="off" if delta == 0 else "inverse",
        )

    st.divider()

    # ── Zakładki ───────────────────────────────────────────────────────────────
    tab_names = [
        "📊 Podsumowanie", "📈 Telemetria", "🔄 Zakręty",
        "🏁 Sektory", "🎯 Styl jazdy", "🗺️ Mapa toru",
        "🏎 Race Pace", "🔀 Cross-session", "📋 Info",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        _tab_summary(sorted_drivers, ref_time, drivers_data, figs)
    with tabs[1]:
        _tab_telemetry(figs)
    with tabs[2]:
        _tab_corners(figs, corner_analysis, drivers_data)
    with tabs[3]:
        _tab_sectors(figs, stats_df)
    with tabs[4]:
        _tab_style(figs, fingerprints, METRIC_LABELS, METRIC_FIELDS)
    with tabs[5]:
        _tab_track(figs, drivers_data, session_data, import_modules_fn)
    with tabs[6]:
        _tab_race_pace(figs, race_pace_df, position_df, session_data, import_modules_fn, drivers_data)
    with tabs[7]:
        _tab_cross_session(session_b, session_data, drivers_data, corner_analysis,
                           import_modules_fn)
    with tabs[8]:
        _tab_info(figs, session_b)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PODSUMOWANIE
# ══════════════════════════════════════════════════════════════════════════════
def _tab_summary(sorted_drivers, ref_time, drivers_data, figs) -> None:
    st.markdown('<div class="f1-subheader">Wyniki okrążeń</div>', unsafe_allow_html=True)

    lap_rows = []
    for i, d in enumerate(sorted_drivers):
        delta = d.lap_time - ref_time
        lap_rows.append({
            "#":         ["🥇", "🥈", "🥉"][i] if i < 3 else str(i + 1),
            "Kierowca":  d.driver,
            "Czas":      d.lap_time_str,
            "Delta":     "POLE" if delta == 0 else f"+{delta:.3f}s",
            "S1 [s]":    round(d.sector1, 3),
            "S2 [s]":    round(d.sector2, 3),
            "S3 [s]":    round(d.sector3, 3),
            "Okrążenie": d.lap_number,
            "Opona":     d.compound,
        })
    st.dataframe(pd.DataFrame(lap_rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="f1-subheader">Profile kierowców</div>', unsafe_allow_html=True)
    driver_cols = st.columns(min(len(drivers_data), 3))
    for col, d in zip(driver_cols, sorted_drivers):
        with col:
            badge = "🥇 POLE" if d.lap_time == ref_time else ""
            st.markdown(f"""
            <div class="driver-card" style="--accent:{d.color}">
                <div class="driver-card-header">
                    <div class="driver-title">{d.driver}</div>
                    <div class="driver-badge">{badge}</div>
                </div>
                <div class="driver-time">{d.lap_time_str}</div>
                <div class="driver-grid">
                    <div class="driver-chip">
                        <div class="driver-chip-label">S1</div>
                        <div class="driver-chip-value">{d.sector1:.3f}</div>
                    </div>
                    <div class="driver-chip">
                        <div class="driver-chip-label">S2</div>
                        <div class="driver-chip-value">{d.sector2:.3f}</div>
                    </div>
                    <div class="driver-chip">
                        <div class="driver-chip-label">S3</div>
                        <div class="driver-chip-value">{d.sector3:.3f}</div>
                    </div>
                </div>
                <div class="driver-meta">Okr. #{d.lap_number} &nbsp;·&nbsp; {d.compound}</div>
            </div>
            """, unsafe_allow_html=True)

    if figs.get("weather"):
        with st.expander("☁️ Warunki pogodowe sesji", expanded=False):
            st.plotly_chart(figs["weather"], use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TELEMETRIA
# ══════════════════════════════════════════════════════════════════════════════
def _tab_telemetry(figs) -> None:
    fig = figs.get("telemetry")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Moduł Telemetria nie był uruchomiony lub brak danych.")

    fig_delta = figs.get("delta_time")
    if fig_delta is not None:
        st.markdown('<div class="f1-subheader">Delta czasu</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_delta, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ZAKRĘTY
# ══════════════════════════════════════════════════════════════════════════════
def _tab_corners(figs, corner_analysis, drivers_data) -> None:
    fig = figs.get("corners")
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)

        if corner_analysis and corner_analysis.corners:
            st.markdown(
                f'<div class="f1-subheader">Dane zakrętów ({len(corner_analysis.corners)} wykryto)</div>',
                unsafe_allow_html=True,
            )
            rows = []
            for corner in corner_analysis.corners:
                row = {"Zakręt": f"T{corner['id']}", "Dystans [m]": f"{corner['distance']:.0f}"}
                for drv in drivers_data:
                    ev_map = {e.corner_id: e for e in corner_analysis.driver_corners.get(drv, [])}
                    ev = ev_map.get(corner["id"])
                    row[f"{drv} – Apeks [km/h]"] = f"{ev.apex_speed:.1f}" if ev else "—"
                    row[f"{drv} – Ham. [m]"]     = f"{ev.braking_distance:.1f}" if ev else "—"
                rows.append(row)
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    fig_bp = figs.get("braking_points")
    if fig_bp is not None:
        st.markdown('<div class="f1-subheader">Punkty hamowania per zakręt</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig_bp, use_container_width=True)

    if fig is None and fig_bp is None:
        st.info("Moduł Zakręty nie był uruchomiony lub brak danych.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SEKTORY
# ══════════════════════════════════════════════════════════════════════════════
def _tab_sectors(figs, stats_df) -> None:
    fig1 = figs.get("mini_sectors")
    fig2 = figs.get("sector_heatmap")

    if fig1 is not None:
        st.plotly_chart(fig1, use_container_width=True)
    if fig2 is not None:
        st.plotly_chart(fig2, use_container_width=True)

    fig_sc = figs.get("sector_colors")
    if fig_sc is not None:
        st.markdown('<div class="f1-subheader">🟣 Purple / 🟢 Green / 🟡 Yellow</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(fig_sc, use_container_width=True)

    if stats_df is not None and not stats_df.empty:
        st.markdown('<div class="f1-subheader">Statystyki sektorowe</div>', unsafe_allow_html=True)
        display_cols = {
            "Driver": "Kierowca",   "Sector": "Sektor",
            "Time_s": "Czas [s]",   "MaxSpeed": "Max V [km/h]",
            "AvgSpeed": "Śr. V [km/h]", "FullThrottle_pct": "Pełny gaz %",
            "Braking_pct": "Hamowanie %",
        }
        st.dataframe(
            stats_df[list(display_cols.keys())].rename(columns=display_cols)
                .sort_values(["Sektor", "Czas [s]"]).reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

    if fig1 is None and fig2 is None:
        st.info("Moduł Sektory nie był uruchomiony lub brak danych.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — STYL JAZDY
# ══════════════════════════════════════════════════════════════════════════════
def _tab_style(figs, fingerprints, METRIC_LABELS, METRIC_FIELDS) -> None:
    fig_radar = figs.get("radar")
    fig_bars  = figs.get("style_bars")

    if fig_radar is not None or fig_bars is not None:
        col_r, col_b = st.columns([1, 1])
        with col_r:
            if fig_radar is not None:
                st.markdown('<div class="f1-subheader">Radar stylu jazdy</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(fig_radar, use_container_width=True)
        with col_b:
            if fig_bars is not None:
                st.markdown('<div class="f1-subheader">Porównanie metryk</div>',
                            unsafe_allow_html=True)
                st.plotly_chart(fig_bars, use_container_width=True)

    if fingerprints:
        st.markdown('<div class="f1-subheader">Metryki stylu jazdy (0 – 100)</div>',
                    unsafe_allow_html=True)
        metric_rows = []
        for label, field in zip(METRIC_LABELS, METRIC_FIELDS):
            row = {"Metryka": label.replace("\n", " ")}
            vals = [getattr(fp, field) for fp in fingerprints]
            best = max(vals)
            for fp, val in zip(fingerprints, vals):
                row[fp.driver] = f"{'★ ' if val == best else ''}{val:.1f}"
            metric_rows.append(row)
        st.dataframe(pd.DataFrame(metric_rows), use_container_width=True, hide_index=True)

    if fig_radar is None and not fingerprints:
        st.info("Moduł Styl jazdy nie był uruchomiony lub brak danych.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — MAPA TORU + ANIMACJA
# ══════════════════════════════════════════════════════════════════════════════
def _tab_track(figs, drivers_data, session_data, import_modules_fn) -> None:
    fig_dom = figs.get("track_dominance")

    if fig_dom is not None:
        st.markdown('<div class="f1-subheader">Dominacja na torze</div>', unsafe_allow_html=True)
        st.plotly_chart(fig_dom, use_container_width=True)
    elif st.session_state.get("params", {}).get("mods", {}).get("track"):
        st.warning("⚠️ Brak danych GPS — mapa dominacji niedostępna dla tej sesji.")

    _drv_with_maps = [d for d in drivers_data
                      if figs.get(f"speed_map_{d}") or figs.get(f"gear_map_{d}")]
    if _drv_with_maps:
        st.markdown('<div class="f1-subheader">Mapy toru per kierowca</div>',
                    unsafe_allow_html=True)
        _drv_map_tabs = st.tabs([f"🗺️ {d}" for d in _drv_with_maps])
        for _drv_tab, _drv in zip(_drv_map_tabs, _drv_with_maps):
            with _drv_tab:
                _fig_spd  = figs.get(f"speed_map_{_drv}")
                _fig_gear = figs.get(f"gear_map_{_drv}")
                _c1, _c2 = st.columns(2)
                if _fig_spd is not None:
                    _c1.subheader("Prędkość")
                    _c1.plotly_chart(_fig_spd, use_container_width=True)
                if _fig_gear is not None:
                    _c2.subheader("Biegi")
                    _c2.plotly_chart(_fig_gear, use_container_width=True)

    _fig_drs = figs.get("drs")
    if _fig_drs is not None:
        st.markdown('<div class="f1-subheader">Analiza DRS</div>', unsafe_allow_html=True)
        st.plotly_chart(_fig_drs, use_container_width=True)

    st.markdown('<div class="f1-subheader" style="margin-top:20px">Animacja okrążenia</div>',
                unsafe_allow_html=True)

    has_gps = any("X" in d.telemetry.columns for d in drivers_data.values())
    if not has_gps:
        st.warning("⚠️ Brak danych GPS — animacja niedostępna dla tej sesji.")
    else:
        anim_key = "anim_" + "_".join(sorted(drivers_data.keys()))
        if st.button("▶ Wygeneruj animację okrążenia", key="gen_anim"):
            with st.spinner("Generowanie animacji..."):
                try:
                    mods = import_modules_fn()
                    fig_generated = mods["plot_track_animation_interactive"](
                        drivers_data, session_data, n_frames=80
                    )
                    if fig_generated is not None:
                        st.session_state[anim_key] = fig_generated
                    else:
                        st.warning("⚠️ Nie można wygenerować animacji — brak danych GPS.")
                except Exception as _anim_err:
                    st.error(f"Błąd generowania animacji: {_anim_err}")

        fig_anim = st.session_state.get(anim_key)
        if fig_anim is not None:
            st.plotly_chart(fig_anim, use_container_width=True)
        else:
            st.caption("Kliknij przycisk powyżej, aby wygenerować animację.")

    if not any(
        k.startswith(("track_", "speed_map_", "gear_map_"))
        for k, v in figs.items() if v is not None
    ) and not has_gps:
        st.info("Moduł Mapa toru nie był uruchomiony lub brak danych GPS.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — RACE PACE
# ══════════════════════════════════════════════════════════════════════════════
def _tab_race_pace(figs, race_pace_df, position_df, session_data, import_modules_fn, drivers_data) -> None:
    fig_rp = figs.get("race_pace")

    if fig_rp is not None:
        st.plotly_chart(fig_rp, use_container_width=True)

        if race_pace_df is not None and not race_pace_df.empty:
            st.markdown('<div class="f1-subheader">Statystyki tempa</div>',
                        unsafe_allow_html=True)
            pace_stats = (
                race_pace_df.groupby("Driver")["LapTime_s"]
                .agg(["mean", "median", "std", "min", "count"])
                .rename(columns={
                    "mean":   "Śr. [s]",
                    "median": "Mediana [s]",
                    "std":    "Odch. std [s]",
                    "min":    "Najszybsze [s]",
                    "count":  "Okrążeń",
                })
                .round(3)
                .reset_index()
                .rename(columns={"Driver": "Kierowca"})
                .sort_values("Śr. [s]")
            )
            st.dataframe(pace_stats, use_container_width=True, hide_index=True)

        _fig_td = figs.get("tire_degradation")
        if _fig_td is not None:
            st.markdown('<div class="f1-subheader">Degradacja opon per stint</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(_fig_td, use_container_width=True)

        _fig_stint = figs.get("stint_overview")
        if _fig_stint is not None:
            st.markdown('<div class="f1-subheader">Podział na stinty</div>',
                        unsafe_allow_html=True)
            st.plotly_chart(_fig_stint, use_container_width=True)

    elif session_data.session_type != "Wyścig":
        st.info(
            "ℹ️ Race Pace jest najbardziej miarodajny dla sesji wyścigowych. "
            f"Aktualna sesja: **{session_data.session_type}**. "
            "Dane są dostępne, ale mogą być ograniczone."
        )
        if race_pace_df is not None and not race_pace_df.empty:
            mods = import_modules_fn()
            fig_rp2 = mods["plot_race_pace_interactive"](race_pace_df, drivers_data, session_data)
            if fig_rp2 is not None:
                st.plotly_chart(fig_rp2, use_container_width=True)
        else:
            st.warning("Brak danych race pace dla tej sesji lub moduł nie był uruchomiony.")
    else:
        st.info("Moduł Race Pace nie był uruchomiony lub brak danych.")

    # Pozycje i stinty pokazywane niezależnie od dostępności race pace
    _fig_pos = figs.get("positions")
    if _fig_pos is not None:
        st.markdown('<div class="f1-subheader">Pozycje w wyścigu</div>', unsafe_allow_html=True)
        st.plotly_chart(_fig_pos, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — CROSS-SESSION
# ══════════════════════════════════════════════════════════════════════════════
def _tab_cross_session(session_b, session_data, drivers_data, corner_analysis,
                       import_modules_fn) -> None:
    if not session_b:
        st.markdown("""
        <div class="note-card">
            🔀 <b>Cross-session comparison</b><br><br>
            Aby porównać kierowców między dwiema sesjami (np. Monaco 2023 vs 2024):
            <ol style="margin-top:10px; color: var(--muted);">
                <li>Rozwiń panel <b>🔀 Porównanie sesji</b> w sidebarze po lewej</li>
                <li>Wybierz rok, rundę i typ sesji B</li>
                <li>Wybierz kierowców sesji B</li>
                <li>Kliknij <b>➕ Załaduj sesję B</b></li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        return

    session_b_data = session_b["session_data"]
    drivers_b_data = session_b["drivers_data"]

    col_a, col_sep, col_b_head = st.columns([5, 1, 5])
    with col_a:
        st.markdown(f"""
        <div class="results-header" style="margin-bottom:8px">
            <div>
                <div class="results-title">{session_data.event_name} {session_data.year}</div>
                <div class="results-meta">SESJA A · {session_data.session_type} · {session_data.circuit_name}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with col_sep:
        st.markdown("<div style='text-align:center;font-size:2rem;padding-top:20px'>⚔️</div>",
                    unsafe_allow_html=True)
    with col_b_head:
        st.markdown(f"""
        <div class="results-header" style="margin-bottom:8px;border-left-color:#00d1ff">
            <div>
                <div class="results-title">{session_b_data.event_name} {session_b_data.year}</div>
                <div class="results-meta">SESJA B · {session_b_data.session_type} · {session_b_data.circuit_name}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="f1-subheader">Porównanie najszybszych okrążeń</div>',
                unsafe_allow_html=True)
    all_d = {
        **{f"A:{k}": v for k, v in drivers_data.items()},
        **{f"B:{k}": v for k, v in drivers_b_data.items()},
    }
    cmp_rows = []
    for tag, d in all_d.items():
        cmp_rows.append({
            "Sesja":     "A" if tag.startswith("A:") else "B",
            "Kierowca":  d.driver,
            "Czas":      d.lap_time_str,
            "S1 [s]":    round(d.sector1, 3),
            "S2 [s]":    round(d.sector2, 3),
            "S3 [s]":    round(d.sector3, 3),
            "Okr. #":    d.lap_number,
            "Opona":     d.compound,
        })
    st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)

    st.markdown('<div class="f1-subheader">Telemetria — sesja A vs B</div>',
                unsafe_allow_html=True)
    combined_data: dict = {}
    for drv, d in drivers_data.items():
        combined_data[drv] = d
    for drv, d in drivers_b_data.items():
        tag = f"B:{drv}"
        combined_data[tag] = replace(d, driver=tag, color=_dim_color(d.color))

    if len(combined_data) >= 2:
        mods = import_modules_fn()
        fig_cross_telem = mods["plot_telemetry_interactive"](combined_data, session_data)
        if fig_cross_telem is not None:
            st.plotly_chart(fig_cross_telem, use_container_width=True)

    st.markdown('<div class="f1-subheader">Styl jazdy — sesja A vs B</div>',
                unsafe_allow_html=True)
    mods = import_modules_fn()
    all_fps_raw = []
    for drv, d in drivers_data.items():
        all_fps_raw.append(mods["compute_style_fingerprint"](d, corner_analysis))
    for drv, d in drivers_b_data.items():
        tagged = replace(d, driver=f"B:{drv}", color=_dim_color(d.color))
        all_fps_raw.append(mods["compute_style_fingerprint"](tagged))

    if len(all_fps_raw) >= 2:
        all_fps = mods["normalize_fingerprints"](all_fps_raw)
        crc, crb = st.columns([1, 1])
        with crc:
            fig_crs_radar = mods["plot_radar_interactive"](all_fps, session_data)
            st.plotly_chart(fig_crs_radar, use_container_width=True)
        with crb:
            fig_crs_bars = mods["plot_style_bars_interactive"](all_fps, session_data)
            st.plotly_chart(fig_crs_bars, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — INFO
# ══════════════════════════════════════════════════════════════════════════════
def _tab_info(figs, session_b) -> None:
    st.markdown('<div class="f1-subheader">Wygenerowane wykresy</div>', unsafe_allow_html=True)
    generated = {k: v for k, v in figs.items() if v is not None}
    if generated:
        st.success(f"✅ {len(generated)} interaktywnych wykresów wygenerowanych.")
        st.dataframe(
            pd.DataFrame([{"Wykres": k} for k in generated]),
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Brak wygenerowanych wykresów.")

    if session_b:
        st.markdown('<div class="f1-subheader">Sesja B</div>', unsafe_allow_html=True)
        sb_d = session_b["session_data"]
        st.info(
            f"Załadowana sesja B: **{sb_d.event_name} {sb_d.year}** "
            f"— {sb_d.session_type} | {sb_d.circuit_name}, {sb_d.country}"
        )
