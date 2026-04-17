"""
Interaktywne wykresy Plotly dla dashboardu Streamlit.
Każda funkcja zwraca go.Figure gotowy do st.plotly_chart().
"""
from __future__ import annotations

from typing import Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.colors as pc
from plotly.subplots import make_subplots
from scipy.interpolate import interp1d

from .data_loader import DriverLapData, SessionData
from .sector_analysis import MiniSector
from .driver_style import StyleFingerprint, METRIC_LABELS, METRIC_FIELDS

# ── Motyw ciemny ───────────────────────────────────────────────────────────────
_BG   = "#0F0F0F"
_PLOT = "#1A1A1A"
_GRID = "#2A2A2A"
_TEXT = "#CCCCCC"
_AXIS = "#888888"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _dark(fig: go.Figure, title: str = "", height: int = 700) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(color="#FFFFFF", size=15, family="Courier New")),
        paper_bgcolor=_BG,
        plot_bgcolor=_PLOT,
        font=dict(color=_TEXT, family="Courier New, monospace", size=13),
        height=height,
        legend=dict(bgcolor="#222222", bordercolor="#444444", borderwidth=1,
                    font=dict(color=_TEXT)),
        margin=dict(l=60, r=30, t=60, b=50),
        hoverlabel=dict(bgcolor="#1A1A1A", bordercolor="#444444", font_color="#FFFFFF"),
    )
    fig.update_xaxes(gridcolor=_GRID, zerolinecolor=_GRID,
                     tickfont=dict(color=_AXIS), showgrid=True)
    fig.update_yaxes(gridcolor=_GRID, zerolinecolor=_GRID,
                     tickfont=dict(color=_AXIS), showgrid=True)
    return fig


def _axis(title: str = "") -> dict:
    return dict(
        title=dict(text=title, font=dict(color=_TEXT, size=12)),
        gridcolor=_GRID,
        zerolinecolor=_GRID,
        tickfont=dict(color=_AXIS, size=10),
    )


def _interp(telem: pd.DataFrame, channel: str, common: np.ndarray) -> np.ndarray:
    dist = telem["Distance"].values
    vals = (telem[channel].values if channel in telem.columns
            else np.zeros(len(dist)))
    _, idx = np.unique(dist, return_index=True)
    dist, vals = dist[idx], vals[idx]
    if len(dist) < 2:
        return np.zeros_like(common)
    f = interp1d(dist, vals, kind="linear",
                 bounds_error=False, fill_value="extrapolate")
    return f(common)


def _common_d(drivers_data: dict[str, DriverLapData], n: int = 1500) -> np.ndarray:
    max_d = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    return np.linspace(0, max_d, n)


