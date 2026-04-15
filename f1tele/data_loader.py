"""
Moduł ładowania i cachowania danych telemetrycznych FastF1.
Obsługuje pobieranie sesji, okrążeń i pełnych danych telemetrycznych.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import fastf1
import fastf1.plotting
import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich import box

warnings.filterwarnings("ignore")

console = Console()

CACHE_DIR = Path(__file__).parent.parent / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

DRIVER_COLORS: dict[str, str] = {
    "VER": "#3671C6",
    "PER": "#3671C6",
    "HAM": "#27F4D2",
    "RUS": "#27F4D2",
    "LEC": "#E8002D",
    "SAI": "#E8002D",
    "NOR": "#FF8000",
    "PIA": "#FF8000",
    "ALO": "#358C75",
    "STR": "#358C75",
    "OCO": "#FF87BC",
    "GAS": "#FF87BC",
    "ALB": "#64C4FF",
    "SAR": "#64C4FF",
    "BOT": "#C92D4B",
    "ZHO": "#C92D4B",
    "HUL": "#B6BABD",
    "MAG": "#B6BABD",
    "TSU": "#356FAD",
    "LAW": "#356FAD",
    "RIC": "#356FAD",
    "DEV": "#356FAD",
    "BEA": "#229971",
    "ANT": "#229971",
}

FALLBACK_COLORS = [
    "#FF0000", "#0000FF", "#00FF00", "#FF8C00", "#9400D3",
    "#00CED1", "#FF1493", "#32CD32", "#FFD700", "#FF6347",
]


@dataclass
class DriverLapData:
    """Kompletne dane telemetryczne jednego okrążenia kierowcy."""
    driver: str
    lap_number: int
    lap_time: float          # sekundy
    lap_time_str: str
    compound: str
    sector1: float
    sector2: float
    sector3: float
    telemetry: pd.DataFrame  # Distance, Speed, Throttle, Brake, nGear, RPM, DRS
    color: str
    team: str = ""


@dataclass
class SessionData:
    """Dane całej sesji wyścigowej."""
    year: int
    round_number: int
    event_name: str
    session_type: str        # Q, R, FP1, FP2, FP3, S, SS
    circuit_name: str
    country: str
    drivers: list[str] = field(default_factory=list)
    fastest_laps: dict[str, DriverLapData] = field(default_factory=dict)
    _session: object = field(default=None, repr=False)


def get_driver_color(driver: str, index: int = 0) -> str:
    """Zwraca kolor kierowcy lub kolor zapasowy."""
    return DRIVER_COLORS.get(driver.upper(), FALLBACK_COLORS[index % len(FALLBACK_COLORS)])


def load_session(
    year: int,
    round_number: int | str,
    session_type: str = "Q",
    verbose: bool = True,
) -> SessionData:
    """
    Ładuje sesję F1 i zwraca obiekt SessionData.

    Args:
        year: Rok sezonu (np. 2024)
        round_number: Numer rundy lub nazwa GP (np. 5 lub 'Monaco')
        session_type: Typ sesji: Q, R, FP1, FP2, FP3, S, SS
        verbose: Czy wyświetlać postęp

    Returns:
        SessionData z załadowanymi danymi
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            f"Ładowanie sesji {year} GP#{round_number} [{session_type}]...", total=None
        )

        ff1_session = fastf1.get_session(year, round_number, session_type)
        progress.update(task, description="Pobieranie danych telemetrycznych...")
        ff1_session.load(telemetry=True, weather=False, messages=False)

        event = ff1_session.event
        sd = SessionData(
            year=year,
            round_number=ff1_session.event.RoundNumber,
            event_name=str(event.get("EventName", f"GP #{round_number}")),
            session_type=session_type,
            circuit_name=str(event.get("Location", "Unknown")),
            country=str(event.get("Country", "Unknown")),
            _session=ff1_session,
        )

        # Lista kierowców w sesji
        try:
            sd.drivers = list(ff1_session.drivers)
        except Exception:
            sd.drivers = []

    if verbose:
        console.print(
            f"[bold green]✓[/bold green] Załadowano: [bold]{sd.event_name} {sd.year}[/bold] "
            f"— {sd.session_type} | {sd.circuit_name}, {sd.country}"
        )
    return sd


