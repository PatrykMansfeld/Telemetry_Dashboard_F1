"""
Analiza zakrętów (corner-by-corner).
Wyznacza punkty hamowania, apeksy i wyjścia z zakrętów dla każdego kierowcy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter
from rich.console import Console

from .data_loader import DriverLapData

console = Console()


@dataclass
class CornerEvent:
    """Dane jednego zakrętu dla jednego kierowcy."""
    corner_id: int
    driver: str
    braking_point: float
    apex_speed: float
    apex_distance: float
    exit_throttle_point: float
    min_speed: float
    max_brake_pressure: float
    braking_distance: float
    corner_time: float


@dataclass
class CornerAnalysis:
    """Pełna analiza zakrętów dla sesji."""
    corners: list[dict]
    driver_corners: dict[str, list[CornerEvent]] = field(default_factory=dict)


def _smooth_speed(speed: np.ndarray, window: int = 21) -> np.ndarray:
    if len(speed) < window:
        return speed
    return savgol_filter(speed, min(window, len(speed) - (1 if len(speed) % 2 == 0 else 0)), 3)


def detect_corners(
    telemetry: pd.DataFrame,
    min_speed_drop: float = 30.0,
    min_distance_between: float = 200.0,
) -> list[dict]:
    dist   = telemetry["Distance"].values
    speed  = telemetry["Speed"].values
    smooth = _smooth_speed(speed)

    min_dist_samples = max(1, int(min_distance_between / (dist[-1] / len(dist))))
    valleys, _ = find_peaks(-smooth, distance=min_dist_samples, prominence=min_speed_drop)

    return [
        {"id": cid, "distance": float(dist[idx]), "min_speed": float(speed[idx]), "name": f"T{cid}"}
        for cid, idx in enumerate(valleys, start=1)
    ]


def analyze_corner_events(
    driver: str,
    telemetry: pd.DataFrame,
    corners: list[dict],
    window_before: float = 300.0,
    window_after: float = 200.0,
) -> list[CornerEvent]:
    dist     = telemetry["Distance"].values
    speed    = telemetry["Speed"].values
    throttle = telemetry["Throttle"].values if "Throttle" in telemetry.columns else np.zeros_like(speed)
    brake    = telemetry["Brake"].values    if "Brake"    in telemetry.columns else np.zeros_like(speed)

    if brake.max() <= 1.0:
        brake = brake * 100.0

    events: list[CornerEvent] = []

    for corner in corners:
        apex_d = corner["distance"]
        mask   = (dist >= apex_d - window_before) & (dist <= apex_d + window_after)
        if mask.sum() < 5:
            continue

        seg_dist  = dist[mask]
        seg_speed = speed[mask]
        seg_throt = throttle[mask]
        seg_brake = brake[mask]

        apex_local_idx = np.argmin(seg_speed)
        apex_d_actual  = float(seg_dist[apex_local_idx])
        apex_speed_val = float(seg_speed[apex_local_idx])

        before_apex      = seg_dist <= apex_d_actual
        brake_before     = seg_brake[before_apex]
        dist_before      = seg_dist[before_apex]
        braking_indices  = np.where(brake_before > 5.0)[0]
        braking_point    = (
            float(dist_before[braking_indices[0]]) if len(braking_indices) > 0
            else apex_d_actual - 50.0
        )

        after_apex           = seg_dist >= apex_d_actual
        throt_after          = seg_throt[after_apex]
        dist_after           = seg_dist[after_apex]
        throttle_idx         = np.where(throt_after > 80.0)[0]
        exit_throttle_point  = (
            float(dist_after[throttle_idx[0]]) if len(throttle_idx) > 0
            else apex_d_actual + 100.0
        )

        braking_distance = apex_d_actual - braking_point
        max_brake        = float(seg_brake.max())
        dt = np.where(seg_speed > 1, np.diff(seg_dist, prepend=seg_dist[0]) / (seg_speed / 3.6), 0)
        corner_time = float(dt.sum())

        events.append(CornerEvent(
            corner_id=corner["id"],
            driver=driver,
            braking_point=braking_point,
            apex_speed=apex_speed_val,
            apex_distance=apex_d_actual,
            exit_throttle_point=exit_throttle_point,
            min_speed=apex_speed_val,
            max_brake_pressure=max_brake,
            braking_distance=max(0.0, braking_distance),
            corner_time=corner_time,
        ))

    return events


def run_corner_analysis(drivers_data: dict[str, DriverLapData]) -> CornerAnalysis:
    if not drivers_data:
        return CornerAnalysis(corners=[])

    leader  = min(drivers_data.values(), key=lambda d: d.lap_time)
    corners = detect_corners(leader.telemetry)
    console.print(f"[cyan]Wykryto {len(corners)} zakrętów[/cyan]")

    analysis = CornerAnalysis(corners=corners)
    for drv, data in drivers_data.items():
        analysis.driver_corners[drv] = analyze_corner_events(drv, data.telemetry, corners)

    return analysis