def _resample_xy(
    telem: pd.DataFrame, channel: str, n: int = 2000
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if "X" not in telem.columns or "Y" not in telem.columns:
        return np.array([]), np.array([]), np.array([])
    dist = telem["Distance"].values
    x = telem["X"].values
    y = telem["Y"].values
    vals = (telem[channel].values if channel in telem.columns
            else np.zeros(len(dist)))
    _, idx = np.unique(dist, return_index=True)
    dist, x, y, vals = dist[idx], x[idx], y[idx], vals[idx]
    if len(dist) < 4:
        return np.array([]), np.array([]), np.array([])
    common = np.linspace(dist[0], dist[-1], n)
    xi = interp1d(dist, x,    fill_value="extrapolate")(common)
    yi = interp1d(dist, y,    fill_value="extrapolate")(common)
    vi = interp1d(dist, vals, fill_value="extrapolate")(common)
    return xi, yi, vi


# ══════════════════════════════════════════════════════════════════════════════
# 1. TELEMETRIA
# ══════════════════════════════════════════════════════════════════════════════
def plot_telemetry_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> go.Figure:
    """Interaktywne porównanie telemetrii: prędkość, delta, gaz, hamulec, biegi, RPM."""
    if not drivers_data:
        return go.Figure()

    common = _common_d(drivers_data)
    driver_list = list(drivers_data.values())

    fig = make_subplots(
        rows=6, cols=1,
        shared_xaxes=True,
        row_heights=[3, 1.5, 1, 1, 1.2, 0.8],
        vertical_spacing=0.025,
        subplot_titles=[
            "Prędkość [km/h]", "Δ czas [s]",
            "Gaz [%]", "Hamulec [%]", "Bieg", "RPM",
        ],
    )

    # Interpolacja danych
    di: dict[str, dict] = {}
    for d in driver_list:
        brake = _interp(d.telemetry, "Brake", common)
        if brake.max() <= 1.0:
            brake = brake * 100
        di[d.driver] = {
            "speed":    _interp(d.telemetry, "Speed",    common),
            "throttle": _interp(d.telemetry, "Throttle", common),
            "brake":    brake,
            "gear":     np.clip(np.round(_interp(d.telemetry, "nGear", common)), 1, 8),
            "rpm":      _interp(d.telemetry, "RPM",      common),
        }

    # Delta vs kierowca referencyjny (pierwszy)
    ref = driver_list[0]
    step = np.diff(common, prepend=common[0])
    ref_spd = di[ref.driver]["speed"]
    ref_t_m = np.where(ref_spd > 1, step / (ref_spd / 3.6), 0)

    for d in driver_list:
        c = d.color
        lbl = f"{d.driver}  {d.lap_time_str}"

        # ── Prędkość ──────────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["speed"],
            name=lbl, line=dict(color=c, width=1.8),
            legendgroup=d.driver, showlegend=True,
            hovertemplate=(
                f"<b>{d.driver}</b><br>"
                "Dystans: %{x:.0f} m<br>"
                "V: %{y:.1f} km/h<extra></extra>"
            ),
        ), row=1, col=1)

        # ── Delta czasu ───────────────────────────────────────────────────────
        if d.driver != ref.driver:
            spd = di[d.driver]["speed"]
            drv_t_m = np.where(spd > 1, step / (spd / 3.6), 0)
            delta = np.cumsum(drv_t_m - ref_t_m)
            fig.add_trace(go.Scatter(
                x=common, y=delta,
                name=lbl, line=dict(color=c, width=1.3),
                legendgroup=d.driver, showlegend=False,
                fill="tozeroy", fillcolor=_rgba(c, 0.10),
                hovertemplate=(
                    f"<b>{d.driver} vs {ref.driver}</b><br>"
                    "Δt: %{y:.3f} s<extra></extra>"
                ),
            ), row=2, col=1)
        else:
            fig.add_trace(go.Scatter(
                x=common, y=np.zeros_like(common),
                name=f"{ref.driver} (ref)",
                line=dict(color=c, width=1, dash="dot"),
                legendgroup=d.driver, showlegend=False,
                hoverinfo="skip",
            ), row=2, col=1)

        # ── Gaz ───────────────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["throttle"],
            name=lbl, line=dict(color=c, width=1),
            legendgroup=d.driver, showlegend=False,
            fill="tozeroy", fillcolor=_rgba(c, 0.07),
            hovertemplate=f"<b>{d.driver}</b><br>Gaz: %{{y:.0f}}%<extra></extra>",
        ), row=3, col=1)

        # ── Hamulec ───────────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["brake"],
            name=lbl, line=dict(color=c, width=1),
            legendgroup=d.driver, showlegend=False,
            fill="tozeroy", fillcolor=_rgba(c, 0.07),
            hovertemplate=f"<b>{d.driver}</b><br>Ham: %{{y:.0f}}%<extra></extra>",
        ), row=4, col=1)

        # ── Bieg (krok) ───────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["gear"],
            name=lbl, line=dict(color=c, width=1.2, shape="hv"),
            legendgroup=d.driver, showlegend=False,
            hovertemplate=f"<b>{d.driver}</b><br>Bieg: %{{y:.0f}}<extra></extra>",
        ), row=5, col=1)

        # ── RPM ───────────────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["rpm"],
            name=lbl, line=dict(color=c, width=1),
            legendgroup=d.driver, showlegend=False,
            hovertemplate=f"<b>{d.driver}</b><br>RPM: %{{y:.0f}}<extra></extra>",
        ), row=6, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"{session_data.session_type}  |  {session_data.circuit_name}"
    )
    _dark(fig, title=title, height=1100)

    fig.update_yaxes(**_axis("V [km/h]"),       row=1, col=1)
    fig.update_yaxes(**_axis("Δt [s]"),          row=2, col=1)
    fig.update_yaxes(**_axis("Gaz [%]"),         row=3, col=1, range=[0, 108])
    fig.update_yaxes(**_axis("Ham [%]"),         row=4, col=1, range=[-5, 108])
    fig.update_yaxes(**_axis("Bieg"),             row=5, col=1,
                     tickvals=list(range(1, 9)), range=[0.5, 8.5])
    fig.update_yaxes(**_axis("RPM"),              row=6, col=1)
    fig.update_xaxes(**_axis("Dystans [m]"),      row=6, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 2. ANALIZA ZAKRĘTÓW
# ══════════════════════════════════════════════════════════════════════════════
def plot_corners_interactive(
    drivers_data: dict[str, DriverLapData],
    corner_analysis,   # CornerAnalysis
    session_data: SessionData,
) -> go.Figure:
    """Interaktywny wykres porównania zakrętów: prędkość, hamowanie, wyjście."""
    if corner_analysis is None or not corner_analysis.corners:
        return go.Figure()

    corners = corner_analysis.corners[:12]
    c_labels = [f"T{c['id']}" for c in corners]
    drivers = list(drivers_data.keys())

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=[
            "Prędkość w apeksie [km/h]",
            "Dystans hamowania [m]",
            "Dystans powrotu do gazu po apeksie [m]",
        ],
    )

    for drv in drivers:
        color = drivers_data[drv].color
        ev_map = {e.corner_id: e for e in corner_analysis.driver_corners.get(drv, [])}

        apex_spd, brk_dist, exit_dist = [], [], []
        for c in corners:
            ev = ev_map.get(c["id"])
            apex_spd.append(ev.apex_speed if ev else 0)
            brk_dist.append(ev.braking_distance if ev else 0)
            exit_dist.append(
                max(0, ev.exit_throttle_point - ev.apex_distance) if ev else 0
            )

        common_bar = dict(
            x=c_labels, marker_color=color, name=drv,
            legendgroup=drv, marker_line_width=0,
        )

        fig.add_trace(go.Bar(
            **common_bar, y=apex_spd, showlegend=True,
            hovertemplate=f"<b>{drv}</b><br>Zakręt: %{{x}}<br>V apeks: %{{y:.1f}} km/h<extra></extra>",
        ), row=1, col=1)
        fig.add_trace(go.Bar(
            **common_bar, y=brk_dist, showlegend=False,
            hovertemplate=f"<b>{drv}</b><br>Zakręt: %{{x}}<br>Hamowanie: %{{y:.1f}} m<extra></extra>",
        ), row=2, col=1)
        fig.add_trace(go.Bar(
            **common_bar, y=exit_dist, showlegend=False,
            hovertemplate=f"<b>{drv}</b><br>Zakręt: %{{x}}<br>Wyjście: %{{y:.1f}} m<extra></extra>",
        ), row=3, col=1)

    fig.update_layout(barmode="group")
    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Analiza zakrętów  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=850)

    fig.update_yaxes(**_axis("V [km/h]"),  row=1, col=1)
    fig.update_yaxes(**_axis("Dystans [m]"), row=2, col=1)
    fig.update_yaxes(**_axis("Dystans [m]"), row=3, col=1)
    fig.update_xaxes(**_axis("Zakręt"),      row=3, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 3. DOMINACJA MINI-SEKTORÓW
# ══════════════════════════════════════════════════════════════════════════════
def plot_mini_sector_dominance_interactive(
    drivers_data: dict[str, DriverLapData],
    mini_sectors: list,   # list[MiniSector]
    session_data: SessionData,
) -> go.Figure:
    """Interaktywna dominacja mini-sektorów + delta czasu + prędkość."""
    if not mini_sectors:
        return go.Figure()

    drivers = list(drivers_data.keys())
    ref_drv = min(drivers_data.values(), key=lambda d: d.lap_time).driver

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.15, 0.425, 0.425],
        vertical_spacing=0.04,
        subplot_titles=[
            "Dominacja mini-sektorów",
            "Skumulowana delta czasu [s]",
            "Średnia prędkość w mini-sektorach [km/h]",
        ],
    )

    # ── Pasek dominacji — wypełnione prostokąty na osi czasu ──────────────────
    for drv in drivers:
        color = drivers_data[drv].color
        xs, ys = [], []
        for ms in mini_sectors:
            if ms.fastest_driver == drv:
                xs += [ms.dist_start, ms.dist_start, ms.dist_end, ms.dist_end, None]
                ys += [-0.45, 0.45, 0.45, -0.45, None]
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys,
                fill="toself", fillcolor=_rgba(color, 0.85),
                line=dict(width=0), name=drv,
                legendgroup=drv, showlegend=True,
                mode="lines",
                hovertemplate=f"<b>{drv}</b><br>Dominuje w tym mini-sektorze<extra></extra>",
            ), row=1, col=1)

    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_xaxes(showgrid=False, row=1, col=1)

    # ── Delta czasu ───────────────────────────────────────────────────────────
    fig.add_hline(y=0, line=dict(color="#555555", width=1, dash="dash"), row=2, col=1)

    for drv in drivers:
        if drv == ref_drv:
            continue
        color = drivers_data[drv].color
        cum_delta, dists, deltas = 0.0, [], []
        for ms in mini_sectors:
            ref_t = ms.times.get(ref_drv, 0)
            drv_t = ms.times.get(drv, 0)
            if ref_t > 0 and drv_t > 0:
                cum_delta += drv_t - ref_t
            dists.append(ms.dist_end)
            deltas.append(cum_delta)

        fig.add_trace(go.Scatter(
            x=dists, y=deltas,
            name=drv, line=dict(color=color, width=1.5),
            legendgroup=drv, showlegend=False,
            fill="tozeroy", fillcolor=_rgba(color, 0.08),
            hovertemplate=(
                f"<b>{drv} vs {ref_drv}</b><br>"
                "Dist: %{x:.0f} m<br>"
                "Δt: %{y:.3f} s<extra></extra>"
            ),
        ), row=2, col=1)

    fig.update_yaxes(**_axis("Δt [s]"), row=2, col=1)

    # ── Prędkość średnia ──────────────────────────────────────────────────────
    for drv in drivers:
        color = drivers_data[drv].color
        dists  = [ms.dist_start + (ms.dist_end - ms.dist_start) / 2 for ms in mini_sectors]
        speeds = [ms.speeds.get(drv, 0) for ms in mini_sectors]
        fig.add_trace(go.Scatter(
            x=dists, y=speeds,
            name=drv, line=dict(color=color, width=1.6),
            legendgroup=drv, showlegend=False,
            hovertemplate=(
                f"<b>{drv}</b><br>"
                "Dist: %{x:.0f} m<br>"
                "Śr. V: %{y:.1f} km/h<extra></extra>"
            ),
        ), row=3, col=1)

    fig.update_yaxes(**_axis("V [km/h]"),   row=3, col=1)
    fig.update_xaxes(**_axis("Dystans [m]"), row=3, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Dominacja mini-sektorów  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=850)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. MAPA CIEPŁA SEKTORÓW