def get_fastest_lap(
    session_data: SessionData,
    driver: str,
    lap_number: Optional[int] = None,
) -> Optional[DriverLapData]:
    """
    Pobiera najszybsze (lub konkretne) okrążenie kierowcy.

    Args:
        session_data: Załadowana sesja
        driver: Kod kierowcy (np. 'VER', 'HAM')
        lap_number: Numer okrążenia (None = najszybsze)

    Returns:
        DriverLapData lub None jeśli brak danych
    """
    ff1 = session_data._session
    try:
        drv_laps = ff1.laps.pick_drivers(driver.upper())
        if drv_laps.empty:
            console.print(f"[yellow]⚠ Brak okrążeń dla kierowcy {driver}[/yellow]")
            return None

        if lap_number is not None:
            lap = drv_laps[drv_laps["LapNumber"] == lap_number]
            if lap.empty:
                console.print(f"[yellow]⚠ Nie znaleziono okrążenia #{lap_number} dla {driver}[/yellow]")
                return None
            lap = lap.iloc[0]
        else:
            lap = drv_laps.pick_fastest()

        telem = lap.get_telemetry().add_distance()

        # Normalizacja kolumn
        needed = {"Distance", "Speed", "Throttle", "Brake", "nGear", "RPM", "DRS"}
        for col in needed:
            if col not in telem.columns:
                telem[col] = 0

        gps_cols = [c for c in ("X", "Y") if c in telem.columns]
        telem = telem[list(needed) + gps_cols].copy()
        telem = telem.dropna(subset=["Distance", "Speed"])
        telem = telem.sort_values("Distance").reset_index(drop=True)

        lap_time_s = float(lap["LapTime"].total_seconds()) if pd.notna(lap["LapTime"]) else 0.0
        m, s = divmod(lap_time_s, 60)
        lap_time_str = f"{int(m)}:{s:06.3f}"

        s1 = float(lap["Sector1Time"].total_seconds()) if pd.notna(lap.get("Sector1Time")) else 0.0
        s2 = float(lap["Sector2Time"].total_seconds()) if pd.notna(lap.get("Sector2Time")) else 0.0
        s3 = float(lap["Sector3Time"].total_seconds()) if pd.notna(lap.get("Sector3Time")) else 0.0

        team = str(lap.get("Team", "")) if "Team" in lap.index else ""

        idx = list(session_data.drivers).index(driver.upper()) if driver.upper() in session_data.drivers else 0
        color = get_driver_color(driver, idx)

        return DriverLapData(
            driver=driver.upper(),
            lap_number=int(lap["LapNumber"]),
            lap_time=lap_time_s,
            lap_time_str=lap_time_str,
            compound=str(lap.get("Compound", "UNKNOWN")),
            sector1=s1,
            sector2=s2,
            sector3=s3,
            telemetry=telem,
            color=color,
            team=team,
        )
    except Exception as exc:
        console.print(f"[red]✗ Błąd pobierania danych dla {driver}: {exc}[/red]")
        return None


def load_drivers_data(
    session_data: SessionData,
    drivers: list[str],
    lap_numbers: Optional[dict[str, int]] = None,
) -> dict[str, DriverLapData]:
    """
    Ładuje dane dla listy kierowców.

    Args:
        session_data: Załadowana sesja
        drivers: Lista kodów kierowców
        lap_numbers: Opcjonalny słownik {driver: lap_number}

    Returns:
        Słownik {driver: DriverLapData}
    """
    results: dict[str, DriverLapData] = {}
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Pobieranie danych kierowców...", total=len(drivers))
        for drv in drivers:
            progress.update(task, description=f"Pobieranie danych {drv}...")
            ln = (lap_numbers or {}).get(drv)
            data = get_fastest_lap(session_data, drv, ln)
            if data is not None:
                results[drv] = data
                session_data.fastest_laps[drv] = data
            progress.advance(task)

    return results


