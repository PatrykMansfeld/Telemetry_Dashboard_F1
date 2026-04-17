"""
Analiza sektorów i mini-sektorów.
Dzieli okrążenie na 3 oficjalne sektory oraz N równych mini-sektorów.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data_loader import DriverLapData


@dataclass
class MiniSector:
    """Wyniki jednego mini-sektora."""
    index: int
    dist_start: float
    dist_end: float
    fastest_driver: str
    times: dict[str, float]
    speeds: dict[str, float]


def _time_in_range(telemetry: pd.DataFrame, d_start: float, d_end: float) -> float:
    mask = (telemetry["Distance"] >= d_start) & (telemetry["Distance"] <= d_end)
    seg  = telemetry[mask]
    if len(seg) < 2:
        return 0.0
    dist  = seg["Distance"].values
    speed = seg["Speed"].values
    dt = np.where(speed > 1, np.diff(dist, prepend=dist[0]) / (speed / 3.6), 0)
    return float(dt.sum())


def _avg_speed_in_range(telemetry: pd.DataFrame, d_start: float, d_end: float) -> float:
    mask = (telemetry["Distance"] >= d_start) & (telemetry["Distance"] <= d_end)
    seg  = telemetry[mask]
    return float(seg["Speed"].mean()) if not seg.empty else 0.0


def compute_mini_sectors(
    drivers_data: dict[str, DriverLapData],
    n_sectors: int = 25,
) -> list[MiniSector]:
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
    rows = []
    for drv, data in drivers_data.items():
        telem       = data.telemetry
        total_dist  = telem["Distance"].max()
        sector_bounds = [
            (0.0,               total_dist / 3),
            (total_dist / 3,    2 * total_dist / 3),
            (2 * total_dist / 3, total_dist),
        ]

        for s_idx, (d_start, d_end) in enumerate(sector_bounds, start=1):
            mask = (telem["Distance"] >= d_start) & (telem["Distance"] <= d_end)
            seg  = telem[mask]
            if seg.empty:
                continue

            full_throttle_pct = (
                (seg["Throttle"] > 90).sum() / len(seg) * 100
                if "Throttle" in seg.columns else 0
            )
            brake_col = seg["Brake"].values if "Brake" in seg.columns else np.zeros(len(seg))
            threshold = 0.05 if brake_col.max() <= 1 else 5.0
            brake_pct = (brake_col > threshold).sum() / len(seg) * 100

            rows.append({
                "Driver":           drv,
                "Sector":           f"S{s_idx}",
                "Time_s":           _time_in_range(data.telemetry, d_start, d_end),
                "MaxSpeed":         float(seg["Speed"].max()),
                "AvgSpeed":         float(seg["Speed"].mean()),
                "FullThrottle_pct": full_throttle_pct,
                "Braking_pct":      brake_pct,
                "Official_s":       [data.sector1, data.sector2, data.sector3][s_idx - 1],
            })

    return pd.DataFrame(rows)