# ══════════════════════════════════════════════════════════════════════════════
def plot_sector_heatmap_interactive(
    stats_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> go.Figure:
    """Interaktywna mapa ciepła statystyk sektorowych."""
    if stats_df is None or stats_df.empty:
        return go.Figure()

    metrics = ["Time_s", "MaxSpeed", "AvgSpeed", "FullThrottle_pct", "Braking_pct"]
    m_labels = ["Czas [s]", "Max V [km/h]", "Śr. V [km/h]", "Pełny gaz %", "Hamowanie %"]
    sectors  = ["S1", "S2", "S3"]
    drivers  = sorted(stats_df["Driver"].unique())

    fig = make_subplots(
        rows=1, cols=len(metrics),
        subplot_titles=m_labels,
        horizontal_spacing=0.04,
    )

    for col_i, (metric, mlabel) in enumerate(zip(metrics, m_labels), start=1):
        matrix = np.full((len(drivers), len(sectors)), np.nan)
        text   = np.full((len(drivers), len(sectors)), "", dtype=object)

        for i, drv in enumerate(drivers):
            for j, sec in enumerate(sectors):
                row = stats_df[(stats_df["Driver"] == drv) & (stats_df["Sector"] == sec)]
                if not row.empty:
                    val = float(row[metric].iloc[0])
                    matrix[i, j] = val
                    text[i, j] = f"{val:.2f}" if metric == "Time_s" else f"{val:.1f}"

        # Normalizacja kolumn
        normed = matrix.copy()
        for j in range(len(sectors)):
            col = matrix[:, j]
            valid = col[~np.isnan(col)]
            if len(valid) > 1 and valid.max() > valid.min():
                if metric == "Time_s":
                    normed[:, j] = 1.0 - (col - valid.min()) / (valid.max() - valid.min())
                else:
                    normed[:, j] = (col - valid.min()) / (valid.max() - valid.min())
            else:
                normed[:, j] = 0.5

        fig.add_trace(go.Heatmap(
            z=normed,
            x=sectors,
            y=drivers,
            text=text,
            texttemplate="%{text}",
            textfont=dict(size=11, color="#FFFFFF", family="Courier New"),
            colorscale="RdYlGn",
            zmin=0, zmax=1,
            showscale=False,
            hovertemplate=(
                f"<b>{mlabel}</b><br>"
                "Kierowca: %{y}<br>"
                "Sektor: %{x}<br>"
                "Wartość: %{text}<extra></extra>"
            ),
        ), row=1, col=col_i)

        fig.update_xaxes(tickfont=dict(color=_AXIS, size=10), row=1, col=col_i)
        if col_i == 1:
            fig.update_yaxes(tickfont=dict(color=_AXIS, size=10), row=1, col=col_i)
        else:
            fig.update_yaxes(showticklabels=False, row=1, col=col_i)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Mapa ciepła sektorów  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=max(500, len(drivers) * 90 + 150))

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 5. RADAR STYLU JAZDY
# ══════════════════════════════════════════════════════════════════════════════
def plot_radar_interactive(
    fingerprints: list,   # list[StyleFingerprint]
    session_data: SessionData,
) -> go.Figure:
    """Interaktywny radar 10 metryk stylu jazdy."""
    if not fingerprints:
        return go.Figure()

    # Etykiety bez newline
    labels = [lbl.replace("\n", " ") for lbl in METRIC_LABELS]
    # Radar wymaga zamknięcia pętli
    labels_closed = labels + [labels[0]]

    fig = go.Figure()

    for fp in fingerprints:
        vals = [getattr(fp, f) for f in METRIC_FIELDS]
        vals_closed = vals + [vals[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor=_rgba(fp.color, 0.12),
            line=dict(color=fp.color, width=2),
            name=fp.driver,
            hovertemplate=(
                f"<b>{fp.driver}</b><br>"
                "%{theta}: %{r:.1f}<extra></extra>"
            ),
        ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Styl jazdy  |  {session_data.session_type}"
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color="#FFFFFF", size=15, family="Courier New")),
        paper_bgcolor=_BG,
        font=dict(color=_TEXT, family="Courier New", size=13),
        height=650,
        legend=dict(bgcolor="#222222", bordercolor="#444444", borderwidth=1,
                    font=dict(color=_TEXT)),
        margin=dict(l=60, r=60, t=70, b=60),
        hoverlabel=dict(bgcolor="#1A1A1A", bordercolor="#444444", font_color="#FFFFFF"),
        polar=dict(
            bgcolor=_PLOT,
            angularaxis=dict(
                gridcolor=_GRID,
                linecolor="#444444",
                tickfont=dict(color=_TEXT, size=11),
            ),
            radialaxis=dict(
                range=[0, 105],
                gridcolor=_GRID,
                linecolor="#444444",
                tickfont=dict(color=_AXIS, size=10),
                tickvals=[20, 40, 60, 80, 100],
            ),
        ),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 6. SŁUPKI STYLU JAZDY
