"""Wykresy analizy zakrętów: apeksy, hamowanie, wyjście."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..config import CORNER_PLOT_LIMIT
from ..data_loader import DriverLapData, SessionData
from .theme import DEFAULT_THEME, get_theme


def plot_corners_interactive(
    drivers_data: dict[str, DriverLapData],
    corner_analysis,   # CornerAnalysis
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywny wykres porównania zakrętów: prędkość, hamowanie, wyjście."""
    t = get_theme(theme)
    if corner_analysis is None or not corner_analysis.corners:
        return go.Figure()

    corners = corner_analysis.corners[:CORNER_PLOT_LIMIT]
    c_labels = [c.get("name") or f"T{c['id']}" for c in corners]
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
    t.style(fig, title=title, height=850)

    fig.update_yaxes(**t.axis("V [km/h]"),  row=1, col=1)
    fig.update_yaxes(**t.axis("Dystans [m]"), row=2, col=1)
    fig.update_yaxes(**t.axis("Dystans [m]"), row=3, col=1)
    fig.update_xaxes(**t.axis("Zakręt"),      row=3, col=1)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 3. DOMINACJA MINI-SEKTORÓW
# ══════════════════════════════════════════════════════════════════════════════

def plot_braking_points_interactive(
    drivers_data: dict[str, DriverLapData],
    corner_analysis,
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """
    Scatter punktów hamowania per zakręt:
      góra — absolutna pozycja na torze gdzie kierowca zaczyna hamować [m]
              (wyżej = późniejsze hamowanie = agresywniej)
      dół  — maksymalne ciśnienie hamulca [%]
    """
    t = get_theme(theme)
    if corner_analysis is None or not corner_analysis.corners:
        return None

    corners  = corner_analysis.corners[:CORNER_PLOT_LIMIT]
    c_labels = [c.get("name") or f"T{c['id']}" for c in corners]
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
            marker=dict(color=color, size=11, line=dict(color=t.marker_edge, width=1)),
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
    t.style(fig, title=title, height=720)
    fig.update_yaxes(**t.axis("Pozycja [m]"),   row=1, col=1)
    fig.update_yaxes(**t.axis("Ciśnienie [%]"), row=2, col=1)
    fig.update_xaxes(**t.axis("Zakręt"),         row=2, col=1)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 18. POZYCJE W WYŚCIGU
# ══════════════════════════════════════════════════════════════════════════════
