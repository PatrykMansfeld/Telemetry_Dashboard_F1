"""Wykresy na mapie toru: dominacja, prędkość, biegi, DRS, animacja."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import interp1d

from ..config import ANIMATION_FRAMES, TRACK_MAP_POINTS
from ..data_loader import DriverLapData, SessionData
from ._resample import resample_xy
from .theme import (
    DEFAULT_THEME,
    FONT_MONO,
    ROLE_DRIVER_DOT,
    ROLE_START,
    ROLE_TRACK_LINE,
    ROLE_TRACK_UNDER,
    get_theme,
    rgba,
)

DRS_ACTIVE = "#00C853"   # zielony DRS — czytelny na jasnym i ciemnym tle


def plot_driver_dominance_map_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    n_points: int = TRACK_MAP_POINTS,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Mapa toru: każdy segment pokolorowany kierowcą, który był najszybszy."""
    t = get_theme(theme)
    if not drivers_data:
        return None

    sample = next(iter(drivers_data.values()))
    if "X" not in sample.telemetry.columns:
        return None

    driver_speeds: dict[str, np.ndarray] = {}
    ref_xy: tuple[np.ndarray, np.ndarray] = (np.array([]), np.array([]))

    for i, (drv, data) in enumerate(drivers_data.items()):
        xi, yi, spd = resample_xy(data.telemetry, "Speed", n_points)
        driver_speeds[drv] = spd
        if i == 0 and len(xi) > 0:
            ref_xy = (xi, yi)

    if len(ref_xy[0]) == 0:
        return None

    x_ref, y_ref = ref_xy
    drivers_list  = list(drivers_data.keys())

    # Najszybszy kierowca w każdym punkcie
    fastest_per_pt = []
    for seg_i in range(n_points):
        spds = {d: driver_speeds[d][seg_i]
                for d in drivers_list if len(driver_speeds.get(d, [])) > seg_i}
        fastest_per_pt.append(max(spds, key=spds.get) if spds else drivers_list[0])

    fig = go.Figure()

    # Tło toru
    fig.add_trace(go.Scatter(
        x=x_ref, y=y_ref,
        mode="markers",
        marker=dict(color=t.track_under, size=12),
        meta={"role": ROLE_TRACK_UNDER},
        showlegend=False, hoverinfo="skip",
    ))

    # Każdy kierowca — punkty dominacji
    for drv in drivers_list:
        data  = drivers_data[drv]
        mask  = np.array([fastest_per_pt[i] == drv for i in range(n_points)])
        if not mask.any():
            continue
        fig.add_trace(go.Scatter(
            x=x_ref[mask], y=y_ref[mask],
            mode="markers",
            marker=dict(color=data.color, size=7),
            name=f"{drv}  {data.lap_time_str}",
            hovertemplate=f"<b>{drv}</b><extra></extra>",
        ))

    # Punkt startowy
    fig.add_trace(go.Scatter(
        x=[x_ref[0]], y=[y_ref[0]],
        mode="markers+text",
        marker=dict(color=t.start, size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color=t.start, size=10),
        meta={"role": ROLE_START},
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Dominacja na torze  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=720)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor=t.track_bg,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 8. MAPA PRĘDKOŚCI NA TORZE
# ══════════════════════════════════════════════════════════════════════════════

def plot_speed_heatmap_track_interactive(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = TRACK_MAP_POINTS,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Mapa prędkości jednego kierowcy na torze (gradient kolorów)."""
    t = get_theme(theme)
    telem = driver_data.telemetry
    if "X" not in telem.columns:
        return None

    xi, yi, spd = resample_xy(telem, "Speed", n_points)
    if len(xi) == 0:
        return None

    fig = go.Figure()

    # Tło toru
    fig.add_trace(go.Scatter(
        x=xi, y=yi,
        mode="markers",
        marker=dict(color=t.track_under, size=12),
        meta={"role": ROLE_TRACK_UNDER},
        showlegend=False, hoverinfo="skip",
    ))

    # Gradient prędkości
    fig.add_trace(go.Scatter(
        x=xi, y=yi,
        mode="markers",
        marker=dict(
            color=spd,
            colorscale="RdYlGn",
            size=6,
            colorbar=dict(
                title=dict(text="V [km/h]", font=dict(color=t.text)),
                tickfont=dict(color=t.tick),
                bgcolor=t.plot,
                bordercolor=t.border,
                thickness=12,
                len=0.7,
            ),
        ),
        name=f"V {driver_data.driver}",
        hovertemplate=(
            f"<b>{driver_data.driver}</b><br>"
            "V: %{marker.color:.0f} km/h<extra></extra>"
        ),
    ))

    # Start/Meta
    fig.add_trace(go.Scatter(
        x=[xi[0]], y=[yi[0]],
        mode="markers+text",
        marker=dict(color=t.start, size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color=t.start, size=10),
        meta={"role": ROLE_START},
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{driver_data.driver}  |  Mapa prędkości  |  "
        f"{session_data.event_name} {session_data.year} [{session_data.session_type}]"
    )
    t.style(fig, title=title, height=650)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor=t.track_bg,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 9. MAPA BIEGÓW NA TORZE
# ══════════════════════════════════════════════════════════════════════════════

def plot_gear_map_interactive(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = TRACK_MAP_POINTS,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Mapa biegów jednego kierowcy na torze (kolor per bieg)."""
    t = get_theme(theme)
    telem = driver_data.telemetry
    if "X" not in telem.columns or "nGear" not in telem.columns:
        return None

    xi, yi, gear = resample_xy(telem, "nGear", n_points)
    if len(xi) == 0:
        return None

    gear = np.clip(np.round(gear), 1, 8).astype(int)

    # Kolory biegów 1–8
    gear_colors = [
        f"hsl({int(h * 360)}, 85%, 55%)"
        for h in np.linspace(0.65, 0.05, 8)
    ]

    fig = go.Figure()

    # Tło
    fig.add_trace(go.Scatter(
        x=xi, y=yi,
        mode="markers",
        marker=dict(color=t.track_under, size=12),
        meta={"role": ROLE_TRACK_UNDER},
        showlegend=False, hoverinfo="skip",
    ))

    for g in range(1, 9):
        mask = gear == g
        if not mask.any():
            continue
        fig.add_trace(go.Scatter(
            x=xi[mask], y=yi[mask],
            mode="markers",
            marker=dict(color=gear_colors[g - 1], size=6),
            name=f"Bieg {g}",
            hovertemplate=f"<b>Bieg {g}</b><extra></extra>",
        ))

    # Start/Meta
    fig.add_trace(go.Scatter(
        x=[xi[0]], y=[yi[0]],
        mode="markers+text",
        marker=dict(color=t.start, size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color=t.start, size=10),
        meta={"role": ROLE_START},
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{driver_data.driver}  |  Mapa biegów  |  "
        f"{session_data.event_name} {session_data.year} [{session_data.session_type}]"
    )
    t.style(fig, title=title, height=650)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor=t.track_bg,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 10. RACE PACE
# ══════════════════════════════════════════════════════════════════════════════

def plot_track_animation_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    n_frames: int = ANIMATION_FRAMES,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """
    Animacja Plotly: pozycje kierowców poruszające się po torze.
    Wymaga danych GPS (kolumny X, Y w telemetrii).
    Osie czasu znormalizowane do 0–1 (procent ukończonego okrążenia).
    """
    t = get_theme(theme)
    # Sprawdź dostępność GPS
    gps_drivers = {
        drv: data for drv, data in drivers_data.items()
        if "X" in data.telemetry.columns and "Y" in data.telemetry.columns
    }
    if not gps_drivers:
        return None

    TRAIL = 14  # długość śladu

    # Dla każdego kierowcy: znormalizowany czas → X, Y
    driver_pos: dict[str, dict] = {}
    for drv, data in gps_drivers.items():
        telem = data.telemetry
        dist = telem["Distance"].values
        speed = np.maximum(telem["Speed"].values, 1.0)
        step = np.diff(dist, prepend=dist[0])
        step = np.maximum(step, 0.0)
        dt = step / (speed / 3.6)
        cum_time = np.cumsum(dt)
        t_norm = cum_time / max(cum_time[-1], 1e-9)

        _, idx = np.unique(t_norm, return_index=True)
        t_u, x_u, y_u = t_norm[idx], telem["X"].values[idx], telem["Y"].values[idx]

        common_t = np.linspace(0, 1, n_frames)
        xi = interp1d(t_u, x_u, fill_value="extrapolate", bounds_error=False)(common_t)
        yi = interp1d(t_u, y_u, fill_value="extrapolate", bounds_error=False)(common_t)

        driver_pos[drv] = {
            "x": xi, "y": yi,
            "color": data.color,
            "lap_time": data.lap_time_str,
        }

    # Obrys toru z referencyjnego kierowcy
    ref_t = next(iter(gps_drivers.values())).telemetry
    x_track = ref_t["X"].values
    y_track = ref_t["Y"].values

    # ── Bazowy rysunek ────────────────────────────────────────────────────────
    # Trasy statyczne (tor) mają indeksy 0, 1, 2.
    # Trasy kierowców (ślad + kropka) mają indeksy 3, 4 / 5, 6 / ...
    # Klatki animacji aktualizują TYLKO trasy kierowców (oszczędność danych).
    fig = go.Figure()

    # Tło toru (dwie warstwy dla efektu grubości)
    for w, c in [(12, t.track_wide), (7, t.track_mid)]:
        fig.add_trace(go.Scatter(
            x=x_track, y=y_track, mode="lines",
            line=dict(color=c, width=w),
            meta={"role": ROLE_TRACK_LINE},
            showlegend=False, hoverinfo="skip",
        ))

    # Linia start/meta
    fig.add_trace(go.Scatter(
        x=[x_track[0]], y=[y_track[0]],
        mode="markers+text",
        marker=dict(color=t.start, size=14, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color=t.start, size=9, family=FONT_MONO),
        meta={"role": ROLE_START},
        showlegend=False, hoverinfo="skip",
    ))

    # Ślad i kropka każdego kierowcy (stan początkowy — klatka 0)
    n_static = 3  # liczba statycznych tras toru powyżej
    drv_list = list(driver_pos.keys())
    drv_trace_indices: list[int] = []  # indeksy tras kierowców do aktualizacji w klatkach

    for i, drv in enumerate(drv_list):
        pos = driver_pos[drv]
        trail_idx = n_static + i * 2
        dot_idx   = n_static + i * 2 + 1
        drv_trace_indices.extend([trail_idx, dot_idx])

        fig.add_trace(go.Scatter(
            x=[pos["x"][0]], y=[pos["y"][0]],
            mode="lines",
            line=dict(color=pos["color"], width=2.5),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=[pos["x"][0]], y=[pos["y"][0]],
            mode="markers+text",
            marker=dict(color=pos["color"], size=16,
                        line=dict(color=t.dot_edge, width=2)),
            text=[drv],
            textposition="top center",
            textfont=dict(color=pos["color"], size=9, family=FONT_MONO),
            name=f"{drv}  {pos['lap_time']}",
            meta={"role": ROLE_DRIVER_DOT},
            showlegend=True,
            hovertemplate=f"<b>{drv}</b><extra></extra>",
        ))

    # ── Klatki animacji ───────────────────────────────────────────────────────
    # Każda klatka zawiera TYLKO trasy kierowców (ślad + kropka).
    # Parametr `traces=` wskazuje Plotly, które trasy zaktualizować —
    # tor pozostaje statyczny w figureie bazowym i nie jest kopiowany.
    frames: list[go.Frame] = []
    for fi in range(n_frames):
        fd: list[go.BaseTraceType] = []

        for drv in drv_list:
            pos = driver_pos[drv]
            start = max(0, fi - TRAIL)
            # Ślad
            fd.append(go.Scatter(
                x=list(pos["x"][start: fi + 1]),
                y=list(pos["y"][start: fi + 1]),
                mode="lines",
                line=dict(color=pos["color"], width=2.5),
                showlegend=False, hoverinfo="skip",
            ))
            # Aktualna pozycja
            fd.append(go.Scatter(
                x=[pos["x"][fi]], y=[pos["y"][fi]],
                mode="markers+text",
                marker=dict(color=pos["color"], size=16,
                            line=dict(color=t.dot_edge, width=2)),
                text=[drv],
                textposition="top center",
                textfont=dict(color=pos["color"], size=9, family=FONT_MONO),
                meta={"role": ROLE_DRIVER_DOT},
                showlegend=False,
            ))

        frames.append(go.Frame(
            data=fd,
            traces=drv_trace_indices,  # aktualizuj tylko trasy kierowców
            name=str(fi),
        ))

    fig.frames = frames

    # ── Kontrolki animacji ────────────────────────────────────────────────────
    step_labels = [f"{int(i / n_frames * 100)}%" for i in range(n_frames)]
    fig.update_layout(
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "x": 0.5, "y": -0.06,
            "xanchor": "center", "yanchor": "top",
            "bgcolor": t.plot,
            "bordercolor": t.border,
            "font": {"color": t.text},
            "buttons": [
                {
                    "label": "▶  Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 55, "redraw": True},
                        "fromcurrent": True,
                        "transition": {"duration": 15, "easing": "linear"},
                    }],
                },
                {
                    "label": "⏸  Pauza",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                },
            ],
        }],
        sliders=[{
            "active": 0,
            "steps": [
                {
                    "args": [[str(i)], {
                        "frame": {"duration": 55, "redraw": True},
                        "mode": "immediate",
                        "transition": {"duration": 0},
                    }],
                    "label": step_labels[i],
                    "method": "animate",
                }
                for i in range(n_frames)
            ],
            "y": 0, "x": 0.07, "len": 0.86,
            "pad": {"t": 55},
            "currentvalue": {
                "prefix": "Postęp okrążenia: ",
                "visible": True,
                "xanchor": "center",
                "font": {"color": t.text, "size": 11, "family": FONT_MONO},
            },
            "bgcolor": t.plot,
            "bordercolor": t.border,
            "font": {"color": t.subtitle, "size": 8},
            "tickcolor": t.border,
        }],
    )

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Animacja okrążenia  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=820)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor=t.track_bg,
        margin=dict(l=30, r=30, t=70, b=140),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 12. DANE POGODOWE