# ══════════════════════════════════════════════════════════════════════════════
def plot_style_bars_interactive(
    fingerprints: list,   # list[StyleFingerprint]
    session_data: SessionData,
) -> go.Figure:
    """Interaktywny wykres słupkowy 10 metryk stylu jazdy."""
    if not fingerprints:
        return go.Figure()

    labels = [lbl.replace("\n", " ") for lbl in METRIC_LABELS]

    fig = go.Figure()

    for fp in fingerprints:
        vals = [getattr(fp, f) for f in METRIC_FIELDS]
        fig.add_trace(go.Bar(
            y=labels,
            x=vals,
            name=fp.driver,
            orientation="h",
            marker=dict(color=fp.color, line=dict(width=0)),
            hovertemplate=(
                f"<b>{fp.driver}</b><br>"
                "%{y}: %{x:.1f}<extra></extra>"
            ),
        ))

    # Linia referencyjna przy 50
    fig.add_vline(x=50, line=dict(color="#555555", width=1, dash="dash"))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Metryki stylu jazdy  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=max(550, len(labels) * 55 + 150))

    fig.update_layout(
        barmode="group",
        xaxis=dict(**_axis("Wartość (0–100)"), range=[0, 115]),
        yaxis=dict(**_axis(), categoryorder="array", categoryarray=labels[::-1]),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 7. MAPA DOMINACJI NA TORZE
# ══════════════════════════════════════════════════════════════════════════════
def plot_driver_dominance_map_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    n_points: int = 2000,
) -> Optional[go.Figure]:
    """Mapa toru: każdy segment pokolorowany kierowcą, który był najszybszy."""
    if not drivers_data:
        return None

    sample = next(iter(drivers_data.values()))
    if "X" not in sample.telemetry.columns:
        return None

    # Resample do wspólnej siatki
    max_dist = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    common   = np.linspace(0, max_dist, n_points)

    driver_speeds: dict[str, np.ndarray] = {}
    ref_xy: tuple[np.ndarray, np.ndarray] = (np.array([]), np.array([]))

    for i, (drv, data) in enumerate(drivers_data.items()):
        xi, yi, spd = _resample_xy(data.telemetry, "Speed", n_points)
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
        marker=dict(color="#1A1A1A", size=12),
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
        marker=dict(color="#FFFF00", size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color="#FFFF00", size=10),
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Dominacja na torze  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=720)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor="#0A0A0A",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 8. MAPA PRĘDKOŚCI NA TORZE
# ══════════════════════════════════════════════════════════════════════════════
def plot_speed_heatmap_track_interactive(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = 2000,
) -> Optional[go.Figure]:
    """Mapa prędkości jednego kierowcy na torze (gradient kolorów)."""
    telem = driver_data.telemetry
    if "X" not in telem.columns:
        return None

    xi, yi, spd = _resample_xy(telem, "Speed", n_points)
    if len(xi) == 0:
        return None

    fig = go.Figure()

    # Tło toru
    fig.add_trace(go.Scatter(
        x=xi, y=yi,
        mode="markers",
        marker=dict(color="#1A1A1A", size=12),
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
                title=dict(text="V [km/h]", font=dict(color=_TEXT)),
                tickfont=dict(color=_AXIS),
                bgcolor=_PLOT,
                bordercolor="#444444",
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
        marker=dict(color="#FFFF00", size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color="#FFFF00", size=10),
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{driver_data.driver}  |  Mapa prędkości  |  "
        f"{session_data.event_name} {session_data.year} [{session_data.session_type}]"
    )
    _dark(fig, title=title, height=650)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor="#0A0A0A",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 9. MAPA BIEGÓW NA TORZE
# ══════════════════════════════════════════════════════════════════════════════
def plot_gear_map_interactive(
    driver_data: DriverLapData,
    session_data: SessionData,
    n_points: int = 2000,
) -> Optional[go.Figure]:
    """Mapa biegów jednego kierowcy na torze (kolor per bieg)."""
    telem = driver_data.telemetry
    if "X" not in telem.columns or "nGear" not in telem.columns:
        return None

    xi, yi, gear = _resample_xy(telem, "nGear", n_points)
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
        marker=dict(color="#1A1A1A", size=12),
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
        marker=dict(color="#FFFF00", size=12, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color="#FFFF00", size=10),
        showlegend=False, hoverinfo="skip",
    ))

    title = (
        f"{driver_data.driver}  |  Mapa biegów  |  "
        f"{session_data.event_name} {session_data.year} [{session_data.session_type}]"
    )
    _dark(fig, title=title, height=650)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor="#0A0A0A",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 10. RACE PACE