def print_lap_summary(drivers_data: dict[str, DriverLapData]) -> None:
    """Wyświetla tabelę podsumowania okrążeń."""
    table = Table(
        title="[bold]Podsumowanie okrążeń[/bold]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Kierowca", style="bold", width=10)
    table.add_column("Czas okrążenia", justify="right", width=15)
    table.add_column("S1", justify="right", width=9)
    table.add_column("S2", justify="right", width=9)
    table.add_column("S3", justify="right", width=9)
    table.add_column("Okrążenie #", justify="center", width=11)
    table.add_column("Opona", justify="center", width=8)

    sorted_drivers = sorted(drivers_data.values(), key=lambda d: d.lap_time)
    reference_time = sorted_drivers[0].lap_time if sorted_drivers else 0.0

    for i, d in enumerate(sorted_drivers):
        delta = d.lap_time - reference_time
        delta_str = f"+{delta:.3f}" if delta > 0 else "POLE"
        time_color = "green" if i == 0 else "white"

        table.add_row(
            f"[{d.color}]{d.driver}[/{d.color}]",
            f"[{time_color}]{d.lap_time_str}[/{time_color}] ({delta_str})",
            f"{d.sector1:.3f}s",
            f"{d.sector2:.3f}s",
            f"{d.sector3:.3f}s",
            str(d.lap_number),
            d.compound,
        )

    console.print(table)


def get_available_sessions(year: int) -> pd.DataFrame:
    """Zwraca listę dostępnych sesji dla danego roku."""
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule[["RoundNumber", "EventName", "Location", "Country", "EventDate"]]
    except Exception as exc:
        console.print(f"[red]Błąd pobierania harmonogramu: {exc}[/red]")
        return pd.DataFrame()


def get_session_drivers_list(
    year: int,
    round_number: int | str,
    session_type: str = "Q",
) -> list[dict]:
    """
    Szybko pobiera listę kierowców z sesji bez ładowania telemetrii.

    Returns:
        Lista słowników {abbr, full_name, team}
    """
    ff1_session = fastf1.get_session(year, round_number, session_type)
    ff1_session.load(telemetry=False, weather=False, messages=False)

    result: list[dict] = []
    for abbr in ff1_session.drivers:
        try:
            info = ff1_session.get_driver(abbr)
            full_name = str(info.get("FullName", abbr))
            team = str(info.get("TeamName", ""))
        except Exception:
            full_name = str(abbr)
            team = ""
        result.append({"abbr": str(abbr), "full_name": full_name, "team": team})

    return result


def get_race_pace_data(
    session_data: SessionData,
    drivers: list[str],
) -> pd.DataFrame:
    """
    Pobiera wszystkie prawidłowe okrążenia każdego kierowcy do analizy tempa wyścigu.
    Filtruje pit-lapy i outliery (pick_quicklaps).

    Returns:
        DataFrame z kolumnami: Driver, LapNumber, LapTime_s, Compound, Stint, Color
    """
    ff1 = session_data._session
    rows: list[dict] = []

    for drv in drivers:
        try:
            drv_laps = ff1.laps.pick_drivers(drv.upper()).pick_quicklaps()
            if drv_laps.empty:
                continue
            color = get_driver_color(drv)
            for _, lap in drv_laps.iterrows():
                if not pd.notna(lap["LapTime"]):
                    continue
                try:
                    stint = int(lap["Stint"]) if pd.notna(lap.get("Stint")) else 0
                except (TypeError, ValueError):
                    stint = 0
                rows.append({
                    "Driver":    drv.upper(),
                    "LapNumber": int(lap["LapNumber"]),
                    "LapTime_s": float(lap["LapTime"].total_seconds()),
                    "Compound":  str(lap.get("Compound", "UNKNOWN")),
                    "Stint":     stint,
                    "Color":     color,
                })
        except Exception as exc:
            console.print(f"[yellow]⚠ Race pace: błąd dla {drv}: {exc}[/yellow]")

    return pd.DataFrame(rows) if rows else pd.DataFrame()
