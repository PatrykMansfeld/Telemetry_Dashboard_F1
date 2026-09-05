"""
Motywy wykresów Plotly.

Cały kolor wykresu pochodzi z obiektu `PlotTheme` — nie ma zaszytych na sztywno
wartości w funkcjach rysujących. Dzięki temu ten sam wykres da się wyświetlić
w motywie ciemnym i jasnym, a już wygenerowaną figurę można przemalować przez
`restyle(fig, theme)` bez ponownego liczenia danych.
"""

from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go

FONT_MONO = "JetBrains Mono, Courier New, monospace"

# Role tras zależnych od motywu — ustawiane w `meta` przy tworzeniu trasy,
# odczytywane przez `restyle()`.
ROLE_TRACK_UNDER = "track_under"   # szeroki podkład toru pod mapą
ROLE_TRACK_LINE  = "track_line"    # obrys toru w animacji
ROLE_START       = "start_marker"  # znacznik linii start/meta
ROLE_DRIVER_DOT  = "driver_dot"    # kropka kierowcy w animacji


@dataclass(frozen=True)
class PlotTheme:
    """Paleta jednego motywu wykresów."""
    name: str
    bg: str            # tło całej figury
    plot: str          # tło obszaru kreślenia
    track_bg: str      # tło map toru
    grid: str          # siatka
    text: str          # tekst podstawowy
    tick: str          # etykiety osi
    subtitle: str      # tytuły subplotów
    heading: str       # tytuł figury
    border: str        # ramki legendy, colorbara, kontrolek
    legend_bg: str
    hover_bg: str
    hover_text: str
    soft: str          # linie pomocnicze (hline/vline)
    track_under: str   # podkład toru (trasa markerowa)
    track_wide: str    # gruba warstwa obrysu toru
    track_mid: str     # cieńsza warstwa obrysu toru
    dot_edge: str      # obwódka kropki kierowcy
    marker_edge: str   # obwódka markerów scatter
    start: str         # kolor znacznika S/F
    corner_line: str   # pionowe linie zakrętów
    corner_text: str   # etykiety T1, T2…
    value_text: str    # tekst na wypełnionych polach (heatmapa, słupki)

    # ── Pomocniki budujące layout ────────────────────────────────────────────
    def style(self, fig: go.Figure, title: str = "", height: int = 700) -> go.Figure:
        """Nakłada motyw na całą figurę (tło, czcionki, osie, legenda, hover)."""
        fig.update_layout(
            title=dict(text=title, font=dict(color=self.heading, size=15, family=FONT_MONO)),
            paper_bgcolor=self.bg,
            plot_bgcolor=self.plot,
            font=dict(color=self.text, family=FONT_MONO, size=13),
            height=height,
            legend=dict(bgcolor=self.legend_bg, bordercolor=self.border, borderwidth=1,
                        font=dict(color=self.text)),
            margin=dict(l=60, r=30, t=60, b=50),
            hoverlabel=dict(bgcolor=self.hover_bg, bordercolor=self.border,
                            font_color=self.hover_text),
        )
        fig.update_xaxes(gridcolor=self.grid, zerolinecolor=self.grid,
                         tickfont=dict(color=self.tick), showgrid=True)
        fig.update_yaxes(gridcolor=self.grid, zerolinecolor=self.grid,
                         tickfont=dict(color=self.tick), showgrid=True)
        self.style_subplot_titles(fig)
        return fig

    def axis(self, title: str = "") -> dict:
        """Ustawienia jednej osi — do `fig.update_yaxes(**t.axis("V"))`."""
        return dict(
            title=dict(text=title, font=dict(color=self.text, size=12)),
            gridcolor=self.grid,
            zerolinecolor=self.grid,
            tickfont=dict(color=self.tick, size=10),
        )

    def style_subplot_titles(self, fig: go.Figure) -> None:
        """Przemalowuje adnotacje (tytuły subplotów) zachowując rozmiar czcionki."""
        for ann in fig.layout.annotations:
            ann.font.color = self.subtitle
            if ann.font.family is None:
                ann.font.family = FONT_MONO

    def track_axes(self, fig: go.Figure, row=None, col=None) -> None:
        """Osie mapy toru: ukryte, z zachowaniem proporcji 1:1."""
        kw = {} if row is None else dict(row=row, col=col)
        fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1, **kw)
        fig.update_yaxes(visible=False, **kw)
        if row is None:
            fig.update_layout(plot_bgcolor=self.track_bg)


DARK = PlotTheme(
    name="dark",
    bg="#0F0F0F",
    plot="#1A1A1A",
    track_bg="#0A0A0A",
    grid="#2A2A2A",
    text="#CCCCCC",
    tick="#888888",
    subtitle="#AAAAAA",
    heading="#FFFFFF",
    border="#444444",
    legend_bg="#222222",
    hover_bg="#1A1A1A",
    hover_text="#FFFFFF",
    soft="#555555",
    track_under="#1A1A1A",
    track_wide="#222222",
    track_mid="#303030",
    dot_edge="#FFFFFF",
    marker_edge="#222222",
    start="#FFFF00",
    corner_line="#383838",
    corner_text="#666666",
    value_text="#FFFFFF",
)

