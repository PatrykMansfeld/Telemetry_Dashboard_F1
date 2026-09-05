"""Wykresy stylu jazdy: radar i słupki metryk."""

from __future__ import annotations

import plotly.graph_objects as go

from ..data_loader import SessionData
from ..driver_style import METRIC_FIELDS, METRIC_LABELS
from .theme import DEFAULT_THEME, get_theme, rgba


def plot_radar_interactive(
    fingerprints: list,   # list[StyleFingerprint]
    session_data: SessionData,
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywny radar 10 metryk stylu jazdy."""
    t = get_theme(theme)
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
            fillcolor=rgba(fp.color, 0.12),
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
    t.style(fig, title=title, height=650)
    fig.update_layout(
        # Podpisy metryk są długie („Agresywność hamowania”) — bez szerokich
        # marginesów obcinają się, gdy radar stoi w wąskiej kolumnie.
        margin=dict(l=110, r=110, t=70, b=60),
        polar=dict(
            bgcolor=t.plot,
            angularaxis=dict(
                gridcolor=t.grid,
                linecolor=t.border,
                tickfont=dict(color=t.text, size=11),
            ),
            radialaxis=dict(
                range=[0, 105],
                gridcolor=t.grid,
                linecolor=t.border,
                tickfont=dict(color=t.tick, size=10),
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
    theme: str = DEFAULT_THEME,
) -> go.Figure:
    """Interaktywny wykres słupkowy 10 metryk stylu jazdy."""
    t = get_theme(theme)
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
    fig.add_vline(x=50, line=dict(color=t.soft, width=1, dash="dash"))

    title = (
        f"{session_data.event_name} {session_data.year}  |  "
        f"Metryki stylu jazdy  |  {session_data.session_type}"
    )
    t.style(fig, title=title, height=max(550, len(labels) * 55 + 150))

    fig.update_layout(
        barmode="group",
        xaxis=dict(**t.axis("Wartość (0–100)"), range=[0, 115]),
        yaxis=dict(**t.axis(), categoryorder="array", categoryarray=labels[::-1]),
    )

    return fig


# ══════════════════════════════════════════════════════════════════════════════
# 7. MAPA DOMINACJI NA TORZE
# ══════════════════════════════════════════════════════════════════════════════