# ══════════════════════════════════════════════════════════════════════════════
_COMPOUND_SYMBOL: dict[str, str] = {
    "SOFT":         "circle",
    "MEDIUM":       "square",
    "HARD":         "diamond",
    "INTERMEDIATE": "triangle-up",
    "WET":          "triangle-down",
    "UNKNOWN":      "x",
}
_COMPOUND_COLOR: dict[str, str] = {
    "SOFT":         "#FF3333",
    "MEDIUM":       "#FFD700",
    "HARD":         "#EEEEEE",
    "INTERMEDIATE": "#39B54A",
    "WET":          "#4499FF",
    "UNKNOWN":      "#888888",
}


def plot_race_pace_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> go.Figure:
    """
    Tempo wyścigu: czas okrążenia vs numer okrążenia.
    Scatter per opona + linia trendu (rolling avg) + pasek składu opon.
    """
    if race_pace_df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[5, 1],
        vertical_spacing=0.03,
        subplot_titles=["Czas okrążenia [s]", "Opona / stint"],
    )

    drivers = race_pace_df["Driver"].unique()

    for drv in drivers:
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber")
        if drv_df.empty:
            continue
        color = drv_df["Color"].iloc[0]
        laps = drv_df["LapNumber"].values
        times = drv_df["LapTime_s"].values

        # Rolling average (window 3–5)
        win = min(5, max(3, len(times)))
        rolling = (
            pd.Series(times)
            .rolling(win, center=True, min_periods=1)
            .mean()
            .values
        )

        # Scatter per compound type
        shown_legend_for_drv = False
        for compound in drv_df["Compound"].unique():
            mask = drv_df["Compound"] == compound
            sub = drv_df[mask]
            symbol = _COMPOUND_SYMBOL.get(compound, "circle")
            c_border = _COMPOUND_COLOR.get(compound, "#888888")

            fig.add_trace(go.Scatter(
                x=sub["LapNumber"],
                y=sub["LapTime_s"],
                mode="markers",
                marker=dict(
                    color=color,
                    symbol=symbol,
                    size=9,
                    line=dict(color=c_border, width=1.8),
                ),
                name=f"{drv}",
                legendgroup=drv,
                showlegend=not shown_legend_for_drv,
                hovertemplate=(
                    f"<b>{drv}</b><br>"
                    "Okrążenie: %{x}<br>"
                    f"Czas: %{{y:.3f}} s<br>"
                    f"Opona: {compound}<extra></extra>"
                ),
            ), row=1, col=1)
            shown_legend_for_drv = True

        # Trend
        fig.add_trace(go.Scatter(
            x=laps, y=rolling,
            mode="lines",
            line=dict(color=color, width=2.2),
            legendgroup=drv,
            showlegend=False,
            hoverinfo="skip",
        ), row=1, col=1)

    # Compound color legend entries (once each)
    added_compounds: set[str] = set()
    for drv in drivers:
        drv_df = race_pace_df[race_pace_df["Driver"] == drv]
        for compound in drv_df["Compound"].unique():
            if compound in added_compounds:
                continue
            added_compounds.add(compound)
            c_color = _COMPOUND_COLOR.get(compound, "#888888")
            symbol = _COMPOUND_SYMBOL.get(compound, "circle")
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(color=c_color, symbol=symbol, size=10),
                name=compound,
                legendgroup=f"_cpd_{compound}",
                showlegend=True,
            ), row=1, col=1)

    # Stint compound bars (row 2) — one colored bar per lap per driver
    for drv_i, drv in enumerate(drivers):
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber")
        if drv_df.empty:
            continue
        offset = drv_i * 0.8
        for compound in drv_df["Compound"].unique():
            mask = drv_df["Compound"] == compound
            sub_laps = drv_df[mask]["LapNumber"].values
            c_color = _COMPOUND_COLOR.get(compound, "#888888")
            fig.add_trace(go.Bar(
                x=sub_laps,
                y=[0.7] * len(sub_laps),
                base=offset,
                marker_color=c_color,
                marker_line_width=0,
                name=f"{drv} {compound}",
                legendgroup=drv,
                showlegend=False,
                hovertemplate=f"{drv}: {compound}  Lap %{{x}}<extra></extra>",
                width=0.9,
            ), row=2, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Race Pace  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=820)
    fig.update_layout(barmode="stack")
    fig.update_yaxes(**_axis("Czas [s]"),     row=1, col=1)
    fig.update_yaxes(visible=False,           row=2, col=1)
    fig.update_xaxes(**_axis("Okrążenie"),    row=2, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 11. ANIMACJA TORU
# ══════════════════════════════════════════════════════════════════════════════
def plot_track_animation_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    n_frames: int = 100,
) -> Optional[go.Figure]:
    """
    Animacja Plotly: pozycje kierowców poruszające się po torze.
    Wymaga danych GPS (kolumny X, Y w telemetrii).
    Osie czasu znormalizowane do 0–1 (procent ukończonego okrążenia).
    """
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
        t = data.telemetry
        dist = t["Distance"].values
        speed = np.maximum(t["Speed"].values, 1.0)
        step = np.diff(dist, prepend=dist[0])
        step = np.maximum(step, 0.0)
        dt = step / (speed / 3.6)
        cum_time = np.cumsum(dt)
        t_norm = cum_time / max(cum_time[-1], 1e-9)

        _, idx = np.unique(t_norm, return_index=True)
        t_u, x_u, y_u = t_norm[idx], t["X"].values[idx], t["Y"].values[idx]

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
    for w, c in [(12, "#222222"), (7, "#303030")]:
        fig.add_trace(go.Scatter(
            x=x_track, y=y_track, mode="lines",
            line=dict(color=c, width=w),
            showlegend=False, hoverinfo="skip",
        ))

    # Linia start/meta
    fig.add_trace(go.Scatter(
        x=[x_track[0]], y=[y_track[0]],
        mode="markers+text",
        marker=dict(color="#FFFF00", size=14, symbol="diamond"),
        text=["S/F"], textposition="top right",
        textfont=dict(color="#FFFF00", size=9, family="Courier New"),
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
                        line=dict(color="#FFFFFF", width=2)),
            text=[drv],
            textposition="top center",
            textfont=dict(color=pos["color"], size=9, family="Courier New"),
            name=f"{drv}  {pos['lap_time']}",
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
                            line=dict(color="#FFFFFF", width=2)),
                text=[drv],
                textposition="top center",
                textfont=dict(color=pos["color"], size=9, family="Courier New"),
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
            "bgcolor": "#1A1A1A",
            "bordercolor": "#444444",
            "font": {"color": "#CCCCCC"},
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
                "font": {"color": "#CCCCCC", "size": 11, "family": "Courier New"},
            },
            "bgcolor": "#1A1A1A",
            "bordercolor": "#444444",
            "font": {"color": "#AAAAAA", "size": 8},
            "tickcolor": "#444444",
        }],
    )

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Animacja okrążenia  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=820)
    fig.update_layout(
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        plot_bgcolor="#0A0A0A",
        margin=dict(l=30, r=30, t=70, b=140),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 12. DANE POGODOWE
# ══════════════════════════════════════════════════════════════════════════════
def plot_weather_interactive(
    weather_df: pd.DataFrame,
    session_data: SessionData,
) -> Optional[go.Figure]:
    """Dane pogodowe sesji: temperatury powietrza/toru, wiatr, wilgotność, opady."""
    if weather_df is None or weather_df.empty:
        return None

    if "Time" in weather_df.columns:
        mins = weather_df["Time"].dt.total_seconds() / 60
    else:
        mins = np.arange(len(weather_df))

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        subplot_titles=["Temperatura [°C]", "Wiatr [m/s]  &  Wilgotność [%]", "Opady"],
    )

    if "AirTemp" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["AirTemp"],
            name="Powietrze [°C]", line=dict(color="#4da6ff", width=2.2),
            hovertemplate="Powietrze: %{y:.1f}°C<extra></extra>",
        ), row=1, col=1)

    if "TrackTemp" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["TrackTemp"],
            name="Tor [°C]", line=dict(color="#ff7c4d", width=2.2),
            hovertemplate="Tor: %{y:.1f}°C<extra></extra>",
        ), row=1, col=1)

    if "WindSpeed" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["WindSpeed"],
            name="Wiatr [m/s]", line=dict(color="#c8ff3d", width=1.8),
            hovertemplate="Wiatr: %{y:.1f} m/s<extra></extra>",
        ), row=2, col=1)

    if "Humidity" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["Humidity"],
            name="Wilgotność [%]", line=dict(color="#a78bfa", width=1.8, dash="dot"),
            hovertemplate="Wilgotność: %{y:.1f}%<extra></extra>",
        ), row=2, col=1)

    if "Rainfall" in weather_df.columns:
        rain = pd.to_numeric(weather_df["Rainfall"], errors="coerce").fillna(0).astype(float)
        fig.add_trace(go.Bar(
            x=mins, y=rain,
            name="Opady", marker_color="#00d4ff", opacity=0.8,
            hovertemplate="Opady: %{y}<extra></extra>",
        ), row=3, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Warunki pogodowe  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=650)
    fig.update_yaxes(**_axis("Temp [°C]"),     row=1, col=1)
    fig.update_yaxes(**_axis("Wiatr / Wilg."), row=2, col=1)
    fig.update_yaxes(**_axis("Opady"),          row=3, col=1)
    fig.update_xaxes(**_axis("Czas [min]"),     row=3, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 13. DEGRADACJA OPON
# ══════════════════════════════════════════════════════════════════════════════
def plot_tire_degradation_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> go.Figure:
    """Degradacja opon per stint — czas okrążenia vs numer okrążenia z regresją liniową."""
    if race_pace_df is None or race_pace_df.empty:
        return go.Figure()

    fig = go.Figure()

    for drv in race_pace_df["Driver"].unique():
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber").copy()
        if drv_df.empty:
            continue
        color = drv_df["Color"].iloc[0]

        # Wykryj stinty przez zmianę składu opony
        stint_ids, stint_n, prev = [], 1, drv_df["Compound"].iloc[0]
        for compound in drv_df["Compound"]:
            if compound != prev:
                stint_n += 1
                prev = compound
            stint_ids.append(stint_n)
        drv_df["Stint"] = stint_ids

        for s_num, s_df in drv_df.groupby("Stint"):
            if len(s_df) < 2:
                continue
            compound  = s_df["Compound"].iloc[0]
            laps      = s_df["LapNumber"].values
            times     = s_df["LapTime_s"].values
            laps_norm = laps - laps[0]
            coeffs    = np.polyfit(laps_norm, times, 1)
            trend     = np.poly1d(coeffs)(laps_norm)
            deg_rate  = coeffs[0]
            label     = f"{drv}  Stint {s_num}  ({compound})  {deg_rate:+.3f} s/lap"

            fig.add_trace(go.Scatter(
                x=laps, y=times,
                mode="markers",
                marker=dict(color=color, size=8, opacity=0.65),
                name=label, legendgroup=f"{drv}_{s_num}",
                showlegend=True,
                hovertemplate=(
                    f"<b>{drv}  Stint {s_num}</b><br>"
                    "Okrążenie: %{x}<br>Czas: %{y:.3f} s<extra></extra>"
                ),
            ))
            fig.add_trace(go.Scatter(
                x=laps, y=trend,
                mode="lines",
                line=dict(color=color, width=2.2, dash="dot"),
                legendgroup=f"{drv}_{s_num}", showlegend=False,
                hovertemplate=f"Trend ({deg_rate:+.4f} s/lap): %{{y:.3f}}s<extra></extra>",
            ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Degradacja opon  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=700)
    fig.update_yaxes(**_axis("Czas okrążenia [s]"))
    fig.update_xaxes(**_axis("Okrążenie"))
    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 14. SEKTORY  PURPLE / GREEN / YELLOW
# ══════════════════════════════════════════════════════════════════════════════
def plot_sector_colors_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> go.Figure:
    """
    Kolorowanie sektorów jak w F1 TV:
    🟣 Fioletowy = najlepszy w polu  |  🟢 Zielony ≤ +0.3 s  |  🟡 Żółty = wolniejszy.
    """
    if not drivers_data:
        return go.Figure()

    sector_fields = {"S1": "sector1", "S2": "sector2", "S3": "sector3"}

    best_sector: dict[str, float] = {}
    for sec, field in sector_fields.items():
        times = [getattr(d, field) for d in drivers_data.values() if getattr(d, field) > 0]
        best_sector[sec] = min(times) if times else 0.0

    fig = go.Figure()

    for drv in drivers_data:
        d = drivers_data[drv]
        bar_colors, bar_texts, bar_vals, bar_secs = [], [], [], []

        for sec, field in sector_fields.items():
            val = getattr(d, field)
            if val <= 0:
                continue
            gap = val - best_sector[sec]

            if abs(gap) < 0.001:
                cell_color, extra = "#CC00FF", " ⬡"
            elif gap <= 0.300:
                cell_color, extra = "#00C853", ""
            else:
                cell_color, extra = "#FFD600", ""

            bar_colors.append(cell_color)
            bar_texts.append(f"{val:.3f}s{extra}<br>+{gap:.3f}")
            bar_vals.append(val)
            bar_secs.append(sec)

        fig.add_trace(go.Bar(
            x=bar_secs,
            y=bar_vals,
            name=drv,
            marker_color=bar_colors,
            text=bar_texts,
            textposition="inside",
            textfont=dict(color="#FFFFFF", size=12, family="Courier New"),
            legendgroup=drv,
            offsetgroup=drv,
            hovertemplate=(
                f"<b>{drv}</b><br>"
                "Sektor: %{x}<br>Czas: %{y:.3f} s<extra></extra>"
            ),
        ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Sektory  🟣 Purple / 🟢 Green / 🟡 Yellow  |  {session_data.session_type}"
    )
    fig.update_layout(barmode="group")
    _dark(fig, title=title, height=550)
    fig.update_yaxes(**_axis("Czas [s]"))
    fig.update_xaxes(**_axis("Sektor"))
    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 16. DELTA CZASU — dedykowany wykres
# ══════════════════════════════════════════════════════════════════════════════
def plot_delta_time_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    corner_analysis=None,
) -> Optional[go.Figure]:
    """Delta czasu po dystansie względem najszybszego kierowcy, z adnotacjami zakrętów."""
    if len(drivers_data) < 2:
        return None

    common = _common_d(drivers_data)
    ref    = min(drivers_data.values(), key=lambda d: d.lap_time)
    step   = np.diff(common, prepend=common[0])

    ref_spd = _interp(ref.telemetry, "Speed", common)
    ref_dt  = np.where(ref_spd > 1, step / (ref_spd / 3.6), 0)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=common, y=np.zeros_like(common),
        name=f"{ref.driver}  {ref.lap_time_str}  (ref)",
        line=dict(color=ref.color, width=1.5, dash="dot"),
        hoverinfo="skip",
    ))

    for drv, data in drivers_data.items():
        if drv == ref.driver:
            continue
        spd   = _interp(data.telemetry, "Speed", common)
        dt    = np.where(spd > 1, step / (spd / 3.6), 0)
        delta = np.cumsum(dt - ref_dt)

        fig.add_trace(go.Scatter(
            x=common, y=delta,
            name=f"{drv}  {data.lap_time_str}",
            line=dict(color=data.color, width=2.2),
            fill="tozeroy",
            fillcolor=_rgba(data.color, 0.10),
            hovertemplate=(
                f"<b>{drv} vs {ref.driver}</b><br>"
                "Dystans: %{x:.0f} m<br>"
                "Δt: %{y:+.3f} s<br>"
                "<i>+ = wolniej, − = szybciej od ref</i><extra></extra>"
            ),
        ))

    if corner_analysis and corner_analysis.corners:
        for c in corner_analysis.corners:
            fig.add_vline(x=c["distance"], line=dict(color="#383838", width=1))
            fig.add_annotation(
                x=c["distance"], xanchor="center",
                y=1.0, yref="paper", yanchor="bottom",
                text=f"T{c['id']}", showarrow=False,
                font=dict(color="#666666", size=9, family="Courier New"),
            )

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Delta czasu  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=480)
    fig.update_layout(
        hovermode="x unified",
        yaxis=dict(
            **_axis("Δt [s]  (+ wolniej od ref)"),
            zeroline=True, zerolinecolor="#555555", zerolinewidth=1,
        ),
        xaxis=dict(**_axis("Dystans [m]")),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 17. PUNKTY HAMOWANIA PER ZAKRĘT
# ══════════════════════════════════════════════════════════════════════════════
def plot_braking_points_interactive(
    drivers_data: dict[str, DriverLapData],
    corner_analysis,
    session_data: SessionData,
) -> Optional[go.Figure]:
    """
    Scatter punktów hamowania per zakręt:
      góra — absolutna pozycja na torze gdzie kierowca zaczyna hamować [m]
              (wyżej = późniejsze hamowanie = agresywniej)
      dół  — maksymalne ciśnienie hamulca [%]
    """
    if corner_analysis is None or not corner_analysis.corners:
        return None

    corners  = corner_analysis.corners[:16]
    c_labels = [f"T{c['id']}" for c in corners]
    drivers  = list(drivers_data.keys())

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=[
            "Punkt hamowania — pozycja na torze [m]  (wyżej = późniejsze hamowanie)",
            "Maksymalne ciśnienie hamulca [%]",
        ],
    )

    for drv in drivers:
        color  = drivers_data[drv].color
        ev_map = {e.corner_id: e for e in corner_analysis.driver_corners.get(drv, [])}

        braking_pts, max_brakes = [], []
        for c in corners:
            ev = ev_map.get(c["id"])
            braking_pts.append(ev.braking_point     if ev else None)
            max_brakes.append(ev.max_brake_pressure if ev else None)

        scatter_kw = dict(
            x=c_labels, name=drv, legendgroup=drv,
            mode="markers+lines",
            marker=dict(color=color, size=11, line=dict(color="#222222", width=1)),
            line=dict(color=color, width=1.4, dash="dot"),
        )

        fig.add_trace(go.Scatter(
            **scatter_kw, y=braking_pts, showlegend=True,
            hovertemplate=(
                f"<b>{drv}</b><br>Zakręt: %{{x}}<br>"
                "Hamowanie od: %{y:.0f} m<extra></extra>"
            ),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            **scatter_kw, y=max_brakes, showlegend=False,
            hovertemplate=(
                f"<b>{drv}</b><br>Zakręt: %{{x}}<br>"
                "Maks. hamulec: %{y:.1f}%<extra></extra>"
            ),
        ), row=2, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Analiza punktów hamowania  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=720)
    fig.update_yaxes(**_axis("Pozycja [m]"),   row=1, col=1)
    fig.update_yaxes(**_axis("Ciśnienie [%]"), row=2, col=1)
    fig.update_xaxes(**_axis("Zakręt"),         row=2, col=1)

    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 18. POZYCJE W WYŚCIGU
