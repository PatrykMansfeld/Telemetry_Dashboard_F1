"""Wykresy wyścigowe: tempo, degradacja opon, pozycje, stinty."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..data_loader import DriverLapData, SessionData
from .theme import DEFAULT_THEME, FONT_MONO, get_theme

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


# Opona HARD jest w F1 biała — na jasnym motywie trzeba ją przyciemnić,
# inaczej znika na tle wykresu.
_COMPOUND_COLOR_LIGHT: dict[str, str] = {"HARD": "#9AA5B1", "UNKNOWN": "#6B7280"}


def compound_color(compound: str, t) -> str:
    """Kolor składu opony dopasowany do motywu."""
    if t.name == "light" and compound in _COMPOUND_COLOR_LIGHT:
        return _COMPOUND_COLOR_LIGHT[compound]
    return _COMPOUND_COLOR.get(compound, _COMPOUND_COLOR["UNKNOWN"])

def plot_race_pace_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """
    Tempo wyścigu: czas okrążenia vs numer okrążenia.
    Scatter per opona + linia trendu (rolling avg) + pasek składu opon.
    """
    t = get_theme(theme)
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
            c_border = compound_color(compound, t)

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
            c_color = compound_color(compound, t)
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
            c_color = compound_color(compound, t)
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
    t.style(fig, title=title, height=820)
    fig.update_layout(barmode="stack")
    fig.update_yaxes(**t.axis("Czas [s]"),     row=1, col=1)
    fig.update_yaxes(visible=False,           row=2, col=1)
    fig.update_xaxes(**t.axis("Okrążenie"),    row=2, col=1)


    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 11. ANIMACJA TORU
# ══════════════════════════════════════════════════════════════════════════════

def _stint_ids(drv_df: pd.DataFrame) -> pd.Series:
    """
    Numery stintów kierowcy.

    Pierwszeństwo ma kolumna `Stint` z FastF1 (uwzględnia każdy pit stop);
    dopiero gdy jej brak, dzielimy przejazd po zmianach składu opony.
    """
    if "Stint" in drv_df.columns and drv_df["Stint"].gt(0).all():
        return drv_df["Stint"].astype(int)
    return (drv_df["Compound"] != drv_df["Compound"].shift()).cumsum()


def plot_tire_degradation_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Degradacja opon per stint — czas okrążenia vs numer okrążenia z regresją liniową."""
    t = get_theme(theme)
    if race_pace_df is None or race_pace_df.empty:
        return go.Figure()

    fig = go.Figure()

    for drv in race_pace_df["Driver"].unique():
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber").copy()
        if drv_df.empty:
            continue
        color = drv_df["Color"].iloc[0]

        # Numer stintu podaje FastF1; sami wykrywalibyśmy tylko zmiany opony,
        # więc pit stop na tę samą mieszankę zostałby przeoczony.
        drv_df["_stint"] = _stint_ids(drv_df)

        for s_num, s_df in drv_df.groupby("_stint"):
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
    t.style(fig, title=title, height=700)
    fig.update_yaxes(**t.axis("Czas okrążenia [s]"))
    fig.update_xaxes(**t.axis("Okrążenie"))

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 14. SEKTORY  PURPLE / GREEN / YELLOW
# ══════════════════════════════════════════════════════════════════════════════

def plot_position_interactive(
    position_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Pozycja kierowcy okrążenie po okrążeniu (oś Y odwrócona — P1 na górze)."""
    t = get_theme(theme)
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
    t.style(fig, title=title, height=580)
    fig.update_layout(
        yaxis=dict(
            **t.axis("Pozycja"),
            autorange="reversed",
            tickvals=list(range(1, 21)),
            dtick=1,
        ),
        xaxis=dict(**t.axis("Okrążenie")),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 19. PODZIAŁ NA STINTY (GANTT)
# ══════════════════════════════════════════════════════════════════════════════

def plot_stint_overview_interactive(
    race_pace_df: pd.DataFrame,
    drivers_data: dict[str, DriverLapData],
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure | None:
    """Podział na stinty: poziome paski per kierowca, kolorowane składem opony."""
    t = get_theme(theme)
    if race_pace_df is None or race_pace_df.empty:
        return None

    drivers = sorted(race_pace_df["Driver"].unique())
    fig     = go.Figure()
    added_compounds: set[str] = set()

    for drv in drivers:
        drv_df = race_pace_df[race_pace_df["Driver"] == drv].sort_values("LapNumber").copy()
        if drv_df.empty:
            continue

        drv_df["_stint"] = _stint_ids(drv_df)

        for _, stint_df in drv_df.groupby("_stint"):
            compound  = str(stint_df["Compound"].iloc[0])
            lap_start = int(stint_df["LapNumber"].min())
            lap_end   = int(stint_df["LapNumber"].max())
            n_laps    = lap_end - lap_start + 1
            c_color   = compound_color(compound, t)
            txt_color = "#000000" if compound in ("MEDIUM", "HARD", "INTERMEDIATE") else "#FFFFFF"

            fig.add_trace(go.Bar(
                x=[n_laps],
                y=[drv],
                base=lap_start - 1,
                orientation="h",
                marker_color=c_color,
                marker_line_color=t.bg,
                marker_line_width=2,
                name=compound,
                legendgroup=f"cpd_{compound}",
                showlegend=compound not in added_compounds,
                text=compound[:1] if n_laps >= 3 else "",
                textposition="inside",
                textfont=dict(color=txt_color, size=10, family=FONT_MONO),
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
    t.style(fig, title=title, height=max(350, len(drivers) * 55 + 160))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(**t.axis("Numer okrążenia")),
        yaxis=dict(
            **t.axis("Kierowca"),
            categoryorder="array",
            categoryarray=drivers[::-1],
        ),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 15. ANALIZA DRS
# ══════════════════════════════════════════════════════════════════════════════
