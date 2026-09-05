"""
Interaktywne wykresy Plotly.

Każda funkcja `plot_*` zwraca gotową `go.Figure` (albo `None`, gdy sesja nie ma
potrzebnych danych) i przyjmuje nazwę motywu w argumencie `theme`.
Gotową figurę można przemalować bez przeliczania danych: `restyle(fig, "light")`.
"""

from __future__ import annotations

from .corners import plot_braking_points_interactive, plot_corners_interactive
from .race import (
    plot_position_interactive,
    plot_race_pace_interactive,
    plot_stint_overview_interactive,
    plot_tire_degradation_interactive,
)
from .sectors import (
    plot_mini_sector_dominance_interactive,
    plot_sector_colors_interactive,
    plot_sector_heatmap_interactive,
)
from .style import plot_radar_interactive, plot_style_bars_interactive
from .telemetry import plot_delta_time_interactive, plot_telemetry_interactive
from .theme import DEFAULT_THEME, THEMES, PlotTheme, get_theme, restyle
from .track import (
    plot_driver_dominance_map_interactive,
    plot_drs_interactive,
    plot_gear_map_interactive,
    plot_speed_heatmap_track_interactive,
    plot_track_animation_interactive,
)
from .weather import plot_weather_interactive

__all__ = [
    "DEFAULT_THEME",
    "THEMES",
    "PlotTheme",
    "get_theme",
    "restyle",
    "plot_braking_points_interactive",
    "plot_corners_interactive",
    "plot_delta_time_interactive",
    "plot_drs_interactive",
    "plot_driver_dominance_map_interactive",
    "plot_gear_map_interactive",
    "plot_mini_sector_dominance_interactive",
    "plot_position_interactive",
    "plot_race_pace_interactive",
    "plot_radar_interactive",
    "plot_sector_colors_interactive",
    "plot_sector_heatmap_interactive",
    "plot_speed_heatmap_track_interactive",
    "plot_stint_overview_interactive",
    "plot_style_bars_interactive",
    "plot_telemetry_interactive",
    "plot_tire_degradation_interactive",
    "plot_track_animation_interactive",
    "plot_weather_interactive",
]