# ══════════════════════════════════════════════════════════════════════════════
def plot_position_interactive(
    position_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> Optional[go.Figure]:
    """Pozycja kierowcy okrążenie po okrążeniu (oś Y odwrócona — P1 na górze)."""
    if position_df is None or position_df.empty:
        return None

    fig = go.Figure()

    for drv in position_df["Driver"].unique():
        drv_df = position_df[position_df["Driver"] == drv].sort_values("LapNumber")
        if drv_df.empty:
            continue
        color = drv_df["Color"].iloc[0]

        fig.add_trace(go.Scatter(
            x=drv_df["LapNumber"],
            y=drv_df["Position"],
            name=drv,
            line=dict(color=color, width=2.2),
            mode="lines",
            hovertemplate=(
                f"<b>{drv}</b><br>"
                "Okrążenie: %{x}<br>"
                "Pozycja: P%{y}<extra></extra>"
            ),
        ))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Pozycje w wyścigu  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=580)
    fig.update_layout(
        yaxis=dict(
            **_axis("Pozycja"),
            autorange="reversed",
            tickvals=list(range(1, 21)),
            dtick=1,
        ),
        xaxis=dict(**_axis("Okrążenie")),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 19. PODZIAŁ NA STINTY (GANTT)
# ══════════════════════════════════════════════════════════════════════════════
def plot_stint_overview_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> Optional[go.Figure]:
    """Podział na stinty: poziome paski per kierowca, kolorowane składem opony."""
    if race_pace_df is None or race_pace_df.empty:
        return None

    drivers = sorted(race_pace_df["Driver"].unique())
    fig     = go.Figure()
    added_compounds: set[str] = set()

    for drv in drivers:
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber").copy()
        if drv_df.empty:
            continue

        drv_df["_new"] = drv_df["Compound"] != drv_df["Compound"].shift()
        drv_df["_sid"] = drv_df["_new"].cumsum()

        for _, stint_df in drv_df.groupby("_sid"):
            compound  = str(stint_df["Compound"].iloc[0])
            lap_start = int(stint_df["LapNumber"].min())
            lap_end   = int(stint_df["LapNumber"].max())
            n_laps    = lap_end - lap_start + 1
            c_color   = _COMPOUND_COLOR.get(compound, "#888888")
            txt_color = "#000000" if compound in ("MEDIUM", "HARD", "INTERMEDIATE") else "#FFFFFF"

            fig.add_trace(go.Bar(
                x=[n_laps],
                y=[drv],
                base=lap_start - 1,
                orientation="h",
                marker_color=c_color,
                marker_line_color=_BG,
                marker_line_width=2,
                name=compound,
                legendgroup=f"cpd_{compound}",
                showlegend=compound not in added_compounds,
                text=compound[:1] if n_laps >= 3 else "",
                textposition="inside",
                textfont=dict(color=txt_color, size=10, family="Courier New"),
                hovertemplate=(
                    f"<b>{drv}</b>  {compound}<br>"
                    f"Okrążenia: {lap_start}–{lap_end}  ({n_laps} kółek)<extra></extra>"
                ),
            ))
            added_compounds.add(compound)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Podział na stinty  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=max(350, len(drivers) * 55 + 160))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(**_axis("Numer okrążenia")),
        yaxis=dict(
            **_axis("Kierowca"),
            categoryorder="array",
            categoryarray=drivers[::-1],
        ),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 15. ANALIZA DRS
# ══════════════════════════════════════════════════════════════════════════════
def plot_drs_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
) -> Optional[go.Figure]:
    """Analiza DRS: strefy aktywacji na mapie toru + rozkład prędkości DRS on vs off."""
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
                marker=dict(color="#1A1A1A", size=9),
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
                    marker=dict(color="#00FF88", size=7, opacity=0.95),
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
                fillcolor=_rgba(data.color, alpha),
                box_visible=True, meanline_visible=True,
                legendgroup=drv, showlegend=False,
                hovertemplate=f"<b>{drv} DRS {label}</b><br>V: %{{y:.0f}} km/h<extra></extra>",
                x0=f"{drv} {label}",
            ), row=1, col=col_spd)

    if has_gps and col_map:
        fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, row=1, col=col_map)
        fig.update_yaxes(visible=False, row=1, col=col_map)

    fig.update_yaxes(**_axis("V [km/h]"), row=1, col=col_spd)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Analiza DRS  |  {session_data.session_type}"
    )
    _dark(fig, title=title, height=680)
    for ann in fig.layout.annotations:
        ann.font = dict(color="#AAAAAA", size=11, family="Courier New")

    return fig
