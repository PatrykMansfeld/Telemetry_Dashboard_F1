"""
Analiza sektorów i mini-sektorów.

Sektory S1/S2/S3 wyznaczamy z **oficjalnych czasów sektorowych**: znając czas
zakończenia S1 i S2 znajdujemy w telemetrii dystans, na którym kierowca ten czas
osiągnął. Wcześniejsza wersja dzieliła okrążenie na trzy równe odcinki dystansu,
co na większości torów nie pokrywa się z prawdziwymi granicami.

Mini-sektory to nadal równy podział dystansu — tam chodzi o gęstą siatkę
porównawczą, a nie o zgodność z oficjalnym podziałem toru.

Czas w odcinku liczymy całkując dystans przez prędkość — telemetria FastF1 nie
podaje go wprost.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import (
    BRAKE_ON_THRESHOLD,
    DEFAULT_MINI_SECTS,
    THROTTLE_FULL_THRESHOLD,
)
from .data_loader import DriverLapData

SECTOR_NAMES = ("S1", "S2", "S3")


@dataclass
class MiniSector:
    """Wyniki jednego mini-sektora."""
    index: int
    dist_start: float
    dist_end: float
    fastest_driver: str
    times: dict[str, float]
    speeds: dict[str, float]


def _segment(telemetry: pd.DataFrame, d_start: float, d_end: float) -> pd.DataFrame:
    mask = (telemetry["Distance"] >= d_start) & (telemetry["Distance"] <= d_end)
    return telemetry[mask]


def _time_in_range(telemetry: pd.DataFrame, d_start: float, d_end: float) -> float:
    """Czas przejazdu odcinka [m] wyliczony z prędkości chwilowej."""
    seg = _segment(telemetry, d_start, d_end)
    if len(seg) < 2:
        return 0.0
    dist  = seg["Distance"].values
    speed = seg["Speed"].values
    dt = np.where(speed > 1, np.diff(dist, prepend=dist[0]) / (speed / 3.6), 0)
    return float(dt.sum())


def _avg_speed_in_range(telemetry: pd.DataFrame, d_start: float, d_end: float) -> float:
    seg = _segment(telemetry, d_start, d_end)
    return float(seg["Speed"].mean()) if not seg.empty else 0.0


def sector_bounds(data: DriverLapData) -> list[tuple[float, float]]:
    """
    Granice S1/S2/S3 na osi dystansu, wyznaczone z oficjalnych czasów sektorów.

    Gdy sesja nie ma czasów sektorowych albo kanału czasu, wracamy do podziału
    na trzy równe odcinki — z zaznaczeniem, że to przybliżenie
    (patrz `uses_official_sectors`).
    """
    telem = data.telemetry
    total = float(telem["Distance"].max())

    if uses_official_sectors(data):
        time = telem["Time"].values
        dist = telem["Distance"].values
        # Czas narastająco od startu okrążenia -> dystans na końcu S1 i S2.
        end_s1 = float(np.interp(data.sector1, time, dist))
        end_s2 = float(np.interp(data.sector1 + data.sector2, time, dist))
        if 0 < end_s1 < end_s2 < total:
            return [(0.0, end_s1), (end_s1, end_s2), (end_s2, total)]

    third = total / 3
    return [(0.0, third), (third, 2 * third), (2 * third, total)]


def uses_official_sectors(data: DriverLapData) -> bool:
    """Czy da się odtworzyć prawdziwe granice sektorów dla tego okrążenia."""
    telem = data.telemetry
    if "Time" not in telem.columns or telem["Time"].max() <= 0:
        return False
    return data.sector1 > 0 and data.sector2 > 0


def compute_mini_sectors(
    drivers_data: dict[str, DriverLapData],
    n_sectors: int = DEFAULT_MINI_SECTS,
) -> list[MiniSector]:
    """Dzieli okrążenie na `n_sectors` równych odcinków i wskazuje najszybszego w każdym."""
    if not drivers_data:
        return []

    max_dist = min(d.telemetry["Distance"].max() for d in drivers_data.values())
    edges = np.linspace(0, max_dist, n_sectors + 1)
    mini_sectors: list[MiniSector] = []

    for i in range(n_sectors):
        d_start = float(edges[i])
        d_end   = float(edges[i + 1])

        times:  dict[str, float] = {}
        speeds: dict[str, float] = {}

        for drv, data in drivers_data.items():
            times[drv]  = _time_in_range(data.telemetry, d_start, d_end)
            speeds[drv] = _avg_speed_in_range(data.telemetry, d_start, d_end)

        valid   = {k: v for k, v in times.items() if v > 0}
        fastest = min(valid, key=valid.get) if valid else ""

        mini_sectors.append(MiniSector(
            index=i + 1,
            dist_start=d_start,
            dist_end=d_end,
            fastest_driver=fastest,
            times=times,
            speeds=speeds,
        ))

    return mini_sectors


def compute_sector_stats(drivers_data: dict[str, DriverLapData]) -> pd.DataFrame:
    """
    Statystyki S1/S2/S3 per kierowca, na prawdziwych granicach sektorów.

    Returns:
        DataFrame: Driver, Sector, Time_s, Official_s, Diff_s, MaxSpeed, AvgSpeed,
        FullThrottle_pct, Braking_pct, Official (czy granice są oficjalne)
    """
    rows = []
    for drv, data in drivers_data.items():
        telem    = data.telemetry
        bounds   = sector_bounds(data)
        official = [data.sector1, data.sector2, data.sector3]
        is_official = uses_official_sectors(data)

        for s_idx, (d_start, d_end) in enumerate(bounds, start=1):
            seg = _segment(telem, d_start, d_end)
            if seg.empty:
                continue

            full_throttle_pct = (
                (seg["Throttle"] > THROTTLE_FULL_THRESHOLD).sum() / len(seg) * 100
                if "Throttle" in seg.columns else 0.0
            )
            brake_col = seg["Brake"].values if "Brake" in seg.columns else np.zeros(len(seg))
            # Hamulec bywa zapisany jako 0/1 albo jako 0–100 — próg dobieramy do skali.
            threshold = (BRAKE_ON_THRESHOLD / 100 if brake_col.max() <= 1
                         else BRAKE_ON_THRESHOLD)
            brake_pct = (brake_col > threshold).sum() / len(seg) * 100

            measured = _time_in_range(telem, d_start, d_end)
            official_time = official[s_idx - 1]

            rows.append({
                "Driver":           drv,
                "Sector":           SECTOR_NAMES[s_idx - 1],
                "Time_s":           measured,
                "Official_s":       official_time,
                "Diff_s":           measured - official_time if official_time > 0 else 0.0,
                "MaxSpeed":         float(seg["Speed"].max()),
                "AvgSpeed":         float(seg["Speed"].mean()),
                "FullThrottle_pct": full_throttle_pct,
                "Braking_pct":      brake_pct,
                "Official":         is_official,
                "DistStart":        d_start,
                "DistEnd":          d_end,
            })

    return pd.DataFrame(rows)
