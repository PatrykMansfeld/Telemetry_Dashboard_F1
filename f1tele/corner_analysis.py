"""
Analiza zakrętów (corner-by-corner).

Pozycje zakrętów bierzemy z FastF1 (`session.get_circuit_info()`) — to oficjalna
numeracja toru, ta sama co w transmisji. Własna detekcja z przebiegu prędkości
zostaje jako awaryjna, gdy sesja nie ma danych o torze; jest zgrubna, bo
łagodniejsze łuki nie dają wyraźnego minimum prędkości.

Zakręty wyznaczamy raz dla całej sesji, a potem mierzymy w tych samych miejscach
każdego kierowcę, żeby porównanie było uczciwe. Progi pochodzą z `f1tele.config`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.signal import find_peaks, savgol_filter

from .config import (
    CORNER_BRAKE_ON,
    CORNER_MIN_DIST_BETWEEN,
    CORNER_MIN_SPEED_DROP,
    CORNER_SMOOTH_WINDOW,
    CORNER_THROTTLE_ON,
    CORNER_WINDOW_AFTER,
    CORNER_WINDOW_BEFORE,
)
from .data_loader import DriverLapData

log = logging.getLogger(__name__)


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
    source: str = "official"   # official | detected

    @property
    def is_official(self) -> bool:
        return self.source == "official"


def _smooth_speed(speed: np.ndarray, window: int = CORNER_SMOOTH_WINDOW) -> np.ndarray:
    """Wygładza przebieg prędkości, żeby szum nie generował fałszywych zakrętów."""
    if len(speed) < window:
        return speed
    return savgol_filter(speed, min(window, len(speed) - (1 if len(speed) % 2 == 0 else 0)), 3)


def _as_percent(values: np.ndarray) -> np.ndarray:
    """FastF1 podaje hamulec raz jako 0/1, raz jako 0–100 — normalizuje do procentów."""
    values = np.asarray(values, dtype=float)
    return values * 100.0 if values.size and values.max() <= 1.0 else values


def corners_from_circuit(circuit_corners: pd.DataFrame, max_distance: float) -> list[dict]:
    """
    Przepisuje oficjalne zakręty toru na format używany w analizie.

    Args:
        circuit_corners: DataFrame z FastF1 (kolumny Number, Letter, Distance)
        max_distance: długość okrążenia w telemetrii — odcina zakręty poza zakresem
    """
    if circuit_corners is None or circuit_corners.empty:
        return []

    corners: list[dict] = []
    for _, row in circuit_corners.iterrows():
        distance = float(row["Distance"])
        if not 0 < distance < max_distance:
            continue
        letter = str(row.get("Letter") or "").strip()
        number = int(row["Number"])
        corners.append({
            "id": number,
            "distance": distance,
            "name": f"T{number}{letter}",
            "min_speed": 0.0,
        })
    return corners


def detect_corners(
    telemetry: pd.DataFrame,
    min_speed_drop: float = CORNER_MIN_SPEED_DROP,
    min_distance_between: float = CORNER_MIN_DIST_BETWEEN,
) -> list[dict]:
    """Awaryjna detekcja: zakręt = lokalne minimum prędkości na okrążeniu."""
    dist   = telemetry["Distance"].values
    speed  = telemetry["Speed"].values
    smooth = _smooth_speed(speed)

    min_dist_samples = max(1, int(min_distance_between / (dist[-1] / len(dist))))
    valleys, _ = find_peaks(-smooth, distance=min_dist_samples, prominence=min_speed_drop)

    return [
        {"id": cid, "distance": float(dist[idx]), "min_speed": float(speed[idx]),
         "name": f"T{cid}"}
        for cid, idx in enumerate(valleys, start=1)
    ]


def analyze_corner_events(
    driver: str,
    telemetry: pd.DataFrame,
    corners: list[dict],
    window_before: float = CORNER_WINDOW_BEFORE,
    window_after: float = CORNER_WINDOW_AFTER,
) -> list[CornerEvent]:
    """Mierzy punkt hamowania, apeks i powrót do gazu w każdym zakręcie."""
    dist     = telemetry["Distance"].values
    speed    = telemetry["Speed"].values
    throttle = (telemetry["Throttle"].values if "Throttle" in telemetry.columns
                else np.zeros_like(speed))
    brake    = _as_percent(
        telemetry["Brake"].values if "Brake" in telemetry.columns else np.zeros_like(speed)
    )

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
        braking_indices  = np.where(brake_before > CORNER_BRAKE_ON)[0]
        braking_point    = (
            float(dist_before[braking_indices[0]]) if len(braking_indices) > 0
            else apex_d_actual - 50.0
        )

        after_apex           = seg_dist >= apex_d_actual
        throt_after          = seg_throt[after_apex]
        dist_after           = seg_dist[after_apex]
        throttle_idx         = np.where(throt_after > CORNER_THROTTLE_ON)[0]
        exit_throttle_point  = (
            float(dist_after[throttle_idx[0]]) if len(throttle_idx) > 0
            else apex_d_actual + 100.0
        )

        dt = np.where(seg_speed > 1, np.diff(seg_dist, prepend=seg_dist[0]) / (seg_speed / 3.6), 0)

        events.append(CornerEvent(
            corner_id=corner["id"],
            driver=driver,
            braking_point=braking_point,
            apex_speed=apex_speed_val,
            apex_distance=apex_d_actual,
            exit_throttle_point=exit_throttle_point,
            min_speed=apex_speed_val,
            max_brake_pressure=float(seg_brake.max()),
            braking_distance=max(0.0, apex_d_actual - braking_point),
            corner_time=float(dt.sum()),
        ))

    return events


def run_corner_analysis(
    drivers_data: dict[str, DriverLapData],
    circuit_corners: pd.DataFrame | None = None,
) -> CornerAnalysis:
    """
    Wyznacza zakręty toru i analizuje je dla wszystkich kierowców.

    Args:
        drivers_data: telemetria porównywanych kierowców
        circuit_corners: oficjalne zakręty z FastF1 (`SessionData.corners`);
            gdy ich brak, wracamy do detekcji z przebiegu prędkości
    """
    if not drivers_data:
        return CornerAnalysis(corners=[], source="detected")

    leader   = min(drivers_data.values(), key=lambda d: d.lap_time)
    max_dist = float(leader.telemetry["Distance"].max())

    corners = corners_from_circuit(circuit_corners, max_dist)
    source = "official"
    if not corners:
        corners = detect_corners(leader.telemetry)
        source = "detected"
        log.info("Brak oficjalnych zakrętów — wykryto %d z przebiegu prędkości",
                 len(corners))
    else:
        log.info("Oficjalne zakręty toru: %d", len(corners))

    analysis = CornerAnalysis(corners=corners, source=source)
    for drv, data in drivers_data.items():
        analysis.driver_corners[drv] = analyze_corner_events(drv, data.telemetry, corners)

    # Oficjalny dystans wskazuje wejście w zakręt; realny apeks bierzemy
    # z najwolniejszego przejazdu, żeby etykiety siadały tam, gdzie faktycznie
    # kierowcy zwalniają.
    for corner in analysis.corners:
        apexes = [e.apex_speed for events in analysis.driver_corners.values()
                  for e in events if e.corner_id == corner["id"]]
        if apexes:
            corner["min_speed"] = float(min(apexes))

    return analysis
