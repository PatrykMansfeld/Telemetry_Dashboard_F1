"""Wykresy telemetrii: przebiegi kanałów i delta czasu."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_loader import DriverLapData, SessionData
from ._resample import common_distance, interp
from .theme import DEFAULT_THEME, FONT_MONO, get_theme, rgba


def plot_telemetry_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywne porównanie telemetrii: prędkość, delta, gaz, hamulec, biegi, RPM."""
    t = get_theme(theme)
    if not drivers_data:
        return go.Figure()

    common = common_distance(drivers_data)
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
        brake = interp(d.telemetry, "Brake", common)
        if brake.max() <= 1.0:
            brake = brake * 100
        di[d.driver] = {
            "speed":    interp(d.telemetry, "Speed",    common),
            "throttle": interp(d.telemetry, "Throttle", common),
            "brake":    brake,
            "gear":     np.clip(np.round(interp(d.telemetry, "nGear", common)), 1, 8),
            "rpm":      interp(d.telemetry, "RPM",      common),
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
                fill="tozeroy", fillcolor=rgba(c, 0.10),
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
            fill="tozeroy", fillcolor=rgba(c, 0.07),
            hovertemplate=f"<b>{d.driver}</b><br>Gaz: %{{y:.0f}}%<extra></extra>",
        ), row=3, col=1)

        # ── Hamulec ───────────────────────────────────────────────────────────
        fig.add_trace(go.Scatter(
            x=common, y=di[d.driver]["brake"],
            name=lbl, line=dict(color=c, width=1),
            legendgroup=d.driver, showlegend=False,
            fill="tozeroy", fillcolor=rgba(c, 0.07),
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
    t.style(fig, title=title, height=1100)

    fig.update_yaxes(**t.axis("V [km/h]"),       row=1, col=1)
    fig.update_yaxes(**t.axis("Δt [s]"),          row=2, col=1)
    fig.update_yaxes(**t.axis("Gaz [%]"),         row=3, col=1, range=[0, 108])
    fig.update_yaxes(**t.axis("Ham [%]"),         row=4, col=1, range=[-5, 108])
    fig.update_yaxes(**t.axis("Bieg"),             row=5, col=1,
                     tickvals=list(range(1, 9)), range=[0.5, 8.5])
    fig.update_yaxes(**t.axis("RPM"),              row=6, col=1)
    fig.update_xaxes(**t.axis("Dystans [m]"),      row=6, col=1)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 2. ANALIZA ZAKRĘTÓW
# ══════════════════════════════════════════════════════════════════════════════

def plot_delta_time_interactive(
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    corner_analysis=None,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Delta czasu po dystansie względem najszybszego kierowcy, z adnotacjami zakrętów."""
    t = get_theme(theme)
    if len(drivers_data) < 2:
        return None

    common = common_distance(drivers_data)
    ref    = min(drivers_data.values(), key=lambda d: d.lap_time)
    step   = np.diff(common, prepend=common[0])

    ref_spd = interp(ref.telemetry, "Speed", common)
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
        spd   = interp(data.telemetry, "Speed", common)
        dt    = np.where(spd > 1, step / (spd / 3.6), 0)
        delta = np.cumsum(dt - ref_dt)

        fig.add_trace(go.Scatter(
            x=common, y=delta,
            name=f"{drv}  {data.lap_time_str}",
            line=dict(color=data.color, width=2.2),
            fill="tozeroy",
            fillcolor=rgba(data.color, 0.10),
            hovertemplate=(
                f"<b>{drv} vs {ref.driver}</b><br>"
                "Dystans: %{x:.0f} m<br>"
                "Δt: %{y:+.3f} s<br>"
                "<i>+ = wolniej, − = szybciej od ref</i><extra></extra>"
            ),
        ))

    if corner_analysis and corner_analysis.corners:
        for c in corner_analysis.corners:
            fig.add_vline(x=c["distance"], line=dict(color=t.corner_line, width=1))
            fig.add_annotation(
                x=c["distance"], xanchor="center",
                y=1.0, yref="paper", yanchor="bottom",
                text=c.get("name") or f"T{c['id']}", showarrow=False,
                font=dict(color=t.corner_text, size=9, family=FONT_MONO),
            )

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Delta czasu  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=480)
    fig.update_layout(
        hovermode="x unified",
        # Oś zerowa mocniej zaznaczona niż siatka — stąd nadpisanie zerolinecolor.
        yaxis={
            **t.axis("Δt [s]  (+ wolniej od ref)"),
            "zeroline": True, "zerolinecolor": t.soft, "zerolinewidth": 1,
        },
        xaxis=dict(**t.axis("Dystans [m]")),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 17. PUNKTY HAMOWANIA PER ZAKRĘT
# ══════════════════════════════════════════════════════════════════════════════
