"""Wykres warunków pogodowych sesji."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_loader import SessionData
from .theme import DEFAULT_THEME, get_theme

# Kolory serii pogodowych — dobrane tak, by były czytelne na jasnym i ciemnym tle.
COLOR_AIR      = "#2E86FF"
COLOR_TRACK    = "#FF6B35"
COLOR_WIND     = "#8AA300"
COLOR_HUMIDITY = "#7C4DFF"
COLOR_RAIN     = "#00A3CC"



def plot_weather_interactive(
    weather_df: pd.DataFrame,
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Dane pogodowe sesji: temperatury powietrza/toru, wiatr, wilgotność, opady."""
    t = get_theme(theme)
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
            name="Powietrze [°C]", line=dict(color=COLOR_AIR, width=2.2),
            hovertemplate="Powietrze: %{y:.1f}°C<extra></extra>",
        ), row=1, col=1)

    if "TrackTemp" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["TrackTemp"],
            name="Tor [°C]", line=dict(color=COLOR_TRACK, width=2.2),
            hovertemplate="Tor: %{y:.1f}°C<extra></extra>",
        ), row=1, col=1)

    if "WindSpeed" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["WindSpeed"],
            name="Wiatr [m/s]", line=dict(color=COLOR_WIND, width=1.8),
            hovertemplate="Wiatr: %{y:.1f} m/s<extra></extra>",
        ), row=2, col=1)

    if "Humidity" in weather_df.columns:
        fig.add_trace(go.Scatter(
            x=mins, y=weather_df["Humidity"],
            name="Wilgotność [%]", line=dict(color=COLOR_HUMIDITY, width=1.8, dash="dot"),
            hovertemplate="Wilgotność: %{y:.1f}%<extra></extra>",
        ), row=2, col=1)

    if "Rainfall" in weather_df.columns:
        rain = pd.to_numeric(weather_df["Rainfall"], errors="coerce").fillna(0).astype(float)
        fig.add_trace(go.Bar(
            x=mins, y=rain,
            name="Opady", marker_color=COLOR_RAIN, opacity=0.8,
            hovertemplate="Opady: %{y}<extra></extra>",
        ), row=3, col=1)

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Warunki pogodowe  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=650)
    fig.update_yaxes(**t.axis("Temp [°C]"),     row=1, col=1)
    fig.update_yaxes(**t.axis("Wiatr / Wilg."), row=2, col=1)
    fig.update_yaxes(**t.axis("Opady"),          row=3, col=1)
    fig.update_xaxes(**t.axis("Czas [min]"),     row=3, col=1)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 13. DEGRADACJA OPON
# ══════════════════════════════════════════════════════════════════════════════
