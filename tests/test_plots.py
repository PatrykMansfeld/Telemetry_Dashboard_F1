"""Każdy wykres musi się zbudować w obu motywach i dać przemalować."""

from __future__ import annotations

import pytest

from f1tele import plots
from f1tele.corner_analysis import run_corner_analysis
from f1tele.driver_style import compute_style_fingerprint, normalize_fingerprints
from f1tele.plots.theme import DARK, LIGHT
from f1tele.sector_analysis import compute_mini_sectors, compute_sector_stats

# Kolory, które w motywie jasnym nie mają prawa zostać na tle figury.
DARK_BACKGROUNDS = {DARK.bg.upper(), DARK.plot.upper(), DARK.track_bg.upper()}


@pytest.fixture(scope="module")
def figures_input(drivers, session, race_pace, positions, weather):
    corners = run_corner_analysis(drivers)
    fingerprints = normalize_fingerprints(
        [compute_style_fingerprint(d, corners) for d in drivers.values()])
    return {
        "drivers":      drivers,
        "session":      session,
        "corners":      corners,
        "mini_sectors": compute_mini_sectors(drivers, 20),
        "stats":        compute_sector_stats(drivers),
        "fingerprints": fingerprints,
        "race_pace":    race_pace,
        "positions":    positions,
        "weather":      weather,
    }


def _cases(d):
    """(nazwa, funkcja, argumenty) dla wszystkich wykresów."""
    return [
        ("telemetry", plots.plot_telemetry_interactive, (d["drivers"], d["session"])),
        ("delta_time", plots.plot_delta_time_interactive,
         (d["drivers"], d["session"], d["corners"])),
        ("corners", plots.plot_corners_interactive,
         (d["drivers"], d["corners"], d["session"])),
        ("braking_points", plots.plot_braking_points_interactive,
         (d["drivers"], d["corners"], d["session"])),
        ("mini_sectors", plots.plot_mini_sector_dominance_interactive,
         (d["drivers"], d["mini_sectors"], d["session"])),
        ("sector_heatmap", plots.plot_sector_heatmap_interactive,
         (d["stats"], d["drivers"], d["session"])),
        ("sector_colors", plots.plot_sector_colors_interactive,
         (d["drivers"], d["session"])),
        ("radar", plots.plot_radar_interactive, (d["fingerprints"], d["session"])),
        ("style_bars", plots.plot_style_bars_interactive,
         (d["fingerprints"], d["session"])),
        ("track_dominance", plots.plot_driver_dominance_map_interactive,
         (d["drivers"], d["session"])),
        ("speed_map", plots.plot_speed_heatmap_track_interactive,
         (d["drivers"]["VER"], d["session"])),
        ("gear_map", plots.plot_gear_map_interactive,
         (d["drivers"]["VER"], d["session"])),
        ("animation", plots.plot_track_animation_interactive,
         (d["drivers"], d["session"])),
        ("drs", plots.plot_drs_interactive, (d["drivers"], d["session"])),
        ("race_pace", plots.plot_race_pace_interactive,
         (d["race_pace"], d["drivers"], d["session"])),
        ("tire_degradation", plots.plot_tire_degradation_interactive,
         (d["race_pace"], d["drivers"], d["session"])),
        ("stint_overview", plots.plot_stint_overview_interactive,
         (d["race_pace"], d["drivers"], d["session"])),
        ("positions", plots.plot_position_interactive,
         (d["positions"], d["drivers"], d["session"])),
        ("weather", plots.plot_weather_interactive, (d["weather"], d["session"])),
    ]


def _case_ids(d):
    return [name for name, _, _ in _cases(d)]


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_every_plot_builds(figures_input, theme):
    """Wykres powstaje, jest niepusty i przechodzi walidację Plotly."""
    for name, fn, args in _cases(figures_input):
        figure = fn(*args, theme=theme)
        assert figure is not None, f"{name} [{theme}] zwrócił None"
        assert figure.data, f"{name} [{theme}] nie ma żadnych danych"
        figure.to_json()


def test_light_theme_has_no_dark_background(figures_input):
    """Motyw jasny nie może zostawić ciemnego tła — to był błąd sprzed refactoru."""
    for name, fn, args in _cases(figures_input):
        figure = fn(*args, theme="light")
        assert str(figure.layout.paper_bgcolor).upper() not in DARK_BACKGROUNDS, name
        assert str(figure.layout.plot_bgcolor or LIGHT.plot).upper() \
            not in DARK_BACKGROUNDS, name


def test_restyle_repaints_existing_figure(figures_input):
    """Przełączenie motywu po analizie przemalowuje gotowe figury."""
    for name, fn, args in _cases(figures_input):
        figure = plots.restyle(fn(*args, theme="dark"), "light")
        figure.to_json()
        assert str(figure.layout.paper_bgcolor).upper() not in DARK_BACKGROUNDS, name
        assert str(figure.layout.font.color).upper() == LIGHT.text.upper(), name


def test_restyle_keeps_driver_colors(figures_input):
    """Kolory kierowców są danymi, nie motywem — restyle ich nie rusza."""
    figure = plots.plot_telemetry_interactive(
        figures_input["drivers"], figures_input["session"], theme="dark")
    before = [trace.line.color for trace in figure.data]
    plots.restyle(figure, "light")
    assert [trace.line.color for trace in figure.data] == before


def test_unknown_theme_falls_back_to_dark():
    assert plots.get_theme("nie-ma-takiego") is DARK