# ══════════════════════════════════════════════════════════════════════════════

def plot_drs_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Analiza DRS: strefy aktywacji na mapie toru + rozkład prędkości DRS on vs off."""
    t = get_theme(theme)
    any_drs = any(
        "DRS" in d.telemetry.columns and d.telemetry["DRS"].max() > 0
        for d in drivers_data.values()
    )
    if not any_drs:
        return None

    has_gps = any(
        "X" in d.telemetry.columns and "Y" in d.telemetry.columns
        for d in drivers_data.values()
    )

    if has_gps:
        fig = make_subplots(
            rows=1, cols=2,
            column_widths=[0.55, 0.45],
            subplot_titles=["Strefy DRS na torze", "Prędkość  DRS on vs off [km/h]"],
            specs=[[{"type": "scatter"}, {"type": "scatter"}]],
        )
        col_map, col_spd = 1, 2
    else:
        fig = make_subplots(
            rows=1, cols=1,
            subplot_titles=["Prędkość  DRS on vs off [km/h]"],
        )
        col_map, col_spd = None, 1

    for drv, data in drivers_data.items():
        telem    = data.telemetry
        if "DRS" not in telem.columns:
            continue
        drs_open = telem["DRS"] >= 10

        if has_gps and col_map and "X" in telem.columns:
            x_all, y_all = telem["X"].values, telem["Y"].values

            fig.add_trace(go.Scatter(
                x=x_all, y=y_all, mode="markers",
                marker=dict(color=t.track_under, size=9),
                meta={"role": ROLE_TRACK_UNDER},
                showlegend=False, hoverinfo="skip",
            ), row=1, col=col_map)

            mask_off = ~drs_open.values
            if mask_off.any():
                fig.add_trace(go.Scatter(
                    x=x_all[mask_off], y=y_all[mask_off], mode="markers",
                    marker=dict(color=data.color, size=4, opacity=0.3),
                    name=f"{drv} DRS off", legendgroup=drv, showlegend=False,
                    hoverinfo="skip",
                ), row=1, col=col_map)

            mask_on = drs_open.values
            if mask_on.any():
                fig.add_trace(go.Scatter(
                    x=x_all[mask_on], y=y_all[mask_on], mode="markers",
                    marker=dict(color=DRS_ACTIVE, size=7, opacity=0.95),
                    name=f"{drv}  DRS ✓",
                    legendgroup=drv, showlegend=True,
                    hovertemplate=(
                        f"<b>{drv}</b> DRS aktywny<br>"
                        "V: %{customdata:.0f} km/h<extra></extra>"
                    ),
                    customdata=telem.loc[mask_on, "Speed"].values,
                ), row=1, col=col_map)

        spd_on  = telem.loc[drs_open,  "Speed"].values if drs_open.any()  else np.array([])
        spd_off = telem.loc[~drs_open, "Speed"].values if (~drs_open).any() else np.array([])

        for label, spd, alpha in [("on", spd_on, 0.35), ("off", spd_off, 0.12)]:
            if len(spd) < 5:
                continue
            fig.add_trace(go.Violin(
                y=spd, name=f"{drv}  DRS {label}",
                line_color=data.color,
                fillcolor=rgba(data.color, alpha),
                box_visible=True, meanline_visible=True,
                legendgroup=drv, showlegend=False,
                hovertemplate=f"<b>{drv} DRS {label}</b><br>V: %{{y:.0f}} km/h<extra></extra>",
                x0=f"{drv} {label}",
            ), row=1, col=col_spd)

    if has_gps and col_map:
        fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, row=1, col=col_map)
        fig.update_yaxes(visible=False, row=1, col=col_map)

    fig.update_yaxes(**t.axis("V [km/h]"), row=1, col=col_spd)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Analiza DRS  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=680)

    return fig
