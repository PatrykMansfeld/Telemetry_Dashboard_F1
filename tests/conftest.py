"""
Dane syntetyczne dla testów — nie wymagają sieci ani cache'u FastF1.

Generujemy „tor” z sensownym profilem prędkości, żeby detekcja zakrętów
i analiza sektorów miały na czym pracować.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from f1tele.data_loader import DriverLapData, SessionData

LAP_LENGTH = 5000.0
SAMPLES = 900


def _telemetry(rng: np.random.Generator, offset: float, gps: bool) -> pd.DataFrame:
    dist = np.linspace(0, LAP_LENGTH, SAMPLES)
    base = 250 + 70 * np.sin(dist / 380.0) - 40 * np.sin(dist / 120.0)
    speed = np.clip(base + offset + rng.normal(0, 2, SAMPLES), 60, 340)

    # Czas od startu okrążenia — całka z prędkości po dystansie; na nim opierają
    # się prawdziwe granice sektorów.
    step = np.diff(dist, prepend=dist[0])
    elapsed = np.cumsum(step / (speed / 3.6))

    telem = pd.DataFrame({
        "Distance": dist,
        "Time":     elapsed,
        "Speed":    speed,
        "Throttle": np.clip((speed - 90) / 2.2, 0, 100),
        "Brake":    np.clip(-np.gradient(speed) * 22, 0, 100),
        "nGear":    np.clip(np.round(speed / 42), 1, 8),
        "RPM":      4000 + speed * 25,
        "DRS":      np.where((dist % 1700) < 260, 12, 0),
    })
    if gps:
        angle = dist / LAP_LENGTH * 2 * np.pi
        telem["X"] = 1000 * np.cos(angle) + 260 * np.cos(3 * angle)
        telem["Y"] = 1000 * np.sin(angle) + 260 * np.sin(2 * angle)
    return telem


def make_driver(name: str, color: str, offset: float, *,
                rng: np.random.Generator, gps: bool = True) -> DriverLapData:
    """
    Jeden kierowca; `offset` [km/h] decyduje, o ile jest szybszy od bazy.

    Czasy sektorów wyliczamy z wygenerowanej telemetrii (30 % / 35 % / 35 %
    okrążenia), żeby granice sektorów dało się na niej odtworzyć.
    """
    telemetry = _telemetry(rng, offset, gps)
    lap_time = float(telemetry["Time"].iloc[-1])
    return DriverLapData(
        driver=name,
        lap_number=12,
        lap_time=lap_time,
        lap_time_str=f"1:{lap_time - 60:06.3f}",
        compound="SOFT",
        sector1=lap_time * 0.30,
        sector2=lap_time * 0.35,
        sector3=lap_time * 0.35,
        telemetry=telemetry,
        color=color,
        team="Test",
    )


@pytest.fixture(scope="session")
def drivers() -> dict[str, DriverLapData]:
    rng = np.random.default_rng(7)
    return {
        "VER": make_driver("VER", "#3671C6", 3.0, rng=rng),
        "NOR": make_driver("NOR", "#FF8000", 0.0, rng=rng),
        "LEC": make_driver("LEC", "#E8002D", -2.0, rng=rng),
    }


@pytest.fixture(scope="session")
def session(drivers) -> SessionData:
    return SessionData(
        year=2024, round_number=5, event_name="Test Grand Prix",
        session_type="Kwalifikacje", circuit_name="Testowo", country="PL",
        drivers=list(drivers),
    )


@pytest.fixture(scope="session")
def race_pace(drivers) -> pd.DataFrame:
    rng = np.random.default_rng(11)
    laps = np.arange(1, 41)
    return pd.DataFrame([
        {
            "Driver":    drv,
            "LapNumber": int(lap),
            "LapTime_s": 84 + i * 0.25 + (lap % 18) * 0.05 + rng.normal(0, 0.08),
            "Compound":  "SOFT" if lap <= 18 else ("MEDIUM" if lap <= 30 else "HARD"),
            "Stint":     1 if lap <= 18 else (2 if lap <= 30 else 3),
            "Color":     data.color,
        }
        for i, (drv, data) in enumerate(drivers.items()) for lap in laps
    ])


@pytest.fixture(scope="session")
def positions(drivers) -> pd.DataFrame:
    return pd.DataFrame([
        {"Driver": drv, "LapNumber": int(lap), "Position": 1 + i + (lap % 3),
         "Color": data.color}
        for i, (drv, data) in enumerate(drivers.items())
        for lap in range(1, 41)
    ])


@pytest.fixture(scope="session")
def weather() -> pd.DataFrame:
    rng = np.random.default_rng(13)
    return pd.DataFrame({
        "Time":      pd.to_timedelta(np.arange(30) * 60, unit="s"),
        "AirTemp":   22 + rng.normal(0, 0.4, 30),
        "TrackTemp": 38 + rng.normal(0, 0.8, 30),
        "Humidity":  55 + rng.normal(0, 2, 30),
        "WindSpeed": 3 + rng.normal(0, 0.6, 30),
        "Rainfall":  np.zeros(30),
    })
