"""Wykresy sektorowe: mini-sektory, mapa ciepła, kolory S1/S2/S3."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_loader import DriverLapData, SessionData
from .theme import DEFAULT_THEME, FONT_MONO, get_theme, rgba


def plot_mini_sector_dominance_interactive(
    drivers_data: dict[str, DriverLapData],
    mini_sectors: list,   # list[MiniSector]
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywna dominacja mini-sektorów + delta czasu + prędkość."""
    t = get_theme(theme)
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
                fill="toself", fillcolor=rgba(color, 0.85),
                line=dict(width=0), name=drv,
                legendgroup=drv, showlegend=True,
                mode="lines",
                hovertemplate=f"<b>{drv}</b><br>Dominuje w tym mini-sektorze<extra></extra>",
            ), row=1, col=1)

    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_xaxes(showgrid=False, row=1, col=1)

    # ── Delta czasu ───────────────────────────────────────────────────────────
    fig.add_hline(y=0, line=dict(color=t.soft, width=1, dash="dash"), row=2, col=1)

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
            fill="tozeroy", fillcolor=rgba(color, 0.08),
            hovertemplate=(
                f"<b>{drv} vs {ref_drv}</b><br>"
                "Dist: %{x:.0f} m<br>"
                "Δt: %{y:.3f} s<extra></extra>"
            ),
        ), row=2, col=1)

    fig.update_yaxes(**t.axis("Δt [s]"), row=2, col=1)

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

    fig.update_yaxes(**t.axis("V [km/h]"),   row=3, col=1)
    fig.update_xaxes(**t.axis("Dystans [m]"), row=3, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Dominacja mini-sektorów  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=850)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 4. MAPA CIEPŁA SEKTORÓW
# ══════════════════════════════════════════════════════════════════════════════

def plot_sector_heatmap_interactive(
    stats_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywna mapa ciepła statystyk sektorowych."""
    t = get_theme(theme)
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
            textfont=dict(size=11, color=t.value_text, family=FONT_MONO),
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

        fig.update_xaxes(tickfont=dict(color=t.tick, size=10), row=1, col=col_i)
        if col_i == 1:
            fig.update_yaxes(tickfont=dict(color=t.tick, size=10), row=1, col=col_i)
        else:
            fig.update_yaxes(showticklabels=False, row=1, col=col_i)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Mapa ciepła sektorów  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=max(500, len(drivers) * 90 + 150))


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 5. RADAR STYLU JAZDY
# ══════════════════════════════════════════════════════════════════════════════

def plot_sector_colors_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """
    Kolorowanie sektorów jak w F1 TV:
    🟣 Fioletowy = najlepszy w polu  |  🟢 Zielony ≤ +0.3 s  |  🟡 Żółty = wolniejszy.
    """
    t = get_theme(theme)
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
            textfont=dict(color=t.value_text, size=12, family=FONT_MONO),
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
    t.style(fig, title=title, height=550)
    fig.update_yaxes(**t.axis("Czas [s]"))
    fig.update_xaxes(**t.axis("Sektor"))

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 16. DELTA CZASU — dedykowany wykres
# ══════════════════════════════════════════════════════════════════════════════
