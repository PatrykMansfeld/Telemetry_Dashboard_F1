"""
Pipeline analizy: od parametrów sesji do gotowych wykresów.

Cała orkiestracja żyje tutaj, a nie w warstwie Streamlita — dzięki temu tę samą
analizę da się odpalić z notatnika czy skryptu. Postęp raportujemy przez
`on_progress`, a moduł, który się wywróci, ląduje w `AnalysisResult.warnings`
zamiast wysadzać całą analizę.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go

from . import plots
from .config import ANIMATION_FRAMES, DEFAULT_MINI_SECTS, DEFAULT_PLOT_THEME
from .corner_analysis import CornerAnalysis, run_corner_analysis
from .data_loader import (
    DriverLapData,
    SessionData,
    get_position_data,
    get_race_pace_data,
    get_weather_data,
    load_drivers_data,
    load_session,
)
from .driver_style import (
    StyleFingerprint,
    compute_style_fingerprint,
    normalize_fingerprints,
)
from .sector_analysis import MiniSector, compute_mini_sectors, compute_sector_stats

log = logging.getLogger(__name__)

# callback(procent 0-100, opis kroku)
ProgressFn = Callable[[int, str], None]


@dataclass
class Modules:
    """Które moduły analizy uruchomić."""
    telemetry: bool = True
    corners: bool = True
    sectors: bool = True
    style: bool = True
    track: bool = True
    race_pace: bool = True
    weather: bool = True


@dataclass
class AnalysisRequest:
    """Parametry jednego uruchomienia analizy."""
    year: int
    round_number: int | str
    session_type: str
    drivers: list[str]
    mini_sectors: int = DEFAULT_MINI_SECTS
    modules: Modules = field(default_factory=Modules)
    theme: str = DEFAULT_PLOT_THEME
    # None = najszybsze okrążenie każdego kierowcy; liczba = to konkretne okrążenie
    # (przydatne np. do porównania świeżej opony ze zużytą).
    lap_number: int | None = None

    def cache_key(self) -> tuple:
        """Klucz identyfikujący analizę — bez motywu, bo ten zmieniamy w locie."""
        return (
            self.year, str(self.round_number), self.session_type,
            tuple(sorted(self.drivers)), self.mini_sectors, self.lap_number,
            tuple(sorted(vars(self.modules).items())),
        )


@dataclass
class AnalysisResult:
    """Komplet danych i wykresów jednej sesji."""
    session: SessionData
    drivers: dict[str, DriverLapData]
    theme: str
    corners: CornerAnalysis | None = None
    mini_sectors: list[MiniSector] = field(default_factory=list)
    sector_stats: pd.DataFrame | None = None
    fingerprints: list[StyleFingerprint] = field(default_factory=list)
    race_pace: pd.DataFrame = field(default_factory=pd.DataFrame)
    positions: pd.DataFrame = field(default_factory=pd.DataFrame)
    weather: pd.DataFrame = field(default_factory=pd.DataFrame)
    figures: dict[str, go.Figure] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def sorted_drivers(self) -> list[DriverLapData]:
        """Kierowcy od najszybszego okrążenia."""
        return sorted(self.drivers.values(), key=lambda d: d.lap_time)

    @property
    def has_gps(self) -> bool:
        return any(d.has_gps for d in self.drivers.values())

    def same_circuit_as(self, other: AnalysisResult) -> bool:
        """
        Czy obie sesje odbyły się na tym samym torze.

        Bez tego porównanie telemetrii po dystansie nie ma sensu — ten sam
        kilometr okrążenia to na każdym torze inne miejsce.
        """
        return (self.session.circuit_name.strip().lower()
                == other.session.circuit_name.strip().lower())


class _Builder:
    """Zbiera wykresy, zapisując błędy zamiast przerywać analizę."""

    def __init__(self, result: AnalysisResult, theme: str) -> None:
        self.result = result
        self.theme = theme

    def add(self, key: str, fn, *args, **kwargs) -> go.Figure | None:
        """Buduje wykres pod kluczem `key`; niepowodzenie trafia do `warnings`."""
        try:
            fig = fn(*args, theme=self.theme, **kwargs)
        except Exception as exc:
            log.exception("Nie udało się wygenerować wykresu %s", key)
            self.result.warnings.append(f"{key}: {type(exc).__name__} — {exc}")
            return None
        if fig is not None:
            self.result.figures[key] = fig
        return fig


def run_analysis(
    request: AnalysisRequest,
    on_progress: ProgressFn | None = None,
) -> AnalysisResult:
    """
    Uruchamia pełną analizę sesji zgodnie z `request`.

    Raises:
        ValueError: gdy nie podano kierowców albo nie udało się pobrać
            telemetrii dla żadnego z nich.
    """
    def progress(pct: int, text: str) -> None:
        if on_progress is not None:
            on_progress(pct, text)

    if not request.drivers:
        raise ValueError("Nie wybrano żadnego kierowcy.")

    mods = request.modules

    progress(5, f"Ładowanie sesji {request.year} GP#{request.round_number} "
                f"[{request.session_type}]...")
    session = load_session(request.year, request.round_number, request.session_type)

    progress(20, f"Pobieranie telemetrii: {', '.join(request.drivers)}")
    lap_numbers = (dict.fromkeys(request.drivers, request.lap_number)
                   if request.lap_number else None)
    drivers_data = load_drivers_data(
        session, request.drivers, lap_numbers=lap_numbers,
        on_progress=lambda drv, i, total: progress(
            20 + int(15 * i / total), f"Telemetria {drv} ({i}/{total})"),
    )
    if not drivers_data:
        raise ValueError(
            f"Nie udało się pobrać okrążenia {request.lap_number} dla żadnego kierowcy."
            if request.lap_number else
            "Nie udało się pobrać danych dla żadnego kierowcy."
        )

    result = AnalysisResult(session=session, drivers=drivers_data, theme=request.theme)
    build = _Builder(result, request.theme)

    if mods.telemetry:
        progress(45, "Wykres telemetrii...")
        build.add("telemetry", plots.plot_telemetry_interactive, drivers_data, session)

    if mods.corners:
        progress(55, "Analiza zakrętów...")
        try:
            result.corners = run_corner_analysis(drivers_data, session.corners)
        except Exception as exc:
            log.exception("Analiza zakrętów nie powiodła się")
            result.warnings.append(f"zakręty: {type(exc).__name__} — {exc}")
        if result.corners is not None:
            build.add("corners", plots.plot_corners_interactive,
                      drivers_data, result.corners, session)
            build.add("braking_points", plots.plot_braking_points_interactive,
                      drivers_data, result.corners, session)

    if mods.telemetry and len(drivers_data) >= 2:
        build.add("delta_time", plots.plot_delta_time_interactive,
                  drivers_data, session, result.corners)

    if mods.sectors:
        progress(65, "Analiza sektorów...")
        result.mini_sectors = compute_mini_sectors(drivers_data, request.mini_sectors)
        result.sector_stats = compute_sector_stats(drivers_data)
        build.add("mini_sectors", plots.plot_mini_sector_dominance_interactive,
                  drivers_data, result.mini_sectors, session)
        build.add("sector_heatmap", plots.plot_sector_heatmap_interactive,
                  result.sector_stats, drivers_data, session)
        build.add("sector_colors", plots.plot_sector_colors_interactive,
                  drivers_data, session)

    if mods.style:
        progress(75, "Odcisk palca stylu jazdy...")
        result.fingerprints = normalize_fingerprints([
            compute_style_fingerprint(d, result.corners) for d in drivers_data.values()
        ])
        build.add("radar", plots.plot_radar_interactive, result.fingerprints, session)
        build.add("style_bars", plots.plot_style_bars_interactive,
                  result.fingerprints, session)

    if mods.track:
        progress(85, "Mapy toru...")
        build.add("track_dominance", plots.plot_driver_dominance_map_interactive,
                  drivers_data, session)
        for d in drivers_data.values():
            build.add(f"speed_map_{d.driver}",
                      plots.plot_speed_heatmap_track_interactive, d, session)
            build.add(f"gear_map_{d.driver}",
                      plots.plot_gear_map_interactive, d, session)
        build.add("drs", plots.plot_drs_interactive, drivers_data, session)

    if mods.race_pace:
        progress(92, "Tempo wyścigu...")
        result.race_pace = get_race_pace_data(session, list(drivers_data))
        result.positions = get_position_data(session, list(drivers_data))
        if not result.race_pace.empty:
            build.add("race_pace", plots.plot_race_pace_interactive,
                      result.race_pace, drivers_data, session)
            build.add("tire_degradation", plots.plot_tire_degradation_interactive,
                      result.race_pace, drivers_data, session)
            build.add("stint_overview", plots.plot_stint_overview_interactive,
                      result.race_pace, drivers_data, session)
        if not result.positions.empty:
            build.add("positions", plots.plot_position_interactive,
                      result.positions, drivers_data, session)

    if mods.weather:
        progress(97, "Warunki pogodowe...")
        result.weather = get_weather_data(session)
        if not result.weather.empty:
            build.add("weather", plots.plot_weather_interactive, result.weather, session)

    progress(100, "Analiza zakończona")
    log.info("Wygenerowano %d wykresów, %d ostrzeżeń",
             len(result.figures), len(result.warnings))
    return result


def build_track_animation(
    result: AnalysisResult,
    n_frames: int = ANIMATION_FRAMES,
) -> go.Figure | None:
    """Animacja okrążenia — liczona na żądanie, bo jest kosztowna."""
    return plots.plot_track_animation_interactive(
        result.drivers, result.session, n_frames=n_frames, theme=result.theme,
    )


def load_comparison_session(
    year: int,
    round_number: int | str,
    session_type: str,
    drivers: list[str],
) -> AnalysisResult:
    """
    Ładuje samą telemetrię drugiej sesji (do porównania cross-session).

    Raises:
        ValueError: gdy brak kierowców albo danych.
    """
    if not drivers:
        raise ValueError("Nie wybrano kierowców sesji B.")

    session = load_session(year, round_number, session_type)
    drivers_data = load_drivers_data(session, drivers)
    if not drivers_data:
        raise ValueError("Brak danych dla wybranych kierowców sesji B.")

    return AnalysisResult(session=session, drivers=drivers_data, theme=DEFAULT_PLOT_THEME)
