"""
Warstwa danych na podstawionej sesji FastF1 — bez sieci.

`data_loader` był jedynym modułem bez testów, bo jako jedyny rozmawia ze
światem. Podstawiamy więc minimalny obiekt sesji, który udaje API FastF1
w zakresie, z którego naprawdę korzystamy.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from f1tele import data_loader
from f1tele.data_loader import (
    DriverLapData,
    SessionData,
    _team_color,
    describe_drivers,
    format_lap_time,
    get_driver_color,
    get_fastest_lap,
    load_circuit_corners,
)


# ── Atrapy obiektów FastF1 ───────────────────────────────────────────────────
class FakeLap:
    """Wiersz okrążenia: dostęp jak do Series plus `get_telemetry()`."""

    def __init__(self, telemetry: pd.DataFrame, **values):
        self._values = values
        self._telemetry = telemetry

    def __getitem__(self, key):
        return self._values[key]

    def get(self, key, default=None):
        return self._values.get(key, default)

    @property
    def index(self):
        return list(self._values)

    def get_telemetry(self):
        return FakeTelemetry(self._telemetry)


class FakeTelemetry(pd.DataFrame):
    """DataFrame telemetrii z metodą `add_distance()` w stylu FastF1."""

    @property
    def _constructor(self):
        return FakeTelemetry

    def add_distance(self):
        return self


class FakeLaps:
    def __init__(self, laps: list[FakeLap]):
        self._laps = laps

    @property
    def empty(self) -> bool:
        return not self._laps

    def pick_drivers(self, _driver):
        return self

    def pick_quicklaps(self):
        return self

    def pick_fastest(self):
        return min(self._laps, key=lambda lap: lap["LapTime"])


class FakeSession:
    def __init__(self, laps: FakeLaps, corners: pd.DataFrame | None = None):
        self.laps = laps
        self.drivers = ["1", "4"]
        self._corners = corners if corners is not None else pd.DataFrame()

    def get_driver(self, number):
        return {
            "1": {"Abbreviation": "VER", "FullName": "Max Verstappen",
                  "TeamName": "Red Bull Racing", "TeamColor": "3671C6"},
            "4": {"Abbreviation": "NOR", "FullName": "Lando Norris",
                  "TeamName": "McLaren", "TeamColor": "#FF8000"},
        }[str(number)]

    def get_circuit_info(self):
        return type("CircuitInfo", (), {"corners": self._corners})()


@pytest.fixture
def telemetry() -> pd.DataFrame:
    n = 200
    distance = np.linspace(0, 5000, n)
    return FakeTelemetry({
        "Distance": distance,
        # celowo nieposortowana kolejność kolumn i timedelta w „Time”
        "Time":     pd.to_timedelta(np.linspace(0, 90, n), unit="s"),
        "Speed":    np.full(n, 200.0),
        "Throttle": np.full(n, 80.0),
        "Brake":    np.zeros(n),
        "nGear":    np.full(n, 6),
        "RPM":      np.full(n, 10000),
        "DRS":      np.zeros(n),
        "X":        np.cos(distance / 800) * 1000,
        "Y":        np.sin(distance / 800) * 1000,
        "Z":        np.zeros(n),          # kolumna, której nie chcemy
    })


@pytest.fixture
def session(telemetry) -> SessionData:
    lap = FakeLap(
        telemetry,
        LapTime=pd.Timedelta(seconds=93.66),
        Sector1Time=pd.Timedelta(seconds=24.981),
        Sector2Time=pd.Timedelta(seconds=28.168),
        Sector3Time=pd.Timedelta(seconds=40.511),
        LapNumber=17,
        Compound="SOFT",
        Team="Red Bull Racing",
    )
    data = SessionData(
        year=2024, round_number=5, event_name="Test GP", session_type="Kwalifikacje",
        circuit_name="Testowo", country="PL", drivers=["VER", "NOR"],
        driver_colors={"VER": "#3671C6"},
    )
    data._session = FakeSession(FakeLaps([lap]))
    return data


# ── Testy ────────────────────────────────────────────────────────────────────
def test_team_color_accepts_fastf1_format():
    assert _team_color("3671C6") == "#3671C6"
    assert _team_color("#ff8000") == "#FF8000"
    assert _team_color(None) == ""
    assert _team_color("czerwony") == ""


def test_format_lap_time():
    assert format_lap_time(93.66) == "1:33.660"
    assert format_lap_time(59.999) == "0:59.999"


def test_describe_drivers_maps_numbers_to_codes():
    """FastF1 identyfikuje kierowców numerami — my kodami."""
    described = describe_drivers(FakeSession(FakeLaps([])))
    assert [d["abbr"] for d in described] == ["VER", "NOR"]
    assert described[0]["full_name"] == "Max Verstappen"
    assert described[0]["color"] == "#3671C6"


def test_session_color_prefers_team_color(session):
    assert session.color_for("VER") == "#3671C6"
    # Kierowca spoza sesji dostaje kolor z listy wbudowanej lub zapasowy
    assert session.color_for("NOR") == get_driver_color("NOR")


def test_load_circuit_corners_sorts_and_drops_empty():
    corners = pd.DataFrame({
        "Number":   [3, 1, 2],
        "Letter":   ["", "", "A"],
        "Distance": [900.0, 550.0, np.nan],
    })
    loaded = load_circuit_corners(FakeSession(FakeLaps([]), corners))
    assert list(loaded["Number"]) == [1, 3]
    assert list(loaded["Distance"]) == [550.0, 900.0]


def test_load_circuit_corners_survives_missing_data():
    assert load_circuit_corners(FakeSession(FakeLaps([]))).empty


def test_get_fastest_lap_normalizes_telemetry(session):
    lap = get_fastest_lap(session, "VER")

    assert isinstance(lap, DriverLapData)
    assert lap.driver == "VER"
    assert lap.lap_time == pytest.approx(93.66)
    assert lap.lap_time_str == "1:33.660"
    assert lap.sector1 == pytest.approx(24.981)
    assert lap.color == "#3671C6"
    assert lap.has_gps

    # Kolumny w stałej kolejności, bez zbędnego „Z”
    assert list(lap.telemetry.columns) == data_loader.TELEMETRY_CHANNELS + ["X", "Y"]
    # „Time” zamienione na sekundy — na tym opierają się granice sektorów
    assert lap.telemetry["Time"].iloc[-1] == pytest.approx(90.0)


def test_get_fastest_lap_returns_none_without_laps(session):
    session._session = FakeSession(FakeLaps([]))
    assert get_fastest_lap(session, "VER") is None