LIGHT = PlotTheme(
    name="light",
    bg="#FFFFFF",
    plot="#F5F7FB",
    track_bg="#EEF1F7",
    grid="#DDE4F0",
    text="#1A2540",
    tick="#5A6B8A",
    subtitle="#5A6B8A",
    heading="#0A0F20",
    border="#C8D4E8",
    legend_bg="#FFFFFF",
    hover_bg="#FFFFFF",
    hover_text="#0A0F20",
    soft="#A9B5CB",
    track_under="#D6DCE8",
    track_wide="#C3CBDB",
    track_mid="#DCE2EE",
    dot_edge="#0A0F20",
    marker_edge="#FFFFFF",
    start="#D98A00",
    corner_line="#CBD3E2",
    corner_text="#7C8AA3",
    value_text="#10203A",
)

THEMES: dict[str, PlotTheme] = {DARK.name: DARK, LIGHT.name: LIGHT}
DEFAULT_THEME = DARK.name


def get_theme(theme: str | PlotTheme = DEFAULT_THEME) -> PlotTheme:
    """Zwraca paletę po nazwie; nieznana nazwa cofa się do motywu domyślnego."""
    if isinstance(theme, PlotTheme):
        return theme
    return THEMES.get(str(theme).lower(), DARK)


def rgba(hex_color: str, alpha: float) -> str:
    """#RRGGBB -> rgba(r,g,b,alpha)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def restyle(fig: go.Figure, theme: str | PlotTheme) -> go.Figure:
    """
    Przemalowuje gotową figurę na inny motyw — bez przeliczania danych.

    Kolory kierowców i skale barwne zostają nietknięte; zmieniamy tylko to,
    co zależy od motywu: tła, czcionki, siatkę, legendę, hover, kontrolki
    animacji oraz trasy oznaczone rolą w `meta`.
    """
    if fig is None:
        return fig
    t = get_theme(theme)
    lay = fig.layout

    is_track = lay.plot_bgcolor in (DARK.track_bg, LIGHT.track_bg)
    fig.update_layout(
        paper_bgcolor=t.bg,
        plot_bgcolor=t.track_bg if is_track else t.plot,
        font=dict(color=t.text, family=FONT_MONO),
        legend=dict(bgcolor=t.legend_bg, bordercolor=t.border, font=dict(color=t.text)),
        hoverlabel=dict(bgcolor=t.hover_bg, bordercolor=t.border, font_color=t.hover_text),
        title=dict(font=dict(color=t.heading, family=FONT_MONO)),
    )

    fig.update_xaxes(gridcolor=t.grid, zerolinecolor=t.grid,
                     tickfont=dict(color=t.tick), title_font=dict(color=t.text))
    fig.update_yaxes(gridcolor=t.grid, zerolinecolor=t.grid,
                     tickfont=dict(color=t.tick), title_font=dict(color=t.text))

    if lay.polar is not None and lay.polar.bgcolor is not None:
        fig.update_layout(polar=dict(
            bgcolor=t.plot,
            angularaxis=dict(gridcolor=t.grid, linecolor=t.border,
                             tickfont=dict(color=t.text)),
            radialaxis=dict(gridcolor=t.grid, linecolor=t.border,
                            tickfont=dict(color=t.tick)),
        ))

    for ann in lay.annotations:
        ann.font.color = t.corner_text if (ann.font.size or 11) <= 9 else t.subtitle

    for shape in lay.shapes:
        if shape.line is not None and shape.line.color is not None:
            shape.line.color = t.corner_line if shape.line.dash is None else t.soft

    for menu in lay.updatemenus:
        menu.bgcolor, menu.bordercolor = t.plot, t.border
        menu.font.color = t.text
    for slider in lay.sliders:
        slider.bgcolor, slider.bordercolor, slider.tickcolor = t.plot, t.border, t.border
        slider.font.color = t.tick
        if slider.currentvalue is not None:
            slider.currentvalue.font.color = t.text

    _restyle_traces(fig.data, t)
    for frame in (fig.frames or []):
        _restyle_traces(frame.data, t)
    return fig


def _restyle_traces(traces, t: PlotTheme) -> None:
    """Aktualizuje trasy oznaczone rolą motywu (podkład toru, znacznik S/F…)."""
    for tr in traces:
        role = tr.meta.get("role") if isinstance(tr.meta, dict) else None
        if role == ROLE_TRACK_UNDER:
            tr.marker.color = t.track_under
        elif role == ROLE_TRACK_LINE:
            tr.line.color = t.track_wide if (tr.line.width or 0) >= 10 else t.track_mid
        elif role == ROLE_START:
            tr.marker.color = t.start
            tr.textfont.color = t.start
        elif role == ROLE_DRIVER_DOT:
            tr.marker.line.color = t.dot_edge

        marker = getattr(tr, "marker", None)
        colorbar = getattr(marker, "colorbar", None)
        if colorbar is not None and colorbar.bgcolor is not None:
            colorbar.bgcolor = t.plot
            colorbar.bordercolor = t.border
            colorbar.tickfont.color = t.tick
            if colorbar.title is not None:
                colorbar.title.font.color = t.text
